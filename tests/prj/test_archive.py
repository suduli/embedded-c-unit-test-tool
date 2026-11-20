# implements: TOOL-PRJ-100, TOOL-PRJ-110
"""Archival export and reproduction verification (WP-PRJ-05).

Equivalence partitioning over the record sections (full, partial, empty),
deterministic persistence with digest binding, and the reproduction verdict
partitions: matching tool version, mismatched tool version, corrupted record.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.prj.archive import (
    ARCHIVE_SCHEMA_VERSION,
    ArchiveError,
    build_archive_record,
    dump_archive_record,
    load_archive_record,
    verify_archive_record,
)

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")

CONFIGURATION = {
    "schema_version": 1,
    "name": "demo-project",
    "source_roots": ["src"],
    "output_root": "build",
}
TEST_CASES = {"schema_version": 1, "cases": [{"id": "case-1", "inputs": {"a": 1}}]}


def _result_set() -> ResultSet:
    return ResultSet(
        run_id="run-archive",
        execution=ExecutionMetadata(where="host", toolchain="gcc", target_id="tgt-1"),
        results=(
            finalize_result("t1", "pass", "d1" * 32),
            finalize_result("t2", "pass", "d2" * 32),
        ),
    )


def _record() -> Any:
    return build_archive_record(
        configuration=CONFIGURATION,
        clock=CLOCK,
        test_cases=TEST_CASES,
        result_set=_result_set(),
        coverage=({"unit": "src/adc.c", "covered": 8, "total": 10},),
    )


# --- TOOL-PRJ-100: export partitions ---------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "case_id"),
    [
        ({}, "configuration_only"),
        ({"test_cases": TEST_CASES}, "with_test_cases"),
        ({"result_set": "rs"}, "with_results"),
        ({"coverage": ({"unit": "u.c", "covered": 0, "total": 0},)}, "with_empty_coverage"),
    ],
    ids=["configuration_only", "with_test_cases", "with_results", "with_empty_coverage"],
)
def test_export_partitions(kwargs: dict[str, Any], case_id: str) -> None:
    params = dict(kwargs)
    if params.get("result_set") == "rs":
        params["result_set"] = _result_set()
    record = build_archive_record(configuration=CONFIGURATION, clock=CLOCK, **params)

    text = dump_archive_record(record)
    doc: dict[str, Any] = json.loads(text)

    assert doc["schema_version"] == ARCHIVE_SCHEMA_VERSION
    assert doc["provenance"]["tool_version"]
    for section, given in (
        ("test_cases", "test_cases" in params),
        ("result_set", "result_set" in params),
        ("coverage", "coverage" in params),
    ):
        if section == "coverage":
            # coverage is always present; empty when not supplied
            assert (doc["coverage"] != []) == given
        else:
            assert (section in doc) == given
    assert load_archive_record(text) == record  # every partition round-trips


def test_export_requires_configuration() -> None:
    with pytest.raises(ArchiveError) as excinfo:
        build_archive_record(configuration={}, clock=CLOCK)
    assert excinfo.value.reason == "missing_configuration"


def test_export_is_byte_deterministic() -> None:
    assert dump_archive_record(_record()) == dump_archive_record(_record())
    text = dump_archive_record(_record())
    assert text.splitlines()[0] == "{"
    assert text.splitlines()[1] == f'  "schema_version": "{ARCHIVE_SCHEMA_VERSION}",'
    assert "\r" not in text


def test_export_records_input_digests_and_tool_version() -> None:
    record = _record()

    assert record.provenance.input_digests["test_cases"]
    assert record.provenance.input_digests["result_set"]
    assert record.provenance.input_digests["coverage[0]"]
    assert record.provenance.schema_versions["archive"] == ARCHIVE_SCHEMA_VERSION
    assert record.provenance.tool_version  # tool version recorded (PRJ-100)


def test_load_refuses_tampered_configuration() -> None:
    doc: dict[str, Any] = json.loads(dump_archive_record(_record()))
    doc["configuration"]["name"] = "tampered"

    with pytest.raises(ArchiveError) as excinfo:
        load_archive_record(doc)
    assert excinfo.value.reason == "digest_mismatch"


def test_load_refuses_tampered_provenance() -> None:
    doc: dict[str, Any] = json.loads(dump_archive_record(_record()))
    doc["provenance"]["tool_version"] = "999.9"

    with pytest.raises(ArchiveError) as excinfo:
        load_archive_record(doc)
    assert excinfo.value.reason == "digest_mismatch"


def test_load_refuses_unknown_schema_version() -> None:
    doc: dict[str, Any] = json.loads(dump_archive_record(_record()))
    doc["schema_version"] = "9.9"

    with pytest.raises(ArchiveError) as excinfo:
        load_archive_record(doc)
    assert excinfo.value.reason == "incompatible_schema_version"


# --- TOOL-PRJ-110: reproduction verification -------------------------------------------


def test_matching_tool_version_reports_reproducible() -> None:
    record = _record()
    verdict = verify_archive_record(dump_archive_record(record), current_tool_version=record.provenance.tool_version)

    assert verdict.verdict == "reproducible"
    assert verdict.produced_with == verdict.current_tool_version


def test_mismatched_tool_version_is_reported_with_the_producing_version() -> None:
    verdict = verify_archive_record(dump_archive_record(_record()), current_tool_version="0.0.1-other")

    assert verdict.verdict == "tool_version_mismatch"
    assert verdict.produced_with != "0.0.1-other"
    assert verdict.produced_with in verdict.detail
    assert "reproduce with the producing version" in verdict.detail


def test_absent_comparison_reports_integrity_only() -> None:
    verdict = verify_archive_record(dump_archive_record(_record()))

    assert verdict.verdict == "reproducible"
    assert "no tool version comparison" in verdict.detail


def test_corrupted_record_reports_not_raises() -> None:
    doc: dict[str, Any] = json.loads(dump_archive_record(_record()))
    doc["coverage"] = [{"unit": "evil.c", "covered": 1, "total": 1}]

    verdict = verify_archive_record(doc, current_tool_version=doc["provenance"]["tool_version"])

    assert verdict.verdict == "corrupt_record"
    assert verdict.produced_with == doc["provenance"]["tool_version"]  # read best-effort
    assert "integrity check failed" in verdict.detail


def test_verdict_is_deterministic_and_json_safe() -> None:
    record_text = dump_archive_record(_record())
    first = verify_archive_record(record_text, current_tool_version="x").to_dict()
    second = verify_archive_record(record_text, current_tool_version="x").to_dict()

    assert first == second
    assert json.dumps(first)
