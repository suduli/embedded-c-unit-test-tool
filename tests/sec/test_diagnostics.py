"""Tests for the WP-SEC-04 diagnostic content control.

Covers: location-only formatting, verbatim-source rejection (including
whitespace variants and length exemption), clean diagnostics, and the exact
bundle manifest.

Verifies: TOOL-SEC-120.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.sec import (
    BUNDLE_ENTRIES,
    BUNDLE_EXCLUSIONS,
    MIN_SOURCE_LINE_LENGTH,
    SourceContentInDiagnosticError,
    assert_no_source_content,
    bundle_manifest,
    location_reference,
)

SOURCE_LINES = [
    "int compute(int a, int b) {",
    "    return a * scale_factor + offset_value;",
    "}",
    "static int g_state = 42;",
]


def test_location_reference_formats_path_line_column() -> None:
    """verifies: TOOL-SEC-120"""
    assert location_reference("src/uut.c") == "src/uut.c"
    assert location_reference("src/uut.c", 12) == "src/uut.c:12"
    assert location_reference("src/uut.c", 12, 4) == "src/uut.c:12:4"


def test_location_reference_carries_no_source_text() -> None:
    """verifies: TOOL-SEC-120"""
    reference = location_reference("src/uut.c", 12, 4)
    for source_line in SOURCE_LINES:
        assert source_line.strip() not in reference


def test_guard_rejects_verbatim_source_line() -> None:
    """verifies: TOOL-SEC-120"""
    diagnostic = (
        "analysis failed at src/uut.c:2\n"
        "    return a * scale_factor + offset_value;\n"
    )
    with pytest.raises(SourceContentInDiagnosticError) as excinfo:
        assert_no_source_content(diagnostic, SOURCE_LINES, origin="src/uut.c:2")
    assert "src/uut.c:2" in str(excinfo.value)
    assert "scale_factor" in str(excinfo.value)


def test_guard_rejects_whitespace_variant() -> None:
    """verifies: TOOL-SEC-120"""
    diagnostic = "hint: static int g_state = 42;   \n"
    with pytest.raises(SourceContentInDiagnosticError):
        assert_no_source_content(diagnostic, SOURCE_LINES)


def test_guard_allows_location_and_messages() -> None:
    """verifies: TOOL-SEC-120"""
    diagnostic = (
        "analysis failed at src/uut.c:2\n"
        "reason=unresolved_include\n"
        "see src/uut.c:2:9 for the include that could not be resolved\n"
    )
    assert_no_source_content(diagnostic, SOURCE_LINES)


def test_guard_exempts_short_source_lines() -> None:
    """verifies: TOOL-SEC-120"""
    # "}" and other short lines are exempt: they cannot identify a location
    # and legitimately appear in tool messages (e.g. echoed flags).
    diagnostic = "flags echo: -c -O0 }\n"
    assert_no_source_content(diagnostic, SOURCE_LINES)


def test_guard_threshold_is_documented() -> None:
    """verifies: TOOL-SEC-120"""
    assert MIN_SOURCE_LINE_LENGTH >= 8


def test_guard_with_no_forbidden_lines_passes() -> None:
    """verifies: TOOL-SEC-120"""
    assert_no_source_content("anything goes {}", [])


def test_bundle_manifest_documents_contents_exactly() -> None:
    """verifies: TOOL-SEC-120"""
    manifest = bundle_manifest()
    assert len(manifest.entries) >= 4
    assert all(entry.strip() for entry in manifest.entries)
    assert manifest.entries == BUNDLE_ENTRIES


def test_bundle_manifest_excludes_source_content() -> None:
    """verifies: TOOL-SEC-120"""
    manifest = bundle_manifest()
    assert manifest.exclusions[0].startswith("user source code content")
    assert len(manifest.exclusions) >= 3
    assert manifest.exclusions == BUNDLE_EXCLUSIONS


def test_bundle_manifest_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-SEC-120"""
    manifest = bundle_manifest()
    assert manifest.to_dict() == bundle_manifest().to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        manifest.entries = ()  # type: ignore[misc]
