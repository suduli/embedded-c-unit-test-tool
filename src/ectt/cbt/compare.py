# implements: TOOL-CBT-050, TOOL-CBT-060
"""Run comparison and coverage delta (WP-CBT-03).

**Run comparison (TOOL-CBT-050).** One run against a previous one, classified by
exact outcome transitions over the S3 vocabulary (`pass | fail | error | timeout |
not_run`, ectt.exh): *newly failing* passed in the baseline and fails now, *newly
passing* failed in the baseline and passes now, *newly added* exists only in the
current run. A test that vanished since the baseline is reported as *removed* —
surfaced, never silently dropped (flagged as derived: the requirement names three
categories, this package adds the anti-loss fourth). An `error` is neither newly
failing nor newly passing: it is not a verdict change. Unknown outcomes are refused
with a named reason before anything is classified.

**Coverage delta (TOOL-CBT-060).** Coverage change relative to a baseline run, per
metric, as exact integer arithmetic over `ectt.cov.metrics.MetricTotals` (the unit
the coverage engine produces); both runs' totals travel with the delta for the
report. A metric absent from either side is **unmeasured** and its change is `None`:
unmeasured is never reported as a decrease or an increase.

Both are pure functions of plain data (outcome maps; per-metric totals) — the
composition wires the run records and the coverage engine in.

Satisfies: TOOL-CBT-050, TOOL-CBT-060.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ectt.cov.metrics import MetricTotals
from ectt.exh.results import ResultSet

__all__ = [
    "RUN_OUTCOMES",
    "CoverageComparison",
    "MetricDelta",
    "RunComparison",
    "compare_coverage",
    "compare_runs",
    "run_outcomes",
]

#: The S3 per-test outcome vocabulary (ectt.exh.results).
RUN_OUTCOMES: tuple[str, ...] = ("pass", "fail", "error", "timeout", "not_run")


@dataclass(frozen=True)
class RunComparison:
    """One run against a baseline, by exact outcome transition (TOOL-CBT-050)."""

    newly_failing: tuple[str, ...]
    newly_passing: tuple[str, ...]
    newly_added: tuple[str, ...]
    #: Present in the baseline, absent from the current run (derived, surfaced).
    removed: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "newly_added": list(self.newly_added),
            "newly_failing": list(self.newly_failing),
            "newly_passing": list(self.newly_passing),
            "removed": list(self.removed),
        }


def run_outcomes(run: ResultSet) -> dict[str, str]:
    """The outcome map of one executed run (``test_id -> outcome``)."""
    return {record.test_id: record.outcome for record in run.results}


def _checked_outcomes(outcomes: Mapping[str, str], *, which: str) -> None:
    for test_id, outcome in outcomes.items():
        if outcome not in RUN_OUTCOMES:
            raise ValueError(
                f"{which} run outcome for '{test_id}' is '{outcome}', "
                f"not one of {', '.join(RUN_OUTCOMES)}"
            )


def compare_runs(baseline: Mapping[str, str], current: Mapping[str, str]) -> RunComparison:
    """Compare a current run against a baseline run, sorted and deterministic.

    Both maps are ``test_id -> outcome`` in the S3 vocabulary; anything else is
    refused before classification (a typo must not read as a verdict change).
    """
    _checked_outcomes(baseline, which="baseline")
    _checked_outcomes(current, which="current")
    shared = sorted(set(baseline) & set(current))
    return RunComparison(
        newly_failing=tuple(t for t in shared if baseline[t] == "pass" and current[t] == "fail"),
        newly_passing=tuple(t for t in shared if baseline[t] == "fail" and current[t] == "pass"),
        newly_added=tuple(sorted(set(current) - set(baseline))),
        removed=tuple(sorted(set(baseline) - set(current))),
    )


@dataclass(frozen=True)
class MetricDelta:
    """One metric's coverage change against the baseline (TOOL-CBT-060).

    ``change`` is exact integer arithmetic (current minus baseline covered);
    ``None`` when either side is unmeasured — unmeasured is never read as a
    delta of zero.
    """

    metric: str
    baseline: MetricTotals | None
    current: MetricTotals | None

    @property
    def change(self) -> int | None:
        if self.baseline is None or self.current is None:
            return None
        return self.current.covered - self.baseline.covered

    def to_dict(self) -> dict[str, Any]:
        def side(totals: MetricTotals | None) -> dict[str, Any] | None:
            if totals is None:
                return None
            return {"covered": totals.covered, "total": totals.total}

        return {
            "baseline": side(self.baseline),
            "change": self.change,
            "current": side(self.current),
            "metric": self.metric,
        }


@dataclass(frozen=True)
class CoverageComparison:
    """Per-metric coverage change of one run against a baseline (TOOL-CBT-060)."""

    deltas: tuple[MetricDelta, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"deltas": [delta.to_dict() for delta in self.deltas]}


def compare_coverage(
    baseline: Mapping[str, MetricTotals],
    current: Mapping[str, MetricTotals],
    *,
    metrics: tuple[str, ...] = ("statements", "branches"),
) -> CoverageComparison:
    """Coverage change per metric, exact, deterministic; unmeasured stays unmeasured.

    Both maps key metric names to that metric's totals for the run; a metric
    absent from either side is unmeasured (change ``None``), never zero.
    """
    return CoverageComparison(
        deltas=tuple(
            MetricDelta(metric=metric, baseline=baseline.get(metric), current=current.get(metric))
            for metric in metrics
        )
    )
