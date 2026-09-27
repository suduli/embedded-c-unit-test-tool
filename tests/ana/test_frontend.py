# implements: TOOL-PAR-010, DSN-ANA-090
"""Integration tests for C front-end binding (CMP-ANA).

Verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090, TOOL-NFR-060.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ectt.ana.errors import (
    FrontendParseError,
    LibclangVersionError,
    SourceFileNotFoundError,
)
from ectt.ana.frontend import (
    ClangFrontend,
    check_libclang_version_floor,
    get_libclang_version,
    get_libclang_version_tuple,
    normalize_path,
    parse,
)
from ectt.ana.model import ParsedTranslationUnit
from ectt.ing.model import CompilerInvocation, TranslationUnit


def test_libclang_version_floor_and_query() -> None:
    """verifies: TOOL-PAR-010"""
    ver_str = get_libclang_version()
    assert isinstance(ver_str, str)
    assert "clang version" in ver_str

    ver_tuple = get_libclang_version_tuple()
    assert len(ver_tuple) == 3
    major, minor, patch_num = ver_tuple
    assert (major, minor) >= (18, 1)

    # Floor check succeeds with active version
    check_libclang_version_floor()

    # Floor check fails if version is mocked below floor (e.g. 17.0.6)
    with patch("ectt.ana.frontend.get_libclang_version_tuple", return_value=(17, 0, 6)):
        with pytest.raises(LibclangVersionError) as exc_info:
            check_libclang_version_floor()
        assert exc_info.value.floor == "18.1"
        assert exc_info.value.version == "17.0.6"


def test_parse_with_translation_unit_model(tmp_path: Path) -> None:
    """verifies: TOOL-PAR-010, DSN-ANA-090"""
    # Create a real source file on disk
    src_file = tmp_path / "module.c"
    src_file.write_text(
        "#include \"module.h\"\nint add(int a, int b) { return a + b + BONUS; }\n",
        encoding="utf-8",
    )
    inc_file = tmp_path / "module.h"
    inc_file.write_text("#define BONUS 10\nint add(int a, int b);\n", encoding="utf-8")

    inv = CompilerInvocation(
        executable="arm-none-eabi-gcc",
        arguments=(
            "arm-none-eabi-gcc",
            f"-I{tmp_path.as_posix()}",
            "-std=c99",
            "-c",
            src_file.as_posix(),
        ),
        residual_flags=("-Wall",),
    )
    tu = TranslationUnit(
        source_path=src_file.as_posix(),
        working_directory=tmp_path.as_posix(),
        compiler_invocation=inv,
        language_standard="c99",
    )

    result = parse(tu)
    assert isinstance(result, ParsedTranslationUnit)
    assert result.status == "parsed"
    assert result.is_parsed is True
    assert result.has_errors is False
    assert len(result.errors) == 0
    assert result.translation_unit is not None


def test_parse_syntax_error_yields_failed_status() -> None:
    """verifies: TOOL-PAR-010, DSN-ANA-090"""
    code_with_error = b"""
    int compute(void) {
        return undefined_variable_foo + 42;
    }
    """
    result = parse(
        "broken.c",
        args=["-std=c99"],
        unsaved_files=[("broken.c", code_with_error)],
    )

    assert result.status == "failed"
    assert result.is_failed is True
    assert result.is_parsed is False
    assert result.has_errors is True
    assert len(result.errors) >= 1
    assert any("undefined_variable_foo" in d.message for d in result.errors)
    assert result.translation_unit is not None


def test_missing_source_file_raises_distinct_error(tmp_path: Path) -> None:
    """verifies: TOOL-PAR-010"""
    missing_file = tmp_path / "does_not_exist.c"
    with pytest.raises(SourceFileNotFoundError) as exc_info:
        parse(str(missing_file), args=["-std=c99"])
    assert exc_info.value.reason == "source_file_not_found"
    assert "does_not_exist.c" in str(exc_info.value)


def test_frontend_parse_determinism() -> None:
    """verifies: TOOL-PAR-010, TOOL-NFR-060, DSN-ANA-090"""
    code = b"""
    int calculate(int x) {
        int unknown_token = missing_ref;
        return x * 2;
    }
    """
    # Parse same unit twice
    res1 = parse("det.c", args=["-std=c99"], unsaved_files=[("det.c", code)])
    res2 = parse("det.c", args=["-std=c99"], unsaved_files=[("det.c", code)])

    assert res1.status == res2.status == "failed"
    assert len(res1.diagnostics) == len(res2.diagnostics)

    for d1, d2 in zip(res1.diagnostics, res2.diagnostics, strict=True):
        assert d1.message == d2.message
        assert d1.severity == d2.severity
        assert d1.severity_code == d2.severity_code
        assert d1.line == d2.line
        assert d1.column == d2.column
        assert str(d1) == str(d2)

    # Compare serialized dictionary output
    assert res1.to_dict() == res2.to_dict()
    assert res1.to_json() == res2.to_json()


def test_path_normalization() -> None:
    """verifies: TOOL-PAR-010, TOOL-NFR-060"""
    norm = normalize_path("C:\\foo\\bar\\baz.c")
    assert "\\" not in norm
    assert norm == "C:/foo/bar/baz.c"

    # Relative to base_dir
    base = "C:/foo"
    norm_rel = normalize_path("C:/foo/bar/baz.c", base_dir=base)
    assert norm_rel == "bar/baz.c"
