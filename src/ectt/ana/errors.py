# implements: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090
"""Error classes for ectt C front-end binding and analysis.

Satisfies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
"""

from __future__ import annotations

from pathlib import Path

from ectt.core.determinism import CoreError

__all__ = [
    "AnalysisError",
    "LibclangError",
    "LibclangNotFoundError",
    "LibclangLoadError",
    "LibclangVersionError",
    "DialectError",
    "UnsupportedDialectError",
    "SourceFileNotFoundError",
    "FrontendParseError",
    "ExtractionError",
    "ExtractionRefusedError",
]


class AnalysisError(CoreError):
    """Base exception for ectt analysis and C front-end errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "analysis_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class LibclangError(AnalysisError):
    """Base exception for libclang library and binding issues."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "libclang_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class LibclangNotFoundError(LibclangError):
    """Raised when the libclang Python package/bindings cannot be imported."""

    def __init__(
        self,
        message: str = "libclang Python bindings are not installed or cannot be found",
        *,
        reason: str = "libclang_not_found",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class LibclangLoadError(LibclangError):
    """Raised when the libclang native shared library fails to load."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "libclang_load_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class LibclangVersionError(LibclangError):
    """Raised when loaded libclang version is below the required version floor."""

    def __init__(
        self,
        message: str,
        *,
        version: str | None = None,
        floor: str = "18.1",
        reason: str = "libclang_version_below_floor",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.version = version
        self.floor = floor

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}", f"floor={self.floor}"]
        if self.version is not None:
            details.append(f"version={self.version}")
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class DialectError(AnalysisError):
    """Base exception for C language standard dialect errors."""

    def __init__(
        self,
        message: str,
        *,
        dialect: str | None = None,
        reason: str = "dialect_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.dialect = dialect

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.dialect is not None:
            details.append(f"dialect={self.dialect}")
        if self.path is not None:
            details.append(f"path={self.path}")
        return f"{self.message} [{', '.join(details)}]"


class UnsupportedDialectError(DialectError):
    """Raised when an unsupported or unrecognized C dialect standard is specified."""

    def __init__(
        self,
        message: str,
        *,
        dialect: str | None = None,
        reason: str = "unsupported_dialect",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, dialect=dialect, reason=reason, path=path)


class SourceFileNotFoundError(AnalysisError):
    """Raised when a translation unit source file does not exist on disk."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "source_file_not_found",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class FrontendParseError(AnalysisError):
    """Raised when libclang encounters an unrecoverable parse or translation unit loading failure."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "frontend_parse_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ExtractionError(AnalysisError):
    """Base exception for interface, type, or global extraction errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "extraction_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ExtractionRefusedError(ExtractionError):
    """Raised when extraction is refused on a failed or unparsed translation unit."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "extraction_refused_failed_unit",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
