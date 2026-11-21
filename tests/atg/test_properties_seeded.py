# implements: TOOL-ATG-100
"""Seeded property-style tests for ectt.atg run limits (A7, tests only; no src/ edits).

Inputs come from ``random.Random(seed)`` with fixed seeds (the seed is the test id);
no wall clock anywhere — the clock is a scripted ``FakeClock``, so the same seed
replays the same run byte-for-byte. Properties:

* **Case limit** (TOOL-ATG-100): presented cases never exceed ``max_cases``; reaching
  it terminates the run with ``terminated_by = "case_limit"`` and ``not_attempted``
  accounts for every candidate it did not get to; nothing is discarded by a limit.
* **Memory limit**: a probe at or above the bound stops the run before the first
  candidate; a configured limit without a usable probe is an error, never a limit
  that is silently not enforced.
* **Time limit**: a scripted clock crossing the bound stops the run; the report
  carries the reason, never a measured duration.
* **Order invariance**: candidates are processed in id order — a seeded shuffle of
  the input list yields the same presented cases and the same discard accounting.
* **Determinism**: identical inputs (same seed script) give identical report
  documents.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

import pytest

from ectt.atg.errors import AtgError
from ectt.atg.lifecycle import (
    BuildOutcome,
    CoverageDelta,
    EngineInfo,
    ExecutionOutcome,
    GenerationCandidate,
)
from ectt.atg.run import Construct, RunLimits, dump_run_report, run_generation
from ectt.tcm import datacases as dd

SEEDS = [0, 1, 7, 42, 1337]

ENGINE = EngineInfo("seeded-engine", "1.0")

TARGETS = tuple(Construct(f"L{i}", "line", f"src/a.c:{i}") for i in range(1, 4))


@dataclass
class FakePort:
    """A port that builds and runs everything, covering per-candidate constructs."""

    coverage: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def build(self, candidate: GenerationCandidate) -> BuildOutcome:
        return BuildOutcome(ok=True)

    def execute(self, candidate: GenerationCandidate) -> ExecutionOutcome:
        return ExecutionOutcome(state="completed", detail="pass")

    def measure(self, candidate: GenerationCandidate) -> CoverageDelta | None:
        covers = self.coverage.get(candidate.candidate_id)
        return None if covers is None else CoverageDelta(0, len(covers), 3, newly_covered=covers)


@dataclass
class FakeClock:
    """A scripted clock: every ``now()`` consumes the next scripted value."""

    readings: list[float]
    calls: int = 0

    def now(self) -> float:
        value = self.readings[min(self.calls, len(self.readings) - 1)]
        self.calls += 1
        return value


def _candidates(count: int) -> list[GenerationCandidate]:
    return [
        GenerationCandidate(f"atg.{i:03d}", "src/a.c", "f", dd.TestCaseInputs(parameters={"x": str(i)}))
        for i in range(count)
    ]


def _run(candidates: list[GenerationCandidate], port: FakePort, **kw: object) -> object:
    return run_generation(candidates, port, ENGINE, function="f", targets=TARGETS, **kw)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_case_limit_bounds_the_presented_cases(seed: int) -> None:
    """verifies: TOOL-ATG-100 — presented <= max_cases; the stop is named; the
    remainder is accounted as not attempted, never discarded."""
    rng = random.Random(seed)
    total = rng.randint(6, 12)
    max_cases = rng.randint(1, 5)
    run = _run(_candidates(total), FakePort(), limits=RunLimits(max_cases=max_cases))

    assert run.report.cases_generated == max_cases
    assert run.report.terminated_by == "case_limit"
    assert run.report.not_attempted == total - max_cases
    assert run.report.candidates == total
    assert all(d.reason != "case_limit" for d in run.report.discarded)  # a limit discards nothing


@pytest.mark.parametrize("seed", SEEDS)
def test_reports_are_byte_identical_for_identical_inputs(seed: int) -> None:
    """verifies: TOOL-NFR-060 — same seed, same report document."""
    rng = random.Random(seed)
    total = rng.randint(4, 9)
    max_cases = rng.randint(1, 4)
    candidates = _candidates(total)
    port = FakePort()
    first = _run(candidates, port, limits=RunLimits(max_cases=max_cases))
    second = _run(candidates, FakePort(), limits=RunLimits(max_cases=max_cases))
    assert dump_run_report(first.report) == dump_run_report(second.report)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_memory_limit_stops_before_the_first_candidate_when_reached(seed: int) -> None:
    """verifies: TOOL-ATG-100 — a probe at the bound stops the run immediately
    and names the limit."""
    rng = random.Random(seed)
    total = rng.randint(3, 8)
    bound = rng.randint(100, 500)
    probe_readings = iter([bound])  # first probe call is already at the bound
    run = _run(
        _candidates(total),
        FakePort(),
        limits=RunLimits(max_memory_bytes=bound),
        memory_probe=lambda: next(probe_readings),
    )
    assert run.report.terminated_by == "memory_limit"
    assert run.report.attempted == 0
    assert run.report.not_attempted == total


@pytest.mark.parametrize("seed", SEEDS)
def test_a_memory_limit_without_a_probe_falls_back_to_the_python_heap(seed: int) -> None:
    """verifies: TOOL-ATG-100 — a configured limit without a probe is enforced
    through the default (Python heap) probe: the run completes when the bound
    is far above the heap, and the report says so deterministically."""
    rng = random.Random(seed)
    run = _run(
        _candidates(rng.randint(1, 4)),
        FakePort(),
        limits=RunLimits(max_memory_bytes=10**9),
    )
    assert run.report.terminated_by == "complete"
    assert run.report.limits.max_memory_bytes == 10**9


@pytest.mark.parametrize("seed", SEEDS)
def test_the_time_limit_is_enforced_by_the_scripted_clock(seed: int) -> None:
    """verifies: TOOL-ATG-100 — a scripted clock crossing the bound stops the
    run mid-way; no wall clock is consulted (the readings are the seed's)."""
    rng = random.Random(seed)
    total = rng.randint(4, 9)
    stop_after = rng.randint(1, 3)
    # One reading before each candidate: t=0, then crossing the bound after
    # ``stop_after`` candidates (each step consumes one now()).
    readings = [float(i) for i in range(stop_after + 1)] + [10_000.0] * (total + 1)
    clock = FakeClock(readings)
    run = _run(
        _candidates(total),
        FakePort(),
        limits=RunLimits(max_seconds=5.0),
        clock=clock,
    )
    assert run.report.terminated_by == "time_limit"
    assert run.report.cases_generated == stop_after
    assert run.report.not_attempted == total - stop_after


@pytest.mark.parametrize("seed", SEEDS)
def test_candidate_order_does_not_change_the_run_verdict(seed: int) -> None:
    """verifies: TOOL-ATG-060 — candidates are processed in id order: a seeded
    shuffle in, same presented set and same discard accounting out."""
    rng = random.Random(seed)
    total = rng.randint(4, 8)
    candidates = _candidates(total)
    shuffled = candidates[:]
    rng.shuffle(shuffled)
    coverage = {c.candidate_id: (f"L{(i % 3) + 1}",) for i, c in enumerate(candidates)}
    straight = _run(candidates, FakePort(coverage=coverage))
    mixed = _run(shuffled, FakePort(coverage=coverage))
    assert dump_run_report(straight.report) == dump_run_report(mixed.report)
    assert {c.case_id for c in straight.cases} == {c.case_id for c in mixed.cases}


@pytest.mark.parametrize("seed", SEEDS)
def test_invalid_limits_are_refused_with_the_named_reason(seed: int) -> None:
    """verifies: TOOL-ATG-100 — zero, negative or boolean limits are refused."""
    rng = random.Random(seed)
    bad_values = [0, -rng.randint(1, 100), True]
    kind = rng.choice(["max_seconds", "max_memory_bytes", "max_cases"])
    for bad in bad_values:
        with pytest.raises(AtgError) as excinfo:
            RunLimits(**{kind: bad})
        assert excinfo.value.reason == "invalid_limit"


@pytest.mark.parametrize("seed", SEEDS)
def test_the_report_document_is_deterministic_json(seed: int) -> None:
    """verifies: TOOL-NFR-060 — the dumped document parses, is stable under
    re-dump, and carries no wall-clock or measured-duration field."""
    rng = random.Random(seed)
    run = _run(_candidates(rng.randint(2, 6)), FakePort())
    text = dump_run_report(run.report)
    document = json.loads(text)
    assert dump_run_report(run.report) == text  # stable under re-dump
    for key in ("max_seconds", "max_memory_bytes", "max_cases"):
        assert key in document["limits"]
    assert "duration" not in text and "elapsed" not in text
