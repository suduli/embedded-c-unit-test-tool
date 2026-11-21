# implements: TOOL-COV-010, TOOL-COV-020
"""Statement and branch/decision coverage metrics over the gcov model.

Satisfies: TOOL-COV-010, TOOL-COV-020.

Statement semantics (TOOL-COV-010): every ``GcovLine`` entry is a statement
line; a line with ``count > 0`` is covered, ``count == 0`` uncovered, and a
line with ``count > 0`` and ``unexecuted_block`` true is partial (not all
statements on the line ran). The total is the number of line entries.

Branch semantics (TOOL-COV-020): every ``GcovBranch`` entry is a decision
branch; a branch is covered iff ``count > 0``. A file (or document) with no
branch entries has no applicable branch coverage — the metric reports an
empty total rather than a fabricated 100%.

All ratios are exact fractions; nothing in this module consults a wall clock
or the network.
"""

from __future__ import annotations

from collections.abc import Iterable

from ectt.cov.model import GcovDocument, GcovFile, MetricTotals

__all__ = [
    "statement_coverage",
    "branch_coverage",
]


def statement_coverage(files: Iterable[GcovFile]) -> MetricTotals:
    """Covered/total statement lines across the given files (TOOL-COV-010).

    Covered counts lines with ``count > 0``; partial lines (``count > 0`` with
    ``unexecuted_block``) are counted as covered statements whose partial state
    travels with the line record — the metric never relabels them fully covered.
    """
    covered = 0
    total = 0
    for file in files:
        for line in file.lines:
            total += 1
            if line.count > 0:
                covered += 1
    return MetricTotals(covered=covered, total=total)


def branch_coverage(files: Iterable[GcovFile]) -> MetricTotals:
    """Covered/total decision branches across the given files (TOOL-COV-020).

    A branch is covered iff ``count > 0``. When no file carries any branch
    entry the total is ``None`` — branch coverage is not applicable, and no
    100% figure is fabricated.
    """
    covered = 0
    total = 0
    for file in files:
        for line in file.lines:
            for branch in line.branches:
                total += 1
                if branch.count > 0:
                    covered += 1
    if total == 0:
        return MetricTotals(covered=0, total=None)
    return MetricTotals(covered=covered, total=total)


def document_metrics(document: GcovDocument) -> dict[str, MetricTotals]:
    """Statement and branch totals across all files of a document."""
    return {
        "statements": statement_coverage(document.files),
        "branches": branch_coverage(document.files),
    }
