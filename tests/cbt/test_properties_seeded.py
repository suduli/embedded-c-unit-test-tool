# implements: TOOL-CBT-010, TOOL-CBT-020
"""Seeded property-style tests for ectt.cbt (A7, tests only; no src/ edits).

Fixed seeds (the seed is the test id); no wall clock. Properties:

* **Re-execution record round trip** (TOOL-CBT-010): for random suites, the
  stored record round-trips byte-identically, keeps its digest-bound id, and
  refuses any tampering with its content or its bindings.
* **Impact sets under random changes** (TOOL-CBT-020): for random coverage maps
  and random changes, a case is affected exactly when its covered set intersects
  the change (checked against an independent set-intersection oracle); the diff
  mapper's construct identities under random extents always name the containing
  function, and the affected/unaffected partition is exact.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from ectt.cbt import (
    LineRange,
    SourceChange,
    SourceDiff,
    affected_cases,
    bindings_from_cases,
    changed_constructs,
    dump_suite_record,
    load_suite_record,
    record_compiled_suite,
)
from ectt.exh.results import ExecutionMetadata
from ectt.tcm import datacases as dd

SEEDS = [0, 1, 7, 42, 1337]

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")


def _case(rng: random.Random, index: int) -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id=f"tc.{index:03d}",
            unit=f"src/unit_{rng.randint(0, 3)}.c",
            function="f",
            inputs=dd.TestCaseInputs(parameters={"x": str(rng.randint(0, 100))}),
            expected=dd.TestCaseExpected(return_value=str(rng.randint(0, 50))),
            stubs=(),
        )
    )


def _random_identifier(rng: random.Random) -> str:
    head = rng.choice("abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    body = "".join(
        rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
        for _ in range(rng.randint(0, 24))
    )
    return head + body


@pytest.mark.parametrize("seed", SEEDS)
def test_record_round_trips_byte_identically_and_refuses_tampering(seed: int, tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — random suites: dump -> load is lossless, the
    document is deterministic, and any content or binding edit is refused."""
    rng = random.Random(seed)
    cases = [_case(rng, i) for i in range(rng.randint(1, 6))]
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / f"harness_{seed}").write_text(
        "\n".join(f"print('RESULT {c.case_id} pass')" for c in cases) + f"\n# seed {seed}\n",
        encoding="utf-8",
    )
    record = record_compiled_suite(
        tmp_path, f"build/harness_{seed}", EXECUTION, bindings_from_cases(cases)
    )
    dumped = dump_suite_record(record)
    assert dumped == dump_suite_record(record)  # deterministic
    assert load_suite_record(dumped) == record

    tampered = json.loads(dumped)
    tampered["toolchain"] = "clang-99"
    with pytest.raises(Exception) as excinfo:
        load_suite_record(json.dumps(tampered))
    assert "digest" in str(getattr(excinfo.value, "reason", ""))

    binding_tampered = json.loads(dumped)
    binding_tampered["bindings"][0]["artifact_digest"] = "0" * 64
    with pytest.raises(Exception):  # noqa: B017 - CbtError
        load_suite_record(json.dumps(binding_tampered))


@pytest.mark.parametrize("seed", SEEDS)
def test_impact_sets_match_the_set_intersection_oracle(seed: int) -> None:
    """verifies: TOOL-CBT-020 — a case is affected exactly when its covered set
    intersects the change (independent oracle); the partition is exact."""
    rng = random.Random(seed)
    constructs = [f"src/f.c:{i}" for i in range(rng.randint(3, 15))]
    coverage = {
        f"tc.{i:02d}": frozenset(rng.sample(constructs, rng.randint(0, len(constructs))))
        for i in range(rng.randint(1, 8))
    }
    changed = set(rng.sample(constructs, rng.randint(0, len(constructs))))
    result = affected_cases(SourceChange(frozenset(changed)), coverage)

    oracle_affected = {test_id for test_id, covered in coverage.items() if set(covered) & changed}
    assert set(result.affected) == oracle_affected
    assert set(result.affected) | set(result.unaffected) == set(coverage)
    assert not (set(result.affected) & set(result.unaffected))
    assert result.affected == tuple(sorted(result.affected))


@pytest.mark.parametrize("seed", SEEDS)
def test_diff_constructs_carry_their_containing_function(seed: int) -> None:
    """verifies: TOOL-CBT-020 — under random extents, every changed line inside
    an extent maps to a construct and names that function; the answer is exact
    against an independently computed expectation."""
    rng = random.Random(seed)
    extents: dict[str, tuple[int, int]] = {}
    start = rng.randint(1, 5)
    for i in range(rng.randint(1, 4)):
        length = rng.randint(2, 8)
        name = _random_identifier(rng)
        if not name or name in extents:
            name = f"fn_{i}_{seed}"
        extents[name] = (start, start + length - 1)
        start += length + rng.randint(1, 4)  # gaps between functions

    chosen = sorted({rng.randint(1, start - 1) for _ in range(rng.randint(1, 6))})
    impact = changed_constructs(
        SourceDiff(
            path="src/f.c",
            old_digest="a" * 8,
            new_digest="b" * 8,
            ranges=tuple(LineRange(line, line) for line in chosen),
        ),
        extents,
    )

    inside = {line: name for name, (first, last) in extents.items() for line in chosen if first <= line <= last}
    expected_functions = tuple(sorted(set(inside.values())))
    expected_constructs = tuple(sorted(f"src/f.c:{line}" for line in inside))  # the mapper sorts lexically
    assert impact.functions == expected_functions
    assert impact.constructs == expected_constructs
    if len(inside) == len(chosen):
        assert impact.file_construct is None and impact.note is None
    else:
        assert impact.file_construct == "src/f.c" and impact.note == "lines_outside_extents"


def test_bindings_follow_their_case_ids_under_shuffling() -> None:
    """verifies: TOOL-CBT-010 — bindings are canonically ordered by test id,
    whatever order the cases arrived in (D-02)."""
    rng = random.Random(2026)
    cases = [_case(rng, i) for i in range(8)]
    shuffled = cases[:]
    rng.shuffle(shuffled)
    forward = bindings_from_cases(cases)
    backward = bindings_from_cases(shuffled)
    assert forward == backward
    assert [b.test_id for b in forward] == sorted(b.test_id for b in forward)
