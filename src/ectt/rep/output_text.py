# implements: TOOL-REP-010, TOOL-REP-020, TOOL-REP-030, TOOL-MIG-080
"""Text a report output can carry, and the refusal when it cannot.

Escaping protects a document from the markup and the quotes in the text it
carries. It cannot protect it from everything: XML 1.0 forbids most control
characters, an LCOV record ends at its line break, and a lone surrogate cannot
be written as UTF-8 at all. Those are refused here, in the renderer, with a
named reason and before anything is written, instead of surfacing later as a
document that does not parse or as a bare encoding error.

A refusal names the field and the offending character. It never quotes what
was refused: an identifier appears control-free and bounded, and a source line
appears only as its location (the discipline of TOOL-SEC-120).

Supports: TOOL-REP-010, TOOL-REP-020, TOOL-REP-030, TOOL-MIG-080.
"""

from __future__ import annotations

import re

from ectt.rep.errors import ReportModelError

__all__ = [
    "describe",
    "refuse_characters",
    "xml_attribute",
]

_DESCRIBE_LIMIT = 60

#: A lone surrogate: text holding one cannot be encoded as UTF-8.
_LONE_SURROGATE = re.compile(r"[\ud800-\udfff]")


def describe(value: str, limit: int = _DESCRIBE_LIMIT) -> str:
    """A control-free, bounded rendering of an identifier for a diagnostic.

    ``ascii`` shows every control character, surrogate and non-ASCII character
    as an escape, so the rendering can neither carry a control sequence nor
    reverse the display. A long identifier is cut.
    """
    text = ascii(value)
    if len(text) > limit:
        text = text[: limit - 1] + "...'"
    return text


def refuse_characters(
    value: str,
    what: str,
    *,
    forbidden: re.Pattern[str],
    reason: str,
    problem: str,
    carrier: str,
) -> None:
    """Refuse the first character of ``value`` that ``forbidden`` matches.

    ``what`` names the field (already control-free), ``problem`` names the kind
    of character, and ``carrier`` names the output that cannot carry it. Text
    that cannot be written as UTF-8 is refused first, as ``unencodable_text``.
    """
    match = _LONE_SURROGATE.search(value)
    if match is not None:
        raise ReportModelError(
            f"{what} contains a lone surrogate (U+{ord(match.group()):04X}) and cannot be written as UTF-8",
            reason="unencodable_text",
        )
    match = forbidden.search(value)
    if match is not None:
        raise ReportModelError(
            f"{what} contains {problem} (U+{ord(match.group()):04X}), which {carrier} cannot carry",
            reason=reason,
        )


#: Everything outside the XML 1.0 ``Char`` production (lone surrogates excluded).
_XML_ILLEGAL = re.compile(r"[^\t\n\r\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]")


def xml_attribute(value: str, what: str = "XML attribute value") -> str:
    """Return ``value`` as a quoted XML attribute that reads back as ``value``.

    Markup and quotes are escaped. Tab, line feed and carriage return are
    written as character references, because an XML parser replaces those
    three inside an attribute value and the text would otherwise read back
    changed. Refused with a named reason: a character XML 1.0 does not allow
    (``xml_illegal_character``) and text that cannot be written as UTF-8
    (``unencodable_text``).
    """
    refuse_characters(
        value,
        what,
        forbidden=_XML_ILLEGAL,
        reason="xml_illegal_character",
        problem="a character XML 1.0 does not allow",
        carrier="an XML 1.0 document",
    )
    escaped = (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\t", "&#9;")
        .replace("\n", "&#10;")
        .replace("\r", "&#13;")
    )
    if '"' in escaped:
        if "'" not in escaped:
            return f"'{escaped}'"
        escaped = escaped.replace('"', "&quot;")
    return f'"{escaped}"'
