# implements: TOOL-PAR-090, DSN-ANA-020
"""Macro resolution for extracted interfaces (WP-ANA-06, TOOL-PAR-090).

Resolves the function-like and object-like macros used in the interfaces of
extracted function definitions, and records where a macro obscures the true
interface.

Scope (deliberate, smallest increment):

- "Interface" means the signature portion of a function definition — from the
  definition start to its body brace — using the same extraction boundary as
  ``ectt.ana.interface`` (definitions in the translation unit's main file).
  A macro used only inside a function body is not an interface use and is not
  recorded.
- A function-like macro in the interface cannot be resolved to a value, so it
  is recorded as obscuring the interface. An object-like macro is resolved to
  its expansion (the literal body tokens joined with a single space). A use
  whose definition cannot be reached is recorded as ``unresolved`` and
  obscures (fail closed).
- Chained macros are not transitively expanded; the recorded expansion is the
  definition's own body.
- The parse must enable the detailed preprocessing record
  (``DETAILED_PROCESSING_OPTIONS``), the only way macro definitions and
  instantiations enter the libclang AST. Without it the resolver returns an
  empty tuple rather than guessing.

The records are derived, in-memory data consumed by CMP-ATG (WP-GEN-03);
they are deliberately NOT part of the persisted S1 analysis model, matching
the precedent of the eligibility records (``ectt.ana.eligibility``).

Satisfies: TOOL-PAR-090.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clang.cindex import CursorKind, TranslationUnit  # type: ignore[import-untyped]

from ectt.ana.errors import ExtractionRefusedError
from ectt.ana.interface import _is_in_main_file
from ectt.ana.model import ParsedTranslationUnit

__all__ = [
    "DETAILED_PROCESSING_OPTIONS",
    "MacroResolution",
    "resolve_interface_macros",
]

#: Parse options required for macro resolution: macro definitions and
#: instantiations only enter the libclang AST when the detailed preprocessing
#: record is enabled.
DETAILED_PROCESSING_OPTIONS = TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD

_OBJECT_LIKE = "object_like"
_FUNCTION_LIKE = "function_like"
_UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class _MacroDef:
    """A resolved macro definition: kind, expansion, and definition location."""

    kind: str
    expansion: str | None
    file: str | None
    line: int


@dataclass(frozen=True)
class MacroResolution:
    """One macro use inside an extracted function's interface (TOOL-PAR-090).

    ``kind`` is ``object_like`` (resolvable to ``expansion``),
    ``function_like`` (not resolvable to a value; obscures the interface) or
    ``unresolved`` (no definition reachable; obscures, fail closed).
    ``obscures_interface`` is True when the use site hides part of the true
    interface from the extracted model.
    """

    name: str
    kind: str
    obscures_interface: bool
    expansion: str | None
    definition_file: str | None
    definition_line: int | None
    used_in_function: str
    used_at_line: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "name": self.name,
            "kind": self.kind,
            "obscures_interface": self.obscures_interface,
            "expansion": self.expansion,
            "definition_file": self.definition_file,
            "definition_line": self.definition_line,
            "used_in_function": self.used_in_function,
            "used_at_line": self.used_at_line,
        }


def _tokens_of(cursor: Any) -> list[Any]:
    return list(cursor.get_tokens())


def _is_function_like(tokens: list[Any]) -> bool:
    """Decide function-likeness from token adjacency to the macro name.

    ``#define FLAG (1 << 3)`` is object-like despite its leading parenthesis:
    the parenthesis is separated from the name by a space. ``#define PTR(T) T*``
    has ``(`` immediately adjacent to the name. Token extents carry the
    difference.
    """
    if len(tokens) < 2:
        return False
    return tokens[1].extent.start.offset == tokens[0].extent.end.offset


def _definition_from_cursor(cursor: Any) -> _MacroDef:
    """Build a definition record from a MACRO_DEFINITION cursor."""
    tokens = _tokens_of(cursor)
    if _is_function_like(tokens):
        return _MacroDef(
            kind=_FUNCTION_LIKE,
            expansion=None,
            file=cursor.location.file.name if cursor.location.file else None,
            line=cursor.location.line,
        )
    expansion = " ".join(token.spelling for token in tokens[1:])
    return _MacroDef(
        kind=_OBJECT_LIKE,
        expansion=expansion,
        file=cursor.location.file.name if cursor.location.file else None,
        line=cursor.location.line,
    )


def _collect_definitions(tu_handle: Any) -> dict[str, _MacroDef]:
    """Collect the translation unit's macro definitions, last definition wins.

    Builtin compiler macros have no source location and are still collected
    (they are resolvable); the ``file``/``line`` stay ``None``/``1``.
    """
    definitions: dict[str, _MacroDef] = {}
    for child in tu_handle.cursor.get_children():
        if child.kind != CursorKind.MACRO_DEFINITION:
            continue
        tokens = _tokens_of(child)
        if not tokens:
            continue
        definitions[child.spelling] = _definition_from_cursor(child)
    return definitions


def _signature_ranges(tu_handle: Any, main_path: str, working_directory: str | Path | None) -> Iterator[tuple[int, int, str]]:
    """Yield (start, signature_end, name) for definitions in the main file.

    The signature ends at the first body brace; a macro use at or after that
    brace is a body use, not an interface use. Definitions share the
    extraction boundary of ``ectt.ana.interface``.
    """
    for child in tu_handle.cursor.get_children():
        if child.kind != CursorKind.FUNCTION_DECL or not child.is_definition():
            continue
        if not _is_in_main_file(child.location, main_path, working_directory):
            continue
        signature_end = child.extent.end.offset
        for token in child.get_tokens():
            if token.spelling == "{":
                signature_end = token.extent.start.offset
                break
        yield child.extent.start.offset, signature_end, child.spelling


def resolve_interface_macros(
    parsed_tu: ParsedTranslationUnit,
    *,
    working_directory: str | Path | None = None,
) -> tuple[MacroResolution, ...]:
    """Resolve the macros used in the interfaces of extracted definitions.

    Returns one record per macro use inside a definition's signature, sorted
    by (function, line, name). Raises ``ExtractionRefusedError`` for a failed
    translation unit, mirroring ``extract_interfaces``. Requires the parse to
    have enabled ``DETAILED_PROCESSING_OPTIONS``; without the detailed
    preprocessing record the AST carries no macro cursors and the result is
    empty.
    """
    if parsed_tu.is_failed or parsed_tu.status == "failed":
        raise ExtractionRefusedError(
            f"Cannot resolve interface macros of failed translation unit '{parsed_tu.source_path}'",
            path=parsed_tu.source_path,
        )
    if parsed_tu.translation_unit is None:
        raise ExtractionRefusedError(
            f"Parsed translation unit has no libclang AST handle: '{parsed_tu.source_path}'",
            path=parsed_tu.source_path,
        )

    tu_handle = parsed_tu.translation_unit
    definitions = _collect_definitions(tu_handle)
    ranges = list(_signature_ranges(tu_handle, parsed_tu.source_path, working_directory))

    results: list[MacroResolution] = []
    for inst in tu_handle.cursor.get_children():
        if inst.kind != CursorKind.MACRO_INSTANTIATION:
            continue
        offset = inst.extent.start.offset
        owner = next(
            (entry for entry in ranges if entry[0] <= offset < entry[1]), None
        )
        if owner is None:
            continue  # not an interface use of an extracted definition
        ref = inst.referenced
        definition: _MacroDef | None
        if ref is not None and ref.kind == CursorKind.MACRO_DEFINITION:
            definition = _definition_from_cursor(ref)
        else:
            definition = definitions.get(inst.spelling)
        if definition is None:
            # Fail closed: an unreachable definition cannot promise anything
            # about the interface it appears in.
            results.append(
                MacroResolution(
                    name=inst.spelling,
                    kind=_UNRESOLVED,
                    obscures_interface=True,
                    expansion=None,
                    definition_file=None,
                    definition_line=None,
                    used_in_function=owner[2],
                    used_at_line=inst.location.line,
                )
            )
            continue
        results.append(
            MacroResolution(
                name=inst.spelling,
                kind=definition.kind,
                obscures_interface=definition.kind == _FUNCTION_LIKE,
                expansion=definition.expansion,
                definition_file=definition.file,
                definition_line=definition.line,
                used_in_function=owner[2],
                used_at_line=inst.location.line,
            )
        )

    results.sort(key=lambda r: (r.used_in_function, r.used_at_line, r.name))
    return tuple(results)
