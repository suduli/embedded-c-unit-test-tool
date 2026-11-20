# implements: TOOL-TGT-070
"""Host and target test parity (WP-EXT-04).

Verifies: TOOL-TGT-070 (test cases execute unmodified on host and target; only
configuration distinguishes the two) with the TOOL-TGT-130 rule that host success never
establishes target behavior.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result
from ectt.ext.parity import (
    HOST_TRANSPORT,
    ExecutionConfig,
    ExecutionPlan,
    ParityError,
    check_parity,
    compare_outcomes,
    find_portability_issues,
)
from ectt.tcm import datacases as dd

HOST = ExecutionConfig("host", "gcc-14", "native", HOST_TRANSPORT)
TARGET = ExecutionConfig("target", "arm-none-eabi-gcc-13", "openocd", "serial_uart", target_id="stm32-1", settings={"flash_timeout": "30"})
CODE = "/* generated harness */\nint main(void) { return 0; }\n"


def _case(case_id: str, **kw: Any) -> dd.DataDrivenTestCase:
    parameters = kw.pop("parameters", {"x": "1"})
    expected = kw.pop("expected", dd.TestCaseExpected(return_value="2"))
    stubs = kw.pop("stubs", ())
    return dd.refresh_digest(
        dd.DataDrivenTestCase(case_id, "src/a.c", "f", dd.TestCaseInputs(parameters=parameters), expected, stubs, **kw)
    )


CASES = [_case("tc.one"), _case("tc.two", parameters={"x": "9"})]


def _plans(**kw: Any) -> tuple[ExecutionPlan, ExecutionPlan]:
    host_cases = kw.get("host_cases", CASES)
    target_cases = kw.get("target_cases", CASES)
    return (
        ExecutionPlan.build(host_cases, kw.get("host_code", CODE), kw.get("host_config", HOST)),
        ExecutionPlan.build(target_cases, kw.get("target_code", CODE), kw.get("target_config", TARGET)),
    )


# --- parity of the plans ----------------------------------------------------------------------


def test_identical_cases_and_code_with_different_configuration_is_parity() -> None:
    report = check_parity(*_plans())

    assert report.ok and report.violations == ()
    assert report.identical_cases == 2
    assert report.config_differences == ("toolchain", "runner", "transport", "settings")


def test_only_configuration_may_differ_and_the_differences_are_listed() -> None:
    same_runner = replace(TARGET, runner="native", settings={})
    report = check_parity(*_plans(target_config=same_runner))
    assert report.ok and report.config_differences == ("toolchain", "transport")


def test_a_case_missing_on_either_side_is_a_violation() -> None:
    report = check_parity(*_plans(target_cases=CASES[:1], host_cases=[*CASES, _case("tc.three")]))

    assert not report.ok
    assert {(v.kind, v.subject) for v in report.violations} == {("case_only_on_host", "tc.two"), ("case_only_on_host", "tc.three")}
    assert report.identical_cases == 1


def test_a_case_present_only_on_the_target_is_a_violation() -> None:
    report = check_parity(*_plans(target_cases=[*CASES, _case("tc.extra")]))
    assert [(v.kind, v.subject) for v in report.violations] == [("case_only_on_target", "tc.extra")]


def test_the_same_case_id_with_different_content_is_a_violation() -> None:
    edited = [CASES[0], _case("tc.two", parameters={"x": "10"})]

    report = check_parity(*_plans(target_cases=edited))

    assert [(v.kind, v.subject) for v in report.violations] == [("case_content_differs", "tc.two")]
    assert report.identical_cases == 1


def test_different_generated_code_is_a_violation() -> None:
    report = check_parity(*_plans(target_code=CODE + "/* target tweak */\n"))
    assert [v.kind for v in report.violations] == ["generated_code_differs"]


def test_all_violations_are_reported_together_and_deterministically() -> None:
    report = check_parity(*_plans(target_cases=[_case("tc.two", parameters={"x": "10"}), _case("z.new")], target_code="other"))
    kinds = [(v.kind, v.subject) for v in report.violations]
    assert kinds == [
        ("case_only_on_host", "tc.one"),
        ("case_only_on_target", "z.new"),
        ("case_content_differs", "tc.two"),
        ("generated_code_differs", "generated code"),
    ]
    assert report == check_parity(*_plans(target_cases=[_case("tc.two", parameters={"x": "10"}), _case("z.new")], target_code="other"))


def test_case_order_does_not_matter() -> None:
    assert check_parity(*_plans(target_cases=list(reversed(CASES)))).ok


def test_parity_of_inputs_never_claims_target_behavior() -> None:
    assert check_parity(*_plans()).establishes_target_behavior is False


def test_check_parity_needs_a_host_plan_and_a_target_plan() -> None:
    host, target = _plans()
    for pair in ((target, host), (host, host), (target, target)):
        with pytest.raises(ParityError) as excinfo:
            check_parity(*pair)
        assert excinfo.value.reason == "wrong_kind"


def test_duplicate_case_ids_cannot_be_planned() -> None:
    with pytest.raises(ParityError) as excinfo:
        ExecutionPlan.build([CASES[0], CASES[0]], CODE, HOST)
    assert excinfo.value.reason == "duplicate_case"


# --- the configuration ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kwargs",
    [
        {"kind": "simulator", "toolchain": "t", "runner": "r", "transport": HOST_TRANSPORT},
        {"kind": "host", "toolchain": "", "runner": "r", "transport": HOST_TRANSPORT},
        {"kind": "host", "toolchain": "gcc 14", "runner": "r", "transport": HOST_TRANSPORT},
        {"kind": "host", "toolchain": "t", "runner": "", "transport": HOST_TRANSPORT},
        {"kind": "host", "toolchain": "t", "runner": "r", "transport": "serial_uart"},
        {"kind": "host", "toolchain": "t", "runner": "r", "transport": HOST_TRANSPORT, "target_id": "t1"},
        {"kind": "target", "toolchain": "t", "runner": "r", "transport": "serial_uart"},
        {"kind": "target", "toolchain": "t", "runner": "r", "transport": "stdout", "target_id": "t1"},
        {"kind": "target", "toolchain": "t", "runner": "r", "transport": "serial_uart", "target_id": "has space"},
    ],
)
def test_invalid_configurations_are_refused(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ParityError) as excinfo:
        ExecutionConfig(**kwargs)
    assert excinfo.value.reason == "invalid_config"


@pytest.mark.parametrize("transport", ["semihosting", "serial_uart"])
def test_a_target_may_use_either_documented_channel(transport: str) -> None:
    assert ExecutionConfig("target", "t", "r", transport, target_id="t1").transport == transport


# --- portability lint --------------------------------------------------------------------------


def _issues(**kw: Any) -> list[tuple[str, str, str]]:
    return [(i.field_path, i.kind, i.text) for i in find_portability_issues([_case("c1", **kw)])]


def test_a_clean_case_has_no_issues() -> None:
    assert find_portability_issues(CASES) == ()


@pytest.mark.parametrize("value", ["C:\\temp\\x.bin", "D:/data/in.txt", "/home/user/in.txt", "/usr/lib/x.so", '"/tmp/work/a"'])
def test_absolute_paths_are_host_specific(value: str) -> None:
    assert [kind for _f, kind, _t in _issues(parameters={"path": value})] == ["absolute_path"]


@pytest.mark.parametrize("value", ["a / b", "1/2/3", "x/y", "10 / 2", "(a)/b/c", "4/2"])
def test_division_and_relative_text_are_not_paths(value: str) -> None:
    assert _issues(parameters={"v": value}) == []


@pytest.mark.parametrize("macro", ["_WIN32", "__linux__", "__APPLE__", "__x86_64__", "__arm__", "__aarch64__", "__ARM_ARCH_7M__", "__CYGWIN__"])
def test_platform_macros_are_host_or_target_specific(macro: str) -> None:
    assert _issues(parameters={"v": f"defined({macro}) ? 1 : 0"}) == [("inputs.parameters.v", "platform_macro", macro)]


def test_getenv_is_host_specific() -> None:
    assert _issues(parameters={"v": 'getenv("HOME")'}) == [("inputs.parameters.v", "host_environment", "getenv(")]


@pytest.mark.parametrize("value", ["(char *)0x20000000", "(volatile unsigned *) 0x40021000", "(int*)4096", "(struct S *)0xDEADBEEF"])
def test_non_zero_pointer_literals_name_a_memory_map(value: str) -> None:
    assert [kind for _f, kind, _t in _issues(parameters={"p": value})] == ["pointer_literal"]


@pytest.mark.parametrize("value", ["(char *)0", "(void *)0x0", "(int *)00", "NULL", "(unsigned)0x20000000", "(a) * 0x10"])
def test_null_and_integer_casts_are_not_pointer_literals(value: str) -> None:
    assert _issues(parameters={"p": value}) == []


def test_every_value_field_is_scanned_with_its_path() -> None:
    leak = "__linux__"
    case = _case(
        "c1",
        parameters={"a": leak},
        expected=dd.TestCaseExpected(return_value=leak, global_finals={"g": leak}, out_parameters={"o": leak}),
        stubs=(dd.StubSpec("s", "fixed", returns=(leak,), out_parameters={"q": leak}),),
        extra={"note": leak},
    )
    inputs = dd.TestCaseInputs(parameters={"a": leak}, global_inits={"gi": leak})

    paths = {i.field_path for i in find_portability_issues([replace(case, inputs=inputs)])}

    assert paths == {
        "inputs.parameters.a",
        "inputs.globals.gi",
        "expected.return",
        "expected.globals.g",
        "expected.out_parameters.o",
        "stubs.s.returns[0]",
        "stubs.s.out_parameters.q",
        "extra.note",
    }


def test_issues_are_sorted_by_case_and_field_and_deduplicated() -> None:
    cases = [_case("b", parameters={"x": "__linux__ _WIN32"}), _case("a", parameters={"x": "__linux__ __linux__"})]

    issues = find_portability_issues(cases)

    assert [(i.case_id, i.text) for i in issues] == [("a", "__linux__"), ("b", "_WIN32"), ("b", "__linux__")]
    assert issues == find_portability_issues(list(reversed(cases)))


# --- outcomes ----------------------------------------------------------------------------------


def _run(run_id: str, outcomes: dict[str, str], kind: str = "host") -> ResultSet:
    execution = ExecutionMetadata("host", "gcc") if kind == "host" else ExecutionMetadata("rig", "arm-gcc", target_id="stm32-1")
    results = tuple(finalize_result(t, o, "d" * 64, failures=_failure(o)) for t, o in sorted(outcomes.items()))
    return ResultSet(run_id=run_id, execution=execution, results=results)


def _failure(outcome: str) -> tuple[Any, ...]:
    from ectt.exh.results import AssertionFailure, SourceLocation

    return (AssertionFailure("a", "1", "2", SourceLocation("f.c", 1)),) if outcome == "fail" else ()


def test_equal_outcomes_agree_without_establishing_target_behavior() -> None:
    comparison = compare_outcomes(_run("h", {"t1": "pass", "t2": "pass"}), _run("t", {"t1": "pass", "t2": "pass"}, "target"))

    assert comparison.agreed == ("t1", "t2") and comparison.consistent
    assert comparison.establishes_target_behavior is False


def test_a_host_pass_that_is_a_target_failure_is_a_divergence() -> None:
    comparison = compare_outcomes(_run("h", {"t1": "pass", "t2": "pass"}), _run("t", {"t1": "pass", "t2": "fail"}, "target"))

    assert comparison.agreed == ("t1",)
    assert [(d.test_id, d.host, d.target) for d in comparison.divergences] == [("t2", "pass", "fail")]
    assert not comparison.consistent


def test_tests_run_on_one_side_only_are_listed_not_skipped() -> None:
    comparison = compare_outcomes(_run("h", {"t1": "pass", "t2": "pass"}), _run("t", {"t1": "pass", "t3": "pass"}, "target"))

    assert comparison.only_on_host == ("t2",) and comparison.only_on_target == ("t3",)
    assert comparison.agreed == ("t1",) and not comparison.consistent


def test_empty_runs_compare_as_consistent_but_prove_nothing() -> None:
    comparison = compare_outcomes(_run("h", {}), _run("t", {}, "target"))
    assert comparison.consistent and comparison.agreed == () and comparison.establishes_target_behavior is False
