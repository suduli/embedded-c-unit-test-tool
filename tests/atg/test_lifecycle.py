# implements: TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080
"""Validation port and generated-case lifecycle (WP-ATG-01).

Verifies: TOOL-ATG-040 (canonical, editable emission), TOOL-ATG-050 (nothing is
presented unless it compiled and ran), TOOL-ATG-070 (machine-generated marks in
artifact and reports), TOOL-ATG-080 (observed behaviour as unreviewed expected
value). The port is a stub: generation is testable without a builder or runner.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import ectt.atg
from ectt.atg import (
    AtgError,
    BuildOutcome,
    CoverageDelta,
    EngineInfo,
    ExecutionOutcome,
    GenerationCandidate,
    case_marks,
    confirm_expected,
    expected_status,
    format_mark,
    is_machine_generated,
    make_candidate,
    report_marks,
    unreviewed_test_ids,
    validate_candidates,
)
from ectt.atg import TestValidationPort as ValidationPort
from ectt.prj.yaml_adapter import RestrictedYamlAdapter
from ectt.tcm import datacases as dd
from ectt.trc import AssociationSet, build_matrix

ENGINE = EngineInfo("klee", "3.1")


class StubPort:
    """Scripted validation port: behaviour keyed by the first parameter value."""

    def __init__(self, script: dict[str, Any]) -> None:
        self.script = script
        self.calls: list[tuple[str, str]] = []

    def _entry(self, candidate: GenerationCandidate) -> Any:
        return self.script[candidate.inputs.parameters["x"]]

    def build(self, candidate: GenerationCandidate) -> BuildOutcome:
        self.calls.append(("build", candidate.candidate_id))
        entry = self._entry(candidate)
        return BuildOutcome(ok=entry != "build_error", diagnostics=("error: unknown type",) if entry == "build_error" else ())

    def execute(self, candidate: GenerationCandidate) -> ExecutionOutcome:
        self.calls.append(("execute", candidate.candidate_id))
        entry = self._entry(candidate)
        if isinstance(entry, ExecutionOutcome):
            return entry
        raise AssertionError(f"unexpected script entry {entry!r}")

    def measure(self, candidate: GenerationCandidate) -> CoverageDelta | None:
        return None


def _cand(x: str, **kw: Any) -> GenerationCandidate:
    return make_candidate("src/a.c", "f", dd.TestCaseInputs(parameters={"x": x}), **kw)


def _ok(value: str, **kw: Any) -> ExecutionOutcome:
    return ExecutionOutcome("completed", return_value=value, **kw)


# --- TOOL-ATG-050: validation gate -------------------------------------------------------


def test_only_candidates_that_built_and_ran_are_presented() -> None:
    port = StubPort(
        {
            "1": _ok("10"),
            "2": "build_error",
            "3": ExecutionOutcome("crash", detail="SIGSEGV"),
            "4": ExecutionOutcome("timeout", detail="5s"),
            "5": ExecutionOutcome("harness_error", detail="fixture broke"),
        }
    )
    candidates = [_cand(x) for x in "12345"]

    outcome = validate_candidates(candidates, port, ENGINE)

    assert [c.inputs.parameters["x"] for c in outcome.cases] == ["1"]
    assert {d.reason for d in outcome.discarded} == {"build_failed", "crash", "timeout", "harness_error"}
    assert outcome.counts() == {
        "candidates": 5,
        "discarded": 4,
        "discarded_build_failed": 1,
        "discarded_crash": 1,
        "discarded_harness_error": 1,
        "discarded_timeout": 1,
        "presented": 1,
    }


def test_discards_carry_their_diagnostics() -> None:
    port = StubPort({"2": "build_error", "3": ExecutionOutcome("crash", detail="SIGSEGV at f+0x10")})
    outcome = validate_candidates([_cand("2"), _cand("3")], port, ENGINE)

    details = {d.reason: d.detail for d in outcome.discarded}
    assert details == {"build_failed": "error: unknown type", "crash": "SIGSEGV at f+0x10"}


def test_a_candidate_is_never_executed_when_it_did_not_build() -> None:
    port = StubPort({"2": "build_error"})
    candidate = _cand("2")
    validate_candidates([candidate], port, ENGINE)
    assert port.calls == [("build", candidate.candidate_id)]


def test_equal_vectors_collapse_to_one_validation() -> None:
    port = StubPort({"1": _ok("10")})
    outcome = validate_candidates([_cand("1"), _cand("1")], port, ENGINE)

    assert len(outcome.cases) == 1
    assert [d.reason for d in outcome.discarded] == ["duplicate"]
    assert port.calls.count(("build", outcome.cases[0].case_id)) == 1


def test_a_failing_port_presents_nothing_and_raises() -> None:
    class Broken(StubPort):
        def execute(self, candidate: GenerationCandidate) -> ExecutionOutcome:
            raise OSError("runner unavailable")

    with pytest.raises(AtgError) as excinfo:
        validate_candidates([_cand("1")], Broken({"1": _ok("1")}), ENGINE)
    assert excinfo.value.reason == "port_failed"
    assert isinstance(excinfo.value.__cause__, OSError)


def test_an_unknown_execution_state_from_the_port_is_refused() -> None:
    port = StubPort({"1": ExecutionOutcome("exploded")})
    with pytest.raises(AtgError) as excinfo:
        validate_candidates([_cand("1")], port, ENGINE)
    assert excinfo.value.reason == "invalid_port_result"


def test_no_candidates_is_an_empty_outcome() -> None:
    outcome = validate_candidates([], StubPort({}), ENGINE)
    assert outcome.cases == () and outcome.counts()["candidates"] == 0


def test_results_do_not_depend_on_candidate_order() -> None:
    port = StubPort({x: _ok(x) for x in "abc"})
    forward = validate_candidates([_cand(x) for x in "abc"], port, ENGINE)
    backward = validate_candidates([_cand(x) for x in "cba"], StubPort({x: _ok(x) for x in "abc"}), ENGINE)
    assert forward == backward


# --- TOOL-ATG-040: canonical emission ----------------------------------------------------


def test_a_generated_case_is_an_ordinary_data_driven_case() -> None:
    stubs = (dd.StubSpec(name="hal", mode="fixed", returns=("7",)),)
    port = StubPort({"1": _ok("10", global_finals={"g": "3"}, out_parameters={"p": "9"})})

    (case,) = validate_candidates([_cand("1", stubs=stubs, requirements=("REQ-1",))], port, ENGINE).cases

    assert isinstance(case, dd.DataDrivenTestCase)
    assert (case.unit, case.function) == ("src/a.c", "f")
    assert dict(case.inputs.parameters) == {"x": "1"}
    assert case.expected.return_value == "10"
    assert dict(case.expected.global_finals) == {"g": "3"}
    assert dict(case.expected.out_parameters) == {"p": "9"}
    assert case.stubs == stubs and case.requirements == ("REQ-1",)
    assert not case.stale


def test_a_generated_case_survives_the_tests_file_writer_and_parser() -> None:
    port = StubPort({"1": _ok("10")})
    (case,) = validate_candidates([_cand("1")], port, ENGINE).cases

    text = dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(case,)))
    (parsed,) = dd.parse_test_cases_document(RestrictedYamlAdapter().load(text)).cases

    assert parsed == case
    assert "atg" in text and "klee@3.1" in text and "unreviewed" in text


def test_a_generated_case_stays_editable_and_keeps_its_id_and_marks() -> None:
    port = StubPort({"1": _ok("10")})
    (case,) = validate_candidates([_cand("1")], port, ENGINE).cases

    edited = dd.refresh_digest(replace(case, expected=replace(case.expected, return_value="11")))

    assert edited.case_id == case.case_id
    assert edited.expected.return_value == "11"
    assert edited.content_digest != case.content_digest
    assert is_machine_generated(edited) and expected_status(edited) == "unreviewed"


def test_candidate_ids_are_stable_and_content_derived() -> None:
    first, again, other = _cand("1"), _cand("1"), _cand("2")
    assert first.candidate_id == again.candidate_id != other.candidate_id
    assert first.candidate_id.startswith("atg.")
    with_stub = _cand("1", stubs=(dd.StubSpec("s", "fixed"),))
    assert with_stub.candidate_id != first.candidate_id


# --- TOOL-ATG-070: machine-generated marks -----------------------------------------------


def test_origin_records_author_engine_and_version() -> None:
    (case,) = validate_candidates([_cand("1")], StubPort({"1": _ok("10")}), ENGINE).cases
    assert (case.origin.author, case.origin.engine) == ("atg", "klee@3.1")


def test_marks_distinguish_generated_from_authored_cases() -> None:
    (generated,) = validate_candidates([_cand("1")], StubPort({"1": _ok("10")}), ENGINE).cases
    authored = dd.refresh_digest(
        dd.DataDrivenTestCase("hand.1", "src/a.c", "f", dd.TestCaseInputs(), dd.TestCaseExpected("1"), ())
    )

    assert case_marks(generated) == {
        "case_id": generated.case_id,
        "engine": "klee@3.1",
        "expected": "unreviewed",
        "machine_generated": True,
    }
    assert case_marks(authored)["machine_generated"] is False
    assert case_marks(authored)["expected"] == "authored"
    assert format_mark(authored) == "authored"
    assert format_mark(generated) == "machine-generated (klee@3.1); expected value unreviewed"


def test_ai_provider_cases_are_machine_generated_too() -> None:
    ai_case = dd.refresh_digest(
        dd.DataDrivenTestCase(
            "ai.1", "src/a.c", "f", dd.TestCaseInputs(), dd.TestCaseExpected("1"), (), origin=dd.TestCaseOrigin(author="ai")
        )
    )
    assert is_machine_generated(ai_case) and expected_status(ai_case) == "unreviewed"
    assert format_mark(ai_case) == "machine-generated (unknown engine); expected value unreviewed"


def test_report_marks_count_generated_and_unreviewed_cases() -> None:
    port = StubPort({x: _ok(x) for x in "12"})
    generated = validate_candidates([_cand("1"), _cand("2")], port, ENGINE).cases
    confirmed = confirm_expected(generated[0])
    authored = dd.refresh_digest(
        dd.DataDrivenTestCase("hand.1", "src/a.c", "f", dd.TestCaseInputs(), dd.TestCaseExpected("1"), ())
    )

    marks = report_marks([confirmed, generated[1], authored])

    assert marks["machine_generated"] == 2
    assert marks["unreviewed_expectations"] == 1
    assert [m["case_id"] for m in marks["cases"]] == sorted(m["case_id"] for m in marks["cases"])


# --- TOOL-ATG-080: unreviewed expectations -----------------------------------------------


def test_observed_behaviour_becomes_the_expected_value_marked_unreviewed() -> None:
    port = StubPort({"1": _ok("42", global_finals={"g_mode": "2"})})
    (case,) = validate_candidates([_cand("1")], port, ENGINE).cases

    assert case.expected.return_value == "42"
    assert dict(case.expected.global_finals) == {"g_mode": "2"}
    assert case.origin.review_state == "unreviewed"
    assert expected_status(case) == "unreviewed"


def test_a_void_function_records_no_expected_return() -> None:
    (case,) = validate_candidates([_cand("1")], StubPort({"1": ExecutionOutcome("completed")}), ENGINE).cases
    assert case.expected.return_value is None


def test_confirming_marks_reviewed_rebinds_the_digest_and_keeps_the_id() -> None:
    (case,) = validate_candidates([_cand("1")], StubPort({"1": _ok("42")}), ENGINE).cases

    confirmed = confirm_expected(case)

    assert expected_status(confirmed) == "reviewed"
    assert confirmed.case_id == case.case_id and confirmed.expected == case.expected
    assert confirmed.content_digest != case.content_digest and not confirmed.stale
    assert confirm_expected(confirmed) is confirmed


def test_an_authored_case_cannot_be_confirmed() -> None:
    authored = dd.refresh_digest(
        dd.DataDrivenTestCase("hand.1", "src/a.c", "f", dd.TestCaseInputs(), dd.TestCaseExpected("1"), ())
    )
    with pytest.raises(AtgError) as excinfo:
        confirm_expected(authored)
    assert excinfo.value.reason == "not_generated"


def test_unreviewed_cases_do_not_count_toward_requirement_verdicts() -> None:
    """Reports can say which expectation is a specification and which a regression detector."""
    generated = validate_candidates([_cand("1", requirements=("REQ-1",))], StubPort({"1": _ok("1")}), ENGINE).cases
    (case,) = generated
    associations = AssociationSet()
    associations.add("REQ-1", case.case_id)
    statuses = {case.case_id: "pass"}

    before = build_matrix(associations, statuses, unreviewed_tests=unreviewed_test_ids(generated))
    after = build_matrix(associations, statuses, unreviewed_tests=unreviewed_test_ids([confirm_expected(case)]))

    assert before.rows[0].verdict == "unverified"
    assert after.rows[0].verdict == "pass"


# --- the port (DSN-ATG-110) --------------------------------------------------------------


def test_the_stub_satisfies_the_port_protocol_and_a_partial_object_does_not() -> None:
    assert isinstance(StubPort({}), ValidationPort)

    class OnlyBuild:
        def build(self, candidate: GenerationCandidate) -> BuildOutcome:
            return BuildOutcome(True)

    assert not isinstance(OnlyBuild(), ValidationPort)


def test_the_generation_package_does_not_depend_on_the_layers_below_it() -> None:
    """The validation port is an inverted dependency: no import of the builder, runner or coverage."""
    forbidden = ("ectt.bld", "ectt.exh", "ectt.cov", "ectt.tch", "ectt.gen")
    imported: set[str] = set()
    for source in Path(ectt.atg.__file__).parent.glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
            elif isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
    assert not {m for m in imported if m.startswith(forbidden)}


# --- input validation --------------------------------------------------------------------


@pytest.mark.parametrize(("name", "version"), [("", "1"), ("klee", ""), ("kl ee", "1"), ("klee", "3@1"), (" ", " ")])
def test_engine_identity_must_be_clean_tokens(name: str, version: str) -> None:
    with pytest.raises(AtgError) as excinfo:
        EngineInfo(name, version)
    assert excinfo.value.reason == "invalid_engine"


@pytest.mark.parametrize(("unit", "function"), [("", "f"), ("u", ""), (" ", "f")])
def test_candidates_need_a_unit_and_a_function(unit: str, function: str) -> None:
    with pytest.raises(AtgError) as excinfo:
        make_candidate(unit, function, dd.TestCaseInputs())
    assert excinfo.value.reason == "invalid_candidate"
