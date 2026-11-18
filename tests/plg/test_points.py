"""Tests for the WP-PLG-01 extension-point definition surface.

Covers: the four built-in extension points required by the SRS, descriptor
validation, duplicate/unknown handling, deterministic ordering, and
open-ended registration without tool-source modification.

Verifies: TOOL-PLG-010.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.core.fs import CoreError
from ectt.plg import (
    BUILTIN_EXTENSION_POINTS,
    CONTRACT_COMPILER_CONFIG,
    CONTRACT_FRAMEWORK_BACKEND,
    CONTRACT_REPORT_FORMAT,
    CONTRACT_TARGET_EXECUTION,
    DuplicateExtensionPointError,
    ExtensionPoint,
    ExtensionPointRegistry,
    InvalidExtensionPointError,
    PlgError,
    UnknownExtensionPointError,
    default_registry,
)

REQUIRED_IDS = (
    "compiler_configs",
    "framework_backends",
    "target_execution_methods",
    "report_formats",
)


def _make_point(point_id: str = "user_point") -> ExtensionPoint:
    return ExtensionPoint(
        point_id=point_id,
        title="User point",
        description="A user-defined extension point.",
        contract="user_contract",
        interface_version="1",
    )


def test_builtin_registry_exposes_four_minimum_points() -> None:
    """verifies: TOOL-PLG-010"""
    points = {p.point_id for p in default_registry().list_points()}
    for required in REQUIRED_IDS:
        assert required in points


def test_builtin_contracts_cover_the_four_required_kinds() -> None:
    """verifies: TOOL-PLG-010"""
    contracts = {p.contract for p in BUILTIN_EXTENSION_POINTS}
    assert contracts == {
        CONTRACT_COMPILER_CONFIG,
        CONTRACT_FRAMEWORK_BACKEND,
        CONTRACT_TARGET_EXECUTION,
        CONTRACT_REPORT_FORMAT,
    }


def test_every_builtin_descriptor_is_documented_and_versioned() -> None:
    """verifies: TOOL-PLG-010"""
    assert len(BUILTIN_EXTENSION_POINTS) >= 4
    for point in BUILTIN_EXTENSION_POINTS:
        assert point.title.strip(), point.point_id
        assert point.description.strip(), point.point_id
        assert point.interface_version


def test_listing_is_deterministic_and_sorted() -> None:
    """verifies: TOOL-PLG-010"""
    registry = default_registry()
    first = [p.point_id for p in registry.list_points()]
    second = [p.point_id for p in default_registry().list_points()]
    assert first == second == sorted(first)


def test_register_and_lookup_user_point() -> None:
    """verifies: TOOL-PLG-010"""
    registry = default_registry()
    point = _make_point()
    registry.register(point)
    assert registry.lookup("user_point") == point
    assert "user_point" in [p.point_id for p in registry.list_points()]


def test_lookup_unknown_point_is_rejected() -> None:
    """verifies: TOOL-PLG-010"""
    registry = default_registry()
    with pytest.raises(UnknownExtensionPointError) as excinfo:
        registry.lookup("does_not_exist")
    assert "does_not_exist" in str(excinfo.value)


def test_duplicate_registration_is_rejected() -> None:
    """verifies: TOOL-PLG-010"""
    registry = default_registry()
    with pytest.raises(DuplicateExtensionPointError):
        registry.register(_make_point("compiler_configs"))


def test_register_rejects_blank_fields() -> None:
    """verifies: TOOL-PLG-010"""
    registry = ExtensionPointRegistry()
    fields = ("point_id", "title", "description", "contract", "interface_version")
    for field in fields:
        blank = dict.fromkeys(fields, "x")
        blank[field] = "   "
        with pytest.raises(InvalidExtensionPointError):
            registry.register(ExtensionPoint(**blank))


def test_register_rejects_non_string_fields() -> None:
    """verifies: TOOL-PLG-010"""
    registry = ExtensionPointRegistry()
    fields = ("point_id", "title", "description", "contract", "interface_version")
    for field in fields:
        kwargs = dict.fromkeys(fields, "x")
        kwargs[field] = 7  # type: ignore[assignment]
        with pytest.raises(InvalidExtensionPointError):
            registry.register(ExtensionPoint(**kwargs))  # type: ignore[arg-type]


def test_register_rejects_malformed_interface_version() -> None:
    """verifies: TOOL-PLG-010"""
    registry = ExtensionPointRegistry()
    for bad in ("v1", "1.x", "", "1.", "1..0"):
        kwargs = {
            "point_id": "bad_version",
            "title": "Bad version",
            "description": "Point with a malformed interface version.",
            "contract": "user_contract",
            "interface_version": bad,
        }
        with pytest.raises(InvalidExtensionPointError):
            registry.register(ExtensionPoint(**kwargs))


def test_builtin_descriptors_are_frozen() -> None:
    """verifies: TOOL-PLG-010"""
    for point in BUILTIN_EXTENSION_POINTS:
        with pytest.raises(dataclasses.FrozenInstanceError):
            point.point_id = "mutated"  # type: ignore[misc]


def test_default_registry_returns_fresh_instances() -> None:
    """verifies: TOOL-PLG-010"""
    a = default_registry()
    b = default_registry()
    assert a is not b
    a.register(_make_point())
    with pytest.raises(UnknownExtensionPointError):
        b.lookup("user_point")


def test_error_hierarchy_derives_from_core_error() -> None:
    """verifies: TOOL-PLG-010"""
    for cls in (
        PlgError,
        InvalidExtensionPointError,
        DuplicateExtensionPointError,
        UnknownExtensionPointError,
    ):
        assert issubclass(cls, CoreError)
