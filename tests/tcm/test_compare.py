"""Tests for the expected-value comparison engine (WP-TCM-03).

Covers TOOL-TCD-050 (scalars, enums, pointers, arrays, structs, unions) and
TOOL-TCD-060 (float tolerances) per docs/verification/WP-TCM-03-analysis.md.
"""

from __future__ import annotations

import pytest

from ectt.tcm.compare import (
    ArrayType,
    EnumType,
    Member,
    PointerType,
    ScalarType,
    StructType,
    Tolerance,
    UnionType,
    compare,
)
from ectt.tcm.errors import InvalidComparisonSpecError, ValueParseError

INT = ScalarType("int")
UINT = ScalarType("unsigned int")
CHAR = ScalarType("char")
BOOL = ScalarType("_Bool")
FLOAT = ScalarType("double")


def mismatches(result):  # type: ignore[no-untyped-def]
    return result.mismatches


# --- AC-1: scalars and enums by value ----------------------------------------


def test_scalars_compare_by_value() -> None:
    assert compare(INT, "4095", "4095").matched
    assert compare(INT, "0x1F", "31").matched
    assert compare(INT, "-7", "-7").matched
    assert compare(UINT, "4294967295", "4294967295").matched
    assert compare(CHAR, "A", "65").matched  # single char text vs its code
    assert compare(BOOL, "true", "1").matched
    assert compare(BOOL, "false", "0").matched
    result = compare(INT, "1", "2")
    assert not result.matched
    assert mismatches(result)[0].reason == "value_mismatch"


def test_enum_by_name_and_value() -> None:
    enum = EnumType({"IDLE": "0", "ACTIVE": "1", "ERROR": "0x2"})
    assert compare(enum, "ACTIVE", "1").matched
    assert compare(enum, "ERROR", "2").matched
    assert compare(enum, "IDLE", "ACTIVE").matched is False
    with pytest.raises(ValueParseError, match="declared enumerator"):
        compare(enum, "SLEEPING", "0")


def test_octal_text_is_rejected_not_misread() -> None:
    with pytest.raises(ValueParseError, match="octal"):
        compare(INT, "010", "8")


# --- AC-2: pointers by policy -------------------------------------------------


def test_pointer_null_policy() -> None:
    null_ptr = PointerType(policy="null")
    assert compare(null_ptr, "NULL", "0").matched
    assert compare(null_ptr, "NULL", "0x7fff").matched is False
    assert compare(null_ptr, "0x1000", "0x2000").matched  # nullness only


def test_pointer_address_policy() -> None:
    addr_ptr = PointerType(policy="address")
    assert compare(addr_ptr, "0x7fff0100", "0x7fff0100").matched
    result = compare(addr_ptr, "0x7fff0100", "0x7fff0200")
    assert not result.matched
    assert mismatches(result)[0].reason == "value_mismatch"


def test_pointer_pointee_policy() -> None:
    ptr = PointerType(policy="pointee", pointee=INT)
    assert compare(ptr, "42", "42").matched
    result = compare(ptr, "42", "43")
    assert not result.matched
    assert mismatches(result)[0].path == "value"
    with pytest.raises(InvalidComparisonSpecError):
        PointerType(policy="pointee", pointee=None)


# --- AC-3: arrays and structs member-wise -------------------------------------


def test_array_elementwise_with_count_diagnostic() -> None:
    arr3 = ArrayType(element=INT, length=3)
    assert compare(arr3, ["1", "2", "3"], ["1", "2", "3"]).matched
    result = compare(arr3, ["1", "2", "3"], ["1", "9", "3"])
    assert not result.matched
    assert mismatches(result)[0].path == "value[1]"
    result = compare(arr3, ["1", "2", "3"], ["1", "2"])
    assert mismatches(result)[0].reason == "element_count"


def test_struct_memberwise_in_declared_order() -> None:
    point = StructType(
        members=(Member("x", INT), Member("gain", FLOAT), Member("tag", CHAR))
    )
    result = compare(
        point,
        {"x": "1", "gain": "2.5", "tag": "A"},
        {"tag": "B", "gain": "9.5", "x": "2"},  # actual order must not matter
        tolerances={"value.gain": Tolerance("absolute", 0.25)},
    )
    assert not result.matched
    # declared order: x first, then gain, then tag (all three differ)
    paths = [m.path for m in mismatches(result)]
    assert paths == ["value.x", "value.gain", "value.tag"]


def test_struct_missing_and_unexpected_members() -> None:
    point = StructType(members=(Member("x", INT), Member("y", INT)))
    result = compare(point, {"x": "1", "y": "2"}, {"x": "1"})
    assert mismatches(result)[0].reason == "missing_member"
    result = compare(point, {"x": "1", "y": "2"}, {"x": "1", "y": "2", "z": "3"})
    assert mismatches(result)[0].reason == "unexpected_member"
    with pytest.raises(ValueParseError, match="declared member"):
        compare(point, {"x": "1"}, {"x": "1", "y": "2"})
    with pytest.raises(ValueParseError, match="not a declared member"):
        compare(point, {"x": "1", "q": "2"}, {"x": "1", "y": "2"})


# --- AC-4: unions by the active member ----------------------------------------


def test_union_compares_only_active_member() -> None:
    shape = UnionType(
        members=(Member("raw", UINT), Member("scaled", FLOAT), Member("tag", CHAR))
    )
    # same 4 bytes, different active member: only the active one decides
    assert compare(
        shape, {"raw": "1065353216"}, {"raw": "1065353216"},
        active_members={"value": "raw"},
    ).matched
    assert compare(
        shape, {"raw": "1065353216"}, {"scaled": "1.0", "raw": "999"},
        active_members={"value": "raw"},
    ).matched is False
    result = compare(
        shape, {"scaled": "1.0"}, {"scaled": "1.5"},
        active_members={"value": "scaled"},
    )
    assert not result.matched
    assert mismatches(result)[0].path == "value.scaled"


def test_union_requires_declared_active_member() -> None:
    shape = UnionType(members=(Member("raw", UINT), Member("tag", CHAR)))
    with pytest.raises(InvalidComparisonSpecError, match="active"):
        compare(shape, {"raw": "1"}, {"raw": "1"})
    with pytest.raises(InvalidComparisonSpecError, match="no member"):
        compare(shape, {"raw": "1"}, {"raw": "1"}, active_members={"value": "ghost"})
    with pytest.raises(ValueParseError, match="non-member"):
        compare(
            shape, {"raw": "1"}, {"raw": "1", "bogus": "0"},
            active_members={"value": "raw"},
        )


# --- AC-5: float tolerance -----------------------------------------------------


def test_float_exact_by_default() -> None:
    assert compare(FLOAT, "0.1", "0.1").matched
    assert compare(FLOAT, "0.1", "0.10000000000000001").matched  # same double
    assert compare(FLOAT, "0.1", "0.2").matched is False


def test_float_absolute_tolerance() -> None:
    result = compare(FLOAT, "1.0", "1.0000001", tolerances={"value": Tolerance("absolute", 1e-6)})
    assert result.matched
    result = compare(FLOAT, "1.0", "1.001", tolerances={"value": Tolerance("absolute", 1e-6)})
    assert not result.matched


def test_float_relative_tolerance() -> None:
    result = compare(FLOAT, "1000.0", "1000.5", tolerances={"value": Tolerance("relative", 1e-3)})
    assert result.matched
    result = compare(FLOAT, "1000.0", "1002.0", tolerances={"value": Tolerance("relative", 1e-3)})
    assert not result.matched
    # relative tolerance with a zero expected degenerates to exact
    result = compare(FLOAT, "0.0", "0.0000001", tolerances={"value": Tolerance("relative", 0.5)})
    assert not result.matched
    assert compare(FLOAT, "0.0", "0.0", tolerances={"value": Tolerance("relative", 0.5)}).matched


def test_nan_matches_only_nan() -> None:
    assert compare(FLOAT, "nan", "nan").matched
    assert compare(FLOAT, "nan", "1.0").matched is False
    assert compare(FLOAT, "inf", "inf").matched
    assert compare(FLOAT, "-inf", "inf").matched is False


def test_tolerance_on_non_float_is_error() -> None:
    with pytest.raises(InvalidComparisonSpecError, match="float"):
        compare(INT, "1", "2", tolerances={"value": Tolerance("absolute", 0.5)})


def test_both_tolerance_modes_is_error() -> None:
    bad = Tolerance("absolute", 1.0)
    with pytest.raises(InvalidComparisonSpecError):
        Tolerance("diagonal", 1.0)  # type: ignore[arg-type]
    with pytest.raises(InvalidComparisonSpecError):
        Tolerance("absolute", -1.0)
    assert bad.mode == "absolute"


# --- AC-6/7: determinism -------------------------------------------------------


def test_diagnostics_are_in_declared_order() -> None:
    point = StructType(members=(Member("a", INT), Member("b", INT), Member("c", INT)))
    result = compare(
        point,
        {"a": "1", "b": "2", "c": "3"},
        {"a": "9", "b": "2", "c": "8"},
    )
    paths = [m.path for m in mismatches(result)]
    assert paths == ["value.a", "value.c"]  # b matches; declared order kept


def test_float_rendering_is_canonical() -> None:
    result = compare(FLOAT, "0.3", "0.3000001")
    mismatch = mismatches(result)[0]
    assert mismatch.expected == "0.3"
    assert mismatch.actual == "0.3000001"
