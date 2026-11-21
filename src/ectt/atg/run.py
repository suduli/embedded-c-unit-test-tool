# implements: TOOL-ATG-060, TOOL-ATG-100
"""A bounded generation run and its report (WP-ATG-05, DSN-ATG-060).

``run_generation`` validates candidates through the port (``ectt.atg.lifecycle``) under
configurable limits and reports, per run (TOOL-ATG-060): the number of cases generated,
the coverage achieved, and the specific constructs left uncovered.

**Bounds (TOOL-ATG-100).** ``RunLimits`` bounds wall time, memory and the number of
presented cases. The limits are checked between candidates (cooperatively): when one is
reached the run stops and *returns what it has*, with ``terminated_by`` naming the limit
and ``not_attempted`` counting the candidates it did not get to. Nothing is discarded or
failed because a limit was hit. The report carries the configured limits and the reason
for stopping, never a measured duration or byte count, so it is deterministic. The clock
and the memory probe are injectable; a configured memory limit with no usable probe is an
error, never a limit that is silently not enforced. The default probe measures the Python
heap (``tracemalloc``); an engine's native memory is the engine adapter's to bound.

**Coverage (TOOL-ATG-060).** The port reports, per presented case, the constructs it newly
covered (``CoverageDelta.newly_covered``). The caller names the ``targets``: the constructs
of the designated function (line, branch or condition), optionally with some already
covered. The report lists every target still uncovered, with kind and location: the part a
user acts on. If the port cannot measure a case, coverage is reported ``unmeasured`` and
no uncovered list is asserted: unmeasured is not uncovered.

**Capability limits (TOOL-ATG-110)** from ``ectt.atg.capabilities`` ride in the report so
an absent test is distinguishable from an impossible one.

Satisfies: TOOL-ATG-060, TOOL-ATG-100.
"""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from ectt.atg.capabilities import (
    ASSESSED_KINDS,
    NOT_ASSESSED_KINDS,
    Limitation,
)
from ectt.atg.errors import AtgError
from ectt.atg.lifecycle import (
    Discard,
    EngineInfo,
    GenerationCandidate,
    GenerationOutcome,
    TestValidationPort,
    validate_one,
)
from ectt.core.determinism import canonical_json
from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "CONSTRUCT_KINDS",
    "TERMINATIONS",
    "BudgetClock",
    "Construct",
    "CoverageReport",
    "GenerationRun",
    "MonotonicClock",
    "RunLimits",
    "RunReport",
    "dump_run_report",
    "python_heap_probe",
    "run_generation",
]

CONSTRUCT_KINDS: tuple[str, ...] = ("line", "branch", "condition")
TERMINATIONS: tuple[str, ...] = ("complete", "time_limit", "memory_limit", "case_limit")


class BudgetClock(Protocol):
    """A monotonic clock in seconds, used only to enforce the time limit."""

    def now(self) -> float: ...


class MonotonicClock:
    """The production budget clock (``time.monotonic``)."""

    def now(self) -> float:
        return time.monotonic()


def python_heap_probe() -> int:
    """Bytes currently allocated by the Python heap (requires ``tracemalloc`` tracing)."""
    return tracemalloc.get_traced_memory()[0]


@dataclass(frozen=True)
class Construct:
    """A coverage construct of the designated function: what generation aims to cover."""

    construct_id: str
    kind: str  # line | branch | condition
    location: str  # "file:line"

    def __post_init__(self) -> None:
        if not self.construct_id or any(c.isspace() for c in self.construct_id):
            raise AtgError("a construct id must be a non-empty token", reason="invalid_construct")
        if self.kind not in CONSTRUCT_KINDS:
            raise AtgError(f"construct '{self.construct_id}' has unknown kind '{self.kind}' (expected one of {', '.join(CONSTRUCT_KINDS)})", reason="invalid_construct")

    def to_dict(self) -> dict[str, str]:
        return {"construct_id": self.construct_id, "kind": self.kind, "location": self.location}


@dataclass(frozen=True)
class RunLimits:
    """Bounds on one run; ``None`` means unbounded for that resource."""

    max_seconds: float | None = None
    max_memory_bytes: int | None = None
    max_cases: int | None = None

    def __post_init__(self) -> None:
        for what, value in (("max_seconds", self.max_seconds), ("max_memory_bytes", self.max_memory_bytes), ("max_cases", self.max_cases)):
            if value is not None and (isinstance(value, bool) or not value > 0):
                raise AtgError(f"{what} must be positive when set (got {value!r})", reason="invalid_limit")

    def to_dict(self) -> dict[str, Any]:
        return {"max_cases": self.max_cases, "max_memory_bytes": self.max_memory_bytes, "max_seconds": self.max_seconds}


@dataclass(frozen=True)
class CoverageReport:
    """Coverage achieved by the presented cases, or an explicit statement that it is unknown."""

    status: str  # "measured" | "unmeasured"
    covered: int
    total: int
    uncovered: tuple[Construct, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "covered": self.covered,
            "status": self.status,
            "total": self.total,
            "uncovered": [c.to_dict() for c in self.uncovered],
        }


@dataclass(frozen=True)
class RunReport:
    """The per-run report of TOOL-ATG-060, bounds of TOOL-ATG-100, limits of TOOL-ATG-110."""

    engine: str
    function: str
    candidates: int
    attempted: int
    not_attempted: int
    cases_generated: int
    discarded: tuple[Discard, ...]
    terminated_by: str
    limits: RunLimits
    coverage: CoverageReport
    limitations: tuple[Limitation, ...]

    def to_dict(self) -> dict[str, Any]:
        discard_counts: dict[str, int] = {}
        for item in self.discarded:
            discard_counts[item.reason] = discard_counts.get(item.reason, 0) + 1
        return {
            "assessed_limitation_kinds": list(ASSESSED_KINDS),
            "attempted": self.attempted,
            "candidates": self.candidates,
            "cases_generated": self.cases_generated,
            "coverage": self.coverage.to_dict(),
            "discarded": dict(sorted(discard_counts.items())),
            "engine": self.engine,
            "function": self.function,
            "limitations": [limitation.to_dict() for limitation in self.limitations],
            "limits": self.limits.to_dict(),
            "not_assessed_limitation_kinds": list(NOT_ASSESSED_KINDS),
            "not_attempted": self.not_attempted,
            "terminated_by": self.terminated_by,
        }


@dataclass(frozen=True)
class GenerationRun:
    """What a run produced and the report about it."""

    outcome: GenerationOutcome
    report: RunReport

    @property
    def cases(self) -> tuple[DataDrivenTestCase, ...]:
        return self.outcome.cases


def dump_run_report(report: RunReport) -> str:
    """Deterministic JSON text of a run report."""
    return canonical_json(report.to_dict())


def run_generation(
    candidates: Iterable[GenerationCandidate],
    port: TestValidationPort,
    engine: EngineInfo,
    *,
    function: str,
    targets: Sequence[Construct],
    already_covered: Iterable[str] = (),
    limits: RunLimits | None = None,
    clock: BudgetClock | None = None,
    memory_probe: Callable[[], int] | None = None,
    limitations: Sequence[Limitation] = (),
) -> GenerationRun:
    """Validate ``candidates`` under ``limits`` and report the run.

    Candidates are processed in id order (equal ids are discarded as duplicates). Limits are
    checked before each candidate; on reaching one the run stops and returns what it has.
    Coverage comes from ``port.measure`` for each *presented* case.
    """
    bounds = limits or RunLimits()
    target_ids = {t.construct_id for t in targets}
    if len(target_ids) != len(targets):
        raise AtgError("two coverage targets share an id", reason="duplicate_construct")
    covered: set[str] = set()
    for construct_id in already_covered:
        if construct_id not in target_ids:
            raise AtgError(f"already-covered id '{construct_id}' is not one of the targets", reason="unknown_construct")
        covered.add(construct_id)

    unique: dict[str, GenerationCandidate] = {}
    duplicates: list[Discard] = []
    received = 0
    for candidate in candidates:
        received += 1
        if candidate.candidate_id in unique:
            duplicates.append(Discard(candidate.candidate_id, "duplicate", "same candidate id supplied more than once"))
        else:
            unique[candidate.candidate_id] = candidate
    order = sorted(unique)

    budget_clock = clock or MonotonicClock()
    started = budget_clock.now()
    probe = memory_probe
    started_tracing = False
    if bounds.max_memory_bytes is not None and probe is None:
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            started_tracing = True
        probe = python_heap_probe

    cases: list[DataDrivenTestCase] = []
    discarded: list[Discard] = list(duplicates)
    measured = True
    attempted = 0
    terminated_by = "complete"
    try:
        for candidate_id in order:
            if bounds.max_cases is not None and len(cases) >= bounds.max_cases:
                terminated_by = "case_limit"
                break
            if bounds.max_seconds is not None and budget_clock.now() - started >= bounds.max_seconds:
                terminated_by = "time_limit"
                break
            if bounds.max_memory_bytes is not None and probe is not None and probe() >= bounds.max_memory_bytes:
                terminated_by = "memory_limit"
                break
            attempted += 1
            case, discard = validate_one(unique[candidate_id], port, engine)
            if discard is not None:
                discarded.append(discard)
                continue
            assert case is not None
            cases.append(case)
            measured = _record_coverage(port, unique[candidate_id], target_ids, covered) and measured
    finally:
        if started_tracing:
            tracemalloc.stop()

    uncovered = tuple(t for t in targets if t.construct_id not in covered)
    coverage = (
        CoverageReport("measured", len(covered), len(targets), uncovered)
        if measured
        else CoverageReport("unmeasured", 0, len(targets), ())
    )
    outcome = GenerationOutcome(
        cases=tuple(cases),
        discarded=tuple(sorted(discarded, key=lambda d: (d.candidate_id, d.reason))),
        candidates=received,
    )
    report = RunReport(
        engine=engine.label,
        function=function,
        candidates=received,
        attempted=attempted,
        not_attempted=len(order) - attempted,
        cases_generated=len(cases),
        discarded=outcome.discarded,
        terminated_by=terminated_by,
        limits=bounds,
        coverage=coverage,
        limitations=tuple(sorted(limitations, key=lambda x: (x.unit, x.function, x.kind, x.evidence))),
    )
    return GenerationRun(outcome, report)


def _record_coverage(
    port: TestValidationPort,
    candidate: GenerationCandidate,
    target_ids: set[str],
    covered: set[str],
) -> bool:
    """Fold one presented case's coverage into ``covered``; False when the port cannot measure it."""
    try:
        delta = port.measure(candidate)
    except AtgError:
        raise
    except Exception as exc:
        raise AtgError(f"validation port failed measuring '{candidate.candidate_id}': {exc}", reason="port_failed") from exc
    if delta is None:
        return False
    unknown = sorted(c for c in delta.newly_covered if c not in target_ids)
    if unknown:
        raise AtgError(
            f"port reported covering construct(s) {', '.join(unknown)} that are not among the run's targets",
            reason="unknown_construct",
        )
    covered.update(delta.newly_covered)
    return True
