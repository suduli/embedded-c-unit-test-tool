"""Tests for the WP-ING-02 single-file ingestion path.

Covers: ingestion of a single .c file with user include paths and defines,
named errors for missing/non-.c sources, and model invariants shared with the
primary path.

Verifies: TOOL-ING-060, TOOL-ING-210 (existing evidence claim).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.ing import CompilationDatabase
from ectt.ing.single_file import (
    NotCSourceError,
    SingleSourceReadError,
    ingest_single_source,
)


def _write_source(tmp_path: Path, name: str = "main.c") -> Path:
    source = tmp_path / name
    source.write_text(
        "int compute(int a) { return a + 1; }\n", encoding="utf-8"
    )
    return source


def test_single_c_file_ingests_into_database(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    source = _write_source(tmp_path)
    database = ingest_single_source(
        source,
        include_paths=("inc", "vendor/inc"),
        preprocessor_definitions=("USE_FAST=1", "DEBUG"),
        working_directory=tmp_path,
    )
    assert isinstance(database, CompilationDatabase)
    assert len(database.translation_units) == 1
    unit = database.translation_units[0]
    assert unit.source_path == source.as_posix()
    assert unit.include_paths == ("inc", "vendor/inc")
    assert unit.preprocessor_definitions == ("USE_FAST=1", "DEBUG")
    assert unit.working_directory == tmp_path.as_posix()


def test_single_file_invocation_is_the_equivalent_compile_command(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    source = _write_source(tmp_path)
    database = ingest_single_source(
        source,
        include_paths=("inc",),
        preprocessor_definitions=("DEBUG",),
    )
    invocation = database.translation_units[0].compiler_invocation
    assert invocation.executable == "cc"
    assert invocation.arguments == ("-Iinc", "-DDEBUG", source.as_posix())


def test_include_and_define_order_is_preserved(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    source = _write_source(tmp_path)
    database = ingest_single_source(
        source,
        include_paths=("b", "a"),
        preprocessor_definitions=("Z", "A", "M"),
    )
    unit = database.translation_units[0]
    assert unit.include_paths == ("b", "a")
    assert unit.preprocessor_definitions == ("Z", "A", "M")


def test_missing_source_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    with pytest.raises(SingleSourceReadError):
        ingest_single_source(tmp_path / "absent.c")


def test_directory_as_source_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    directory = tmp_path / "src.c"
    directory.mkdir()
    with pytest.raises(SingleSourceReadError):
        ingest_single_source(directory)


def test_non_c_source_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    header = tmp_path / "thing.h"
    header.write_text("#pragma once\n", encoding="utf-8")
    with pytest.raises(NotCSourceError) as excinfo:
        ingest_single_source(header)
    assert ".c" in str(excinfo.value)


def test_database_round_trips_through_model_invariants(tmp_path: Path) -> None:
    """verifies: TOOL-ING-060"""
    source = _write_source(tmp_path)
    database = ingest_single_source(
        source,
        include_paths=("inc",),
        preprocessor_definitions=("DEBUG",),
        working_directory=tmp_path,
    )
    unit = database.translation_units[0]
    assert unit.to_dict()["source_path"] == source.as_posix()
    assert unit.compiler_invocation.to_dict()["executable"] == "cc"
