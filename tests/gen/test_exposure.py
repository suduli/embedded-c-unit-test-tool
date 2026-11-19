"""Tests for WP-GEN-03 static exposure and integration harnesses.

Verifies: TOOL-HAR-030, TOOL-HAR-080.
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
    STATIC_EXPOSURE_MARKER,
    HarnessGenerator,
    IntegrationScopeTooSmallError,
    UnknownUnitError,
    generate_integration_harness,
    generate_with_statics,
)


def _fn(name: str, *, static: bool = False) -> FunctionModel:
    return FunctionModel(
        name=name,
        linkage="internal" if static else "external",
        storage_class="static" if static else "none",
        location=SourceLocation(file="uut.c", line=1),
        return_type="ref:type.int",
    )


def _model(functions: tuple[FunctionModel, ...], *, path: str = "uut.c") -> AnalysisModel:
    return AnalysisModel(
        provenance=ProvenanceModel(
            tool_version="0.1.0", front_end="fixture", generated_at="2026-11-18T00:00:00Z"
        ),
        units=(AnalysisUnit(path=path, status="parsed", functions=functions),),
        types={"type.int": TypeModel(kind="builtin", name="int")},
    )


def test_static_exposure_is_optional_and_off_by_default() -> None:
    """verifies: TOOL-HAR-030"""
    model = _model((_fn("compute"), _fn("hidden", static=True)))
    default = HarnessGenerator(model).generate()
    assert STATIC_EXPOSURE_MARKER not in default.source


def test_static_exposure_includes_uut_source_and_records_statics() -> None:
    """verifies: TOOL-HAR-030"""
    model = _model((_fn("compute"), _fn("hidden", static=True)))
    exposed = generate_with_statics(model)
    assert '#include "uut.c"' in exposed.source
    assert "ectt:exposes-static: int hidden()" in exposed.source
    assert "/* exposes: int compute(void) */" in exposed.source


def test_static_exposure_lists_every_static_function() -> None:
    """verifies: TOOL-HAR-030"""
    model = _model((_fn("s1", static=True), _fn("s2", static=True)))
    exposed = generate_with_statics(model)
    assert "ectt:exposes-static: int s1()" in exposed.source
    assert "ectt:exposes-static: int s2()" in exposed.source


def test_integration_harness_needs_two_units() -> None:
    """verifies: TOOL-HAR-080"""
    model = _model((_fn("compute"),))
    with pytest.raises(IntegrationScopeTooSmallError):
        generate_integration_harness(model, ("uut.c",))
    with pytest.raises(IntegrationScopeTooSmallError):
        generate_integration_harness(model, ())


def test_integration_harness_spans_members() -> None:
    """verifies: TOOL-HAR-080"""
    units = (
        AnalysisUnit(path="a.c", status="parsed", functions=(_fn("from_a"),)),
        AnalysisUnit(path="b.c", status="parsed", functions=(_fn("from_b"),)),
    )
    model = AnalysisModel(
        provenance=ProvenanceModel(
            tool_version="0.1.0", front_end="fixture", generated_at="2026-11-18T00:00:00Z"
        ),
        units=units,
        types={"type.int": TypeModel(kind="builtin", name="int")},
    )
    harness = generate_integration_harness(model, ("a.c", "b.c"))
    assert harness.members == ("a.h", "b.h")
    assert '#include "a.h"' in harness.source
    assert '#include "b.h"' in harness.source
    names = [fn.name for fn in harness.functions]
    assert names == ["from_a", "from_b"]


def test_integration_harness_marks_only_external_stubs() -> None:
    """verifies: TOOL-HAR-080"""
    units = (
        AnalysisUnit(path="a.c", status="parsed", functions=(_fn("from_a"),)),
        AnalysisUnit(path="b.c", status="parsed", functions=(_fn("from_b"),)),
    )
    model = AnalysisModel(
        provenance=ProvenanceModel(
            tool_version="0.1.0", front_end="fixture", generated_at="2026-11-18T00:00:00Z"
        ),
        units=units,
        types={"type.int": TypeModel(kind="builtin", name="int")},
    )
    harness = generate_integration_harness(
        model,
        ("a.c", "b.c"),
        calls={"a.c": ("from_b", "memset")},
        defined_functions={"a.c": ("from_a",), "b.c": ("from_b",)},
    )
    assert harness.stub_required == ("memset",)
    assert "/* ectt:stub-required: memset */" in harness.source
    assert "from_b" not in harness.stub_required


def test_integration_member_not_in_model_is_named_error() -> None:
    """verifies: TOOL-HAR-080"""
    model = _model((_fn("compute"),))
    with pytest.raises(UnknownUnitError):
        generate_integration_harness(model, ("a.c", "ghost.c"))
