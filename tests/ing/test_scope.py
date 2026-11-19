"""Tests for the WP-ING-04 test scope model and resolution.

Verifies: TOOL-ING-120, TOOL-ING-130, TOOL-ING-140, TOOL-ING-150, TOOL-ING-190.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.ing.scope import (
    KIND_EXTERNAL,
    KIND_INTRA,
    SCOPE_SCHEMA_VERSION,
    DuplicateScopeNameError,
    ScopeRecordError,
    ScopeSet,
    ScopeTooSmallError,
    UnknownScopeTargetError,
    classify_calls,
    expand_directory,
    expand_files,
    expand_glob,
    expand_target,
    external_dependencies,
    load_scope,
    save_scope,
)
from ectt.ing.scope import (
    TestScope as ScopeRecord,
)


def test_two_or_more_sources_form_a_scope() -> None:
    """verifies: TOOL-ING-120"""
    scope = ScopeRecord(name="pair", members=("a.c", "b.c"))
    assert scope.members == ("a.c", "b.c")


def test_fewer_than_two_sources_is_named_error() -> None:
    """verifies: TOOL-ING-120"""
    with pytest.raises(ScopeTooSmallError):
        ScopeRecord(name="solo", members=("a.c",))
    with pytest.raises(ScopeTooSmallError):
        ScopeRecord(name="empty", members=())


def test_scope_is_named_first_class_record() -> None:
    """verifies: TOOL-ING-130"""
    scope = ScopeRecord(name="integration", members=("a.c", "b.c"))
    assert scope.name == "integration"
    assert scope.to_dict() == {"members": ["a.c", "b.c"], "name": "integration"}


def test_calls_classified_intra_vs_external() -> None:
    """verifies: TOOL-ING-140"""
    calls = {
        "a.c": ("helper", "memset"),
        "b.c": ("helper",),
    }
    defined = {"a.c": {"helper"}, "b.c": set()}
    classification = classify_calls(calls, defined)
    assert classification["a.c"]["helper"] == KIND_INTRA
    assert classification["a.c"]["memset"] == KIND_EXTERNAL
    assert classification["b.c"]["helper"] == KIND_INTRA


def test_external_dependencies_listed_exactly() -> None:
    """verifies: TOOL-ING-130"""
    calls = {"a.c": ("zeta", "alpha", "helper"), "b.c": ("zeta",)}
    defined = {"a.c": ("helper",), "b.c": ()}
    assert external_dependencies(calls, defined) == ("alpha", "zeta")


def test_explicit_file_list_deduplicated_and_sorted() -> None:
    """verifies: TOOL-ING-150"""
    assert expand_files(("b.c", "a.c", "b.c")) == ("a.c", "b.c")


def test_directory_expansion_finds_c_files_recursively(tmp_path: Path) -> None:
    """verifies: TOOL-ING-150"""
    (tmp_path / "sub").mkdir()
    (tmp_path / "b.c").write_text("int b;\n", encoding="utf-8")
    (tmp_path / "sub" / "a.c").write_text("int a;\n", encoding="utf-8")
    (tmp_path / "note.txt").write_text("x", encoding="utf-8")
    assert expand_directory(tmp_path) == (
        (tmp_path / "b.c").as_posix(),
        (tmp_path / "sub" / "a.c").as_posix(),
    )


def test_glob_expansion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """verifies: TOOL-ING-150"""
    (tmp_path / "x_driver.c").write_text("int x;\n", encoding="utf-8")
    (tmp_path / "y_driver.c").write_text("int y;\n", encoding="utf-8")
    (tmp_path / "main.c").write_text("int m;\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    assert expand_glob("*_driver.c") == ("x_driver.c", "y_driver.c")


def test_named_build_target_resolved_from_mapping() -> None:
    """verifies: TOOL-ING-150"""
    members = expand_target(
        "app_integration", {"app_integration": ("c.c", "a.c", "c.c"), "other": ("d.c",)}
    )
    assert members == ("a.c", "c.c")


def test_unknown_build_target_is_named_error() -> None:
    """verifies: TOOL-ING-150"""
    with pytest.raises(UnknownScopeTargetError) as excinfo:
        expand_target("ghost", {"real": ("a.c", "b.c")})
    assert "ghost" in str(excinfo.value)


def test_scope_persists_and_reloads_byte_identical(tmp_path: Path) -> None:
    """verifies: TOOL-ING-190"""
    scope = ScopeRecord(name="pair", members=("b.c", "a.c"))
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    save_scope(scope, first)
    save_scope(scope, second)
    assert first.read_bytes() == second.read_bytes()
    document = json.loads(first.read_text(encoding="utf-8"))
    assert document["schema_version"] == SCOPE_SCHEMA_VERSION
    reloaded = load_scope(first)
    assert reloaded == scope


def test_malformed_scope_files_are_named_errors(tmp_path: Path) -> None:
    """verifies: TOOL-ING-190"""
    missing = tmp_path / "absent.json"
    with pytest.raises(ScopeRecordError):
        load_scope(missing)
    bad = tmp_path / "bad.json"
    bad.write_text("{nope", encoding="utf-8")
    with pytest.raises(ScopeRecordError):
        load_scope(bad)
    old = tmp_path / "old.json"
    old.write_text(json.dumps({"schema_version": 99, "scope": {"name": "x", "members": ["a.c", "b.c"]}}), encoding="utf-8")
    with pytest.raises(ScopeRecordError):
        load_scope(old)


def test_scope_set_rejects_duplicate_names() -> None:
    """verifies: TOOL-ING-190"""
    scopes = ScopeSet()
    scopes.add(ScopeRecord(name="pair", members=("a.c", "b.c")))
    with pytest.raises(DuplicateScopeNameError):
        scopes.add(ScopeRecord(name="pair", members=("c.c", "d.c")))
    assert scopes.list_names() == ("pair",)
    with pytest.raises(ScopeRecordError):
        scopes.lookup("ghost")
