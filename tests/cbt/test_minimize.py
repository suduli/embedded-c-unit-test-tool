# implements: TOOL-CBT-080
"""Test suite minimization (WP-CBT-04).

The invariant under test: union preservation (the kept set covers everything the
whole suite covered) plus loss-free redundancy (every redundant case adds nothing
the kept set does not cover), with deterministic tie-breaking.
"""

from __future__ import annotations

import random

import pytest

from ectt.cbt import Minimization, minimize_suite

COVERAGE = {
    "tc.alpha": ("src/adc.c:L1", "src/adc.c:L2"),
    "tc.beta": ("src/adc.c:L1", "src/adc.c:L2"),  # duplicate of alpha
    "tc.gamma": ("src/adc.c:L2",),  # subset of alpha
    "tc.delta": ("src/hal.c:L1",),  # unique contributor
    "tc.epsilon": ("src/dsp.c:L1", "src/dsp.c:L2", "src/dsp.c:L3"),
}


def _union(coverage_by_test: dict[str, tuple[str, ...]], ids: tuple[str, ...]) -> set[str]:
    union: set[str] = set()
    for test_id in ids:
        union.update(coverage_by_test[test_id])
    return union


def _assert_loss_free(coverage_by_test: dict[str, tuple[str, ...]], result: Minimization) -> None:
    """The invariant: union preserved, and every redundant case adds nothing."""
    assert _union(coverage_by_test, result.kept) == _union(coverage_by_test, tuple(coverage_by_test))
    kept_union = _union(coverage_by_test, result.kept)
    for test_id in result.redundant:
        assert set(coverage_by_test[test_id]) <= kept_union


def test_a_subset_test_is_redundant() -> None:
    """verifies: TOOL-CBT-080 — a case whose coverage is contained in another's
    is redundant; the unique contributor is kept."""
    result = minimize_suite(COVERAGE)
    assert result.redundant == ("tc.beta", "tc.gamma")
    assert result.kept == ("tc.alpha", "tc.delta", "tc.epsilon")
    _assert_loss_free(COVERAGE, result)


def test_a_duplicate_test_is_redundant_and_one_is_kept() -> None:
    """verifies: TOOL-CBT-080 — identical coverage keeps exactly one test."""
    coverage = {"tc.b": ("L1",), "tc.a": ("L1",), "tc.c": ("L1",)}
    result = minimize_suite(coverage)
    assert result.kept == ("tc.a",)
    assert result.redundant == ("tc.b", "tc.c")
    _assert_loss_free(coverage, result)


def test_a_unique_contributor_is_never_dropped() -> None:
    """verifies: TOOL-CBT-080 — dropping the unique contributor would lose
    coverage, so it is always kept."""
    coverage = {"tc.a": ("L1",), "tc.b": ("L1", "L2")}
    result = minimize_suite(coverage)
    assert "tc.b" in result.kept
    assert result.redundant == ("tc.a",)
    _assert_loss_free(coverage, result)


def test_the_union_is_preserved() -> None:
    """verifies: TOOL-CBT-080 — minimizing loses no coverage at all."""
    result = minimize_suite(COVERAGE)
    _assert_loss_free(COVERAGE, result)


def test_the_result_is_deterministic_under_input_shuffling() -> None:
    """verifies: AC-2 — same data in any mapping order, same answer."""
    first = minimize_suite(COVERAGE)
    shuffled = dict(reversed(list(COVERAGE.items())))
    second = minimize_suite(shuffled)
    assert first == second


def test_an_empty_suite_minimizes_to_nothing() -> None:
    """verifies: AC-3 — no tests, no verdict."""
    result = minimize_suite({})
    assert result == Minimization(kept=(), redundant=())


def test_tests_covering_nothing_are_all_redundant() -> None:
    """verifies: AC-3 — an empty union is preserved by the empty kept set."""
    coverage = {"tc.a": (), "tc.b": ()}
    result = minimize_suite(coverage)
    assert result == Minimization(kept=(), redundant=("tc.a", "tc.b"))


def test_blank_ids_and_non_constructs_are_refused() -> None:
    """verifies: AC-3 — malformed input is refused before any selection."""
    with pytest.raises(ValueError) as blank:
        minimize_suite({" ": ("L1",)})
    assert "non-empty test ids" in str(blank.value)
    with pytest.raises(ValueError) as nonconstruct:
        minimize_suite({"tc.a": (12,)})  # type: ignore[list-item]
    assert "non-construct" in str(nonconstruct.value)


def test_seeded_union_preservation() -> None:
    """verifies: TOOL-CBT-080 — the invariant holds for seeded random suites
    (fixed seeds; no wall clock)."""
    for seed in range(20):
        rng = random.Random(seed)
        constructs = [f"L{i}" for i in range(rng.randint(2, 12))]
        coverage = {
            f"tc.{i:02d}": tuple(sorted(rng.sample(constructs, rng.randint(0, len(constructs)))))
            for i in range(rng.randint(1, 8))
        }
        result = minimize_suite(coverage)
        _assert_loss_free(coverage, result)
        assert not (set(result.kept) & set(result.redundant))
        assert set(result.kept) | set(result.redundant) == set(coverage)
