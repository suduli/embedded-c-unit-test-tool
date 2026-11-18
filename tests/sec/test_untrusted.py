"""Tests for the WP-SEC-07 untrusted target-data boundary.

Verifies: TOOL-SEC-090.
"""

from __future__ import annotations

import pytest

from ectt.sec import mark_untrusted, parse_target_output


def test_payload_wrapper_exposes_data_accessors_only() -> None:
    """verifies: TOOL-SEC-090"""
    payload = mark_untrusted("PASS test_one\n", "uart0")
    assert payload.text() == "PASS test_one\n"
    assert payload.lines() == ("PASS test_one",)
    assert payload.length() == len("PASS test_one\n")
    assert payload.origin == "uart0"
    # No execution surface anywhere on the wrapper.
    for forbidden in ("exec", "eval", "compile", "run", "call", "system"):
        assert not hasattr(payload, forbidden)


def test_repr_is_sanitised() -> None:
    """verifies: TOOL-SEC-090"""
    payload = mark_untrusted("PASS test_one\nFAIL test_two\n", "uart0")
    rendered = repr(payload)
    assert "PASS" not in rendered
    assert "uart0" in rendered
    assert "size=" in rendered


def test_result_lines_parse_as_data() -> None:
    """verifies: TOOL-SEC-090"""
    payload = mark_untrusted(
        "PASS test_one\nFAIL test_two expected=3 actual=4\nTIMEOUT test_three\nLOG 42 cycles\n",
        "uart0",
    )
    results = parse_target_output(payload)
    assert [r.kind for r in results] == ["PASS", "FAIL", "TIMEOUT", "LOG"]
    assert results[0].test_name == "test_one"
    assert results[1].payload == "test_two expected=3 actual=4"
    assert all(r.origin == "uart0" for r in results)


def test_unparsable_lines_retained_as_data() -> None:
    """verifies: TOOL-SEC-090"""
    payload = mark_untrusted("PASS test_one\n???garbage???\n", "uart0")
    results = parse_target_output(payload)
    assert results[1].kind == "unparsed"
    assert results[1].payload == "???garbage???"


def test_code_looking_content_is_data_never_executed() -> None:
    """verifies: TOOL-SEC-090"""
    code_like = "import os; os.system('rm -rf /'); EXECUTE(everything)\n"
    payload = mark_untrusted(code_like, "semihosting")
    results = parse_target_output(payload)
    assert len(results) == 1
    assert results[0].kind == "unparsed"
    # The content is retained verbatim as data — and nothing ran.
    assert results[0].payload == code_like.strip()
    assert isinstance(results[0].payload, str)


def test_empty_lines_and_whitespace_are_data() -> None:
    """verifies: TOOL-SEC-090"""
    payload = mark_untrusted("\n\n", "uart0")
    results = parse_target_output(payload)
    assert all(r.kind == "unparsed" for r in results)


def test_parsing_is_deterministic() -> None:
    """verifies: TOOL-SEC-090"""
    raw = "PASS a\nFAIL b\nnoise\n"
    first = parse_target_output(mark_untrusted(raw, "uart0"))
    second = parse_target_output(mark_untrusted(raw, "uart0"))
    assert first == second


def test_blank_origin_rejected() -> None:
    """verifies: TOOL-SEC-090"""
    with pytest.raises(ValueError):
        mark_untrusted("PASS x\n", "   ")


def test_non_text_content_rejected_at_capture() -> None:
    """verifies: TOOL-SEC-090"""
    with pytest.raises(TypeError):
        mark_untrusted(b"\x00\x01binary", "uart0")  # type: ignore[arg-type]
