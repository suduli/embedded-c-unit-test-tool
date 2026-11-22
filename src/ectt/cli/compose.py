"""Production composition of the generation run's validation port (A1).

``ectt.atg`` declares :class:`~ectt.atg.binding.BoundValidationPort` and the
layer rule is pinned: nothing under ``ectt.atg`` imports the builder or the
runner (DSN-ATG-110). The composition happens here, in the CLI layer, which by
design depends on every engine component:

* **build** is bound to the harness-build step
  (:func:`ectt.bld.harness_build.build_harness_suite`): the authored link plan
  gates the build, the caller-supplied *compile port* produces the harness
  binary (no C compiler is available on every machine — tests and offline runs
  supply a fake), and the built suite is recorded
  (``ectt.cbt.record_compiled_suite``) in the project layout;
* **execute** is bound to :func:`ectt.cbt.reexecute.reexecute_isolated` over
  the recorded suite (no regeneration, binary integrity, per-test isolation
  with a timeout), with the executed run mapped onto the lifecycle's execution
  states;
* both delegates may be injected directly (``build=``/``execute=``) — tests
  bind fakes — and the port calls build first, then execute, exactly as the
  lifecycle's validation gate does.

A refused link plan or a failed recording is a *named build failure* of the
candidate (it reaches the run as a counted discard with its reason); a failure
of the compile port itself propagates — the lifecycle reports the port as
failed, and nothing is presented on the strength of a validation that did not
happen.

Satisfies: DSN-ATG-110 (composition), TOOL-ATG-050 (validation gate).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ectt.atg.binding import BoundValidationPort
from ectt.atg.errors import AtgError
from ectt.atg.lifecycle import BuildOutcome, ExecutionOutcome, GenerationCandidate
from ectt.bld.harness_build import HarnessBuildError, build_harness_suite
from ectt.cbt.errors import CbtError
from ectt.cbt.reexecute import CompiledSuiteRecord, reexecute_isolated
from ectt.exh.results import ExecutionMetadata
from ectt.tcm.datacases import DataDrivenTestCase, TestCaseExpected, refresh_digest

__all__ = [
    "BuildDelegate",
    "CompilePort",
    "CoverageSource",
    "ExecuteDelegate",
    "GenerationRunComposition",
    "compose_generation_run",
]

#: Builds one candidate: the harness-build step in production, a fake in tests.
BuildDelegate = Callable[[GenerationCandidate], BuildOutcome]

#: Executes one built candidate: the recorded re-execution in production.
ExecuteDelegate = Callable[[GenerationCandidate], ExecutionOutcome]

#: Produces the harness binary (a callable over the build request); production
#: binds a toolchain-driving port, tests and offline runs bind a fake.
CompilePort = Callable[[Any], str]

#: The constructs one candidate's run covered; ``None`` = the port cannot
#: measure and says so.
CoverageSource = Callable[[GenerationCandidate], Sequence[str]] | None


@dataclass(frozen=True)
class GenerationRunComposition:
    """The composed port plus the suite records its build step produced."""

    port: BoundValidationPort
    #: candidate id -> the record of the suite built for it (a read-only view).
    records: Mapping[str, CompiledSuiteRecord]


def compose_generation_run(
    root: Path | str,
    *,
    scope: str,
    environment: str,
    execution: ExecutionMetadata,
    compile_port: CompilePort,
    coverage_for: CoverageSource = None,
    total_constructs: int = 0,
    output_root: str | None = None,
    timeout_seconds: float = 30.0,
    argv_prefix: Sequence[str] = (),
    run_label: str = "atg",
    build: BuildDelegate | None = None,
    execute: ExecuteDelegate | None = None,
) -> GenerationRunComposition:
    """Bind the generation run's validation port to the engine components.

    Without ``build``/``execute`` the real components are bound: build runs
    the harness-build step for ``scope`` (plan-gated, recorded) and execute
    re-runs the recorded suite through the runner with per-test isolation.
    The delegates are bound in validation order — build first, then execute —
    which is the order the lifecycle's gate calls them in. Everything is
    deterministic: no wall clock in the outcomes, no network.
    """
    records: dict[str, CompiledSuiteRecord] = {}

    if build is None:
        build = _bind_build(
            root,
            scope=scope,
            environment=environment,
            execution=execution,
            compile_port=compile_port,
            output_root=output_root,
            records=records,
        )
    if execute is None:
        execute = _bind_execute(
            root,
            timeout_seconds=timeout_seconds,
            argv_prefix=argv_prefix,
            run_label=run_label,
            records=records,
        )

    port = BoundValidationPort(
        build=build,
        execute=execute,
        coverage_for=coverage_for,
        total_constructs=total_constructs,
    )
    # A live view: the build delegate records suites as candidates are built,
    # and callers read the records after the run.
    return GenerationRunComposition(port=port, records=MappingProxyType(records))


def _case_for(candidate: GenerationCandidate) -> DataDrivenTestCase:
    """The single-case suite a candidate validates against (D-02 digests)."""
    return refresh_digest(
        DataDrivenTestCase(
            case_id=candidate.candidate_id,
            unit=candidate.unit,
            function=candidate.function,
            inputs=candidate.inputs,
            expected=TestCaseExpected(),
            stubs=candidate.stubs,
            requirements=candidate.requirements,
        )
    )


def _bind_build(
    root: Path | str,
    *,
    scope: str,
    environment: str,
    execution: ExecutionMetadata,
    compile_port: CompilePort,
    output_root: str | None,
    records: dict[str, CompiledSuiteRecord],
) -> BuildDelegate:
    """The harness-build step as a build delegate (plan-gated, recorded)."""

    def build(candidate: GenerationCandidate) -> BuildOutcome:
        case = _case_for(candidate)
        try:
            result = build_harness_suite(
                root,
                scope=scope,
                environment=environment,
                execution=execution,
                cases=(case,),
                build=compile_port,
                output_root=output_root,
            )
        except (HarnessBuildError, CbtError) as exc:
            # A refused link plan or a failed recording is a named build
            # failure of this candidate. A failure of the compile port itself
            # propagates: the lifecycle reports a port failure, not a discard.
            return BuildOutcome(ok=False, diagnostics=(exc.message,))
        records[candidate.candidate_id] = result.record
        return BuildOutcome(ok=True)

    return build


def _bind_execute(
    root: Path | str,
    *,
    timeout_seconds: float,
    argv_prefix: Sequence[str],
    run_label: str,
    records: Mapping[str, CompiledSuiteRecord],
) -> ExecuteDelegate:
    """The recorded re-execution as an execute delegate (state-mapped)."""

    def execute(candidate: GenerationCandidate) -> ExecutionOutcome:
        record = records.get(candidate.candidate_id)
        if record is None:
            raise AtgError(
                f"candidate '{candidate.candidate_id}' was never built through the port",
                reason="not_built",
            )
        case = _case_for(candidate)
        rexec = reexecute_isolated(
            record,
            root,
            {case.case_id: case.content_digest},
            run_label=run_label,
            timeout_seconds=timeout_seconds,
            argv_prefix=argv_prefix,
        )
        return _outcome_of(candidate.candidate_id, rexec.run)

    return execute


def _outcome_of(candidate_id: str, run: Any) -> ExecutionOutcome:
    """Map an executed run onto the lifecycle's execution states."""
    outcomes = {r.test_id: r.outcome for r in run.result_set.results}
    if any(o == "timeout" for o in outcomes.values()):
        return ExecutionOutcome(state="timeout", detail="the harness exceeded the port's timeout")
    if any(o == "error" for o in outcomes.values()) or run.outcome == "incomplete":
        missing = ",".join(run.result_set.not_executed) or candidate_id
        return ExecutionOutcome(state="crash", detail=f"no result record for: {missing}")
    if run.outcome == "build_failed":
        return ExecutionOutcome(state="harness_error", detail="the recorded suite failed to build")
    if run.outcome in ("pass", "failed"):
        return ExecutionOutcome(state="completed", detail=run.outcome)
    return ExecutionOutcome(state="harness_error", detail=f"unmapped run outcome '{run.outcome}'")
