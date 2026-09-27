# implements: DSN-PRJ-010, DSN-PRJ-030
"""Tests for schema version dispatch and file kind registry.

Verifies: TOOL-PRJ-020, TOOL-PRJ-030, DSN-PRJ-010.
"""

from __future__ import annotations

import pytest

from ectt.prj.errors import (
    InvalidSchemaVersionError,
    MigrationRequiredError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
)
from ectt.prj.model import (
    DEFAULT_KIND_REGISTRY,
    PROJECT_KIND,
    FileKind,
    KindRegistry,
    dispatch_schema_version,
)


def test_schema_version_supported() -> None:
    """verifies: TOOL-PRJ-020, TOOL-PRJ-030, DSN-PRJ-010"""
    doc = {"schema_version": "1", "name": "test"}
    version = dispatch_schema_version(doc, PROJECT_KIND)
    assert version == 1

    doc_int = {"schema_version": 1, "name": "test"}
    version_int = dispatch_schema_version(doc_int, PROJECT_KIND)
    assert version_int == 1


def test_schema_version_absent() -> None:
    """verifies: TOOL-PRJ-020, TOOL-PRJ-030, DSN-PRJ-010"""
    doc = {"name": "missing_version"}
    with pytest.raises(MissingSchemaVersionError) as exc_info:
        dispatch_schema_version(doc, PROJECT_KIND, file_path="ectt.project")
    assert exc_info.value.reason == "missing_schema_version"
    assert "ectt.project" in str(exc_info.value)


def test_schema_version_non_integer() -> None:
    """verifies: TOOL-PRJ-020, TOOL-PRJ-030, DSN-PRJ-010"""
    invalid_versions = ["foo", "1.2.3", "v1", "", "1.0", None, [1]]
    for bad_ver in invalid_versions:
        doc = {"schema_version": bad_ver, "name": "test"}
        with pytest.raises(InvalidSchemaVersionError) as exc_info:
            dispatch_schema_version(doc, PROJECT_KIND, file_path="ectt.project")
        assert exc_info.value.reason == "invalid_schema_version"


def test_schema_version_greater_than_max() -> None:
    """verifies: TOOL-PRJ-030, DSN-PRJ-010"""
    doc = {"schema_version": "2", "name": "future_version"}
    with pytest.raises(UnsupportedSchemaVersionError) as exc_info:
        dispatch_schema_version(doc, PROJECT_KIND, file_path="ectt.project")
    assert exc_info.value.reason == "unsupported_schema_version"
    assert exc_info.value.version == 2
    assert exc_info.value.max_version == 1
    assert "newer version of ectt is required" in str(exc_info.value)


def test_schema_version_less_than_min() -> None:
    """verifies: TOOL-PRJ-030, DSN-PRJ-010"""
    kind = FileKind(name="custom", file_pattern="*.custom", min_version=3, max_version=5)
    doc = {"schema_version": "2", "name": "legacy"}
    with pytest.raises(MigrationRequiredError) as exc_info:
        dispatch_schema_version(doc, kind, file_path="test.custom")
    assert exc_info.value.reason == "migration_required"
    assert exc_info.value.version == 2
    assert exc_info.value.min_version == 3
    assert "migration is required" in str(exc_info.value)


def test_kind_registry() -> None:
    """verifies: TOOL-PRJ-020, DSN-PRJ-010"""
    registry = KindRegistry()
    registry.register(PROJECT_KIND)

    assert registry.get("project") == PROJECT_KIND
    assert registry.find_by_filename("ectt.project") == PROJECT_KIND
    assert registry.find_by_filename("unknown.file") is None

    with pytest.raises(KeyError):
        registry.get("nonexistent")
