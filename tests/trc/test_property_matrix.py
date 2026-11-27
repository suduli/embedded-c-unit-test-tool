# implements: TOOL-TRC-020, TOOL-TRC-110
"""Seeded property-style tests over the traceability matrix (B7).

Tests only; no src/ edits. Association rows, statuses and unreviewed sets are
generated from fixed seeds (``random.Random(SEED)``) so a failure reproduces
exactly; no wall clock. Properties, not snapshots:

- symmetry: a pair ``(requirement, test)`` appears in ``forward`` if and only
  if it appears in ``reverse``, over every seeded draw;
- the pair count is exactly the number of unique pairs, never the raw row
  count;
- row order and link order are deterministic under input shuffling.
"""

from __future__ import annotations

import random

from ectt.trc import AssociationSet, build_matrix

# Aliased: a module-level name starting with "Test" is collected by pytest
# as a test class and warns.
from ectt.trc.matrix import TestLink as _TestLink

SEED = 20261123
_STATUSES = ("pass", "fail", "error", "timeout", "not_run")


def _seeded(rng: random.Random) -> tuple[AssociationSet, dict[str, str], set[str], list[tuple[str, str]]]:
    requirements = [f"REQ-{i:03d}" for i in range(rng.randint(2, 6))]
    tests = [f"t.{i:02d}" for i in range(rng.randint(2, 8))]
    raw = [(rng.choice(requirements), rng.choice(tests)) for _ in range(rng.randint(1, 12))]
    associations = AssociationSet.from_rows(raw)
    statuses = {test: rng.choice(_STATUSES) for test in tests}
    unreviewed = {test for test in tests if rng.random() < 0.3}
    return associations, statuses, unreviewed, raw


def test_matrix_forward_and_reverse_agree_over_seeded_draws() -> None:
    """verifies: TOOL-TRC-020 — symmetry: test in forward[req] iff req in reverse[test]."""
    for round_index in range(8):
        rng = random.Random(SEED + round_index)
        associations, statuses, unreviewed, raw = _seeded(rng)
        matrix = build_matrix(
            associations, statuses, unreviewed_tests=sorted(unreviewed)
        )
        forward = matrix.forward()
        reverse = matrix.reverse()

        unique_pairs = {(req, test) for req, test in raw}
        for requirement, test in unique_pairs:
            assert test in forward.get(requirement, ()), (round_index, requirement, test)
            assert requirement in reverse.get(test, ()), (round_index, requirement, test)
        # and nothing appears that was not a pair
        for requirement, tests in forward.items():
            for test in tests:
                assert (requirement, test) in unique_pairs
        for test, requirements in reverse.items():
            for requirement in requirements:
                assert (requirement, test) in unique_pairs


def test_pair_count_is_the_unique_pair_count_over_seeded_draws() -> None:
    """verifies: TOOL-TRC-110 — the numerator over unique pairs, never raw rows."""
    for round_index in range(8):
        rng = random.Random(SEED + 10 + round_index)
        associations, statuses, unreviewed, raw = _seeded(rng)
        matrix = build_matrix(associations, statuses, unreviewed_tests=sorted(unreviewed))
        assert matrix.pair_count == len({(req, test) for req, test in raw})
        # the rows agree with the associations: every linked test is a pair member
        for row in matrix.rows:
            for link in row.links:
                assert any(
                    row.requirement_id == req and link.test_id == test for req, test in raw
                )


def test_row_and_link_order_is_stable_under_input_shuffling() -> None:
    """The same associations in another order give the same rows, links and
    verdict figures."""
    for round_index in range(6):
        rng = random.Random(SEED + 20 + round_index)
        associations, statuses, unreviewed, raw = _seeded(rng)
        universe = sorted({req for req, _test in raw} | {f"REQ-X{i}" for i in range(rng.randint(0, 2))})
        first = build_matrix(associations, statuses, requirement_universe=universe, unreviewed_tests=sorted(unreviewed))

        shuffled = list(raw)
        rng.shuffle(shuffled)
        reassociated = AssociationSet.from_rows(shuffled)
        shuffled_statuses = dict(reversed(list(statuses.items())))
        second = build_matrix(
            reassociated,
            shuffled_statuses,
            requirement_universe=universe,
            unreviewed_tests=sorted(unreviewed),
        )
        assert first.to_dict() == second.to_dict(), round_index


def test_unreviewed_links_are_marked_and_keep_their_status() -> None:
    """The unreviewed mark travels with the link data (TOOL-ATG-080), whatever
    the draw; the verdict itself is WP-TRC-110 and covered above."""
    rng = random.Random(SEED + 30)
    associations, statuses, unreviewed, _raw = _seeded(rng)
    matrix = build_matrix(associations, statuses, unreviewed_tests=sorted(unreviewed))
    for row in matrix.rows:
        for link in row.links:
            assert isinstance(link, _TestLink)
            assert link.unreviewed == (link.test_id in unreviewed)
            assert link.status == statuses.get(link.test_id, "not_run")
