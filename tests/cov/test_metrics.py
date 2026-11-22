# implements: TOOL-COV-010, TOOL-COV-020
"""Statement and branch/decision coverage metrics (WP-COV-01)."""

from __future__ import annotations

from fractions import Fraction

from ectt.cov.gcov import read_gcov_document
from ectt.cov.metrics import branch_coverage, document_metrics, statement_coverage
from tests.cov import GCOV_V1_MINIMAL, GCOV_V2_WITH_BRANCHES_AND_CONDITIONS, gcov_json


def _doc(payload: object) -> object:
    return read_gcov_document(gcov_json(payload))  # type: ignore[arg-type]


def test_statement_coverage_counts_covered_uncovered_partial() -> None:
    """verifies: TOOL-COV-010 — covered/uncovered/partial statements from counts."""
    doc = _doc(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    (file,) = doc.files
    totals = statement_coverage([file])
    assert totals.total == 4
    # lines 6, 8, 10 have count > 0 (10 is partial: unexecuted_block); 12 is uncovered
    assert totals.covered == 3
    assert totals.fraction() == Fraction(3, 4)
    # the partial state travels with the line record, never relabelled
    assert file.lines[2].unexecuted_block is True


def test_statement_coverage_aggregates_across_files() -> None:
    doc = _doc(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    other = _doc(GCOV_V1_MINIMAL)
    totals = statement_coverage([*doc.files, *other.files])
    assert totals.total == 7
    assert totals.covered == 5


def test_statement_coverage_empty_file_is_zero_total() -> None:
    doc = _doc({"format_version": "2", "gcc_version": "14.1.0", "data_file": "d.gcda",
                "files": [{"file": "empty.c", "lines": []}]})
    (file,) = doc.files
    totals = statement_coverage([file])
    assert totals.covered == 0
    assert totals.total == 0
    assert totals.fraction() is None  # no statements: no fabricated ratio


def test_branch_coverage_counts_taken_branches() -> None:
    """verifies: TOOL-COV-020 — a branch is covered iff its count is > 0."""
    doc = _doc(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    (file,) = doc.files
    totals = branch_coverage([file])
    assert totals.total == 2
    assert totals.covered == 2
    assert totals.fraction() == Fraction(1, 1)


def test_branch_coverage_not_applicable_without_branches() -> None:
    """A file with no branch entries has no applicable branch coverage — no
    fabricated 100%."""
    doc = _doc(GCOV_V1_MINIMAL)
    (file,) = doc.files
    totals = branch_coverage([file])
    assert totals.total is None
    assert totals.covered == 0
    assert totals.fraction() is None


def test_branch_coverage_aggregates_across_files() -> None:
    doc = _doc(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    other = _doc(GCOV_V1_MINIMAL)
    totals = branch_coverage([*doc.files, *other.files])
    assert totals.total == 2
    assert totals.covered == 2


def test_document_metrics_reports_both() -> None:
    doc = _doc(GCOV_V2_WITH_BRANCHES_AND_CONDITIONS)
    metrics = document_metrics(doc)
    assert metrics["statements"].total == 4
    assert metrics["branches"].total == 2
