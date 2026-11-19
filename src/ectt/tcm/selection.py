# implements: DSN-TCM-050
"""Suites and the shared selection expression (WP-TCM-04).

One selection expression serves the CLI, the engine API, and the GUI
(DSN-TCM-050): cases are selected by suite, unit, function, or test id.
Dimensions combine with OR ("by suite, unit, function, or test name",
TOOL-TCD-080); within a dimension, multiple values are OR. An empty
selection selects everything — no filter means run everything, never
silently nothing. The partition is deterministic: input order is preserved.

Suite membership itself rides the case model (``DataDrivenTestCase.suites``,
WP-TCM-02's record extended in this work package) and joins the content
digest per D-02 option (a).

Satisfies: TOOL-TCD-080; DSN-TCM-050.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ectt.tcm.datacases import DataDrivenTestCase
from ectt.tcm.errors import InvalidSelectionError

__all__ = [
    "Selection",
    "partition_cases",
]


@dataclass(frozen=True)
class Selection:
    """The shared selection expression: criteria per dimension, OR-combined."""

    suites: tuple[str, ...] = ()
    units: tuple[str, ...] = ()
    functions: tuple[str, ...] = ()
    test_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, values in (
            ("suites", self.suites),
            ("units", self.units),
            ("functions", self.functions),
            ("test_ids", self.test_ids),
        ):
            for value in values:
                if not isinstance(value, str) or not value.strip():
                    raise InvalidSelectionError(
                        f"selection {name} must be non-empty strings; got {value!r}"
                    )

    @property
    def is_empty(self) -> bool:
        """True when no criterion is set: everything is selected."""
        return not (self.suites or self.units or self.functions or self.test_ids)

    def matches(self, case: DataDrivenTestCase) -> bool:
        """OR across dimensions, OR within each dimension."""
        if self.is_empty:
            return True
        matched: list[bool] = []
        if self.suites:
            matched.append(bool(set(case.suites) & set(self.suites)))
        if self.units:
            matched.append(case.unit in self.units)
        if self.functions:
            matched.append(case.function in self.functions)
        if self.test_ids:
            matched.append(case.case_id in self.test_ids)
        return any(matched)


def _require_case(case: Any) -> DataDrivenTestCase:
    if not isinstance(case, DataDrivenTestCase):
        raise InvalidSelectionError(
            f"selection operates on DataDrivenTestCase records, got {type(case).__name__}"
        )
    return case


def partition_cases(
    cases: Iterable[DataDrivenTestCase],
    selection: Selection,
) -> tuple[tuple[DataDrivenTestCase, ...], tuple[DataDrivenTestCase, ...]]:
    """Split cases into (selected, excluded) under ``selection``.

    Deterministic: both halves preserve the input order.
    """
    selected: list[DataDrivenTestCase] = []
    excluded: list[DataDrivenTestCase] = []
    for case in cases:
        checked = _require_case(case)
        if selection.is_empty or selection.matches(checked):
            selected.append(checked)
        else:
            excluded.append(checked)
    return tuple(selected), tuple(excluded)
