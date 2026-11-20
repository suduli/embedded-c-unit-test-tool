"""Tests for host execution and per-test result reporting (WP-EXH-01).

Covers TOOL-EXE-010 (execute half), TOOL-EXE-020, and the T-14 run-integrity
acceptance (NR-17/18/19) with D-02 digest binding, per
docs/verification/WP-EXH-01-analysis.md.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.exh.errors import (
    DuplicateTestResultError,
    ExecutableMissingError,
    InvalidAllocationError,
    InvalidResultRecordError,
    MalformedResultStreamError,
    UnknownTestResultError,
    WrongAttemptStateError,
)
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultRecord,
    SourceLocation,
    aggregate_outcome,
    dump_result_set,
    finalize_result,
)
from ectt.exh.runner import (
    RunAttempt,
    allocate_attempt,
    build_failed_run,
    check_test_bindings,
    mark_built,
    record_build_failure,
    run_harness,
)
from ectt.exh.runner import (
    TestBinding as ExhTestBinding,
)

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64

HARNESS_ALL_PASS = """\
import sys
print("framework banner noise")
print("RESULT tc.one pass")
print("RESULT tc.two pass")
sys.exit(0)
"""

HARNESS_ONE_FAIL = """\
import sys
print("RESULT tc.one pass")
print("RESULT tc.two fail")
print("FAILURE tc.two expected_return 4095 0 src/a.c 88")
sys.exit(1)
"""


def write_harness(tmp_path: Path, body: str) -> Path:
    script = tmp_path / "harness_stub.py"
    script.write_text(body, encoding="utf-8", newline="\n")
    return script


def make_attempt() -> RunAttempt:
    return allocate_attempt(
        ExecutionMetadata(where="host", toolchain="gcc-14.2"),
        [
            ExhTestBinding(test_id="tc.one", artifact_digest=DIGEST_A),
            ExhTestBinding(test_id="tc.two", artifact_digest=DIGEST_B),
        ],
    )


def run_stub(tmp_path: Path, body: str, **kwargs: Any) -> Any:
    attempt = mark_built(make_attempt())
    digests = {"tc.one": DIGEST_A, "tc.two": DIGEST_B}
    digests.update(kwargs.pop("digests", {}))
    return run_harness(
        attempt,
        write_harness(tmp_path, body),
        current_digests=digests,
        argv_prefix=(sys.executable,),
        **kwargs,
    )


# --- AC-1: execute half ------------------------------------------------------


def test_happy_path_reports_one_record_per_result_line(tmp_path) -> None:
    executed = run_stub(tmp_path, HARNESS_ALL_PASS)
    assert executed.outcome == "pass"
    assert executed.stale_ids == ()
    assert len(executed.result_set.results) == 2
    assert [record.test_id for record in executed.result_set.results] == ["tc.one", "tc.two"]
    assert all(record.outcome == "pass" for record in executed.result_set.results)
    assert executed.result_set.partial is False
    assert executed.result_set.not_executed == ()


def test_missing_executable_raises_named_error(tmp_path) -> None:
    attempt = mark_built(make_attempt())
    with pytest.raises(ExecutableMissingError):
        run_harness(
            attempt,
            tmp_path / "no_such_harness.bin",
            current_digests={"tc.one": DIGEST_A, "tc.two": DIGEST_B},
        )


# --- AC-2: per-test reporting ------------------------------------------------


def test_fail_record_carries_assertion_expected_actual_location(tmp_path) -> None:
    executed = run_stub(tmp_path, HARNESS_ONE_FAIL)
    assert executed.outcome == "failed"
    failing = executed.result_set.results[1]
    assert failing.test_id == "tc.two"
    assert failing.outcome == "fail"
    assert len(failing.failures) == 1
    failure = failing.failures[0]
    assert failure.assertion == "expected_return"
    assert failure.expected == "4095"
    assert failure.actual == "0"
    assert failure.location.file == "src/a.c"
    assert failure.location.line == 88


def test_pass_record_carries_no_failures(tmp_path) -> None:
    executed = run_stub(tmp_path, HARNESS_ALL_PASS)
    assert all(record.failures == () for record in executed.result_set.results)


def test_unknown_test_result_is_rejected(tmp_path) -> None:
    with pytest.raises(UnknownTestResultError, match=r"tc\.ghost"):
        run_stub(tmp_path, "import sys\nprint('RESULT tc.ghost pass')\n")


def test_duplicate_result_is_rejected(tmp_path) -> None:
    body = "import sys\nprint('RESULT tc.one pass')\nprint('RESULT tc.one pass')\n"
    with pytest.raises(DuplicateTestResultError, match=r"tc\.one"):
        run_stub(tmp_path, body)


@pytest.mark.parametrize(
    ("body", "error"),
    [
        ("import sys\nprint('RESULT tc.one')\n", MalformedResultStreamError),
        ("import sys\nprint('RESULT tc.one bloomed')\n", MalformedResultStreamError),
        ("import sys\nprint('FAILURE tc.one a b c f 1')\n", MalformedResultStreamError),
        ("import sys\nprint('RESULT tc.one fail')\n", InvalidResultRecordError),
        ("import sys\nprint('RESULT tc.one pass')\nprint('FAILURE tc.one a b c f 1')\n", MalformedResultStreamError),
    ],
)
def test_malformed_stream_is_rejected(tmp_path, body: str, error: type) -> None:
    with pytest.raises(error):
        run_stub(tmp_path, body)


# --- AC-3: NR-17 attempt lifecycle -------------------------------------------


def test_attempt_is_allocated_before_build_with_allocations() -> None:
    attempt = make_attempt()
    assert attempt.status == "allocated"
    assert [binding.test_id for binding in attempt.allocations] == ["tc.one", "tc.two"]
    assert attempt.attempt_id
    twin = make_attempt()
    assert twin.attempt_id == attempt.attempt_id  # deterministic, content-derived


def test_allocation_validation() -> None:
    execution = ExecutionMetadata(where="host", toolchain="gcc-14.2")
    with pytest.raises(InvalidAllocationError):
        allocate_attempt(execution, [])
    with pytest.raises(InvalidAllocationError, match="more than once"):
        allocate_attempt(
            execution,
            [ExhTestBinding("tc.one", DIGEST_A), ExhTestBinding("tc.one", DIGEST_A)],
        )
    with pytest.raises(InvalidAllocationError, match="digest"):
        allocate_attempt(execution, [ExhTestBinding("tc.one", "  ")])


def test_build_failure_is_first_class_attempt_record() -> None:
    attempt = record_build_failure(make_attempt(), ["error: undefined reference to hal_read"])
    assert attempt.status == "build_failed"
    assert attempt.build_diagnostics == ("error: undefined reference to hal_read",)
    executed = build_failed_run(attempt)
    assert executed.outcome == "build_failed"
    assert executed.result_set.results == ()
    assert executed.result_set.partial is True
    assert executed.result_set.not_executed == ("tc.one", "tc.two")
    with pytest.raises(WrongAttemptStateError, match="never executes"):
        run_harness(
            attempt,
            Path("irrelevant"),
            current_digests={"tc.one": DIGEST_A, "tc.two": DIGEST_B},
        )


# --- AC-4: NR-18 finalized records decide ------------------------------------


def test_pass_aggregation_requires_finalized_records_for_every_allocation() -> None:
    records: dict[str, ResultRecord] = {
        "tc.one": finalize_result("tc.one", "pass", DIGEST_A),
        "tc.two": finalize_result("tc.two", "pass", DIGEST_B),
    }
    assert aggregate_outcome(records, ["tc.one", "tc.two"]) == "pass"
    del records["tc.two"]
    assert aggregate_outcome(records, ["tc.one", "tc.two"]) == "incomplete"
    records["tc.two"] = finalize_result("tc.two", "fail", DIGEST_B,
                                        failures=(AssertionFailure("expected_return", "4095", "0",
                                                                   SourceLocation("src/a.c", 88)),))
    assert aggregate_outcome(records, ["tc.one", "tc.two"]) == "failed"


def test_record_invariants_are_enforced() -> None:
    with pytest.raises(InvalidResultRecordError, match="digest"):
        finalize_result("tc.one", "pass", "")
    with pytest.raises(InvalidResultRecordError, match="unknown outcome"):
        finalize_result("tc.one", "bloomed", DIGEST_A)
    with pytest.raises(InvalidResultRecordError, match="carries failures"):
        finalize_result(
            "tc.one", "pass", DIGEST_A,
            failures=(AssertionFailure("a", "1", "2", SourceLocation("f", 1)),),
        )
    with pytest.raises(InvalidResultRecordError, match="names no assertion"):
        finalize_result("tc.one", "fail", DIGEST_A)
    with pytest.raises(InvalidResultRecordError, match="source file"):
        finalize_result(
            "tc.one", "fail", DIGEST_A,
            failures=(AssertionFailure("a", "1", "2", SourceLocation("", 0)),),
        )


def test_exit_status_is_never_consulted_for_outcome(tmp_path) -> None:
    # exit(0) alone is abnormal: an all-pass stream decides pass, exit(1) with
    # an all-pass stream still passes; the exit status is never consulted.
    executed = run_stub(tmp_path, HARNESS_ALL_PASS)
    assert executed.outcome == "pass"
    body = "import sys\nprint('RESULT tc.one pass')\nprint('RESULT tc.two pass')\nsys.exit(1)\n"
    executed = run_stub(tmp_path, body)
    assert executed.outcome == "pass"


# --- AC-5: NR-19 binding check before every run ------------------------------


def test_stale_binding_rejects_results_and_reports_not_executed(tmp_path) -> None:
    # the artifact was built from DIGEST_B, but tc.two's content has moved on;
    # its result is rejected as stale evidence, never accepted as current.
    executed = run_stub(
        tmp_path,
        HARNESS_ALL_PASS,
        digests={"tc.two": "c" * 64},
    )
    assert executed.stale_ids == ("tc.two",)
    assert [record.test_id for record in executed.result_set.results] == ["tc.one"]
    assert executed.result_set.not_executed == ("tc.two",)
    assert executed.result_set.partial is True
    assert executed.outcome == "incomplete"


def test_check_test_bindings_is_callable_standalone() -> None:
    binding = check_test_bindings(make_attempt(), {"tc.one": DIGEST_A, "tc.two": "c" * 64})
    assert binding.bound == ("tc.one",)
    assert binding.stale == ("tc.two",)


# --- AC-6: partial / not_executed travel with the data -----------------------


def test_missing_results_mark_run_partial(tmp_path) -> None:
    executed = run_stub(tmp_path, "import sys\nprint('RESULT tc.one pass')\n")
    assert executed.result_set.not_executed == ("tc.two",)
    assert executed.result_set.partial is True
    assert executed.outcome == "incomplete"


# --- AC-7: deterministic canonical JSON, no wall-clock -----------------------


def test_result_set_dump_is_deterministic_canonical_json(tmp_path) -> None:
    executed = run_stub(tmp_path, HARNESS_ONE_FAIL)
    one = dump_result_set(executed.result_set)
    two = dump_result_set(executed.result_set)
    assert one == two
    assert one.startswith('{\n  "schema_version": "1.0"')
    assert "duration_ms" not in one
    assert "generated_at" not in one
