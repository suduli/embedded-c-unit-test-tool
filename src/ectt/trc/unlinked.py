# implements: TOOL-TRC-040
"""Unlinked requirement and unlinked test reporting (WP-TRC-02).

TOOL-TRC-040: report requirements with no linked test case, and test cases
with no linked requirement. Both universes must be supplied explicitly — a
defaulted universe would silently hide gaps (an empty universe would report
nothing, which is exactly the misleading output NFR-090 forbids).

Consistency: ``find_unlinked(...).unlinked_requirements`` is exactly the set
of requirement ids for which ``build_matrix`` emits rows without links.

Satisfies: TOOL-TRC-040.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from ectt.trc.associations import AssociationSet

__all__ = [
    "UnlinkedReport",
    "find_unlinked",
]


@dataclass(frozen=True)
class UnlinkedReport:
    """The two gap lists TOOL-TRC-040 asks for, deterministically sorted."""

    unlinked_requirements: tuple[str, ...] = ()
    unlinked_tests: tuple[str, ...] = ()
    requirement_universe: tuple[str, ...] = field(default_factory=tuple)
    test_universe: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form."""
        return {
            "requirement_universe_size": len(self.requirement_universe),
            "test_universe_size": len(self.test_universe),
            "unlinked_requirements": list(self.unlinked_requirements),
            "unlinked_tests": list(self.unlinked_tests),
        }


def find_unlinked(
    associations: AssociationSet,
    *,
    requirement_universe: Iterable[str],
    test_universe: Iterable[str],
) -> UnlinkedReport:
    """Report requirements with no linked test and tests with no linked requirement.

    A requirement is unlinked when it appears in the requirement universe but
    in no association pair; a test likewise. The universes are required: the
    caller declares what "everything" means (the requirement register and the
    test-case inventory).
    """
    requirements = sorted(set(requirement_universe))
    tests = sorted(set(test_universe))
    linked_requirements = set(associations.requirements())
    linked_tests = {pair.test_id for pair in associations.pairs}

    return UnlinkedReport(
        unlinked_requirements=tuple(req for req in requirements if req not in linked_requirements),
        unlinked_tests=tuple(test for test in tests if test not in linked_tests),
        requirement_universe=tuple(requirements),
        test_universe=tuple(tests),
    )
