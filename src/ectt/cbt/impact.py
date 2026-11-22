# implements: TOOL-CBT-020
"""Change impact analysis: which recorded tests did a source change touch (WP-CBT-02).

A source change names the constructs it touched (file paths or construct ids, at the
granularity the caller's coverage data uses). A test case is **affected exactly when**
the constructs its recorded per-test coverage covers intersect the changed set:
unaffected cases are never listed, a construct no test covers affects nothing (that
is a reporting concern, not an impact one), and the answer is a sorted, deterministic
function of its inputs.

The per-test coverage comes in as plain data (`coverage_by_test`): binding it to the
coverage engine's per-test attribution is composition work (see the WP-CBT-02
analysis note), so the CBT layer stays layer-clean.

Satisfies: TOOL-CBT-020.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field

__all__ = ["ImpactResult", "SourceChange", "affected_cases"]


@dataclass(frozen=True)
class SourceChange:
    """The source constructs a change touched (file paths or construct ids)."""

    constructs: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        for construct in self.constructs:
            if not isinstance(construct, str) or not construct.strip():
                raise ValueError("a source change names non-empty construct ids only")

    def __bool__(self) -> bool:
        return bool(self.constructs)


@dataclass(frozen=True)
class ImpactResult:
    """The impact verdict for one change over one set of per-test coverages."""

    affected: tuple[str, ...]
    unaffected: tuple[str, ...]
    #: The change constructs no supplied test covered (surfaced, never silently dropped).
    uncovered_by_tests: tuple[str, ...] = field(default_factory=tuple)


def affected_cases(
    change: SourceChange,
    coverage_by_test: Mapping[str, Collection[str]],
) -> ImpactResult:
    """The cases whose covered code the change touched, sorted, deterministic.

    A case is affected exactly when its covered set intersects the changed
    constructs. A construct no test covers is reported in
    ``uncovered_by_tests`` — visible, but it affects nothing (TOOL-CBT-020
    asks for the affected tests, not a coverage audit).
    """
    changed = frozenset(c.strip() for c in change.constructs if c.strip())
    affected: list[str] = []
    unaffected: list[str] = []
    covered_anywhere: set[str] = set()
    for test_id in sorted(coverage_by_test):
        covered = frozenset(coverage_by_test[test_id])
        covered_anywhere.update(covered)
        if changed & covered:
            affected.append(test_id)
        else:
            unaffected.append(test_id)
    return ImpactResult(
        affected=tuple(affected),
        unaffected=tuple(unaffected),
        uncovered_by_tests=tuple(sorted(changed - covered_anywhere)),
    )
