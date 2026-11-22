# implements: TOOL-COV-030, TOOL-COV-040
"""Function and function-call coverage (WP-COV-04)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.cov.errors import CoverageError, CoverageParseError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import RunCoverage, merge_run_coverage
from ectt.cov.metrics import call_coverage, function_coverage


def _doc_with_functions() -> dict[str, Any]:
    return {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "functions": [
                    {
                        "name": "convert",
                        "start_line": 1,
                        "start_column": 5,
                        "end_line": 12,
                        "end_column": 1,
                        "blocks": 3,
                        "blocks_executed": 2,
                        "execution_count": 2,
                    },
                    {
                        "name": "clamp",
                        "start_line": 14,
                        "end_line": 18,
                        "execution_count": 0,
                        "blocks": 2,
                        "blocks_executed": 0,
                    },
                ],
                "lines": [
                    {"line_number": 1, "count": 2, "unexecuted_block": False, "function_name": "convert"},
                    {"line_number": 14, "count": 0, "unexecuted_block": False, "function_name": "clamp"},
                ],
            }
        ],
    }


def _doc_with_calls() -> dict[str, Any]:
    return {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {
                        "line_number": 8,
                        "count": 2,
                        "unexecuted_block": False,
                        "calls": [
                            {"returned": 2, "source_block_id": 3, "destination_block_id": 9},
                            {"returned": 0, "source_block_id": 3, "destination_block_id": 10},
                        ],
                    }
                ],
            }
        ],
    }


# --- TOOL-COV-030: function coverage -------------------------------------------


def test_function_coverage_counts_executed_functions() -> None:
    doc = read_gcov_document(_doc_with_functions())
    (file,) = doc.files
    totals = function_coverage([file])
    assert totals.total == 2
    assert totals.covered == 1  # convert executed, clamp never


def test_function_coverage_not_applicable_without_functions() -> None:
    doc = read_gcov_document(
        {"format_version": "2", "gcc_version": "14.1.0", "data_file": "d.gcda",
         "files": [{"file": "a.c", "lines": []}]}
    )
    (file,) = doc.files
    totals = function_coverage([file])
    assert totals.total is None
    assert totals.covered == 0


def test_function_coverage_aggregates_across_files() -> None:
    doc = read_gcov_document(_doc_with_functions())
    other = read_gcov_document(
        {"format_version": "2", "gcc_version": "14.1.0", "data_file": "d.gcda",
         "files": [{"file": "b.c",
                    "functions": [{"name": "scale", "start_line": 1, "end_line": 3, "execution_count": 5}],
                    "lines": []}]}
    )
    totals = function_coverage([*doc.files, *other.files])
    assert totals.total == 3
    assert totals.covered == 2


# --- TOOL-COV-040: function call coverage ----------------------------------------


def test_call_coverage_counts_returned_calls() -> None:
    """verifies: TOOL-COV-040 — a call is covered iff it returned."""
    doc = read_gcov_document(_doc_with_calls())
    (file,) = doc.files
    totals = call_coverage([file])
    assert totals.total == 2
    assert totals.covered == 1


def test_call_coverage_not_applicable_without_calls() -> None:
    doc = read_gcov_document(
        {"format_version": "2", "gcc_version": "14.1.0", "data_file": "d.gcda",
         "files": [{"file": "a.c", "lines": [{"line_number": 1, "count": 1, "unexecuted_block": False}]}]}
    )
    (file,) = doc.files
    totals = call_coverage([file])
    assert totals.total is None


# --- reader validation -----------------------------------------------------------


def test_duplicate_function_name_is_refused() -> None:
    payload = _doc_with_functions()
    payload["files"][0]["functions"].append(json.loads(json.dumps(payload["files"][0]["functions"][0])))
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "duplicate_function"


def test_negative_execution_count_is_refused() -> None:
    payload = _doc_with_functions()
    payload["files"][0]["functions"][0]["execution_count"] = -1
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "missing_or_invalid_key"


def test_missing_function_name_is_refused() -> None:
    payload = _doc_with_functions()
    del payload["files"][0]["functions"][0]["name"]
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "missing_or_invalid_key"


def test_negative_returned_count_is_refused() -> None:
    payload = _doc_with_calls()
    payload["files"][0]["lines"][0]["calls"][0]["returned"] = -2
    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == "missing_or_invalid_key"


def test_function_records_are_sorted_and_carried() -> None:
    doc = read_gcov_document(_doc_with_functions())
    (file,) = doc.files
    assert [fn.name for fn in file.functions] == ["convert", "clamp"]  # sorted by start line
    convert = file.functions[0]
    assert convert.execution_count == 2
    assert convert.start_column == 5
    assert convert.blocks == 3
    assert convert.blocks_executed == 2


def test_function_records_dump_canonically() -> None:
    doc = read_gcov_document(_doc_with_functions())
    dumped = json.loads(doc.to_json_bytes().decode("utf-8"))
    (file,) = dumped["files"]
    assert {fn["name"] for fn in file["functions"]} == {"convert", "clamp"}
    assert next(iter(dumped.keys())) == "schema_version"


# --- merge discipline --------------------------------------------------------------


def _run(test_id: str, payload: dict[str, Any]) -> Any:
    return RunCoverage(test_id=test_id, outcome="pass", completeness="complete",
                       document=read_gcov_document(payload))


def test_merge_sums_function_execution_counts() -> None:
    a_payload = _doc_with_functions()
    b_payload = json.loads(json.dumps(_doc_with_functions()))
    b_payload["files"][0]["functions"][0]["execution_count"] = 1
    b_payload["files"][0]["functions"][1]["blocks_executed"] = 1
    result = merge_run_coverage([_run("t1", a_payload), _run("t2", b_payload)])
    (file,) = result.document.files
    by_name = {fn.name: fn for fn in file.functions}
    assert by_name["convert"].execution_count == 3  # 2 + 1
    assert by_name["clamp"].blocks_executed == 1  # max(0, 1)
    assert by_name["convert"].blocks == 3  # static count carried, never summed


def test_merge_blocks_mismatch_is_refused() -> None:
    a_payload = _doc_with_functions()
    b_payload = json.loads(json.dumps(_doc_with_functions()))
    b_payload["files"][0]["functions"][0]["blocks"] = 4
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", a_payload), _run("t2", b_payload)])
    assert exc_info.value.reason == "blocks_mismatch"


def test_merge_call_returned_counts_sum() -> None:
    a_payload = _doc_with_calls()
    b_payload = json.loads(json.dumps(_doc_with_calls()))
    b_payload["files"][0]["lines"][0]["calls"][0]["returned"] = 0
    b_payload["files"][0]["lines"][0]["calls"][1]["returned"] = 3
    result = merge_run_coverage([_run("t1", a_payload), _run("t2", b_payload)])
    (file,) = result.document.files
    (first, second) = file.lines[0].calls
    assert first.returned == 2  # 2 + 0
    assert second.returned == 3  # 0 + 3


def test_merge_call_block_id_disagreement_is_refused() -> None:
    a_payload = _doc_with_calls()
    b_payload = json.loads(json.dumps(_doc_with_calls()))
    b_payload["files"][0]["lines"][0]["calls"][0]["destination_block_id"] = 99
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", a_payload), _run("t2", b_payload)])
    assert exc_info.value.reason == "call_block_id_mismatch"


def test_merge_call_site_count_mismatch_is_refused() -> None:
    a_payload = _doc_with_calls()
    b_payload = json.loads(json.dumps(_doc_with_calls()))
    b_payload["files"][0]["lines"][0]["calls"].append({"returned": 1, "source_block_id": 3})
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", a_payload), _run("t2", b_payload)])
    assert exc_info.value.reason == "call_count_mismatch"
