"""Tests for the WP-GEN-09 stub regeneration and flagging.

Verifies: TOOL-STB-110, TOOL-STB-120, TOOL-STB-130.
"""

from __future__ import annotations

import pytest

from ectt.gen import (
    UNSUPPORTED_CONSTRUCT_MARKER,
    FunctionSignature,
    GenError,
    extract_user_body,
    flag_unsupported_constructs,
    render_stub_output,
    resync_stub,
    stub_with_user_region,
)


def _sig(
    name: str,
    *,
    return_type: str = "int",
    parameters: tuple[tuple[str, str], ...] = (),
) -> FunctionSignature:
    return FunctionSignature(name=name, return_type=return_type, parameters=parameters)


def test_stub_body_is_delimited_user_region() -> None:
    """verifies: TOOL-STB-110"""
    text = stub_with_user_region(_sig("hal_read"), "    return 42;\n")
    assert "/* ectt:stub-body: hal_read begin */" in text
    assert "/* ectt:stub-body: hal_read end */" in text
    assert "int hal_read(void) {" in text  # regenerated region
    assert extract_user_body(text, "hal_read") == "    return 42;\n"


def test_extract_missing_body_is_empty() -> None:
    """verifies: TOOL-STB-110"""
    assert extract_user_body("no regions here", "hal_read") == ""
    assert extract_user_body(
        stub_with_user_region(_sig("other")), "hal_read"
    ) == ""


def test_resync_preserves_body_when_change_permits() -> None:
    """verifies: TOOL-STB-120"""
    old = stub_with_user_region(
        _sig("hal_read", parameters=(("unsigned", "addr"),)), "    return cache[addr];\n"
    )
    result = resync_stub(old, _sig("hal_read", parameters=(("uint32_t", "addr"),)))
    assert result.body_preserved is True
    assert result.report == ()
    assert "return cache[addr];" in result.text
    assert "uint32_t addr" in result.text  # signature re-synchronised


def test_resync_reports_parameter_list_change() -> None:
    """verifies: TOOL-STB-120"""
    old = stub_with_user_region(
        _sig("hal_read", parameters=(("unsigned", "addr"),)), "    return cache[addr];\n"
    )
    result = resync_stub(old, _sig("hal_read", parameters=(("unsigned", "addr"), ("unsigned", "len"))))
    assert result.body_preserved is False
    assert any("parameter list changed" in entry for entry in result.report)
    assert "cache[addr]" not in result.text  # body regenerated


def test_resync_reports_return_type_change() -> None:
    """verifies: TOOL-STB-120"""
    old = stub_with_user_region(_sig("probe", return_type="void"), "    last = 1;\n")
    result = resync_stub(old, _sig("probe", return_type="int"))
    assert result.body_preserved is False
    assert any("not preserved" in entry for entry in result.report)


def test_resync_without_captured_body_is_reported() -> None:
    """verifies: TOOL-STB-120"""
    result = resync_stub("no regions", _sig("hal_read"))
    assert result.body_preserved is False
    assert any("no user body captured" in entry for entry in result.report)


def test_variadic_parameter_is_flagged() -> None:
    """verifies: TOOL-STB-130"""
    signatures = (
        _sig("log_msg", return_type="void", parameters=(("const char *", "fmt"), ("...", ""),)),
        _sig("hal_read"),
    )
    flagged = flag_unsupported_constructs(signatures)
    assert len(flagged) == 1
    assert flagged[0].function == "log_msg"
    assert flagged[0].reason == "variadic parameter"
    output = render_stub_output(signatures)
    assert "/* ectt:unsupported-construct: log_msg variadic parameter */" in output
    assert "int hal_read(void)" in output


def test_complex_function_pointer_parameter_is_flagged() -> None:
    """verifies: TOOL-STB-130"""
    signatures = (
        _sig(
            "register_cb",
            return_type="void",
            parameters=(("int (*handler)(int, void *)", "handler"),),
        ),
    )
    flagged = flag_unsupported_constructs(signatures)
    assert flagged[0].reason == "complex function-pointer parameter"
    output = render_stub_output(signatures)
    assert f"/* {UNSUPPORTED_CONSTRUCT_MARKER}: register_cb complex function-pointer parameter */" in output
    assert "int register_cb(" not in output  # no stub body for the flagged one


def test_handleable_constructs_never_flagged() -> None:
    """verifies: TOOL-STB-130"""
    signatures = (
        _sig("f", return_type="int", parameters=(("const char *", "s"),)),
        _sig("g", return_type="struct Point *", parameters=(("struct Point *", "p"),)),
    )
    assert flag_unsupported_constructs(signatures) == ()
    output = render_stub_output(signatures)
    assert UNSUPPORTED_CONSTRUCT_MARKER not in output


def test_resync_error_derives_from_gen_error() -> None:
    """verifies: TOOL-STB-120"""
    from ectt.gen.stubregen import StubResyncError

    assert issubclass(StubResyncError, GenError)
    with pytest.raises(GenError):
        raise StubResyncError("boom")
