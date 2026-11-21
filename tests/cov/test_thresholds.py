# implements: TOOL-COV-130
"""Coverage threshold enforcement (WP-COV-03)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from ectt.cov.errors import CoverageError
from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import MetricThreshold, ThresholdResult, enforce_thresholds


def test_metric_below_threshold_fails() -> None:
    """verifies: TOOL-COV-130 — a metric below its minimum fails with exact values."""
    result = enforce_thresholds(
        {"statements": MetricTotals(covered=3, total=4)},
        [MetricThreshold(metric="statements", minimum=Fraction(4, 5))],
    )
    assert result.passed is False
    (evaluation,) = result.evaluations
    assert evaluation.state == "fail"
    assert evaluation.covered == 3 and evaluation.total == 4


def test_metric_at_threshold_passes() -> None:
    result = enforce_thresholds(
        {"statements": MetricTotals(covered=4, total=5)},
        [MetricThreshold(metric="statements", minimum=Fraction(4, 5))],
    )
    assert result.passed is True
    assert result.evaluations[0].state == "pass"


def test_metric_above_threshold_passes() -> None:
    result = enforce_thresholds(
        {"branches": MetricTotals(covered=9, total=10)},
        [MetricThreshold(metric="branches", minimum=Fraction(4, 5))],
    )
    assert result.passed is True


def test_overall_passed_is_false_when_any_metric_fails() -> None:
    result = enforce_thresholds(
        {
            "statements": MetricTotals(covered=10, total=10),
            "branches": MetricTotals(covered=1, total=3),
        },
        [
            MetricThreshold(metric="statements", minimum=Fraction(1, 1)),
            MetricThreshold(metric="branches", minimum=Fraction(1, 2)),
        ],
    )
    assert result.passed is False
    assert [e.state for e in result.evaluations] == ["pass", "fail"]


def test_unconfigured_metric_is_not_enforced() -> None:
    """Only configured metrics are evaluated; a configured metric without
    totals is a caller error (named), never a silent skip."""
    result = enforce_thresholds(
        {
            "statements": MetricTotals(covered=0, total=10),
            "branches": MetricTotals(covered=4, total=4),
        },
        [MetricThreshold(metric="branches", minimum=Fraction(1, 1))],
    )
    assert result.passed is True
    assert [e.metric for e in result.evaluations] == ["branches"]
    assert result.evaluations[0].state == "pass"


def test_configured_metric_without_totals_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        enforce_thresholds(
            {"statements": MetricTotals(covered=0, total=10)},
            [MetricThreshold(metric="branches", minimum=Fraction(1, 1))],
        )
    assert exc_info.value.reason == "missing_metric_totals"


def test_not_applicable_metric_does_not_fail() -> None:
    """A configured metric with no data records not_applicable, never a fabricated fail."""
    result = enforce_thresholds(
        {
            "statements": MetricTotals(covered=0, total=0),
            "branches": MetricTotals(covered=0, total=None),
        },
        [
            MetricThreshold(metric="statements", minimum=Fraction(1, 1)),
            MetricThreshold(metric="branches", minimum=Fraction(1, 1)),
        ],
    )
    assert result.passed is True
    assert [e.state for e in result.evaluations] == ["not_applicable", "not_applicable"]


def test_unknown_metric_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        MetricThreshold(metric="conditions", minimum=Fraction(1, 2))
    assert exc_info.value.reason == "unknown_metric"


def test_minimum_outside_unit_interval_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        MetricThreshold(metric="statements", minimum=Fraction(3, 2))
    assert exc_info.value.reason == "minimum_out_of_range"
    with pytest.raises(CoverageError) as exc_info:
        MetricThreshold(metric="statements", minimum=Fraction(-1, 10))
    assert exc_info.value.reason == "minimum_out_of_range"


def test_non_fraction_minimum_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        MetricThreshold(metric="statements", minimum=0.8)  # type: ignore[arg-type]
    assert exc_info.value.reason == "invalid_minimum_type"


def test_missing_metric_totals_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        enforce_thresholds({}, [MetricThreshold(metric="statements", minimum=Fraction(1, 2))])
    assert exc_info.value.reason == "missing_metric_totals"


def test_evaluation_dict_is_canonical_and_ordered() -> None:
    result = enforce_thresholds(
        {
            "statements": MetricTotals(covered=4, total=5),
            "branches": MetricTotals(covered=3, total=4),
        },
        [
            MetricThreshold(metric="statements", minimum=Fraction(3, 4)),
            MetricThreshold(metric="branches", minimum=Fraction(1, 2)),
        ],
    )
    assert isinstance(result, ThresholdResult)
    dumped = result.to_dict()
    assert [e["metric"] for e in dumped["evaluations"]] == ["statements", "branches"]
    assert dumped["evaluations"][0]["minimum"] == "3/4"
    assert dumped["passed"] is True
