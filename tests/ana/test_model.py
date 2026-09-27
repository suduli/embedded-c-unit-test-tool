# implements: DSN-ANA-090
"""Unit tests for ectt.ana model classes.

Verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from ectt.ana.model import (
    AnalysisUnit,
    Diagnostic,
    EnumeratorModel,
    FunctionModel,
    GlobalAccessModel,
    ParameterModel,
    ParsedTranslationUnit,
    ParseResult,
    SourceLocation,
    StructMemberModel,
    TypeModel,
)


def test_diagnostic_properties_and_formatting() -> None:
    """verifies: TOOL-PAR-010, DSN-ANA-090"""
    diag_error = Diagnostic(
        message="use of undeclared identifier 'foo'",
        severity="error",
        severity_code=3,
        file="src/driver.c",
        line=42,
        column=12,
        category="Semantic Issue",
    )

    assert diag_error.message == "use of undeclared identifier 'foo'"
    assert diag_error.severity == "error"
    assert diag_error.severity_code == 3
    assert diag_error.file == "src/driver.c"
    assert diag_error.line == 42
    assert diag_error.column == 12
    assert diag_error.category == "Semantic Issue"
    assert diag_error.is_error is True
    assert str(diag_error) == "src/driver.c:42:12: error: use of undeclared identifier 'foo'"

    d_dict = diag_error.to_dict()
    assert d_dict == {
        "message": "use of undeclared identifier 'foo'",
        "severity": "error",
        "severity_code": 3,
        "file": "src/driver.c",
        "line": 42,
        "column": 12,
        "category": "Semantic Issue",
    }

    # Immutability
    with pytest.raises(FrozenInstanceError):
        diag_error.message = "new message"  # type: ignore[misc]

    # Non-error diagnostic
    diag_warning = Diagnostic(
        message="unused variable 'x'",
        severity="warning",
        severity_code=2,
    )
    assert diag_warning.is_error is False
    assert str(diag_warning) == "warning: unused variable 'x'"


def test_parsed_translation_unit_properties_and_serialization() -> None:
    """verifies: TOOL-PAR-010, DSN-ANA-090"""
    diag1 = Diagnostic(message="implicit conversion", severity="warning", severity_code=2)
    diag2 = Diagnostic(message="syntax error", severity="error", severity_code=3, file="main.c", line=1)

    ptu_failed = ParsedTranslationUnit(
        source_path="src/main.c",
        status="failed",
        diagnostics=(diag1, diag2),
    )

    assert ptu_failed.source_path == "src/main.c"
    assert ptu_failed.status == "failed"
    assert ptu_failed.is_parsed is False
    assert ptu_failed.is_failed is True
    assert ptu_failed.has_errors is True
    assert len(ptu_failed.diagnostics) == 2
    assert len(ptu_failed.errors) == 1
    assert ptu_failed.errors[0] == diag2
    assert len(ptu_failed.warnings) == 1
    assert ptu_failed.warnings[0] == diag1

    data = ptu_failed.to_dict()
    assert data["path"] == "src/main.c"
    assert data["status"] == "failed"
    assert len(data["diagnostics"]) == 2

    # Deterministic JSON serialization
    serialized = ptu_failed.to_json()
    assert isinstance(serialized, str)
    decoded = json.loads(serialized)
    assert decoded["status"] == "failed"

    # Verify ParseResult alias
    assert ParseResult is ParsedTranslationUnit

    # Immutability
    with pytest.raises(FrozenInstanceError):
        ptu_failed.status = "parsed"  # type: ignore[misc]


def test_function_and_type_models_properties_and_immutability() -> None:
    """verifies: TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-020"""
    param = ParameterModel(name="val", type="ref:type.int", direction="in")
    assert param.to_dict() == {"name": "val", "type": "ref:type.int", "direction": "in"}
    with pytest.raises(FrozenInstanceError):
        param.direction = "out"  # type: ignore[misc]

    glob = GlobalAccessModel(name="g_count", access="rw")
    assert glob.to_dict() == {"name": "g_count", "access": "rw"}
    with pytest.raises(FrozenInstanceError):
        glob.access = "r"  # type: ignore[misc]

    fn = FunctionModel(
        name="test_func",
        linkage="external",
        storage_class="none",
        location=SourceLocation(file="src/test.c", line=10),
        return_type="ref:type.void",
        parameters=(param,),
        globals=(glob,),
    )
    fn_dict = fn.to_dict()
    assert fn_dict["name"] == "test_func"
    assert fn_dict["location"] == {"file": "src/test.c", "line": 10, "origin": "project"}
    with pytest.raises(FrozenInstanceError):
        fn.name = "renamed"  # type: ignore[misc]

    mem = StructMemberModel(name="x", type="ref:type.int", bit_width=4)
    assert mem.to_dict() == {"name": "x", "type": "ref:type.int", "bit_width": 4}

    enum_val = EnumeratorModel(name="STATUS_OK", value=0)
    assert enum_val.to_dict() == {"name": "STATUS_OK", "value": 0}

    t_struct = TypeModel(
        kind="struct",
        name="MyStruct",
        location=SourceLocation(file="src/types.h", line=20),
        members=(mem,),
    )
    t_dict = t_struct.to_dict()
    assert t_dict["kind"] == "struct"
    assert t_dict["name"] == "MyStruct"
    assert len(t_dict["members"]) == 1

    unit = AnalysisUnit(
        path="src/test.c",
        status="parsed",
        functions=(fn,),
        types={"type.MyStruct": t_struct},
    )
    u_dict = unit.to_dict()
    assert u_dict["path"] == "src/test.c"
    assert u_dict["status"] == "parsed"
    assert "type.MyStruct" in u_dict["types"]
    assert json.loads(unit.to_json())["path"] == "src/test.c"
