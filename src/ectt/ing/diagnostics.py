"""Ingestion diagnostics (WP-ING-03).

A validation pass over an ingested database that detects and reports, with
the offending entry and subject identified: sources missing on disk, include
paths that do not resolve on disk, and compiler flags outside the documented
recognized vocabulary.

Satisfies: TOOL-ING-070.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ectt.ing.model import CompilationDatabase

__all__ = [
    "KIND_MISSING_SOURCE",
    "KIND_UNRESOLVABLE_INCLUDE",
    "KIND_UNKNOWN_FLAG",
    "RECOGNIZED_FLAG_PREFIXES",
    "RECOGNIZED_FLAG_EXACT",
    "IngestionDiagnostic",
    "collect_ingestion_diagnostics",
]

KIND_MISSING_SOURCE = "missing_source"
KIND_UNRESOLVABLE_INCLUDE = "unresolvable_include"
KIND_UNKNOWN_FLAG = "unknown_flag"

# Documented recognized vocabulary: any argument matching one of these
# prefixes, or one of the exact tokens, is recognized; anything else is
# reported as an unknown flag (TOOL-ING-070).
RECOGNIZED_FLAG_PREFIXES: tuple[str, ...] = (
    "-I",
    "-D",
    "-U",
    "-isystem",
    "-include",
    "-std",
    "-o",
    "-g",
    "-O",
    "-W",
    "-f",
    "-m",
    "-M",
)
RECOGNIZED_FLAG_EXACT: frozenset[str] = frozenset(
    {"-c", "-E", "-S", "-target", "--sysroot", "-isysroot", "-nostdinc"}
)


@dataclass(frozen=True)
class IngestionDiagnostic:
    """One detected ingestion problem, with the offending entry and subject."""

    kind: str
    entry_source: str
    subject: str
    detail: str


def _flag_is_recognized(argument: str) -> bool:
    if argument in RECOGNIZED_FLAG_EXACT:
        return True
    return any(argument.startswith(prefix) for prefix in RECOGNIZED_FLAG_PREFIXES)


def collect_ingestion_diagnostics(
    database: CompilationDatabase,
    *,
    project_root: Path | str = ".",
) -> tuple[IngestionDiagnostic, ...]:
    """Report ingestion problems for the database, deterministically ordered.

    Checks every entry: the source must exist under the project root, every
    include path must resolve to an existing directory, and every invocation
    argument must belong to the documented recognized vocabulary.
    """
    root = Path(project_root)
    diagnostics: list[IngestionDiagnostic] = []
    for unit in database.translation_units:
        source = root / unit.source_path
        if not source.is_file():
            diagnostics.append(
                IngestionDiagnostic(
                    kind=KIND_MISSING_SOURCE,
                    entry_source=unit.source_path,
                    subject=unit.source_path,
                    detail=f"source file '{unit.source_path}' does not exist",
                )
            )
        for include in unit.include_paths:
            include_dir = (Path(unit.working_directory) / include).resolve()
            if not include_dir.is_dir():
                diagnostics.append(
                    IngestionDiagnostic(
                        kind=KIND_UNRESOLVABLE_INCLUDE,
                        entry_source=unit.source_path,
                        subject=include,
                        detail=(
                            f"include path '{include}' does not resolve to an "
                            f"existing directory"
                        ),
                    )
                )
        for argument in unit.compiler_invocation.arguments:
            if argument == unit.source_path or _flag_is_recognized(argument):
                continue
            diagnostics.append(
                IngestionDiagnostic(
                    kind=KIND_UNKNOWN_FLAG,
                    entry_source=unit.source_path,
                    subject=argument,
                    detail=(
                        f"compiler flag '{argument}' is outside the "
                        f"documented recognized vocabulary"
                    ),
                )
            )
    return tuple(
        sorted(
            diagnostics,
            key=lambda d: (d.kind, d.entry_source, d.subject),
        )
    )
