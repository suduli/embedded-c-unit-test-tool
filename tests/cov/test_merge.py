# implements: TOOL-COV-110, TOOL-COV-120, TOOL-COV-180, TOOL-COV-220
"""Coverage merge, per-test attribution, completeness and quarantine (WP-COV-02)."""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import (
    ExcludedRun,
    MergeResult,
    RunAdmission,
    RunCoverage,
    coverage_for_test,
    merge_run_coverage,
)


def _doc(counts: dict[int, int] | None = None, **overrides: Any) -> Any:
    """A two-line single-file document with configurable per-line counts."""
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {"line_number": 1, "count": 3, "unexecuted_block": False},
                    {"line_number": 2, "count": 1, "unexecuted_block": False},
                ],
            }
        ],
    }
    if counts is not None:
        for line, count in zip(payload["files"][0]["lines"], [counts.get(1, 0), counts.get(2, 0)], strict=True):
            line["count"] = count
    payload.update(overrides)
    return read_gcov_document(payload)


def _run(test_id: str, document: Any = None, outcome: str = "pass", **kw: Any) -> RunCoverage:
    return RunCoverage(test_id=test_id, outcome=outcome, completeness="complete", document=document, **kw)


# --- TOOL-COV-110: merge ------------------------------------------------------


def test_merge_sums_line_counts_across_runs() -> None:
    a = _run("t1", _doc({1: 3, 2: 1}))
    b = _run("t2", _doc({1: 2, 2: 4}))
    result = merge_run_coverage([a, b])
    assert isinstance(result, MergeResult)
    (file,) = result.document.files
    assert [line.count for line in file.lines] == [5, 5]


def test_merge_unions_lines_across_files() -> None:
    a_doc = _doc({1: 3, 2: 1})
    b_payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {"file": "adc.c", "lines": [{"line_number": 3, "count": 2, "unexecuted_block": False}]},
            {"file": "gain.c", "lines": [{"line_number": 9, "count": 1, "unexecuted_block": False}]},
        ],
    }
    b = _run("t2", read_gcov_document(b_payload))
    result = merge_run_coverage([_run("t1", a_doc), b])
    assert [f.file for f in result.document.files] == ["adc.c", "gain.c"]
    (adc,) = [f for f in result.document.files if f.file == "adc.c"]
    assert [line.line_number for line in adc.lines] == [1, 2, 3]
    (gain,) = [f for f in result.document.files if f.file == "gain.c"]
    assert gain.lines[0].count == 1


def test_merge_or_unexecuted_block() -> None:
    partial_doc = _doc({1: 2})
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {"file": "adc.c", "lines": [{"line_number": 1, "count": 4, "unexecuted_block": True}]}
        ],
    }
    result = merge_run_coverage([_run("t1", partial_doc), _run("t2", read_gcov_document(payload))])
    (file,) = result.document.files
    assert file.lines[0].count == 6
    assert file.lines[0].unexecuted_block is True


def test_branch_flag_disagreement_is_refused() -> None:
    a_payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {
                        "line_number": 5,
                        "count": 1,
                        "unexecuted_block": False,
                        "branches": [
                            {"count": 1, "fallthrough": True, "throw": False,
                             "source_block_id": 2, "destination_block_id": 4}
                        ],
                    }
                ],
            }
        ],
    }
    b_payload = json.loads(json.dumps(a_payload))
    b_payload["files"][0]["lines"][0]["branches"][0]["fallthrough"] = False
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", read_gcov_document(a_payload)), _run("t2", read_gcov_document(b_payload))])
    assert exc_info.value.reason == "branch_flag_mismatch"


def test_condition_outcomes_merge_conservatively() -> None:
    """A term is not-covered in the merge iff it was not-covered in EVERY run."""
    a_payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {
                        "line_number": 7,
                        "count": 2,
                        "unexecuted_block": False,
                        "conditions": [
                            {"count": 4, "covered": 2, "not_covered_false": [], "not_covered_true": [0, 1]}
                        ],
                    }
                ],
            }
        ],
    }
    b_payload = json.loads(json.dumps(a_payload))
    b_payload["files"][0]["lines"][0]["conditions"][0]["not_covered_true"] = [1]
    result = merge_run_coverage([_run("t1", read_gcov_document(a_payload)), _run("t2", read_gcov_document(b_payload))])
    (file,) = result.document.files
    (condition,) = file.lines[0].conditions
    # term 0 seen true in run B; term 1 never seen true -> still not covered
    assert condition.not_covered_true == (1,)
    assert condition.not_covered_false == ()
    assert condition.covered == 3  # 4 outcomes, 1 not covered
    assert condition.count == 4


def test_condition_presence_mismatch_is_refused() -> None:
    with_cond = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {
                        "line_number": 7,
                        "count": 1,
                        "unexecuted_block": False,
                        "conditions": [{"count": 2, "covered": 1, "not_covered_false": [0], "not_covered_true": []}],
                    }
                ],
            }
        ],
    }
    without_cond = json.loads(json.dumps(with_cond))
    del without_cond["files"][0]["lines"][0]["conditions"]
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", read_gcov_document(with_cond)), _run("t2", read_gcov_document(without_cond))])
    assert exc_info.value.reason == "condition_presence_mismatch"


def test_branch_count_mismatch_is_refused() -> None:
    a_payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {
                        "line_number": 5,
                        "count": 1,
                        "unexecuted_block": False,
                        "branches": [{"count": 1, "fallthrough": True, "throw": False}],
                    }
                ],
            }
        ],
    }
    b_payload = json.loads(json.dumps(a_payload))
    b_payload["files"][0]["lines"][0]["branches"].append({"count": 0, "fallthrough": False, "throw": False})
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", read_gcov_document(a_payload)), _run("t2", read_gcov_document(b_payload))])
    assert exc_info.value.reason == "branch_count_mismatch"


def test_condition_count_mismatch_is_refused() -> None:
    a_payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "adc.c",
                "lines": [
                    {
                        "line_number": 7,
                        "count": 1,
                        "unexecuted_block": False,
                        "conditions": [{"count": 2, "covered": 1, "not_covered_false": [0], "not_covered_true": []}],
                    }
                ],
            }
        ],
    }
    b_payload = json.loads(json.dumps(a_payload))
    b_payload["files"][0]["lines"][0]["conditions"][0]["count"] = 3
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", read_gcov_document(a_payload)), _run("t2", read_gcov_document(b_payload))])
    assert exc_info.value.reason == "condition_count_mismatch"


def test_compiler_version_mismatch_is_refused() -> None:
    a = _run("t1", _doc())
    b = _run("t2", _doc(gcc_version="13.2.0"))
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([a, b])
    assert exc_info.value.reason == "gcc_version_mismatch"


def test_merged_dump_is_canonical_and_byte_identical() -> None:
    a = _run("t1", _doc({1: 3, 2: 1}))
    b = _run("t2", _doc({1: 2, 2: 4}))
    first = merge_run_coverage([a, b])
    second = merge_run_coverage([b, a])  # order does not change the aggregate
    assert first.document.to_json_bytes() == second.document.to_json_bytes()
    assert next(iter(json.loads(first.document.to_json_bytes().decode("utf-8")).keys())) == "schema_version"


# --- TOOL-COV-120: per-test attribution ----------------------------------------


def test_per_test_coverage_is_attributed() -> None:
    a = _run("t1", _doc({1: 3, 2: 1}))
    b = _run("t2", _doc({1: 0, 2: 2}))
    totals_a = coverage_for_test(a)
    totals_b = coverage_for_test(b)
    assert totals_a["statements"].covered == 2
    assert totals_b["statements"].covered == 1  # only line 2 ran in t2
    result = merge_run_coverage([a, b])
    assert {run.test_id for run in result.per_run} == {"t1", "t2"}


def test_duplicate_test_ids_are_refused() -> None:
    doc = _doc()
    with pytest.raises(CoverageError) as exc_info:
        merge_run_coverage([_run("t1", doc), _run("t1", doc)])
    assert exc_info.value.reason == "duplicate_test_id"


# --- TOOL-COV-180: completeness ------------------------------------------------


def test_truncated_artifact_is_excluded_with_advisory() -> None:
    complete = _run("t1", _doc({1: 3, 2: 1}))
    truncated = RunCoverage(
        test_id="t2",
        outcome="pass",
        completeness="truncated",
        document=_doc({1: 0, 2: 9}),
        advisory="gcda flush interrupted; counts not trustworthy",
    )
    result = merge_run_coverage([complete, truncated])
    (file,) = result.document.files
    assert [line.count for line in file.lines] == [3, 1]  # truncated counts excluded
    (excluded,) = result.excluded
    assert excluded.reason == "incomplete_artifact"
    assert excluded.advisory == "gcda flush interrupted; counts not trustworthy"
    # truncated record retained in provenance exactly as recorded
    assert {run.completeness for run in result.per_run} == {"complete", "truncated"}


def test_missing_artifact_is_excluded_with_advisory() -> None:
    complete = _run("t1", _doc({1: 3}))
    missing = RunCoverage(
        test_id="t2",
        outcome="pass",
        completeness="missing",
        advisory="no gcda produced for this run",
    )
    result = merge_run_coverage([complete, missing])
    (file,) = result.document.files
    assert file.lines[0].count == 3
    (excluded,) = result.excluded
    assert excluded.reason == "incomplete_artifact"
    assert excluded.completeness == "missing"
    assert excluded.advisory == "no gcda produced for this run"


def test_completeness_state_travels_unrelabeled() -> None:
    """verifies: TOOL-COV-180 — the recorded state is surfaced exactly as recorded."""
    truncated = RunCoverage(
        test_id="t1",
        outcome="error",
        completeness="truncated",
        advisory="profile truncated",
    )
    result = merge_run_coverage([truncated])
    assert result.per_run[0].completeness == "truncated"
    (excluded,) = result.excluded
    assert excluded.completeness == "truncated"
    dumped = json.dumps(result.to_dict())
    assert "truncated" in dumped


# --- §5.4 recorded criterion: quarantine ----------------------------------------


def test_error_outcome_is_quarantined_by_default() -> None:
    good = _run("t1", _doc({1: 3, 2: 1}))
    crashed = _run("t2", _doc({1: 9, 2: 9}), outcome="error")
    result = merge_run_coverage([good, crashed])
    (file,) = result.document.files
    assert [line.count for line in file.lines] == [3, 1]  # aggregate excludes quarantined
    (excluded,) = result.excluded
    assert excluded.reason == "quarantined_outcome"
    assert excluded.test_id == "t2"
    # quarantined data stays visible in per-run provenance
    assert {run.test_id for run in result.per_run} == {"t1", "t2"}


def test_timeout_outcome_is_quarantined_by_default() -> None:
    good = _run("t1", _doc({1: 1}))
    hung = _run("t2", _doc({1: 5}), outcome="timeout")
    result = merge_run_coverage([good, hung])
    (file,) = result.document.files
    assert file.lines[0].count == 1
    assert result.excluded[0].reason == "quarantined_outcome"


def test_explicit_admission_admits_quarantined_run() -> None:
    good = _run("t1", _doc({1: 3}))
    crashed = _run("t2", _doc({1: 9}), outcome="error")
    result = merge_run_coverage(
        [good, crashed],
        admissions={"t2": RunAdmission(test_id="t2", admitted=True, reason="operator-reviewed; crash after flush")},
    )
    (file,) = result.document.files
    assert file.lines[0].count == 12  # admitted: aggregate includes it
    assert result.excluded == ()


def test_explicit_denial_excludes_run() -> None:
    good = _run("t1", _doc({1: 3}))
    flaky = _run("t2", _doc({1: 1}), outcome="pass")
    result = merge_run_coverage(
        [good, flaky],
        admissions={"t2": RunAdmission(test_id="t2", admitted=False, reason="environment noise")},
    )
    (file,) = result.document.files
    assert file.lines[0].count == 3
    (excluded,) = result.excluded
    assert excluded.reason == "denied_by_admission"


def test_quarantined_run_stays_in_provenance() -> None:
    """verifies: §5.4 — per-run provenance still shows the quarantined profile."""
    good = _run("t1", _doc({1: 3}))
    crashed = _run("t2", _doc({1: 9}), outcome="error")
    result = merge_run_coverage([good, crashed])
    assert {run.test_id for run in result.per_run} == {"t1", "t2"}
    quarantined = next(run for run in result.per_run if run.test_id == "t2")
    assert quarantined.outcome == "error"
    assert quarantined.document is not None  # retained, not destroyed


# --- AC-5: fail-closed inputs ----------------------------------------------------


def test_unknown_completeness_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        RunCoverage(test_id="t1", outcome="pass", completeness="partial", advisory="x")
    assert exc_info.value.reason == "unknown_completeness"


def test_unknown_outcome_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        RunCoverage(test_id="t1", outcome="crashed", completeness="complete", document=_doc())
    assert exc_info.value.reason == "unknown_run_outcome"


def test_complete_run_without_document_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        RunCoverage(test_id="t1", outcome="pass", completeness="complete")
    assert exc_info.value.reason == "complete_run_without_document"


def test_missing_run_with_document_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        RunCoverage(test_id="t1", outcome="pass", completeness="missing", document=_doc(), advisory="x")
    assert exc_info.value.reason == "missing_run_with_document"


def test_incomplete_run_requires_advisory() -> None:
    with pytest.raises(CoverageError) as exc_info:
        RunCoverage(test_id="t1", outcome="pass", completeness="truncated", document=_doc())
    assert exc_info.value.reason == "advisory_required"


def test_merge_result_dict_is_deterministic() -> None:
    good = _run("t1", _doc({1: 3}))
    crashed = _run("t2", _doc({1: 9}), outcome="error")
    first = merge_run_coverage([good, crashed])
    second = merge_run_coverage([good, crashed])
    assert first.to_dict() == second.to_dict()
    assert isinstance(first.excluded[0], ExcludedRun)
