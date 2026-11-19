"""Standards objective mapping (WP-QUA-06).

TOOL-QUA-080: the tool shall document the mapping between its capabilities
and the verification objectives of ISO 26262, IEC 61508, IEC 62304,
EN 50128, and DO-178C.

The mapping structure is fail-closed: every row must cite both the standard
clause and the repository evidence for the capability, and no row may claim
satisfaction or compliance — only that a capability *addresses* a clause,
with the evidence named. The default mapping is empty and says so:
populating it is the classification-dependent work (WP-QUA-01/02), which an
unattended run must not invent.

Satisfies: TOOL-QUA-080.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = [
    "STANDARDS",
    "ObjectiveMapping",
    "ObjectiveMappingError",
    "default_mapping",
    "render",
]

#: The standards TOOL-QUA-080 names, in render order.
STANDARDS: tuple[str, ...] = (
    "ISO 26262",
    "IEC 61508",
    "IEC 62304",
    "EN 50128",
    "DO-178C",
)

#: Tokens that would constitute a satisfaction/compliance claim; rows
#: containing them are refused (only addressing language is permitted).
_CLAIM_TOKENS = ("satisfies", "compliant", "certified", "fulfils", "fulfills")


class ObjectiveMappingError(Exception):
    """Raised for unsourced rows or satisfaction claims in the mapping."""


@dataclass(frozen=True)
class ObjectiveMapping:
    """One capability-to-objective row, doubly sourced."""

    standard: str
    clause: str
    capability_claim: str
    evidence: str


@dataclass(frozen=True)
class StandardsMapping:
    """Rows grouped per standard; empty until the classification exists."""

    rows: tuple[ObjectiveMapping, ...] = ()
    revision: str = field(default="2026-11-18")


def default_mapping() -> StandardsMapping:
    """The mapping as recorded by this run: deliberately empty, stated so.

    Populating rows requires the tool-classification decision and the
    qualification context (WP-QUA-01/02, ADR-sensitive); no row is invented
    here.
    """
    return StandardsMapping()


def _validate(mapping: StandardsMapping) -> None:
    for row in mapping.rows:
        if row.standard not in STANDARDS:
            raise ObjectiveMappingError(f"unknown standard: {row.standard!r}")
        if not row.clause:
            raise ObjectiveMappingError(
                f"row without a standard clause: {row.capability_claim!r}"
            )
        if not row.evidence:
            raise ObjectiveMappingError(
                f"row without capability evidence: {row.capability_claim!r}"
            )
        lowered = row.capability_claim.lower()
        for token in _CLAIM_TOKENS:
            if token in lowered:
                raise ObjectiveMappingError(
                    f"row claims satisfaction ('{token}'); only addressing "
                    f"language is permitted (TOOL-QUA-080 fail-closed)"
                )


def render(mapping: StandardsMapping) -> str:
    """Render the deterministic mapping; refuses unsourced or claiming rows."""
    _validate(mapping)
    lines: list[str] = [
        "Standards objective mapping",
        "===========================",
        "",
        (
            "No objective mappings are recorded yet: rows are populated only "
            "after the tool-classification decision (WP-QUA-01) and in the "
            "owner's qualification context. Nothing below claims compliance."
        ),
        "",
    ]
    for standard in STANDARDS:
        lines.append(f"{standard}:")
        standard_rows = [row for row in mapping.rows if row.standard == standard]
        if not standard_rows:
            lines.append("  (no mappings recorded)")
        else:
            lines.extend(
                f"  - clause {row.clause}: {row.capability_claim} "
                f"[evidence: {row.evidence}]"
                for row in standard_rows
            )
        lines.append("")
    lines.append(f"Mapping revision: {mapping.revision} (single source: ectt.qua)")
    return "\n".join(lines) + "\n"
