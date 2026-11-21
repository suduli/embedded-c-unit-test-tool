# implements: TOOL-TRC-080
"""Requirement-to-source-element links (WP-TRC-05, DSN-TRC-060).

TOOL-TRC-080: link requirements to source code elements in addition to test
cases. A link names a *function* in a unit, or a *line range* in a unit.
Line numbers move when code is edited, so a range link is resolved through the
analysis model (S1) and persisted as the **function that contains it**
(:meth:`SourceLinkResolution.anchored`); a function link keeps resolving after
the function moves.

Honest limits, never papered over:

* Since the analysis-model schema 1.5 bump, a function carries its full extent
  (start and end line). A range fully inside one function's extent resolves
  *exactly* (``approximate=False``); a range reaching beyond that function's end
  is refused (``range_spans_functions``), and a range in a gap between two
  extents is refused (``range_outside_any_function``) — no guessing.
* Models recorded before schema 1.5 carry no extent: a range is then attributed
  to the last function that starts at or before its first line and is refused
  (``range_spans_functions``) when it reaches the next function's start. Such a
  link is flagged ``approximate``: file-scope code between two functions cannot
  be told apart from the earlier function's body. Approximate behaviour is kept
  only for models without extent.
* A link that does not resolve is reported with a reason and kept out of the
  anchored set; nothing is guessed (a renamed function is ``function_not_found``).

Satisfies: TOOL-TRC-080.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ectt.ana.model import AnalysisModel, AnalysisUnit, FunctionModel
from ectt.core.determinism import canonical_json
from ectt.trc.errors import TrcError

__all__ = [
    "SOURCE_LINKS_VERSION",
    "ResolvedSourceLink",
    "SourceLink",
    "SourceLinkResolution",
    "dump_source_links",
    "load_source_links",
    "resolve_source_links",
]

SOURCE_LINKS_VERSION = "1"


@dataclass(frozen=True)
class SourceLink:
    """One requirement-to-source-element link: a function, or a line range."""

    requirement_id: str
    unit: str
    function: str | None = None
    start_line: int | None = None
    end_line: int | None = None

    def __post_init__(self) -> None:
        for name, value, expected in (
            ("requirement_id", self.requirement_id, str),
            ("unit", self.unit, str),
            ("function", self.function, str),
            ("start_line", self.start_line, int),
            ("end_line", self.end_line, int),
        ):
            if value is not None and not isinstance(value, expected):
                raise TrcError(f"source link field '{name}' must be a {expected.__name__}", reason="invalid_link")
        if not self.requirement_id or any(c.isspace() for c in self.requirement_id):
            raise TrcError("requirement id must be a non-empty string without whitespace", reason="invalid_id")
        if not self.unit or not self.unit.strip():
            raise TrcError("source link needs a unit path", reason="invalid_link")
        has_function = self.function is not None
        has_range = self.start_line is not None or self.end_line is not None
        if has_function == has_range:
            raise TrcError(
                f"link of '{self.requirement_id}' to '{self.unit}' must name either a function or a line range",
                reason="invalid_link",
            )
        if has_function and not (self.function or "").strip():
            raise TrcError("function name must not be empty", reason="invalid_link")
        if has_range:
            start, end = self.start_line, self.end_line
            if start is None or end is None or isinstance(start, bool) or isinstance(end, bool) or start < 1 or end < start:
                raise TrcError(
                    f"line range {start}-{end} of '{self.unit}' must be 1 <= start <= end",
                    reason="invalid_range",
                )

    def _key(self) -> tuple[str, str, str, int, int]:
        return (self.requirement_id, self.unit, self.function or "", self.start_line or 0, self.end_line or 0)

    def __lt__(self, other: SourceLink) -> bool:
        """Deterministic order; ``None`` fields cannot be compared by the dataclass itself."""
        return self._key() < other._key()

    def to_dict(self) -> dict[str, Any]:
        doc: dict[str, Any] = {"requirement_id": self.requirement_id, "unit": self.unit}
        if self.function is not None:
            doc["function"] = self.function
        else:
            doc["end_line"] = self.end_line
            doc["start_line"] = self.start_line
        return doc


@dataclass(frozen=True)
class ResolvedSourceLink:
    """A link plus what the analysis model made of it."""

    link: SourceLink
    status: str  # "resolved" | "unresolved"
    function: str | None = None
    reason: str | None = None
    approximate: bool = False


@dataclass(frozen=True)
class SourceLinkResolution:
    """Result of resolving links against one analysis model."""

    links: tuple[ResolvedSourceLink, ...]

    @property
    def resolved(self) -> tuple[ResolvedSourceLink, ...]:
        return tuple(r for r in self.links if r.status == "resolved")

    @property
    def unresolved(self) -> tuple[ResolvedSourceLink, ...]:
        return tuple(r for r in self.links if r.status == "unresolved")

    def anchored(self) -> tuple[SourceLink, ...]:
        """The persistable form: every resolved link expressed as a function link."""
        anchored = {
            SourceLink(r.link.requirement_id, r.link.unit, function=r.function)
            for r in self.links
            if r.status == "resolved" and r.function is not None
        }
        return tuple(sorted(anchored))

    def forward(self) -> dict[str, tuple[tuple[str, str], ...]]:
        """Requirement -> ``(unit, function)`` elements it is linked to."""
        result: dict[str, set[tuple[str, str]]] = {}
        for link in self.anchored():
            result.setdefault(link.requirement_id, set()).add((link.unit, link.function or ""))
        return {req: tuple(sorted(items)) for req, items in sorted(result.items())}

    def reverse(self) -> dict[tuple[str, str], tuple[str, ...]]:
        """``(unit, function)`` -> requirements linked to it."""
        result: dict[tuple[str, str], set[str]] = {}
        for link in self.anchored():
            result.setdefault((link.unit, link.function or ""), set()).add(link.requirement_id)
        return {key: tuple(sorted(items)) for key, items in sorted(result.items())}


def _normalise(path: str) -> str:
    posix = path.replace("\\", "/")
    while posix.startswith("./"):
        posix = posix[2:]
    return posix


def _unit_functions(unit: AnalysisUnit) -> list[FunctionModel]:
    own = _normalise(unit.path)
    return sorted(
        (f for f in unit.functions if _normalise(f.location.file) == own),
        key=lambda f: (f.location.line, f.name),
    )


def _resolve_one(link: SourceLink, units: dict[str, AnalysisUnit]) -> ResolvedSourceLink:
    unit = units.get(_normalise(link.unit))
    if unit is None:
        return ResolvedSourceLink(link, "unresolved", reason="unit_not_found")
    if unit.status != "parsed":
        return ResolvedSourceLink(link, "unresolved", reason="unit_not_parsed")
    functions = _unit_functions(unit)

    if link.function is not None:
        matches = [f for f in functions if f.name == link.function]
        if not matches:
            return ResolvedSourceLink(link, "unresolved", reason="function_not_found")
        if len(matches) > 1:
            return ResolvedSourceLink(link, "unresolved", reason="ambiguous_function")
        return ResolvedSourceLink(link, "resolved", function=link.function)

    start, end = link.start_line or 0, link.end_line or 0
    # Exact resolution via the schema-1.5 function extent: a range fully inside
    # one extent is exact; reaching beyond it or landing between extents is
    # refused with a named reason — no guessing.
    extent_functions = [f for f in functions if f.start_line is not None and f.end_line is not None]
    for candidate in extent_functions:
        assert candidate.start_line is not None and candidate.end_line is not None
        if candidate.start_line <= start <= candidate.end_line:
            if end <= candidate.end_line:
                return ResolvedSourceLink(link, "resolved", function=candidate.name, approximate=False)
            return ResolvedSourceLink(link, "unresolved", reason="range_spans_functions")
    if len(extent_functions) == len(functions):
        return ResolvedSourceLink(link, "unresolved", reason="range_outside_any_function")

    # Fallback for models recorded before schema 1.5 (no extent): the last
    # function starting at or before the range's first line, refused when the
    # range reaches the next function's start. Approximate by nature.
    legacy = [f for f in functions if f.start_line is None and f.end_line is None]
    containing = [f for f in legacy if f.location.line <= start]
    if not containing:
        return ResolvedSourceLink(link, "unresolved", reason="range_outside_any_function")
    candidate = containing[-1]
    later = [f for f in legacy if f.location.line > candidate.location.line]
    if later and end >= later[0].location.line:
        return ResolvedSourceLink(link, "unresolved", reason="range_spans_functions")
    return ResolvedSourceLink(link, "resolved", function=candidate.name, approximate=True)


def resolve_source_links(links: Iterable[SourceLink], model: AnalysisModel) -> SourceLinkResolution:
    """Resolve ``links`` through ``model``; every link gets exactly one outcome."""
    units = {_normalise(u.path): u for u in model.units}
    unique = sorted(set(links))
    return SourceLinkResolution(tuple(_resolve_one(link, units) for link in unique))


def dump_source_links(links: Iterable[SourceLink]) -> str:
    """Deterministic JSON for persisting links (store the anchored form)."""
    return canonical_json(
        {"links": [link.to_dict() for link in sorted(set(links))], "links_version": SOURCE_LINKS_VERSION}
    )


def load_source_links(text: str) -> tuple[SourceLink, ...]:
    """Strictly load persisted links; refuses unknown versions and malformed entries."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TrcError(f"source links are not valid JSON: {exc}", reason="invalid_links_document") from exc
    if not isinstance(doc, dict) or doc.get("links_version") != SOURCE_LINKS_VERSION:
        raise TrcError(
            f"unsupported source links document (expected links_version {SOURCE_LINKS_VERSION!r})",
            reason="unsupported_links_version",
        )
    raw = doc.get("links")
    if not isinstance(raw, list):
        raise TrcError("'links' must be an array", reason="invalid_links_document")
    links: list[SourceLink] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise TrcError("every link must be an object", reason="invalid_links_document")
        unknown = set(entry) - {"requirement_id", "unit", "function", "start_line", "end_line"}
        if unknown:
            raise TrcError(f"link has unknown field(s): {', '.join(sorted(unknown))}", reason="invalid_links_document")
        try:
            links.append(
                SourceLink(
                    entry["requirement_id"],
                    entry["unit"],
                    function=entry.get("function"),
                    start_line=entry.get("start_line"),
                    end_line=entry.get("end_line"),
                )
            )
        except (KeyError, TypeError) as exc:
            raise TrcError(f"malformed link entry: {exc!r}", reason="invalid_links_document") from exc
    return tuple(sorted(set(links)))
