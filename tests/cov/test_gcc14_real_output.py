# implements: TOOL-COV-050
"""The coverage reader against real GCC 14.4.0 output (see fixtures/gcc14/README.md)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.cov.gcov import read_gcov_document

FIXTURES = Path(__file__).parent / "fixtures" / "gcc14"


def _condition_lines(name: str) -> dict[int, tuple[int, int]]:
    document = read_gcov_document((FIXTURES / f"{name}.gcov.json").read_bytes())
    return {
        line.line_number: (line.conditions[0].count, line.conditions[0].covered)
        for file in document.files
        for line in file.lines
        if line.conditions
    }


def test_real_condition_records_are_read() -> None:
    """verifies: TOOL-COV-050 — ``count`` is two outcomes per condition."""
    lines = _condition_lines("mcdc")
    assert lines[2] == (4, 3)  # a && b
    assert lines[3] == (6, 3)  # a && (b || c)


@pytest.mark.parametrize(("name", "expected"), [("limit64", {1: (128, 64)}), ("limit65", {})])
def test_real_condition_limit(name: str, expected: dict[int, tuple[int, int]]) -> None:
    """verifies: TOOL-COV-190 — GCC measures 64 conditions and gives up at 65."""
    assert _condition_lines(name) == expected
