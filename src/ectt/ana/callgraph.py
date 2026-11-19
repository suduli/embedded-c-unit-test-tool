# implements: TOOL-PAR-060, DSN-ANA-030
"""Call graph extraction and callee scope classification (WP-ANA-03).

For each function body, every call expression is recorded with its callee and a
classification. Indirect calls are recorded as unresolved and never guessed: the
callee name is left empty. Undeclared callees (implicit declarations) are recorded
as unresolved with via="undeclared".

Satisfies: TOOL-PAR-060.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from clang.cindex import CursorKind  # type: ignore[import-untyped]

from ectt.ana.model import CallModel

__all__ = ["extract_calls"]


def _is_implicit_declaration(decl: Any) -> bool:
    """An implicit declaration (undeclared callee) has no source extent of its own."""
    start = decl.extent.start
    return start is None or start.file is None or start.line == 0


def _classify_call(
    call: Any,
    is_in_unit_file: Callable[[Any], bool],
) -> CallModel:
    line = call.location.line
    decl = call.referenced

    if decl is None or decl.kind != CursorKind.FUNCTION_DECL:
        # Calls through a variable, parameter or member: the target is not known statically.
        return CallModel(callee="", classification="unresolved", via="function_pointer", line=line)

    name = decl.spelling or call.spelling
    if _is_implicit_declaration(decl):
        return CallModel(callee=name, classification="unresolved", via="undeclared", line=line)

    definition = decl.get_definition()
    if definition is not None and is_in_unit_file(definition.location):
        classification = "internal"
    elif decl.location.is_in_system_header:
        classification = "library"
    else:
        classification = "external"
    return CallModel(callee=name, classification=classification, via="direct", line=line)


def extract_calls(
    func_cursor: Any,
    is_in_unit_file: Callable[[Any], bool],
) -> tuple[CallModel, ...]:
    """Return the call sites in a function body, sorted for deterministic output.

    ``is_in_unit_file`` tells whether a source location belongs to the unit under test.
    """
    found: list[CallModel] = []

    def walk(cursor: Any) -> None:
        if cursor.kind == CursorKind.CALL_EXPR:
            found.append(_classify_call(cursor, is_in_unit_file))
        for child in cursor.get_children():
            walk(child)

    walk(func_cursor)
    found.sort(key=lambda c: (c.line, c.callee, c.via, c.classification))
    return tuple(found)
