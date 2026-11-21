# implements: TOOL-EXE-020, TOOL-TCD-090
"""Generated harness: RESULT/FAILURE stream and per-test state reset (FIX-GENPROTO).

Verifies: the harness emits the stream protocol defined in
docs/verification/WP-EXH-01-analysis.md (TOOL-EXE-020) and its setup hook resets
harness state so nothing leaks from one test into the next (DSN-TCM-060,
TOOL-TCD-090).

No C compiler is available to the test suite. The generated C is therefore checked by
(1) parsing it with libclang, as C99 and as strict C89, with zero diagnostics;
(2) deriving the *shape* of each emitted line from the C text itself and feeding the
resulting stream to the real host-side reader, ``ectt.exh.runner``, so drift between
the C and the reader fails a test; and (3) structural assertions on the state machine.
Executing the C is recorded as follow-up work.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from ectt.ana.frontend import parse
from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    FunctionModel,
    ProvenanceModel,
    SourceLocation,
)
from ectt.exh.errors import MalformedResultStreamError
from ectt.exh.runner import _parse_result_stream
from ectt.gen.harness import HarnessGenerator
from ectt.gen.protocol import RESULT_PROTOCOL_BLOCK, SETUP_TEARDOWN_BLOCK

NULL_TRANSPORT = "-DECTT_STREAM_WRITE(t)=((void)(t))"


def _diagnostics(source: str, *args: str, extra: list[tuple[str, str]] | None = None) -> list[str]:
    parsed = parse("probe.c", args=["-I.", *args], unsaved_files=[("probe.c", source), *(extra or [])])
    assert parsed.status == "parsed"
    return [f"{d.severity}: {d.message}" for d in parsed.diagnostics]


def _harness() -> Any:
    function = FunctionModel("adc_scale", "external", "none", SourceLocation("src/adc.c", 3), "ref:type.int")
    unit = AnalysisUnit(path="src/adc.c", status="parsed", functions=(function,))
    model = AnalysisModel(provenance=ProvenanceModel("0", "t", "t"), units=(unit,), types={})
    return HarnessGenerator(model, uut_path="src/adc.c").generate()


# --- the C is valid -------------------------------------------------------------------------


@pytest.mark.parametrize("standard", ["-std=c99", "-std=c89"])
def test_the_runtime_blocks_parse_cleanly_as_c99_and_strict_c89(standard: str) -> None:
    assert _diagnostics(RESULT_PROTOCOL_BLOCK + "\n" + SETUP_TEARDOWN_BLOCK, standard, "-pedantic", NULL_TRANSPORT) == []


def test_a_whole_generated_harness_parses_with_its_unit_header_present(tmp_path: Path) -> None:
    harness = _harness()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "adc.h").write_text("int adc_scale(int raw);\n", encoding="utf-8")
    (tmp_path / "harness.c").write_text(harness.source, encoding="utf-8")

    parsed = parse(tmp_path / "harness.c", args=["-std=c99", "-I", str(tmp_path), NULL_TRANSPORT])

    assert parsed.status == "parsed"
    assert [d for d in parsed.diagnostics if d.severity in ("error", "fatal")] == []


def test_the_transport_can_be_replaced_without_touching_stdio() -> None:
    assert "#ifndef ECTT_STREAM_WRITE" in RESULT_PROTOCOL_BLOCK
    replaced = "static void sink(const char *t) { (void)t; }\n#define ECTT_STREAM_WRITE(t) sink(t)\n" + RESULT_PROTOCOL_BLOCK
    assert "stdio" not in replaced.split("#define ECTT_STREAM_WRITE(t) sink(t)")[1].split("#ifndef ECTT_STREAM_WRITE")[0]
    assert _diagnostics(replaced + SETUP_TEARDOWN_BLOCK, "-std=c99") == []


# --- the stream matches the host reader -----------------------------------------------------------


def _body(source: str, signature_start: str) -> str:
    """The braces-delimited body of the *definition* that starts with ``signature_start``.

    A prototype with the same opening text is skipped: the definition is the occurrence
    whose next ``{`` comes before its next ``;``.
    """
    position = 0
    while True:
        start = source.index(signature_start, position)
        brace, semicolon = source.find("{", start), source.find(";", start)
        if brace != -1 and (semicolon == -1 or brace < semicolon):
            break
        position = start + 1
    depth, index = 0, brace
    while True:
        depth += {"{": 1, "}": -1}.get(source[index], 0)
        index += 1
        if depth == 0:
            return source[brace + 1 : index - 1]


def _shape(function_start: str) -> list[tuple[str, str]]:
    """The ordered writes a C function performs: literals, tokens and numbers."""
    shape: list[tuple[str, str]] = []
    for match in re.finditer(r'ECTT_STREAM_WRITE\("((?:[^"\\]|\\.)*)"\);|ectt_write_token\((\w+)\);|ectt_write_unsigned\(([^;]*)\);', _body(RESULT_PROTOCOL_BLOCK, function_start)):
        literal, token, number = match.groups()
        if literal is not None:
            shape.append(("lit", literal.replace("\\n", "\n")))
        elif token is not None:
            shape.append(("tok", token))
        else:
            shape.append(("num", number))
    return shape


def _token(value: str | None) -> str:
    """Token rule of ectt_write_token: whitespace becomes '_', empty becomes '-'."""
    if not value:
        return "-"
    return "".join("_" if c in " \t\n\r" else c for c in value)


def _emit(function_start: str, **args: Any) -> str:
    out = []
    for kind, item in _shape(function_start):
        if kind == "lit":
            out.append(item)
        elif kind == "tok":
            out.append(_token(args[item]))
        else:
            assert "line == 0 ? 1ul" in item, "the line number must be clamped to at least 1"
            out.append(str(1 if args["line"] == 0 else args["line"]))
    return "".join(out)


RESULT_FN = "void ectt_report_result(const char *test_id, const char *outcome) {"
FAILURE_FN = "void ectt_report_failure(const char *test_id, const char *assertion, const char *expected,"


def _parse(stream: str, ids: tuple[str, ...] = ("tc.one", "tc.two")) -> Any:
    return _parse_result_stream(stream, frozenset(ids), dict.fromkeys(ids, "a" * 64))


def test_a_result_line_has_the_shape_the_reader_expects() -> None:
    assert _shape(RESULT_FN) == [("lit", "RESULT "), ("tok", "test_id"), ("lit", " "), ("tok", "outcome"), ("lit", "\n")]
    records = _parse(_emit(RESULT_FN, test_id="tc.one", outcome="pass"))
    assert [(r.test_id, r.outcome) for r in records] == [("tc.one", "pass")]


def test_a_failure_line_has_six_tokens_in_the_order_the_reader_expects() -> None:
    items = [item for kind, item in _shape(FAILURE_FN) if kind != "lit"]
    assert items[:5] == ["test_id", "assertion", "expected", "actual", "file"]
    assert len(items) == 6 and "line" in items[5]
    stream = _emit(RESULT_FN, test_id="tc.two", outcome="fail") + _emit(
        FAILURE_FN, test_id="tc.two", assertion="expected_return", expected="4095", actual="0", file="src/a.c", line=88
    )

    (record,) = _parse(stream)

    (failure,) = record.failures
    assert (failure.assertion, failure.expected, failure.actual) == ("expected_return", "4095", "0")
    assert (failure.location.file, failure.location.line) == ("src/a.c", 88)


def test_a_failure_line_may_precede_its_result_line() -> None:
    stream = _emit(FAILURE_FN, test_id="tc.two", assertion="a", expected="1", actual="2", file="f.c", line=3) + _emit(
        RESULT_FN, test_id="tc.two", outcome="fail"
    )
    assert [r.outcome for r in _parse(stream)] == ["fail"]


def test_whitespace_in_values_becomes_underscores_so_the_line_still_has_seven_tokens() -> None:
    line = _emit(FAILURE_FN, test_id="tc.two", assertion="values differ", expected="a b", actual="c\td", file="my file.c", line=4)
    assert len(line.split()) == 7
    stream = _emit(RESULT_FN, test_id="tc.two", outcome="fail") + line
    assert _parse(stream)[0].failures[0].expected == "a_b"


def test_empty_values_become_a_dash_and_line_zero_becomes_one() -> None:
    line = _emit(FAILURE_FN, test_id="tc.two", assertion="", expected=None, actual="", file="", line=0)
    assert line == "FAILURE tc.two - - - - 1\n"
    assert _parse(_emit(RESULT_FN, test_id="tc.two", outcome="fail") + line)[0].failures[0].location.line == 1


def test_the_reader_refuses_what_a_line_number_below_one_would_produce() -> None:
    bad = "RESULT tc.two fail\nFAILURE tc.two a 1 2 f.c 0\n"
    with pytest.raises(MalformedResultStreamError):
        _parse(bad)


def test_token_and_number_helpers_in_c_match_the_documented_rules() -> None:
    body = _body(RESULT_PROTOCOL_BLOCK, "static void ectt_write_token(const char *text) {")
    assert "ECTT_STREAM_WRITE(\"-\")" in body
    assert "(unsigned char)*text <= ' '" in body  # space and every control character, not just four
    assert "'_'" in body
    assert "ECTT_STREAM_WRITE(\"0\")" in _body(RESULT_PROTOCOL_BLOCK, "static void ectt_write_unsigned(unsigned long value) {")


# --- outcomes: a test is never reported as a pass unless it ended with no failure ---------------------


def test_only_ending_a_test_with_no_failures_reports_a_pass() -> None:
    assert _body(RESULT_PROTOCOL_BLOCK, "void ectt_end_test(void) {").count('"pass"') == 1
    assert 'ectt_current_failures > 0 ? "fail" : "pass"' in RESULT_PROTOCOL_BLOCK
    assert RESULT_PROTOCOL_BLOCK.count('"pass"') == 1  # no other path can report a pass


def test_an_unfinished_test_is_error_or_fail_and_never_pass() -> None:
    body = _body(RESULT_PROTOCOL_BLOCK, "static void ectt_finish_open_test(void) {")
    assert 'ectt_current_failures > 0 ? "fail" : "error"' in body
    assert '"pass"' not in body


def test_starting_a_test_first_settles_the_previous_one() -> None:
    body = _body(RESULT_PROTOCOL_BLOCK, "void ectt_begin_test(const char *test_id) {")
    assert body.index("ectt_finish_open_test();") < body.index("ectt_current_test = test_id;")
    assert "ectt_current_failures = 0;" in body


def test_a_failure_outside_any_test_is_counted_not_dropped_or_misattributed() -> None:
    body = _body(RESULT_PROTOCOL_BLOCK, "void ectt_fail(const char *assertion, const char *expected, const char *actual,")
    assert body.index("ectt_current_test == 0") < body.index("ectt_report_failure(")
    assert "ectt_unattributed_failures++;" in body
    assert "unsigned ectt_unattributed_failure_count(void)" in RESULT_PROTOCOL_BLOCK


def test_ending_a_test_twice_reports_it_once() -> None:
    body = _body(RESULT_PROTOCOL_BLOCK, "void ectt_end_test(void) {")
    assert body.startswith("\n    if (ectt_current_test != 0) {")
    assert "ectt_current_test = 0;" in body


# --- state never leaks from one test into the next (DSN-TCM-060) ------------------------------------------


def test_setup_resets_state_then_runs_registered_resets_then_the_users_hook() -> None:
    body = _body(SETUP_TEARDOWN_BLOCK, "void ectt_run_setup(void) {")
    order = [body.index(token) for token in ("ectt_reset_test_state();", "ectt_run_state_resets();", "ectt_setup_hook();")]
    assert order == sorted(order)


def test_the_reset_clears_the_failure_count_and_settles_an_open_test() -> None:
    body = _body(RESULT_PROTOCOL_BLOCK, "static void ectt_reset_test_state(void) {")
    assert "ectt_finish_open_test();" in body
    assert "ectt_current_failures = 0;" in body


def test_teardown_runs_the_users_hook_and_then_settles_an_open_test() -> None:
    body = _body(SETUP_TEARDOWN_BLOCK, "void ectt_run_teardown(void) {")
    assert body.index("ectt_teardown_hook();") < body.index("ectt_finish_open_test();")


def test_every_registered_state_reset_runs_and_registration_never_drops_silently() -> None:
    run = _body(RESULT_PROTOCOL_BLOCK, "static void ectt_run_state_resets(void) {")
    assert "for (i = 0; i < ectt_state_reset_count; i++)" in run and "ectt_state_resets[i]();" in run
    register = _body(RESULT_PROTOCOL_BLOCK, "int ectt_register_state_reset(void (*fn)(void)) {")
    assert "ectt_state_reset_count >= ECTT_MAX_STATE_RESETS" in register
    assert register.count("return 0;") == 1 and register.count("return 1;") == 1
    assert "#define ECTT_MAX_STATE_RESETS 8" in RESULT_PROTOCOL_BLOCK


def test_the_per_test_state_is_the_only_harness_state_the_runtime_keeps() -> None:
    statics = re.findall(r"^static [^(\n]*?(ectt_\w+)(?:\[[^\]]*\])?\s*(?:=|;)", RESULT_PROTOCOL_BLOCK, flags=re.MULTILINE)
    assert set(statics) >= {"ectt_current_test", "ectt_current_failures", "ectt_unattributed_failures", "ectt_state_reset_count"}
    resets = _body(RESULT_PROTOCOL_BLOCK, "static void ectt_reset_test_state(void) {") + _body(
        RESULT_PROTOCOL_BLOCK, "static void ectt_finish_open_test(void) {"
    )
    assert "ectt_current_test = 0;" in resets and "ectt_current_failures = 0;" in resets


# --- integration with the generator ------------------------------------------------------------------------


def test_every_generated_harness_carries_the_protocol_before_the_hooks() -> None:
    harness = _harness()

    assert harness.has_result_protocol() and harness.has_setup_teardown()
    assert harness.source.count("ectt:result-protocol") == 1
    assert harness.source.index(RESULT_PROTOCOL_BLOCK) < harness.source.index(SETUP_TEARDOWN_BLOCK)


def test_the_generated_harness_is_still_byte_identical_across_runs() -> None:
    assert _harness().source == _harness().source


def test_the_user_hooks_are_still_registered_and_dispatched() -> None:
    for text in ("ectt_register_setup", "ectt_register_teardown", "ectt_setup_hook();", "ectt_teardown_hook();"):
        assert text in SETUP_TEARDOWN_BLOCK


def test_every_character_the_reader_splits_on_is_written_as_an_underscore() -> None:
    # The reader splits lines with str.splitlines()/str.split(), which also break on \v, \f and
    # 0x1c-0x1f; a token carrying one of them used to corrupt the field count of its line.
    match = re.search(r"one\[0\] = \(\(unsigned char\)\*text <= ' ' \|\| \(unsigned char\)\*text == (0x[0-9a-f]+)\) \? '_' : \*text;", RESULT_PROTOCOL_BLOCK)
    assert match is not None
    mapped = {value for value in range(0x80) if value <= 0x20 or value == int(match.group(1), 16)}
    splitting = {value for value in range(0x80) if chr(value).isspace() or len(("a" + chr(value) + "b").splitlines()) > 1}
    assert splitting <= mapped
    assert {ord(" "), ord("\t"), ord("\n"), ord("\r"), 0x0B, 0x0C, 0x1C} <= splitting
    assert _diagnostics(RESULT_PROTOCOL_BLOCK, "-std=c89", "-pedantic-errors", NULL_TRANSPORT) == []
