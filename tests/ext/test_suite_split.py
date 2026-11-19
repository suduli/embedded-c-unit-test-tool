"""Tests for the WP-EXT-06 suite splitting and footprint documentation.

Verifies: TOOL-TGT-100, TOOL-TGT-110.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.ext import (
    OVERHEAD_BASIS,
    ChunkTooLargeError,
    SuiteSplit,
    UnknownConfigurationError,
    overhead_table,
    split_suite,
)


def test_fitting_suite_is_not_split() -> None:
    """verifies: TOOL-TGT-100"""
    split = split_suite({"a": 10, "b": 20, "c": 30}, budget=100)
    assert isinstance(split, SuiteSplit)
    assert split.split_needed is False
    assert len(split.chunks) == 1
    assert split.chunks[0].tests == ("a", "b", "c")
    assert split.chunks[0].total_cost == 60


def test_oversized_suite_splits_into_multiple_executions() -> None:
    """verifies: TOOL-TGT-100"""
    split = split_suite({"a": 40, "b": 40, "c": 40, "d": 40}, budget=100)
    assert split.split_needed is True
    assert len(split.chunks) == 2
    assert split.chunks[0].tests == ("a", "b")
    assert split.chunks[1].tests == ("c", "d")


def test_every_test_appears_exactly_once() -> None:
    """verifies: TOOL-TGT-100"""
    costs = {"alpha": 60, "beta": 60, "gamma": 60, "delta": 25, "epsilon": 25}
    split = split_suite(costs, budget=100)
    seen = [test for chunk in split.chunks for test in chunk.tests]
    assert sorted(seen) == sorted(costs)
    assert len(seen) == len(set(seen))


def test_chunks_are_deterministically_ordered_and_sorted() -> None:
    """verifies: TOOL-TGT-100"""
    first = split_suite({"zeta": 50, "alpha": 50, "mid": 50}, budget=90)
    second = split_suite({"mid": 50, "zeta": 50, "alpha": 50}, budget=90)
    assert first.to_dict() == second.to_dict()
    assert all(list(c.tests) == sorted(c.tests) for c in first.chunks)


def test_first_fit_minimises_chunk_count() -> None:
    """verifies: TOOL-TGT-100"""
    # 5 tests of 20 each, budget 100: exactly 1 chunk. budget 60: 2 chunks.
    costs = {"a": 20, "b": 20, "c": 20, "d": 20, "e": 20}
    assert len(split_suite(costs, budget=100).chunks) == 1
    assert len(split_suite(costs, budget=60).chunks) == 2


def test_chunk_larger_than_budget_is_named_error() -> None:
    """verifies: TOOL-TGT-100"""
    with pytest.raises(ChunkTooLargeError) as excinfo:
        split_suite({"huge": 500, "small": 10}, budget=100)
    assert "huge" in str(excinfo.value)
    with pytest.raises(ChunkTooLargeError):
        split_suite({"a": 10}, budget=0)


def test_overhead_documented_per_configuration() -> None:
    """verifies: TOOL-TGT-110"""
    table = overhead_table()
    entry = table.lookup("qemu-mps2-an385")
    assert entry.ram_bytes == 256
    assert entry.flash_bytes == 1024
    assert entry.stack_bytes == 128
    assert table.lookup("stm32f407vg-openocd").ram_bytes == 192
    assert table.lookup("stm32f411re-pyocd").flash_bytes == 768


def test_overhead_states_its_measurement_basis() -> None:
    """verifies: TOOL-TGT-110"""
    table = overhead_table()
    assert "analytical estimates" in table.basis
    assert "pending on-target measurement" in table.basis
    assert all(entry.basis == OVERHEAD_BASIS for entry in table.entries)


def test_unknown_configuration_is_named_error() -> None:
    """verifies: TOOL-TGT-110"""
    table = overhead_table()
    with pytest.raises(UnknownConfigurationError) as excinfo:
        table.lookup("unknown-board")
    assert "unknown-board" in str(excinfo.value)


def test_table_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-TGT-110"""
    table = overhead_table()
    assert table.to_dict() == overhead_table().to_dict()
    assert [e.configuration for e in table.entries] == sorted(
        e.configuration for e in table.entries
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        table.basis = "x"  # type: ignore[misc]
