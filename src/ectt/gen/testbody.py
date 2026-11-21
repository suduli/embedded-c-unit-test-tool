# implements: TOOL-STB-040, TOOL-STB-050, TOOL-TCD-090
"""Per-case test bodies: stub programming, expectation checks, protocol markers (A2).

Wires the WP-GEN-07 stub API (``render_stub_setup`` and
``render_stub_expectations``) into the per-case C a harness runs, and wires the
checks into the RESULT/FAILURE stream (``ectt.gen.protocol``):

* every case becomes one generated function that opens the test
  (``ectt_begin_test``), programs its stubs (the ``render_stub_setup`` lines),
  runs the case body (a caller slot — rendering the UUT call itself is
  CMP-GEN, not this module), evaluates its expectations (the
  ``render_stub_expectations`` expressions; a failed one is reported through
  ``ectt_fail`` with the expected and the *actual* call count, and so reaches
  the host runner as a FAILURE record) and closes the test
  (``ectt_end_test``);
* ``ectt_stub_reset_all`` is registered as a state reset exactly once through
  the protocol's ``ectt_register_state_reset``; the generated registration
  function guards itself, so a back-end may call it from a per-test setup
  without registering the same reset twice.

Unity runs the case functions directly from ``run_all_tests``; cmocka needs
``void **state`` wrappers, so the cmocka glue renders them. Everything here is
deterministic: identical inputs give byte-identical text. There is no C
compiler here: correctness is verified by parsing the composed C with libclang
and by string-level golden tests, and the expectation-failure line shape is
derived from the C and fed to the real host reader (``ectt.exh.runner``).

Satisfies: TOOL-STB-040, TOOL-STB-050, TOOL-TCD-090.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ectt.ana.model import TypeModel
from ectt.gen.errors import GenError
from ectt.gen.stubctl import render_stub_expectations, render_stub_setup
from ectt.gen.stubs import FunctionSignature
from ectt.tcm.datacases import StubSpec

__all__ = [
    "GENERATED_FILE_TOKEN",
    "STATE_RESET_REGISTRATION_NAME",
    "CaseSections",
    "StubbedCase",
    "TestCaseRender",
    "case_render",
    "render_back_end_sections",
    "render_case_functions",
    "render_harness_interface_header",
    "render_state_reset_registration",
]

#: The file token reported for generated expectation failures: the check is
#: generated, not user-authored, so it names no user file.
GENERATED_FILE_TOKEN = "ectt-generated"

#: Name of the generated function that registers the stub state reset.
STATE_RESET_REGISTRATION_NAME = "ectt_register_generated_resets"

_CALL_COUNT_RE = re.compile(r"^ectt_stub_(\w+)_call_count\(\) == (\d+)u$")
#: A case id may travel into a C string literal and a function name; keep the
#: character set closed so no escaping is ever needed.
_SAFE_CASE_ID = re.compile(r"^[A-Za-z0-9_.\-]{1,64}$")


@dataclass(frozen=True)
class StubbedCase:
    """One test case and the stub behaviour attached to it."""

    case_id: str
    stubs: tuple[StubSpec, ...] = ()


@dataclass(frozen=True)
class TestCaseRender:
    """The rendered pieces of one case, before they are shaped into C."""

    __test__ = False  # a render record, not a pytest test class

    case_id: str
    setup_lines: tuple[str, ...]
    expectation_expressions: tuple[str, ...]
    call_lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class CaseSections:
    """The two C texts a back-end template needs for a set of cases.

    ``case_section`` goes at file scope before the framework entry points;
    ``test_invocations`` fills the template's ``{test_invocations}`` slot.
    """

    case_section: str
    test_invocations: str


def _c_string_literal(text: str, what: str) -> str:
    if not _SAFE_CASE_ID.match(text):
        raise GenError(
            f"{what} {text!r} is not safe for generated C (allowed: letters, digits, '_', '.', '-'; max 64)",
            reason="unsafe_case_id",
        )
    return f'"{text}"'


def _assigned_names(renders: tuple[TestCaseRender, ...]) -> tuple[tuple[TestCaseRender, str], ...]:
    """The one deterministic case-id -> function-name mapping for all renderers.

    Every renderer must use this mapping so a case is named identically in its
    definition and in every invocation; two case ids that map to one name are
    refused instead of silently merged.
    """
    taken: set[str] = set()
    assigned: list[tuple[TestCaseRender, str]] = []
    for render in renders:
        if not _SAFE_CASE_ID.match(render.case_id):
            raise GenError(
                f"case id {render.case_id!r} is not safe for generated C "
                "(allowed: letters, digits, '_', '.', '-'; max 64)",
                reason="unsafe_case_id",
            )
        name = "ectt_case_" + re.sub(r"[^A-Za-z0-9_]", "_", render.case_id)
        if name in taken:
            raise GenError(
                f"two case ids map to the generated function name '{name}'",
                reason="duplicate_case_function",
            )
        taken.add(name)
        assigned.append((render, name))
    return tuple(assigned)


def case_render(
    case: StubbedCase,
    signatures: dict[str, FunctionSignature],
    *,
    types: dict[str, TypeModel] | None = None,
    call_lines: tuple[str, ...] = (),
) -> TestCaseRender:
    """Render one case's stub programming and expectation checks.

    ``signatures`` maps stub function names to their signatures; every stub
    spec must name one of them (the stub unit must be generated for the same
    set). Setup lines come from ``render_stub_setup`` and expectation
    expressions from ``render_stub_expectations`` — the WP-GEN-07 semantics,
    not a re-implementation.
    """
    setup: list[str] = []
    expressions: list[str] = []
    for spec in case.stubs:
        signature = signatures.get(spec.name)
        if signature is None:
            raise GenError(
                f"case '{case.case_id}' programs stub '{spec.name}', which is not in the stub set",
                reason="unknown_stub",
            )
        setup.extend(render_stub_setup(signature, spec, types=types))
        expressions.extend(render_stub_expectations(signature, spec))
    return TestCaseRender(
        case_id=case.case_id,
        setup_lines=tuple(setup),
        expectation_expressions=tuple(expressions),
        call_lines=tuple(call_lines),
    )


def render_state_reset_registration(stubbed: bool) -> tuple[str, ...]:
    """The generated function registering ``ectt_stub_reset_all`` as a state reset.

    Called once per suite by the back-ends; the guard makes it safe if a
    back-end calls it from a per-test setup instead. Without stubs there is
    nothing to register and nothing is emitted.
    """
    if not stubbed:
        return ()
    return (
        f"static void {STATE_RESET_REGISTRATION_NAME}(void)",
        "{",
        "    static unsigned ectt_generated_resets_done = 0;",
        "    if (ectt_generated_resets_done) { return; }",
        "    ectt_generated_resets_done = 1;",
        "    ectt_register_state_reset(ectt_stub_reset_all);",
        "}",
    )


def render_case_functions(
    renders: tuple[TestCaseRender, ...],
    *,
    stubbed: bool,
) -> str:
    """Shape the rendered cases into the per-case C section of a harness.

    Deterministic: cases keep input order, one ``static`` function per case
    plus (when stubs are generated) the state-reset registration function.
    A failed expectation is reported through ``ectt_fail`` with the expected
    and the actual call count; ``ectt_number_token`` (protocol block) renders
    the number as a protocol token, so the host reader gets a real FAILURE
    record, not a lost check.
    """
    lines: list[str] = ["/* ectt:generated-cases - one function per case; do not edit. */"]
    lines.extend(render_state_reset_registration(stubbed))
    for render, name in _assigned_names(renders):
        literal = _c_string_literal(render.case_id, "case id")
        lines.append("")
        lines.append(f"static void {name}(void)")
        lines.append("{")
        lines.append(f"    ectt_begin_test({literal});")
        lines.extend(f"    {line}" for line in render.setup_lines)
        lines.extend(f"    {line}" for line in render.call_lines)
        for expression in render.expectation_expressions:
            match = _CALL_COUNT_RE.match(expression)
            if match is None:
                raise GenError(
                    f"expectation expression is not a generated call-count check: {expression!r}",
                    reason="unexpected_expectation",
                )
            stub_name, expected = match.group(1), match.group(2)
            count_call = f"ectt_stub_{stub_name}_call_count()"
            lines.append(f"    if (!({expression})) {{")
            lines.append(
                f'        ectt_fail("{stub_name}_expect_calls", "{expected}", '
                f"ectt_number_token({count_call}), "
                f'"{GENERATED_FILE_TOKEN}", 1u);'
            )
            lines.append("    }")
        lines.append("    ectt_end_test();")
        lines.append("}")
    lines.append("")
    return "\n".join(lines)


def render_harness_interface_header(stubbed: bool) -> str:
    """The ``ectt_harness.h`` the generated translation units share.

    The framework back-end file includes this header (the templates say so);
    it declares the protocol API the per-case functions call, the setup/teardown
    entry points the framework hooks call, and — when stubs are generated —
    the programmable-stub header. Without it the back-end output cannot parse
    or link against the harness translation unit.
    """
    lines = [
        "/* ectt_harness.h - shared interface of the generated harness units. */",
        "#ifndef ECTT_HARNESS_H",
        "#define ECTT_HARNESS_H",
        "",
    ]
    if stubbed:
        lines += ['#include "ectt_stubs.h"', ""]
    lines += [
        "void ectt_begin_test(const char *test_id);",
        "void ectt_fail(const char *assertion, const char *expected, const char *actual,",
        "               const char *file, unsigned line);",
        "void ectt_end_test(void);",
        "int ectt_register_state_reset(void (*fn)(void));",
        "const char *ectt_number_token(unsigned long value);",
        "void ectt_run_setup(void);",
        "void ectt_run_teardown(void);",
        "",
        "#endif",
        "",
    ]
    return "\n".join(lines)


def render_back_end_sections(
    renders: tuple[TestCaseRender, ...],
    *,
    backend_id: str,
    stubbed: bool,
) -> CaseSections:
    """The per-case C section and the ``{test_invocations}`` body for one back-end.

    Unity runs the case functions directly from ``run_all_tests``, after
    registering the state resets once. cmocka test functions take
    ``void **state``, so the glue renders one wrapper per case and lists them
    as ``cmocka_unit_test`` entries.
    """
    core = render_case_functions(renders, stubbed=stubbed)
    assigned = _assigned_names(renders)
    if not renders:
        return CaseSections(case_section="", test_invocations="")
    if backend_id == "unity":
        invocations = [f"    {STATE_RESET_REGISTRATION_NAME}();"]
        invocations.extend(f"    {name}();" for _render, name in assigned)
        return CaseSections(case_section=core, test_invocations="\n".join(invocations))
    if backend_id == "cmocka":
        wrappers: list[str] = []
        entries: list[str] = []
        for _render, name in assigned:
            wrapper = name.replace("ectt_case_", "ectt_cmocka_", 1)
            wrappers.append(f"static void {wrapper}(void **state)")
            wrappers.append("{")
            wrappers.append("    (void)state;")
            wrappers.append(f"    {name}();")
            wrappers.append("}")
            entries.append(f"    cmocka_unit_test({wrapper}),")
        return CaseSections(
            case_section=core + "\n" + "\n".join(wrappers) + "\n",
            test_invocations="\n".join(entries),
        )
    raise GenError(
        f"no per-case rendering is defined for back-end '{backend_id}'",
        reason="unsupported_backend_for_cases",
    )
