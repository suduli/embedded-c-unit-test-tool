# implements: TOOL-ATG-060, TOOL-ATG-100
"""A bounded generation run and its report (WP-ATG-05).

Verifies: TOOL-ATG-060 (cases generated, coverage achieved, constructs left uncovered
per run), TOOL-ATG-100 (time, memory and case bounds; graceful termination returning
what was generated), with the unmeasured-is-not-uncovered rule.
"""

from __future__ import annotations

import json
import tracemalloc
from typing import Any

import pytest

from ectt.atg import (
    AtgError,
    BuildOutcome,
    CoverageDelta,
    EngineInfo,
    ExecutionOutcome,
    GenerationCandidate,
)
from ectt.atg.run import (
    TERMINATIONS,
    Construct,
    RunLimits,
    dump_run_report,
    run_generation,
)
from ectt.tcm import datacases as dd

ENGINE = EngineInfo("klee", "3.1")
TARGETS = [
    Construct("L1", "line", "src/a.c:3"),
    Construct("L2", "line", "src/a.c:5"),
    Construct("B1", "branch", "src/a.c:4"),
    Construct("C1", "condition", "src/a.c:4"),
]


class ScriptedPort:
    """Port whose behaviour is keyed by the candidate's ``x`` parameter."""

    def __init__(self, covers: dict[str, tuple[str, ...] | None], *, bad: dict[str, str] | None = None, tick: Any = None) -> None:
        self.covers = covers
        self.bad = bad or {}
        self.tick = tick
        self.measured: list[str] = []

    def build(self, candidate: GenerationCandidate) -> BuildOutcome:
        if self.tick:
            self.tick()
        return BuildOutcome(ok=self.bad.get(candidate.inputs.parameters["x"]) != "build")

    def execute(self, candidate: GenerationCandidate) -> ExecutionOutcome:
        if self.bad.get(candidate.inputs.parameters["x"]) == "crash":
            return ExecutionOutcome("crash", detail="SIGSEGV")
        return ExecutionOutcome("completed", return_value="1")

    def measure(self, candidate: GenerationCandidate) -> CoverageDelta | None:
        x = candidate.inputs.parameters["x"]
        self.measured.append(x)
        covers = self.covers.get(x)
        return None if covers is None else CoverageDelta(0, len(covers), len(TARGETS), newly_covered=covers)


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t


def _cands(*xs: str) -> list[GenerationCandidate]:
    """Candidates with explicit ids so the id-ordered processing order is the order of ``x``."""
    return [GenerationCandidate(f"atg.{x}", "src/a.c", "f", dd.TestCaseInputs(parameters={"x": x})) for x in xs]


def _run(port: ScriptedPort, candidates: list[GenerationCandidate], **kw: Any) -> Any:
    return run_generation(candidates, port, ENGINE, function="f", targets=TARGETS, **kw)


FULL = {"1": ("L1", "B1"), "2": ("L2",), "3": ("C1",), "4": ()}


# --- TOOL-ATG-060: the report -------------------------------------------------------------------


def test_the_report_gives_cases_generated_coverage_and_the_uncovered_constructs() -> None:
    run = _run(ScriptedPort(FULL), _cands("1", "2"))
    report = run.report

    assert report.cases_generated == 2 and len(run.cases) == 2
    assert (report.coverage.status, report.coverage.covered, report.coverage.total) == ("measured", 3, 4)
    assert [(c.construct_id, c.kind, c.location) for c in report.coverage.uncovered] == [("C1", "condition", "src/a.c:4")]


def test_all_constructs_covered_leaves_nothing_uncovered() -> None:
    run = _run(ScriptedPort(FULL), _cands("1", "2", "3"))
    assert run.report.coverage.covered == 4 and run.report.coverage.uncovered == ()


def test_only_presented_cases_contribute_coverage() -> None:
    port = ScriptedPort(FULL, bad={"1": "crash", "2": "build"})
    run = _run(port, _cands("1", "2", "3"))

    assert run.report.coverage.covered == 1  # only "3" was presented
    assert sorted(port.measured) == ["3"]
    assert {d.reason for d in run.report.discarded} == {"crash", "build_failed"}


def test_already_covered_constructs_count_and_are_not_listed_as_uncovered() -> None:
    run = _run(ScriptedPort(FULL), _cands("2"), already_covered=["L1", "B1", "C1"])
    assert run.report.coverage.covered == 4 and run.report.coverage.uncovered == ()


def test_a_case_that_cannot_be_measured_makes_coverage_unmeasured_not_uncovered() -> None:
    run = _run(ScriptedPort({"1": ("L1",), "2": None}), _cands("1", "2"))

    assert run.report.coverage.status == "unmeasured"
    assert run.report.coverage.uncovered == () and run.report.coverage.covered == 0
    assert run.report.cases_generated == 2  # the cases are still presented


def test_no_presented_case_means_zero_coverage_listing_every_target() -> None:
    run = _run(ScriptedPort(FULL, bad={"1": "crash"}), _cands("1"))
    assert run.report.coverage.status == "measured"
    assert [c.construct_id for c in run.report.coverage.uncovered] == ["L1", "L2", "B1", "C1"]


def test_discards_are_counted_by_reason_in_the_report_document() -> None:
    port = ScriptedPort(FULL, bad={"1": "crash", "2": "build"})
    document = json.loads(dump_run_report(_run(port, _cands("1", "2", "3", "3")).report))

    assert document["discarded"] == {"build_failed": 1, "crash": 1, "duplicate": 1}
    assert document["candidates"] == 4 and document["attempted"] == 3 and document["cases_generated"] == 1


def test_a_port_reporting_an_unknown_construct_is_refused() -> None:
    with pytest.raises(AtgError) as excinfo:
        _run(ScriptedPort({"1": ("L1", "NOPE")}), _cands("1"))
    assert excinfo.value.reason == "unknown_construct"


def test_measurement_failures_raise_instead_of_reading_as_uncovered() -> None:
    class Broken(ScriptedPort):
        def measure(self, candidate: GenerationCandidate) -> CoverageDelta | None:
            raise OSError("profiler unavailable")

    with pytest.raises(AtgError) as excinfo:
        _run(Broken(FULL), _cands("1"))
    assert excinfo.value.reason == "port_failed"


def test_bad_run_inputs_are_refused() -> None:
    with pytest.raises(AtgError) as dup:
        run_generation(_cands("1"), ScriptedPort(FULL), ENGINE, function="f", targets=[TARGETS[0], TARGETS[0]])
    assert dup.value.reason == "duplicate_construct"
    with pytest.raises(AtgError) as unknown:
        _run(ScriptedPort(FULL), _cands("1"), already_covered=["NOPE"])
    assert unknown.value.reason == "unknown_construct"


@pytest.mark.parametrize(("construct_id", "kind"), [("", "line"), ("a b", "line"), ("L9", "statement")])
def test_constructs_need_a_token_id_and_a_known_kind(construct_id: str, kind: str) -> None:
    with pytest.raises(AtgError) as excinfo:
        Construct(construct_id, kind, "f.c:1")
    assert excinfo.value.reason == "invalid_construct"


# --- TOOL-ATG-100: bounds -------------------------------------------------------------------------


def test_without_limits_a_run_completes() -> None:
    run = _run(ScriptedPort(FULL), _cands("1", "2", "3", "4"))
    assert run.report.terminated_by == "complete" and run.report.not_attempted == 0
    assert run.report.limits == RunLimits()


def test_a_time_limit_stops_the_run_and_returns_what_was_generated() -> None:
    clock = FakeClock()
    port = ScriptedPort(FULL, tick=lambda: setattr(clock, "t", clock.t + 1.0))

    run = _run(port, _cands("1", "2", "3", "4"), limits=RunLimits(max_seconds=2.0), clock=clock)

    assert run.report.terminated_by == "time_limit"
    assert (run.report.attempted, run.report.not_attempted, run.report.cases_generated) == (2, 2, 2)
    assert all(not case.stale for case in run.cases)
    assert run.report.coverage.covered == 3  # coverage of what was generated, not of what was skipped


def test_a_memory_limit_stops_the_run_gracefully() -> None:
    readings = iter([10, 20, 500, 500, 500])

    run = _run(ScriptedPort(FULL), _cands("1", "2", "3", "4"), limits=RunLimits(max_memory_bytes=100), memory_probe=lambda: next(readings))

    assert run.report.terminated_by == "memory_limit"
    assert (run.report.attempted, run.report.cases_generated, run.report.not_attempted) == (2, 2, 2)


def test_a_case_limit_stops_the_run_once_enough_cases_are_presented() -> None:
    run = _run(ScriptedPort(FULL), _cands("1", "2", "3", "4"), limits=RunLimits(max_cases=2))
    assert run.report.terminated_by == "case_limit" and run.report.cases_generated == 2 and run.report.not_attempted == 2


def test_discarded_candidates_do_not_count_toward_the_case_limit() -> None:
    run = _run(ScriptedPort(FULL, bad={"1": "crash"}), _cands("1", "2", "3"), limits=RunLimits(max_cases=2))
    assert run.report.cases_generated == 2 and run.report.terminated_by == "complete"


def test_a_limit_hit_on_the_first_candidate_returns_an_empty_but_valid_run() -> None:
    clock = FakeClock()
    clock.t = 0.0
    run = _run(ScriptedPort(FULL), _cands("1", "2"), limits=RunLimits(max_seconds=1e-9), clock=_Advancing(clock))
    assert run.report.terminated_by == "time_limit" and run.cases == () and run.report.not_attempted == 2
    assert run.report.coverage.covered == 0 and len(run.report.coverage.uncovered) == 4


class _Advancing:
    def __init__(self, clock: FakeClock) -> None:
        self.clock = clock

    def now(self) -> float:
        self.clock.t += 1.0
        return self.clock.t


def test_the_default_memory_probe_measures_the_python_heap_and_restores_tracing() -> None:
    assert not tracemalloc.is_tracing()

    run = _run(ScriptedPort(FULL), _cands("1", "2"), limits=RunLimits(max_memory_bytes=1))

    assert run.report.terminated_by == "memory_limit" and run.cases == ()
    assert not tracemalloc.is_tracing()


def test_an_already_tracing_process_is_left_tracing() -> None:
    tracemalloc.start()
    try:
        _run(ScriptedPort(FULL), _cands("1"), limits=RunLimits(max_memory_bytes=10**12))
        assert tracemalloc.is_tracing()
    finally:
        tracemalloc.stop()


@pytest.mark.parametrize("kwargs", [{"max_seconds": 0}, {"max_seconds": -1.0}, {"max_memory_bytes": 0}, {"max_cases": 0}, {"max_cases": True}])
def test_limits_must_be_positive_when_set(kwargs: dict[str, Any]) -> None:
    with pytest.raises(AtgError) as excinfo:
        RunLimits(**kwargs)
    assert excinfo.value.reason == "invalid_limit"


# --- determinism and the document --------------------------------------------------------------------------


def test_the_report_is_deterministic_and_carries_no_measured_time_or_memory() -> None:
    clock = FakeClock()
    port = ScriptedPort(FULL, tick=lambda: setattr(clock, "t", clock.t + 0.123456))
    first = dump_run_report(_run(port, _cands("1", "2"), limits=RunLimits(max_seconds=100.0), clock=clock).report)
    clock.t = 77.0
    second = dump_run_report(_run(ScriptedPort(FULL), _cands("2", "1"), limits=RunLimits(max_seconds=100.0), clock=clock).report)

    assert first == second
    document = json.loads(first)
    assert document["limits"] == {"max_cases": None, "max_memory_bytes": None, "max_seconds": 100.0}
    assert "0.123" not in first and "77" not in first


def test_the_report_names_what_limitations_were_and_were_not_assessed() -> None:
    document = json.loads(dump_run_report(_run(ScriptedPort(FULL), _cands("1")).report))
    assert document["assessed_limitation_kinds"] == ["concurrency", "dynamic_memory", "floating_point"]
    assert document["not_assessed_limitation_kinds"] == ["inline_assembly"]
    assert document["engine"] == "klee@3.1" and document["function"] == "f"


def test_terminations_are_a_closed_vocabulary() -> None:
    assert TERMINATIONS == ("complete", "time_limit", "memory_limit", "case_limit")


@pytest.mark.parametrize("field", ["max_seconds", "max_memory_bytes", "max_cases"])
def test_a_non_finite_limit_is_refused_not_silently_unenforced(field: str) -> None:
    with pytest.raises(AtgError) as excinfo:
        RunLimits(**{field: float("nan")})
    assert excinfo.value.reason == "invalid_limit"
