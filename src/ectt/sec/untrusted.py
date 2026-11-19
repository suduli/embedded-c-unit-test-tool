"""Target-supplied data treated as untrusted (WP-SEC-07).

Data retrieved from a target device or an external process enters the tool
only through a frozen, origin-carrying payload wrapper with data accessors
only, and is parsed strictly as plain-text result lines. Unparsable or
code-looking content is retained verbatim as data — never executed or
interpreted as code.

Satisfies: TOOL-SEC-090.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "RESULT_LINE_KINDS",
    "UntrustedPayload",
    "TargetResultLine",
    "mark_untrusted",
    "parse_target_output",
]

RESULT_LINE_KINDS = ("PASS", "FAIL", "ERROR", "TIMEOUT", "LOG")


@dataclass(frozen=True)
class UntrustedPayload:
    """Content retrieved from a target or external process: data, never code."""

    origin: str
    content: str

    def text(self) -> str:
        """The raw content as text (data access)."""
        return self.content

    def lines(self) -> tuple[str, ...]:
        """The content split into lines (data access)."""
        return tuple(self.content.splitlines())

    def length(self) -> int:
        """The content length (data access)."""
        return len(self.content)

    def __repr__(self) -> str:
        """Sanitised: origin and size only, never the content."""
        return f"UntrustedPayload(origin={self.origin!r}, size={len(self.content)})"


def mark_untrusted(content: str, origin: str) -> UntrustedPayload:
    """Wrap retrieved content as untrusted, carrying its origin."""
    if not isinstance(content, str):
        raise TypeError("target-supplied data must be captured as text")
    if not origin.strip():
        raise ValueError("untrusted payload requires a non-empty origin")
    return UntrustedPayload(origin=origin, content=content)


@dataclass(frozen=True)
class TargetResultLine:
    """One line of target output, parsed as data only."""

    origin: str
    kind: str  # one of RESULT_LINE_KINDS, or "unparsed"
    test_name: str | None
    payload: str
    raw: str


def parse_target_output(payload: UntrustedPayload) -> tuple[TargetResultLine, ...]:
    """Parse target output as plain-text result lines — data, never code.

    A line is parsed when its first token is one of the protocol kinds; every
    other line is retained verbatim as an ``unparsed`` data entry. No line is
    ever executed or interpreted beyond this text split.
    """
    results: list[TargetResultLine] = []
    for line in payload.lines():
        stripped = line.strip()
        first_token = stripped.split(" ", 1)[0] if stripped else ""
        if first_token in RESULT_LINE_KINDS:
            remainder = stripped[len(first_token) :].strip()
            test_name = remainder.split(" ", 1)[0] if remainder else None
            results.append(
                TargetResultLine(
                    origin=payload.origin,
                    kind=first_token,
                    test_name=test_name or None,
                    payload=remainder,
                    raw=line,
                )
            )
        else:
            results.append(
                TargetResultLine(
                    origin=payload.origin,
                    kind="unparsed",
                    test_name=None,
                    payload=stripped,
                    raw=line,
                )
            )
    return tuple(results)
