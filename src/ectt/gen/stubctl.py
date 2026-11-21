# implements: TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070
"""Stub behaviour programming and interaction recording (WP-GEN-07, DSN-GEN-110/120).

``generate_programmable_stubs`` extends the plain stubs of WP-GEN-06: each stub
gets a small, statically allocated control block and journal, and a public C API
that test code (and generated per-case setup code) uses to program and inspect it.

Behaviour (TOOL-STB-040, TOOL-STB-070), set per test case, as data:

* ``fixed``: a configured return value;
* ``sequence``: successive return values across successive calls. After the last
  value the stub keeps returning it and ``..._sequence_exhausted()`` reports 1, so
  a test can assert that the sequence was not overrun;
* ``callback``: a user-supplied function with the stub's own signature;
* output parameters: values written through non-const pointer arguments.

Recording (TOOL-STB-050, TOOL-STB-060): call count and the argument values of each
call, kept in a fixed-capacity journal (``ECTT_STUB_JOURNAL_CAPACITY``, default 16;
no dynamic allocation, so the same code runs on a bare-metal target). Calls past
the capacity are still counted and ``..._journal_overflowed()`` says so; the
journal never claims arguments it did not keep. One shared sequence counter and a
fixed-capacity order log (``ECTT_STUB_ORDER_CAPACITY``, default 64) across all stubs
back ``ectt_stub_verify_order`` (call order across stubs); an overflowed log is
never reported as verified.

Per-case configuration is generated from the case's ``StubSpec`` by
``render_stub_setup`` and ``render_stub_expectations``; behaviour is data attached to
the case, not code in the stub. Values placed into generated C are checked against a
conservative character set so an authored value cannot smuggle in statements.

A stub whose signature the control block cannot express (variadic tail, function
pointer or array parameters) is emitted as a plain default stub carrying an
``ectt:unsupported-construct`` marker and is listed in ``unsupported``; configuring
it raises instead of pretending.

Satisfies: TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from ectt.ana.model import TypeModel
from ectt.gen.errors import GenError
from ectt.gen.stubs import (
    STUB_MARKER,
    DuplicateStubError,
    FunctionSignature,
    _candidate_keys,
    _default_return,
    _required_type_declarations,
)
from ectt.tcm.datacases import StubSpec

__all__ = [
    "JOURNAL_CAPACITY_MACRO",
    "ORDER_CAPACITY_MACRO",
    "STUB_MODES",
    "UNSUPPORTED_MARKER",
    "ProgrammableStubUnit",
    "generate_programmable_stubs",
    "out_parameter_names",
    "render_stub_expectations",
    "render_stub_setup",
]

JOURNAL_CAPACITY_MACRO = "ECTT_STUB_JOURNAL_CAPACITY"
ORDER_CAPACITY_MACRO = "ECTT_STUB_ORDER_CAPACITY"
UNSUPPORTED_MARKER = "ectt:unsupported-construct"
STUB_MODES: tuple[str, ...] = ("default", "fixed", "sequence", "callback")

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SAFE_VALUE = re.compile(r"""^[A-Za-z0-9_+\-.'"()\s,*/%<>=!&|^~?:\\\[\]]*$""")
_FORBIDDEN_IN_VALUE = (";", "{", "}", "#", "/*", "//", "\n", "\r")


@dataclass(frozen=True)
class _Plan:
    """What the generator derived about one signature."""

    signature: FunctionSignature
    is_void: bool
    parameters: tuple[tuple[str, str], ...]
    outs: tuple[tuple[str, str], ...]  # (parameter name, pointee type)
    unsupported: str | None
    return_storage: str = "void"  # return type without top-level qualifiers


@dataclass(frozen=True)
class ProgrammableStubUnit:
    """Generated programmable stubs: the C source and the header for test code."""

    stub_names: tuple[str, ...]
    type_declarations: tuple[str, ...]
    source: str
    header: str
    unsupported: tuple[tuple[str, str], ...]  # (stub name, reason)


def _is_void(return_type: str) -> bool:
    return return_type.strip() == "void"


_SCALAR_WORDS = frozenset({"signed", "unsigned", "char", "short", "int", "long", "float", "double", "_Bool"})


def _is_scalar(type_text: str, types: dict[str, TypeModel] | None) -> bool:
    """True for a builtin scalar spelling or a typedef of one (resolved through ``types``)."""
    words = type_text.split()
    if words and all(w in _SCALAR_WORDS for w in words):
        return True
    if type_text == "bool":
        return True
    if types is not None:
        for key in _candidate_keys(type_text):
            model = types.get(key)
            if model is None:
                continue
            if model.kind == "typedef" and model.underlying_type:
                return _is_scalar(model.underlying_type.strip(), types)
            # the analyser's graph spells a typedef's target as ``ref:type.<id>`` and the builtin carries the C name
            if model.kind == "builtin" and model.name and model.name != type_text:
                return _is_scalar(model.name.strip(), None)
    return False


def _out_pointee(c_type: str, types: dict[str, TypeModel] | None) -> str | None:
    """Pointee type of a non-const pointer to a scalar; None when it cannot be an output.

    Only scalar pointees are supported: the stub keeps a by-value copy of the value to
    write, which needs a complete type, and a stub unit only forward-declares structs and
    unions. A struct output is written by a user callback instead.
    """
    text = c_type.strip()
    if not text.endswith("*") or "const" in text.split():
        return None
    pointee = text[:-1].strip()
    if not pointee or not _is_scalar(pointee, types):
        return None
    return pointee


_QUALIFIERS = frozenset({"const", "volatile", "restrict", "__restrict"})


def _storage_type(c_type: str) -> str:
    """``c_type`` without its top-level qualifiers (``const int`` -> ``int``, ``char *const`` -> ``char *``).

    The journal and the programmed values are stored and assigned, which a const-qualified
    object type forbids; top-level qualifiers do not change the stub's signature, so they are
    dropped from the storage typedefs only. A qualifier on the pointee (``const char *``) stays.
    """
    text = c_type.strip()
    head, star, tail = text.rpartition("*")
    kept_tail = [word for word in tail.split() if word not in _QUALIFIERS]
    if star:
        return " ".join([head.strip() + " *", *kept_tail]) if kept_tail else head.strip() + " *"
    return " ".join(kept_tail)


def _plan(signature: FunctionSignature, types: dict[str, TypeModel] | None = None) -> _Plan:
    reason: str | None = None
    for c_type, _name in signature.parameters:
        text = c_type.strip()
        if text == "...":
            reason = "variadic parameter list"
        elif "(" in text or "[" in text:
            reason = f"parameter type '{text}' is a function pointer or array"
        if reason:
            break
    named = tuple((c_type.strip(), name) for c_type, name in signature.parameters if c_type.strip() != "...")
    outs = tuple((name, pointee) for c_type, name in named if (pointee := _out_pointee(c_type, types)) is not None)
    storage = tuple((_storage_type(c_type), name) for c_type, name in named)
    return _Plan(signature, _is_void(signature.return_type), storage, outs, reason, _storage_type(signature.return_type))


def _checked_value(value: str, what: str) -> str:
    text = value.strip()
    if not text or any(token in text for token in _FORBIDDEN_IN_VALUE) or not _SAFE_VALUE.match(text):
        raise GenError(f"{what} '{value}' is not a plain C value expression", reason="unsafe_value")
    return text


def _typedefs(plan: _Plan) -> list[str]:
    name = plan.signature.name
    lines: list[str] = []
    if not plan.is_void:
        lines.append(f"typedef {plan.return_storage} ectt_stub_{name}_ret_t;")
    lines.extend(f"typedef {c_type} ectt_stub_{name}_arg_{pname}_t;" for c_type, pname in plan.parameters)
    lines.extend(f"typedef {pointee} ectt_stub_{name}_out_{pname}_t;" for pname, pointee in plan.outs)
    return lines


def _callback_type(plan: _Plan) -> str:
    name = plan.signature.name
    ret = "void" if plan.is_void else f"ectt_stub_{name}_ret_t"
    args = ", ".join(f"ectt_stub_{name}_arg_{pname}_t" for _c, pname in plan.parameters) or "void"
    return f"{ret} (*ectt_stub_{name}_callback_t)({args})"


def _declarations(plan: _Plan) -> list[str]:
    """Prototypes of the public API of one stub (the header text)."""
    name = plan.signature.name
    lines = [f"typedef {_callback_type(plan)};"]
    lines.append(f"void ectt_stub_{name}_reset(void);")
    if not plan.is_void:
        lines.append(f"void ectt_stub_{name}_set_return(ectt_stub_{name}_ret_t value);")
        lines.append(f"void ectt_stub_{name}_set_sequence(const ectt_stub_{name}_ret_t *values, unsigned count);")
        lines.append(f"int ectt_stub_{name}_sequence_exhausted(void);")
    lines.append(f"void ectt_stub_{name}_set_callback(ectt_stub_{name}_callback_t callback);")
    lines.extend(f"void ectt_stub_{name}_set_out_{pname}(ectt_stub_{name}_out_{pname}_t value);" for pname, _p in plan.outs)
    lines.append(f"unsigned ectt_stub_{name}_call_count(void);")
    lines.append(f"unsigned long ectt_stub_{name}_call_order(unsigned call_index);")
    lines.extend(f"ectt_stub_{name}_arg_{pname}_t ectt_stub_{name}_arg_{pname}(unsigned call_index);" for _c, pname in plan.parameters)
    lines.append(f"int ectt_stub_{name}_journal_overflowed(void);")
    return lines


def _definition(plan: _Plan) -> list[str]:
    name = plan.signature.name
    state = f"ectt_stub_{name}_state"
    ret = "void" if plan.is_void else f"ectt_stub_{name}_ret_t"
    # The definition names its parameters itself so a user parameter called, say,
    # ``ectt_call_index`` can never collide with the generated locals.
    local = {pname: f"ectt_arg{index}" for index, (_c, pname) in enumerate(plan.parameters)}
    params = ", ".join(f"ectt_stub_{name}_arg_{pname}_t {local[pname]}" for _c, pname in plan.parameters) or "void"
    call_args = ", ".join(local[pname] for _c, pname in plan.parameters)

    lines: list[str] = [f"/* {STUB_MARKER}: {name} */", "static struct {", "    unsigned calls;", "    int journal_overflow;", "    unsigned long order[ECTT_STUB_JOURNAL_CAPACITY];", "    int mode;"]
    lines.extend(f"    ectt_stub_{name}_arg_{pname}_t arg_{pname}[ECTT_STUB_JOURNAL_CAPACITY];" for _c, pname in plan.parameters)
    if not plan.is_void:
        lines += [f"    ectt_stub_{name}_ret_t fixed;", f"    const ectt_stub_{name}_ret_t *sequence;", "    unsigned sequence_length;", "    unsigned sequence_index;", "    int sequence_exhausted;"]
    lines.append(f"    ectt_stub_{name}_callback_t callback;")
    for pname, _pointee in plan.outs:
        lines += [f"    ectt_stub_{name}_out_{pname}_t out_{pname}_value;", f"    int out_{pname}_set;"]
    lines += [f"}} {state};", ""]

    lines += [f"void ectt_stub_{name}_reset(void) {{", f"    {state}.calls = 0;", f"    {state}.journal_overflow = 0;", f"    {state}.mode = ECTT_STUB_MODE_DEFAULT;"]
    if not plan.is_void:
        lines += [f"    {state}.sequence = 0;", f"    {state}.sequence_length = 0;", f"    {state}.sequence_index = 0;", f"    {state}.sequence_exhausted = 0;"]
    lines.append(f"    {state}.callback = 0;")
    lines.extend(f"    {state}.out_{pname}_set = 0;" for pname, _p in plan.outs)
    lines += ["}", ""]

    if not plan.is_void:
        lines += [
            f"void ectt_stub_{name}_set_return(ectt_stub_{name}_ret_t value) {{",
            f"    {state}.fixed = value;",
            f"    {state}.mode = ECTT_STUB_MODE_FIXED;",
            "}",
            "",
            f"void ectt_stub_{name}_set_sequence(const ectt_stub_{name}_ret_t *values, unsigned count) {{",
            f"    {state}.sequence = values;",
            f"    {state}.sequence_length = count;",
            f"    {state}.sequence_index = 0;",
            f"    {state}.sequence_exhausted = 0;",
            f"    {state}.mode = (values != 0 && count > 0) ? ECTT_STUB_MODE_SEQUENCE : ECTT_STUB_MODE_DEFAULT;",
            "}",
            "",
            f"int ectt_stub_{name}_sequence_exhausted(void) {{ return {state}.sequence_exhausted; }}",
            "",
        ]
    lines += [f"void ectt_stub_{name}_set_callback(ectt_stub_{name}_callback_t callback) {{", f"    {state}.callback = callback;", f"    {state}.mode = callback != 0 ? ECTT_STUB_MODE_CALLBACK : ECTT_STUB_MODE_DEFAULT;", "}", ""]
    for pname, _pointee in plan.outs:
        lines += [
            f"void ectt_stub_{name}_set_out_{pname}(ectt_stub_{name}_out_{pname}_t value) {{",
            f"    {state}.out_{pname}_value = value;",
            f"    {state}.out_{pname}_set = 1;",
            "}",
            "",
        ]
    lines += [
        f"unsigned ectt_stub_{name}_call_count(void) {{ return {state}.calls; }}",
        f"unsigned long ectt_stub_{name}_call_order(unsigned call_index) {{ return call_index < ECTT_STUB_JOURNAL_CAPACITY ? {state}.order[call_index] : 0ul; }}",
        f"int ectt_stub_{name}_journal_overflowed(void) {{ return {state}.journal_overflow; }}",
    ]
    for _c, pname in plan.parameters:
        lines.append(
            f"ectt_stub_{name}_arg_{pname}_t ectt_stub_{name}_arg_{pname}(unsigned call_index) {{ return {state}.arg_{pname}[call_index < ECTT_STUB_JOURNAL_CAPACITY ? call_index : 0]; }}"
        )
    lines.append("")

    lines += [f"{ret} {name}({params}) {{", f"    unsigned ectt_call_index = {state}.calls;", f"    {state}.calls++;", "    if (ectt_call_index < ECTT_STUB_JOURNAL_CAPACITY) {"]
    lines.extend(f"        {state}.arg_{pname}[ectt_call_index] = {local[pname]};" for _c, pname in plan.parameters)
    lines += [f'        {state}.order[ectt_call_index] = ectt_stub_next_sequence("{name}");', "    } else {", f"        {state}.journal_overflow = 1;", f'        (void)ectt_stub_next_sequence("{name}");', "    }"]
    for pname, _pointee in plan.outs:
        lines += [f"    if ({state}.out_{pname}_set && {local[pname]} != 0) {{", f"        *{local[pname]} = {state}.out_{pname}_value;", "    }"]
    if plan.is_void:
        lines += [f"    if ({state}.mode == ECTT_STUB_MODE_CALLBACK && {state}.callback != 0) {{", f"        {state}.callback({call_args});", "    }", "    return;", "}", ""]
    else:
        default = _default_return(plan.signature.return_type).strip()
        lines += [
            f"    if ({state}.mode == ECTT_STUB_MODE_CALLBACK && {state}.callback != 0) {{",
            f"        return {state}.callback({call_args});",
            "    }",
            f"    if ({state}.mode == ECTT_STUB_MODE_FIXED) {{",
            f"        return {state}.fixed;",
            "    }",
            f"    if ({state}.mode == ECTT_STUB_MODE_SEQUENCE) {{",
            f"        if ({state}.sequence_index < {state}.sequence_length) {{",
            f"            return {state}.sequence[{state}.sequence_index++];",
            "        }",
            f"        {state}.sequence_exhausted = 1;",
            f"        return {state}.sequence[{state}.sequence_length - 1u];",
            "    }",
            f"    {default}",
            "}",
            "",
        ]
    return lines


def _fallback_definition(plan: _Plan) -> list[str]:
    signature = plan.signature
    params = ", ".join(f"{c_type} {name}" if c_type.strip() != "..." else "..." for c_type, name in signature.parameters)
    return [
        f"/* {STUB_MARKER}: {signature.name} */",
        f"/* {UNSUPPORTED_MARKER}: {signature.name}: {plan.unsupported}; emitted as a default stub, not programmable */",
        f"{signature.return_type} {signature.name}({params or 'void'}) {{",
        _default_return(signature.return_type),
        "}",
        "",
    ]


_RUNTIME_DECLARATIONS = (
    "void ectt_stub_reset_all(void);",
    "int ectt_stub_verify_order(const char *const *expected, unsigned count);",
    "unsigned ectt_stub_global_call_count(void);",
    "int ectt_stub_order_overflowed(void);",
)

_RUNTIME_DEFINITIONS = f"""\
#ifndef {JOURNAL_CAPACITY_MACRO}
#define {JOURNAL_CAPACITY_MACRO} 16
#endif
#ifndef {ORDER_CAPACITY_MACRO}
#define {ORDER_CAPACITY_MACRO} 64
#endif
#define ECTT_STUB_MODE_DEFAULT 0
#define ECTT_STUB_MODE_FIXED 1
#define ECTT_STUB_MODE_SEQUENCE 2
#define ECTT_STUB_MODE_CALLBACK 3

static unsigned long ectt_stub_sequence_counter;
static const char *ectt_stub_order_log[{ORDER_CAPACITY_MACRO}];
static unsigned ectt_stub_order_count;

static unsigned long ectt_stub_next_sequence(const char *name) {{
    if (ectt_stub_order_count < {ORDER_CAPACITY_MACRO}) {{
        ectt_stub_order_log[ectt_stub_order_count] = name;
    }}
    ectt_stub_order_count++;
    ectt_stub_sequence_counter++;
    return ectt_stub_sequence_counter;
}}

static int ectt_stub_same_name(const char *a, const char *b) {{
    while (*a != 0 && *a == *b) {{
        a++;
        b++;
    }}
    return *a == *b;
}}

unsigned ectt_stub_global_call_count(void) {{ return ectt_stub_order_count; }}

int ectt_stub_order_overflowed(void) {{ return ectt_stub_order_count > {ORDER_CAPACITY_MACRO}; }}

int ectt_stub_verify_order(const char *const *expected, unsigned count) {{
    unsigned i;
    if (ectt_stub_order_count > {ORDER_CAPACITY_MACRO}) {{
        return 0;
    }}
    if (ectt_stub_order_count != count) {{
        return 0;
    }}
    for (i = 0; i < count; i++) {{
        if (!ectt_stub_same_name(ectt_stub_order_log[i], expected[i])) {{
            return 0;
        }}
    }}
    return 1;
}}
"""


def generate_programmable_stubs(
    signatures: Sequence[FunctionSignature],
    *,
    types: dict[str, TypeModel] | None = None,
) -> ProgrammableStubUnit:
    """Generate programmable, recording stubs for ``signatures``, deterministically ordered."""
    seen: set[str] = set()
    for signature in signatures:
        if not _IDENTIFIER.match(signature.name):
            raise GenError(f"stub function name '{signature.name}' is not a C identifier", reason="invalid_signature")
        if signature.name in seen:
            raise DuplicateStubError(f"two stubs would be generated for '{signature.name}'")
        seen.add(signature.name)
        for _c_type, pname in signature.parameters:
            if pname and not _IDENTIFIER.match(pname):
                raise GenError(f"stub '{signature.name}' parameter name '{pname}' is not a C identifier", reason="invalid_signature")
    ordered = tuple(sorted(signatures, key=lambda s: s.name))
    plans = [_plan(s, types) for s in ordered]
    type_declarations = _required_type_declarations(ordered, types)

    supported = [p for p in plans if p.unsupported is None]
    declarations: list[str] = list(type_declarations)
    for plan in supported:
        declarations += _typedefs(plan) + _declarations(plan)
    declarations += list(_RUNTIME_DECLARATIONS)

    header = "\n".join(
        ["/* Generated by ectt - do not edit. Programmable stub API for test code. */", "#ifndef ECTT_STUBS_H", "#define ECTT_STUBS_H", "", *declarations, "", "#endif", ""]
    )

    body: list[str] = ["/* Generated by ectt - do not edit. Programmable stubs for external functions. */", "", *declarations, "", _RUNTIME_DEFINITIONS]
    for plan in plans:
        body += _fallback_definition(plan) if plan.unsupported else _definition(plan)
    reset = ["void ectt_stub_reset_all(void) {", "    unsigned i;", "    ectt_stub_sequence_counter = 0;", "    ectt_stub_order_count = 0;", f"    for (i = 0; i < {ORDER_CAPACITY_MACRO}; i++) {{", "        ectt_stub_order_log[i] = 0;", "    }"]
    reset.extend(f"    ectt_stub_{p.signature.name}_reset();" for p in supported)
    reset += ["}", ""]
    body += reset

    return ProgrammableStubUnit(
        stub_names=tuple(p.signature.name for p in plans),
        type_declarations=type_declarations,
        source="\n".join(body),
        header=header,
        unsupported=tuple((p.signature.name, p.unsupported) for p in plans if p.unsupported is not None),
    )


def out_parameter_names(signature: FunctionSignature, *, types: dict[str, TypeModel] | None = None) -> tuple[str, ...]:
    """Parameters of ``signature`` that can carry output values (non-const pointers to scalars)."""
    return tuple(name for name, _pointee in _plan(signature, types).outs)


def render_stub_setup(
    signature: FunctionSignature,
    spec: StubSpec,
    *,
    types: dict[str, TypeModel] | None = None,
) -> tuple[str, ...]:
    """C statements that program one stub from a case's ``StubSpec`` (TOOL-STB-040, TOOL-STB-070).

    Modes: ``default`` (nothing), ``fixed`` (one return value), ``sequence`` (one or
    more), ``callback`` (the callback's name is the single entry of ``returns``).
    Output-parameter values come from ``out_parameters``.
    """
    plan = _plan(signature, types)
    if spec.name != signature.name:
        raise GenError(f"stub spec '{spec.name}' does not belong to '{signature.name}'", reason="spec_mismatch")
    if plan.unsupported is not None:
        raise GenError(
            f"stub '{signature.name}' is not programmable: {plan.unsupported}",
            reason="stub_not_programmable",
        )
    name = signature.name
    mode = spec.mode.strip() or "default"
    if mode not in STUB_MODES:
        raise GenError(f"stub '{name}' has unknown mode '{spec.mode}' (expected one of {', '.join(STUB_MODES)})", reason="unknown_stub_mode")

    lines: list[str] = [f"ectt_stub_{name}_reset();"]
    if mode in ("fixed", "sequence") and plan.is_void:
        raise GenError(f"stub '{name}' returns void; a {mode} return value cannot be configured", reason="void_return_value")
    if mode == "fixed":
        if len(spec.returns) != 1:
            raise GenError(f"stub '{name}' mode fixed needs exactly one return value", reason="invalid_returns")
        lines.append(f"ectt_stub_{name}_set_return({_checked_value(spec.returns[0], f'stub {name} return value')});")
    elif mode == "sequence":
        if not spec.returns:
            raise GenError(f"stub '{name}' mode sequence needs at least one return value", reason="invalid_returns")
        values = ", ".join(_checked_value(v, f"stub {name} return value") for v in spec.returns)
        lines += [
            "{",
            f"    static const ectt_stub_{name}_ret_t ectt_sequence[] = {{{values}}};",
            f"    ectt_stub_{name}_set_sequence(ectt_sequence, {len(spec.returns)}u);",
            "}",
        ]
    elif mode == "callback":
        if len(spec.returns) != 1 or not _IDENTIFIER.match(spec.returns[0].strip()):
            raise GenError(f"stub '{name}' mode callback needs the callback's C name as its single entry", reason="invalid_callback")
        lines.append(f"ectt_stub_{name}_set_callback({spec.returns[0].strip()});")

    out_names = {pname for pname, _pointee in plan.outs}
    for pname in sorted(spec.out_parameters):
        if pname not in out_names:
            raise GenError(
                f"stub '{name}' has no output parameter '{pname}' (scalar output parameters: {', '.join(sorted(out_names)) or 'none'}; struct outputs need a callback)",
                reason="unknown_out_parameter",
            )
        lines.append(f"ectt_stub_{name}_set_out_{pname}({_checked_value(spec.out_parameters[pname], f'stub {name} output value')});")
    return tuple(lines)


def render_stub_expectations(signature: FunctionSignature, spec: StubSpec) -> tuple[str, ...]:
    """C boolean expressions a harness evaluates after the run (TOOL-STB-050).

    Currently the expected call count (``StubSpec.expect_calls``); empty when none is set.
    """
    if spec.name != signature.name:
        raise GenError(f"stub spec '{spec.name}' does not belong to '{signature.name}'", reason="spec_mismatch")
    if _plan(signature).unsupported is not None:
        raise GenError(f"stub '{signature.name}' is not programmable: {_plan(signature).unsupported}", reason="stub_not_programmable")
    if spec.expect_calls is None:
        return ()
    if not spec.expect_calls.isdigit():
        raise GenError(f"stub '{signature.name}' expect_calls '{spec.expect_calls}' is not a non-negative integer", reason="invalid_expect_calls")
    return (f"ectt_stub_{signature.name}_call_count() == {int(spec.expect_calls)}u",)
