# implements: TOOL-MIG-010
"""Hand-written mutation battery for ectt.mig existing-suite parsers (B8).

No product code is changed. Each mutant is a hand-written copy of one
critical parser decision with a single seeded fault, executed in isolation.
The battery asserts (1) the real implementation satisfies every case and
(2) every mutant is killed by at least one case — the behaviour the suite
pins down detects the fault class.

Mutant selection: the verdict→outcome mapping, the under-detailed-failure
rule (a FAIL without detail must never become a `fail` claim), IGNORE as
`not_run`, and the "a test that never reported its verdict is never a silent
pass" rule are the contracts the S3 vocabulary and NR-18 lean on at the
existing-suite boundary.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import pytest

from ectt.mig.existing_suites import parse_cmocka_output, parse_unity_output

_UNITY_LINE = re.compile(
    r"^(?P<file>(?:[A-Za-z]:)?[^:]+):(?P<line>\d+):(?P<name>[^:\s]+):"
    r"(?P<verdict>PASS|FAIL|IGNORE)(?::\s*(?P<message>.*))?$"
)
_UNITY_EXPECTED = re.compile(r"Expected (?P<expected>.+) Was (?P<actual>.+)$")
_CMOCKA_VERDICT = re.compile(r"^\[\s*(?P<verdict>OKAY|OK|FAILED)\s*\]\s*(?P<name>\S+)\s*$")
_CMOCKA_RUN = re.compile(r"^\[\s*RUN\s*\]\s*(?P<name>\S+)\s*$")


@dataclass(frozen=True)
class Case:
    case_id: str
    run: Callable[[Any], Any]
    expect: Any


def _outcomes(records: Any) -> dict[str, str]:
    return {record.test_id: record.outcome for record in records}


def _killed(case: Case, impl: Any) -> bool:
    try:
        actual = case.run(impl)
    except Exception:
        return True
    return actual != case.expect


# --- unity mutants ---------------------------------------------------------------


def _m1_unity_underdetailed_fail_becomes_fail(text: str):
    """Seeded fault: a FAIL without detail becomes a `fail` claim (must be `error`)."""
    records, unrecognised = [], []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = _UNITY_LINE.match(line)
        if match is None:
            unrecognised.append(line)
            continue
        verdict = match.group("verdict")
        if verdict == "PASS":
            records.append(("pass", match.group("name")))
        elif verdict == "IGNORE":
            records.append(("not_run", match.group("name")))
        else:
            message = match.group("message") or ""
            detail = _UNITY_EXPECTED.search(message)
            if detail is not None:
                records.append(
                    ("fail", match.group("name"), detail.group("expected").strip(), detail.group("actual").strip())
                )
            else:
                records.append(("fail", match.group("name")))  # FAULT: was "error"
    return records, unrecognised


def _m2_unity_ignore_becomes_pass(text: str):
    """Seeded fault: IGNORE is upgraded to a pass (must be not_run)."""
    records, unrecognised = [], []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = _UNITY_LINE.match(line)
        if match is None:
            unrecognised.append(line)
            continue
        verdict = match.group("verdict")
        if verdict == "PASS":
            records.append(("pass", match.group("name")))
        elif verdict == "IGNORE":
            records.append(("pass", match.group("name")))  # FAULT: was "not_run"
        else:
            message = match.group("message") or ""
            detail = _UNITY_EXPECTED.search(message)
            if detail is not None:
                records.append(("fail", match.group("name")))
            else:
                records.append(("error", match.group("name")))
    return records, unrecognised


def _m3_unity_unrecognised_lines_dropped(text: str):
    """Seeded fault: unrecognised lines are silently dropped (must be reported)."""
    records = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        match = _UNITY_LINE.match(line)
        if match is None:
            continue  # FAULT: never reported
        verdict = match.group("verdict")
        records.append(("pass" if verdict == "PASS" else ("not_run" if verdict == "IGNORE" else "error"), match.group("name")))
    return records, []


# --- cmocka mutants ---------------------------------------------------------------


def _m4_cmocka_failed_becomes_pass(text: str):
    """Seeded fault: the FAILED verdict is normalised as a pass."""
    records, unrecognised = [], []
    started = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        verdict_match = _CMOCKA_VERDICT.match(line)
        if verdict_match is None:
            run_match = _CMOCKA_RUN.match(line)
            if run_match is not None:
                started = run_match.group("name")
            unrecognised.append(line)
            continue
        name = verdict_match.group("name")
        if name == started:
            started = None
        outcome = "pass"  # FAULT: "error" if FAILED
        records.append((outcome, name))
    if started is not None:
        records.append(("error", started))
    return records, unrecognised


def _m5_cmocka_unfinished_test_silent_pass(text: str):
    """Seeded fault: a test whose RUN never got a verdict is dropped (must be error)."""
    records, unrecognised = [], []
    started = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        verdict_match = _CMOCKA_VERDICT.match(line)
        if verdict_match is None:
            run_match = _CMOCKA_RUN.match(line)
            if run_match is not None:
                if started is not None:
                    records.append(("error", started))
                started = run_match.group("name")
            unrecognised.append(line)
            continue
        name = verdict_match.group("name")
        if name == started:
            started = None
        outcome = "error" if verdict_match.group("verdict") == "FAILED" else "pass"
        records.append((outcome, name))
    # FAULT: the trailing `if started is not None` finalisation is dropped
    return records, unrecognised


CASES_UNITY = [
    Case(
        "pass_ignored_detailed_fail",
        lambda p: _outcomes(p("f.c:12:test_a:PASS\nf.c:13:test_b:IGNORE\nf.c:14:test_c:FAIL: Expected 1 Was 2\n")[0]),
        {"test_a": "pass", "test_b": "not_run", "test_c": "fail"},
    ),
    Case(
        "underdetailed_fail_is_error",
        lambda p: _outcomes(p("f.c:12:test_a:FAIL\n")[0]),
        {"test_a": "error"},
    ),
    Case(
        "unrecognised_lines_reported",
        lambda p: p("this is not unity output\n")[1],
        ("this is not unity output",),
    ),
]

CASES_CMOCKA = [
    Case(
        "ok_failed_mapping",
        lambda p: _outcomes(p("[  OKAY    ] calibrates\n[  FAILED  ] broken\n")[0]),
        {"calibrates": "pass", "broken": "error"},
    ),
    Case(
        "unfinished_run_is_error",
        lambda p: _outcomes(p("[ RUN      ] x\n[  OKAY    ] x\n[ RUN      ] y\n")[0]),
        {"x": "pass", "y": "error"},
    ),
]


MUTANTS = [
    ("mig-m1-unity-underdetailed-fail-becomes-fail", _m1_unity_underdetailed_fail_becomes_fail, CASES_UNITY),
    ("mig-m2-unity-ignore-becomes-pass", _m2_unity_ignore_becomes_pass, CASES_UNITY),
    ("mig-m3-unity-unrecognised-dropped", _m3_unity_unrecognised_lines_dropped, CASES_UNITY),
    ("mig-m4-cmocka-failed-becomes-pass", _m4_cmocka_failed_becomes_pass, CASES_CMOCKA),
    ("mig-m5-cmocka-unfinished-silent-pass", _m5_cmocka_unfinished_test_silent_pass, CASES_CMOCKA),
]


@pytest.mark.parametrize("impl", [parse_unity_output, parse_cmocka_output], ids=["unity", "cmocka"])
def test_real_parsers_pass_the_battery(impl: Any) -> None:
    cases = CASES_UNITY if impl is parse_unity_output else CASES_CMOCKA
    for case in cases:
        assert case.run(impl) == case.expect, case.case_id


@pytest.mark.parametrize("mutant_id, impl, cases", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_mutant_is_killed(mutant_id: str, impl: Any, cases: list[Case]) -> None:
    kills = [case.case_id for case in cases if _killed(case, impl)]
    assert kills, f"{mutant_id} survived the whole battery: no case detects the fault"


def test_mig_kill_rate_report(capsys: pytest.CaptureFixture[str]) -> None:
    total = 0
    killed = 0
    per_mutant: dict[str, bool] = {}
    for mutant_id, impl, cases in MUTANTS:
        this = any(_killed(case, impl) for case in cases)
        per_mutant[mutant_id] = this
        total += 1
        killed += 1 if this else 0
    print(f"\nmig kill rate: {killed}/{total}")
    for mutant_id, this in per_mutant.items():
        print(f"  {mutant_id}: {'killed' if this else 'SURVIVED'}")
    assert killed == total
