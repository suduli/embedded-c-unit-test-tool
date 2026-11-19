# implements: TOOL-TRC-010, TOOL-TRC-110
"""Requirement-to-test association rows (WP-TRC-01).

An association is one (requirement, test) intent. Rows arrive from many
places — data-driven case files, user edits, imports — and duplicates are
normal in the raw data. TOOL-TRC-110 requires requirement-level figures to
be computed over *unique* (requirement, test) pairs, so this set deduplicates
by construction: adding the same pair twice is idempotent, and
``pair_count`` is the only numerator the matrix may use — never a raw row
count over a deduplicated denominator.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ectt.trc.errors import TrcError

__all__ = [
    "Association",
    "AssociationSet",
]


@dataclass(frozen=True, order=True)
class Association:
    """One unique (requirement, test) association pair."""

    requirement_id: str
    test_id: str


def _id(value: object, what: str) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise TrcError(f"{what} must be a non-empty string without whitespace, got {value!r}", reason="invalid_id")
    return value


class AssociationSet:
    """Deduplicated set of (requirement, test) associations."""

    def __init__(self) -> None:
        self._pairs: dict[tuple[str, str], Association] = {}

    @classmethod
    def from_rows(cls, rows: Iterable[tuple[str, str] | Association]) -> AssociationSet:
        """Build from raw association rows; duplicates collapse to one pair."""
        associations = cls()
        for row in rows:
            if isinstance(row, Association):
                associations.add(row.requirement_id, row.test_id)
            else:
                requirement_id, test_id = row
                associations.add(requirement_id, test_id)
        return associations

    def add(self, requirement_id: str, test_id: str) -> None:
        """Add one association; adding an existing pair is idempotent."""
        association = Association(_id(requirement_id, "requirement id"), _id(test_id, "test id"))
        self._pairs.setdefault((association.requirement_id, association.test_id), association)

    @property
    def pairs(self) -> tuple[Association, ...]:
        """All unique pairs, ordered deterministically."""
        return tuple(self._pairs[key] for key in sorted(self._pairs))

    @property
    def pair_count(self) -> int:
        """Number of unique (requirement, test) pairs — the only numerator."""
        return len(self._pairs)

    def requirements(self) -> tuple[str, ...]:
        """Distinct requirement ids, ordered deterministically."""
        return tuple(sorted({pair.requirement_id for pair in self._pairs.values()}))

    def tests_for(self, requirement_id: str) -> tuple[str, ...]:
        """Distinct tests linked to one requirement, ordered deterministically."""
        return tuple(sorted({pair.test_id for pair in self._pairs.values() if pair.requirement_id == requirement_id}))

    def requirements_for(self, test_id: str) -> tuple[str, ...]:
        """Distinct requirements linked to one test (the reverse view)."""
        return tuple(sorted({pair.requirement_id for pair in self._pairs.values() if pair.test_id == test_id}))
