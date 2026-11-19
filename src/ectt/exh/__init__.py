"""ECTT Host Execution.

Provides the execute half of TOOL-EXE-010: run-attempt lifecycle with build
failure as a first-class record (T-14 NR-17), binding checks before every run
(T-14 NR-19, D-02 digest binding), normalised per-test result records
(TOOL-EXE-020, SDD-002 §6), and run aggregation from finalized records
(T-14 NR-18).
"""

from ectt.exh.errors import (
    DuplicateTestResultError,
    ExecutableMissingError,
    ExecutionLaunchError,
    ExhError,
    InvalidAllocationError,
    InvalidResultRecordError,
    MalformedResultStreamError,
    UnknownTestResultError,
    WrongAttemptStateError,
)
from ectt.exh.results import (
    EXECUTED_OUTCOMES,
    AssertionFailure,
    ExecutionMetadata,
    ResultRecord,
    ResultSet,
    SourceLocation,
    aggregate_outcome,
    dump_result_set,
    finalize_result,
    result_set_to_dict,
)
from ectt.exh.runner import (
    BindingCheckResult,
    ExecutedRun,
    RunAttempt,
    TestBinding,
    allocate_attempt,
    build_failed_run,
    check_test_bindings,
    mark_built,
    record_build_failure,
    run_harness,
)

__all__ = [
    # Errors
    "ExhError",
    "InvalidResultRecordError",
    "InvalidAllocationError",
    "WrongAttemptStateError",
    "UnknownTestResultError",
    "DuplicateTestResultError",
    "MalformedResultStreamError",
    "ExecutableMissingError",
    "ExecutionLaunchError",
    # Results
    "EXECUTED_OUTCOMES",
    "SourceLocation",
    "AssertionFailure",
    "ResultRecord",
    "finalize_result",
    "ExecutionMetadata",
    "ResultSet",
    "aggregate_outcome",
    "result_set_to_dict",
    "dump_result_set",
    # Runner
    "TestBinding",
    "RunAttempt",
    "allocate_attempt",
    "mark_built",
    "record_build_failure",
    "build_failed_run",
    "check_test_bindings",
    "BindingCheckResult",
    "ExecutedRun",
    "run_harness",
]
