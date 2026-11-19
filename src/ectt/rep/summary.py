# implements: TOOL-REP-110, TOOL-REP-120
"""Cross-run summary and coverage trend over report models (WP-REP-08).

Both aggregations consume only the persisted report model's accessors
(``test_statuses``, ``coverage_figures``, ``provenance_facts``), so they
inherit the single-model guarantees: no aggregator re-derives a status or a
figure, and every output is a pure, deterministic function of the model
contents (runs are ordered by their recorded facts, never by wall-clock
observation time).

- Cross-run summary (TOOL-REP-110): aggregates results across multiple
  units, targets, and toolchains — the three partitions the requirement
  names are carried distinctly, plus the aggregated status totals.
- Coverage trend (TOOL-REP-120): orders successive runs by their recorded
  ``generated_at`` (ties broken by run id) and records each unit's figures
  per run; a unit absent from a run simply has no entry there.

Satisfies: TOOL-REP-110, TOOL-REP-120.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ectt.core.determinism import canonical_json
from ectt.rep.errors import ReportModelError
from ectt.rep.model import ReportModel

__all__ = [
    "CoverageTrend",
    "RunSummary",
    "TrendPoint",
    "build_coverage_trend",
    "build_cross_run_summary",
    "cross_run_summary_to_dict",
    "coverage_trend_to_dict",
]

_UNKNOWN = "unknown"


@dataclass(frozen=True)
class RunSummary:
    """One run's aggregated facts inside a cross-run summary."""

    run_id: str
    report_id: str
    where: str
    toolchain: str
    target_id: str | None
    tests: int
    status_counts: dict[str, int]
    coverage: dict[str, tuple[int, int]]
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "coverage": {unit: list(figures) for unit, figures in self.coverage.items()},
            "generated_at": self.generated_at,
            "report_id": self.report_id,
            "run_id": self.run_id,
            "status_counts": dict(self.status_counts),
            "target_id": self.target_id,
            "tests": self.tests,
            "toolchain": self.toolchain,
            "where": self.where,
        }


@dataclass(frozen=True)
class CrossRunSummary:
    """Aggregated results across multiple units, targets, and toolchains."""

    runs: tuple[RunSummary, ...]  # ordered by run id
    status_totals: dict[str, int]
    tests_total: int
    toolchains: tuple[str, ...]
    targets: tuple[str, ...]
    units: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "runs": [run.to_dict() for run in self.runs],
            "status_totals": dict(self.status_totals),
            "targets": list(self.targets),
            "tests_total": self.tests_total,
            "toolchains": list(self.toolchains),
            "units": list(self.units),
        }


@dataclass(frozen=True)
class TrendPoint:
    """One run's overall coverage figures inside a trend."""

    run_id: str
    generated_at: str
    covered: int
    total: int

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "covered": self.covered,
            "generated_at": self.generated_at,
            "run_id": self.run_id,
            "total": self.total,
        }


@dataclass(frozen=True)
class CoverageTrend:
    """Coverage across successive runs, ordered oldest first."""

    points: tuple[TrendPoint, ...]
    unit_series: dict[str, tuple[tuple[str, int, int], ...]]  # unit -> (run_id, covered, total)

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "points": [point.to_dict() for point in self.points],
            "unit_series": {
                unit: [list(entry) for entry in series]
                for unit, series in sorted(self.unit_series.items())
            },
        }


def _checked(models: Iterable[ReportModel]) -> list[ReportModel]:
    seen: set[str] = set()
    checked: list[ReportModel] = []
    for model in models:
        if not isinstance(model, ReportModel):
            raise TypeError(f"Expected ReportModel, got {type(model).__name__}")
        if model.run_id in seen:
            raise ReportModelError(f"duplicate run id in aggregation: '{model.run_id}'", reason="duplicate_run")
        seen.add(model.run_id)
        checked.append(model)
    return checked


def _status_counts(model: ReportModel) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in model.test_statuses().values():
        counts[status] = counts.get(status, 0) + 1
    return counts


def _totals(per_run: list[dict[str, int]]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for counts in per_run:
        for status, count in counts.items():
            totals[status] = totals.get(status, 0) + count
    return totals


def build_cross_run_summary(models: Iterable[ReportModel]) -> CrossRunSummary:
    """Aggregate report models from multiple runs into one summary (TOOL-REP-110).

    Runs are ordered by run id; duplicate run ids are refused. Runs whose
    model predates the provenance extension (format 1.0) report ``unknown``
    toolchain/target, so the aggregation stays total over any loadable model.
    """
    checked = _checked(models)
    runs: list[RunSummary] = []
    for model in sorted(checked, key=lambda m: m.run_id):
        facts = model.provenance_facts()
        toolchain = facts.get("compiler", _UNKNOWN)
        target = facts.get("target")
        if target == "none":
            target = None
        runs.append(
            RunSummary(
                run_id=model.run_id,
                report_id=model.report_id,
                where=model.execution.where if model.execution else _UNKNOWN,
                toolchain=toolchain,
                target_id=target,
                tests=len(model.test_statuses()),
                status_counts=_status_counts(model),
                coverage=model.coverage_figures(),
                generated_at=model.generated_at,
            )
        )

    toolchains = tuple(sorted({run.toolchain for run in runs}))
    targets = tuple(sorted({run.target_id for run in runs if run.target_id is not None}))
    units = tuple(sorted({unit for run in runs for unit in run.coverage}))

    return CrossRunSummary(
        runs=tuple(runs),
        status_totals=_totals([run.status_counts for run in runs]),
        tests_total=sum(run.tests for run in runs),
        toolchains=toolchains,
        targets=targets,
        units=units,
    )


def cross_run_summary_to_dict(summary: CrossRunSummary) -> dict[str, Any]:
    """Return the canonical dictionary form of a cross-run summary."""
    return summary.to_dict()


def dump_cross_run_summary(summary: CrossRunSummary) -> str:
    """Serialise the summary to byte-deterministic canonical JSON text."""
    return canonical_json(summary.to_dict())


def build_coverage_trend(models: Iterable[ReportModel]) -> CoverageTrend:
    """Order successive runs and record each unit's figures (TOOL-REP-120).

    Runs are ordered by their recorded ``generated_at`` (the model content),
    ties broken by run id — never by observation time, so the trend is a
    deterministic function of the inputs. A unit absent from a run has no
    entry for that run in its series.
    """
    checked = _checked(models)
    ordered = sorted(checked, key=lambda m: (m.generated_at, m.run_id))

    points: list[TrendPoint] = []
    series: dict[str, list[tuple[str, int, int]]] = {}
    for model in ordered:
        figures = model.coverage_figures()
        covered = sum(pair[0] for pair in figures.values())
        total = sum(pair[1] for pair in figures.values())
        points.append(
            TrendPoint(
                run_id=model.run_id,
                generated_at=model.generated_at,
                covered=covered,
                total=total,
            )
        )
        for unit, (unit_covered, unit_total) in figures.items():
            series.setdefault(unit, []).append((model.run_id, unit_covered, unit_total))

    return CoverageTrend(
        points=tuple(points),
        unit_series={unit: tuple(series[unit]) for unit in sorted(series)},
    )


def coverage_trend_to_dict(trend: CoverageTrend) -> dict[str, Any]:
    """Return the canonical dictionary form of a coverage trend."""
    return trend.to_dict()


def dump_coverage_trend(trend: CoverageTrend) -> str:
    """Serialise the trend to byte-deterministic canonical JSON text."""
    return canonical_json(trend.to_dict())
