"""Tests for order planning and the order-independence check (WP-TCM-04).

Covers TOOL-TCD-090 per docs/verification/WP-TCM-04-analysis.md.
"""

from __future__ import annotations

from ectt.tcm.datacases import DataDrivenTestCase, TestCaseExpected, TestCaseInputs
from ectt.tcm.independence import check_order_independence, execution_order


def case(case_id: str) -> DataDrivenTestCase:  # type: ignore[no-untyped-def]
    return DataDrivenTestCase(
        case_id=case_id,
        unit="src/a.c",
        function="f",
        inputs=TestCaseInputs(),
        expected=TestCaseExpected(return_value="0"),
        stubs=(),
    )


def cases():  # type: ignore[no-untyped-def]
    return [case(f"tc.a.{i:04d}") for i in range(8)]


def test_declared_order_without_seed() -> None:
    ordered = execution_order(cases())
    assert ordered == tuple(f"tc.a.{i:04d}" for i in range(8))


def test_seeded_order_is_deterministic_across_calls() -> None:
    first = execution_order(cases(), order_seed=20260807)
    second = execution_order(cases(), order_seed=20260807)
    assert first == second
    assert sorted(first) == sorted(c.case_id for c in cases())  # permutation
    other = execution_order(cases(), order_seed=1)
    assert first != other  # different seed, different order (fixed seeds)
    # a lone case is trivially stable
    assert execution_order([case("tc.only")], order_seed=99) == ("tc.only",)


def test_identical_outcomes_are_order_independent() -> None:
    report = check_order_independence(
        {"tc.a": "pass", "tc.b": "pass", "tc.c": "fail"},
        {"tc.c": "fail", "tc.a": "pass", "tc.b": "pass"},
    )
    assert report.order_independent
    assert report.divergent == ()


def test_outcome_divergence_names_the_test() -> None:
    report = check_order_independence(
        {"tc.a": "pass", "tc.b": "pass"},
        {"tc.a": "pass", "tc.b": "fail"},
    )
    assert not report.order_independent
    assert report.divergent == ("tc.b",)


def test_execution_set_divergence_is_reported() -> None:
    report = check_order_independence(
        {"tc.a": "pass", "tc.b": "pass"},
        {"tc.a": "pass"},
    )
    assert not report.order_independent
    assert report.divergent == ("tc.b",)
