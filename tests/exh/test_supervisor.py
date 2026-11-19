"""Tests for crash isolation, timeout, and exit status (WP-EXH-02).

Covers TOOL-EXE-030, TOOL-EXE-040, TOOL-EXE-060 per
docs/verification/WP-EXH-02-analysis.md, including the board acceptance
criterion: a test that aborts, one that hangs past the timeout, and (through
the same no-RESULT attribution path) a segfault-style silent crash are each
attributed while the remaining cases still execute.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.exh.errors import (
    ExecutableMissingError,
    MalformedResultStreamError,
    UnknownTestResultError,
    WrongAttemptStateError,
)
from ectt.exh.results import ExecutionMetadata
from ectt.exh.runner import (
    TestBinding as ExhTestBinding,
)
from ectt.exh.runner import (
    allocate_attempt,
    build_failed_run,
    exit_code,
    mark_built,
    record_build_failure,
    run_isolated,
)

DIGEST = "d" * 64

# The stub harness selects one test per process (--ectt-select) and exhibits
# the fault mode that the selected test name asks for: a genuine C-level
# abort() (os.abort), a hang past any timeout, a silent non-zero exit (the
# segfault-class path: no protocol output), and a pass otherwise.
ISOLATED_HARNESS = """\
import os, sys
assert sys.argv[1] == "--ectt-select"
selected = sys.argv[2]
if selected == "tc.abort":
    os.abort()
elif selected == "tc.segv":
    os._exit(2)
elif selected == "tc.hang":
    import time
    time.sleep(30)
else:
    print(f"RESULT {selected} pass")
"""

TESTS = ["tc.abort", "tc.segv", "tc.hang", "tc.ok"]


def make_attempt() -> Any:
    return allocate_attempt(
        ExecutionMetadata(where="host", toolchain="gcc-14.2"),
        [ExhTestBinding(test_id, DIGEST) for test_id in TESTS],
    )


def run_isolated_stub(tmp_path: Path, body: str = ISOLATED_HARNESS, **kwargs: Any) -> Any:
    attempt = mark_built(make_attempt())
    script = tmp_path / "harness_stub.py"
    script.write_text(body, encoding="utf-8", newline="\n")
    digests = dict.fromkeys(TESTS, DIGEST)
    digests.update(kwargs.pop("digests", {}))
    return run_isolated(
        attempt,
        script,
        current_digests=digests,
        timeout_seconds=kwargs.pop("timeout_seconds", 2.0),
        argv_prefix=(sys.executable,),
        **kwargs,
    )


def by_id(executed: Any) -> dict[str, Any]:
    return {record.test_id: record for record in executed.result_set.results}


# --- board acceptance criterion ----------------------------------------------


def test_crash_attributed_and_remaining_cases_still_execute(tmp_path) -> None:
    executed = run_isolated_stub(tmp_path, timeout_seconds=2.0)
    records = by_id(executed)
    # abort() and the silent-crash path: attributed, not pass
    assert records["tc.abort"].outcome == "error"
    assert records["tc.abort"].failures == ()
    assert records["tc.segv"].outcome == "error"
    # the remaining cases still executed
    assert records["tc.ok"].outcome == "pass"
    # a crash costs one result, not the run: every allocated case has a record
    assert executed.outcome == "failed"  # error records make it failed
    assert executed.result_set.not_executed == ()
    assert executed.result_set.partial is False


def test_timeout_is_distinct_outcome_and_run_continues(tmp_path) -> None:
    executed = run_isolated_stub(tmp_path, timeout_seconds=0.5)
    records = by_id(executed)
    hang = records["tc.hang"]
    assert hang.outcome == "timeout"  # neither pass nor fail (RV-02 F-11)
    assert hang.failures == ()
    assert records["tc.ok"].outcome == "pass"
    assert executed.outcome == "failed"
    # a timed-out test is not missing: it has a finalized record
    assert "tc.hang" not in executed.result_set.not_executed
    assert executed.result_set.not_executed == ()


# --- TOOL-EXE-060: exit-code contract ----------------------------------------


ALL_PASS_BODY = """\
import sys
assert sys.argv[1] == "--ectt-select"
print(f"RESULT {sys.argv[2]} pass")
"""


def test_exit_code_contract(tmp_path) -> None:
    # timeout present -> non-zero
    executed = run_isolated_stub(tmp_path, timeout_seconds=0.5)
    assert exit_code(executed) == 1
    # every test passes -> exit code 0
    executed = run_isolated_stub(tmp_path, ALL_PASS_BODY, timeout_seconds=2.0)
    assert exit_code(executed) == 0
    assert executed.outcome == "pass"
    # a failing test -> non-zero
    fail_body = ISOLATED_HARNESS.replace(
        "os.abort()",
        "print('RESULT tc.abort fail'); print('FAILURE tc.abort a b c f 1')",
    )
    executed = run_isolated_stub(tmp_path, fail_body, timeout_seconds=0.5)
    assert exit_code(executed) == 1
    # build-failed is non-zero as well
    attempt = record_build_failure(make_attempt(), ["linker error"])
    assert exit_code(build_failed_run(attempt)) == 1


# --- run integrity under isolation (T-14) ------------------------------------


def test_isolated_run_respects_stale_binding(tmp_path) -> None:
    executed = run_isolated_stub(
        tmp_path,
        timeout_seconds=2.0,
        digests={"tc.ok": "e" * 64},
    )
    assert executed.stale_ids == ("tc.ok",)
    assert "tc.ok" in executed.result_set.not_executed
    assert all(record.test_id != "tc.ok" for record in executed.result_set.results)
    assert executed.outcome == "incomplete"


def test_build_failed_attempt_never_executes(tmp_path) -> None:
    attempt = record_build_failure(make_attempt(), ["error: no rule to make target"])
    with pytest.raises(WrongAttemptStateError, match="never executes"):
        run_isolated(
            attempt,
            tmp_path / "unused.py",
            current_digests=dict.fromkeys(TESTS, DIGEST),
            timeout_seconds=2.0,
        )


def test_allocated_state_is_refused(tmp_path) -> None:
    attempt = make_attempt()  # never marked built
    script = tmp_path / "harness_stub.py"
    script.write_text(ISOLATED_HARNESS, encoding="utf-8")
    with pytest.raises(WrongAttemptStateError, match="not 'built'"):
        run_isolated(
            attempt,
            script,
            current_digests=dict.fromkeys(TESTS, DIGEST),
            timeout_seconds=2.0,
            argv_prefix=(sys.executable,),
        )


# --- protocol discipline still surfaces under isolation ----------------------


def test_protocol_violation_still_surfaces_under_isolation(tmp_path) -> None:
    body = ISOLATED_HARNESS.replace(
        "os.abort()",
        "print('RESULT tc.other pass')",
    )
    with pytest.raises(UnknownTestResultError):
        run_isolated_stub(tmp_path, body, timeout_seconds=2.0)
    malformed = ISOLATED_HARNESS.replace(
        "os.abort()",
        "print('RESULT tc.abort pass'); print('FAILURE tc.abort a b c f 1')",
    )
    with pytest.raises(MalformedResultStreamError):
        run_isolated_stub(tmp_path, malformed, timeout_seconds=2.0)


def test_missing_executable_raises_named_error(tmp_path) -> None:
    attempt = mark_built(make_attempt())
    with pytest.raises(ExecutableMissingError):
        run_isolated(
            attempt,
            tmp_path / "no_such_harness.bin",
            current_digests=dict.fromkeys(TESTS, DIGEST),
            timeout_seconds=2.0,
        )


def test_nonpositive_timeout_is_rejected(tmp_path) -> None:
    attempt = mark_built(make_attempt())
    script = tmp_path / "harness_stub.py"
    script.write_text(ISOLATED_HARNESS, encoding="utf-8")
    with pytest.raises(ValueError, match="timeout_seconds"):
        run_isolated(
            attempt,
            script,
            current_digests=dict.fromkeys(TESTS, DIGEST),
            timeout_seconds=0,
            argv_prefix=(sys.executable,),
        )
