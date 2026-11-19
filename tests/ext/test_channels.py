"""Tests for the WP-EXT-03 retrieval channels and protocol.

Verifies: TOOL-TGT-050, TOOL-TGT-060.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.ext import (
    CHANNEL_SEMIHOSTING,
    CHANNEL_SERIAL_UART,
    UnknownChannelError,
    parse_channel_output,
    semihosting_channel,
    serial_uart_channel,
)


def test_documented_minimum_channels_exist() -> None:
    """verifies: TOOL-TGT-050"""
    semihosting = semihosting_channel()
    uart = serial_uart_channel()
    assert semihosting.kind == CHANNEL_SEMIHOSTING
    assert uart.kind == CHANNEL_SERIAL_UART
    assert semihosting.origin == "semihosting"
    assert uart.origin == "uart0"


def test_channels_are_frozen_and_serialisable() -> None:
    """verifies: TOOL-TGT-050"""
    channel = serial_uart_channel("uart3")
    assert channel.to_dict() == {"kind": "serial_uart", "origin": "uart3"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        channel.origin = "x"  # type: ignore[misc]


def test_unknown_channel_kind_is_named_error() -> None:
    """verifies: TOOL-TGT-050"""
    with pytest.raises(UnknownChannelError) as excinfo:
        serial_uart_channel().__class__(kind="carrier_pigeon", origin="loft")
    assert "carrier_pigeon" in str(excinfo.value)


def test_blank_origin_is_named_error() -> None:
    """verifies: TOOL-TGT-050"""
    with pytest.raises(UnknownChannelError):
        semihosting_channel("  ")


def test_protocol_is_one_way_plain_text() -> None:
    """verifies: TOOL-TGT-060"""
    channel = serial_uart_channel()
    results = parse_channel_output(
        channel,
        "PASS test_alpha\nFAIL test_beta expected=1 actual=2\nTIMEOUT test_gamma\n",
    )
    assert [r.kind for r in results] == ["PASS", "FAIL", "TIMEOUT"]
    assert results[0].test_name == "test_alpha"
    assert results[1].payload == "test_beta expected=1 actual=2"
    assert all(r.origin == "uart0" for r in results)


def test_parse_is_a_pure_function_of_the_stream() -> None:
    """verifies: TOOL-TGT-060"""
    channel = semihosting_channel()
    stream = "LOG boot\nPASS one\nnoise\nPASS one\nnoise\n"
    assert parse_channel_output(channel, stream) == parse_channel_output(channel, stream)
    # The parse API has no reply surface: it takes text and returns data.
    import inspect

    signature = inspect.signature(parse_channel_output)
    assert len(signature.parameters) == 2  # channel, output text — nothing else


def test_unparsable_content_retained_verbatim() -> None:
    """verifies: TOOL-TGT-060"""
    channel = semihosting_channel()
    results = parse_channel_output(channel, "\x1b[31mcolour codes\nPASS ok\n")
    assert results[0].kind == "unparsed"
    assert "colour codes" in results[0].payload
    assert results[1].kind == "PASS"
