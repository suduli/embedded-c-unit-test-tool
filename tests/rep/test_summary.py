# implements: TOOL-REP-110, TOOL-REP-120
"""Cross-run summary and coverage trend (WP-REP-08).

Equivalence partitioning over units, targets, and toolchains (REP-110), and
successive-run ordering for the coverage trend (REP-120). All outputs are
deterministic functions of the persisted models.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.core.determinism import FixedClock, canonical_json_bytes, stable_id
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.rep.errors import ReportModelError
from ectt.rep.model import (
    CoverageEntry,
    ReportModel,
    build_report_model,
    dump_report_model,
    load_report_model,
)
from ectt.rep.summary import (
    build_coverage_trend,
    build_cross_run_summary,
    dump_coverage_trend,
    dump_cross_run_summary,
)


def _model(
    run_id: str,
    *,
    where: str = "host",
    toolchain: str = "gcc",
    target_id: str | None = None,
    results: tuple[Any, ...] = (),
    coverage: tuple[Any, ...] = (),
    generated_at: str = "2026-11-19T00:00:00+00:00",
) -> ReportModel:
    rs = ResultSet(
        run_id=run_id,
        execution=ExecutionMetadata(where=where, toolchain=toolchain, target_id=target_id),
        results=results,
    )
    model = build_report_model(rs, coverage=coverage, clock=FixedClock(generated_at))
    return load_report_model(dump_report_model(model))  # persisted round trip


def _pass(test_id: str) -> Any:
    return finalize_result(test_id, "pass", test_id.replace("_", "") * 16)


_ADC = (CoverageEntry(unit="src/adc.c", covered=8, total=10),)


# --- TOOL-REP-110: cross-unit, target, toolchain aggregation ---------------------------


def test_summary_partitions_units_targets_toolchains() -> None:
    models = [
        _model("run-a", where="host1", toolchain="gcc", target_id="tgt-1", results=(_pass("a1"), _pass("a2"))),
        _model("run-b", where="host2", toolchain="clang", target_id="tgt-2", results=(_pass("b1"),)),
        _model("run-c", where="host1", toolchain="gcc", target_id=None),
    ]

    summary = build_cross_run_summary(models)

    assert [run.run_id for run in summary.runs] == ["run-a", "run-b", "run-c"]
    assert summary.toolchains == ("clang", "gcc")
    assert summary.targets == ("tgt-1", "tgt-2")
    assert summary.tests_total == 3
    assert summary.status_totals == {"pass": 3}


def test_summary_aggregates_units_across_runs() -> None:
    models = [
        _model("r1", coverage=_ADC),
        _model("r2", coverage=(CoverageEntry(unit="src/led.c", covered=1, total=2),)),
    ]

    summary = build_cross_run_summary(models)

    assert summary.units == ("src/adc.c", "src/led.c")
    assert summary.runs[0].coverage == {"src/adc.c": (8, 10)}
    assert summary.runs[1].coverage == {"src/led.c": (1, 2)}


def test_summary_counts_status_families_across_runs() -> None:
    models = [
        _model("r1", results=(_pass("x"),)),
        _model("r2", results=(finalize_result("y", "not_run", "d" * 32),)),
    ]

    summary = build_cross_run_summary(models)

    assert summary.status_totals == {"not_run": 1, "pass": 1}
    assert summary.runs[0].status_counts == {"pass": 1}
    assert summary.runs[1].status_counts == {"not_run": 1}


def test_summary_refuses_duplicate_run_ids() -> None:
    with pytest.raises(ReportModelError) as excinfo:
        build_cross_run_summary([_model("same"), _model("same")])
    assert excinfo.value.reason == "duplicate_run"


def test_summary_of_no_runs_is_empty_and_deterministic() -> None:
    summary = build_cross_run_summary([])

    assert summary.runs == ()
    assert summary.tests_total == 0
    assert dump_cross_run_summary(summary) == dump_cross_run_summary(summary)


def test_summary_is_deterministic_and_input_order_free() -> None:
    models = [_model("r-b", results=(_pass("b"),)), _model("r-a", results=(_pass("a"),))]

    first = dump_cross_run_summary(build_cross_run_summary(list(reversed(models))))
    second = dump_cross_run_summary(build_cross_run_summary(models))

    assert first == second  # runs ordered by run id, not input order
    assert json.loads(first)["runs"][0]["run_id"] == "r-a"


def test_summary_round_trips_through_canonical_json() -> None:
    summary = build_cross_run_summary([_model("r1", toolchain="gcc", target_id="t9", results=(_pass("p"),))])

    doc: dict[str, Any] = json.loads(dump_cross_run_summary(summary))

    assert doc["toolchains"] == ["gcc"]
    assert doc["targets"] == ["t9"]
    assert doc["runs"][0]["target_id"] == "t9"
    assert doc["runs"][0]["status_counts"] == {"pass": 1}


def test_summary_handles_1_0_models_without_provenance() -> None:
    """A 1.0-archived model has no execution facts: unknown, not invented."""
    model = _model("old")
    doc: dict[str, Any] = json.loads(dump_report_model(model))
    body = {key: doc[key] for key in ("coverage", "generated_at", "partial", "run_id", "tests")}
    legacy: dict[str, Any] = {
        "schema_version": "1.0",
        "report_id": stable_id(canonical_json_bytes(body)),
    }
    legacy.update(body)
    old_model = load_report_model(legacy)

    summary = build_cross_run_summary([old_model])

    assert summary.runs[0].toolchain == "unknown"
    assert summary.runs[0].target_id is None
    assert summary.runs[0].where == "unknown"


# --- TOOL-REP-120: coverage trend across successive runs -------------------------------


def test_trend_orders_runs_by_recorded_time() -> None:
    models = [
        _model("later", generated_at="2026-11-20T00:00:00+00:00"),
        _model("earlier", generated_at="2026-11-18T00:00:00+00:00"),
    ]

    trend = build_coverage_trend(models)

    assert [point.run_id for point in trend.points] == ["earlier", "later"]


def test_trend_ties_break_by_run_id() -> None:
    models = [
        _model("zz", generated_at="2026-11-19T00:00:00+00:00"),
        _model("aa", generated_at="2026-11-19T00:00:00+00:00"),
    ]

    trend = build_coverage_trend(models)

    assert [point.run_id for point in trend.points] == ["aa", "zz"]


def test_trend_totals_covered_and_total_per_run() -> None:
    models = [
        _model(
            "r1",
            generated_at="2026-11-18T00:00:00+00:00",
            coverage=(CoverageEntry(unit="src/a.c", covered=2, total=4), CoverageEntry(unit="src/b.c", covered=1, total=1)),
        ),
        _model("r2", generated_at="2026-11-19T00:00:00+00:00", coverage=_ADC),
    ]

    trend = build_coverage_trend(models)

    assert (trend.points[0].covered, trend.points[0].total) == (3, 5)
    assert (trend.points[1].covered, trend.points[1].total) == (8, 10)
    assert trend.unit_series["src/a.c"] == (("r1", 2, 4),)
    assert trend.unit_series["src/adc.c"] == (("r2", 8, 10),)


def test_trend_series_skips_units_absent_from_a_run() -> None:
    models = [
        _model("r1", generated_at="2026-11-18T00:00:00+00:00", coverage=()),
        _model("r2", generated_at="2026-11-19T00:00:00+00:00", coverage=_ADC),
    ]

    trend = build_coverage_trend(models)

    assert set(trend.unit_series) == {"src/adc.c"}
    assert trend.unit_series["src/adc.c"] == (("r2", 8, 10),)  # absent from r1


def test_trend_refuses_duplicate_run_ids() -> None:
    with pytest.raises(ReportModelError) as excinfo:
        build_coverage_trend([_model("same"), _model("same")])
    assert excinfo.value.reason == "duplicate_run"


def test_trend_dump_is_deterministic() -> None:
    models = [
        _model("r1", generated_at="2026-11-18T00:00:00+00:00", coverage=()),
        _model("r2", generated_at="2026-11-19T00:00:00+00:00", coverage=_ADC),
    ]

    trend = build_coverage_trend(models)

    assert dump_coverage_trend(trend) == dump_coverage_trend(trend)
    doc: dict[str, Any] = json.loads(dump_coverage_trend(trend))
    assert [p["run_id"] for p in doc["points"]] == ["r1", "r2"]
    assert doc["unit_series"]["src/adc.c"] == [["r2", 8, 10]]
