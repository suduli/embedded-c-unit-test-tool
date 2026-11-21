# implements: TOOL-MIG-010
"""Execution of existing Unity and cmocka suites (WP-MIG-01).

Equivalence partitioning over the frameworks' native output grammars, plus
end-to-end runs of interpreter-hosted suite stubs: the suite's own main runs
unrewritten and its stdout is the only thing the adapter reads.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.exh.results import ResultRecord
from ectt.mig.errors import MigError
from ectt.mig.existing_suites import (
    SUPPORTED_FRAMEWORKS,
    parse_cmocka_output,
    parse_unity_output,
    run_existing_suite,
)

# --- Unity grammar partitions ----------------------------------------------------------


def test_unity_pass_ignore_and_detailed_fail() -> None:
    records, unrecognised = parse_unity_output(
        "test_adc.c:12:test_read:PASS\n"
        "test_adc.c:20:test_range:FAIL: Expected 0 Was 42\n"
        "test_adc.c:30:test_off:IGNORE\n"
    )

    by_id = {r.test_id: r for r in records}
    assert by_id["test_read"].outcome == "pass"
    assert by_id["test_off"].outcome == "not_run"
    fail = by_id["test_range"]
    assert fail.outcome == "fail"
    assert fail.failures[0].expected == "0"
    assert fail.failures[0].actual == "42"
    assert fail.failures[0].location.file == "test_adc.c"
    assert fail.failures[0].location.line == 20
    assert unrecognised == ()


def test_unity_fail_without_detail_becomes_error_not_an_upgraded_claim() -> None:
    records, _ = parse_unity_output("test_adc.c:9:test_bare:FAIL\n")

    assert records[0].outcome == "error"  # NR-18 forbids a fail record without expected/actual
    assert records[0].failures == ()


def test_unity_unrecognised_lines_are_reported() -> None:
    records, unrecognised = parse_unity_output("test.c:1:t:PASS\nSOME BANNER\ntest.c:2:u:PASS\n")

    assert len(records) == 2
    assert unrecognised == ("SOME BANNER",)


# --- cmocka grammar partitions ---------------------------------------------------------


def test_cmocka_okay_and_failed_become_pass_and_error() -> None:
    records, unrecognised = parse_cmocka_output(
        "[ RUN      ] reads_channel\n"
        "[   LINE   ] test_adc.c:9: error: Failure!\n"
        "[  FAILED  ] reads_channel\n"
        "[ RUN      ] calibrates\n"
        "[  OKAY    ] calibrates\n"
        "[  PASSED  ] 1 test(s).\n"
    )

    by_id = {r.test_id: r for r in records}
    assert by_id["calibrates"].outcome == "pass"
    assert by_id["reads_channel"].outcome == "error"  # stream carries no expected/actual
    assert {"[   LINE   ] test_adc.c:9: error: Failure!", "[  PASSED  ] 1 test(s)."} <= set(unrecognised)


def test_both_parsers_are_deterministic() -> None:
    unity_text = "t.c:1:a:PASS\nt.c:2:b:FAIL: Expected 1 Was 2\n"
    cmocka_text = "[ RUN      ] x\n[  OKAY    ] x\n"

    assert parse_unity_output(unity_text) == parse_unity_output(unity_text)
    assert parse_cmocka_output(cmocka_text) == parse_cmocka_output(cmocka_text)


def test_records_satisfy_the_s3_vocabulary_and_nr18() -> None:
    records, _ = parse_unity_output(
        "t.c:1:a:PASS\nt.c:2:b:FAIL: Expected 1 Was 2\nt.c:3:c:IGNORE\n"
    )

    for record in records:
        assert record.outcome in ("pass", "fail", "error", "timeout", "not_run")
        assert record.test_digest  # every record carries an identity digest (D-02)
        if record.outcome == "fail":
            assert record.failures


# --- execution ------------------------------------------------------------------------


def _stub_suite(tmp_path: Path, output: str) -> tuple[Path, list[str]]:
    script = tmp_path / "suite_stub.py"
    script.write_text(f"import sys\nprint({output!r})\n", encoding="utf-8")
    return script, [sys.executable]


def test_run_existing_suite_aggregates_the_framework_result(tmp_path: Path) -> None:
    script, prefix = _stub_suite(
        tmp_path,
        "t.c:1:passing:PASS\nt.c:2:broken:FAIL: Expected 0 Was 7\n",
    )

    run = run_existing_suite(script, "unity", argv_prefix=prefix)

    assert run.aggregate == "failed"
    statuses = {r.test_id: r.outcome for r in run.records}
    assert statuses == {"passing": "pass", "broken": "fail"}


def test_all_pass_aggregate_is_pass(tmp_path: Path) -> None:
    script, prefix = _stub_suite(tmp_path, "t.c:1:only:PASS\n")

    run = run_existing_suite(script, "unity", argv_prefix=prefix)

    assert run.aggregate == "pass"


def test_silent_suite_is_never_a_silent_pass(tmp_path: Path) -> None:
    script, prefix = _stub_suite(tmp_path, "crashed before printing anything")

    run = run_existing_suite(script, "unity", argv_prefix=prefix)

    assert run.records == ()
    assert run.aggregate is None  # never inferred from an empty stream
    assert run.unrecognised_lines == ("crashed before printing anything",)


def test_exit_status_is_never_consulted(tmp_path: Path) -> None:
    """A failing exit status with passing output is still a passing run."""
    script = tmp_path / "suite_stub.py"
    script.write_text(
        "import sys\nprint('t.c:1:only:PASS')\nsys.exit(3)\n", encoding="utf-8"
    )

    run = run_existing_suite(script, "unity", argv_prefix=[sys.executable])

    assert run.aggregate == "pass"


def test_unsupported_framework_and_missing_executable_are_refused(tmp_path: Path) -> None:
    with pytest.raises(MigError) as excinfo:
        run_existing_suite(tmp_path / "x", "googletest")
    assert excinfo.value.reason == "unsupported_framework"

    with pytest.raises(MigError) as excinfo:
        run_existing_suite(tmp_path / "missing.exe", "unity")
    assert excinfo.value.reason == "executable_missing"


def test_supported_frameworks_match_the_generator_backends() -> None:
    """The same two frameworks the generator emits for (WP-GEN-02 ids)."""
    from ectt.gen.backends import CMOCKA_BACKEND_ID, UNITY_BACKEND_ID

    assert SUPPORTED_FRAMEWORKS == (CMOCKA_BACKEND_ID, UNITY_BACKEND_ID) == ("cmocka", "unity")


def test_run_is_deterministic(tmp_path: Path) -> None:
    script, prefix = _stub_suite(tmp_path, "t.c:1:a:PASS\nt.c:2:b:FAIL: Expected 1 Was 2\n")

    first: Any = run_existing_suite(script, "unity", argv_prefix=prefix)
    second: Any = run_existing_suite(script, "unity", argv_prefix=prefix)

    assert first.records == second.records
    assert first.aggregate == second.aggregate


def test_record_type_is_the_shared_finalized_record() -> None:
    """The normalised records are exh's finalized records, not a new model."""
    records, _ = parse_unity_output("t.c:1:a:PASS\n")

    assert isinstance(records[0], ResultRecord)


def test_real_cmocka_ok_spelling_is_a_pass() -> None:
    """Regression: cmocka itself prints ``[       OK ]``; only ``OKAY`` was recognised before."""
    records, context = parse_cmocka_output(
        "[==========] tests: Running 2 test(s).\n"
        "[ RUN      ] reads_channel\n"
        "[       OK ] reads_channel\n"
        "[ RUN      ] calibrates\n"
        "[  FAILED  ] calibrates\n"
    )

    assert {r.test_id: r.outcome for r in records} == {"reads_channel": "pass", "calibrates": "error"}
    assert all("OK" not in line for line in context if line.startswith("[       OK"))
    assert "[       OK ] reads_channel" not in context


# --- review-fix regressions --------------------------------------------------------------


def test_unity_windows_drive_letter_path_is_recognised() -> None:
    """Regression: a Windows ``__FILE__`` such as a drive-letter path contains a colon."""
    records, unrecognised = parse_unity_output(
        "C:" + chr(92) + "proj" + chr(92) + "test_a.c:12:test_x:PASS\n"
        "C:/proj/test_a.c:20:test_y:FAIL: Expected 1 Was 2\n"
    )

    assert {r.test_id: r.outcome for r in records} == {"test_x": "pass", "test_y": "fail"}
    assert records[1].failures[0].location.file == "C:/proj/test_a.c"
    assert unrecognised == ()


def test_repeated_test_name_cannot_mask_an_earlier_failure(tmp_path: Path) -> None:
    script, prefix = _stub_suite(tmp_path, "a.c:1:test_x:FAIL: Expected 1 Was 2\nb.c:1:test_x:PASS\n")

    run = run_existing_suite(script, "unity", argv_prefix=prefix)

    assert len(run.records) == 2
    assert run.aggregate == "failed"


def test_cmocka_test_started_but_never_finished_is_an_error_not_a_pass(tmp_path: Path) -> None:
    """A crash after ``[ RUN ]`` leaves no verdict line; the run must not aggregate to pass."""
    text = "[ RUN      ] t1\n[       OK ] t1\n[ RUN      ] t2\n"
    records, _ = parse_cmocka_output(text)
    assert {r.test_id: r.outcome for r in records} == {"t1": "pass", "t2": "error"}

    script, prefix = _stub_suite(tmp_path, text)
    assert run_existing_suite(script, "cmocka", argv_prefix=prefix).aggregate == "failed"


def test_cmocka_unfinished_test_before_next_run_is_an_error() -> None:
    records, _ = parse_cmocka_output("[ RUN      ] t1\n[ RUN      ] t2\n[       OK ] t2\n")

    assert {r.test_id: r.outcome for r in records} == {"t1": "error", "t2": "pass"}


def test_undecodable_suite_output_does_not_crash_the_run(tmp_path: Path) -> None:
    script = tmp_path / "suite_bytes.py"
    script.write_text(
        "import sys\nsys.stdout.buffer.write(bytes([97, 46, 99, 58, 49, 58, 116, 58, 80, 65, 83, 83, 10, 129, 254, 10]))\n",
        encoding="utf-8",
    )

    run = run_existing_suite(script, "unity", argv_prefix=[sys.executable])

    assert run.aggregate == "pass"
    assert len(run.unrecognised_lines) == 1


def test_unity_fail_with_an_empty_expected_or_actual_is_an_error_not_a_crash() -> None:
    for message in ("Expected  Was 1", "Expected 1 Was ", "Expected  Was "):
        records, _ = parse_unity_output(f"a.c:1:t:FAIL: {message}\n")
        assert [r.outcome for r in records] == ["error"]
