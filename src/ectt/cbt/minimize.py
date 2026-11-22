# implements: TOOL-CBT-080
"""Test suite minimization: redundant tests contribute no unique coverage (WP-CBT-04).

A test case is redundant exactly when its recorded coverage adds nothing to the
coverage of the minimized set — every construct it covers is covered by the kept
tests — so dropping all redundant cases loses no coverage at all (the union of the
kept sets equals the union of all sets).

The selection is a deterministic greedy cover of that union: prefer the test
covering the most not-yet-covered constructs, break ties on the lowest test id, and
everything left over is redundant. Greedy is not proven-minimal (the exact minimum
cover is NP-hard); the requirement asks for identifying redundancy, and the
invariant — union preservation plus loss-free redundancy — is what the tests pin.

Per-test coverage arrives as plain data (``coverage_by_test``); binding the
coverage engine's per-test attribution is composition work, as in WP-CBT-02/03.

Satisfies: TOOL-CBT-080.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass

__all__ = ["Minimization", "minimize_suite"]


@dataclass(frozen=True)
class Minimization:
    """The minimized suite and the cases it makes redundant (TOOL-CBT-080)."""

    kept: tuple[str, ...]
    redundant: tuple[str, ...]


def _checked(coverage_by_test: Mapping[str, Collection[str]]) -> dict[str, frozenset[str]]:
    checked: dict[str, frozenset[str]] = {}
    for test_id, covered in coverage_by_test.items():
        if not isinstance(test_id, str) or not test_id.strip():
            raise ValueError("a suite minimization needs non-empty test ids")
        entries = tuple(covered)
        for construct in entries:
            if not isinstance(construct, str) or not construct.strip():
                raise ValueError(f"test '{test_id}' covers a non-construct entry")
        checked[test_id] = frozenset(entries)
    return checked


def minimize_suite(coverage_by_test: Mapping[str, Collection[str]]) -> Minimization:
    """The deterministic greedy minimization of one suite's coverage data.

    Keeps a set whose union equals the union of all coverage sets and marks
    every other case redundant: each redundant case contributes no construct
    the kept set does not already cover. Deterministic: identical inputs give
    identical kept/redundant tuples, whatever order the mapping was built in.
    """
    coverage = _checked(coverage_by_test)
    full_union: set[str] = set()
    for covered_set in coverage.values():
        full_union.update(covered_set)

    remaining = set(coverage)
    kept: list[str] = []
    covered: set[str] = set()
    while covered != full_union:
        candidates = [
            test_id
            for test_id in remaining
            if coverage[test_id] - covered
        ]
        if not candidates:
            break  # nothing left contributes anything: the rest is redundant
        # Most new coverage first; ties break on the lowest test id.
        best = min(candidates, key=lambda t: (-len(coverage[t] - covered), t))
        kept.append(best)
        covered.update(coverage[best])
        remaining.remove(best)

    return Minimization(kept=tuple(sorted(kept)), redundant=tuple(sorted(remaining)))
