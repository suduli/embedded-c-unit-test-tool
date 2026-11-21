# implements: TOOL-COV-160
"""Coverage separation: UUT versus harness, stubs, framework (WP-COV-08)."""

from __future__ import annotations

import pytest

from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.metrics import statement_coverage
from ectt.cov.separation import COVERAGE_ROLES, separate_coverage

PAYLOAD = {
    "format_version": "2",
    "gcc_version": "14.1.0",
    "data_file": "d.gcda",
    "files": [
        {
            "file": "src/adc.c",  # unit under test
            "functions": [{"name": "convert", "start_line": 1, "end_line": 4, "execution_count": 2}],
            "lines": [
                {"line_number": 1, "count": 2, "unexecuted_block": False},
                {"line_number": 2, "count": 1, "unexecuted_block": False},
            ],
        },
        {
            "file": "gen/test_main.c",  # generated harness
            "lines": [
                {"line_number": 10, "count": 2, "unexecuted_block": False},
                {"line_number": 11, "count": 0, "unexecuted_block": False},
            ],
        },
        {
            "file": "gen/stub_uart.c",  # generated stub
            "lines": [{"line_number": 5, "count": 1, "unexecuted_block": False}],
        },
        {
            "file": "runtime/framework.c",  # tool runtime
            "lines": [{"line_number": 1, "count": 4, "unexecuted_block": False}],
        },
    ],
}

ASSIGNMENTS = {
    "src/adc.c": "uut",
    "gen/test_main.c": "harness",
    "gen/stub_uart.c": "stub",
    "runtime/framework.c": "framework",
}


def test_uut_coverage_is_separate_from_harness() -> None:
    """verifies: TOOL-COV-160 — the UUT figure is never polluted by harness execution."""
    doc = read_gcov_document(PAYLOAD)
    separated = separate_coverage(doc, ASSIGNMENTS)
    by_role = {role.role: role for role in separated.roles}
    assert by_role["uut"].statements == (2, 2) or (
        by_role["uut"].statements.covered == 2 and by_role["uut"].statements.total == 2
    )
    assert by_role["harness"].statements.covered == 1 and by_role["harness"].statements.total == 2
    assert by_role["stub"].statements.covered == 1 and by_role["stub"].statements.total == 1
    assert by_role["framework"].statements.covered == 1 and by_role["framework"].statements.total == 1
    assert by_role["uut"].files == ("src/adc.c",)
    assert by_role["harness"].files == ("gen/test_main.c",)


def test_per_role_metrics_use_only_that_roles_files() -> None:
    doc = read_gcov_document(PAYLOAD)
    separated = separate_coverage(doc, ASSIGNMENTS)
    by_role = {role.role: role for role in separated.roles}
    # cross-check against the metric functions applied to the role's own file set
    uut_files = [f for f in doc.files if f.file == "src/adc.c"]
    assert by_role["uut"].statements == statement_coverage(uut_files)
    assert by_role["uut"].functions.covered == 1 and by_role["uut"].functions.total == 1
    assert by_role["harness"].branches.total is None  # no branches in the harness file


def test_unclassified_file_is_surfaced_not_merged() -> None:
    """verifies: AC-2 — no guessing: an unassigned file is neither merged nor dropped."""
    doc = read_gcov_document(PAYLOAD)
    separated = separate_coverage(doc, {"src/adc.c": "uut"})
    assert separated.unclassified == ("gen/stub_uart.c", "gen/test_main.c", "runtime/framework.c")
    by_role = {role.role: role for role in separated.roles}
    assert by_role["harness"].statements.total == 0  # nothing assigned -> nothing measured


def test_unknown_role_is_refused() -> None:
    doc = read_gcov_document(PAYLOAD)
    with pytest.raises(CoverageError) as exc_info:
        separate_coverage(doc, {"src/adc.c": "production"})
    assert exc_info.value.reason == "unknown_role"


def test_conservation_role_totals_plus_unclassified_equal_document() -> None:
    """verifies: AC-3 — no file counted twice, none lost."""
    doc = read_gcov_document(PAYLOAD)
    separated = separate_coverage(doc, {"src/adc.c": "uut", "gen/test_main.c": "harness"})
    # covered conservation
    unclassified_files = [f for f in doc.files if f.file in separated.unclassified]
    unclassified_covered = statement_coverage(unclassified_files).covered
    assert (
        sum(role.statements.covered for role in separated.roles) + unclassified_covered
        == statement_coverage(doc.files).covered
    )
    # total conservation: roles with files contribute their counts; unclassified carry the rest
    unclassified_files = [f for f in doc.files if f.file in separated.unclassified]
    unclassified = statement_coverage(unclassified_files)
    assert (
        sum(role.statements.total or 0 for role in separated.roles) + (unclassified.total or 0)
        == statement_coverage(doc.files).total
    )


def test_roles_render_in_fixed_order_and_deterministically() -> None:
    """verifies: AC-4 — fixed role order, sorted files, canonical dict."""
    doc = read_gcov_document(PAYLOAD)
    separated = separate_coverage(doc, ASSIGNMENTS)
    assert [role.role for role in separated.roles] == list(COVERAGE_ROLES)
    assert separated.to_dict() == separate_coverage(doc, ASSIGNMENTS).to_dict()
    assert separated.roles[0].to_dict()["files"] == ["src/adc.c"]
