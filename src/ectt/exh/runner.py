# implements: DSN-EXH-010
"""Host execution of a built harness and run-attempt lifecycle.

The execute half of TOOL-EXE-010 (the build half is DSN-BLD-010/CMP-BLD):
invoke the built harness executable directly on the development host, capture
its result stream, and normalise it into per-test records. Run integrity
(T-14) is enforced here:

- NR-17 — an attempt is allocated *before* the build is invoked; a build
  failure is a first-class attempt record, not an absence of records.
- NR-18 — the run outcome is aggregated from finalized per-test records;
  the process exit status is never consulted to decide pass.
- NR-19 — before every run, each allocated test's artifact-recorded content
  digest is checked against its current content digest (D-02 option a); a
  stale test is not executed.

Satisfies: TOOL-EXE-010 (execute half), TOOL-EXE-020; T-14 NR-17/18/19.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path

from ectt.core.determinism import stable_id
from ectt.exh.errors import (
    DuplicateTestResultError,
    ExecutableMissingError,
    ExecutionLaunchError,
    InvalidAllocationError,
    MalformedResultStreamError,
    UnknownTestResultError,
    WrongAttemptStateError,
)
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultRecord,
    ResultSet,
    SourceLocation,
    aggregate_outcome,
    finalize_result,
)

__all__ = [
    "TestBinding",
    "RunAttempt",
    "allocate_attempt",
    "mark_built",
    "record_build_failure",
    "build_failed_run",
    "check_test_bindings",
    "ExecutedRun",
    "run_harness",
]

HarnessOutcome = str  # pass | fail | error as emitted by the harness protocol


@dataclass(frozen=True)
class TestBinding:
    """One allocated test and the test-content digest the artifact was built from."""

    test_id: str
    artifact_digest: str


@dataclass(frozen=True)
class RunAttempt:
    """A run attempt record (T-14 NR-17): allocated before the build runs.

    ``status`` is ``allocated`` until the build is reported, then ``built``
    or ``build_failed``. A build failure keeps the attempt as a first-class
    record carrying the structured build diagnostics.
    """

    execution: ExecutionMetadata
    allocations: tuple[TestBinding, ...]
    status: str
    attempt_id: str
    build_diagnostics: tuple[str, ...] = ()


def allocate_attempt(
    execution: ExecutionMetadata,
    allocations: Sequence[TestBinding],
) -> RunAttempt:
    """Allocate a run attempt before the build is invoked (T-14 NR-17)."""
    if not allocations:
        raise InvalidAllocationError("a run attempt requires at least one test allocation")
    seen: set[str] = set()
    for binding in allocations:
        if not isinstance(binding.test_id, str) or not binding.test_id.strip():
            raise InvalidAllocationError("test allocations require non-empty test ids")
        if not isinstance(binding.artifact_digest, str) or not binding.artifact_digest.strip():
            raise InvalidAllocationError(
                f"test allocation '{binding.test_id}' requires the artifact's "
                "recorded test-content digest (NR-19 binding check)"
            )
        if binding.test_id in seen:
            raise InvalidAllocationError(
                f"test '{binding.test_id}' is allocated more than once in the attempt"
            )
        seen.add(binding.test_id)
    attempt_id = stable_id(
        execution.where,
        execution.toolchain,
        execution.target_id,
        [binding.test_id for binding in allocations],
        [binding.artifact_digest for binding in allocations],
    )
    return RunAttempt(
        execution=execution,
        allocations=tuple(allocations),
        status="allocated",
        attempt_id=attempt_id,
    )


def mark_built(attempt: RunAttempt) -> RunAttempt:
    """Record that the attempt's build succeeded; execution may proceed."""
    if attempt.status != "allocated":
        raise WrongAttemptStateError(
            f"attempt '{attempt.attempt_id}' is '{attempt.status}', not 'allocated'; "
            "a build can be reported only once"
        )
    return replace(attempt, status="built")


def record_build_failure(
    attempt: RunAttempt,
    diagnostics: Sequence[str],
) -> RunAttempt:
    """Record a build failure as a first-class attempt record (T-14 NR-17)."""
    if attempt.status != "allocated":
        raise WrongAttemptStateError(
            f"attempt '{attempt.attempt_id}' is '{attempt.status}', not 'allocated'; "
            "a build can be reported only once"
        )
    return replace(attempt, status="build_failed", build_diagnostics=tuple(diagnostics))


def build_failed_run(attempt: RunAttempt) -> ExecutedRun:
    """Turn a build-failed attempt into a first-class run outcome.

    The outcome is ``build_failed`` — never ``pass`` — and no result records
    are fabricated; the diagnostics ride with the attempt.
    """
    if attempt.status != "build_failed":
        raise WrongAttemptStateError(
            f"attempt '{attempt.attempt_id}' is '{attempt.status}', not 'build_failed'"
        )
    result_set = ResultSet(
        run_id=attempt.attempt_id,
        execution=attempt.execution,
        results=(),
        partial=True,
        not_executed=tuple(binding.test_id for binding in attempt.allocations),
    )
    return ExecutedRun(
        attempt=attempt,
        result_set=result_set,
        outcome="build_failed",
        stale_ids=(),
    )


@dataclass(frozen=True)
class BindingCheckResult:
    """Outcome of the NR-19 binding check over one attempt's allocations."""

    bound: tuple[str, ...]
    stale: tuple[str, ...]


def check_test_bindings(
    attempt: RunAttempt,
    current_digests: Mapping[str, str],
) -> BindingCheckResult:
    """Check every allocated test's artifact digest against current content.

    A test whose artifact-recorded digest differs from its current content
    digest is stale (D-02 option a: digest binding is the staleness
    mechanism) and must not be executed (T-14 NR-19).
    """
    bound: list[str] = []
    stale: list[str] = []
    for binding in attempt.allocations:
        current = current_digests.get(binding.test_id)
        if current is None or current != binding.artifact_digest:
            stale.append(binding.test_id)
        else:
            bound.append(binding.test_id)
    return BindingCheckResult(bound=tuple(bound), stale=tuple(stale))


@dataclass(frozen=True)
class ExecutedRun:
    """The outcome of one run attempt: attempt record plus normalised results."""

    attempt: RunAttempt
    result_set: ResultSet
    outcome: str
    stale_ids: tuple[str, ...] = ()


_RESULT_LINE_TOKENS = 3  # RESULT <test_id> <outcome>
_FAILURE_LINE_TOKENS = 7  # FAILURE <test_id> <assertion> <expected> <actual> <file> <line>
_HARNESS_OUTCOMES = ("pass", "fail", "error")


def _parse_result_stream(
    text: str,
    allocated_ids: frozenset[str],
    digests_by_test: Mapping[str, str],
) -> tuple[ResultRecord, ...]:
    """Normalise the harness result stream into finalized records (EXE-020).

    Blank and non-protocol lines are ignored (framework chatter). A FAILURE
    line may precede or follow its RESULT line. Protocol violations — unknown
    test, duplicate result, malformed tokens, a fail without failures, a
    failure without a result — are named errors. Records finalize in a
    second pass so a failure record is attached regardless of line order.
    """
    outcomes: dict[str, str] = {}
    failures: dict[str, list[AssertionFailure]] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        tokens = line.split()
        if tokens[0] == "RESULT":
            if len(tokens) != _RESULT_LINE_TOKENS:
                raise MalformedResultStreamError(
                    f"RESULT line needs {_RESULT_LINE_TOKENS} tokens: '{raw_line}'"
                )
            _, test_id, outcome = tokens
            if test_id not in allocated_ids:
                raise UnknownTestResultError(
                    f"harness reported a result for unallocated test '{test_id}'"
                )
            if test_id in outcomes:
                raise DuplicateTestResultError(
                    f"harness reported more than one result for test '{test_id}'"
                )
            if outcome not in _HARNESS_OUTCOMES:
                raise MalformedResultStreamError(
                    f"harness outcome '{outcome}' for test '{test_id}' is not one "
                    f"of {_HARNESS_OUTCOMES}"
                )
            outcomes[test_id] = outcome
        elif tokens[0] == "FAILURE":
            if len(tokens) != _FAILURE_LINE_TOKENS:
                raise MalformedResultStreamError(
                    f"FAILURE line needs {_FAILURE_LINE_TOKENS} tokens: '{raw_line}'"
                )
            _, test_id, assertion, expected, actual, file, line = tokens
            if test_id not in allocated_ids:
                raise UnknownTestResultError(
                    f"harness reported a failure for unallocated test '{test_id}'"
                )
            if not line.isdigit() or int(line) < 1:
                raise MalformedResultStreamError(
                    f"FAILURE line for '{test_id}' has a non-positive line number: '{raw_line}'"
                )
            failures.setdefault(test_id, []).append(
                AssertionFailure(
                    assertion=assertion,
                    expected=expected,
                    actual=actual,
                    location=SourceLocation(file=file, line=int(line)),
                )
            )
        # any other line is framework chatter and is ignored
    orphaned = sorted(tid for tid in failures if tid not in outcomes)
    if orphaned:
        raise MalformedResultStreamError(
            f"FAILURE record(s) without a matching RESULT line: {orphaned}"
        )
    for test_id in sorted(tid for tid in failures if tid in outcomes):
        if outcomes[test_id] == "pass":
            raise MalformedResultStreamError(
                f"passing test '{test_id}' cannot carry a FAILURE record"
            )
    return tuple(
        finalize_result(
            test_id,
            outcomes[test_id],
            digests_by_test[test_id],
            failures=tuple(failures.get(test_id, ())),
        )
        for test_id in sorted(outcomes)
    )


def run_harness(
    attempt: RunAttempt,
    executable: Path | str,
    *,
    current_digests: Mapping[str, str],
    argv_prefix: Sequence[str] = (),
) -> ExecutedRun:
    """Execute the built harness on the host and normalise its result stream.

    Enforces, in order: the attempt is in ``built`` state (a build-failed
    attempt never runs — use :func:`build_failed_run`), the NR-19 binding
    check (a stale test's results are not accepted as current evidence; the
    test lands in ``not_executed``), then direct execution of the executable
    (no shell, no network) with stream normalisation into finalized records
    (EXE-020). The run outcome is aggregated over every allocated test from
    finalized records (NR-18); the process exit status is ignored.

    ``argv_prefix`` lets a caller prepend interpreter arguments (used by the
    test suite for interpreter-hosted harness stubs); production passes
    nothing and the executable is invoked directly.
    """
    if attempt.status == "build_failed":
        raise WrongAttemptStateError(
            f"attempt '{attempt.attempt_id}' failed to build; a build-failed "
            "attempt never executes (use build_failed_run)"
        )
    if attempt.status != "built":
        raise WrongAttemptStateError(
            f"attempt '{attempt.attempt_id}' is '{attempt.status}', not 'built'; "
            "report the build outcome before running"
        )
    binding = check_test_bindings(attempt, current_digests)
    digests_by_test = {b.test_id: b.artifact_digest for b in attempt.allocations}
    allocated_ids = frozenset(digests_by_test)
    stale_ids = frozenset(binding.stale)

    executable_path = Path(executable)
    if not executable_path.is_file():
        raise ExecutableMissingError(
            f"built harness executable '{executable_path}' does not exist",
            path=executable_path,
        )
    stdout = ""
    try:
        completed = subprocess.run(
            [*argv_prefix, str(executable_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=None,
        )
        stdout = completed.stdout
    except OSError as exc:
        raise ExecutionLaunchError(
            f"cannot launch harness executable '{executable_path}': {exc}",
            path=executable_path,
        ) from exc

    records = _parse_result_stream(stdout, allocated_ids, digests_by_test)
    # A stale test's results are rejected: they describe content the artifact
    # was not built from (NR-19), so they never become current evidence.
    accepted = tuple(record for record in records if record.test_id not in stale_ids)
    accepted_ids = {record.test_id for record in accepted}
    missing = tuple(
        b.test_id for b in attempt.allocations if b.test_id not in accepted_ids
    )
    not_executed = tuple(sorted(set(missing) | set(binding.stale)))
    result_set = ResultSet(
        run_id=attempt.attempt_id,
        execution=attempt.execution,
        results=accepted,
        partial=bool(not_executed),
        not_executed=not_executed,
    )
    outcome = aggregate_outcome(
        {record.test_id: record for record in accepted},
        [b.test_id for b in attempt.allocations],
    )
    return ExecutedRun(
        attempt=attempt,
        result_set=result_set,
        outcome=outcome,
        stale_ids=binding.stale,
    )
