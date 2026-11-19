"""Tests for the WP-GEN-06 stub generation core.

Verifies: TOOL-STB-010, TOOL-STB-020, TOOL-STB-030.
"""

from __future__ import annotations

import pytest

from ectt.ana.model import TypeModel
from ectt.gen import (
    STUB_MARKER,
    DuplicateStubError,
    FunctionSignature,
    GenError,
    generate_stubs,
)


def _sig(
    name: str,
    *,
    return_type: str = "int",
    parameters: tuple[tuple[str, str], ...] = (),
) -> FunctionSignature:
    return FunctionSignature(name=name, return_type=return_type, parameters=parameters)


def test_stub_for_every_external_function() -> None:
    """verifies: TOOL-STB-010"""
    unit = generate_stubs((_sig("memset"), _sig("driver_write")))
    assert [stub.signature.name for stub in unit.stubs] == ["driver_write", "memset"]
    assert len(unit.stubs) == 2


def test_empty_external_list_yields_empty_unit() -> None:
    """verifies: TOOL-STB-010"""
    unit = generate_stubs(())
    assert unit.stubs == ()
    assert unit.source  # header still emitted


def test_duplicate_stub_name_is_named_error() -> None:
    """verifies: TOOL-STB-010"""
    with pytest.raises(DuplicateStubError):
        generate_stubs((_sig("memset"), _sig("memset")))


def test_stub_signature_identical_to_replaced_function() -> None:
    """verifies: TOOL-STB-020"""
    signature = _sig(
        "hal_transfer",
        return_type="unsigned",
        parameters=(("const char *", "buffer"), ("unsigned", "length")),
    )
    unit = generate_stubs((signature,))
    assert unit.signature_texts() == ("unsigned hal_transfer(const char * buffer, unsigned length)",)
    assert "unsigned hal_transfer(const char * buffer, unsigned length)" in unit.stubs[0].c_text
    assert "void hal_transfer(void)" not in unit.source


def test_void_stub_renders_void_parameter_list() -> None:
    """verifies: TOOL-STB-020"""
    unit = generate_stubs((_sig("kick_watchdog", return_type="void"),))
    assert "void kick_watchdog(void)" in unit.source


def test_stub_bodies_carry_marker_and_default_return() -> None:
    """verifies: TOOL-STB-010"""
    unit = generate_stubs(
        (
            _sig("read_reg", return_type="int", parameters=(("unsigned", "addr"),)),
            _sig("kick", return_type="void"),
        )
    )
    assert unit.source.count(STUB_MARKER) == 2
    by_name = {stub.signature.name: stub.c_text for stub in unit.stubs}
    assert "return 0;" in by_name["read_reg"]
    assert "return;" in by_name["kick"]


def test_pointer_and_float_returns_get_cast_defaults() -> None:
    """verifies: TOOL-STB-030"""
    unit = generate_stubs(
        (
            _sig("get_buffer", return_type="void *"),
            _sig("get_ratio", return_type="float"),
        )
    )
    assert "return (void *)0;" in unit.source
    assert "return 0.0f;" in unit.source


def test_struct_type_declarations_collected() -> None:
    """verifies: TOOL-STB-030"""
    types = {
        "type.struct.Frame": TypeModel(kind="struct", name="Frame"),
        "type.enum.State": TypeModel(kind="enum", name="State"),
    }
    unit = generate_stubs(
        (
            _sig(
                "push_frame",
                return_type="void",
                parameters=(("struct Frame", "frame"),),
            ),
            _sig("get_state", return_type="enum State"),
            _sig("len_of", return_type="unsigned", parameters=(("const char *", "s"),)),
        ),
        types=types,
    )
    assert "typedef struct Frame Frame;" in unit.type_declarations
    # enum return handled via cast default; enum typedef emitted only when
    # the ref resolves through the type graph.
    assert "return (enum State)0;" in unit.source


def test_builtin_and_pointer_types_need_no_declarations() -> None:
    """verifies: TOOL-STB-030"""
    unit = generate_stubs(
        (
            _sig("f", return_type="int", parameters=(("const char *", "s"),)),
        ),
        types={"type.int": TypeModel(kind="builtin", name="int")},
    )
    assert unit.type_declarations == ()


def test_output_is_deterministic() -> None:
    """verifies: TOOL-STB-010"""
    signatures = (_sig("memset"), _sig("alpha"), _sig("zulu"))
    first = generate_stubs(signatures)
    second = generate_stubs(signatures)
    assert first.source == second.source
    assert [s.signature.name for s in first.stubs] == ["alpha", "memset", "zulu"]


def test_malformed_signature_is_named_error() -> None:
    """verifies: TOOL-STB-020"""
    with pytest.raises(GenError):
        FunctionSignature(name="", return_type="int")
    with pytest.raises(GenError):
        FunctionSignature(name="x", return_type="int", parameters=(("int", "  "),))
