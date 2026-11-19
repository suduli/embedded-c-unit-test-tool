# implements: TOOL-REP-090, TOOL-REP-100
"""Renderer agreement and determinism over the single model (WP-REP-01).

Acceptance criterion (PLAN-001 §5.4): two different renderers over one
persisted report model cannot disagree on any test's status or any coverage
figure; re-running the renderer produces byte-identical output excluding
timestamps.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultSet,
    SourceLocation,
    finalize_result,
)
from ectt.rep.model import (
    CoverageEntry,
    ReportModel,
    build_report_model,
    dump_report_model,
    load_report_model,
)
from ectt.rep.render import render_json, render_text

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")

_FAILURE = AssertionFailure(
    assertion="assert_equal",
    expected="0",
    actual="1",
    location=SourceLocation(file="test_alpha.c", line=42),
)


def _result_set(
    results: tuple[Any, ...],
    not_executed: tuple[str, ...] = (),
    partial: bool = False,
) -> ResultSet:
    return ResultSet(
        run_id="run-agreement",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=results,
        not_executed=not_executed,
        partial=partial,
    )


def _models() -> list[ReportModel]:
    """Battery: mixed statuses, empty, partial, zero coverage, single test."""
    mixed = build_report_model(
        _result_set(
            (
                finalize_result("t.beta", "pass", "db" * 32),
                finalize_result("t.alpha", "fail", "da" * 32, failures=(_FAILURE,)),
                finalize_result("t.gamma", "error", "dg" * 32),
                finalize_result("t.delta", "timeout", "dd" * 32),
            ),
            not_executed=("t.epsilon",),
        ),
        coverage=(CoverageEntry(unit="src/adc.c", covered=8, total=10), CoverageEntry(unit="src/led.c", covered=0, total=5)),
        clock=CLOCK,
    )
    empty = build_report_model(_result_set(()), coverage=(), clock=CLOCK)
    partial = build_report_model(
        _result_set((finalize_result("t.one", "pass", "d1" * 32),), partial=True),
        coverage=(CoverageEntry(unit="src/x.c", covered=0, total=0),),
        clock=CLOCK,
    )
    single = build_report_model(
        _result_set((finalize_result("solo", "pass", "ds" * 32),)),
        coverage=(CoverageEntry(unit="src/solo.c", covered=3, total=3),),
        clock=CLOCK,
    )
    return [mixed, empty, partial, single]


def _parse_text(text: str) -> tuple[dict[str, str], dict[str, tuple[int, int]]]:
    statuses: dict[str, str] = {}
    figures: dict[str, tuple[int, int]] = {}
    for line in text.splitlines():
        if line.startswith("TEST "):
            _, test_id, status = line.split(" ")
            statuses[test_id] = status
        elif line.startswith("COVERAGE "):
            _, unit, counters = line.split(" ")
            covered, total = counters.split("/")
            figures[unit] = (int(covered), int(total))
    return statuses, figures


def _parse_json(text: str) -> tuple[dict[str, str], dict[str, tuple[int, int]]]:
    doc: dict[str, Any] = json.loads(text)
    statuses = {entry["id"]: entry["status"] for entry in doc["tests"]}
    figures = {entry["unit"]: (entry["covered"], entry["total"]) for entry in doc["coverage"]}
    return statuses, figures


@pytest.mark.parametrize("model", _models(), ids=["mixed", "empty", "partial", "single"])
def test_renderers_cannot_disagree(model: ReportModel) -> None:
    """verifies: the PLAN-001 §5.4 criterion for WP-REP-01.

    Both renderers are fed the same persisted round-trip model; the status
    and coverage maps they expose must equal each other and the model.
    """
    persisted = load_report_model(dump_report_model(model))

    text_statuses, text_figures = _parse_text(render_text(persisted))
    json_statuses, json_figures = _parse_json(render_json(persisted))

    assert text_statuses == json_statuses == persisted.test_statuses()
    assert text_figures == json_figures == persisted.coverage_figures()


@pytest.mark.parametrize("model", _models(), ids=["mixed", "empty", "partial", "single"])
def test_rendering_is_byte_identical(model: ReportModel) -> None:
    """verifies: TOOL-REP-100 — identical inputs, byte-identical output."""
    persisted = load_report_model(dump_report_model(model))

    assert render_text(persisted) == render_text(persisted)
    assert render_json(persisted) == render_json(persisted)
    assert dump_report_model(persisted) == dump_report_model(persisted)


def test_renderers_exclude_timestamps() -> None:
    """verifies: TOOL-REP-100 — rendered output excludes timestamps."""
    model = _models()[0]

    assert "generated_at" not in render_json(model)
    assert "2026-11-19" not in render_text(model)
    assert "2026-11-19" not in render_json(model)


def test_text_summary_counts_statuses_deterministically() -> None:
    model = _models()[0]

    lines = render_text(model).splitlines()
    assert lines[0] == "ectt report run-agreement"
    assert lines[1] == "partial: no"
    assert lines[2] == "tests: 5 error=1 fail=1 not_run=1 pass=1 timeout=1"
    assert "COVERAGE src/adc.c 8/10" in lines
    assert "COVERAGE src/led.c 0/5" in lines


def test_zero_total_coverage_renders_without_division() -> None:
    model = _models()[2]

    text = render_text(model)
    assert "COVERAGE src/x.c 0/0" in text
    assert "%" not in text  # no renderer owns a rounding policy


def test_renderers_are_pure_functions_of_content() -> None:
    """A model rebuilt from the same inputs renders identically."""
    rebuilt = build_report_model(
        _result_set((finalize_result("t.beta", "pass", "db" * 32),)),
        coverage=(CoverageEntry(unit="src/a.c", covered=1, total=2),),
        clock=CLOCK,
    )
    rebuilt_again = build_report_model(
        _result_set((finalize_result("t.beta", "pass", "db" * 32),)),
        coverage=(CoverageEntry(unit="src/a.c", covered=1, total=2),),
        clock=CLOCK,
    )

    assert render_text(rebuilt) == render_text(rebuilt_again)
    assert render_json(rebuilt) == render_json(rebuilt_again)
