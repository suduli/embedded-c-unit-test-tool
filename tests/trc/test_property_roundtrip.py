# implements: TOOL-TRC-020, TOOL-TRC-070
"""Seeded property-style tests: matrix consistency and ReqIF round trip (B9).

Tests only; no src/ edits. Every generator is seeded from a fixed constant
(``random.Random(SEED)``), so a failure reproduces exactly; no wall clock
anywhere (``creation_time`` is a fixed string). Properties, not snapshots:

- the matrix's forward and reverse maps are inverse views of the same pairs;
- ``pair_count`` equals the number of unique pairs (never the raw row count);
- a requirement's verdict is the worst outcome among its linked executed,
  reviewed tests, and ``unverified`` when none;
- export → import reproduces the records and the exact unique pair set;
- identical seeds produce byte-identical exports.
"""

from __future__ import annotations

import random
import re

from ectt.trc import (
    Association,
    AssociationSet,
    RequirementRecord,
    build_matrix,
    export_reqif,
    import_reqif_with_associations,
)

SEED = 20261121
WHEN = "2026-11-21T00:00:00+00:00"
_STATUSES = ("pass", "fail", "error", "timeout", "not_run")
_FAILING = ("fail", "error", "timeout")


def _seeded_pairs(rng: random.Random, n_requirements: int, n_tests: int, n_pairs: int):
    requirements = [f"REQ-{i:03d}" for i in range(n_requirements)]
    tests = [f"t.{i:03d}" for i in range(n_tests)]
    raw = [(rng.choice(requirements), rng.choice(tests)) for _ in range(n_pairs)]
    return requirements, tests, raw


def _verdict_of(pairs, requirement: str, statuses: dict[str, str], unreviewed: set[str]) -> str:
    """The property the matrix must satisfy, computed independently."""
    linked = [test_id for req, test_id in pairs if req == requirement]
    executed = [t for t in linked if t in statuses and statuses[t] in (*_FAILING, "pass") and t not in unreviewed]
    if not executed:
        return "unverified"
    worst = max(executed, key=lambda t: 2 if statuses[t] in _FAILING else 0)
    return "failed" if statuses[worst] in _FAILING else "pass"


def test_matrix_properties_over_seeded_inputs() -> None:
    rng = random.Random(SEED)
    for round_index in range(5):
        requirements, tests, raw = _seeded_pairs(rng, 8, 10, 25)
        associations = AssociationSet.from_rows(raw)
        statuses = {t: rng.choice(_STATUSES) for t in tests}
        unreviewed = {t for t in tests if rng.random() < 0.3}
        universe = [*requirements, "REQ-EXTRA"]
        matrix = build_matrix(associations, statuses, requirement_universe=universe, unreviewed_tests=unreviewed)

        unique_pairs = {(req, test) for req, test in raw}
        # pair_count is the unique-pair numerator
        assert matrix.pair_count == len(unique_pairs)
        # forward and reverse are inverse views of the same pairs
        forward = matrix.forward()
        assert all(req in forward for req, _ in unique_pairs)
        reverse = matrix.reverse()
        for req, test in unique_pairs:
            assert test in forward[req]
            assert req in reverse[test]
        # row verdicts equal the independently computed property
        rows = {row.requirement_id: row for row in matrix.rows}
        for requirement in universe:
            expected = _verdict_of(unique_pairs, requirement, statuses, unreviewed)
            assert rows[requirement].verdict == expected, (round_index, requirement)


def test_reqif_roundtrip_over_seeded_inputs() -> None:
    rng = random.Random(SEED + 1)
    for _round_index in range(5):
        requirements, tests, raw = _seeded_pairs(rng, 6, 8, 15)
        associations = AssociationSet.from_rows(raw)
        statuses = {t: rng.choice(_STATUSES) for t in tests}
        unreviewed = {t for t in tests if rng.random() < 0.25}
        matrix = build_matrix(associations, statuses, requirement_universe=requirements, unreviewed_tests=unreviewed)
        records = tuple(
            RequirementRecord(req, f"title {req}", f"text for {req} with <markup> & entities")
            for req in sorted(requirements)
        )

        text = export_reqif(matrix, records, creation_time=WHEN)
        imported = import_reqif_with_associations(text)

        # associations come back exactly as the unique pairs
        expected_pairs = tuple(sorted(Association(req, test) for req, test in {(r, t) for r, t in raw}))
        assert imported.associations.pairs == expected_pairs
        # records match the inventory (deduplicated ids keep the first title/text)
        assert sorted(r.requirement_id for r in imported.records) == sorted(requirements)
        by_id = {r.requirement_id: r for r in imported.records}
        for record in records:
            assert by_id[record.requirement_id].title == record.title
            assert by_id[record.requirement_id].text == record.text


def test_identical_seed_produces_byte_identical_export() -> None:
    """No wall-clock: the same seed and inputs render the same bytes."""

    def render(seed: int) -> str:
        rng = random.Random(seed)
        _, _, raw = _seeded_pairs(rng, 5, 6, 12)
        associations = AssociationSet.from_rows(raw)
        statuses = {t: rng.choice(_STATUSES) for t in {t for _, t in raw}}
        matrix = build_matrix(associations, statuses, requirement_universe=[f"REQ-{i:03d}" for i in range(5)])
        return export_reqif(matrix, (), creation_time=WHEN)

    assert render(SEED) == render(SEED)
    assert re.search(r'CREATION-TIME>' + re.escape(WHEN), render(SEED))


def test_shuffled_pair_order_gives_identical_matrix_and_export() -> None:
    """Association rows arrive in arbitrary order; the artifacts do not care."""
    rng = random.Random(SEED + 2)
    _, _, raw = _seeded_pairs(rng, 6, 7, 18)
    statuses = {t: rng.choice(_STATUSES) for t in {t for _, t in raw}}
    universe = sorted({req for req, _ in raw})

    matrix_a = build_matrix(AssociationSet.from_rows(raw), statuses, requirement_universe=universe)
    shuffled = list(raw)
    rng.shuffle(shuffled)
    matrix_b = build_matrix(AssociationSet.from_rows(shuffled), statuses, requirement_universe=universe)
    assert matrix_a.to_dict() == matrix_b.to_dict()

    text_a = export_reqif(matrix_a, (), creation_time=WHEN)
    text_b = export_reqif(matrix_b, (), creation_time=WHEN)
    assert text_a == text_b
