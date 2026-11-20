# implements: DSN-EXH-010
"""Normalised per-test result records and result sets (SDD-002 §6, S3).

One result record per test case, normalised at the runner boundary so
nothing downstream knows which framework ran. Records bind to the digest of
the test definition they executed (D-02 option a, SDD-003 §7 amendment) and
are constructed only through :func:`finalize_result`, which enforces the
run-integrity invariants (T-14 NR-18): a pass carries no failures, a fail
identifies the assertion, expected value, actual value, and source location,
and every executed record binds to a non-empty test digest.

A result set also carries the run-level fields the S3 seam fixes:
``partial`` and ``not_executed`` are fields of the data, not report options,
so a subset run cannot be presented as a full one (SDD-002 §6.1).

Satisfies: TOOL-EXE-020; SDD-002 §6 (S3) model; T-14 NR-18.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Literal

from ectt.core.determinism import canonical_json
from ectt.exh.errors import InvalidResultRecordError

__all__ = [
    "TestOutcome",
    "EXECUTED_OUTCOMES",
    "SourceLocation",
    "AssertionFailure",
    "ResultRecord",
    "finalize_result",
    "ExecutionMetadata",
    "NotExecutedReason",
    "ResultSet",
    "aggregate_outcome",
    "result_set_to_dict",
    "dump_result_set",
]

TestOutcome = Literal["pass", "fail", "error", "timeout", "not_run"]
"""Outcome vocabulary fixed by the S3 seam (SDD-002 §6)."""

EXECUTED_OUTCOMES: tuple[str, ...] = ("pass", "fail", "error", "timeout")
"""Outcomes that mean the test actually ran (everything but not_run)."""

_NOT_EXECUTED_REASONS: tuple[str, ...] = ("stale", "unexecuted")
NotExecutedReason = Literal["stale", "unexecuted"]

_RESULT_SET_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class SourceLocation:
    """Where a failing assertion lives: file plus 1-based line."""

    file: str
    line: int
    column: int | None = None


@dataclass(frozen=True)
class AssertionFailure:
    """One failed assertion: what was checked, what was expected, what came out."""

    assertion: str
    expected: str
    actual: str
    location: SourceLocation


@dataclass(frozen=True)
class ResultRecord:
    """Per-test result, normalised at the runner boundary.

    Construct only through :func:`finalize_result`; the frozen fields carry
    the finalized, validated state (T-14 NR-18).
    """

    test_id: str
    outcome: TestOutcome
    test_digest: str
    failures: tuple[AssertionFailure, ...] = ()
    duration_ms: int | None = None


def finalize_result(
    test_id: str,
    outcome: str,
    test_digest: str,
    *,
    failures: Iterable[AssertionFailure] = (),
    duration_ms: int | None = None,
) -> ResultRecord:
    """Construct a finalized result record, enforcing the NR-18 invariants.

    - ``test_id`` and ``test_digest`` must be non-empty (a result binds to the
      digest of the test definition it executed, D-02 option a).
    - ``outcome`` must be a member of the S3 vocabulary.
    - ``pass`` carries no failures; ``fail`` carries at least one, each with
      non-empty assertion/expected/actual and a located file and line.
    - ``error``, ``timeout``, and ``not_run`` carry no assertion failures.
    """
    if not isinstance(test_id, str) or not test_id.strip():
        raise InvalidResultRecordError("result record requires a non-empty test id")
    if not isinstance(test_digest, str) or not test_digest.strip():
        raise InvalidResultRecordError(
            f"result record for '{test_id}' requires a non-empty test digest "
            "(digest binding is the staleness mechanism, SDD-003 §7)"
        )
    if outcome not in ("pass", "fail", "error", "timeout", "not_run"):
        raise InvalidResultRecordError(
            f"result record for '{test_id}' has unknown outcome '{outcome}'"
        )
    failure_tuple = tuple(failures)
    if outcome == "pass" and failure_tuple:
        raise InvalidResultRecordError(
            f"result record for '{test_id}' is a pass but carries failures"
        )
    if outcome == "fail":
        if not failure_tuple:
            raise InvalidResultRecordError(
                f"result record for '{test_id}' is a fail but names no assertion"
            )
        for failure in failure_tuple:
            if not failure.assertion.strip() or not failure.expected.strip() or not failure.actual.strip():
                raise InvalidResultRecordError(
                    f"result record for '{test_id}' has a failure missing "
                    "assertion, expected, or actual value"
                )
            if not failure.location.file.strip() or failure.location.line < 1:
                raise InvalidResultRecordError(
                    f"result record for '{test_id}' has a failure without a "
                    "source file and 1-based line"
                )
    if outcome in ("error", "timeout", "not_run") and failure_tuple:
        raise InvalidResultRecordError(
            f"result record for '{test_id}' has outcome '{outcome}' but carries "
            "assertion failures; diagnostics belong to a fail record"
        )
    if duration_ms is not None and duration_ms < 0:
        raise InvalidResultRecordError(
            f"result record for '{test_id}' has a negative duration"
        )
    return ResultRecord(
        test_id=test_id,
        outcome=outcome,  # type: ignore[arg-type]
        test_digest=test_digest,
        failures=failure_tuple,
        duration_ms=duration_ms,
    )


@dataclass(frozen=True)
class ExecutionMetadata:
    """Where and how a run executed; carried as metadata, never branched on."""

    where: str
    toolchain: str
    target_id: str | None = None
    order_seed: int | None = None


@dataclass(frozen=True)
class ResultSet:
    """One run's normalised results (SDD-002 §6, S3)."""

    run_id: str
    execution: ExecutionMetadata
    results: tuple[ResultRecord, ...] = ()
    partial: bool = False
    not_executed: tuple[str, ...] = ()
    infrastructure_faults: tuple[str, ...] = ()
    schema_version: str = _RESULT_SET_SCHEMA_VERSION


def aggregate_outcome(
    results: Mapping[str, ResultRecord],
    allocated: Iterable[str],
) -> Literal["pass", "failed", "incomplete"]:
    """Aggregate per-test records into a run outcome (T-14 NR-18).

    ``pass`` only when every allocated test has a finalized record with
    outcome ``pass``. Any executed failure makes it ``failed``. Any allocated
    test without a finalized record — unexecuted, stale, or missing — makes
    it ``incomplete``. The process exit status is never consulted.
    """
    allocated_ids = list(allocated)
    missing = [tid for tid in allocated_ids if tid not in results]
    if missing:
        return "incomplete"
    executed = [results[tid] for tid in allocated_ids]
    if any(record.outcome in ("fail", "error", "timeout") for record in executed):
        return "failed"
    return "pass"


def result_set_to_dict(result_set: ResultSet) -> dict[str, Any]:
    """Serialize to the S3 exchange-model dictionary (JSON per ADR-002)."""
    execution: dict[str, Any] = {
        "where": result_set.execution.where,
        "toolchain": result_set.execution.toolchain,
    }
    if result_set.execution.target_id is not None:
        execution["target_id"] = result_set.execution.target_id
    if result_set.execution.order_seed is not None:
        execution["order_seed"] = result_set.execution.order_seed
    results: list[dict[str, Any]] = []
    for record in result_set.results:
        entry: dict[str, Any] = {
            "test_id": record.test_id,
            "outcome": record.outcome,
            "test_digest": record.test_digest,
        }
        if record.duration_ms is not None:
            entry["duration_ms"] = record.duration_ms
        if record.failures:
            entry["failures"] = [
                {
                    "assertion": failure.assertion,
                    "expected": failure.expected,
                    "actual": failure.actual,
                    "location": {
                        "file": failure.location.file,
                        "line": failure.location.line,
                        **({"column": failure.location.column} if failure.location.column is not None else {}),
                    },
                }
                for failure in record.failures
            ]
        results.append(entry)
    return {
        "schema_version": result_set.schema_version,
        "run_id": result_set.run_id,
        "partial": result_set.partial,
        "not_executed": list(result_set.not_executed),
        "execution": execution,
        "results": results,
        "infrastructure_faults": list(result_set.infrastructure_faults),
    }


def dump_result_set(result_set: ResultSet) -> str:
    """Byte-deterministic canonical JSON with ``schema_version`` first."""
    return canonical_json(
        result_set_to_dict(result_set),
        first_keys=("schema_version",),
    )
