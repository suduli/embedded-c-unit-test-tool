# implements: TOOL-CBT-030, TOOL-CBT-050, TOOL-CBT-080, TOOL-COV-130
"""Seeded property-style tests through the new rep views (B8).

Tests only; no src/ edits. Run sets and coverage mappings are generated from
fixed seeds (``random.Random(SEED)``) so a failure reproduces exactly; no
wall clock. Properties, not snapshots:

- subset_run_view: the view's counts and partitions are internally consistent
  with the suite_view data for every random partition;
- run_comparison_view: the view carries the comparison verbatim and the
  removed count equals len(removed) for every random outcome map pair;
- minimized_suite_view: for every random coverage mapping and its own
  minimization, the view's preserved union equals the full union, and a
  mutated (stale) minimization is refused;
- threshold_view: whatever the random draw, no_data is displayed as a failure
  and passed mirrors the real enforcement verdict.
"""

from __future__ import annotations

import random
from fractions import Fraction

import pytest

from ectt.cbt.compare import compare_coverage, compare_runs
from ectt.cbt.minimize import minimize_suite
from ectt.cbt.reexecute import SubsetReExecution
from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import MetricThreshold, enforce_thresholds
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.rep.errors import ReportModelError
from ectt.rep.views import (
    minimized_suite_view,
    run_comparison_view,
    subset_run_view,
    threshold_view,
)

SEED = 20261122
_OUTCOMES = ("pass", "fail", "error", "timeout", "not_run")


def _seeded_suite_view(rng: random.Random, n_tests: int, n_selected: int) -> SubsetReExecution:
    all_ids = [f"t.{i:03d}" for i in range(n_tests)]
    selected = sorted(rng.sample(all_ids, n_selected))
    not_selected = tuple(sorted(set(all_ids) - set(selected)))
    # fail requires assertion failures, so the executed outcomes draw from the
    # failure-free pair (pass, error)
    results = tuple(
        finalize_result(test_id, rng.choice(("pass", "error")), f"d{i}" * 32)
        for i, test_id in enumerate(selected)
    )
    suite_view = ResultSet(
        run_id="run-sub",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=results,
        partial=bool(not_selected),
        not_executed=not_selected,
    )
    return SubsetReExecution(
        reexecution=None,  # type: ignore[arg-type]  # the view reads suite_view data only
        selected=tuple(selected),
        not_selected=not_selected,
        suite_view=suite_view,
    )


def test_subset_view_partition_is_consistent_over_seeded_draws() -> None:
    rng = random.Random(SEED)
    for _round_index in range(30):
        n_selected = rng.randint(1, 6)
        subset = _seeded_suite_view(rng, 8, n_selected)
        view = subset_run_view(subset)
        assert view["partial"] == bool(subset.not_selected)
        assert view["tests_total"] == 8
        assert view["tests_executed"] == len(subset.suite_view.results)
        assert sorted(view["selected"] + view["not_selected"]) == [f"t.{i:03d}" for i in range(8)]
        assert set(view["not_executed"]) == set(subset.not_selected)


def test_comparison_view_carries_random_transitions_verbatim() -> None:
    rng = random.Random(SEED + 1)
    for _round_index in range(30):
        baseline = {f"t.{i}": rng.choice(_OUTCOMES) for i in range(rng.randint(1, 8))}
        current = {f"t.{i}": rng.choice(_OUTCOMES) for i in range(rng.randint(1, 8))}
        comparison = compare_runs(baseline, current)
        coverage = compare_coverage(
            {"statements": MetricTotals(covered=rng.randint(0, 10), total=10)},
            {"statements": MetricTotals(covered=rng.randint(0, 10), total=10)},
        )
        view = run_comparison_view(comparison, coverage)
        assert view["newly_failing"] == list(comparison.newly_failing)
        assert view["newly_passing"] == list(comparison.newly_passing)
        assert view["newly_added"] == list(comparison.newly_added)
        assert view["removed"] == list(comparison.removed)
        assert view["removed_count"] == len(comparison.removed)
        deltas = {d["metric"]: d for d in view["coverage"]["deltas"]}
        delta = deltas["statements"]
        assert delta["change"] == delta["current"]["covered"] - delta["baseline"]["covered"]
        assert deltas["branches"]["current"] is None  # unmeasured stays unmeasured


def test_minimized_view_preserves_the_union_over_seeded_mappings() -> None:
    rng = random.Random(SEED + 2)
    for _round_index in range(30):
        constructs = [f"s{i}" for i in range(rng.randint(2, 10))]
        coverage = {
            f"t.{i}": set(rng.sample(constructs, rng.randint(1, len(constructs))))
            for i in range(rng.randint(2, 6))
        }
        minimization = minimize_suite(coverage)
        view = minimized_suite_view(minimization, coverage)
        full_union = sorted({c for covered in coverage.values() for c in covered})
        assert view["preserved_union"] == full_union
        assert view["kept_count"] == len(minimization.kept)
        assert view["redundant_count"] == len(minimization.redundant)
        assert sorted(view["kept"] + view["redundant"]) == sorted(coverage)
        # a stale minimization (one kept test removed) is refused
        if len(minimization.kept) > 1:
            stale = type(minimization)(kept=minimization.kept[1:], redundant=minimization.redundant)
            with pytest.raises(ReportModelError) as exc_info:
                minimized_suite_view(stale, coverage)
            assert exc_info.value.reason == "stale_minimization"


def test_threshold_view_no_data_displayed_as_failure_over_seeded_draws() -> None:
    rng = random.Random(SEED + 3)
    minimum = Fraction(1, 2)
    threshold = MetricThreshold(metric="statements", minimum=minimum)
    for _round_index in range(50):
        covered = rng.randint(0, 20)
        total = rng.randint(1, 20)
        result = enforce_thresholds(
            {"statements": MetricTotals(covered=covered, total=total),
             "branches": MetricTotals(covered=0, total=None)},
            [threshold, MetricThreshold(metric="branches", minimum=minimum)],
            allow_not_applicable=("branches",) if rng.random() < 0.5 else (),
        )
        view = threshold_view(result)
        assert view["passed"] == result.passed
        by_metric = {e["metric"]: e for e in view["evaluations"]}
        assert by_metric["branches"]["displayed"] in ("fail", "exempt")
        if by_metric["branches"]["state"] == "no_data":
            assert by_metric["branches"]["displayed"] == "fail"
            assert result.passed is False
        statements_expected = "pass" if Fraction(covered, total) >= minimum else "fail"
        assert by_metric["statements"]["displayed"] == statements_expected
