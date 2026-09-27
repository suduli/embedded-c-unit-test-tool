# implements: DSN-PRJ-040
"""Tests for project path validation, POSIX normalization, and confinement.

Verifies: TOOL-PRJ-070, DSN-PRJ-040.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.prj.errors import InvalidRelativePathError, ProjectConfinementError
from ectt.prj.paths import (
    normalize_posix_path,
    resolve_project_path,
    validate_project_path,
)


def test_posix_normalization_valid_paths() -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    cases = [
        ("src/adc/adc.c", "src/adc/adc.c"),
        (r"src\adc\adc.c", "src/adc/adc.c"),
        (r"src\adc/adc.c", "src/adc/adc.c"),
        ("./src/adc/adc.c", "src/adc/adc.c"),
        ("src/./adc/sub/../sub/adc.c", "src/adc/sub/adc.c"),
        ("include/adc.h", "include/adc.h"),
        ("file.c", "file.c"),
    ]

    for input_path, expected in cases:
        assert validate_project_path(input_path) == expected
        assert normalize_posix_path(input_path) == expected


def test_reject_posix_absolute_paths() -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    cases = [
        "/",
        "/etc/shadow",
        "/home/developer/src/adc.c",
        "/usr/local/include/header.h",
    ]

    for bad_path in cases:
        with pytest.raises(InvalidRelativePathError) as exc_info:
            validate_project_path(bad_path)
        assert exc_info.value.reason in ("absolute_path", "root_target")


def test_reject_windows_absolute_and_drive_paths() -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    cases = [
        r"C:\projects\src\main.c",
        "C:/projects/src/main.c",
        r"c:\temp\test.c",
        "d:/work/code.c",
        r"\Windows\System32\drivers.sys",
        r"C:relative_drive_path.c",
        "D:foo/bar",
    ]

    for bad_path in cases:
        with pytest.raises(InvalidRelativePathError) as exc_info:
            validate_project_path(bad_path)
        assert exc_info.value.reason in ("absolute_path", "drive_letter")


def test_reject_unc_paths() -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    cases = [
        r"\\server\share\file.c",
        r"\\192.168.1.1\c$\secret.txt",
        "//server/share/file.c",
    ]

    for bad_path in cases:
        with pytest.raises(InvalidRelativePathError) as exc_info:
            validate_project_path(bad_path)
        assert exc_info.value.reason in ("unc_path", "absolute_path")


def test_reject_escaping_paths() -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    cases = [
        "..",
        "../outside.c",
        r"..\outside.c",
        "src/../../outside.c",
        "a/b/../../../root_escape.c",
        "./../escape",
    ]

    for bad_path in cases:
        with pytest.raises(InvalidRelativePathError) as exc_info:
            validate_project_path(bad_path)
        assert exc_info.value.reason == "path_escape"


def test_reject_empty_or_root_target() -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    cases = [
        "",
        "   ",
        ".",
        "./.",
        "a/..",
    ]

    for bad_path in cases:
        with pytest.raises(InvalidRelativePathError) as exc_info:
            validate_project_path(bad_path)
        assert exc_info.value.reason in ("empty_path", "root_target")


def test_resolve_project_path_confinement(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-070, DSN-PRJ-040"""
    root = tmp_path / "project"
    root.mkdir()

    resolved = resolve_project_path(root, "src/adc/adc.c")
    assert resolved == root.resolve() / "src" / "adc" / "adc.c"
    assert resolved.is_relative_to(root.resolve())

    # Ensure attempts to pass escaping strings are caught
    with pytest.raises(InvalidRelativePathError):
        resolve_project_path(root, "../escaping.c")
