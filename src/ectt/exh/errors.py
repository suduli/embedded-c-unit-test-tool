# implements: DSN-EXH-010
"""Error classes for ectt host execution.

Satisfies: TOOL-EXE-010, TOOL-EXE-020 (named-error discipline).
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "ExhError",
    "InvalidResultRecordError",
    "InvalidAllocationError",
    "WrongAttemptStateError",
    "UnknownTestResultError",
    "DuplicateTestResultError",
    "MalformedResultStreamError",
    "ExecutableMissingError",
    "ExecutionLaunchError",
]


class ExhError(EcttError):
    """Base exception for ectt host execution."""

    category: ClassVar[str] = "execution"


class InvalidResultRecordError(ExhError):
    """Raised when a result record would violate its construction invariants."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_result_record",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidAllocationError(ExhError):
    """Raised when a run attempt's test allocations are malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_allocation",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class WrongAttemptStateError(ExhError):
    """Raised when an operation does not match the attempt's lifecycle state."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "wrong_attempt_state",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownTestResultError(ExhError):
    """Raised when the harness reports a result for an unallocated test."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown_test_result",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class DuplicateTestResultError(ExhError):
    """Raised when the harness reports more than one result for one test."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "duplicate_test_result",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class MalformedResultStreamError(ExhError):
    """Raised when the harness result stream violates the RESULT/FAILURE protocol."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "malformed_result_stream",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ExecutableMissingError(ExhError):
    """Raised when the built harness executable does not exist."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "executable_missing",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ExecutionLaunchError(ExhError):
    """Raised when the harness executable cannot be launched."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "execution_launch_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
