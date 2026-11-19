"""Tests for the WP-GEN-02 framework back-ends.

Covers: built-in Unity/cmocka descriptors registered via the declarative
path, rendering the harness surface, the C++-free scan, adding a framework
by descriptor only, and registry discipline.

Verifies: TOOL-HAR-060, TOOL-HAR-070, TOOL-PLG-030.
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
    FrameworkBackendError,
    GeneratedHarness,
    HarnessGenerator,
    UnknownBackendError,
    register_framework_builtins,
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


def _registry() -> BackendRegistry:
    registry = BackendRegistry()
    register_framework_builtins(registry)
    return registry


def test_builtin_unity_and_cmocka_registered() -> None:
    """verifies: TOOL-HAR-060"""
    registry = _registry()
    assert registry.list_ids() == (CMOCKA_BACKEND_ID, UNITY_BACKEND_ID)
    assert registry.lookup("unity").framework_header == "unity.h"
    assert registry.lookup("cmocka").framework_header == "cmocka.h"


def test_unity_render_includes_framework_header_and_hooks() -> None:
    """verifies: TOOL-HAR-060"""
    rendered = render_framework_test("unity", _harness(), _registry())
    assert '#include "uut.h"' in rendered
    assert '#include "unity.h"' in rendered
    assert "void setUp(void)" in rendered
    assert "void tearDown(void)" in rendered
    assert "/* exposes: int compute(void) */" in rendered


def test_cmocka_render_includes_framework_header_and_hooks() -> None:
    """verifies: TOOL-HAR-060"""
    rendered = render_framework_test("cmocka", _harness(), _registry())
    assert '#include "cmocka.h"' in rendered
    assert "int setup(void **state)" in rendered
    assert "int teardown(void **state)" in rendered


def test_render_output_passes_cpp_free_scan() -> None:
    """verifies: TOOL-HAR-060"""
    for backend_id in (UNITY_BACKEND_ID, CMOCKA_BACKEND_ID):
        rendered = render_framework_test(backend_id, _harness(), _registry())
        for cpp in ("::", "class ", "template<"):
            assert cpp not in rendered


def test_cpp_construct_in_template_is_named_error() -> None:
    """verifies: TOOL-HAR-060"""
    registry = _registry()
    registry.register(
        FrameworkBackend(
            backend_id="cpp_accident",
            framework_header="thing.h",
            template='/* oops */ std::vector<int> v;\n#include "{uut_header}"',
        )
    )
    with pytest.raises(CppConstructInOutputError):
        render_framework_test("cpp_accident", _harness(), registry)


def test_new_framework_needs_only_a_descriptor() -> None:
    """verifies: TOOL-PLG-030"""
    registry = _registry()
    registry.register_descriptor(
        {
            "backend_id": "acme_framework",
            "framework_header": "acme.h",
            "template": (
                '/* user framework */\n#include "{uut_header}"\n'
                '#include "{framework_header}"\n{function_prototypes}\n'
            ),
        }
    )
    rendered = render_framework_test("acme_framework", _harness(), registry)
    assert '#include "acme.h"' in rendered
    assert "acme_framework" in registry.list_ids()


def test_descriptor_missing_field_is_named_error() -> None:
    """verifies: TOOL-PLG-030"""
    with pytest.raises(FrameworkBackendError) as excinfo:
        FrameworkBackend.from_descriptor({"backend_id": "x", "template": "{uut_header}"})
    assert "framework_header" in str(excinfo.value)


def test_template_without_uut_header_slot_rejected() -> None:
    """verifies: TOOL-HAR-070"""
    with pytest.raises(FrameworkBackendError):
        FrameworkBackend(backend_id="bad", framework_header="b.h", template="nothing")


def test_duplicate_and_unknown_ids() -> None:
    """verifies: TOOL-HAR-060"""
    registry = _registry()
    with pytest.raises(DuplicateBackendError):
        register_framework_builtins(registry)
    with pytest.raises(UnknownBackendError):
        registry.lookup("nope")


def test_rendering_is_deterministic() -> None:
    """verifies: TOOL-HAR-060"""
    harness = _harness()
    registry = _registry()
    assert render_framework_test("unity", harness, registry) == render_framework_test(
        "unity", harness, registry
    )
