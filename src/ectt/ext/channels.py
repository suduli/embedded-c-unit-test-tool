"""Result retrieval channels and the plain-text protocol (WP-EXT-03).

Retrieval channels are declarative descriptors for the documented minimum set
(semihosting, serial/UART), each labelling the origin for the WP-SEC-07
untrusted boundary. The protocol is plain-text and line-oriented: parsing is
a pure function of one input string — no bidirectional channel exists in the
API surface.

Satisfies: TOOL-TGT-050, TOOL-TGT-060.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.ext.errors import ExtError
from ectt.sec import TargetResultLine, mark_untrusted, parse_target_output

__all__ = [
    "CHANNEL_SEMIHOSTING",
    "CHANNEL_SERIAL_UART",
    "RetrievalChannel",
    "UnknownChannelError",
    "semihosting_channel",
    "serial_uart_channel",
    "parse_channel_output",
]

CHANNEL_SEMIHOSTING = "semihosting"
CHANNEL_SERIAL_UART = "serial_uart"


class UnknownChannelError(ExtError):
    """Raised when a retrieval channel kind is unknown or malformed."""

    def __init__(self, message: str, *, reason: str = "unknown_channel") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class RetrievalChannel:
    """One declarative result-retrieval channel."""

    kind: str
    origin: str

    def __post_init__(self) -> None:
        if self.kind not in (CHANNEL_SEMIHOSTING, CHANNEL_SERIAL_UART):
            raise UnknownChannelError(
                f"retrieval channel '{self.kind}' is outside the documented set "
                f"({CHANNEL_SEMIHOSTING}, {CHANNEL_SERIAL_UART})"
            )
        if not self.origin.strip():
            raise UnknownChannelError(
                f"channel '{self.kind}' requires a non-empty origin label"
            )

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {"kind": self.kind, "origin": self.origin}


def semihosting_channel(origin: str = "semihosting") -> RetrievalChannel:
    """The semihosting retrieval channel."""
    return RetrievalChannel(kind=CHANNEL_SEMIHOSTING, origin=origin)


def serial_uart_channel(origin: str = "uart0") -> RetrievalChannel:
    """The serial (UART) retrieval channel."""
    return RetrievalChannel(kind=CHANNEL_SERIAL_UART, origin=origin)


def parse_channel_output(channel: RetrievalChannel, output_text: str) -> tuple[TargetResultLine, ...]:
    """Parse one retrieval stream: plain text, one-way, no reply channel.

    Pure function of the output text (plus the channel's origin label);
    recognises the documented result kinds and retains everything else
    verbatim as unparsed data through the WP-SEC-07 boundary.
    """
    payload = mark_untrusted(output_text, channel.origin)
    return parse_target_output(payload)
