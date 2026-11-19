"""Tests for WP-ING-03 ingestion diagnostics, persistence, staleness claims.

Covers: the ingestion diagnostics pass (missing source, unresolvable include,
unknown flag, deterministic order, clean database), persistence round-trip
with byte-identical saves and named errors, and the claimed pre-existing
staleness and build-context capture surfaces.

Verifies: TOOL-ING-070, TOOL-ING-090, TOOL-ING-100, TOOL-ING-220.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.ing import (
    CompilationDatabase,
    CompilerInvocation,
    IngestionError,
    TranslationUnit,
)
from ectt.ing.diagnostics import (
    KIND_MISSING_SOURCE,
    KIND_UNKNOWN_FLAG,
    KIND_UNRESOLVABLE_INCLUDE,
    collect_ingestion_diagnostics,
)
from ectt.ing.persist import (
    PersistedModelFormatError,
    PersistedModelReadError,
    PersistedSchemaVersionError,
    load_database,
    save_database,
)


def _make_database(
    *,
    build_tag: str | None = "firmware-debug",
    arguments: tuple[str, ...] = ("-Iinc", "-DDEBUG", "src/main.c"),
    working_directory: str = "/project",
) -> CompilationDatabase:
    includes = tuple(arg[2:] for arg in arguments if arg.startswith("-I"))
    defines = tuple(arg[2:] for arg in arguments if arg.startswith("-D"))
    return CompilationDatabase(
        translation_units=(
            TranslationUnit(
                source_path="src/main.c",
                working_directory=working_directory,
                include_paths=includes,
                preprocessor_definitions=defines,
                compiler_invocation=CompilerInvocation(
                    executable="arm-none-eabi-gcc",
                    arguments=arguments,
                    target_triple="arm-none-eabi",
                ),
                response_files=("@flags.rsp",),
            ),
        ),
        build_tag=build_tag,
    )


def _populate_project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.c").write_text("int x;\n", encoding="utf-8")
    (tmp_path / "inc").mkdir()
    (tmp_path / "@flags.rsp").write_text("-Iinc\n", encoding="utf-8")
    return tmp_path


def test_clean_database_produces_no_diagnostics(tmp_path: Path) -> None:
    """verifies: TOOL-ING-070"""
    project = _populate_project(tmp_path)
    database = _make_database(working_directory=project.as_posix())
    assert collect_ingestion_diagnostics(database, project_root=project) == ()


def test_missing_source_is_reported_with_entry(tmp_path: Path) -> None:
    """verifies: TOOL-ING-070"""
    project = _populate_project(tmp_path)
    (project / "src" / "main.c").unlink()
    diagnostics = collect_ingestion_diagnostics(
        _make_database(working_directory=project.as_posix()), project_root=project
    )
    assert len(diagnostics) == 1
    assert diagnostics[0].kind == KIND_MISSING_SOURCE
    assert diagnostics[0].entry_source == "src/main.c"
    assert "does not exist" in diagnostics[0].detail


def test_unresolvable_include_is_reported_with_flag(tmp_path: Path) -> None:
    """verifies: TOOL-ING-070"""
    project = _populate_project(tmp_path)
    database = _make_database(
        arguments=("-Imissing_inc", "-DDEBUG", "src/main.c"),
        working_directory=project.as_posix(),
    )
    diagnostics = collect_ingestion_diagnostics(database, project_root=project)
    assert [d.kind for d in diagnostics] == [KIND_UNRESOLVABLE_INCLUDE]
    assert diagnostics[0].subject == "missing_inc"


def test_unknown_flag_is_reported(tmp_path: Path) -> None:
    """verifies: TOOL-ING-070"""
    project = _populate_project(tmp_path)
    database = _make_database(
        arguments=("-Iinc", "/Zi", "src/main.c"),
        working_directory=project.as_posix(),
    )
    diagnostics = collect_ingestion_diagnostics(database, project_root=project)
    assert [d.kind for d in diagnostics] == [KIND_UNKNOWN_FLAG]
    assert diagnostics[0].subject == "/Zi"


def test_diagnostics_are_deterministically_ordered(tmp_path: Path) -> None:
    """verifies: TOOL-ING-070"""
    project = _populate_project(tmp_path)
    database = _make_database(
        arguments=("-Iinc", "/Zi", "-Qundefined", "src/main.c"),
        working_directory=project.as_posix(),
    )
    extra_unit = TranslationUnit(
        source_path="src/absent.c",
        working_directory=project.as_posix(),
        compiler_invocation=CompilerInvocation(executable="cc"),
    )
    database = CompilationDatabase(
        translation_units=(*database.translation_units, extra_unit),
        build_tag=None,
    )
    diagnostics = collect_ingestion_diagnostics(database, project_root=project)
    keys = [(d.kind, d.entry_source, d.subject) for d in diagnostics]
    assert keys == sorted(keys)
    assert len(diagnostics) == 3


def test_persistence_round_trip_preserves_the_model(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    database = _make_database()
    path = tmp_path / "ingested.json"
    save_database(database, path)
    reloaded = load_database(path)
    assert reloaded.to_dict() == database.to_dict()
    assert reloaded.build_tag == "firmware-debug"
    unit = reloaded.translation_units[0]
    assert unit.include_paths == ("inc",)
    assert unit.compiler_invocation.target_triple == "arm-none-eabi"
    assert unit.response_files == ("@flags.rsp",)


def test_persistence_is_byte_identical_for_identical_input(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    database = _make_database()
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    save_database(database, first)
    save_database(database, second)
    assert first.read_bytes() == second.read_bytes()


def test_persisted_file_is_json_text_with_schema_version(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    path = tmp_path / "ingested.json"
    save_database(_make_database(), path)
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1


def test_missing_persisted_file_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    with pytest.raises(PersistedModelReadError):
        load_database(tmp_path / "absent.json")


def test_non_json_persisted_file_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    path = tmp_path / "bad.json"
    path.write_text("not json {{{", encoding="utf-8")
    with pytest.raises(PersistedModelFormatError):
        load_database(path)


def test_persisted_document_without_schema_version_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    path = tmp_path / "noschema.json"
    path.write_text(json.dumps({"database": {"translation_units": []}}), encoding="utf-8")
    with pytest.raises(PersistedSchemaVersionError):
        load_database(path)


def test_unsupported_schema_version_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-090"""
    path = tmp_path / "future.json"
    path.write_text(
        json.dumps({"schema_version": 99, "database": {"translation_units": []}}),
        encoding="utf-8",
    )
    with pytest.raises(PersistedSchemaVersionError):
        load_database(path)


def test_ingestion_error_hierarchy_intact() -> None:
    """verifies: TOOL-ING-090"""
    from ectt.core.fs import CoreError

    for cls in (
        IngestionError,
        PersistedModelReadError,
        PersistedModelFormatError,
        PersistedSchemaVersionError,
    ):
        assert issubclass(cls, CoreError)


def test_staleness_report_is_strict_not_warning_only(tmp_path: Path) -> None:
    """verifies: TOOL-ING-100"""
    from ectt.ing.errors import StalenessError
    from ectt.ing.staleness import (
        assert_fresh,
        capture_staleness_inputs,
        check_staleness,
    )

    project = _populate_project(tmp_path)
    database = _make_database(working_directory=project.as_posix())
    persisted = project / "ingested.json"
    save_database(database, persisted)
    recorded = capture_staleness_inputs(database, compdb_path=persisted)
    fresh_report = check_staleness(
        recorded, capture_staleness_inputs(database, compdb_path=persisted)
    )
    assert_fresh(fresh_report)
    (project / "src" / "main.c").write_text("int changed;\n", encoding="utf-8")
    report = check_staleness(
        recorded, capture_staleness_inputs(database, compdb_path=persisted)
    )
    assert report.stale is True
    with pytest.raises(StalenessError):
        assert_fresh(report)


def test_build_context_identity_captured_per_entry(tmp_path: Path) -> None:
    """verifies: TOOL-ING-220"""
    database = _make_database()
    unit = database.translation_units[0]
    assert unit.compiler_invocation.target_triple == "arm-none-eabi"
    assert database.build_tag == "firmware-debug"
