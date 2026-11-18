"""Error classes for ectt build orchestration.

Satisfies: TOOL-EXE-080.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "BldError",
    "DuplicateArtifactError",
    "InvalidArtifactSpecError",
]


class BldError(CoreError):
    """Base exception for ectt build operations."""

    category: ClassVar[str] = "build"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "build_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class DuplicateArtifactError(BldError):
    """Raised when two requested artifacts claim the same output path."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "duplicate_artifact",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidArtifactSpecError(BldError):
    """Raised when an artifact specification is malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_artifact_spec",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
