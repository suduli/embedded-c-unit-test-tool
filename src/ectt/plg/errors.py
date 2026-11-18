"""Error classes for ectt extension points.

Satisfies: TOOL-PLG-010.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "PlgError",
    "InvalidExtensionPointError",
    "DuplicateExtensionPointError",
    "UnknownExtensionPointError",
]


class PlgError(CoreError):
    """Base exception for ectt extension-point operations."""

    category: ClassVar[str] = "extension"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "extension_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidExtensionPointError(PlgError):
    """Raised when an extension-point descriptor is malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_extension_point",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class DuplicateExtensionPointError(PlgError):
    """Raised when an extension point is registered under an identifier already in use."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "duplicate_extension_point",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownExtensionPointError(PlgError):
    """Raised when a lookup names an extension point that is not defined."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown_extension_point",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
