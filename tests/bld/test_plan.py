"""Tests for the WP-BLD-01 incremental rebuild planner.

Covers: first-build-everything, up-to-date detection, exactly-affected
recompilation per changed dimension, reason recording, deterministic
ordering, duplicate output rejection, and purity of the plan.

Verifies: TOOL-EXE-080.
"""

from __future__ import annotations

import pytest

from ectt.bld import (
    REASON_CONFIG_CHANGED,
    REASON_FLAGS_CHANGED,
    REASON_NO_RECORD,
    REASON_SOURCE_CHANGED,
    ArtifactSpec,
    BuildRecord,
    DuplicateArtifactError,
    IncrementalPlanner,
    InvalidArtifactSpecError,
    RebuildDecision,
)

D1 = "a" * 64
D2 = "b" * 64


def _spec(
    name: str,
    *,
    digest: str = D1,
    compiler: str = "gcc",
    flags: tuple[str, ...] = ("-c", "-O0"),
) -> ArtifactSpec:
    return ArtifactSpec(
        output_path=f"build/{name}.o",
        source_path=f"src/{name}.c",
        source_digest=digest,
        compiler=compiler,
        flags=flags,
    )


def _record(spec: ArtifactSpec) -> BuildRecord:
    return BuildRecord(
        source_digest=spec.source_digest,
        compiler=spec.compiler,
        flags=spec.flags,
    )


def test_first_build_schedules_everything() -> None:
    """verifies: TOOL-EXE-080"""
    planner = IncrementalPlanner()
    decisions = planner.plan((_spec("a"), _spec("b")))
    assert all(d.rebuild for d in decisions)
    assert all(d.reasons == (REASON_NO_RECORD,) for d in decisions)


def test_unchanged_inputs_are_up_to_date() -> None:
    """verifies: TOOL-EXE-080"""
    spec = _spec("a")
    planner = IncrementalPlanner({"build/a.o": _record(spec)})
    decisions = planner.plan((spec,))
    assert len(decisions) == 1
    assert decisions[0].rebuild is False
    assert decisions[0].reasons == ()


def test_only_source_changed_artifact_recompiles() -> None:
    """verifies: TOOL-EXE-080"""
    changed = _spec("a", digest=D2)
    untouched = _spec("b")
    planner = IncrementalPlanner(
        {"build/a.o": _record(_spec("a")), "build/b.o": _record(untouched)}
    )
    decisions = planner.plan((changed, untouched))
    by_output = {d.spec.output_path: d for d in decisions}
    assert by_output["build/a.o"].rebuild is True
    assert by_output["build/a.o"].reasons == (REASON_SOURCE_CHANGED,)
    assert by_output["build/b.o"].rebuild is False


def test_only_flags_changed_artifact_recompiles() -> None:
    """verifies: TOOL-EXE-080"""
    changed = _spec("a", flags=("-c", "-O2"))
    planner = IncrementalPlanner({"build/a.o": _record(_spec("a"))})
    decisions = planner.plan((changed,))
    assert decisions[0].rebuild is True
    assert decisions[0].reasons == (REASON_FLAGS_CHANGED,)


def test_only_config_changed_artifact_recompiles() -> None:
    """verifies: TOOL-EXE-080"""
    changed = _spec("a", compiler="clang")
    planner = IncrementalPlanner({"build/a.o": _record(_spec("a"))})
    decisions = planner.plan((changed,))
    assert decisions[0].rebuild is True
    assert decisions[0].reasons == (REASON_CONFIG_CHANGED,)


def test_multiple_changes_accumulate_reasons() -> None:
    """verifies: TOOL-EXE-080"""
    changed = _spec("a", digest=D2, flags=("-c", "-g"))
    planner = IncrementalPlanner({"build/a.o": _record(_spec("a"))})
    decisions = planner.plan((changed,))
    assert decisions[0].reasons == (REASON_SOURCE_CHANGED, REASON_FLAGS_CHANGED)


def test_planning_output_is_deterministically_ordered() -> None:
    """verifies: TOOL-EXE-080"""
    planner = IncrementalPlanner()
    decisions = planner.plan((_spec("z"), _spec("a"), _spec("m")))
    assert [d.spec.output_path for d in decisions] == [
        "build/a.o",
        "build/m.o",
        "build/z.o",
    ]


def test_duplicate_output_path_rejected() -> None:
    """verifies: TOOL-EXE-080"""
    planner = IncrementalPlanner()
    first = _spec("a")
    second = ArtifactSpec(
        output_path=first.output_path,
        source_path="src/other.c",
        source_digest=D1,
        compiler="gcc",
        flags=(),
    )
    with pytest.raises(DuplicateArtifactError):
        planner.plan((first, second))


def test_blank_fields_rejected() -> None:
    """verifies: TOOL-EXE-080"""
    with pytest.raises(InvalidArtifactSpecError):
        ArtifactSpec(
            output_path="build/a.o",
            source_path="src/a.c",
            source_digest="",
            compiler="gcc",
            flags=(),
        )
    with pytest.raises(InvalidArtifactSpecError):
        ArtifactSpec(
            output_path="build/a.o",
            source_path="src/a.c",
            source_digest=D1,
            compiler="gcc",
            flags=("-c", "  "),
        )


def test_plan_is_a_pure_function() -> None:
    """verifies: TOOL-EXE-080"""
    specs = (_spec("a"), _spec("b"))
    planner_one = IncrementalPlanner({"build/a.o": _record(_spec("a"))})
    planner_two = IncrementalPlanner({"build/a.o": _record(_spec("a"))})
    first = planner_one.plan(specs)
    second = planner_two.plan(specs)
    assert [d.to_dict() for d in first] == [d.to_dict() for d in second]
    decisions: tuple[RebuildDecision, ...] = first
    assert [d.to_dict() for d in planner_one.plan(specs)] == [
        d.to_dict() for d in decisions
    ]


def test_recorded_builds_make_followup_plan_up_to_date() -> None:
    """verifies: TOOL-EXE-080"""
    planner = IncrementalPlanner()
    specs = (_spec("a"),)
    assert all(d.rebuild for d in planner.plan(specs))
    for decision in planner.plan(specs):
        planner.record(
            decision.spec.output_path,
            BuildRecord(
                source_digest=decision.spec.source_digest,
                compiler=decision.spec.compiler,
                flags=decision.spec.flags,
            ),
        )
    assert all(not d.rebuild for d in planner.plan(specs))
