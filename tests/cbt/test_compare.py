# implements: TOOL-CBT-050, TOOL-CBT-060
"""Run comparison and coverage delta (WP-CBT-03).

Classification is by exact outcome transition over the S3 vocabulary with the
vocabulary checked up front; the coverage delta is exact integer arithmetic
with unmeasured sides reported as no change, never as zero.
"""

from __future__ import annotations

import json

import pytest

from ectt.cbt import (
    CoverageComparison,
    RunComparison,
    compare_coverage,
    compare_runs,
    run_outcomes,
)
from ectt.cov.metrics import MetricTotals
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")

BASELINE = {
    "tc.alpha": "pass",
    "tc.beta": "fail",
    "tc.gamma": "error",
    "tc.delta": "pass",
    "tc.gone": "timeout",
}
CURRENT = {
    "tc.alpha": "fail",  # newly failing
    "tc.beta": "pass",  # newly passing
    "tc.gamma": "error",  # unchanged non-verdict
    "tc.delta": "pass",  # unchanged pass
    "tc.fresh": "pass",  # newly added
    # tc.gone vanished -> removed
}


def test_newly_failing_is_a_pass_that_now_fails() -> None:
    """verifies: TOOL-CBT-050 — exact transition semantics; an error is not a
    verdict change."""
    comparison = compare_runs(BASELINE, CURRENT)
    assert comparison.newly_failing == ("tc.alpha",)


def test_newly_passing_is_a_fail_that_now_passes() -> None:
    """verifies: TOOL-CBT-050 — the reverse transition, exactly."""
    comparison = compare_runs(BASELINE, CURRENT)
    assert comparison.newly_passing == ("tc.beta",)


def test_newly_added_tests_are_listed() -> None:
    """verifies: TOOL-CBT-050 — a test absent from the baseline is newly added,
    whatever its outcome."""
    comparison = compare_runs(BASELINE, CURRENT)
    assert comparison.newly_added == ("tc.fresh",)


def test_removed_tests_are_surfaced_not_dropped() -> None:
    """verifies: AC-2 (derived) — a vanished test is named, never silent."""
    comparison = compare_runs(BASELINE, CURRENT)
    assert comparison.removed == ("tc.gone",)


def test_identical_runs_compare_empty() -> None:
    """verifies: TOOL-CBT-050 — the same run against itself is all empty."""
    comparison = compare_runs(BASELINE, BASELINE)
    assert comparison == RunComparison(newly_failing=(), newly_passing=(), newly_added=(), removed=())


def test_an_unknown_outcome_is_refused_by_name() -> None:
    """verifies: TOOL-CBT-050 — a typo'd outcome cannot misclassify."""
    with pytest.raises(ValueError) as excinfo:
        compare_runs({"tc.a": "passed"}, {"tc.a": "pass"})
    assert "baseline" in str(excinfo.value) and "passed" in str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        compare_runs({"tc.a": "pass"}, {"tc.a": "PASS"})
    assert "current" in str(excinfo.value)


def test_the_comparison_is_sorted_and_deterministic() -> None:
    """verifies: AC-5 — same inputs, same sorted document."""
    baseline = {"t.b": "pass", "t.a": "pass", "t.c": "pass"}
    current = {"t.a": "fail", "t.b": "fail", "t.c": "fail", "t.z": "pass", "t.a2": "pass"}
    first = compare_runs(baseline, current)
    second = compare_runs(dict(reversed(list(baseline.items()))), current)
    assert first == second
    assert first.newly_failing == ("t.a", "t.b", "t.c")
    assert first.newly_added == ("t.a2", "t.z")
    assert first.to_dict() == json.loads(json.dumps(first.to_dict()))


def test_run_outcomes_reads_a_result_set() -> None:
    """verifies: TOOL-CBT-050 — the outcome map comes straight from a run."""
    results = tuple(
        finalize_result(t, o, "d" * 64) for t, o in sorted({"tc.one": "pass", "tc.two": "error"}.items())
    )
    run = ResultSet(run_id="run-1", execution=EXECUTION, results=results)
    assert run_outcomes(run) == {"tc.one": "pass", "tc.two": "error"}


# --- the coverage delta -----------------------------------------------------------------------


def test_statement_delta_is_exact() -> None:
    """verifies: TOOL-CBT-060 — covered delta is exact integer arithmetic."""
    comparison = compare_coverage(
        {"statements": MetricTotals(covered=8, total=10)},
        {"statements": MetricTotals(covered=9, total=10)},
        metrics=("statements",),
    )
    (delta,) = comparison.deltas
    assert delta.metric == "statements"
    assert delta.change == 1
    assert delta.baseline is not None and delta.current is not None


def test_branch_delta_with_not_applicable_totals() -> None:
    """verifies: TOOL-CBT-060 — a not-applicable total (None) is carried, not
    treated as zero."""
    comparison = compare_coverage(
        {"branches": MetricTotals(covered=0, total=None)},
        {"branches": MetricTotals(covered=0, total=4)},
        metrics=("branches",),
    )
    (delta,) = comparison.deltas
    assert delta.change == 0
    assert delta.baseline is not None and delta.baseline.total is None
    assert delta.current is not None and delta.current.total == 4


def test_an_unmeasured_side_reports_no_change() -> None:
    """verifies: TOOL-CBT-060 — a metric absent on either side is unmeasured
    (change None), never a decrease or an increase."""
    comparison = compare_coverage(
        {"statements": MetricTotals(covered=8, total=10)},
        {"branches": MetricTotals(covered=3, total=4)},
    )
    by_metric = {d.metric: d for d in comparison.deltas}
    assert by_metric["statements"].change is None
    assert by_metric["branches"].change is None
    assert by_metric["statements"].baseline is not None and by_metric["statements"].current is None


def test_totals_travel_with_the_delta() -> None:
    """verifies: TOOL-CBT-060 — the document carries both runs' totals."""
    comparison: CoverageComparison = compare_coverage(
        {"statements": MetricTotals(covered=8, total=10), "branches": MetricTotals(covered=2, total=4)},
        {"statements": MetricTotals(covered=10, total=12), "branches": MetricTotals(covered=1, total=4)},
    )
    document = comparison.to_dict()
    assert document["deltas"][0]["baseline"] == {"covered": 8, "total": 10}
    assert document["deltas"][0]["current"] == {"covered": 10, "total": 12}
    assert document["deltas"][1]["change"] == -1


def test_the_comparison_document_is_deterministic() -> None:
    """verifies: AC-5 — same inputs, same document text."""
    baseline = {"statements": MetricTotals(covered=8, total=10), "branches": MetricTotals(covered=2, total=4)}
    current = {"statements": MetricTotals(covered=9, total=10), "branches": MetricTotals(covered=3, total=4)}
    first = compare_coverage(baseline, current)
    second = compare_coverage(dict(reversed(list(baseline.items()))), current)
    assert json.dumps(first.to_dict()) == json.dumps(second.to_dict())
    metrics = [d.metric for d in first.deltas]
    assert metrics == ["statements", "branches"]  # documented metric order
