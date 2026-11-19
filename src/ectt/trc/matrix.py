# implements: TOOL-TRC-020, TOOL-TRC-030, TOOL-TRC-110
"""Bidirectional traceability matrix with requirement verdicts (WP-TRC-01).

TOOL-TRC-110, implemented exactly as written:

- figures are computed over **unique** (requirement, test) pairs; duplicate
  association rows collapse before any counting happens, so a requirement
  linked twice to the same test aggregates to one counted pair and one
  verdict — never a 2/1 numerator-over-denominator;
- a requirement's verdict is the worst outcome among its linked *executed*
  tests (``fail`` > ``error`` > ``timeout`` > ``pass``);
- unreviewed-origin tests (generated and not yet reviewed, TOOL-ATG-080)
  count as unverified: they keep their recorded status in the row but do
  not execute into the verdict;
- every requirement-level percentage labels its denominator;
- a requirement linked to no executed test is reported ``unverified``,
  never inferred from coverage (coverage is not an input to this module).

Statuses come from the persisted report model's test statuses (WP-REP-01);
a linked test with no recorded status is ``not_run``.

Satisfies: TOOL-TRC-010, TOOL-TRC-020, TOOL-TRC-030, TOOL-TRC-110.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from ectt.tcm.datacases import DataDrivenTestCase
from ectt.trc.associations import AssociationSet
from ectt.trc.errors import TrcError

__all__ = [
    "TEST_SEVERITY",
    "RequirementRow",
    "TestLink",
    "TraceabilityMatrix",
    "associations_from_datacases",
    "build_matrix",
]

#: Worst-outcome order over the report status vocabulary (TRC-110).
TEST_SEVERITY: dict[str, int] = {"pass": 0, "not_run": 1, "timeout": 2, "error": 3, "fail": 4}

_EXECUTED = ("pass", "fail", "error", "timeout")


@dataclass(frozen=True)
class TestLink:
    """One linked test's recorded status (TOOL-TRC-030)."""

    test_id: str
    status: str
    unreviewed: bool = False  # generated and not yet reviewed (TOOL-ATG-080)


@dataclass(frozen=True)
class RequirementRow:
    """One requirement's links and its aggregate verdict."""

    requirement_id: str
    links: tuple[TestLink, ...]
    verdict: str  # "pass" | "failed" | "unverified"


@dataclass(frozen=True)
class TraceabilityMatrix:
    """The bidirectional matrix: requirements to tests and back."""

    rows: tuple[RequirementRow, ...]
    pair_count: int  # unique (requirement, test) pairs — the only numerator

    def forward(self) -> dict[str, tuple[str, ...]]:
        """Requirement -> linked test ids (TOOL-TRC-020, forward direction)."""
        return {row.requirement_id: tuple(link.test_id for link in row.links) for row in self.rows}

    def reverse(self) -> dict[str, tuple[str, ...]]:
        """Test -> linked requirement ids (TOOL-TRC-020, reverse direction)."""
        reverse: dict[str, list[str]] = {}
        for row in self.rows:
            for link in row.links:
                reverse.setdefault(link.test_id, []).append(row.requirement_id)
        return {test_id: tuple(reqs) for test_id, reqs in sorted(reverse.items())}

    def verdict_figures(self) -> dict[str, Any]:
        """Requirement-level figures with labelled denominators (TOOL-TRC-110)."""
        verdicts: dict[str, int] = {"failed": 0, "pass": 0, "unverified": 0}
        for row in self.rows:
            verdicts[row.verdict] += 1
        total = len(self.rows)
        percentages: dict[str, dict[str, Any]] = {}
        for verdict in ("pass", "failed", "unverified"):
            percentages[verdict] = {
                "value": round(100.0 * verdicts[verdict] / total, 1) if total else 0.0,
                "denominator": f"{total} requirement rows",
            }
        return {
            "pair_count": self.pair_count,
            "pair_denominator": f"{self.pair_count} unique (requirement, test) pairs",
            "requirement_rows": total,
            "requirement_denominator": f"{total} requirement rows",
            "verdicts": verdicts,
            "percentages": percentages,
        }

    def to_dict(self) -> dict[str, Any]:
        """Return the canonical dictionary form (both directions, TRC-020)."""
        return {
            "forward": {req: list(tests) for req, tests in self.forward().items()},
            "pair_count": self.pair_count,
            "reverse": {test: list(reqs) for test, reqs in self.reverse().items()},
            "rows": [
                {
                    "links": [
                        {"status": link.status, "test_id": link.test_id, "unreviewed": link.unreviewed}
                        for link in row.links
                    ],
                    "requirement_id": row.requirement_id,
                    "verdict": row.verdict,
                }
                for row in self.rows
            ],
            "verdict_figures": self.verdict_figures(),
        }


def associations_from_datacases(cases: Iterable[DataDrivenTestCase]) -> AssociationSet:
    """Collect the requirement associations recorded on data-driven cases."""
    associations = AssociationSet()
    for case in cases:
        for requirement_id in case.requirements:
            associations.add(requirement_id, case.case_id)
    return associations


def build_matrix(
    associations: AssociationSet,
    statuses: Mapping[str, str],
    *,
    requirement_universe: Iterable[str] | None = None,
    unreviewed_tests: Iterable[str] = (),
) -> TraceabilityMatrix:
    """Build the bidirectional matrix (TOOL-TRC-020) with verdicts (TRC-110).

    ``statuses`` maps test ids to report statuses (WP-REP-01 vocabulary); a
    linked test with no recorded status is ``not_run``. ``requirement_universe``
    extends the rows beyond the associated requirements — a universe member
    with no associations is reported ``unverified``. ``unreviewed_tests``
    lists generated-and-unreviewed test ids (TOOL-ATG-080): they keep their
    status in the row but do not execute into the verdict.
    """
    for test_id, status in statuses.items():
        if status not in TEST_SEVERITY:
            raise TrcError(
                f"test '{test_id}' has unknown status '{status}' (vocabulary: {', '.join(TEST_SEVERITY)})",
                reason="invalid_status",
            )
    unreviewed = set(unreviewed_tests)

    universe = set(requirement_universe) if requirement_universe is not None else set(associations.requirements())
    rows: list[RequirementRow] = []
    for requirement_id in sorted(universe):
        links: list[TestLink] = []
        for test_id in associations.tests_for(requirement_id):
            status = statuses.get(test_id, "not_run")
            links.append(TestLink(test_id=test_id, status=status, unreviewed=test_id in unreviewed))
        rows.append(
            RequirementRow(
                requirement_id=requirement_id,
                links=tuple(links),
                verdict=_requirement_verdict(tuple(links)),
            )
        )

    return TraceabilityMatrix(rows=tuple(rows), pair_count=associations.pair_count)


def _requirement_verdict(links: tuple[TestLink, ...]) -> str:
    """Worst outcome among linked *executed, reviewed* tests (TOOL-TRC-110)."""
    executed = [link for link in links if link.status in _EXECUTED and not link.unreviewed]
    if not executed:
        return "unverified"  # nothing executed: never inferred from coverage
    worst = max(executed, key=lambda link: TEST_SEVERITY[link.status])
    return "failed" if worst.status in ("fail", "error", "timeout") else "pass"
