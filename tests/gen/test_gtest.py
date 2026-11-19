"""Tests for the WP-GEN-10 optional GoogleTest back-end.

Verifies: TOOL-HAR-065.
"""

from __future__ import annotations

import pytest

from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    FunctionModel,
    ProvenanceModel,
    SourceLocation,
    TypeModel,
)
from ectt.gen import (
    CMOCKA_BACKEND_ID,
    UNITY_BACKEND_ID,
    BackendRegistry,
    CppConstructInOutputError,
    DuplicateBackendError,
    FrameworkBackend,
    GeneratedHarness,
    HarnessGenerator,
    register_framework_builtins,
    register_gtest_backend,
    render_framework_test,
)


def _harness() -> GeneratedHarness:
    model = AnalysisModel(
        provenance=ProvenanceModel(
            tool_version="0.1.0", front_end="fixture", generated_at="2026-11-18T00:00:00Z"
        ),
        units=(
            AnalysisUnit(
                path="uut.c",
                status="parsed",
                functions=(
                    FunctionModel(
                        name="compute",
                        linkage="external",
                        storage_class="none",
                        location=SourceLocation(file="uut.c", line=1),
                        return_type="ref:type.int",
                    ),
                ),
            ),
        ),
        types={"type.int": TypeModel(kind="builtin", name="int")},
    )
    return HarnessGenerator(model).generate()


def test_gtest_is_not_among_the_builtins() -> None:
    """verifies: TOOL-HAR-065"""
    registry = BackendRegistry()
    register_framework_builtins(registry)
    assert registry.list_ids() == (CMOCKA_BACKEND_ID, UNITY_BACKEND_ID)


def test_gtest_registers_on_explicit_request() -> None:
    """verifies: TOOL-HAR-065"""
    registry = BackendRegistry()
    register_framework_builtins(registry)
    register_gtest_backend(registry)
    assert "googletest" in registry.list_ids()
    backend = registry.lookup("googletest")
    assert backend.framework_header == "gtest/gtest.h"
    assert backend.host_only is True
    assert backend.cpp_allowed is True


def test_gtest_render_produces_google_test_style_output() -> None:
    """verifies: TOOL-HAR-065"""
    registry = BackendRegistry()
    register_gtest_backend(registry)
    rendered = render_framework_test("googletest", _harness(), registry)
    assert '#include "gtest/gtest.h"' in rendered
    assert '#include "uut.h"' in rendered
    assert "host-only" in rendered
    assert "namespace" in rendered  # C++ constructs present, no error


def test_gtest_render_is_exempt_from_cpp_free_scan() -> None:
    """verifies: TOOL-HAR-065"""
    registry = BackendRegistry()
    register_gtest_backend(registry)
    rendered = render_framework_test("googletest", _harness(), registry)
    assert "::" in rendered or "namespace" in rendered  # survives the scan


def test_cpp_free_scan_still_applies_to_other_backends() -> None:
    """verifies: TOOL-HAR-065"""
    registry = BackendRegistry()
    register_framework_builtins(registry)
    registry.register(
        FrameworkBackend(
            backend_id="cpp_accident",
            framework_header="thing.h",
            template='/* oops */ std::vector<int> v;\n#include "{uut_header}"',
        )
    )
    with pytest.raises(CppConstructInOutputError):
        render_framework_test("cpp_accident", _harness(), registry)


def test_gtest_double_registration_refused() -> None:
    """verifies: TOOL-HAR-065"""
    registry = BackendRegistry()
    register_gtest_backend(registry)
    with pytest.raises(DuplicateBackendError):
        register_gtest_backend(registry)


def test_descriptor_declares_host_only_through_the_data_path() -> None:
    """verifies: TOOL-HAR-065"""
    backend = FrameworkBackend.from_descriptor(
        {
            "backend_id": "googletest",
            "framework_header": "gtest/gtest.h",
            "template": '#include "{uut_header}"\n',
            "cpp_allowed": True,
            "host_only": True,
        }
    )
    assert backend.cpp_allowed and backend.host_only
    plain = FrameworkBackend.from_descriptor(
        {"backend_id": "x", "framework_header": "x.h", "template": '{uut_header}'}
    )
    assert not plain.cpp_allowed and not plain.host_only
