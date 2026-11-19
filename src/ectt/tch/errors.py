"""Error classes for ectt toolchain configuration.

Satisfies: TOOL-PLG-020, TOOL-TCH-020.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from ectt.core.fs import CoreError

__all__ = [
    "TchError",
    "CompilerConfigReadError",
    "InvalidCompilerConfigError",
    "ConfigSchemaVersionError",
    "UnknownCoverageKindError",
    "DuplicateCompilerConfigError",
    "UnknownCompilerConfigError",
]


class TchError(CoreError):
    """Base exception for ectt toolchain operations."""

    category: ClassVar[str] = "toolchain"

    def __init__(
        self,
        message: str,
        *,
        reason: str = "toolchain_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class CompilerConfigReadError(TchError):
    """Raised when a compiler configuration file is missing or unreadable."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "compiler_config_read_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class InvalidCompilerConfigError(TchError):
    """Raised when a compiler configuration document is structurally invalid."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "invalid_compiler_config",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ConfigSchemaVersionError(TchError):
    """Raised when the configuration schema version is missing or unsupported."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "config_schema_version_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownCoverageKindError(TchError):
    """Raised when a configuration declares a coverage kind outside the vocabulary."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown_coverage_kind",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class DuplicateCompilerConfigError(TchError):
    """Raised when a compiler configuration name is registered twice."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "duplicate_compiler_config",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownCompilerConfigError(TchError):
    """Raised when a compiler configuration name is not registered."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unknown_compiler_config",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
