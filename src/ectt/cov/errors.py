# implements: TOOL-COV-010, TOOL-COV-020
"""Error classes for ectt code coverage (CMP-COV).

Satisfies: TOOL-COV-010, TOOL-COV-020.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from ectt.core.determinism import CoreError

__all__ = [
    "CoverageError",
    "CoverageParseError",
    "CoverageFormatError",
]


class CoverageError(CoreError):
    """Base exception for ectt coverage errors."""

    category: ClassVar[str] = "coverage"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "coverage_error",
        path: Path | str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, context=context)

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class CoverageParseError(CoverageError):
    """A coverage artifact could not be parsed (invalid JSON or structure)."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "coverage_parse_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class CoverageFormatError(CoverageParseError):
    """A coverage artifact carries a value the documented format forbids."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "coverage_format_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
