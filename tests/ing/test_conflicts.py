"""Tests for WP-ING-05 scope conflicts and stub requirements.

Verifies: TOOL-ING-160, TOOL-ING-170, TOOL-ING-180.
"""

from __future__ import annotations

import pytest

from ectt.ing.conflicts import (
    KIND_DUPLICATE_DEFINITION,
    KIND_MIXED_LINKAGE,
    KIND_STATIC_COLLISION,
    StubRequirement,
    SymbolDeclaration,
    detect_symbol_conflicts,
    scopes_containing,
    stub_requirements,
)
from ectt.ing.scope import ScopeRecordError, ScopeSet
from ectt.ing.scope import TestScope as ScopeRecord


def _decl(name: str, static: bool = False) -> SymbolDeclaration:
    return SymbolDeclaration(name=name, linkage="internal" if static else "external")


def test_clean_scope_has_no_conflicts() -> None:
    """verifies: TOOL-ING-160"""
    definitions = {
        "a.c": (_decl("alpha"), _decl("local_helper", static=True)),
        "b.c": (_decl("beta"), _decl("other_helper", static=True)),
    }
    assert detect_symbol_conflicts(definitions) == ()


def test_duplicate_non_static_definition_detected() -> None:
    """verifies: TOOL-ING-160"""
    definitions = {
        "a.c": (_decl("alpha"),),
        "b.c": (_decl("alpha"),),
        "c.c": (_decl("gamma"),),
    }
    conflicts = detect_symbol_conflicts(definitions)
    assert len(conflicts) == 1
    assert conflicts[0].kind == KIND_DUPLICATE_DEFINITION
    assert conflicts[0].symbol == "alpha"
    assert conflicts[0].members == ("a.c", "b.c")


def test_colliding_file_static_identifiers_detected() -> None:
    """verifies: TOOL-ING-160"""
    definitions = {
        "a.c": (_decl("counter", static=True),),
        "b.c": (_decl("counter", static=True),),
    }
    conflicts = detect_symbol_conflicts(definitions)
    assert len(conflicts) == 1
    assert conflicts[0].kind == KIND_STATIC_COLLISION
    assert conflicts[0].members == ("a.c", "b.c")


def test_mixed_linkage_detected() -> None:
    """verifies: TOOL-ING-160"""
    definitions = {
        "a.c": (_decl("setup", static=True),),
        "b.c": (_decl("setup"),),
    }
    conflicts = detect_symbol_conflicts(definitions)
    assert [c.kind for c in conflicts] == [KIND_MIXED_LINKAGE]
    assert conflicts[0].members == ("b.c", "a.c")


def test_conflict_listing_is_deterministic() -> None:
    """verifies: TOOL-ING-160"""
    definitions = {
        "z.c": (_decl("dup"), _decl("shared", static=True)),
        "a.c": (_decl("dup"), _decl("shared", static=True)),
    }
    conflicts = detect_symbol_conflicts(definitions)
    assert [c.symbol for c in conflicts] == ["dup", "shared"]


def test_translation_unit_belongs_to_multiple_scopes() -> None:
    """verifies: TOOL-ING-170"""
    scopes = ScopeSet()
    scopes.add(ScopeRecord(name="pair", members=("a.c", "b.c")))
    scopes.add(ScopeRecord(name="integration", members=("a.c", "b.c", "c.c")))
    assert scopes_containing(scopes, "a.c") == ("integration", "pair")
    assert scopes_containing(scopes, "c.c") == ("integration",)
    assert scopes_containing(scopes, "not_a_member.c") == ()


def test_multi_scope_membership_is_not_a_duplicate_error() -> None:
    """verifies: TOOL-ING-170"""
    scopes = ScopeSet()
    scopes.add(ScopeRecord(name="pair", members=("a.c", "b.c")))
    # Adding a second scope sharing member a.c must not raise.
    scopes.add(ScopeRecord(name="trio", members=("a.c", "c.c", "d.c")))
    assert scopes.list_names() == ("pair", "trio")
    with pytest.raises(ScopeRecordError):
        scopes.lookup("ghost")


def test_stub_requirements_list_complete_and_sorted() -> None:
    """verifies: TOOL-ING-180"""
    calls = {
        "a.c": ("memset", "alpha", "zeta"),
        "b.c": ("memset", "alpha", "helper"),
    }
    defined = {"a.c": ("alpha",), "b.c": ("helper",)}
    requirements = stub_requirements(calls, defined)
    assert [r.symbol for r in requirements] == ["memset", "zeta"]
    assert requirements[0] == StubRequirement(symbol="memset", callers=("a.c", "b.c"))
    assert requirements[1] == StubRequirement(symbol="zeta", callers=("a.c",))


def test_intra_scope_calls_never_require_stubs() -> None:
    """verifies: TOOL-ING-180"""
    calls = {"a.c": ("alpha", "helper")}
    defined = {"a.c": ("alpha",), "b.c": ("helper",)}
    requirements = stub_requirements(calls, defined)
    assert requirements == ()
