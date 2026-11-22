# implements: TOOL-QUA-030
"""The user-executable validation suite (WP-QUA-03).

A suite of self-checks (id, what it proves, declared cost, required tools), an
offline runner (bundled inputs only — no network, no compiler), and a result
record whose every outcome is pass, fail or not-run with a named reason. A
check needing an unavailable tool is not-run, never pass. The record is
deterministic JSON, byte-stable across runs and independent of check order.
"""

from __future__ import annotations

import json

import pytest

from ectt.qua import (
    STATE_FAIL,
    STATE_NOT_RUN,
    STATE_PASS,
    CheckOutcome,
    ValidationCheck,
    ValidationReport,
    default_validation_checks,
    dump_validation_report,
    run_validation_suite,
)


def _check(check_id: str, *, result: bool = True, requires: tuple[str, ...] = (), cost: str = "instant") -> ValidationCheck:
    return ValidationCheck(
        check_id=check_id,
        proves=f"the claim of {check_id}",
        cost=cost,
        requires=requires,
        check=lambda result=result: result,
    )


def test_every_check_passes_on_a_clean_machine() -> None:
    """verifies: TOOL-QUA-030 — a suite whose checks demonstrate their claims
    reports every result as pass, with counts."""
    report = run_validation_suite([_check("c.one"), _check("c.two")], available_tools=())
    assert report.counts() == {"fail": 0, "not-run": 0, "pass": 2}
    assert all(result.state == STATE_PASS and result.reason is None for result in report.results)


def test_a_failing_check_reports_fail_with_its_reason() -> None:
    """verifies: TOOL-QUA-030 — a check that cannot demonstrate its claim is a
    fail with the named reason, never silently dropped."""
    report = run_validation_suite([_check("c.ok"), _check("c.broken", result=False)])
    assert report.counts() == {"fail": 1, "not-run": 0, "pass": 1}
    failed = next(r for r in report.results if r.check_id == "c.broken")
    assert failed.state == STATE_FAIL and failed.reason == "check_failed"


def test_a_missing_tool_is_not_run_never_pass() -> None:
    """verifies: TOOL-QUA-030 — a check needing an unavailable tool is not-run
    with the tool named; its callable is never invoked."""
    invoked: list[str] = []

    def probe() -> bool:
        invoked.append("called")
        return True

    tool_check = ValidationCheck(
        check_id="c.toolchain",
        proves="the generated C compiles",
        cost="quick",
        requires=("compiler",),
        check=probe,
    )
    report = run_validation_suite([_check("c.free"), tool_check], available_tools=())
    outcome = next(r for r in report.results if r.check_id == "c.toolchain")
    assert outcome.state == STATE_NOT_RUN
    assert outcome.reason == "missing_tool"
    assert outcome.detail == "compiler"
    assert invoked == []  # the check never ran
    assert report.counts()["pass"] == 1  # the not-run check cannot read as a pass

    # A partially available tool set still refuses: every requirement must hold.
    both = ValidationCheck(
        check_id="c.both", proves="x", cost="instant", requires=("compiler", "debugger"), check=probe
    )
    partial = run_validation_suite([both], available_tools=("debugger",))
    assert partial.results[0].state == STATE_NOT_RUN
    assert partial.results[0].detail == "compiler"


def test_the_record_is_byte_stable_and_order_independent() -> None:
    """verifies: TOOL-NFR-060 — the result record is deterministic JSON,
    byte-identical across runs and under input reordering."""
    checks = [_check("c.b", cost="quick"), _check("c.a"), _check("c.c", requires=("compiler",))]
    first = dump_validation_report(run_validation_suite(checks))
    second = dump_validation_report(run_validation_suite(checks))
    assert first == second
    reordered = dump_validation_report(run_validation_suite(list(reversed(checks))))
    assert reordered == first  # processed in id order
    document = json.loads(first)
    assert [r["check_id"] for r in document["results"]] == sorted(
        r["check_id"] for r in document["results"]
    )
    assert document["counts"] == {"fail": 0, "not-run": 1, "pass": 2}


def test_the_record_carries_id_proves_and_cost() -> None:
    """verifies: TOOL-QUA-030 — every result names its check, the claim it
    proved (or could not), and the declared cost class."""
    report = run_validation_suite([_check("c.quick", cost="quick")])
    outcome: CheckOutcome = report.results[0]
    assert outcome.check_id == "c.quick"
    assert outcome.proves == "the claim of c.quick"
    assert outcome.cost == "quick"
    document = json.loads(dump_validation_report(report))
    assert document["results"][0]["proves"] == "the claim of c.quick"


def test_a_raising_check_fails_without_details_leaking() -> None:
    """verifies: TOOL-QUA-030 — a check that raises is a fail (check_error);
    the exception text is not recorded, so the record stays byte-stable."""
    boom = ValidationCheck(
        check_id="c.boom", proves="x", cost="instant", check=lambda: (_ for _ in ()).throw(OSError("C:\\users\\secret"))
    )
    report = run_validation_suite([boom])
    outcome = report.results[0]
    assert outcome.state == STATE_FAIL and outcome.reason == "check_error"
    assert "secret" not in dump_validation_report(report)
    again = run_validation_suite([boom])
    assert dump_validation_report(report) == dump_validation_report(again)


def test_invalid_check_definitions_are_refused() -> None:
    """verifies: API — malformed check definitions are refused at construction."""
    with pytest.raises(ValueError):
        ValidationCheck(check_id="", proves="x", cost="instant", check=lambda: True)
    with pytest.raises(ValueError):
        ValidationCheck(check_id="c.x", proves="x", cost="hours", check=lambda: True)
    with pytest.raises(ValueError):
        ValidationCheck(check_id="c.x", proves="  ", cost="instant", check=lambda: True)
    with pytest.raises(ValueError):
        ValidationCheck(check_id="c.x", proves="x", cost="instant", requires=("bad tool!",), check=lambda: True)
    with pytest.raises(ValueError):
        ValidationCheck(check_id="c.x", proves="x", cost="instant", check="not callable")


def test_the_bundled_checks_pass_offline() -> None:
    """verifies: TOOL-QUA-030 — the bundled default checks prove engine
    fundamentals on this machine with no tool and no network."""
    checks = default_validation_checks()
    assert len(checks) >= 3
    assert all(check.requires == () and check.cost == "instant" for check in checks)
    report = run_validation_suite(checks)
    assert report.counts() == {"fail": 0, "not-run": 0, "pass": len(checks)}
    assert json.loads(dump_validation_report(report))["counts"]["pass"] == len(checks)


def test_an_empty_suite_is_a_valid_record() -> None:
    """verifies: API — no checks, an all-zero record (not an error)."""
    report: ValidationReport = run_validation_suite([])
    assert report.counts() == {"fail": 0, "not-run": 0, "pass": 0}
    assert dump_validation_report(report) == dump_validation_report(run_validation_suite([]))
