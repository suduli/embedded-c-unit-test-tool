# implements: TOOL-CBT-020
"""Change impact analysis (WP-CBT-02, TOOL-CBT-020).

A case is affected exactly when the constructs its recorded per-test coverage
covers intersect the changed set; the answer is sorted and deterministic;
degenerate inputs are ordinary results, not errors.
"""

from __future__ import annotations

import pytest

from ectt.cbt import ImpactResult, SourceChange, affected_cases

COVERAGE = {
    "tc.alpha": ("src/adc.c", "src/adc.c:L10", "src/hal.c:L3"),
    "tc.beta": ("src/hal.c:L3", "src/hal.c:L7"),
    "tc.gamma": ("src/dsp.c:L1",),
}


def _change(*constructs: str) -> SourceChange:
    return SourceChange(frozenset(constructs))


def test_affected_exactly_when_the_covered_set_intersects_the_change() -> None:
    """verifies: TOOL-CBT-020 — intersection is the whole decision."""
    result = affected_cases(_change("src/hal.c:L7"), COVERAGE)
    assert result.affected == ("tc.beta",)
    assert result.unaffected == ("tc.alpha", "tc.gamma")
    assert result.uncovered_by_tests == ()


def test_unaffected_cases_are_never_listed() -> None:
    """verifies: TOOL-CBT-020 — a case whose coverage misses the change stays
    out of the affected set, whatever its other coverage."""
    result = affected_cases(_change("src/dsp.c:L1"), COVERAGE)
    assert result.affected == ("tc.gamma",)
    assert "tc.alpha" not in result.affected and "tc.beta" not in result.affected


def test_overlapping_coverage_affects_every_covering_case() -> None:
    """verifies: TOOL-CBT-020 — two tests covering the changed construct are
    both affected."""
    result = affected_cases(_change("src/hal.c:L3"), COVERAGE)
    assert result.affected == ("tc.alpha", "tc.beta")


def test_an_empty_change_affects_nothing() -> None:
    """verifies: TOOL-CBT-020 — no change, no impact."""
    result = affected_cases(SourceChange(), COVERAGE)
    assert result.affected == ()
    assert result.unaffected == ("tc.alpha", "tc.beta", "tc.gamma")


def test_a_construct_no_test_covered_affects_nothing() -> None:
    """verifies: TOOL-CBT-020 — an uncovered change is surfaced, not an error."""
    result = affected_cases(_change("src/boot.c:L1"), COVERAGE)
    assert result.affected == ()
    assert result.uncovered_by_tests == ("src/boot.c:L1",)


def test_the_output_is_sorted_and_deterministic() -> None:
    """verifies: TOOL-NFR-060 — same inputs, same sorted answer."""
    coverage = {
        "tc.z": ("src/a.c:L1",),
        "tc.a": ("src/a.c:L1",),
        "tc.m": ("src/b.c:L1",),
    }
    first = affected_cases(_change("src/a.c:L1"), coverage)
    second = affected_cases(SourceChange(frozenset({"src/a.c:L1"})), coverage)
    assert first == second
    assert isinstance(first, ImpactResult)
    assert first.affected == ("tc.a", "tc.z")
    assert first.unaffected == ("tc.m",)


def test_a_change_construct_may_not_be_empty() -> None:
    """verifies: API — blank construct ids are refused at construction."""
    with pytest.raises(ValueError):
        SourceChange(frozenset({" "}))
