"""Error classes for ectt harness generation.

Satisfies: TOOL-HAR-010.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "GenError",
    "NoUnitError",
    "AmbiguousUnitError",
    "UnknownUnitError",
    "UnitNotParsedError",
]


class GenError(CoreError):
    """Base exception for ectt generation operations."""

    category: ClassVar[str] = "generation"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "generation_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class NoUnitError(GenError):
    """Raised when the analysis model contains no units to generate from."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "no_unit",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class AmbiguousUnitError(GenError):
    """Raised when no UUT is designated and the model has several units."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "ambiguous_unit",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownUnitError(GenError):
    """Raised when the designated UUT path is not present in the model."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown_unit",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnitNotParsedError(GenError):
    """Raised when the designated unit did not parse successfully."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unit_not_parsed",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
