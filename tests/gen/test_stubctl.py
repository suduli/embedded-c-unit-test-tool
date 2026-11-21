# implements: TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070
"""Stub behaviour programming and interaction recording (WP-GEN-07).

Verifies: TOOL-STB-040 (fixed value, sequence, callback), TOOL-STB-050 (call count
and per-call arguments), TOOL-STB-060 (call order across stubs), TOOL-STB-070
(output parameters). No C compiler is available to the test suite, so generated C
is checked by parsing it with libclang (the project's own frontend) and requiring no
error diagnostics, plus structural assertions on the text.
"""

from __future__ import annotations

import re

import pytest

from ectt.ana.frontend import parse
from ectt.ana.model import TypeModel
from ectt.gen import FunctionSignature as Sig
from ectt.gen.errors import GenError
from ectt.gen.stubctl import (
    JOURNAL_CAPACITY_MACRO,
    ORDER_CAPACITY_MACRO,
    UNSUPPORTED_MARKER,
    generate_programmable_stubs,
    out_parameter_names,
    render_stub_expectations,
    render_stub_setup,
)
from ectt.tcm.datacases import StubSpec

SIGS = (
    Sig("hal_read", "int", (("unsigned char", "channel"), ("int *", "value"), ("const char *", "label"))),
    Sig("hal_write", "void", (("unsigned char", "channel"), ("unsigned long long", "payload"))),
    Sig("hal_tick", "void"),
    Sig("hal_name", "char *", (("void *", "context"),)),
    Sig("hal_pair", "unsigned long long", (("int *", "first"), ("short *", "second"))),
)


def _errors(source: str) -> list[str]:
    parsed = parse("probe.c", args=["-std=c99"], unsaved_files=[("probe.c", source)])
    assert parsed.status == "parsed"
    return [f"{d.severity}: {d.message}" for d in parsed.diagnostics if d.severity in ("error", "fatal")]


def _spec(name: str, mode: str = "default", returns: tuple[str, ...] = (), **kw: object) -> StubSpec:
    return StubSpec(name=name, mode=mode, returns=returns, **kw)  # type: ignore[arg-type]


UNIT = generate_programmable_stubs(SIGS)


# --- the generated C is valid ---------------------------------------------------------------


def test_generated_source_has_no_compile_errors() -> None:
    assert _errors(UNIT.source) == []


def test_header_alone_parses_and_declares_the_api() -> None:
    assert _errors(UNIT.header) == []
    for name in ("hal_read", "hal_write", "hal_tick", "hal_name", "hal_pair"):
        assert f"ectt_stub_{name}_call_count" in UNIT.header
    assert UNIT.header.count("#ifndef ECTT_STUBS_H") == 1 and UNIT.header.rstrip().endswith("#endif")


def test_header_has_declarations_only() -> None:
    assert "static " not in UNIT.header and "{" not in UNIT.header.replace("typedef", "")


def test_source_and_header_agree_so_test_code_links_against_the_stubs() -> None:
    combined = UNIT.header + "\n" + UNIT.source.split("\n", 2)[2]
    assert _errors(combined) == []


def test_struct_and_typedef_parameters_compile_with_their_declarations() -> None:
    types = {
        "type.Frame": TypeModel(kind="struct", name="Frame"),
        "type.u16": TypeModel(kind="typedef", name="u16", underlying_type="unsigned short"),
    }
    sigs = (Sig("send", "int", (("struct Frame *", "frame"), ("u16", "length"), ("u16 *", "sent"))),)

    unit = generate_programmable_stubs(sigs, types=types)

    assert "typedef unsigned short u16;" in unit.source
    assert _errors(unit.source) == []
    assert _errors(unit.header) == []


def test_only_scalar_pointees_can_be_outputs_because_structs_are_only_forward_declared() -> None:
    """Regression: a struct output kept as a by-value copy needs a complete type the stub unit lacks."""
    types = {
        "type.Frame": TypeModel(kind="struct", name="Frame"),
        "type.u16": TypeModel(kind="typedef", name="u16", underlying_type="unsigned short"),
        "type.Alias": TypeModel(kind="typedef", name="Alias", underlying_type="struct Frame"),
    }
    sig = Sig("send", "int", (("struct Frame *", "frame"), ("u16 *", "sent"), ("Alias *", "alias"), ("unsigned long *", "big"), ("bool *", "ok")))

    assert out_parameter_names(sig, types=types) == ("sent", "big", "ok")
    assert out_parameter_names(sig) == ("big", "ok")  # without the type graph a typedef is not assumed scalar
    with pytest.raises(GenError) as excinfo:
        render_stub_setup(sig, _spec("send", out_parameters={"frame": "0"}), types=types)
    assert excinfo.value.reason == "unknown_out_parameter"
    assert "struct outputs need a callback" in excinfo.value.message


def test_no_dynamic_allocation_and_capacities_are_overridable_macros() -> None:
    for banned in ("malloc", "calloc", "realloc", "free("):
        assert banned not in UNIT.source
    assert f"#ifndef {JOURNAL_CAPACITY_MACRO}" in UNIT.source
    assert f"#ifndef {ORDER_CAPACITY_MACRO}" in UNIT.source
    assert "ECTT_STUB_JOURNAL_CAPACITY 16" in UNIT.source and "ECTT_STUB_ORDER_CAPACITY 64" in UNIT.source


# --- the API per behaviour -------------------------------------------------------------------


def test_non_void_stubs_get_return_programming_and_void_stubs_do_not() -> None:
    for api in ("set_return", "set_sequence", "sequence_exhausted"):
        assert f"ectt_stub_hal_read_{api}" in UNIT.header
        assert f"ectt_stub_hal_write_{api}" not in UNIT.header
        assert f"ectt_stub_hal_tick_{api}" not in UNIT.header


def test_every_stub_can_take_a_callback_with_its_own_signature() -> None:
    assert re.search(r"typedef ectt_stub_hal_read_ret_t \(\*ectt_stub_hal_read_callback_t\)\(ectt_stub_hal_read_arg_channel_t, ectt_stub_hal_read_arg_value_t, ectt_stub_hal_read_arg_label_t\);", UNIT.header)
    assert "typedef void (*ectt_stub_hal_tick_callback_t)(void);" in UNIT.header
    assert "ectt_stub_hal_tick_set_callback" in UNIT.header


def test_output_parameters_exist_only_for_writable_non_void_pointers() -> None:
    assert out_parameter_names(SIGS[0]) == ("value",)  # int * yes, const char * no
    assert out_parameter_names(SIGS[3]) == ()  # void * cannot be written through
    assert out_parameter_names(SIGS[4]) == ("first", "second")
    assert "ectt_stub_hal_read_set_out_value" in UNIT.header
    assert "ectt_stub_hal_read_set_out_label" not in UNIT.header
    assert "ectt_stub_hal_name_set_out_context" not in UNIT.header


def test_the_stub_writes_the_output_value_through_the_pointer_when_programmed() -> None:
    assert "*ectt_arg1 = ectt_stub_hal_read_state.out_value_value;" in UNIT.source
    assert "if (ectt_stub_hal_read_state.out_value_set && ectt_arg1 != 0)" in UNIT.source


def test_sequence_mode_keeps_the_last_value_and_flags_exhaustion() -> None:
    assert "sequence_exhausted = 1;" in UNIT.source
    assert "sequence[ectt_stub_hal_read_state.sequence_length - 1u]" in UNIT.source


# --- recording ---------------------------------------------------------------------------------


def test_every_call_is_counted_and_every_argument_recorded() -> None:
    for index, parameter in enumerate(("channel", "value", "label")):
        assert f"ectt_stub_hal_read_arg_{parameter}(unsigned call_index)" in UNIT.source
        assert f"ectt_stub_hal_read_state.arg_{parameter}[ectt_call_index] = ectt_arg{index};" in UNIT.source
    assert "ectt_stub_hal_read_call_count(void)" in UNIT.source
    assert "ectt_stub_hal_tick_state.calls++;" in UNIT.source


def test_calls_beyond_the_journal_are_counted_and_flagged_not_dropped_silently() -> None:
    assert "journal_overflow = 1;" in UNIT.source
    assert "ectt_stub_hal_read_journal_overflowed" in UNIT.header
    assert "state.calls++" in UNIT.source  # the count continues past the capacity


def test_argument_reads_are_bounds_safe() -> None:
    assert "call_index < ECTT_STUB_JOURNAL_CAPACITY ? call_index : 0" in UNIT.source


# --- call order across stubs ---------------------------------------------------------------------


def test_one_shared_sequence_counter_orders_calls_across_stubs() -> None:
    assert UNIT.source.count("ectt_stub_next_sequence(") >= 2 * len(SIGS)  # each stub, both branches
    assert "static unsigned long ectt_stub_sequence_counter;" in UNIT.source
    assert "ectt_stub_verify_order" in UNIT.header and "ectt_stub_global_call_count" in UNIT.header


def test_an_overflowed_order_log_is_never_reported_as_verified() -> None:
    body = UNIT.source.split("int ectt_stub_verify_order(const char *const *expected, unsigned count) {", 1)[1].split("return 1;", 1)[0]
    assert "ectt_stub_order_count > ECTT_STUB_ORDER_CAPACITY" in body
    assert "return 0;" in body


def test_reset_all_resets_the_runtime_and_every_programmable_stub() -> None:
    reset = UNIT.source.split("void ectt_stub_reset_all(void) {", 1)[1]
    for name in ("hal_read", "hal_write", "hal_tick", "hal_name", "hal_pair"):
        assert f"ectt_stub_{name}_reset();" in reset
    assert "ectt_stub_order_count = 0;" in reset and "ectt_stub_sequence_counter = 0;" in reset


# --- unsupported signatures ------------------------------------------------------------------------


def test_signatures_the_control_block_cannot_express_are_flagged_not_pretended() -> None:
    sigs = (
        Sig("va", "int", (("const char *", "fmt"), ("...", ""))),
        Sig("fp", "int", (("void (*)(int)", "cb"),)),
        Sig("arr", "int", (("int[4]", "values"),)),
        Sig("ok", "int", (("int", "x"),)),
    )

    unit = generate_programmable_stubs(sigs)

    assert [name for name, _ in unit.unsupported] == ["arr", "fp", "va"]
    assert unit.source.count(UNSUPPORTED_MARKER) == 3
    assert "ectt_stub_ok_set_return" in unit.header
    for name in ("va", "fp", "arr"):
        assert f"ectt_stub_{name}_" not in unit.header


def test_configuring_an_unsupported_stub_raises() -> None:
    sig = Sig("va", "int", (("const char *", "fmt"), ("...", "")))
    for call in (render_stub_setup, render_stub_expectations):
        with pytest.raises(GenError) as excinfo:
            call(sig, _spec("va"))
        assert excinfo.value.reason == "stub_not_programmable"


# --- per-case setup from a StubSpec ---------------------------------------------------------------------


def _setup_compiles(signature: Sig, spec: StubSpec) -> tuple[str, ...]:
    lines = render_stub_setup(signature, spec)
    source = UNIT.source + "\nint hal_cb(unsigned char c, int *v, const char *l) { return c; }\nvoid ectt_case_setup(void) {\n" + "\n".join(lines) + "\n}\n"
    assert _errors(source) == []
    return lines


def test_fixed_return_value_setup() -> None:
    lines = _setup_compiles(SIGS[0], _spec("hal_read", "fixed", ("42",)))
    assert lines == ("ectt_stub_hal_read_reset();", "ectt_stub_hal_read_set_return(42);")


def test_sequence_setup_lists_every_value_in_order() -> None:
    lines = _setup_compiles(SIGS[0], _spec("hal_read", "sequence", ("1", "2", "-3")))
    assert any("{1, 2, -3}" in line for line in lines)
    assert any("set_sequence(ectt_sequence, 3u)" in line for line in lines)


def test_callback_setup_names_the_users_function() -> None:
    lines = _setup_compiles(SIGS[0], _spec("hal_read", "callback", ("hal_cb",)))
    assert lines[-1] == "ectt_stub_hal_read_set_callback(hal_cb);"


def test_output_parameter_setup_is_sorted_and_combines_with_a_return_mode() -> None:
    spec = _spec("hal_pair", "fixed", ("7",), out_parameters={"second": "9", "first": "8"})
    lines = render_stub_setup(SIGS[4], spec)
    source = UNIT.source + "\nvoid ectt_case_setup(void) {\n" + "\n".join(lines) + "\n}\n"

    assert _errors(source) == []
    assert lines == (
        "ectt_stub_hal_pair_reset();",
        "ectt_stub_hal_pair_set_return(7);",
        "ectt_stub_hal_pair_set_out_first(8);",
        "ectt_stub_hal_pair_set_out_second(9);",
    )


def test_default_mode_only_resets_and_a_void_stub_takes_outputs_and_callbacks() -> None:
    assert render_stub_setup(SIGS[2], _spec("hal_tick")) == ("ectt_stub_hal_tick_reset();",)
    assert render_stub_setup(SIGS[2], _spec("hal_tick", "")) == ("ectt_stub_hal_tick_reset();",)


@pytest.mark.parametrize("value", ["-1", "0x10", "'a'", "3.5f", "(char *)0", "A_CONSTANT", "1 << 4", '"text"'])
def test_plain_c_values_are_accepted(value: str) -> None:
    assert render_stub_setup(SIGS[0], _spec("hal_read", "fixed", (value,)))[-1].endswith(f"({value});")


@pytest.mark.parametrize("value", ["1; system(\"x\")", "0 }", "{0}", "#define X 1", "1 /* c */", "1 // c", "1\n2", "", "  ", "a`b"])
def test_values_that_could_carry_statements_are_refused(value: str) -> None:
    with pytest.raises(GenError) as excinfo:
        render_stub_setup(SIGS[0], _spec("hal_read", "fixed", (value,)))
    assert excinfo.value.reason == "unsafe_value"


def test_output_values_are_checked_too() -> None:
    with pytest.raises(GenError) as excinfo:
        render_stub_setup(SIGS[0], _spec("hal_read", out_parameters={"value": "1; boom()"}))
    assert excinfo.value.reason == "unsafe_value"


@pytest.mark.parametrize(
    ("sig_index", "spec", "reason"),
    [
        (0, _spec("hal_read", "wiggle"), "unknown_stub_mode"),
        (0, _spec("hal_read", "fixed"), "invalid_returns"),
        (0, _spec("hal_read", "fixed", ("1", "2")), "invalid_returns"),
        (0, _spec("hal_read", "sequence"), "invalid_returns"),
        (2, _spec("hal_tick", "fixed", ("1",)), "void_return_value"),
        (2, _spec("hal_tick", "sequence", ("1",)), "void_return_value"),
        (0, _spec("hal_read", "callback", ("not an id",)), "invalid_callback"),
        (0, _spec("hal_read", "callback"), "invalid_callback"),
        (0, _spec("hal_read", out_parameters={"label": "1"}), "unknown_out_parameter"),
        (0, _spec("hal_read", out_parameters={"nope": "1"}), "unknown_out_parameter"),
        (0, _spec("hal_write"), "spec_mismatch"),
    ],
)
def test_bad_stub_specs_are_refused_with_a_reason(sig_index: int, spec: StubSpec, reason: str) -> None:
    with pytest.raises(GenError) as excinfo:
        render_stub_setup(SIGS[sig_index], spec)
    assert excinfo.value.reason == reason


# --- expectations --------------------------------------------------------------------------------------------


def test_expected_call_count_becomes_a_c_expression() -> None:
    assert render_stub_expectations(SIGS[0], _spec("hal_read", expect_calls="3")) == ("ectt_stub_hal_read_call_count() == 3u",)
    assert render_stub_expectations(SIGS[0], _spec("hal_read", expect_calls="0")) == ("ectt_stub_hal_read_call_count() == 0u",)
    assert render_stub_expectations(SIGS[0], _spec("hal_read")) == ()


def test_expectations_refuse_a_bad_count_or_a_foreign_spec() -> None:
    with pytest.raises(GenError) as bad:
        render_stub_expectations(SIGS[0], _spec("hal_read", expect_calls="many"))
    assert bad.value.reason == "invalid_expect_calls"
    with pytest.raises(GenError) as foreign:
        render_stub_expectations(SIGS[0], _spec("hal_write"))
    assert foreign.value.reason == "spec_mismatch"


# --- determinism and input validation ---------------------------------------------------------------------------


def test_output_is_deterministic_and_independent_of_input_order() -> None:
    assert generate_programmable_stubs(tuple(reversed(SIGS))) == UNIT
    assert generate_programmable_stubs(SIGS) == UNIT
    assert UNIT.stub_names == tuple(sorted(UNIT.stub_names))


def test_stub_names_and_parameter_names_must_be_c_identifiers() -> None:
    for sig in (Sig("not valid", "int"), Sig("f", "int", (("int", "bad name"),)), Sig("1f", "int")):
        with pytest.raises(GenError) as excinfo:
            generate_programmable_stubs((sig,))
        assert excinfo.value.reason == "invalid_signature"


def test_duplicate_stub_names_are_refused() -> None:
    with pytest.raises(GenError) as excinfo:
        generate_programmable_stubs((Sig("f", "int"), Sig("f", "void")))
    assert excinfo.value.reason == "duplicate_stub"


def test_an_empty_list_yields_a_valid_runtime_only_unit() -> None:
    unit = generate_programmable_stubs(())
    assert unit.stub_names == () and unit.unsupported == ()
    assert _errors(unit.source) == []
    assert _errors(unit.header) == []


def test_default_returns_are_kept_when_nothing_is_programmed() -> None:
    assert "return 0; /* ectt:stub: default value */" in UNIT.source
    assert "return (char *)0; /* ectt:stub: default value */" in UNIT.source


# --- review-fix: qualifiers and name collisions in the generated C ----------------------------


@pytest.mark.parametrize(
    ("return_type", "parameters"),
    [
        ("int", (("const int", "x"),)),
        ("int", (("char *const", "x"),)),
        ("const int", ()),
        ("int", (("volatile int", "v"), ("unsigned char *const", "p"))),
    ],
)
def test_top_level_qualifiers_do_not_make_the_journal_or_value_storage_const(return_type: str, parameters: tuple[tuple[str, str], ...]) -> None:
    # The journal arrays and the programmed return value are assigned to; a const object type would not compile.
    unit = generate_programmable_stubs((Sig("probe_fn", return_type, parameters),))

    assert _errors(unit.source) == []
    assert "const int ectt_stub_probe_fn" not in unit.source.replace("typedef const int", "")


def test_a_pointee_qualifier_is_kept_in_the_storage_type() -> None:
    unit = generate_programmable_stubs((Sig("probe_fn", "const char *", (("const char *", "text"),)),))

    assert "typedef const char * ectt_stub_probe_fn_arg_text_t;" in unit.source
    assert "typedef const char * ectt_stub_probe_fn_ret_t;" in unit.source
    assert _errors(unit.source) == []


@pytest.mark.parametrize("pname", ["ectt_call_index", "ectt_arg0", "ectt_arg1", "calls", "mode"])
def test_a_parameter_named_like_a_generated_identifier_still_compiles(pname: str) -> None:
    unit = generate_programmable_stubs((Sig("probe_fn", "int", (("int", "first"), ("int *", pname))),))

    assert _errors(unit.source) == []


def test_a_typedef_of_a_scalar_is_an_output_parameter_in_the_analysers_own_type_graph_shape() -> None:
    # The analyser spells a typedef's target as 'ref:type.<id>' and the builtin carries the C name.
    types = {
        "type.unsigned_char": TypeModel(kind="builtin", name="unsigned char"),
        "type.u8": TypeModel(kind="typedef", name="u8", underlying_type="ref:type.unsigned_char"),
        "type.u8b": TypeModel(kind="typedef", name="u8b", underlying_type="ref:type.u8"),
        "type.struct.X": TypeModel(kind="struct", name="X"),
        "type.X": TypeModel(kind="typedef", name="X", underlying_type="ref:type.struct.X"),
    }
    signature = Sig("probe_fn", "void", (("u8 *", "p"), ("u8b *", "q"), ("X *", "r")))

    assert out_parameter_names(signature, types=types) == ("p", "q")
