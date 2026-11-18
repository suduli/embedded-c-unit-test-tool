"""Tests for the WP-CORE-06 logging and diagnostic bundle.

Covers: configurable verbosity with boundary cases, location-reference
records, the source-content guard at record time, and the deterministic
diagnostic bundle with its manifest linkage.

Verifies: TOOL-NFR-130, TOOL-NFR-160.
"""

from __future__ import annotations

import pytest

from ectt.core import (
    DiagnosticBundle,
    EcttLogger,
    LogRecord,
    Verbosity,
    build_diagnostic_bundle,
)
from ectt.sec import SourceContentInDiagnosticError

SOURCE_LINES = [
    "int compute(int a, int b) {",
    "    return a * scale_factor + offset_value;",
]


def _guarded_logger() -> EcttLogger:
    return EcttLogger(source_lines_provider=lambda: SOURCE_LINES)


def test_verbosity_admits_and_refers_levels() -> None:
    """verifies: TOOL-NFR-130"""
    logger = EcttLogger(verbosity=Verbosity.VERBOSE)
    logger.log("quiet message", level=Verbosity.QUIET)
    logger.log("normal message", level=Verbosity.NORMAL)
    logger.log("verbose message", level=Verbosity.VERBOSE)
    logger.log("debug message", level=Verbosity.DEBUG)
    recorded = [record.message for record in logger.records()]
    assert recorded == ["quiet message", "normal message", "verbose message"]


def test_boundary_level_is_recorded_exactly() -> None:
    """verifies: TOOL-NFR-130"""
    logger = EcttLogger(verbosity=Verbosity.NORMAL)
    logger.log("at boundary", level=Verbosity.NORMAL)
    logger.log("above boundary", level=Verbosity.VERBOSE)
    assert [r.message for r in logger.records()] == ["at boundary"]


def test_quiet_verbosity_records_only_quiet() -> None:
    """verifies: TOOL-NFR-130"""
    logger = EcttLogger(verbosity=Verbosity.QUIET)
    logger.log("one", level=Verbosity.NORMAL)
    logger.log("two", level=Verbosity.QUIET)
    assert [r.message for r in logger.records()] == ["two"]


def test_set_verbosity_changes_admission() -> None:
    """verifies: TOOL-NFR-130"""
    logger = EcttLogger(verbosity=Verbosity.QUIET)
    logger.log("kept", level=Verbosity.QUIET)
    logger.set_verbosity(Verbosity.DEBUG)
    logger.log("kept verbose", level=Verbosity.DEBUG)
    assert [r.message for r in logger.records()] == ["kept", "kept verbose"]


def test_records_carry_location_references_not_source() -> None:
    """verifies: TOOL-NFR-130"""
    logger = EcttLogger()
    logger.log("parse failed", path="src/uut.c", line=12, column=4)
    record = logger.records()[0]
    assert isinstance(record, LogRecord)
    assert record.location == "src/uut.c:12:4"
    assert record.render() == "parse failed [src/uut.c:12:4]"
    for source_line in SOURCE_LINES:
        assert source_line.strip() not in record.render()


def test_records_are_in_deterministic_order() -> None:
    """verifies: TOOL-NFR-130"""
    logger = EcttLogger()
    logger.log("first")
    logger.log("second")
    logger.log("third")
    assert [r.message for r in logger.records()] == ["first", "second", "third"]


def test_guard_refuses_source_embedding_at_record_time() -> None:
    """verifies: TOOL-NFR-160"""
    logger = _guarded_logger()
    with pytest.raises(SourceContentInDiagnosticError):
        logger.log(f"context: {SOURCE_LINES[1].strip()}")
    # The refused message is not recorded.
    assert logger.records() == ()


def test_guard_allows_location_and_config_messages() -> None:
    """verifies: TOOL-NFR-160"""
    logger = _guarded_logger()
    logger.log("configuration loaded", path="project/ectt.project.yaml")
    logger.log("analysis failed at src/uut.c:2")
    assert len(logger.records()) == 2


def test_bundle_contains_documented_contents() -> None:
    """verifies: TOOL-NFR-160"""
    logger = EcttLogger()
    logger.log("ingestion complete", path="project/compile_commands.json")
    bundle = build_diagnostic_bundle(
        configuration={"compiler": "gcc", "output_root": "out"},
        logger=logger,
        command="ectt analyze --project .",
        exit_status=1,
        ectt_version="0.1.0",
    )
    assert isinstance(bundle, DiagnosticBundle)
    assert bundle.ectt_version == "0.1.0"
    assert bundle.configuration == (("compiler", "gcc"), ("output_root", "out"))
    assert bundle.log_excerpt == ("ingestion complete [project/compile_commands.json]",)
    assert bundle.command == "ectt analyze --project ."
    assert bundle.exit_status == 1
    assert len(bundle.manifest_entries) >= 4


def test_bundle_configuration_is_sorted() -> None:
    """verifies: TOOL-NFR-160"""
    logger = EcttLogger()
    bundle = build_diagnostic_bundle(
        configuration={"z_option": "1", "a_option": "2"},
        logger=logger,
        command="ectt analyze",
        exit_status=0,
        ectt_version="0.1.0",
    )
    assert bundle.configuration == (("a_option", "2"), ("z_option", "1"))


def test_bundle_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-NFR-160"""
    import dataclasses

    logger = EcttLogger()
    kwargs = {
        "configuration": {"compiler": "gcc"},
        "logger": logger,
        "command": "ectt analyze",
        "exit_status": 0,
        "ectt_version": "0.1.0",
    }
    first = build_diagnostic_bundle(**kwargs)
    second = build_diagnostic_bundle(**kwargs)
    assert first.to_dict() == second.to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.command = "mutated"  # type: ignore[misc]


def test_bundle_from_guarded_logger_has_clean_excerpt() -> None:
    """verifies: TOOL-NFR-160"""
    logger = _guarded_logger()
    logger.log("analysis failed at src/uut.c:2", path="src/uut.c", line=2)
    bundle = build_diagnostic_bundle(
        configuration={},
        logger=logger,
        command="ectt analyze",
        exit_status=2,
        ectt_version="0.1.0",
    )
    assert bundle.log_excerpt == ("analysis failed at src/uut.c:2 [src/uut.c:2]",)
    assert bundle.configuration == ()
    for source_line in SOURCE_LINES:
        assert source_line.strip() not in "\n".join(bundle.log_excerpt)


def test_bundle_with_no_logs_and_empty_config() -> None:
    """verifies: TOOL-NFR-160"""
    bundle = build_diagnostic_bundle(
        configuration={},
        logger=EcttLogger(),
        command="ectt analyze",
        exit_status=0,
        ectt_version="0.1.0",
    )
    assert bundle.log_excerpt == ()
    assert bundle.configuration == ()
    assert bundle.to_dict() == bundle.to_dict()
