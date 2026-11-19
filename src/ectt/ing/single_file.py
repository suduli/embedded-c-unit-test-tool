"""Single-file ingestion path without a build system (WP-ING-02).

When no build system is available, the tool ingests a single `.c` source with
user-supplied include paths and preprocessor definitions into the same
compilation-database model the primary path produces.

Satisfies: TOOL-ING-060.
"""

from __future__ import annotations

from pathlib import Path

from ectt.ing.errors import IngestionError
from ectt.ing.model import CompilationDatabase, CompilerInvocation, TranslationUnit

__all__ = [
    "SingleSourceReadError",
    "NotCSourceError",
    "ingest_single_source",
]


class SingleSourceReadError(IngestionError):
    """Raised when the single source file is missing or unreadable."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "single_source_read_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class NotCSourceError(IngestionError):
    """Raised when the single source is not a `.c` file."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "not_c_source",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


def ingest_single_source(
    source_path: Path | str,
    *,
    include_paths: tuple[str, ...] = (),
    preprocessor_definitions: tuple[str, ...] = (),
    working_directory: Path | str | None = None,
    executable: str = "cc",
) -> CompilationDatabase:
    """Ingest one `.c` file with user-supplied include paths and defines.

    The produced database carries exactly one translation unit whose include
    paths and preprocessor definitions are the user-supplied ones, in order.
    The recorded invocation is the equivalent direct compile command.
    """
    source = Path(source_path)
    try:
        source.read_text(encoding="utf-8")
    except OSError as exc:
        raise SingleSourceReadError(
            f"cannot read single-file source: {exc}",
            path=source,
        ) from exc
    if source.suffix != ".c":
        raise NotCSourceError(
            f"single-file ingestion requires a .c source, got '{source.name}'",
            path=source,
        )
    work_dir = Path(working_directory) if working_directory is not None else Path.cwd()
    arguments: list[str] = [f"-I{include}" for include in include_paths]
    arguments.extend(f"-D{definition}" for definition in preprocessor_definitions)
    arguments.append(source.as_posix())
    unit = TranslationUnit(
        source_path=source.as_posix(),
        working_directory=work_dir.as_posix(),
        include_paths=tuple(include_paths),
        preprocessor_definitions=tuple(preprocessor_definitions),
        compiler_invocation=CompilerInvocation(
            executable=executable,
            arguments=tuple(arguments),
        ),
    )
    return CompilationDatabase(translation_units=(unit,))
