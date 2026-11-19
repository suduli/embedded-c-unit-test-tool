"""Error classes for ectt test case management.

Satisfies: TOOL-TCD-010.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "TcmError",
    "InvalidTestCaseError",
    "TestCaseReadError",
    "NotAgainstHarnessError",
    "DuplicateTestCaseError",
    "UnknownTestCaseError",
    "InvalidTestCasesFileError",
    "MissingCaseFieldError",
    "ValueParseError",
    "InvalidComparisonSpecError",
    "InvalidSelectionError",
    "RangeExpansionError",
    "RangeCheckingError",
]


class TcmError(CoreError):
    """Base exception for ectt test case management."""

    category: ClassVar[str] = "testcase"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "testcase_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidTestCaseError(TcmError):
    """Raised when a test case identifier or field is malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_test_case",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class TestCaseReadError(TcmError):
    """Raised when a C test case source file is missing or unreadable."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "testcase_read_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class NotAgainstHarnessError(TcmError):
    """Raised when a C source does not include the harness it targets."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "not_against_harness",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class DuplicateTestCaseError(TcmError):
    """Raised when a test case identifier is registered twice."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "duplicate_test_case",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownTestCaseError(TcmError):
    """Raised when a test case identifier is not registered."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown_test_case",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidTestCasesFileError(TcmError):
    """Raised when a data-driven test cases file is structurally malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_test_cases_file",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class MissingCaseFieldError(TcmError):
    """Raised when a required test case section or field is absent or empty."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "missing_case_field",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ValueParseError(TcmError):
    """Raised when a comparison value is not valid for its declared type."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "value_parse_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidComparisonSpecError(TcmError):
    """Raised when a comparison specification (types, tolerances) is malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_comparison_spec",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidSelectionError(TcmError):
    """Raised when a selection expression or its operands are malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_selection",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class RangeExpansionError(TcmError):
    """Raised when a range specification is malformed or expands to nothing."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "range_expansion_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class RangeCheckingError(TcmError):
    """Raised when the tool's own range check refuses out-of-range inputs."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "range_checking_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
