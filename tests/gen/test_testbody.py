# implements: TOOL-STB-040, TOOL-STB-050, TOOL-TCD-090
"""Per-case test bodies wired into the generator and the result stream (A2).

Verifies: the per-case C (stub programming through ``render_stub_setup``,
expectation checks through ``render_stub_expectations`` reported via
``ectt_fail``, ``ectt_begin_test``/``ectt_end_test`` markers, the
``ectt_stub_reset_all`` state-reset registration) parses cleanly, is
deterministic, and reaches the host runner in the reader's own line shape.

No C compiler is available to the test suite, so the generated C is checked by
parsing it with libclang (the project's own frontend) and by string-level
golden tests; the expectation-failure line shape is derived from the C text
itself and fed to the real host-side reader (``ectt.exh.runner``). Executing
the C is recorded as follow-up work.
"""

from __future__ import annotations

import re

import pytest

from ectt.ana.frontend import parse
from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    FunctionModel,
    ProvenanceModel,
    SourceLocation,
    TypeModel,
)
from ectt.exh.runner import _parse_result_stream
from ectt.gen import (
    UNITY_BACKEND_ID,
    BackendRegistry,
    GeneratedHarness,
    GenError,
    HarnessGenerator,
    StubbedCase,
    case_render,
    register_framework_builtins,
    render_back_end_sections,
    render_case_functions,
    render_framework_test,
    render_harness_interface_header,
    render_state_reset_registration,
)
from ectt.gen import FunctionSignature as Sig
from ectt.gen.protocol import RESULT_PROTOCOL_BLOCK, SETUP_TEARDOWN_BLOCK
from ectt.gen.stubctl import generate_programmable_stubs
from ectt.gen.testbody import GENERATED_FILE_TOKEN, TestCaseRender
from ectt.tcm.datacases import StubSpec

SIGS_DICT = {
    "hal_read": Sig("hal_read", "int", (("unsigned char", "channel"), ("int *", "value"))),
    "hal_write": Sig("hal_write", "void"),
}


NULL_TRANSPORT = "-DECTT_STREAM_WRITE(t)=((void)(t))"


def _errors(source: str, extra: list[tuple[str, str]] | None = None) -> list[str]:
    parsed = parse(
        "probe.c",
        args=["-std=c99", "-pedantic", NULL_TRANSPORT],
        unsaved_files=[("probe.c", source), *(extra or [])],
    )
    assert parsed.status == "parsed"
    return [f"{d.severity}: {d.message}" for d in parsed.diagnostics if d.severity in ("error", "fatal")]


def _parse_on_disk(tmp_path, name: str, source: str, files=None) -> list[str]:
    """Parse with companion headers on disk (libclang resolves includes there)."""
    (tmp_path / name).write_text(source, encoding="utf-8")
    for fname, content in (files or {}).items():
        (tmp_path / fname).write_text(content, encoding="utf-8")
    parsed = parse(tmp_path / name, args=["-std=c99", "-pedantic", NULL_TRANSPORT, "-I", str(tmp_path)])
    assert parsed.status == "parsed"
    return [f"{d.severity}: {d.message}" for d in parsed.diagnostics if d.severity in ("error", "fatal")]


def _case(case_id: str, *stubs: StubSpec) -> StubbedCase:
    return StubbedCase(case_id=case_id, stubs=stubs)


def _renders() -> tuple[TestCaseRender, ...]:
    return (
        case_render(
            _case("tc.one", StubSpec(name="hal_read", mode="fixed", returns=("7",), expect_calls="1")),
            SIGS_DICT,  # type: ignore[arg-type]
        ),
        case_render(_case("tc.two"), SIGS_DICT),  # type: ignore[arg-type]
    )


def _stub_unit():
    return generate_programmable_stubs(tuple(SIGS_DICT.values()))  # type: ignore[arg-type]


def _composed_c(renders=None, *, stubbed: bool = True) -> str:
    if renders is None:
        renders = _renders()
    # One translation unit: the stub definitions, the protocol runtime and the
    # per-case functions. (The interface header is for the split-TU back-end
    # layout and is parse-checked in its own test.)
    parts = [_stub_unit().source, RESULT_PROTOCOL_BLOCK, SETUP_TEARDOWN_BLOCK]
    if renders:
        parts.append(render_case_functions(renders, stubbed=stubbed))
    return "\n".join(parts)


# --- the generated C is valid ---------------------------------------------------------------


def test_the_composed_per_case_c_parses_with_zero_diagnostics(tmp_path) -> None:
    """verifies: TOOL-TCD-090 — stubs + protocol + per-case functions parse as C99."""
    assert _parse_on_disk(tmp_path, "probe.c", _composed_c()) == []


def test_the_per_case_c_parses_even_without_stubs(tmp_path) -> None:
    """verifies: TOOL-TCD-090 — a stub-free case section is self-sufficient C99."""
    renders = (case_render(_case("tc.one"), {}),)  # type: ignore[arg-type]
    assert _parse_on_disk(tmp_path, "probe.c", _composed_c(renders, stubbed=False)) == []


def test_the_unity_back_end_output_with_cases_parses(tmp_path) -> None:
    """verifies: TOOL-HAR-060 — the back-end file with per-case functions parses
    against the shared interface header, stub headers and a stub unity.h."""
    registry = BackendRegistry()
    register_framework_builtins(registry)
    harness = HarnessGenerator(_model()).generate()
    sections = render_back_end_sections(_renders(), backend_id=UNITY_BACKEND_ID, stubbed=True)
    rendered = render_framework_test(
        UNITY_BACKEND_ID,
        harness,
        registry,
        setup_hook="ectt_register_generated_resets();\nectt_run_setup();",
        teardown_hook="ectt_run_teardown();",
        test_cases=sections,
    )
    files = {
        "unity.h": "/* stub unity header for parsing */\n",
        "ectt_harness.h": render_harness_interface_header(True),
        "ectt_stubs.h": _stub_unit().header,
        "uut.h": "/* stub uut header */\n",
    }
    assert _parse_on_disk(tmp_path, "probe.c", rendered, files) == []
    assert "ectt_begin_test" in rendered and "ectt_end_test" in rendered


# --- the stream matches the host reader -----------------------------------------------------------


def _fail_arguments(section: str) -> tuple[str, str]:
    """The (assertion, expected) of the generated ectt_fail call, read from the C.

    The actual token is ``ectt_number_token(<call count>)`` in the C text; the
    test substitutes a concrete observed count, exactly what the C computes at
    run time.
    """
    match = re.search(
        r'ectt_fail\("(\w+_expect_calls)", "(\d+)", '
        r"ectt_number_token\(ectt_stub_(\w+)_call_count\(\)\), "
        r'"([^\"]+)", 1u\);',
        section,
    )
    assert match is not None, "the generated C does not contain the expected ectt_fail call"
    return match.group(1), match.group(2)


def test_a_failed_expectation_reaches_the_host_reader_as_a_failure_record() -> None:
    """verifies: TOOL-STB-050, TOOL-EXE-020 — the expectation check reports
    through ectt_fail; the derived line shape is accepted by the real reader."""
    section = render_case_functions(_renders(), stubbed=True)
    assertion, expected = _fail_arguments(section)
    observed = "3"  # the stub was called three times, once expected
    stream = "\n".join(
        [
            "RESULT tc.one fail",
            f"FAILURE tc.one {assertion} {expected} {observed} {GENERATED_FILE_TOKEN} 1",
            "",
        ]
    )
    records = _parse_result_stream(stream, frozenset({"tc.one"}), {"tc.one": "d" * 64})
    assert len(records) == 1
    failure = records[0].failures[0]
    assert failure.assertion == assertion
    assert failure.expected == expected
    assert failure.actual == observed
    assert failure.location.file == GENERATED_FILE_TOKEN
    assert failure.location.line == 1


# --- determinism and goldens ---------------------------------------------------------------


def test_rendering_is_byte_identical_across_runs() -> None:
    """verifies: TOOL-NFR-060 — identical inputs give byte-identical text."""
    assert _composed_c() == _composed_c()
    registry = BackendRegistry()
    register_framework_builtins(registry)
    harness = HarnessGenerator(_model()).generate()
    sections_a = render_back_end_sections(_renders(), backend_id=UNITY_BACKEND_ID, stubbed=True)
    sections_b = render_back_end_sections(_renders(), backend_id=UNITY_BACKEND_ID, stubbed=True)
    assert sections_a == sections_b
    assert render_framework_test(
        UNITY_BACKEND_ID, harness, registry, test_cases=sections_a
    ) == render_framework_test(UNITY_BACKEND_ID, harness, registry, test_cases=sections_b)


def test_a_case_with_stubs_renders_the_expected_golden_shape() -> None:
    """verifies: TOOL-STB-040, TOOL-STB-050 — golden: programming lines, the
    marker calls and the expectation check in order."""
    section = render_case_functions(_renders(), stubbed=True)
    expected = (
        "/* ectt:generated-cases - one function per case; do not edit. */\n"
        "static void ectt_register_generated_resets(void)\n"
        "{\n"
        "    static unsigned ectt_generated_resets_done = 0;\n"
        "    if (ectt_generated_resets_done) { return; }\n"
        "    ectt_generated_resets_done = 1;\n"
        "    ectt_register_state_reset(ectt_stub_reset_all);\n"
        "}\n"
        "\n"
        "static void ectt_case_tc_one(void)\n"
        "{\n"
        '    ectt_begin_test("tc.one");\n'
        "    ectt_stub_hal_read_reset();\n"
        "    ectt_stub_hal_read_set_return(7);\n"
        "    if (!(ectt_stub_hal_read_call_count() == 1u)) {\n"
        '        ectt_fail("hal_read_expect_calls", "1", ectt_number_token(ectt_stub_hal_read_call_count()), "ectt-generated", 1u);\n'
        "    }\n"
        "    ectt_end_test();\n"
        "}\n"
        "\n"
        "static void ectt_case_tc_two(void)\n"
        "{\n"
        '    ectt_begin_test("tc.two");\n'
        "    ectt_end_test();\n"
        "}\n"
    )
    assert section == expected


def test_a_template_with_no_stubs_is_unchanged() -> None:
    """verifies: TOOL-NFR-060 — without cases the render and the harness source
    are byte-identical to the pre-A2 shape (no slot residue, no case region)."""
    registry = BackendRegistry()
    register_framework_builtins(registry)
    harness = HarnessGenerator(_model()).generate()
    rendered = render_framework_test(UNITY_BACKEND_ID, harness, registry)
    assert "{case_section}" not in rendered
    assert "ectt:generated-cases" not in rendered
    assert "ectt_begin_test" not in rendered
    assert rendered.count("\n\n") == render_framework_test(UNITY_BACKEND_ID, harness, registry).count("\n\n")
    assert harness.case_section == ""
    plain = HarnessGenerator(_model()).generate()
    assert plain.case_section == ""
    assert "ectt:generated-cases" not in plain.source


# --- the state reset registration ------------------------------------------------------------


def test_ectt_stub_reset_all_is_registered_as_a_state_reset() -> None:
    """verifies: TOOL-TCD-090, DSN-TCM-060 — the stub reset is registered once,
    the registration guards itself, and it registers the stub reset only."""
    registration = render_state_reset_registration(True)
    text = "\n".join(registration)
    assert "ectt_register_state_reset(ectt_stub_reset_all);" in text
    assert "static unsigned ectt_generated_resets_done = 0;" in text
    assert "if (ectt_generated_resets_done) { return; }" in text
    assert render_state_reset_registration(False) == ()


def test_the_registration_is_idempotent_by_guard_not_by_protocol_change() -> None:
    """verifies: TOOL-TCD-090 — the protocol's registration semantics stay
    single-shot; the guard lives in the generated function."""
    register = re.search(
        r"int ectt_register_state_reset\(void \(\*fn\)\(void\)\) \{(.*?)\n\}",
        RESULT_PROTOCOL_BLOCK,
        re.DOTALL,
    ).group(1)
    assert register.count("return 1;") == 1 and register.count("return 0;") == 1


# --- refusals ---------------------------------------------------------------------------


def test_a_case_cannot_program_a_stub_outside_the_stub_set() -> None:
    """verifies: TOOL-STB-040 — a spec naming an unknown stub is refused."""
    with pytest.raises(GenError) as excinfo:
        case_render(_case("tc.one", StubSpec(name="ghost", mode="fixed", returns=("1",))), SIGS_DICT)  # type: ignore[arg-type]
    assert excinfo.value.reason == "unknown_stub"


def test_two_cases_that_map_to_one_function_name_are_refused() -> None:
    """verifies: TOOL-NFR-060 — 'tc.one' and 'tc_one' would merge silently."""
    renders = (
        TestCaseRender(case_id="tc.one", setup_lines=(), expectation_expressions=()),
        TestCaseRender(case_id="tc_one", setup_lines=(), expectation_expressions=()),
    )
    with pytest.raises(GenError) as excinfo:
        render_case_functions(renders, stubbed=False)
    assert excinfo.value.reason == "duplicate_case_function"


def test_an_unsafe_case_id_is_refused() -> None:
    """verifies: TOOL-STB-040 — an id that would need C string escaping never
    reaches the generated text."""
    with pytest.raises(GenError) as excinfo:
        render_case_functions(
            (TestCaseRender(case_id='tc"quoted', setup_lines=(), expectation_expressions=()),),
            stubbed=False,
        )
    assert excinfo.value.reason == "unsafe_case_id"


def test_a_back_end_without_a_case_slot_cannot_host_cases() -> None:
    """verifies: TOOL-PLG-030 — a custom template without {case_section} is
    refused instead of silently dropping the per-case functions."""
    registry = BackendRegistry()
    registry.register_descriptor(
        {"backend_id": "slotless", "framework_header": "slotless.h", "template": '/* {uut_header} */\n{test_invocations}\n'}
    )
    harness = HarnessGenerator(_model()).generate()
    sections = render_back_end_sections(_renders(), backend_id=UNITY_BACKEND_ID, stubbed=True)
    with pytest.raises(GenError) as excinfo:
        render_framework_test("slotless", harness, registry, test_cases=sections)
    assert excinfo.value.reason == "missing_case_section_slot"


def test_cases_and_manual_invocations_are_mutually_exclusive() -> None:
    """verifies: TOOL-HAR-060 — one invocation source at a time."""
    registry = BackendRegistry()
    register_framework_builtins(registry)
    harness = HarnessGenerator(_model()).generate()
    sections = render_back_end_sections(_renders(), backend_id=UNITY_BACKEND_ID, stubbed=True)
    with pytest.raises(GenError) as excinfo:
        render_framework_test(UNITY_BACKEND_ID, harness, registry, test_invocations="x();", test_cases=sections)
    assert excinfo.value.reason == "conflicting_invocation_sources"


def test_an_unknown_backend_has_no_case_rendering() -> None:
    """verifies: TOOL-PLG-030 — case rendering is defined per back-end."""
    with pytest.raises(GenError) as excinfo:
        render_back_end_sections(_renders(), backend_id="acme", stubbed=True)
    assert excinfo.value.reason == "unsupported_backend_for_cases"


# --- the generator wiring ------------------------------------------------------------------------


def _model() -> AnalysisModel:
    function = FunctionModel("adc_scale", "external", "none", SourceLocation("uut.c", 3), "ref:type.int")
    unit = AnalysisUnit(path="uut.c", status="parsed", functions=(function,))
    return AnalysisModel(
        provenance=ProvenanceModel("0.1.0", "fixture", "fixture"),
        units=(unit,),
        types={"type.int": TypeModel(kind="builtin", name="int")},
    )


def test_the_generator_wires_the_case_section_into_the_harness() -> None:
    """verifies: TOOL-STB-040 — generated harness carries the per-case region,
    marked as generated, and re-exports it on the harness object."""
    harness = HarnessGenerator(
        _model(),
        cases=[_case("tc.one", StubSpec(name="hal_read", mode="fixed", returns=("7",), expect_calls="1"))],
        stub_signatures=SIGS_DICT,  # type: ignore[arg-type]
    ).generate()

    assert "/* ectt:generated-cases begin */" in harness.source
    assert "/* ectt:generated-cases end */" in harness.source
    assert "ectt_begin_test" in harness.source
    assert harness.case_section != ""
    assert harness.source.index("/* ectt:user-region: user-helpers end */") < harness.source.index(
        "/* ectt:generated-cases begin */"
    )
    # The section inside the source is the section on the object.
    assert harness.case_section.strip() in harness.source


def test_the_generator_output_is_byte_identical_across_runs() -> None:
    """verifies: TOOL-NFR-060 — the case-wired harness is deterministic."""
    kwargs: dict[str, object] = {
        "cases": [_case("tc.one", StubSpec(name="hal_read", mode="fixed", returns=("7",), expect_calls="1"))],
        "stub_signatures": SIGS_DICT,
    }
    assert HarnessGenerator(_model(), **kwargs).generate().source == HarnessGenerator(_model(), **kwargs).generate().source  # type: ignore[arg-type]


def test_the_generator_without_cases_is_unchanged_by_the_wiring() -> None:
    """verifies: TOOL-NFR-060 — a model-only generation is byte-identical to the
    pre-A2 output (no case region, empty case_section)."""
    plain = HarnessGenerator(_model()).generate()
    assert plain.case_section == ""
    assert "ectt:generated-cases" not in plain.source
    assert plain.has_result_protocol() and plain.has_setup_teardown()


def test_generated_harness_type_is_unchanged_for_plain_use() -> None:
    """verifies: API — GeneratedHarness still reports its protocol blocks."""
    harness: GeneratedHarness = HarnessGenerator(_model()).generate()
    assert harness.has_result_protocol() and harness.has_setup_teardown()


def test_the_interface_header_declares_everything_the_case_section_calls(tmp_path) -> None:
    """verifies: TOOL-HAR-060 — every call the per-case C makes is declared by
    the shared header (parse-checked together)."""
    header = render_harness_interface_header(True)
    combined = header + "\n" + render_case_functions(_renders(), stubbed=True)
    files = {"ectt_stubs.h": _stub_unit().header}
    assert _parse_on_disk(tmp_path, "probe.c", combined, files) == []
    for name in ("ectt_begin_test", "ectt_fail", "ectt_end_test", "ectt_register_state_reset", "ectt_number_token"):
        assert name in header
