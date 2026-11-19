"""Error classes for the ectt CLI (WP-CLI-01).

Satisfies: TOOL-CIC-010, TOOL-NFR-090.
"""

from __future__ import annotations

from typing import ClassVar

from ectt.core.errors import EcttError

__all__ = [
    "CliError",
    "OperationNotAvailable",
]


class CliError(EcttError):
    """Base exception for CLI failures."""

    category: ClassVar[str] = "cli"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "cli_error",
    ) -> None:
        super().__init__(message, reason=reason)


class OperationNotAvailable(CliError):
    """Raised when a catalogue operation has no executor wired in this build.

    The catalogue publishes the capability surface; executors arrive with the
    packages that implement each operation. Failing safe here never fakes a
    success (TOOL-NFR-090).
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str,
        reason: str = "operation_not_available",
    ) -> None:
        super().__init__(message, reason=reason)
        self.operation = operation
