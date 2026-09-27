# implements: DSN-ING-010, DSN-ING-020
"""Error classes for ectt compilation database ingestion.

Satisfies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030, TOOL-ING-040.
"""

from __future__ import annotations

from pathlib import Path

from ectt.core.determinism import CoreError

__all__ = [
    "IngestionError",
    "CompilationDatabaseNotFoundError",
    "CompilationDatabaseFormatError",
    "MissingEntryKeyError",
    "MissingCommandOrArgumentsError",
    "CommandParseError",
    "CMakeConfigureError",
]


class IngestionError(CoreError):
    """Base exception for ectt compilation database ingestion errors."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "ingestion_error",
        path: Path | str | None = None,
        entry_index: int | None = None,
        entry_file: str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.entry_index = entry_index
        self.entry_file = entry_file

    def __str__(self) -> str:
        details: list[str] = [f"reason={self.reason}"]
        if self.path is not None:
            details.append(f"path={self.path}")
        if self.entry_index is not None:
            details.append(f"entry_index={self.entry_index}")
        if self.entry_file is not None:
            details.append(f"entry_file={self.entry_file}")
        return f"{self.message} [{', '.join(details)}]"


class CompilationDatabaseNotFoundError(IngestionError):
    """Raised when compile_commands.json does not exist at the specified path."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "compdb_not_found",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class CompilationDatabaseFormatError(IngestionError):
    """Raised when compile_commands.json contains invalid JSON or non-array root."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "compdb_format_error",
        path: Path | str | None = None,
        entry_index: int | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path, entry_index=entry_index)


class MissingEntryKeyError(IngestionError):
    """Raised when an entry is missing a required key such as 'file' or 'directory'."""

    def __init__(
        self,
        message: str,
        *,
        missing_key: str,
        reason: str = "missing_entry_key",
        path: Path | str | None = None,
        entry_index: int | None = None,
        entry_file: str | None = None,
    ) -> None:
        super().__init__(
            message,
            reason=reason,
            path=path,
            entry_index=entry_index,
            entry_file=entry_file,
        )
        self.missing_key = missing_key

    def __str__(self) -> str:
        base = super().__str__()
        return f"{base[:-1]}, missing_key={self.missing_key}]"


class MissingCommandOrArgumentsError(IngestionError):
    """Raised when an entry contains neither 'command' nor 'arguments'."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "missing_command_or_arguments",
        path: Path | str | None = None,
        entry_index: int | None = None,
        entry_file: str | None = None,
    ) -> None:
        super().__init__(
            message,
            reason=reason,
            path=path,
            entry_index=entry_index,
            entry_file=entry_file,
        )


class CommandParseError(IngestionError):
    """Raised when parsing a command string fails (e.g. unclosed quotes)."""

    def __init__(
        self,
        message: str,
        *,
        command: str | None = None,
        reason: str = "command_parse_error",
        path: Path | str | None = None,
        entry_index: int | None = None,
        entry_file: str | None = None,
    ) -> None:
        super().__init__(
            message,
            reason=reason,
            path=path,
            entry_index=entry_index,
            entry_file=entry_file,
        )
        self.command = command


class CMakeConfigureError(IngestionError):
    """Raised when generating a compilation database via CMake fails."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "cmake_configure_error",
        exit_code: int | None = None,
        stderr: str | None = None,
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)
        self.exit_code = exit_code
        self.stderr = stderr
