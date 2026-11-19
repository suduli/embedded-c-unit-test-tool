"""Diagnostic content control (WP-SEC-04).

Diagnostics point at user code; they never quote it. This module provides the
location-reference formatter, the guard that refuses diagnostics embedding
verbatim source lines, and the exact manifest of what a diagnostic bundle
contains and must never contain.

Satisfies: TOOL-SEC-120.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from ectt.sec.errors import SourceContentInDiagnosticError

__all__ = [
    "MIN_SOURCE_LINE_LENGTH",
    "BUNDLE_ENTRIES",
    "BUNDLE_EXCLUSIONS",
    "DiagnosticBundleManifest",
    "bundle_manifest",
    "location_reference",
    "assert_no_source_content",
]

# Source lines shorter than this are exempt from the verbatim-match guard:
# braces, `return 0;`-style fragments and other short tokens are legitimate in
# tool messages (for example in flag echo) and cannot identify a location.
MIN_SOURCE_LINE_LENGTH: Final[int] = 8

BUNDLE_ENTRIES: Final[tuple[str, ...]] = (
    "ectt version and build identifier",
    "operating configuration: project paths, compiler configuration names, option values",
    "the failing tool command and its exit status",
    "diagnostic messages reduced to text plus path[:line[:column]] location references",
    "log excerpts carried by the same location-reference discipline",
)

BUNDLE_EXCLUSIONS: Final[tuple[str, ...]] = (
    "user source code content (verbatim, transformed, or excerpted)",
    "user project file contents beyond paths",
    "credentials, tokens, or environment secrets",
)


@dataclass(frozen=True)
class DiagnosticBundleManifest:
    """Exactly what a diagnostic bundle contains, and what it never contains."""

    entries: tuple[str, ...]
    exclusions: tuple[str, ...]

    def to_dict(self) -> dict[str, list[str]]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "entries": list(self.entries),
            "exclusions": list(self.exclusions),
        }


def bundle_manifest() -> DiagnosticBundleManifest:
    """The current diagnostic bundle manifest. Deterministic on every call."""
    return DiagnosticBundleManifest(entries=BUNDLE_ENTRIES, exclusions=BUNDLE_EXCLUSIONS)


def location_reference(
    path: str, line: int | None = None, column: int | None = None
) -> str:
    """Format a location reference: ``path[:line[:column]]``, never source text."""
    if line is None:
        return path
    if column is None:
        return f"{path}:{line}"
    return f"{path}:{line}:{column}"


def assert_no_source_content(
    diagnostic_text: str,
    source_lines: Iterable[str],
    *,
    origin: str = "diagnostic",
) -> None:
    """Refuse a diagnostic that embeds a verbatim user source line.

    A source line is embedded when it appears in the diagnostic verbatim —
    either as a whole diagnostic line or as a substring of one — after
    whitespace trimming on both sides. Lines shorter than
    ``MIN_SOURCE_LINE_LENGTH`` are exempt so braces and short fragments cannot
    produce false positives. The raised error names ``origin`` (the
    diagnostic's location identity) and the offending line.
    """
    forbidden = {
        line.strip()
        for line in source_lines
        if len(line.strip()) >= MIN_SOURCE_LINE_LENGTH
    }
    if not forbidden:
        return
    for text_line in diagnostic_text.splitlines():
        candidate = text_line.strip()
        for source_line in forbidden:
            if source_line in candidate:
                raise SourceContentInDiagnosticError(
                    f"{origin} embeds verbatim source content: {source_line!r} "
                    f"must be replaced by a location reference",
                )
