# implements: TOOL-COV-130
"""Seeded property-style tests over coverage thresholds (B8).

Tests only; no src/ edits. Metric totals are generated from fixed seeds
(``random.Random(SEED)``) so a failure reproduces exactly; no wall clock.
Properties, not snapshots:

- the verdict matches an independently computed comparison of the exact
  covered/total fraction against the minimum, for every random draw;
- boundary values sit exactly on the pass/fail edge (equal passes);
- an empty metric records no_data and fails unless explicitly allowed;
- the evaluation's recorded values (covered, total, minimum) are the inputs,
  never recomputed or rounded.
"""

from __future__ import annotations

import random
from fractions import Fraction

from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import MetricThreshold, enforce_thresholds

SEED = 20261122


def _expected_state(totals: MetricTotals, minimum: Fraction, allowed: bool) -> str:
    """The property the threshold evaluation must satisfy, computed independently."""
    if totals.total is None or totals.total == 0:
        return "not_applicable" if allowed else "no_data"
    covered_fraction = Fraction(totals.covered, totals.total)
    if covered_fraction >= minimum:
        return "pass"
    return "fail"


def _expected_passed(state: str) -> bool:
    return state in ("pass", "not_applicable")


def test_threshold_verdict_matches_exact_comparison_over_seeded_totals() -> None:
    rng = random.Random(SEED)
    minimum = Fraction(3, 4)
    threshold = MetricThreshold(metric="statements", minimum=minimum)
    mismatches = 0
    for round_index in range(200):
        covered = rng.randint(0, 40)
        total = rng.randint(1, 40)
        totals = MetricTotals(covered=covered, total=total)
        result = enforce_thresholds({"statements": totals}, [threshold])
        (evaluation,) = result.evaluations
        expected = _expected_state(totals, minimum, allowed=False)
        assert evaluation.state == expected, (round_index, covered, total)
        assert result.passed == _expected_passed(expected), (round_index, covered, total)
        # recorded values are the inputs, never recomputed
        assert (evaluation.covered, evaluation.total) == (covered, total)
        if expected == "fail":
            mismatches += 1
    assert mismatches > 0  # the draw exercised failing cases, not only passes


def test_boundary_value_sits_exactly_on_the_edge() -> None:
    """A metric exactly at its minimum passes; one unit below fails."""
    minimum = Fraction(3, 4)
    threshold = MetricThreshold(metric="statements", minimum=minimum)
    at_edge = MetricTotals(covered=3, total=4)
    below_edge = MetricTotals(covered=2, total=4)
    (at,) = enforce_thresholds({"statements": at_edge}, [threshold]).evaluations
    (below,) = enforce_thresholds({"statements": below_edge}, [threshold]).evaluations
    assert at.state == "pass"
    assert below.state == "fail"


def test_boundary_exactness_across_seeded_equivalent_fractions() -> None:
    """covered/total equal to the minimum in lowest terms still passes."""
    rng = random.Random(SEED + 1)
    threshold = MetricThreshold(metric="statements", minimum=Fraction(1, 2))
    for round_index in range(50):
        total = rng.randint(1, 30)
        totals = MetricTotals(covered=total, total=total * 2)  # exactly 1/2
        (evaluation,) = enforce_thresholds({"statements": totals}, [threshold]).evaluations
        assert evaluation.state == "pass", (round_index, total, total * 2)


def test_no_data_fails_unless_allowed_over_seeded_draws() -> None:
    rng = random.Random(SEED + 2)
    for _round_index in range(30):
        allowed = rng.random() < 0.5
        result = enforce_thresholds(
            {"statements": MetricTotals(covered=0, total=None)},
            [MetricThreshold(metric="statements", minimum=Fraction(1, 2))],
            allow_not_applicable=("statements",) if allowed else (),
        )
        (evaluation,) = result.evaluations
        assert evaluation.state == _expected_state(MetricTotals(0, None), Fraction(1, 2), allowed)
        assert result.passed == _expected_passed(evaluation.state)


def test_evaluation_dict_round_trips_the_minimum_exactly() -> None:
    """The recorded minimum is the exact configured fraction, serialized 'n/d'."""
    threshold = MetricThreshold(metric="statements", minimum=Fraction(17, 20))
    (evaluation,) = enforce_thresholds(
        {"statements": MetricTotals(covered=17, total=20)}, [threshold]
    ).evaluations
    assert evaluation.to_dict()["minimum"] == "17/20"
    assert evaluation.minimum == Fraction(17, 20)
