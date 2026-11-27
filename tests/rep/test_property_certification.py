# implements: TOOL-REP-060, TOOL-REP-140, TOOL-REP-100
"""Seeded property-style tests over the certification report (B7).

Tests only; no src/ edits. Inputs are generated from fixed seeds
(``random.Random(SEED)``) so a failure reproduces exactly; no wall clock.
Property: for every seeded draw, the report is byte-identical whatever order
its inputs arrive in - tests, coverage units, criteria evaluations,
traceability rows, justifications.

Criteria evaluations render sorted by metric and links sorted by test id.
"""

from __future__ import annotations

import random
from dataclasses import replace
from fractions import Fraction
from typing import Any

from ectt.core.determinism import FixedClock
from ectt.cov.justification import Justification
from ectt.cov.model import MetricTotals
from ectt.cov.thresholds import (
    MetricThreshold,
    enforce_thresholds,
)
from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.rep.certification import CertificationInputs, build_certification_report
from ectt.rep.model import CoverageEntry, build_report_model
from ectt.trc import AssociationSet, build_matrix
from ectt.trc.matrix import RequirementRow

# Aliased: a module-level name starting with "Test" is collected by pytest as
# a test class and warns.
from ectt.trc.matrix import TestLink as _TestLink

SEED = 20261123
_UNIT_ROOT = "src/u"
FIXED_CLOCK = FixedClock("2026-11-23T00:00:00+00:00")


def _fail_record(test_id: str) -> Any:
    """A fail record with the assertion entry it requires."""
    from ectt.exh.results import AssertionFailure, SourceLocation

    return finalize_result(
        test_id,
        "fail",
        test_id.encode("ascii").hex() * 24,
        failures=(
            AssertionFailure(
                assertion="assert_equal",
                expected="0",
                actual="1",
                location=SourceLocation(file=f"test_{test_id}.c", line=3),
            ),
        ),
    )


def _seeded_inputs(rng: random.Random) -> CertificationInputs:
    """A seeded draw. A ``fail`` record must name an assertion, so failing
    tests carry a standard failure entry; the rest draw as they come."""
    n_tests = rng.randint(1, 6)
    statuses = {f"t.{i}": rng.choice(("pass", "fail", "error", "timeout")) for i in range(n_tests)}
    results = []
    for test_id, outcome in sorted(statuses.items()):
        if outcome == "fail":
            results.append(_fail_record(test_id))
        else:
            results.append(finalize_result(test_id, outcome, test_id.encode("ascii").hex() * 24))
    results = tuple(results)
    n_units = rng.randint(1, 3)
    not_executed = tuple(f"t.n{i}" for i in range(rng.randint(0, 2)))
    coverage = tuple(
        CoverageEntry(unit=f"{_UNIT_ROOT}{i}.c", covered=rng.randint(0, 5), total=rng.randint(5, 10))
        for i in range(n_units)
    )
    model = build_report_model(
        ResultSet(
            run_id="run-seeded",
            execution=ExecutionMetadata(where="host", toolchain="gcc"),
            results=results,
            not_executed=not_executed,
            partial=bool(not_executed),
        ),
        coverage=coverage,
        clock=FIXED_CLOCK,
    )

    metrics = {
        "statements": MetricTotals(covered=rng.randint(0, 10), total=10),
        "branches": MetricTotals(covered=0, total=None),
    }
    criteria = enforce_thresholds(
        metrics,
        [MetricThreshold(metric="statements", minimum=Fraction(rng.randint(1, 9), 10))],
        allow_not_applicable=("branches",),
    )
    metrics_map = {
        evaluation.metric: MetricTotals(covered=evaluation.covered, total=evaluation.total)
        for evaluation in criteria.evaluations
    }

    requirements = [f"REQ-{i}" for i in range(rng.randint(1, 5))]
    drawable_tests = [*statuses, *not_executed]
    pairs = [(rng.choice(requirements), rng.choice(drawable_tests)) for _ in range(rng.randint(1, 8))]
    associations = AssociationSet()
    for requirement, test in pairs:
        associations.add(requirement, test)
    statuses_map = dict(statuses)
    for test in not_executed:
        statuses_map[test] = "not_run"
    matrix = build_matrix(associations, statuses_map)

    justifications = tuple(
        Justification(
            id=f"J-{i}",
            file=entry.unit,
            start_line=rng.randint(1, 9),
            end_line=rng.randint(10, 20),
            author="engineer",
            date="2026-11-20",
            rationale=f"justification {i}",
            source_digest=bytes([i]).hex() * 32,
        )
        for i, entry in enumerate(coverage)
        if rng.random() < 0.7
    )
    digests = {entry.unit: bytes([index]).hex() * 32 for index, entry in enumerate(coverage)}

    return CertificationInputs(
        model=model,
        coverage_metrics=metrics_map,
        coverage_criteria=criteria,
        traceability=matrix,
        justifications=justifications,
        source_digests=digests,
        host_profile=None,
    )


def _shuffled(rng: random.Random, inputs: CertificationInputs) -> CertificationInputs:
    assert inputs.model is not None
    assert inputs.coverage_metrics is not None and inputs.coverage_criteria is not None
    assert inputs.traceability is not None and inputs.justifications is not None
    assert inputs.source_digests is not None

    tests = list(inputs.model.tests)
    rng.shuffle(tests)
    coverage = list(inputs.model.coverage)
    rng.shuffle(coverage)
    metrics = dict(rng.sample(list(inputs.coverage_metrics.items()), len(inputs.coverage_metrics)))
    evaluations = list(inputs.coverage_criteria.evaluations)
    rng.shuffle(evaluations)
    rows = list(inputs.traceability.rows)
    rng.shuffle(rows)
    shuffled_rows = tuple(
        RequirementRow(
            requirement_id=row.requirement_id,
            links=tuple(_shuffled_links(rng, row.links)),
            verdict=row.verdict,
        )
        for row in rows
    )
    justifications = list(inputs.justifications)
    rng.shuffle(justifications)
    digests = dict(rng.sample(list(inputs.source_digests.items()), len(inputs.source_digests)))

    model = replace(
        inputs.model,
        tests=tuple(tests),
        coverage=tuple(coverage),
    )
    return replace(
        inputs,
        model=model,
        coverage_metrics=metrics,
        coverage_criteria=replace(inputs.coverage_criteria, evaluations=tuple(evaluations)),
        traceability=replace(inputs.traceability, rows=shuffled_rows),
        justifications=tuple(justifications),
        source_digests=digests,
    )


def _shuffled_links(rng: random.Random, links: tuple[_TestLink, ...]) -> tuple[_TestLink, ...]:
    shuffled = list(links)
    rng.shuffle(shuffled)
    return tuple(shuffled)


def test_the_report_is_stable_under_seeded_input_orders() -> None:
    """verifies: TOOL-REP-100 — the same content in any input order gives the
    same bytes, over seeded draws. Claims are drawn from the same data: a
    claim is requested only when the draw supports it, and the requested set
    itself is shuffled."""
    for round_index in range(6):
        rng = random.Random(SEED + round_index)
        inputs = _seeded_inputs(rng)
        first = build_certification_report(inputs)
        second = build_certification_report(_shuffled(rng, inputs))
        assert first.to_json_bytes() == second.to_json_bytes(), round_index
        assert first.claims == ()

        # a claim request the data supports (only when nothing was skipped and
        # everything passed) is stable under the same shuffle
        statuses = first.to_dict()["run"]["status_counts"]
        if not inputs.model.partial and statuses["not_run"] == 0 and statuses["pass"] == len(inputs.model.tests):
            claims = ("all_tests_executed", "all_tests_passed")
            claimed_first = build_certification_report(inputs, claims=claims)
            claimed_second = build_certification_report(_shuffled(rng, inputs), claims=claims)
            assert claimed_first.to_json_bytes() == claimed_second.to_json_bytes(), round_index
            assert claimed_first.claims == tuple(sorted(claims))


def test_missing_inputs_are_stable_over_seeded_draws() -> None:
    """A dropped input changes only its own missing-input entry, whatever the
    draw, and the set stays sorted."""
    for round_index in range(4):
        rng = random.Random(SEED + 40 + round_index)
        inputs = _seeded_inputs(rng)
        full = build_certification_report(inputs)
        without_justifications = build_certification_report(replace(inputs, justifications=None))
        assert "justified_exclusions" in without_justifications.missing_inputs
        assert set(without_justifications.missing_inputs) - set(full.missing_inputs) == {"justified_exclusions"}
        assert list(without_justifications.missing_inputs) == sorted(without_justifications.missing_inputs)
