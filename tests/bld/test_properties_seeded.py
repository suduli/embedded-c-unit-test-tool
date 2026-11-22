# implements: TOOL-EXE-080
"""Seeded property-style tests for ectt.bld planning (A7, tests only; no src/ edits).

Property: **planning order independence** — the incremental planner's decision set
is a pure function of (specs, records): shuffling the order in which specs are
requested or records were recorded never changes the decisions, their reasons or
their deterministic serialisation. Inputs come from ``random.Random(seed)`` with
fixed seeds (the seed is the test id); no wall clock anywhere.
"""

from __future__ import annotations

import random

import pytest

from ectt.bld import ArtifactSpec, BuildRecord, IncrementalPlanner

SEEDS = [0, 1, 7, 42, 1337]


def _specs(rng: random.Random, count: int) -> tuple[ArtifactSpec, ...]:
    return tuple(
        ArtifactSpec(
            output_path=f"out/obj_{index}.o",
            source_path=f"src/unit_{rng.randint(0, 5)}.c",
            source_digest=f"{rng.getrandbits(64):016x}",
            compiler=rng.choice(("gcc-14.2", "clang-18")),
            flags=(rng.choice(("-O2", "-O0")), rng.choice(("-g", "-DNDEBUG"))),
        )
        for index in range(count)
    )


@pytest.mark.parametrize("seed", SEEDS)
def test_planning_is_independent_of_request_and_record_order(seed: int) -> None:
    """verifies: TOOL-EXE-080 — shuffled specs and shuffled record insertion
    give the identical decision set."""
    rng = random.Random(seed)
    specs = _specs(rng, rng.randint(3, 8))
    # Record a random subset of the specs as prior builds (with drift).
    prior = list(specs[: rng.randint(0, len(specs))])
    records: dict[str, BuildRecord] = {}
    for spec in prior:
        drift = rng.random() < 0.4
        records[spec.output_path] = BuildRecord(
            source_digest=spec.source_digest if not drift else f"{rng.getrandbits(64):016x}",
            compiler=spec.compiler,
            flags=spec.flags if rng.random() >= 0.2 else ("-O3",),
        )

    def decide(spectuple: tuple[ArtifactSpec, ...], record_items: list[tuple[str, BuildRecord]]) -> list[dict]:
        planner = IncrementalPlanner(dict(record_items))
        rng.shuffle(spectuple_list := list(spectuple))
        rng.shuffle(record_items)
        return [d.to_dict() for d in planner.plan(tuple(spectuple_list))]

    first = decide(specs, list(records.items()))
    second = decide(tuple(reversed(specs)), list(reversed(list(records.items()))))
    assert first == second
    # Reasons travel with every decision, and the order is by output path.
    assert [d["spec"]["output_path"] for d in first] == sorted(d["spec"]["output_path"] for d in first)
    for decision in first:
        if decision["rebuild"]:
            assert decision["reasons"], "a rebuild decision names its reasons"


@pytest.mark.parametrize("seed", SEEDS)
def test_unchanged_records_make_followup_plans_up_to_date(seed: int) -> None:
    """verifies: TOOL-EXE-080 — recording a build makes the next plan up to
    date for exactly the artifacts whose inputs did not change."""
    rng = random.Random(seed)
    specs = _specs(rng, rng.randint(2, 6))
    planner = IncrementalPlanner()
    assert all(d.rebuild for d in planner.plan(specs))
    # Record every build as-is, then re-plan: nothing is scheduled.
    for spec in specs:
        planner.record(spec.output_path, BuildRecord(spec.source_digest, spec.compiler, spec.flags))
    assert all(not d.rebuild for d in planner.plan(specs))
    # Change one dimension of one artifact: exactly that one is scheduled.
    victim = rng.choice(specs)
    edited = ArtifactSpec(
        output_path=victim.output_path,
        source_path=victim.source_path,
        source_digest=f"{rng.getrandbits(64):016x}",
        compiler=victim.compiler,
        flags=victim.flags,
    )
    replan = planner.plan(tuple(edited if s.output_path == victim.output_path else s for s in specs))
    scheduled = [d.spec.output_path for d in replan if d.rebuild]
    assert scheduled == [victim.output_path]
    assert "source_changed" in next(d.reasons for d in replan if d.spec.output_path == victim.output_path)
