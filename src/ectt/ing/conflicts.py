"""Scope conflict detection and stub-requirement reporting (WP-ING-05).

Symbol conflicts inside a scope (duplicate non-static definitions, colliding
file-static names, mixed linkage), multi-scope membership for a single
translation unit, and the complete stub-requirement list a scope needs before
harness generation.

Satisfies: TOOL-ING-160, TOOL-ING-170, TOOL-ING-180.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ectt.ing.scope import ScopeSet

__all__ = [
    "KIND_DUPLICATE_DEFINITION",
    "KIND_STATIC_COLLISION",
    "KIND_MIXED_LINKAGE",
    "SymbolDeclaration",
    "SymbolConflict",
    "detect_symbol_conflicts",
    "scopes_containing",
    "StubRequirement",
    "stub_requirements",
]

KIND_DUPLICATE_DEFINITION = "duplicate_definition"
KIND_STATIC_COLLISION = "static_collision"
KIND_MIXED_LINKAGE = "mixed_linkage"


@dataclass(frozen=True)
class SymbolDeclaration:
    """One symbol defined by a scope member."""

    name: str
    linkage: str  # "external" | "internal" (file-static)


@dataclass(frozen=True)
class SymbolConflict:
    """One detected conflict, naming the symbol and the members involved."""

    kind: str
    symbol: str
    members: tuple[str, ...]
    detail: str


def detect_symbol_conflicts(
    definitions: Mapping[str, tuple[SymbolDeclaration, ...]],
) -> tuple[SymbolConflict, ...]:
    """Detect symbol conflicts across scope members.

    ``definitions`` maps member unit path to the symbols that unit defines.
    Conflicts: the same non-static name defined twice or more; the same
    file-static name defined twice or more; the same name with mixed linkage
    across members. Output is deterministically ordered.
    """
    by_name: dict[str, dict[str, list[str]]] = {}
    for unit in sorted(definitions):
        for declaration in definitions[unit]:
            linkage = "static" if declaration.linkage == "internal" else "external"
            by_name.setdefault(declaration.name, {}).setdefault(linkage, []).append(unit)

    conflicts: list[SymbolConflict] = []
    for name in sorted(by_name):
        linkage_map = by_name[name]
        external_units = tuple(sorted(linkage_map.get("external", [])))
        static_units = tuple(sorted(linkage_map.get("static", [])))
        if len(external_units) >= 2:
            conflicts.append(
                SymbolConflict(
                    kind=KIND_DUPLICATE_DEFINITION,
                    symbol=name,
                    members=external_units,
                    detail=(
                        f"non-static symbol '{name}' is defined by "
                        f"{len(external_units)} members: {', '.join(external_units)}"
                    ),
                )
            )
        if len(static_units) >= 2:
            conflicts.append(
                SymbolConflict(
                    kind=KIND_STATIC_COLLISION,
                    symbol=name,
                    members=static_units,
                    detail=(
                        f"file-static identifier '{name}' collides across "
                        f"{len(static_units)} members: {', '.join(static_units)}"
                    ),
                )
            )
        if external_units and static_units:
            conflicts.append(
                SymbolConflict(
                    kind=KIND_MIXED_LINKAGE,
                    symbol=name,
                    members=external_units + static_units,
                    detail=(
                        f"symbol '{name}' is non-static in {', '.join(external_units)} "
                        f"and file-static in {', '.join(static_units)}"
                    ),
                )
            )
    return tuple(conflicts)


def scopes_containing(scope_set: ScopeSet, unit: str) -> tuple[str, ...]:
    """Every scope name whose members include ``unit`` (TOOL-ING-170)."""
    return tuple(
        name
        for name in scope_set.list_names()
        if unit in scope_set.lookup(name).members
    )


@dataclass(frozen=True)
class StubRequirement:
    """One external dependency that requires a stub before harness generation."""

    symbol: str
    callers: tuple[str, ...]


def stub_requirements(
    calls: Mapping[str, tuple[str, ...]],
    defined_functions: Mapping[str, tuple[str, ...] | set[str]],
) -> tuple[StubRequirement, ...]:
    """The complete stub-requirement list for a scope (TOOL-ING-180).

    Every external callee (defined by no member) appears exactly once with the
    units that reference it, sorted deterministically. Intra-scope calls never
    appear.
    """
    defined: set[str] = set()
    for functions in defined_functions.values():
        defined.update(functions)
    callers_by_symbol: dict[str, list[str]] = {}
    for unit in sorted(calls):
        for callee in calls[unit]:
            if callee not in defined:
                callers_by_symbol.setdefault(callee, []).append(unit)
    return tuple(
        StubRequirement(symbol=symbol, callers=tuple(sorted(set(units))))
        for symbol, units in sorted(callers_by_symbol.items())
    )
