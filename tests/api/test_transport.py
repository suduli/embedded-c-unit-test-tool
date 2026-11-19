"""Transport tests for the local-only engine API (WP-API-02).

Covers the SDD-002 §9.2 required interoperability fixtures (split header,
split body, concatenated frames, oversized frames) plus the DSN-API-030
no-network-listener guard and an end-to-end stdio hello negotiation.

Verifies: TOOL-UIX-050.
"""

from __future__ import annotations

import ast
import io
import pathlib
import struct

import pytest

from ectt.api.catalogue import INTERFACE_VERSION
from ectt.api.errors import ApiError
from ectt.api.transport import (
    MAX_FRAME_BYTES,
    FrameReader,
    StdioTransport,
    TransportError,
    encode_frame,
)

_LENGTH = struct.Struct(">I")


def _frame(body: bytes) -> bytes:
    return _LENGTH.pack(len(body)) + body


def test_frame_round_trip() -> None:
    """verifies: TOOL-UIX-050

    Encode → decode returns the original object.
    """
    payload = {"interface_version": INTERFACE_VERSION, "id": "17", "op": "x"}
    reader = FrameReader()
    assert reader.feed(encode_frame(payload)) == [payload]


def test_header_split_across_feeds() -> None:
    """verifies: TOOL-UIX-050 (SDD-002 §9.2 required fixture)

    A frame whose four-byte header arrives 2+2 bytes still decodes.
    """
    wire = _frame(b'{"id": "1"}')
    reader = FrameReader()
    assert reader.feed(wire[:2]) == []
    assert reader.feed(wire[2:4]) == []
    assert reader.feed(wire[4:]) == [{"id": "1"}]


def test_body_split_across_reads() -> None:
    """verifies: TOOL-UIX-050 (SDD-002 §9.2 required fixture)

    A frame body split across reads buffers until complete.
    """
    wire = _frame(b'{"id": "1", "op": "operation.cancel"}')
    reader = FrameReader()
    assert reader.feed(wire[:6]) == []
    assert reader.feed(wire[6:9]) == []
    assert reader.feed(wire[9:]) == [{"id": "1", "op": "operation.cancel"}]


def test_two_concatenated_frames_in_one_read() -> None:
    """verifies: TOOL-UIX-050 (SDD-002 §9.2 required fixture)

    Two frames in a single read yield two objects.
    """
    first = _frame(b'{"id": "17"}')
    second = _frame(b'{"id": "19"}')
    reader = FrameReader()
    assert reader.feed(first + second) == [{"id": "17"}, {"id": "19"}]


def test_oversized_frame_rejected() -> None:
    """verifies: TOOL-UIX-050 (SDD-002 §9.2 required fixture)

    A frame announcing more than MAX_FRAME_BYTES is a named rejection.
    """
    reader = FrameReader()
    with pytest.raises(TransportError) as excinfo:
        reader.feed(_LENGTH.pack(MAX_FRAME_BYTES + 1))
    assert excinfo.value.reason == "invalid_frame_length"


def test_zero_length_frame_rejected() -> None:
    """verifies: TOOL-UIX-050

    Length zero is outside the inclusive [1, MAX] bound.
    """
    reader = FrameReader()
    with pytest.raises(TransportError) as excinfo:
        reader.feed(_LENGTH.pack(0))
    assert excinfo.value.reason == "invalid_frame_length"


def test_malformed_json_in_frame_rejected() -> None:
    """verifies: TOOL-UIX-050

    A well-framed body that is not JSON is a named rejection.
    """
    reader = FrameReader()
    with pytest.raises(TransportError) as excinfo:
        reader.feed(_frame(b"{not json"))
    assert excinfo.value.reason == "malformed_json"


def test_duplicate_keys_in_frame_rejected() -> None:
    """verifies: TOOL-UIX-050

    Duplicate JSON keys are rejected inside frames too.
    """
    reader = FrameReader()
    with pytest.raises(TransportError) as excinfo:
        reader.feed(_frame(b'{"id": "1", "id": "2"}'))
    assert excinfo.value.reason == "duplicate_json_key"


def test_truncated_frame_at_eof_is_reported() -> None:
    """verifies: TOOL-UIX-050 (SDD-002 §9.2 required fixture)

    A stream ending mid-frame raises on finish() — never silently accepted.
    """
    reader = FrameReader()
    reader.feed(_frame(b'{"id": "1"}')[:-2])
    with pytest.raises(TransportError) as excinfo:
        reader.finish()
    assert excinfo.value.reason == "truncated_frame"


def test_transport_layer_never_imports_socket() -> None:
    """verifies: TOOL-UIX-050, DSN-API-030

    Structural no-network guard: no module under ``src/ectt/api`` imports the
    socket module or touches AF_INET — no network listener can exist.
    """
    api_root = pathlib.Path("src/ectt/api")
    scanned = 0
    for path in sorted(api_root.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "socket", (path, alias.name)
                    assert "asyncio" not in alias.name, (path, alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module != "socket", (path, module)
                assert "asyncio" not in module, (path, module)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert node.value != "AF_INET", path
        scanned += 1
    assert scanned >= 5  # __init__, errors, catalogue, protocol, transport


def test_stdio_round_trip_negotiates_hello_end_to_end() -> None:
    """verifies: TOOL-UIX-050

    Plain pipes only: frame bytes in → hello negotiated → reply bytes out,
    with no network involvement anywhere.
    """
    hello = {
        "bootstrap_version": "1",
        "id": "h1",
        "op": "session.hello",
        "params": {"interface_versions": [INTERFACE_VERSION]},
    }
    reader = io.BytesIO(encode_frame(hello))
    writer = io.BytesIO()
    transport = StdioTransport()
    served = transport.serve(reader, writer)
    assert served == 1
    reply_reader = FrameReader()
    (reply,) = reply_reader.feed(writer.getvalue())
    assert reply["status"] == "ok"
    assert reply["result"] == {"interface_version": INTERFACE_VERSION}


def test_stdio_transport_closes_on_protocol_violation() -> None:
    """verifies: TOOL-UIX-050 (SDD-002 §9.2 close-on-violation)

    A malformed frame terminates the serve loop with the named error.
    """
    reader = io.BytesIO(_frame(b"{not json"))
    writer = io.BytesIO()
    transport = StdioTransport()
    with pytest.raises(ApiError):
        transport.serve(reader, writer)
    assert writer.getvalue() == b""  # nothing written before the violation
