# implements: TOOL-TRC-010, TOOL-TRC-020, TOOL-TRC-030, TOOL-TRC-110
"""Association deduplication and the bidirectional matrix (WP-TRC-01).

Acceptance criterion (PLAN-001 §5.4): a requirement linked by two association
rows to the same test aggregates to one counted pair and one worst-outcome
verdict — never a 2/1 numerator-over-denominator — and a requirement linked
to no executed test is reported unverified.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultSet,
    SourceLocation,
    finalize_result,
)
from ectt.rep.model import ReportModel, build_report_model
from ectt.tcm.datacases import DataDrivenTestCase
from ectt.tcm.datacases import TestCaseExpected as CaseExpected
from ectt.tcm.datacases import TestCaseInputs as CaseInputs
from ectt.trc.associations import AssociationSet
from ectt.trc.errors import TrcError
from ectt.trc.matrix import associations_from_datacases, build_matrix

STATUSES = {
    "t.pass": "pass",
    "t.fail": "fail",
    "t.error": "error",
    "t.timeout": "timeout",
    "t.notrun": "not_run",
}

_FAILURE = AssertionFailure(
    assertion="assert_equal",
    expected="0",
    actual="1",
    location=SourceLocation(file="t.c", line=1),
)


def _case(case_id: str, requirements: tuple[str, ...]) -> DataDrivenTestCase:
    return DataDrivenTestCase(
        case_id=case_id,
        unit="src/adc.c",
        function="adc_read",
        inputs=CaseInputs(),
        expected=CaseExpected(),
        stubs=(),
        requirements=requirements,
    )


def _rows(*pairs: tuple[str, str]) -> AssociationSet:
    return AssociationSet.from_rows(pairs)


# --- TOOL-TRC-010 / TOOL-TRC-110: association deduplication ----------------------------


def test_duplicate_rows_collapse_to_one_pair() -> None:
    """verifies: the PLAN-001 §5.4 criterion for WP-TRC-01."""
    associations = _rows(("R1", "t1"), ("R1", "t1"), ("R1", "t1"))

    assert associations.pair_count == 1
    assert associations.tests_for("R1") == ("t1",)

    matrix = build_matrix(associations, {"t1": "pass"})
    figures = matrix.verdict_figures()

    assert figures["pair_count"] == 1  # one counted pair, never 2/1
    assert len(matrix.rows) == 1
    assert matrix.rows[0].verdict == "pass"
    assert len(matrix.rows[0].links) == 1  # one verdict per (requirement, test)


def test_from_rows_accepts_duplicates_mixed_with_distinct_pairs() -> None:
    associations = _rows(("R1", "t1"), ("R1", "t2"), ("R1", "t1"), ("R2", "t1"))

    assert associations.pair_count == 3
    assert associations.requirements() == ("R1", "R2")
    assert associations.tests_for("R1") == ("t1", "t2")
    assert associations.requirements_for("t1") == ("R1", "R2")  # reverse view


def test_ids_reject_whitespace() -> None:
    with pytest.raises(TrcError) as excinfo:
        AssociationSet.from_rows([("R 1", "t1")])
    assert excinfo.value.reason == "invalid_id"


def test_associations_from_datacases() -> None:
    associations = associations_from_datacases(
        [_case("case.one", ("REQ-1", "REQ-2")), _case("case.two", ("REQ-2",))]
    )

    assert associations.pair_count == 3
    assert associations.requirements() == ("REQ-1", "REQ-2")
    assert associations.tests_for("REQ-2") == ("case.one", "case.two")


# --- TOOL-TRC-020: bidirectional matrix ------------------------------------------------


def test_matrix_is_bidirectional_and_sorted() -> None:
    associations = _rows(("R2", "t.pass"), ("R1", "t.pass"), ("R1", "t.fail"))

    matrix = build_matrix(associations, STATUSES)

    assert list(matrix.forward()) == ["R1", "R2"]
    assert matrix.forward()["R1"] == ("t.fail", "t.pass")
    assert matrix.reverse() == {"t.fail": ("R1",), "t.pass": ("R1", "R2")}
    doc: dict[str, Any] = matrix.to_dict()
    assert set(doc) == {"forward", "pair_count", "reverse", "rows", "verdict_figures"}


# --- TOOL-TRC-030: per-test statuses in the matrix -------------------------------------


def test_links_carry_the_recorded_status() -> None:
    associations = _rows(("R1", "t.pass"), ("R1", "t.fail"))

    matrix = build_matrix(associations, STATUSES)

    links = {link.test_id: link.status for link in matrix.rows[0].links}
    assert links == {"t.pass": "pass", "t.fail": "fail"}


def test_linked_test_without_a_result_is_not_run() -> None:
    associations = _rows(("R1", "t.missing"))

    matrix = build_matrix(associations, STATUSES)

    assert matrix.rows[0].links[0].status == "not_run"
    assert matrix.rows[0].verdict == "unverified"


def test_unknown_status_is_refused() -> None:
    associations = _rows(("R1", "t1"))

    with pytest.raises(TrcError) as excinfo:
        build_matrix(associations, {"t1": "flaky"})
    assert excinfo.value.reason == "invalid_status"


# --- TOOL-TRC-110: worst-outcome verdicts, unreviewed, denominators --------------------


@pytest.mark.parametrize(
    ("linked", "expected"),
    [
        (("t.pass",), "pass"),
        (("t.pass", "t.fail"), "failed"),
        (("t.pass", "t.error"), "failed"),
        (("t.pass", "t.timeout"), "failed"),
        (("t.fail", "t.error"), "failed"),
        (("t.pass", "t.notrun"), "pass"),  # not_run is not an executed outcome
    ],
)
def test_verdict_is_the_worst_executed_outcome(linked: tuple[str, ...], expected: str) -> None:
    associations = _rows(*(("R1", t) for t in linked))

    matrix = build_matrix(associations, STATUSES)

    assert matrix.rows[0].verdict == expected


def test_requirement_linked_to_no_executed_test_is_unverified() -> None:
    """verifies: the PLAN-001 §5.4 criterion for WP-TRC-01."""
    associations = _rows(("R1", "t.notrun"), ("R1", "t.missing"))

    matrix = build_matrix(associations, STATUSES)

    assert matrix.rows[0].verdict == "unverified"


def test_universe_member_without_associations_is_unverified() -> None:
    associations = _rows(("R1", "t.pass"))

    matrix = build_matrix(associations, STATUSES, requirement_universe=("R1", "R2", "R3"))

    assert [row.verdict for row in matrix.rows] == ["pass", "unverified", "unverified"]
    assert matrix.rows[1].links == ()


def test_verdict_is_never_inferred_from_coverage() -> None:
    """Coverage is not an input; a coverage-like mapping cannot sway verdicts."""
    associations = _rows(("R1", "t.notrun"))
    coverage_like = {"R1": {"covered": 10, "total": 10}}  # present but unusable

    matrix = build_matrix(associations, STATUSES)  # coverage_like is not accepted at all

    assert matrix.rows[0].verdict == "unverified"
    assert coverage_like["R1"]["covered"] == 10  # unchanged: ignored


def test_unreviewed_generated_tests_count_as_unverified() -> None:
    """verifies: TOOL-TRC-110 — unreviewed origin per TOOL-ATG-080."""
    associations = _rows(("R1", "t.gen"), ("R2", "t.gen"))
    statuses = {"t.gen": "pass"}

    reviewed = build_matrix(associations, statuses)
    unreviewed = build_matrix(associations, statuses, unreviewed_tests=("t.gen",))

    assert reviewed.rows[0].verdict == "pass"
    assert unreviewed.rows[0].verdict == "unverified"  # flagged, does not execute into verdict
    assert unreviewed.rows[0].links[0].status == "pass"  # status still recorded
    assert unreviewed.rows[0].links[0].unreviewed is True


def test_one_reviewed_test_overrides_unreviewed_ones() -> None:
    associations = _rows(("R1", "t.gen"), ("R1", "t.pass"))
    statuses = {"t.gen": "pass", "t.pass": "pass"}

    matrix = build_matrix(associations, statuses, unreviewed_tests=("t.gen",))

    assert matrix.rows[0].verdict == "pass"


def test_figures_label_every_denominator() -> None:
    """verifies: TOOL-TRC-110 — every requirement-level percentage names it."""
    associations = _rows(("R1", "t.pass"), ("R1", "t.fail"), ("R2", "t.pass"))

    matrix = build_matrix(associations, STATUSES)
    figures = matrix.verdict_figures()

    assert figures["pair_count"] == 3
    assert figures["requirement_rows"] == 2
    assert figures["verdicts"] == {"failed": 1, "pass": 1, "unverified": 0}
    for verdict_percentage in figures["percentages"].values():
        assert "denominator" in verdict_percentage
        assert "requirement rows" in verdict_percentage["denominator"]
    assert "unique (requirement, test) pairs" in figures["pair_denominator"]


def test_matrix_is_deterministic_and_json_safe() -> None:
    associations = _rows(("R2", "t.pass"), ("R1", "t.fail"))

    first = json.dumps(build_matrix(associations, STATUSES).to_dict(), sort_keys=True)
    second = json.dumps(build_matrix(associations, STATUSES).to_dict(), sort_keys=True)

    assert first == second


# --- integration: statuses from the persisted report model -----------------------------


def test_statuses_come_from_a_report_model() -> None:
    result_set = ResultSet(
        run_id="run-1",
        execution=ExecutionMetadata(where="host", toolchain="gcc"),
        results=(
            finalize_result("t.pass", "pass", "d" * 64),
            finalize_result("t.fail", "fail", "e" * 64, failures=(_FAILURE,)),
        ),
    )
    report: ReportModel = build_report_model(result_set, clock=FixedClock("2026-11-19T00:00:00+00:00"))

    associations = _rows(("REQ-1", "t.pass"), ("REQ-1", "t.fail"))
    matrix = build_matrix(associations, report.test_statuses())

    assert matrix.rows[0].verdict == "failed"
    assert matrix.rows[0].links[0].status == "fail"  # links sort by test id
