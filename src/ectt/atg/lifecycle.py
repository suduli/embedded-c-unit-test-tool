# implements: TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080
"""Validation port and generated-case lifecycle (WP-ATG-01, DSN-ATG-040..110).

Generation engines (symbolic execution, bounded model checking, AI providers)
produce *candidate* input vectors. This module owns what happens to a candidate
afterwards, whichever engine made it:

1. **Validation port (DSN-ATG-110).** Generation must build and run the cases it
   produces, which are lower-layer capabilities. :class:`TestValidationPort` is
   declared here and bound at composition time to the build, execution and
   coverage components, so the layer graph stays acyclic and generation is
   testable against a stub port. Nothing here imports the builder or the runner.
2. **Validation gate (TOOL-ATG-050).** Every candidate is built and executed
   through the port before it is presented. A candidate that fails to build,
   crashes the harness or times out is *discarded and counted*, never presented.
   A port that itself fails (infrastructure) raises: nothing is presented on the
   strength of a validation that did not happen.
3. **Canonical emission (TOOL-ATG-040).** A validated candidate becomes an
   ordinary ``DataDrivenTestCase``: the same record, file format and execution
   path as an authored case, editable and diffable afterwards. There is no
   separate generated-test representation.
4. **Observed behaviour as the expectation, unreviewed (TOOL-ATG-080).** The
   expected values are what the case was observed to do, and the case is marked
   ``review_state = "unreviewed"``. An unreviewed expectation is a regression
   detector, not a specification; :func:`confirm_expected` is the explicit user
   act that makes it ``reviewed`` (and, because the review state is part of the
   case content, re-binds the content digest, so earlier evidence is stale).
5. **Marked as machine-generated (TOOL-ATG-070).** The origin records author
   ``atg``, the engine and its version, in the artifact; :func:`case_marks` and
   :func:`report_marks` give reports the same facts.

Vocabulary: ``review_state`` is ``unreviewed`` or ``reviewed`` (absent for an
authored case); ``origin.engine`` is ``<engine name>@<engine version>``.

Satisfies: TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Protocol, runtime_checkable

from ectt.atg.errors import AtgError
from ectt.core.determinism import stable_id
from ectt.tcm.datacases import (
    DataDrivenTestCase,
    StubSpec,
    TestCaseExpected,
    TestCaseInputs,
    TestCaseOrigin,
    refresh_digest,
)

__all__ = [
    "BuildOutcome",
    "CoverageDelta",
    "Discard",
    "EngineInfo",
    "ExecutionOutcome",
    "GenerationCandidate",
    "GenerationOutcome",
    "TestValidationPort",
    "case_marks",
    "confirm_expected",
    "expected_status",
    "format_mark",
    "is_machine_generated",
    "make_candidate",
    "report_marks",
    "unreviewed_test_ids",
    "validate_candidates",
]

UNREVIEWED = "unreviewed"
REVIEWED = "reviewed"
_MACHINE_AUTHORS = ("atg", "ai")
EXECUTION_STATES = ("completed", "crash", "timeout", "harness_error")


@dataclass(frozen=True)
class EngineInfo:
    """The generation engine and its version, recorded as provenance."""

    name: str
    version: str

    def __post_init__(self) -> None:
        for what, value in (("engine name", self.name), ("engine version", self.version)):
            if not value or not value.strip() or "@" in value or any(c.isspace() for c in value):
                raise AtgError(f"{what} must be a non-empty token without '@' or whitespace", reason="invalid_engine")

    @property
    def label(self) -> str:
        return f"{self.name}@{self.version}"


@dataclass(frozen=True)
class GenerationCandidate:
    """An input vector proposed by an engine, before it is validated."""

    candidate_id: str
    unit: str
    function: str
    inputs: TestCaseInputs
    stubs: tuple[StubSpec, ...] = ()
    requirements: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildOutcome:
    """Result of building one candidate through the port."""

    ok: bool
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionOutcome:
    """Result of running one built candidate; values are what was observed."""

    state: str  # one of EXECUTION_STATES
    return_value: str | None = None
    global_finals: Mapping[str, str] = field(default_factory=dict)
    out_parameters: Mapping[str, str] = field(default_factory=dict)
    detail: str = ""


@dataclass(frozen=True)
class CoverageDelta:
    """Coverage gained by one case (reported by the port; used by WP-ATG-05)."""

    covered_before: int
    covered_after: int
    total: int


@runtime_checkable
class TestValidationPort(Protocol):
    """Build, execute and measure a candidate (DSN-ATG-110); bound at composition time."""

    def build(self, candidate: GenerationCandidate) -> BuildOutcome: ...

    def execute(self, candidate: GenerationCandidate) -> ExecutionOutcome: ...

    def measure(self, candidate: GenerationCandidate) -> CoverageDelta | None: ...


@dataclass(frozen=True)
class Discard:
    """A candidate that was not presented, and why."""

    candidate_id: str
    reason: str  # build_failed | crash | timeout | harness_error | duplicate
    detail: str = ""

    def to_dict(self) -> dict[str, str]:
        return {"candidate_id": self.candidate_id, "detail": self.detail, "reason": self.reason}


@dataclass(frozen=True)
class GenerationOutcome:
    """Presented cases plus an account of every candidate that was not."""

    cases: tuple[DataDrivenTestCase, ...]
    discarded: tuple[Discard, ...]
    candidates: int

    def counts(self) -> dict[str, int]:
        result = {"candidates": self.candidates, "presented": len(self.cases), "discarded": len(self.discarded)}
        for item in self.discarded:
            result[f"discarded_{item.reason}"] = result.get(f"discarded_{item.reason}", 0) + 1
        return dict(sorted(result.items()))


def make_candidate(
    unit: str,
    function: str,
    inputs: TestCaseInputs,
    *,
    stubs: Sequence[StubSpec] = (),
    requirements: Sequence[str] = (),
) -> GenerationCandidate:
    """Build a candidate whose id is derived from its content, so equal vectors share an id."""
    if not unit.strip() or not function.strip():
        raise AtgError("a candidate needs a unit and a function", reason="invalid_candidate")
    stub_view = [(s.name, s.mode, list(s.returns), s.expect_calls, dict(s.out_parameters)) for s in sorted(stubs, key=lambda s: s.name)]
    digest = stable_id("atg-candidate", unit, function, dict(inputs.parameters), dict(inputs.global_inits), stub_view)
    return GenerationCandidate(
        candidate_id=f"atg.{digest[:16]}",
        unit=unit,
        function=function,
        inputs=inputs,
        stubs=tuple(sorted(stubs, key=lambda s: s.name)),
        requirements=tuple(requirements),
    )


def _emit(candidate: GenerationCandidate, observed: ExecutionOutcome, engine: EngineInfo) -> DataDrivenTestCase:
    case = DataDrivenTestCase(
        case_id=candidate.candidate_id,
        unit=candidate.unit,
        function=candidate.function,
        inputs=candidate.inputs,
        expected=TestCaseExpected(
            return_value=observed.return_value,
            global_finals=dict(observed.global_finals),
            out_parameters=dict(observed.out_parameters),
        ),
        stubs=candidate.stubs,
        origin=TestCaseOrigin(author="atg", engine=engine.label, review_state=UNREVIEWED),
        requirements=candidate.requirements,
    )
    return refresh_digest(case)


def validate_candidates(
    candidates: Iterable[GenerationCandidate],
    port: TestValidationPort,
    engine: EngineInfo,
) -> GenerationOutcome:
    """Build and run every candidate; present only those that compiled and ran.

    Candidates are processed in id order; a repeated id is discarded as a
    duplicate without touching the port. A discard is counted with its reason;
    a failure of the port itself raises :class:`AtgError` and presents nothing.
    """
    unique: dict[str, GenerationCandidate] = {}
    discarded: list[Discard] = []
    received = 0
    for candidate in candidates:
        received += 1
        if candidate.candidate_id in unique:
            discarded.append(Discard(candidate.candidate_id, "duplicate", "same candidate id supplied more than once"))
        else:
            unique[candidate.candidate_id] = candidate

    cases: list[DataDrivenTestCase] = []
    for candidate_id in sorted(unique):
        candidate = unique[candidate_id]
        try:
            built = port.build(candidate)
            if not built.ok:
                discarded.append(Discard(candidate_id, "build_failed", "; ".join(built.diagnostics)))
                continue
            observed = port.execute(candidate)
        except AtgError:
            raise
        except Exception as exc:
            raise AtgError(
                f"validation port failed on candidate '{candidate_id}': {exc}",
                reason="port_failed",
            ) from exc
        if observed.state not in EXECUTION_STATES:
            raise AtgError(
                f"validation port reported unknown execution state '{observed.state}' for '{candidate_id}'",
                reason="invalid_port_result",
            )
        if observed.state != "completed":
            discarded.append(Discard(candidate_id, observed.state, observed.detail))
            continue
        cases.append(_emit(candidate, observed, engine))

    return GenerationOutcome(
        cases=tuple(cases),
        discarded=tuple(sorted(discarded, key=lambda d: (d.candidate_id, d.reason))),
        candidates=received,
    )


# --- marks (TOOL-ATG-070) and expectation review (TOOL-ATG-080) ---------------------------


def is_machine_generated(case: DataDrivenTestCase) -> bool:
    """True for a case authored by a generation engine or an AI provider."""
    return case.origin.author in _MACHINE_AUTHORS


def expected_status(case: DataDrivenTestCase) -> str:
    """``authored``, ``unreviewed`` or ``reviewed`` - which kind of expectation the case holds."""
    if not is_machine_generated(case):
        return "authored"
    return REVIEWED if case.origin.review_state == REVIEWED else UNREVIEWED


def case_marks(case: DataDrivenTestCase) -> dict[str, Any]:
    """The facts every report must be able to show for one case."""
    return {
        "case_id": case.case_id,
        "engine": case.origin.engine,
        "expected": expected_status(case),
        "machine_generated": is_machine_generated(case),
    }


def format_mark(case: DataDrivenTestCase) -> str:
    """One-line human form of the marks, for text reports."""
    marks = case_marks(case)
    if not marks["machine_generated"]:
        return "authored"
    engine = marks["engine"] or "unknown engine"
    return f"machine-generated ({engine}); expected value {marks['expected']}"


def report_marks(cases: Iterable[DataDrivenTestCase]) -> dict[str, Any]:
    """Marks for a set of cases plus totals, sorted by case id."""
    marks = [case_marks(c) for c in sorted(cases, key=lambda c: c.case_id)]
    return {
        "cases": marks,
        "machine_generated": sum(1 for m in marks if m["machine_generated"]),
        "unreviewed_expectations": sum(1 for m in marks if m["expected"] == UNREVIEWED),
    }


def unreviewed_test_ids(cases: Iterable[DataDrivenTestCase]) -> tuple[str, ...]:
    """Ids of generated cases whose expectation is still unreviewed.

    Pass to ``ectt.trc.build_matrix(unreviewed_tests=...)`` so these cases do
    not count toward a requirement verdict (TOOL-TRC-110).
    """
    return tuple(sorted(c.case_id for c in cases if expected_status(c) == UNREVIEWED))


def confirm_expected(case: DataDrivenTestCase) -> DataDrivenTestCase:
    """Record that a user reviewed and accepts the case's expected value.

    Only a machine-generated case can be confirmed. The review state is part of
    the case content, so the content digest changes: runs made before the
    confirmation are stale against the confirmed case. Confirming a confirmed
    case returns it unchanged.
    """
    if not is_machine_generated(case):
        raise AtgError(f"case '{case.case_id}' is authored, not generated; there is nothing to confirm", reason="not_generated")
    if case.origin.review_state == REVIEWED:
        return case
    return refresh_digest(replace(case, origin=replace(case.origin, review_state=REVIEWED)))
