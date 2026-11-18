"""Multi-toolchain ingestion (WP-ING-06).

A project building with more than one toolchain ingests as one
multi-toolchain record: a separate per-toolchain database whose entries keep
that toolchain's flags verbatim, with per-toolchain build tags (TOOL-ING-220
identity semantics: the same source under two toolchains stays distinct).

Satisfies: TOOL-ING-110.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ectt.ing.errors import IngestionError
from ectt.ing.model import CompilationDatabase, TranslationUnit

__all__ = [
    "MultiToolchainIngestion",
    "ToolchainEntry",
    "UnknownToolchainError",
    "ingest_multi_toolchain",
]


class UnknownToolchainError(IngestionError):
    """Raised when a toolchain name is not part of the ingestion."""

    def __init__(
        self, message: str, *, reason: str = "unknown_toolchain", path: str | None = None
    ) -> None:
        super().__init__(message, reason=reason, path=path)


@dataclass(frozen=True)
class ToolchainEntry:
    """One ingested translation unit under one toolchain."""

    toolchain: str
    unit: TranslationUnit

    def __post_init__(self) -> None:
        if not isinstance(self.toolchain, str) or not self.toolchain.strip():
            raise UnknownToolchainError("toolchain name must be a non-empty string")


@dataclass(frozen=True)
class MultiToolchainIngestion:
    """One ingestion spanning several toolchains, flags retained verbatim."""

    toolchains: tuple[str, ...]
    databases: dict[str, CompilationDatabase]

    def database_for(self, toolchain: str) -> CompilationDatabase:
        """The database of one toolchain; unknown names are named errors."""
        try:
            return self.databases[toolchain]
        except KeyError:
            raise UnknownToolchainError(
                f"toolchain '{toolchain}' is not part of this ingestion"
            ) from None

    def flags_for(self, toolchain: str, source_path: str) -> tuple[str, ...]:
        """The retained per-toolchain flags of one source under one toolchain."""
        database = self.database_for(toolchain)
        for unit in database.translation_units:
            if unit.source_path == source_path:
                return unit.compiler_invocation.arguments
        raise UnknownToolchainError(
            f"source '{source_path}' was not ingested under toolchain '{toolchain}'",
            path=source_path,
        )

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "toolchains": sorted(self.toolchains),
            "databases": {
                toolchain: self.databases[toolchain].to_dict()
                for toolchain in sorted(self.databases)
            },
        }


def ingest_multi_toolchain(
    entries: tuple[ToolchainEntry, ...],
    *,
    build_tags: dict[str, str] | None = None,
) -> MultiToolchainIngestion:
    """Ingest entries grouped per toolchain; each toolchain keeps its flags.

    The same source under two toolchains is retained as two distinct
    configurations. Each toolchain's database carries a build tag: the
    explicit caller tag when supplied, otherwise the toolchain name.
    """
    grouped: dict[str, list[TranslationUnit]] = {}
    order: list[str] = []
    for entry in entries:
        if entry.toolchain not in grouped:
            grouped[entry.toolchain] = []
            order.append(entry.toolchain)
        grouped[entry.toolchain].append(entry.unit)
    tags = build_tags or {}
    databases: dict[str, CompilationDatabase] = {}
    for toolchain in sorted(grouped):
        databases[toolchain] = CompilationDatabase(
            translation_units=tuple(
                sorted(grouped[toolchain], key=lambda unit: unit.source_path)
            ),
            build_tag=tags.get(toolchain, toolchain),
        )
    return MultiToolchainIngestion(toolchains=tuple(sorted(databases)), databases=databases)
