# implements: TOOL-TRC-040
"""Unlinked requirement and unlinked test reporting (WP-TRC-02).

Equivalence partitioning: linked vs unlinked on both sides, mixed universes,
empty associations, and consistency with the WP-TRC-01 matrix.
"""

from __future__ import annotations

import json

import pytest

from ectt.trc.associations import AssociationSet
from ectt.trc.matrix import build_matrix
from ectt.trc.unlinked import find_unlinked


def _rows(*pairs: tuple[str, str]) -> AssociationSet:
    return AssociationSet.from_rows(pairs)


def test_requirements_without_tests_and_tests_without_requirements_are_reported() -> None:
    associations = _rows(("R1", "t1"), ("R2", "t1"))

    report = find_unlinked(
        associations,
        requirement_universe=("R1", "R2", "R3", "R4"),
        test_universe=("t1", "t2", "t3"),
    )

    assert report.unlinked_requirements == ("R3", "R4")
    assert report.unlinked_tests == ("t2", "t3")


def test_fully_linked_universes_report_nothing() -> None:
    associations = _rows(("R1", "t1"), ("R2", "t2"))

    report = find_unlinked(
        associations, requirement_universe=("R1", "R2"), test_universe=("t1", "t2")
    )

    assert report.unlinked_requirements == ()
    assert report.unlinked_tests == ()


def test_empty_associations_report_everything() -> None:
    report = find_unlinked(
        _rows(),
        requirement_universe=("R1", "R2"),
        test_universe=("t1",),
    )

    assert report.unlinked_requirements == ("R1", "R2")
    assert report.unlinked_tests == ("t1",)


def test_empty_universes_report_nothing_without_hiding_gaps() -> None:
    """Universes are explicit: an empty universe is an honest empty report."""
    report = find_unlinked(_rows(("R1", "t1")), requirement_universe=(), test_universe=())

    assert report.unlinked_requirements == ()
    assert report.unlinked_tests == ()
    assert report.to_dict() == {
        "requirement_universe_size": 0,
        "test_universe_size": 0,
        "unlinked_requirements": [],
        "unlinked_tests": [],
    }


def test_duplicate_universe_entries_collapse() -> None:
    associations = _rows(("R1", "t1"))

    report = find_unlinked(
        associations,
        requirement_universe=("R1", "R1", "R2"),
        test_universe=("t1", "t2", "t2"),
    )

    assert report.requirement_universe == ("R1", "R2")
    assert report.unlinked_requirements == ("R2",)
    assert report.unlinked_tests == ("t2",)


def test_report_is_deterministic_and_json_safe() -> None:
    associations = _rows(("R1", "t1"))

    first = json.dumps(
        find_unlinked(
            associations,
            requirement_universe=("R2", "R1"),
            test_universe=("t2", "t1"),
        ).to_dict(),
        sort_keys=True,
    )
    second = json.dumps(
        find_unlinked(
            associations,
            requirement_universe=("R1", "R2"),
            test_universe=("t1", "t2"),
        ).to_dict(),
        sort_keys=True,
    )

    assert first == second


def test_consistent_with_the_matrix_unverified_rows() -> None:
    """Unlinked requirements are exactly the matrix rows without links."""
    associations = _rows(("R1", "t1"), ("R2", "t2"))
    requirement_universe = ("R1", "R2", "R3")

    report = find_unlinked(associations, requirement_universe=requirement_universe, test_universe=("t1", "t2"))
    matrix = build_matrix(associations, {}, requirement_universe=requirement_universe)

    matrix_linkless = tuple(row.requirement_id for row in matrix.rows if not row.links)
    assert report.unlinked_requirements == matrix_linkless == ("R3",)
    assert all(row.verdict == "unverified" for row in matrix.rows if not row.links)


def test_universe_sizes_are_recorded_for_review() -> None:
    report = find_unlinked(
        _rows(("R1", "t1")),
        requirement_universe=("R1", "R2"),
        test_universe=("t1", "t2", "t3"),
    )

    assert report.to_dict()["requirement_universe_size"] == 2
    assert report.to_dict()["test_universe_size"] == 3


@pytest.mark.parametrize(
    ("requirements", "tests", "expected_reqs", "expected_tests"),
    [
        (("R1",), ("t1",), (), ()),
        (("R1", "R2"), ("t1",), ("R2",), ()),
        (("R1",), ("t1", "t2"), (), ("t2",)),
        ((), (), (), ()),
    ],
)
def test_partition_table(
    requirements: tuple[str, ...],
    tests: tuple[str, ...],
    expected_reqs: tuple[str, ...],
    expected_tests: tuple[str, ...],
) -> None:
    associations = _rows(("R1", "t1"))

    report = find_unlinked(associations, requirement_universe=requirements, test_universe=tests)

    assert report.unlinked_requirements == expected_reqs
    assert report.unlinked_tests == expected_tests
