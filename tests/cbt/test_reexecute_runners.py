# implements: TOOL-CBT-010
"""Re-execution through the isolated and parallel runners (WP-CBT-01 wiring).

The same record-integrity gate that guards ``reexecute_suite`` guards every
runner form: ``reexecute_isolated`` runs each test in its own harness process;
``reexecute_parallel`` re-executes independent recorded suites concurrently.
The gate runs for *all* specs before any process starts, so one bad suite
refuses the whole call without side effects.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.cbt import (
    CbtError,
    ParallelReExecution,
    ReExecutionSpec,
    bindings_from_cases,
    record_compiled_suite,
    reexecute_isolated,
    reexecute_parallel,
    reexecute_suite,
)
from ectt.exh.results import ExecutionMetadata
from ectt.tcm import datacases as dd

EXECUTION = ExecutionMetadata(where="host", toolchain="gcc-14.2")

ISOLATED_HARNESS = (
    "import sys\n"
    "args = sys.argv[1:]\n"
    "tid = args[args.index('--ectt-select') + 1] if '--ectt-select' in args else None\n"
    "if tid == 'tc.one' or tid is None:\n"
    "    print('RESULT tc.one pass')\n"
    "if tid == 'tc.two' or tid is None:\n"
    "    print('RESULT tc.two fail')\n"
    "    print('FAILURE tc.two expected_return 1 0 src/a.c 9')\n"
)

HANGING_HARNESS = (
    "import sys, time\n"
    "args = sys.argv[1:]\n"
    "tid = args[args.index('--ectt-select') + 1] if '--ectt-select' in args else None\n"
    "if tid == 'tc.one' or tid is None:\n"
    "    time.sleep(5)\n"
    "    print('RESULT tc.one pass')\n"
    "if tid == 'tc.two' or tid is None:\n"
    "    print('RESULT tc.two pass')\n"
)

PASSING_ISOLATED_HARNESS = (
    "import sys\n"
    "args = sys.argv[1:]\n"
    "tid = args[args.index('--ectt-select') + 1] if '--ectt-select' in args else None\n"
    "if tid == 'tc.one' or tid is None:\n"
    "    print('RESULT tc.one pass')\n"
    "if tid == 'tc.two' or tid is None:\n"
    "    print('RESULT tc.two pass')\n"
)

MARKER_HARNESS_PREFIX = "import sys\nopen(r'{marker}', 'w').write('ran')\n"


def _case(case_id: str, expected: str = "1") -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id=case_id,
            unit="src/a.c",
            function="f",
            inputs=dd.TestCaseInputs(),
            expected=dd.TestCaseExpected(return_value=expected),
            stubs=(),
        )
    )


CASES = [_case("tc.one"), _case("tc.two")]
CURRENT = {c.case_id: c.content_digest for c in CASES}


def _suite(tmp_path: Path, body: str, name: str = "harness") -> tuple[Path, Any]:
    """A project root with one recorded suite: the fake harness and its record."""
    root = tmp_path / f"proj-{name}"
    (root / "build").mkdir(parents=True)
    exe = root / "build" / name
    exe.write_text(body, encoding="utf-8")
    record = record_compiled_suite(root, f"build/{name}", EXECUTION, bindings_from_cases(CASES))
    return root, record


def test_reexecute_isolated_runs_each_test_in_its_own_process(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010, DSN-EXH-020 — one process per test, one crash
    costs one result, not the run."""
    root, record = _suite(tmp_path, ISOLATED_HARNESS)
    rexec = reexecute_isolated(
        record,
        root,
        CURRENT,
        run_label="iso",
        timeout_seconds=30,
        argv_prefix=(sys.executable,),
    )
    assert [r.test_id for r in rexec.run.result_set.results] == ["tc.one", "tc.two"]
    assert rexec.run.outcome == "failed"
    assert rexec.stale_test_ids == ()


def test_reexecute_isolated_shares_the_integrity_gate(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — a changed or missing binary is refused exactly
    as for the plain re-execution; runner choice cannot weaken integrity."""
    root, record = _suite(tmp_path, ISOLATED_HARNESS)
    (root / "build" / "harness").write_text("# rebuilt with different content\n", encoding="utf-8")
    with pytest.raises(CbtError) as changed:
        reexecute_isolated(record, root, CURRENT, run_label="iso", timeout_seconds=30)
    assert changed.value.reason == "executable_changed"

    (root / "build" / "harness").unlink()
    with pytest.raises(CbtError) as missing:
        reexecute_isolated(record, root, CURRENT, run_label="iso", timeout_seconds=30)
    assert missing.value.reason == "executable_missing"


def test_reexecute_isolated_reports_a_hang_as_a_timeout(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-040 — a test hanging past the timeout is killed and
    attributed a timeout record; it is neither pass nor fail."""
    root, record = _suite(tmp_path, HANGING_HARNESS)
    rexec = reexecute_isolated(
        record,
        root,
        CURRENT,
        run_label="iso",
        timeout_seconds=0.2,
        argv_prefix=(sys.executable,),
    )
    outcomes = {r.test_id: r.outcome for r in rexec.run.result_set.results}
    assert outcomes == {"tc.one": "timeout", "tc.two": "pass"}
    # A timeout is a finalized record (the test was attempted, not skipped),
    # so nothing is "not executed" — but the run cannot pass (TOOL-EXE-040).
    assert rexec.run.result_set.not_executed == ()
    assert rexec.run.outcome == "failed"


def test_reexecute_parallel_runs_independent_suites(tmp_path: Path) -> None:
    """verifies: TOOL-EXE-050 — two recorded suites re-execute concurrently and
    each keeps its own record id and outcome."""
    root_a, record_a = _suite(tmp_path, ISOLATED_HARNESS, "alpha")
    root_b, record_b = _suite(tmp_path, PASSING_ISOLATED_HARNESS, "beta")

    parallel = reexecute_parallel(
        [
            ReExecutionSpec(record=record_a, root=root_a, current=CURRENT, run_label="a1"),
            ReExecutionSpec(record=record_b, root=root_b, current=CURRENT, run_label="b1"),
        ],
        concurrency=2,
        timeout_seconds=30,
        argv_prefix=(sys.executable,),
    )

    assert isinstance(parallel, ParallelReExecution)
    assert parallel.outcome == "failed"  # alpha fails (tc.two), beta passes
    assert [rexec.record_id for rexec in parallel.reexecutions] == [record_a.record_id, record_b.record_id]
    assert [rexec.run.outcome for rexec in parallel.reexecutions] == ["failed", "pass"]


def test_reexecute_parallel_refuses_duplicate_run_labels(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — two specs with the same record and label would
    collide on the run id and are refused."""
    root, record = _suite(tmp_path, ISOLATED_HARNESS)
    spec = ReExecutionSpec(record=record, root=root, current=CURRENT, run_label="same")
    with pytest.raises(CbtError) as excinfo:
        reexecute_parallel([spec, spec], concurrency=2, timeout_seconds=30)
    assert excinfo.value.reason == "duplicate_run"


def test_reexecute_parallel_checks_every_suite_before_running_any(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — one tampered suite refuses the whole call and
    no suite runs at all (no partial side effects)."""
    marker = tmp_path / "marker.txt"
    root_a, record_a = _suite(
        tmp_path,
        MARKER_HARNESS_PREFIX.format(marker=marker) + "print('RESULT tc.one pass')\nprint('RESULT tc.two pass')\n",
        "alpha",
    )
    root_b, record_b = _suite(tmp_path, "print('RESULT tc.one pass')\nprint('RESULT tc.two pass')\n", "beta")
    (root_b / "build" / "beta").write_text("# tampered after the build\n", encoding="utf-8")

    with pytest.raises(CbtError) as excinfo:
        reexecute_parallel(
            [
                ReExecutionSpec(record=record_a, root=root_a, current=CURRENT, run_label="a1"),
                ReExecutionSpec(record=record_b, root=root_b, current=CURRENT, run_label="b1"),
            ],
            concurrency=2,
            timeout_seconds=30,
            argv_prefix=(sys.executable,),
        )

    assert excinfo.value.reason == "executable_changed"
    assert not marker.exists()  # the healthy suite was never started


def test_reexecute_parallel_requires_specs(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — an empty parallel re-execution is refused."""
    with pytest.raises(CbtError) as excinfo:
        reexecute_parallel([], concurrency=2, timeout_seconds=30)
    assert excinfo.value.reason == "no_specs"


def test_stale_tests_are_stale_through_every_runner(tmp_path: Path) -> None:
    """verifies: T-14 NR-19 — the binding check is the runner's own; a test
    edited since the build is stale in isolated and parallel forms alike."""
    root, record = _suite(tmp_path, ISOLATED_HARNESS)
    edited = dict(CURRENT)
    edited["tc.one"] = "0" * 64

    iso = reexecute_isolated(record, root, edited, run_label="iso", timeout_seconds=30, argv_prefix=(sys.executable,))
    assert iso.stale_test_ids == ("tc.one",)
    assert iso.run.result_set.partial is True

    par = reexecute_parallel(
        [ReExecutionSpec(record=record, root=root, current=edited, run_label="par")],
        concurrency=1,
        timeout_seconds=30,
        argv_prefix=(sys.executable,),
    )
    assert par.reexecutions[0].stale_test_ids == ("tc.one",)
    assert par.reexecutions[0].run.result_set.partial is True


def test_run_labels_stay_single_tokens_through_the_new_forms(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — run-label rules apply to the runner forms too."""
    root, record = _suite(tmp_path, ISOLATED_HARNESS)
    with pytest.raises(CbtError) as excinfo:
        reexecute_isolated(record, root, CURRENT, run_label="two words", timeout_seconds=30)
    assert excinfo.value.reason == "invalid_run_label"
    with pytest.raises(CbtError) as excinfo:
        reexecute_parallel(
            [ReExecutionSpec(record=record, root=root, current=CURRENT, run_label="")],
            concurrency=1,
            timeout_seconds=30,
        )
    assert excinfo.value.reason == "invalid_run_label"


def test_plain_reexecution_still_works_after_the_refactor(tmp_path: Path) -> None:
    """verifies: TOOL-CBT-010 — the original single-process form is unchanged."""
    root, record = _suite(tmp_path, ISOLATED_HARNESS)
    rexec = reexecute_suite(record, root, CURRENT, run_label="plain", argv_prefix=(sys.executable,))
    assert rexec.run.outcome == "failed"
    assert len(rexec.run.result_set.results) == 2
