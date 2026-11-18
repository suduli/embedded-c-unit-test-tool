"""Local-only transport for the ectt engine API (WP-API-02).

TOOL-UIX-050: front-ends operate against a local engine instance and require
no network access. DSN-API-030 (SDD-001 §4.4): no TCP listener is offered —
this module therefore carries no socket import at all; the transport surface
is stdio (plain pipes).

Framing is SDD-002 §9.2: a four-byte unsigned big-endian payload length
followed by exactly that many UTF-8 bytes containing one JSON object (no
BOM). Length is 1-8,388,608 bytes inclusive. Readers buffer partial
headers/bodies and accept several frames per read; duplicate JSON keys,
malformed UTF-8/JSON, oversized and zero-length frames are rejected; a frame
truncated at EOF is reported, never silently accepted.

Satisfies: TOOL-UIX-050.
Design: SDD-001 §4.4 (DSN-API-030), SDD-002 §9.1/§9.2.
"""

from __future__ import annotations

import json
import struct
from collections.abc import Callable
from typing import BinaryIO

from ectt.api.catalogue import BOOTSTRAP_VERSION
from ectt.api.errors import ApiError
from ectt.api.protocol import Session, parse_payload_strict

__all__ = [
    "MAX_FRAME_BYTES",
    "MIN_FRAME_BYTES",
    "FrameReader",
    "StdioTransport",
    "TransportError",
    "encode_frame",
]

#: SDD-002 §9.2 frame length bounds, inclusive.
MIN_FRAME_BYTES = 1
MAX_FRAME_BYTES = 8_388_608

_LENGTH_STRUCT = struct.Struct(">I")


class TransportError(ApiError):
    """Raised for framing and transport-layer violations (SDD-002 §9.2)."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "transport_error",
    ) -> None:
        super().__init__(message, reason=reason)


def encode_frame(payload: dict[str, object]) -> bytes:
    """Encode one length-prefixed frame for a JSON object payload."""
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    if not MIN_FRAME_BYTES <= len(body) <= MAX_FRAME_BYTES:
        raise TransportError(
            f"frame body length {len(body)} outside [{MIN_FRAME_BYTES}, {MAX_FRAME_BYTES}]",
            reason="invalid_frame_length",
        )
    return _LENGTH_STRUCT.pack(len(body)) + body


class FrameReader:
    """Incremental frame decoder over an arbitrary byte stream.

    Accepts bytes split at arbitrary boundaries (including inside the
    four-byte header) and several concatenated frames per read.
    """

    def __init__(self) -> None:
        self._buffer = b""

    def feed(self, data: bytes) -> list[dict[str, object]]:
        """Consume ``data``, returning every complete frame's JSON object."""
        self._buffer += data
        frames: list[dict[str, object]] = []
        while True:
            if len(self._buffer) < _LENGTH_STRUCT.size:
                return frames
            (length,) = _LENGTH_STRUCT.unpack_from(self._buffer, 0)
            if not MIN_FRAME_BYTES <= length <= MAX_FRAME_BYTES:
                raise TransportError(
                    f"announced frame length {length} outside "
                    f"[{MIN_FRAME_BYTES}, {MAX_FRAME_BYTES}]",
                    reason="invalid_frame_length",
                )
            if len(self._buffer) < _LENGTH_STRUCT.size + length:
                return frames
            body = self._buffer[_LENGTH_STRUCT.size : _LENGTH_STRUCT.size + length]
            self._buffer = self._buffer[_LENGTH_STRUCT.size + length :]
            try:
                frames.append(parse_payload_strict(body))
            except ApiError as exc:
                raise TransportError(str(exc), reason=exc.reason) from exc
            except UnicodeDecodeError as exc:
                raise TransportError(
                    f"frame body is not valid UTF-8: {exc}",
                    reason="malformed_frame",
                ) from None

    def finish(self) -> None:
        """Raise if a partial frame remains at end of stream (SDD-002 §9.2:
        truncated frame at EOF closes the connection, never accepted)."""
        if self._buffer:
            raise TransportError(
                f"stream ended mid-frame with {len(self._buffer)} buffered bytes",
                reason="truncated_frame",
            )


class StdioTransport:
    """Serve the engine protocol over plain stdio pipes (no network)."""

    def __init__(self, session: Session | None = None) -> None:
        self._session = session if session is not None else Session()

    def serve(
        self,
        reader: BinaryIO,
        writer: BinaryIO,
        operation_handler: Callable[[Session, dict[str, object]], dict[str, object]] | None = None,
        *,
        max_frames: int = 64,
    ) -> int:
        """Read frames from ``reader``, reply on ``writer``, return frame count.

        Each payload is dispatched through ``session.hello`` for the bootstrap
        envelope or through ``operation_handler`` afterwards. A transport
        error (oversized, malformed, truncated) terminates the loop — matching
        SDD-002 §9.2's close-on-violation rule.
        """
        frame_reader = FrameReader()
        served = 0
        while served < max_frames:
            chunk = reader.read(4096)
            if not chunk:
                frame_reader.finish()
                return served
            for payload in frame_reader.feed(chunk):
                self._dispatch(payload, writer, operation_handler)
                served += 1
        frame_reader.finish()
        return served

    def _dispatch(
        self,
        payload: dict[str, object],
        writer: BinaryIO,
        operation_handler: Callable[[Session, dict[str, object]], dict[str, object]] | None,
    ) -> None:
        if payload.get("op") == "session.hello" and payload.get("bootstrap_version") == BOOTSTRAP_VERSION:
            reply = self._session.hello(payload)
        elif operation_handler is None:
            raise TransportError(
                "no operation handler wired for this transport",
                reason="no_operation_handler",
            )
        else:
            request, error = self._session.handle_request(payload)
            if error is not None:
                reply = error
            else:
                reply = operation_handler(self._session, request)  # type: ignore[arg-type]
        writer.write(encode_frame(reply))
