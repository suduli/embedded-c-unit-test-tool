# implements: TOOL-COV-110, TOOL-COV-180, TOOL-COV-220
"""Seeded property-style tests over the coverage merge (B9).

Tests only; no src/ edits. Inputs are generated from fixed seeds
(``random.Random(SEED)``) so a failure reproduces exactly; no wall clock.
Properties, not snapshots:

- conservation: the merged per-line counts equal the sum over admitted runs
  that instrument the line (no double counting, nothing lost);
- order independence: shuffling the run order yields byte-identical merges;
- quarantine: every run with an error/timeout outcome stays out of the
  aggregate and inside the provenance, whatever the random draw;
- completeness: truncated/missing artifacts never contribute, whatever the
  random draw.
"""

from __future__ import annotations

import random

from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import RunCoverage, merge_run_coverage

SEED = 20261121
_OUTCOMES = ("pass", "fail", "error", "timeout", "not_run")
_QUARANTINED = ("error", "timeout")


def _seeded_document(rng: random.Random, file_id: str, n_lines: int):
    # one shared data_file: this models runs of ONE build (the standard merge
    # scenario). The merge takes its representative data_file from the first
    # admitted run in input order, so per-run data_file values would make the
    # aggregate depend on the input order - recorded as a cov follow-up in the
    # lane ledger and SECOND_PASS_B.
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "build.gcda",
        "files": [
            {
                "file": file_id,
                "lines": [
                    {
                        "line_number": number,
                        "count": rng.randint(0, 5),
                        "unexecuted_block": rng.random() < 0.2,
                    }
                    for number in range(1, n_lines + 1)
                ],
            }
        ],
    }
    return read_gcov_document(payload)


def _seeded_runs(rng: random.Random, n_runs: int) -> list[RunCoverage]:
    runs: list[RunCoverage] = []
    for index in range(n_runs):
        document = _seeded_document(rng, f"f{index % 3}.c", rng.randint(1, 6))
        outcome = rng.choice(_OUTCOMES)
        completeness = rng.choices(("complete", "truncated", "missing"), weights=(6, 2, 2))[0]
        if completeness == "missing":
            runs.append(
                RunCoverage(
                    test_id=f"t{index:02d}",
                    outcome=outcome,
                    completeness="missing",
                    advisory=f"no artifact for run {index}",
                )
            )
        elif completeness == "truncated":
            runs.append(
                RunCoverage(
                    test_id=f"t{index:02d}",
                    outcome=outcome,
                    completeness="truncated",
                    document=document,
                    advisory=f"truncated dump for run {index}",
                )
            )
        else:
            runs.append(
                RunCoverage(
                    test_id=f"t{index:02d}",
                    outcome=outcome,
                    completeness="complete",
                    document=document,
                )
            )
    return runs


def _admitted_ids(runs: list[RunCoverage]) -> set[str]:
    return {
        run.test_id
        for run in runs
        if run.completeness == "complete"
        and run.outcome not in _QUARANTINED
    }


def test_merge_conservation_over_seeded_runs() -> None:
    rng = random.Random(SEED)
    for round_index in range(5):
        runs = _seeded_runs(rng, rng.randint(3, 8))
        result = merge_run_coverage(runs)

        admitted = _admitted_ids(runs)
        # conservation, per file and line: merged count == sum over admitted runs
        merged_counts: dict[tuple[str, int], int] = {}
        for file in result.document.files:
            for line in file.lines:
                merged_counts[(file.file, line.line_number)] = line.count
        for key, merged_count in merged_counts.items():
            path, number = key
            total = 0
            for run in runs:
                if run.test_id not in admitted or run.document is None:
                    continue
                for file in run.document.files:
                    if file.file == path:
                        for line in file.lines:
                            if line.line_number == number:
                                total += line.count
            assert merged_count == total, (round_index, key)
        # nothing fabricated: the merged set is exactly the union of admitted lines
        union_keys = set()
        for run in runs:
            if run.test_id not in admitted or run.document is None:
                continue
            for file in run.document.files:
                for line in file.lines:
                    union_keys.add((file.file, line.line_number))
        assert set(merged_counts) == union_keys


def test_merge_is_order_independent_over_seeded_runs() -> None:
    rng = random.Random(SEED + 1)
    for _round_index in range(5):
        runs = _seeded_runs(rng, rng.randint(3, 8))
        result_a = merge_run_coverage(runs)
        shuffled = list(runs)
        rng.shuffle(shuffled)
        result_b = merge_run_coverage(shuffled)
        assert result_a.document.to_json_bytes() == result_b.document.to_json_bytes()
        assert {excluded.test_id for excluded in result_a.excluded} == {
            excluded.test_id for excluded in result_b.excluded
        }


def test_quarantine_holds_over_seeded_outcomes() -> None:
    """verifies: TOOL-COV-220 — whatever the random draw, quarantined outcomes
    never contribute and stay in provenance."""
    rng = random.Random(SEED + 2)
    for _round_index in range(5):
        runs = _seeded_runs(rng, rng.randint(4, 9))
        result = merge_run_coverage(runs)
        admitted_ids = _admitted_ids(runs)
        for run in runs:
            if run.outcome in _QUARANTINED and run.completeness == "complete":
                assert run.test_id not in admitted_ids
                assert run.test_id in {r.test_id for r in result.per_run}
                assert run.test_id in {e.test_id for e in result.excluded}
                assert not any(run.test_id == r.test_id for r in result.per_run if r.test_id in admitted_ids)


def test_incomplete_artifacts_never_contribute_over_seeded_draws() -> None:
    rng = random.Random(SEED + 3)
    for _round_index in range(5):
        runs = _seeded_runs(rng, rng.randint(4, 9))
        result = merge_run_coverage(runs)
        excluded = {e.test_id for e in result.excluded}
        for run in runs:
            if run.completeness != "complete":
                assert run.test_id in excluded
                assert run.advisory  # the advisory always travels


def test_no_wall_clock_in_seeded_documents() -> None:
    rng = random.Random(SEED + 4)
    runs = _seeded_runs(rng, 4)
    result = merge_run_coverage(runs)
    dumped = result.document.to_json_bytes().decode("utf-8")
    assert "generated_at" not in dumped and "timestamp" not in dumped
