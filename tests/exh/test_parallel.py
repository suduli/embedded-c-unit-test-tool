"""Tests for parallel test execution (WP-EXH-03).

Covers TOOL-EXE-050 and DSN-EXH-040 per docs/verification/WP-EXH-03-analysis.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from ectt.exh.errors import WrongAttemptStateError
from ectt.exh.results import ExecutionMetadata
from ectt.exh.runner import (
    ParallelUnit,
    allocate_attempt,
    exit_code_for_outcome,
    mark_built,
    record_build_failure,
    run_parallel,
)
from ectt.exh.runner import (
    TestBinding as ExhTestBinding,
)

DIGEST = "d" * 64

PLAIN_HARNESS = """\
import sys
print(f"RESULT {sys.argv[2]} pass")
open("cov.dat", "w").write("data")
"""

FAILING_HARNESS = """\
import sys
selected = sys.argv[2]
if selected == "u1":
    print(f"RESULT {selected} fail")
    print(f"FAILURE {selected} a b c f 1")
else:
    print(f"RESULT {selected} pass")
"""


def overlap_harness(shared_dir: Path) -> str:
    """Overlap probe: u0 sleeps then writes a done-marker to a shared dir; u1
    records whether that marker was still absent at its own start."""
    shared = shared_dir.as_posix()
    return f"""\
import os, sys, time
shared = {shared!r}
selected = sys.argv[2]
if selected == "u0":
    time.sleep(0.5)
    open(os.path.join(shared, "u0.done"), "w").write("done")
else:
    if not os.path.exists(os.path.join(shared, "u0.done")):
        open(os.path.join(shared, "overlap.marker"), "w").write("in-flight")
print(f"RESULT {{selected}} pass")
"""


def make_unit(script: Path, test_id: str, *, digests: dict | None = None) -> ParallelUnit:
    attempt = mark_built(
        allocate_attempt(
            ExecutionMetadata(where="host", toolchain="gcc-14.2"),
            [ExhTestBinding(test_id=test_id, artifact_digest=DIGEST)],
        )
    )
    return ParallelUnit(
        attempt=attempt,
        executable=script,
        current_digests=digests or {test_id: DIGEST},
    )


def run_units(tmp_path: Path, body: str, names: list[str], **kwargs: object) -> object:
    script = tmp_path / "harness_stub.py"
    script.write_text(body, encoding="utf-8", newline="\n")
    units = [make_unit(script, name) for name in names]
    kwargs.setdefault("argv_prefix", (sys.executable,))
    return run_parallel(
        units,
        concurrency=kwargs.pop("concurrency", 2),
        timeout_seconds=kwargs.pop("timeout_seconds", 5.0),
        **kwargs,
    )


# --- AC-1: concurrent at a configurable degree --------------------------------


def test_units_run_to_completion_in_input_order(tmp_path) -> None:
    names = ["u0", "u1", "u2", "u3"]
    parallel = run_units(tmp_path, PLAIN_HARNESS, names)
    assert parallel.outcome == "pass"
    assert [run.attempt.allocations[0].test_id for run in parallel.units] == names
    assert all(run.result_set.results[0].outcome == "pass" for run in parallel.units)


def test_units_overlap_at_degree_two(tmp_path) -> None:
    shared = tmp_path / "shared"
    shared.mkdir()
    parallel = run_units(tmp_path, overlap_harness(shared), ["u0", "u1"], concurrency=2)
    assert parallel.outcome == "pass"
    assert (shared / "overlap.marker").exists()  # u1 started before u0 finished


def test_low_degree_serializes_overlap(tmp_path) -> None:
    shared = tmp_path / "shared"
    shared.mkdir()
    parallel = run_units(tmp_path, overlap_harness(shared), ["u0", "u1"], concurrency=1)
    assert parallel.outcome == "pass"
    assert not (shared / "overlap.marker").exists()  # sequential: u0 done first


# --- AC-2: per-worker output directories --------------------------------------


def test_per_worker_directories_prevent_collisions(tmp_path) -> None:
    parallel = run_units(
        tmp_path,
        PLAIN_HARNESS,
        ["u0", "u1"],
        concurrency=2,
        worker_root=tmp_path / "workers",
    )
    assert parallel.outcome == "pass"
    worker0 = tmp_path / "workers" / "worker-0" / "cov.dat"
    worker1 = tmp_path / "workers" / "worker-1" / "cov.dat"
    assert worker0.exists() and worker1.exists()
    assert len(parallel.worker_dirs) == 2


# --- AC-3: aggregation and exit contract --------------------------------------


def test_parallel_aggregation_and_exit_code(tmp_path) -> None:
    parallel = run_units(tmp_path, FAILING_HARNESS, ["u0", "u1"])
    assert parallel.outcome == "failed"
    assert exit_code_for_outcome(parallel.outcome) == 1
    assert exit_code_for_outcome("pass") == 0
    assert exit_code_for_outcome("incomplete") == 1
    assert exit_code_for_outcome("build_failed") == 1


# --- AC-4: run integrity per unit ---------------------------------------------


def test_stale_unit_is_skipped_others_execute(tmp_path) -> None:
    script = tmp_path / "harness_stub.py"
    script.write_text(PLAIN_HARNESS, encoding="utf-8", newline="\n")
    stale_attempt = mark_built(
        allocate_attempt(
            ExecutionMetadata(where="host", toolchain="gcc-14.2"),
            [ExhTestBinding(test_id="u0", artifact_digest="a" * 64)],
        )
    )
    parallel = run_parallel(
        [
            ParallelUnit(stale_attempt, script, {"u0": "b" * 64}),
            make_unit(script, "u1"),
        ],
        concurrency=2,
        timeout_seconds=5.0,
        argv_prefix=(sys.executable,),
    )
    assert parallel.units[0].stale_ids == ("u0",)
    assert parallel.units[0].outcome == "incomplete"
    assert parallel.units[1].outcome == "pass"
    assert parallel.outcome == "incomplete"  # stale unit forces non-pass overall
    assert exit_code_for_outcome(parallel.outcome) == 1


def test_build_failed_unit_is_never_executed(tmp_path) -> None:
    script = tmp_path / "harness_stub.py"
    script.write_text(PLAIN_HARNESS, encoding="utf-8", newline="\n")
    failed = record_build_failure(
        allocate_attempt(
            ExecutionMetadata(where="host", toolchain="gcc-14.2"),
            [ExhTestBinding(test_id="u0", artifact_digest=DIGEST)],
        ),
        ["linker error"],
    )
    with pytest.raises(WrongAttemptStateError):
        run_parallel(
            [ParallelUnit(failed, script, {"u0": DIGEST})],
            concurrency=1,
            timeout_seconds=5.0,
        )


# --- AC-5: validation ----------------------------------------------------------


def test_concurrency_must_be_positive(tmp_path) -> None:
    script = tmp_path / "harness_stub.py"
    script.write_text(PLAIN_HARNESS, encoding="utf-8", newline="\n")
    with pytest.raises(ValueError, match="concurrency"):
        run_parallel(
            [make_unit(script, "u0")],
            concurrency=0,
            timeout_seconds=5.0,
        )
    with pytest.raises(ValueError, match="at least one unit"):
        run_parallel([], concurrency=2, timeout_seconds=5.0)
