"""Tests for the WP-GEN-08 stub scope control.

Verifies: TOOL-STB-080, TOOL-STB-100, TOOL-STB-140.
"""

from __future__ import annotations

import pytest

from ectt.gen import (
    STDLIB_FUNCTIONS,
    UnknownStubReferenceError,
    build_stub_plan,
)


def test_default_plan_stubs_every_reference() -> None:
    """verifies: TOOL-STB-080"""
    plan = build_stub_plan(("hal_read", "memset", "driver_send"))
    assert plan.stubs == ("driver_send", "hal_read")  # stdlib not stubbed by default
    assert plan.link_real == ()


def test_excluded_function_links_real_implementation() -> None:
    """verifies: TOOL-STB-080"""
    plan = build_stub_plan(("hal_read", "hal_write", "memset"), exclude=("hal_write",))
    assert "hal_write" not in plan.stubs
    assert plan.link_real == ("hal_write",)


def test_excluding_every_reference_leaves_no_stubs() -> None:
    """verifies: TOOL-STB-080"""
    plan = build_stub_plan(("a", "b"), exclude=("a", "b"))
    assert plan.stubs == () and plan.link_real == ("a", "b")


def test_unknown_exclude_is_named_error() -> None:
    """verifies: TOOL-STB-080"""
    with pytest.raises(UnknownStubReferenceError) as excinfo:
        build_stub_plan(("a", "b"), exclude=("ghost",))
    assert "ghost" in str(excinfo.value)


def test_stdlib_never_stubbed_by_default() -> None:
    """verifies: TOOL-STB-100"""
    plan = build_stub_plan(("memcpy", "hal_read"))
    assert "memcpy" not in plan.stubs
    assert plan.stdlib_stubbed == ()
    assert "memcpy" in plan.link_real or "memcpy" not in plan.stubs


def test_stdlib_stubbed_on_explicit_request() -> None:
    """verifies: TOOL-STB-100"""
    plan = build_stub_plan(("memcpy", "hal_read"), stdlib=("memcpy",))
    assert "memcpy" in plan.stubs
    assert plan.stdlib_stubbed == ("memcpy",)


def test_stdlib_request_outside_vocabulary_is_named_error() -> None:
    """verifies: TOOL-STB-100"""
    with pytest.raises(UnknownStubReferenceError) as excinfo:
        build_stub_plan(("psychic_malloc",), stdlib=("psychic_malloc",))
    assert "documented standard-library vocabulary" in str(excinfo.value)
    assert "memcpy" in STDLIB_FUNCTIONS


def test_stdlib_request_for_unreferenced_name_is_named_error() -> None:
    """verifies: TOOL-STB-100"""
    with pytest.raises(UnknownStubReferenceError):
        build_stub_plan(("hal_read",), stdlib=("memset",))


def test_pointer_targets_stubbed_with_access_path() -> None:
    """verifies: TOOL-STB-140"""
    plan = build_stub_plan(
        ("dispatch", "hal_read"),
        pointer_targets=("dispatch",),
        pointer_paths={"dispatch": "cb_table.dispatch"},
    )
    assert "dispatch" in plan.stubs
    assert plan.pointer_targets == ("dispatch",)
    assert plan.pointer_paths["dispatch"] == "cb_table.dispatch"
    assert plan.to_dict()["pointer_paths"] == {"dispatch": "cb_table.dispatch"}


def test_pointer_target_must_be_a_reference() -> None:
    """verifies: TOOL-STB-140"""
    with pytest.raises(UnknownStubReferenceError):
        build_stub_plan(("hal_read",), pointer_targets=("ghost",))


def test_excluded_pointer_target_never_stubbed() -> None:
    """verifies: TOOL-STB-080"""
    plan = build_stub_plan(
        ("dispatch", "hal_read"),
        exclude=("dispatch",),
        pointer_targets=("dispatch",),
    )
    assert plan.stubs == ("hal_read",)
    assert plan.pointer_targets == ()


def test_plan_is_deterministic_and_frozen() -> None:
    """verifies: TOOL-STB-080"""
    first = build_stub_plan(("b", "a", "c"), exclude=("b",))
    second = build_stub_plan(("c", "a", "b"), exclude=("b",))
    assert first.to_dict() == second.to_dict()
    assert first.stubs == ("a", "c")
    with pytest.raises(Exception):  # noqa: B017 - frozen dataclass setattr
        first.stubs = ()  # type: ignore[misc]
