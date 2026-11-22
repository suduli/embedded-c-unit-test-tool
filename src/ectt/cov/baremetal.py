# implements: TOOL-COV-100
"""Bare-metal coverage retrieval over the console transport (CMP-COV).

Satisfies: TOOL-COV-100 — retrieve coverage data from bare-metal targets with
no filesystem and no operating system. The artifact leaves the target through
the console transport captured by the target-execution layer (ectt.ext /
ectt.exh); this package defines the console dump framing the generated
harness emits, reassembles and verifies the artifact bytes, and hands them to
the documented gcov JSON reader (WP-COV-01) or wraps them in a
:class:`ectt.cov.merge.RunCoverage` with a recorded completeness state
(TOOL-COV-180 semantics via WP-COV-02's merge). ADR-004: GCC first; there is
no C compiler on this machine, so this layer is validated against
hand-written fixtures, and real GCC output has not been checked.

Framing (console-safe; one frame per stream):

    GCOVDUMP BEGIN <name> <length-in-bytes>
    <lower-case hex payload, 64 hex chars (32 bytes) per line, last line the remainder>
    GCOVDUMP END <crc32-of-payload-as-8-hex>

Any deviation is a named error; nothing is silently repaired.
"""

from __future__ import annotations

import re
import zlib

from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import RunCoverage
from ectt.cov.model import GcovDocument

__all__ = [
    "DumpFrame",
    "parse_dump",
    "retrieve_coverage",
    "retrieve_run_coverage",
    "dump_frame",
]

_BEGIN_RE = re.compile(r"^GCOVDUMP BEGIN (\S+) (\d+)$")
_END_RE = re.compile(r"^GCOVDUMP END ([0-9a-fA-F]{8})$")
_HEX_RE = re.compile(r"^[0-9a-fA-F]*$")
_HEX_PER_LINE = 64


def dump_frame(name: str, payload: bytes) -> str:
    """Render artifact bytes in the console dump framing (the harness side).

    Provided so the harness generator (WP-GEN) and the retrieval side share one
    definition of the framing; tests use it to build fixtures.
    """
    if not name or any(char.isspace() for char in name):
        raise CoverageError(
            f"dump frame name must be a non-empty token without whitespace, got {name!r}",
            reason="invalid_frame_name",
        )
    crc = f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}"
    lines = [f"GCOVDUMP BEGIN {name} {len(payload)}"]
    hex_payload = payload.hex()
    lines.extend(hex_payload[start : start + _HEX_PER_LINE] for start in range(0, len(hex_payload), _HEX_PER_LINE))
    lines.append(f"GCOVDUMP END {crc}")
    return "\n".join(lines) + "\n"


class DumpFrame:
    """One verified dump frame: the artifact name and its bytes."""

    def __init__(self, name: str, payload: bytes) -> None:
        self.name = name
        self.payload = payload

    def __repr__(self) -> str:
        return f"DumpFrame(name={self.name!r}, payload={len(self.payload)} bytes)"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, DumpFrame) and (self.name, self.payload) == (other.name, other.payload)

    def __hash__(self) -> int:
        return hash((self.name, self.payload))


def parse_dump(stream: str) -> DumpFrame:
    """Reassemble and verify one dump frame from captured console text (TOOL-COV-100).

    Raises a named error for bad hex, length mismatch, CRC mismatch, duplicate
    frames, text outside a frame, or an unterminated (truncated) frame.
    """
    frame_name: str | None = None
    expected_length = 0
    hex_chunks: list[str] = []
    verified: DumpFrame | None = None
    saw_any_line = False
    for raw_line in stream.replace("\r\n", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        saw_any_line = True
        if verified is not None:
            raise CoverageError(
                f"console text after a completed dump frame: {line!r}",
                reason="duplicate_frame",
            )
        begin = _BEGIN_RE.match(line)
        if begin:
            if frame_name is not None:
                raise CoverageError(
                    f"duplicate GCOVDUMP BEGIN for '{begin.group(1)}' inside frame '{frame_name}'",
                    reason="duplicate_frame",
                )
            frame_name = begin.group(1)
            expected_length = int(begin.group(2))
            continue
        end = _END_RE.match(line)
        if end:
            if frame_name is None:
                raise CoverageError("GCOVDUMP END without GCOVDUMP BEGIN", reason="orphan_frame")
            payload = _verify_payload(frame_name, expected_length, hex_chunks, end.group(1))
            verified = DumpFrame(name=frame_name, payload=payload)
            frame_name = None
            continue
        if frame_name is None:
            raise CoverageError(
                f"console text outside a dump frame: {line!r}",
                reason="text_outside_frame",
            )
        if not _HEX_RE.match(line) or len(line) > _HEX_PER_LINE:
            raise CoverageError(
                f"malformed payload line in frame '{frame_name}': {line!r}",
                reason="malformed_payload",
            )
        hex_chunks.append(line.lower())
    if verified is not None:
        return verified
    if frame_name is not None:
        raise CoverageError(
            f"dump frame '{frame_name}' is unterminated (no GCOVDUMP END): the artifact is truncated",
            reason="truncated_dump",
        )
    raise CoverageError(
        "no coverage dump frame found in the captured stream" if saw_any_line else "the captured stream is empty",
        reason="no_dump_frame",
    )


def _verify_payload(
    frame_name: str,
    expected_length: int,
    hex_chunks: list[str],
    crc_field: str,
) -> bytes:
    payload = bytes.fromhex("".join(hex_chunks))
    if len(payload) != expected_length:
        raise CoverageError(
            f"dump frame '{frame_name}' declared {expected_length} bytes but carried {len(payload)}",
            reason="length_mismatch",
        )
    crc = f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}"
    if crc != crc_field.lower():
        raise CoverageError(
            f"dump frame '{frame_name}' CRC mismatch: expected {crc}, frame carries {crc_field.lower()}",
            reason="crc_mismatch",
        )
    if not payload:
        raise CoverageError(
            f"dump frame '{frame_name}' carries no payload",
            reason="malformed_payload",
        )
    return payload


def retrieve_coverage(stream: str) -> GcovDocument:
    """Retrieve a coverage document from a bare-metal console dump (TOOL-COV-100).

    The artifact may be raw JSON text, JSON bytes, or gzip-compressed bytes
    (GCC >= 14 emits gzip); decoding goes through the documented gcov reader
    from WP-COV-01.
    """
    frame = parse_dump(stream)
    return read_gcov_document(frame.payload)


def retrieve_run_coverage(
    stream: str,
    *,
    test_id: str,
    outcome: str,
) -> RunCoverage:
    """Wrap a bare-metal retrieval in a RunCoverage record (TOOL-COV-180/220).

    A verified frame yields a ``complete`` record; a truncated frame (no END
    line) yields a ``truncated`` record carrying the advisory — both flow
    through the WP-COV-02 merge's fail-closed handling unchanged. An empty
    stream yields a ``missing`` record.
    """
    if not stream.strip():
        return RunCoverage(
            test_id=test_id,
            outcome=outcome,
            completeness="missing",
            advisory="no coverage dump captured from the target",
        )
    try:
        document = retrieve_coverage(stream)
    except CoverageError as exc:
        if exc.reason == "truncated_dump":
            return RunCoverage(
                test_id=test_id,
                outcome=outcome,
                completeness="truncated",
                advisory=f"coverage dump truncated: {exc.message}",
            )
        raise
    return RunCoverage(
        test_id=test_id,
        outcome=outcome,
        completeness="complete",
        document=document,
    )
