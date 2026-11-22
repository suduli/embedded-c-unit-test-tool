# implements: TOOL-CBT-030, TOOL-CBT-050, TOOL-CBT-080, TOOL-TGT-130, TOOL-COV-130
"""Report views over re-execution, comparison, minimization, profile and
threshold data (B2).

Each view consumes only the narrow data classes from ectt.cbt, ectt.ext and
ectt.cov; every view is a pure function of its inputs (deterministic dicts).
The five function names are stable API for other lanes — see
docs/verification/WP-REP-views-analysis.md.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from ectt.cbt.compare import RunComparison, compare_coverage
from ectt.cbt.minimize import Minimization
from ectt.cbt.reexecute import SubsetReExecution
from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import MetricThreshold, ThresholdEvaluation, ThresholdResult
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.ext.profile import label_host_results, record_host_profile
from ectt.rep.errors import ReportModelError
from ectt.rep.views import (
    host_profile_view,
    minimized_suite_view,
    run_comparison_view,
    subset_run_view,
    threshold_view,
)


def _suite_view(partial: bool, not_executed: tuple[str, ...]) -> ResultSet:
    return ResultSet(
        run_id="run-sub",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(finalize_result("t.one", "pass", "d1" * 32),),
        partial=partial,
        not_executed=not_executed,
    )


def _subset(partial: bool, not_selected: tuple[str, ...], not_executed: tuple[str, ...] | None = None) -> SubsetReExecution:
    return SubsetReExecution(
        reexecution=None,  # type: ignore[arg-type]  # the view reads suite_view data only
        selected=("t.one",),
        not_selected=not_selected,
        suite_view=_suite_view(partial, not_executed if not_executed is not None else not_selected),
    )


# --- AC-1: subset run view --------------------------------------------------------


def test_subset_run_view_states_partiality_from_suite_view_data() -> None:
    """verifies: TOOL-CBT-040 — partiality is data, not prose."""
    view = subset_run_view(_subset(partial=True, not_selected=("t.two", "t.three")))
    assert view["view"] == "subset_run"
    assert view["partial"] is True
    assert view["not_selected"] == ["t.two", "t.three"]  # sorted by the producer
    assert view["not_executed"] == ["t.two", "t.three"]
    assert view["tests_total"] == 3
    assert view["tests_executed"] == 1
    assert view["outcomes"] == {"t.one": "pass"}


def test_subset_run_view_full_selection_is_not_partial() -> None:
    view = subset_run_view(_subset(partial=False, not_selected=()))
    assert view["partial"] is False
    assert view["not_executed"] == []


def test_subset_run_view_refuses_self_contradicting_data() -> None:
    """verifies: AC-1 — the view never contradicts its data."""
    with pytest.raises(ReportModelError) as exc_info:
        subset_run_view(_subset(partial=True, not_selected=()))
    assert exc_info.value.reason == "inconsistent_subset_view"
    with pytest.raises(ReportModelError) as exc_info:
        subset_run_view(_subset(partial=False, not_selected=("t.two",)))
    assert exc_info.value.reason == "inconsistent_subset_view"


# --- AC-2: run comparison view ------------------------------------------------------


def test_run_comparison_view_carries_transitions_removed_and_delta() -> None:
    comparison = RunComparison(
        newly_failing=("t.beta",),
        newly_passing=("t.alpha",),
        newly_added=("t.new",),
        removed=("t.gone",),
    )
    coverage = compare_coverage(
        {"statements": MetricTotals(covered=8, total=10), "branches": MetricTotals(covered=2, total=4)},
        {"statements": MetricTotals(covered=9, total=10)},
    )
    view = run_comparison_view(comparison, coverage)
    assert view["view"] == "run_comparison"
    assert view["removed"] == ["t.gone"]
    assert view["removed_count"] == 1
    deltas = {d["metric"]: d for d in view["coverage"]["deltas"]}
    assert deltas["statements"]["change"] == 1
    assert deltas["branches"]["change"] is None  # unmeasured stays unmeasured
    assert deltas["branches"]["current"] is None


def test_run_comparison_view_without_coverage_is_deterministic() -> None:
    comparison = RunComparison(newly_failing=(), newly_passing=(), newly_added=("t.a",), removed=("t.b",))
    view = run_comparison_view(comparison)
    assert "coverage" not in view
    assert view == run_comparison_view(comparison)


# --- AC-3: minimized suite view ------------------------------------------------------


def test_minimized_suite_view_shows_kept_redundant_and_union() -> None:
    """verifies: TOOL-CBT-080 — kept versus redundant and the preserved union."""
    minimization = Minimization(kept=("t.a", "t.b"), redundant=("t.c",))
    coverage = {
        "t.a": {"s1", "s2"},
        "t.b": {"s3"},
        "t.c": {"s2"},
    }
    view = minimized_suite_view(minimization, coverage)
    assert view["view"] == "minimized_suite"
    assert view["kept"] == ["t.a", "t.b"]
    assert view["redundant"] == ["t.c"]
    assert view["preserved_union"] == ["s1", "s2", "s3"]
    assert view["preserved_construct_count"] == 3


def test_minimized_suite_view_refuses_stale_minimization() -> None:
    """verifies: AC-3 — a minimization that no longer preserves coverage is refused."""
    stale = Minimization(kept=("t.a",), redundant=("t.b", "t.c"))
    coverage = {"t.a": {"s1"}, "t.b": {"s2"}, "t.c": {"s3"}}
    with pytest.raises(ReportModelError) as exc_info:
        minimized_suite_view(stale, coverage)
    assert exc_info.value.reason == "stale_minimization"
    with pytest.raises(ReportModelError) as exc_info:
        minimized_suite_view(Minimization(kept=("t.ghost",), redundant=()), {"t.a": {"s1"}})
    assert exc_info.value.reason == "stale_minimization"


# --- AC-4: host profile view ---------------------------------------------------------


def test_host_profile_view_labels_every_result() -> None:
    """verifies: TOOL-TGT-130 — the profile label rides beside every result."""
    profile = record_host_profile(
        name="linux-x86-proxy",
        target_triple="arm-none-eabi",
        host_triple="x86_64-linux-gnu",
        unavailable_hardware_behavior="the access is diagnosed and the test fails",
    )
    result_set = ResultSet(
        run_id="run-host",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(finalize_result("t.one", "pass", "d1" * 32), finalize_result("t.two", "error", "d2" * 32)),
    )
    labelled = label_host_results(profile, result_set)
    view = host_profile_view(labelled)
    assert view["view"] == "host_profile"
    assert view["profile_id"] == profile.profile_id
    assert view["profile_label"] == profile.label
    assert [r["test_id"] for r in view["results"]] == ["t.one", "t.two"]
    assert all(r["profile_id"] == profile.profile_id for r in view["results"])
    assert {r["test_id"]: r["outcome"] for r in view["results"]} == {"t.one": "pass", "t.two": "error"}


def test_host_profile_view_refuses_label_result_mismatch() -> None:
    profile = record_host_profile(
        name="linux-x86-proxy",
        target_triple="arm-none-eabi",
        host_triple="x86_64-linux-gnu",
        unavailable_hardware_behavior="the access is diagnosed and the test fails",
    )
    result_set = ResultSet(
        run_id="run-host",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(finalize_result("t.one", "pass", "d1" * 32),),
    )
    labelled = label_host_results(profile, result_set)
    broken = type(labelled)(profile=profile, result_set=result_set, labels=labelled.labels[:0])
    with pytest.raises(ReportModelError) as exc_info:
        host_profile_view(broken)
    assert exc_info.value.reason == "label_result_mismatch"


def test_host_profile_view_labels_sort_deterministically() -> None:
    profile = record_host_profile(
        name="linux-x86-proxy",
        target_triple="arm-none-eabi",
        host_triple="x86_64-linux-gnu",
        unavailable_hardware_behavior="the access is diagnosed and the test fails",
    )
    result_set = ResultSet(
        run_id="run-host",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(
            finalize_result("t.z", "pass", "dz" * 32),
            finalize_result("t.a", "pass", "da" * 32),
        ),
    )
    labelled = label_host_results(profile, result_set)
    view = host_profile_view(labelled)
    assert [r["test_id"] for r in view["results"]] == ["t.a", "t.z"]
    assert view == host_profile_view(labelled)


# --- AC-5: threshold view, no_data shown as a failure ---------------------------------


def _threshold_result(*states: tuple[str, str, int, int | None]) -> ThresholdResult:
    evaluations = tuple(
        ThresholdEvaluation(
            metric=metric,
            state=state,
            covered=covered,
            total=total,
            minimum=Fraction(4, 5),
        )
        for metric, state, covered, total in states
    )
    passed = all(e.state in ("pass", "not_applicable") for e in evaluations)
    return ThresholdResult(evaluations=evaluations, passed=passed)


def test_threshold_view_shows_no_data_as_a_failure() -> None:
    """verifies: TOOL-COV-130 — the new no_data state is displayed as a failure."""
    result = _threshold_result(
        ("statements", "pass", 9, 10),
        ("branches", "no_data", 0, None),
    )
    view = threshold_view(result)
    assert view["view"] == "thresholds"
    assert view["passed"] is False
    assert view["no_data_metrics"] == ["branches"]
    by_metric = {e["metric"]: e for e in view["evaluations"]}
    assert by_metric["branches"]["state"] == "no_data"  # recorded state travels verbatim
    assert by_metric["branches"]["displayed"] == "fail"  # displayed as a failure
    assert by_metric["statements"]["displayed"] == "pass"


def test_threshold_view_not_applicable_displays_exempt() -> None:
    result = _threshold_result(("statements", "not_applicable", 0, 0))
    view = threshold_view(result)
    assert view["passed"] is True
    assert view["evaluations"][0]["displayed"] == "exempt"
    assert view["no_data_metrics"] == []


def test_threshold_view_refuses_unknown_state() -> None:
    """verifies: AC-5 — an unknown recorded state is refused, never rendered."""
    bogus = ThresholdResult(
        evaluations=(
            ThresholdEvaluation(metric="statements", state="maybe", covered=1, total=2,
                                minimum=Fraction(1, 2)),
        ),
        passed=False,
    )
    with pytest.raises(ReportModelError) as exc_info:
        threshold_view(bogus)
    assert exc_info.value.reason == "unknown_threshold_state"


def test_threshold_view_matches_metric_threshold_rejection_vocabulary() -> None:
    """The view is fed by the real enforcement path, not by hand-built states:
    an unallowed empty metric is no_data and displayed as a failure; an allowed
    one is not_applicable and displayed as exempt."""
    from ectt.cov.thresholds import enforce_thresholds

    result = enforce_thresholds(
        {"statements": MetricTotals(covered=4, total=4), "branches": MetricTotals(covered=0, total=None)},
        [MetricThreshold(metric="statements", minimum=Fraction(4, 5)),
         MetricThreshold(metric="branches", minimum=Fraction(1, 2))],
    )
    view = threshold_view(result)
    assert view["passed"] is False  # branches is no_data and fails the run
    assert view["no_data_metrics"] == ["branches"]
    assert view["evaluations"][1]["state"] == "no_data"
    assert view["evaluations"][1]["displayed"] == "fail"

    allowed = enforce_thresholds(
        {"statements": MetricTotals(covered=4, total=4), "branches": MetricTotals(covered=0, total=None)},
        [MetricThreshold(metric="statements", minimum=Fraction(4, 5)),
         MetricThreshold(metric="branches", minimum=Fraction(1, 2))],
        allow_not_applicable=("branches",),
    )
    allowed_view = threshold_view(allowed)
    assert allowed_view["passed"] is True  # not_applicable does not fail
    assert allowed_view["evaluations"][1]["state"] == "not_applicable"
    assert allowed_view["evaluations"][1]["displayed"] == "exempt"
