# implements: TOOL-COV-130
"""Configurable minimum coverage thresholds per metric (CMP-COV).

Satisfies: TOOL-COV-130 — enforce configurable minimum coverage thresholds per
metric and fail the run when they are not met.

Thresholds are exact fractions (``fractions.Fraction``) in the unit interval —
never floats. Only configured metrics are enforced; a configured metric whose
totals are not applicable (no statements or no branches) records state
``not_applicable`` explicitly and does not fail the run. The overall ``passed``
flag is what the run-level caller turns into a run failure.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from ectt.cov.errors import CoverageError
from ectt.cov.model import MetricTotals

__all__ = [
    "THRESHOLD_METRICS",
    "MetricThreshold",
    "ThresholdEvaluation",
    "ThresholdResult",
    "enforce_thresholds",
]

#: Metrics a threshold may be configured for.
THRESHOLD_METRICS: tuple[str, ...] = ("statements", "branches")


@dataclass(frozen=True)
class MetricThreshold:
    """One configured minimum for one metric, as an exact fraction."""

    metric: str
    minimum: Fraction

    def __post_init__(self) -> None:
        if self.metric not in THRESHOLD_METRICS:
            raise CoverageError(
                f"unknown coverage metric '{self.metric}' (known: {', '.join(THRESHOLD_METRICS)})",
                reason="unknown_metric",
            )
        if not isinstance(self.minimum, Fraction):
            raise CoverageError(
                f"threshold minimum for '{self.metric}' must be a Fraction, "
                f"got {type(self.minimum).__name__}",
                reason="invalid_minimum_type",
            )
        if self.minimum < 0 or self.minimum > 1:
            raise CoverageError(
                f"threshold minimum for '{self.metric}' must be within 0..1, got {self.minimum}",
                reason="minimum_out_of_range",
            )


@dataclass(frozen=True)
class ThresholdEvaluation:
    """One metric's threshold outcome, recorded exactly."""

    metric: str
    state: str  # "pass" | "fail" | "not_applicable"
    covered: int
    total: int | None
    minimum: Fraction

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "state": self.state,
            "covered": self.covered,
            "total": self.total,
            "minimum": f"{self.minimum.numerator}/{self.minimum.denominator}",
        }


@dataclass(frozen=True)
class ThresholdResult:
    """All evaluations in configured order, plus the run-level verdict."""

    evaluations: tuple[ThresholdEvaluation, ...]
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "passed": self.passed,
            "evaluations": [e.to_dict() for e in self.evaluations],
        }


def enforce_thresholds(
    metrics: Mapping[str, MetricTotals],
    thresholds: Sequence[MetricThreshold],
) -> ThresholdResult:
    """Evaluate configured thresholds against metric totals (TOOL-COV-130).

    A metric whose totals are not applicable (``total`` is ``None`` or ``0``)
    records ``not_applicable`` and does not fail the run. Otherwise the metric
    passes iff its exact covered/total fraction is >= the configured minimum.
    """
    evaluations: list[ThresholdEvaluation] = []
    passed = True
    for threshold in thresholds:
        totals = metrics.get(threshold.metric)
        if totals is None:
            raise CoverageError(
                f"no metric totals supplied for configured metric '{threshold.metric}'",
                reason="missing_metric_totals",
            )
        if totals.total is None or totals.total == 0:
            evaluations.append(
                ThresholdEvaluation(
                    metric=threshold.metric,
                    state="not_applicable",
                    covered=totals.covered,
                    total=totals.total,
                    minimum=threshold.minimum,
                )
            )
            continue
        value = Fraction(totals.covered, totals.total)
        state = "pass" if value >= threshold.minimum else "fail"
        if state == "fail":
            passed = False
        evaluations.append(
            ThresholdEvaluation(
                metric=threshold.metric,
                state=state,
                covered=totals.covered,
                total=totals.total,
                minimum=threshold.minimum,
            )
        )
    return ThresholdResult(evaluations=tuple(evaluations), passed=passed)
