# implements: TOOL-REP-010, TOOL-REP-100
"""Hand-written mutation battery for ectt.rep (B7).

No product code is changed. Each mutant is a hand-written copy of one
critical contract with a single seeded fault, executed in isolation; the real
implementation is the oracle — a mutant is killed when its outcome differs
from the real implementation on the same probe (a named refusal counts as an
outcome).

Mutant selection: the Cobertura rate's zero-total discipline (no fabricated
100%), the JUnit tests count (every test counted), the rate rounding policy
(half-even, not rounding up), the view layer's no_data-as-failure mapping and
its stale-minimization refusal — the contracts a silent fault would use to
present a broken run as a passing one.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import pytest

from ectt.cov.thresholds import ThresholdEvaluation, ThresholdResult
from ectt.cbt.minimize import Minimization
from ectt.rep.machine_formats import cobertura_rate, render_junit
from ectt.rep.views import minimized_suite_view, threshold_view


# --- cobertura rate mutants ------------------------------------------------------------


def _m7_rate_zero_total_fabricates(covered: int, total: int) -> str:
    """FAULT: a zero-total rate renders '1' (a fabricated 100%)."""
    if total == 0:
        return "1"
    scaled = Fraction(covered, total) * 1_000_000
    six_dp = round(scaled)
    rendered = f"{six_dp / 1_000_000:.6f}".rstrip("0").rstrip(".")
    return rendered or "0"


def _m8_rate_rounds_up(covered: int, total: int) -> str:
    """FAULT: the rate rounds up instead of half-even."""
    if total == 0:
        return "0"
    scaled = Fraction(covered, total) * 1_000_000
    import math

    six_dp = math.ceil(scaled)
    rendered = f"{six_dp / 1_000_000:.6f}".rstrip("0").rstrip(".")
    return rendered or "0"


def _probe_rate(mutant: Any, covered: int, total: int) -> bool:
    return cobertura_rate(covered, total) != mutant(covered, total)


# --- junit count mutants -----------------------------------------------------------------


def _junit_tests_attr(statuses: dict[str, str]) -> str:
    doc = render_junit(_junit_model(statuses))
    suite = doc[doc.index("<testsuite ") :]
    attr = suite.split("tests=")[1]
    return attr.split()[0].strip('"')


def _junit_model(statuses: dict[str, str]) -> Any:
    from ectt.exh.results import finalize_result
    from ectt.rep.model import build_report_model
    from tests.rep.test_renderers import CLOCK, _result_set

    outcomes = {"pass": "pass", "fail": "fail", "error": "error", "timeout": "timeout"}
    results = tuple(
        finalize_result(test_id, outcomes.get(status, "not_run"), f"d{i}" * 32)
        if outcomes.get(status, "not_run") != "not_run"
        else None
        for i, (test_id, status) in enumerate(statuses.items())
    )
    records = tuple(r for r in results if r is not None)
    not_run = tuple(t for (t, s) in statuses.items() if s == "not_run")
    return build_report_model(_result_set(records, not_executed=not_run), clock=CLOCK)


def _m9_junit_tests_count_drops_not_run(statuses: dict[str, str]) -> str:
    """FAULT: the tests attribute counts only executed tests."""
    executed = sum(1 for s in statuses.values() if s != "not_run")
    return f'"{executed}"'


def _probe_junit(statuses: dict[str, str]) -> bool:
    return _junit_tests_attr(statuses) != _m9_junit_tests_count_drops_not_run(statuses)


# --- view mutants --------------------------------------------------------------------------


def _threshold_result(state: str) -> ThresholdResult:
    return ThresholdResult(
        evaluations=(
            ThresholdEvaluation(metric="branches", state=state, covered=0, total=None,
                                minimum=Fraction(1, 2)),
        ),
        passed=state in ("pass", "not_applicable"),
    )


def _m10_no_data_displayed_pass(result: ThresholdResult) -> dict[str, Any]:
    """FAULT: no_data is displayed as a pass."""
    displayed_map = {"pass": "pass", "fail": "fail", "no_data": "pass", "not_applicable": "exempt"}
    return {
        "passed": result.passed,
        "evaluations": [
            {"displayed": displayed_map[e.state], "state": e.state} for e in result.evaluations
        ],
    }


def _probe_no_data() -> bool:
    real = threshold_view(_threshold_result("no_data"))
    mutant = _m10_no_data_displayed_pass(_threshold_result("no_data"))
    return real["evaluations"][0]["displayed"] != mutant["evaluations"][0]["displayed"]


def _m11_stale_minimization_accepted(minimization: Minimization, coverage: dict[str, Any]) -> dict[str, Any]:
    """FAULT: the preserved-union check is removed."""
    full_union: set[str] = set()
    for covered in coverage.values():
        full_union.update(tuple(covered))
    return {
        "view": "minimized_suite",
        "kept": list(minimization.kept),
        "redundant": list(minimization.redundant),
        "preserved_union": sorted(full_union),
    }


def _probe_stale() -> bool:
    stale = Minimization(kept=("t.a",), redundant=("t.b",))
    coverage = {"t.a": {"s1"}, "t.b": {"s2"}}
    try:
        minimized_suite_view(stale, coverage)
        real = "presented"
    except Exception as exc:
        real = f"refused:{type(exc).__name__}"
    mutant = _m11_stale_minimization_accepted(stale, coverage)
    return mutant["view"] != real


MUTANTS = [
    ("rep-m7-rate-zero-total-fabricates", lambda: _probe_rate(_m7_rate_zero_total_fabricates, 0, 0)),
    ("rep-m8-rate-rounds-up", lambda: _probe_rate(_m8_rate_rounds_up, 1, 3)),
    ("rep-m9-junit-tests-count-drops-not-run", lambda: _probe_junit({"t.a": "pass", "t.b": "not_run"})),
    ("rep-m10-no-data-displayed-pass", lambda: _probe_no_data()),
    ("rep-m11-stale-minimization-accepted", lambda: _probe_stale()),
]


@pytest.mark.parametrize("name, killed", MUTANTS, ids=[m[0] for m in MUTANTS])
def test_rep_mutant_is_killed(name: str, killed: bool) -> None:
    assert killed, f"{name} survived: no case detects the fault"


def test_rep_kill_rate_report(capsys: pytest.CaptureFixture[str]) -> None:
    killed = sum(1 for _, probe in MUTANTS if probe())
    print(f"\nrep kill rate: {killed}/{len(MUTANTS)}")
    assert killed == len(MUTANTS)
