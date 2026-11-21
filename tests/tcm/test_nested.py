# implements: TOOL-TCD-040, TOOL-TCD-050
"""Nested struct, array and union expectations in test case files (FIX-TCMNEST).

Verifies: expected values for struct, array and union are authored as path keys in the
unchanged flat ``.tests`` form, validated against the declared type, consumed by the
comparison engine, reported with a path on mismatch, and unknown members refused;
existing flat files stay valid and byte-stable.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from ectt.ana.model import DimensionModel, EnumeratorModel, StructMemberModel, TypeModel
from ectt.prj.yaml_adapter import RestrictedYamlAdapter
from ectt.tcm import datacases as dd
from ectt.tcm.compare import (
    ArrayType,
    EnumType,
    Member,
    PointerType,
    ScalarType,
    StructType,
    Tolerance,
    UnionType,
)
from ectt.tcm.errors import (
    InvalidComparisonSpecError,
    InvalidTestCasesFileError,
    ValueParseError,
)
from ectt.tcm.nested import (
    compare_expected,
    ctype_from_model,
    expected_trees,
    flatten_expected,
    is_nested_key,
    parse_expected_path,
    validate_expected_keys,
)

UCHAR = ScalarType("unsigned char")
HEADER = StructType((Member("len", UCHAR), Member("flags", UCHAR)))
FRAME = StructType((Member("header", HEADER), Member("payload", ArrayType(UCHAR, 3))))
READING = UnionType((Member("as_int", ScalarType("int")), Member("as_float", ScalarType("float"))))
DECLARED = {"g_frame": FRAME, "g_reading": READING, "g_count": ScalarType("int")}

ACTUAL = {
    "g_frame": {"header": {"len": "4", "flags": "1"}, "payload": ["16", "32", "48"]},
    "g_reading": {"as_int": "7", "as_float": "0.5"},
    "g_count": "3",
}
EXPECTED = {
    "g_frame.header.len": "4",
    "g_frame.header.flags": "1",
    "g_frame.payload[0]": "0x10",
    "g_frame.payload[1]": "0x20",
    "g_frame.payload[2]": "0x30",
    "g_reading.as_int": "7",
    "g_count": "3",
}


def _reason(call: Any) -> str:
    with pytest.raises((ValueParseError, InvalidComparisonSpecError)) as excinfo:
        call()
    return str(excinfo.value.reason)


# --- the path syntax ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "root", "steps"),
    [
        ("g_state", "g_state", ()),
        ("weird-name", "weird-name", ()),
        ("g.member", "g", ("member",)),
        ("g[3]", "g", (3,)),
        ("g.a.b", "g", ("a", "b")),
        ("g.a[0].b[12]", "g", ("a", 0, "b", 12)),
        ("g[0][1]", "g", (0, 1)),
    ],
)
def test_paths_parse_into_root_and_steps(key: str, root: str, steps: tuple[Any, ...]) -> None:
    path = parse_expected_path(key)
    assert (path.root, path.steps) == (root, steps)


@pytest.mark.parametrize("key", ["", "a.", ".a", "a..b", "a[", "a[x]", "a[01]", "a[-1]", "a[]", "1a.b", "a.b c", "a.1", "a]b[0]", "a.b!"])
def test_malformed_paths_are_refused(key: str) -> None:
    if key == "":
        assert _reason(lambda: parse_expected_path(key)) == "invalid_value_path"
    else:
        assert _reason(lambda: parse_expected_path(key)) == "invalid_value_path"


def test_plain_keys_are_not_nested_and_are_never_validated_as_paths() -> None:
    assert not is_nested_key("g_state") and is_nested_key("g.x") and is_nested_key("g[0]")
    validate_expected_keys({"g_state": "1", "odd name": "2", "g.x": "3"})


# --- trees ---------------------------------------------------------------------------------------


def test_entries_group_by_root_into_member_and_index_nodes() -> None:
    trees = expected_trees({"a.x": "1", "a.y": "2", "b[1]": "9", "b[0]": "8", "c": "z"})
    assert trees == {"a": {"x": "1", "y": "2"}, "b": {0: "8", 1: "9"}, "c": "z"}


@pytest.mark.parametrize(
    ("entries", "reason"),
    [
        ({"a": "1", "a.x": "2"}, "conflicting_path"),
        ({"a.x": "1", "a.x.y": "2"}, "conflicting_path"),
        ({"a.x.y": "1", "a.x": "2"}, "conflicting_path"),
        ({"a.x": "1", "a[0]": "2"}, "mixed_path"),
    ],
)
def test_conflicting_or_mixed_paths_are_refused(entries: dict[str, str], reason: str) -> None:
    assert _reason(lambda: expected_trees(entries)) == reason


# --- comparison through the engine ---------------------------------------------------------------


def test_matching_nested_values_compare_clean() -> None:
    results = compare_expected(EXPECTED, DECLARED, ACTUAL)

    assert sorted(results) == ["g_count", "g_frame", "g_reading"]
    assert all(r.matched for r in results.values())


def test_a_mismatch_in_an_array_element_names_its_path() -> None:
    actual = {**ACTUAL, "g_frame": {**ACTUAL["g_frame"], "payload": ["16", "33", "48"]}}

    result = compare_expected(EXPECTED, DECLARED, actual)["g_frame"]

    assert not result.matched
    (mismatch,) = result.mismatches
    assert (mismatch.path, mismatch.expected, mismatch.actual, mismatch.reason) == ("g_frame.payload[1]", "0x20", "33", "value_mismatch")


def test_a_mismatch_in_a_nested_member_names_its_full_path() -> None:
    actual = {**ACTUAL, "g_frame": {**ACTUAL["g_frame"], "header": {"len": "5", "flags": "1"}}}

    (mismatch,) = compare_expected(EXPECTED, DECLARED, actual)["g_frame"].mismatches

    assert mismatch.path == "g_frame.header.len"


def test_several_mismatches_come_back_in_declared_order() -> None:
    actual = {"g_frame": {"header": {"len": "9", "flags": "8"}, "payload": ["16", "32", "48"]}}
    result = compare_expected({k: v for k, v in EXPECTED.items() if k.startswith("g_frame")}, {"g_frame": FRAME}, actual)["g_frame"]
    assert [m.path for m in result.mismatches] == ["g_frame.header.len", "g_frame.header.flags"]


def test_only_the_named_union_member_is_compared() -> None:
    different_float = {**ACTUAL, "g_reading": {"as_int": "7", "as_float": "99.0"}}
    assert compare_expected(EXPECTED, DECLARED, different_float)["g_reading"].matched

    wrong_int = {**ACTUAL, "g_reading": {"as_int": "8", "as_float": "0.5"}}
    (mismatch,) = compare_expected(EXPECTED, DECLARED, wrong_int)["g_reading"].mismatches
    assert mismatch.path == "g_reading.as_int"


def test_a_float_member_honours_a_tolerance_given_by_its_path() -> None:
    expected = {"g_reading.as_float": "0.5"}
    actual = {"g_reading": {"as_int": "0", "as_float": "0.75"}}

    assert not compare_expected(expected, DECLARED, actual)["g_reading"].matched
    tolerant = compare_expected(expected, DECLARED, actual, tolerances={"g_reading.as_float": Tolerance("absolute", 0.5)})
    assert tolerant["g_reading"].matched


def test_a_two_dimensional_array_reports_both_indices() -> None:
    declared = {"m": ArrayType(ArrayType(UCHAR, 2), 2)}
    entries = {"m[0][0]": "1", "m[0][1]": "2", "m[1][0]": "3", "m[1][1]": "4"}

    (mismatch,) = compare_expected(entries, declared, {"m": [["1", "2"], ["3", "9"]]})["m"].mismatches

    assert mismatch.path == "m[1][1]"


# --- authoring errors are refused, not turned into mismatches ----------------------------------------


@pytest.mark.parametrize(
    ("entries", "reason"),
    [
        ({"g_frame.header.lenn": "4"}, "unknown_member"),
        ({"g_frame.nothing": "1"}, "unknown_member"),
        ({"g_reading.as_double": "1"}, "unknown_member"),
        ({"g_frame.payload[3]": "1"}, "index_out_of_range"),
        ({"g_frame.header.len": "4", "g_frame.header.flags": "1", "g_frame.payload[0]": "1", "g_frame.payload[2]": "3"}, "missing_element"),
        ({"g_frame.payload.x": "1"}, "member_in_array"),
        ({"g_frame.header[0]": "1"}, "index_in_struct"),
        ({"g_frame.header.len": "4", "g_frame.payload[0]": "1", "g_frame.payload[1]": "2", "g_frame.payload[2]": "3"}, "missing_member"),
        ({"g_frame": "1"}, "scalar_for_composite"),
        ({"g_count.x": "1"}, "composite_for_scalar"),
        ({"g_reading.as_int": "1", "g_reading.as_float": "2"}, "ambiguous_union"),
        ({"g_nope": "1"}, "unknown_variable"),
    ],
)
def test_authoring_errors_are_refused_with_a_reason(entries: dict[str, str], reason: str) -> None:
    assert _reason(lambda: compare_expected(entries, DECLARED, ACTUAL)) == reason


def test_an_unknown_member_is_refused_with_its_path_and_the_declared_members() -> None:
    with pytest.raises(ValueParseError) as excinfo:
        compare_expected({"g_frame.header.lenn": "4"}, DECLARED, ACTUAL)
    message = excinfo.value.message
    assert "g_frame.header.lenn" in message and "len" in message and "flags" in message


def test_an_observed_value_must_be_supplied_for_every_expectation() -> None:
    assert _reason(lambda: compare_expected({"g_count": "3"}, DECLARED, {})) == "missing_actual"


def test_pointer_to_struct_expectations_follow_the_pointee_policy() -> None:
    declared = {"p": PointerType("pointee", HEADER), "q": PointerType("null")}
    entries = {"p.len": "4", "p.flags": "1", "q": "NULL"}

    assert all(r.matched for r in compare_expected(entries, declared, {"p": {"len": "4", "flags": "1"}, "q": "0"}).values())
    assert _reason(lambda: compare_expected({"q.x": "1"}, declared, {"q": "0"})) == "composite_for_scalar"


# --- flattening --------------------------------------------------------------------------------------------


def test_flatten_is_the_inverse_of_building_the_tree() -> None:
    flat = flatten_expected("g_frame", ACTUAL["g_frame"])

    assert flat == {
        "g_frame.header.flags": "1",
        "g_frame.header.len": "4",
        "g_frame.payload[0]": "16",
        "g_frame.payload[1]": "32",
        "g_frame.payload[2]": "48",
    }
    assert compare_expected(flat, {"g_frame": FRAME}, {"g_frame": ACTUAL["g_frame"]})["g_frame"].matched


def test_flatten_is_deterministic_and_handles_a_scalar() -> None:
    assert list(flatten_expected("g", {"b": "2", "a": "1"})) == ["g.a", "g.b"]
    assert flatten_expected("g", "5") == {"g": "5"}


@pytest.mark.parametrize(("root", "value"), [("bad name", "1"), ("g", {"a b": "1"}), ("g", {"a": 5}), ("g", {}), ("g", [])])
def test_flatten_refuses_what_cannot_be_authored(root: str, value: Any) -> None:
    with pytest.raises(ValueParseError):
        flatten_expected(root, value)


# --- the .tests file --------------------------------------------------------------------------------------


def _nested_case() -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id="frame.check",
            unit="src/frame.c",
            function="frame_fill",
            inputs=dd.TestCaseInputs(),
            expected=dd.TestCaseExpected(global_finals=EXPECTED, out_parameters={"out.payload[0]": "1", "out.len": "2"}),
            stubs=(),
        )
    )


def test_nested_expectations_round_trip_through_the_tests_file() -> None:
    case = _nested_case()
    text = dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(case,)))

    (parsed,) = dd.parse_test_cases_document(RestrictedYamlAdapter().load(text)).cases

    assert parsed == case
    assert dict(parsed.expected.global_finals) == EXPECTED
    assert not parsed.stale
    assert "g_frame.payload[1]" in text


def test_file_expectations_feed_the_comparison_directly() -> None:
    text = dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(_nested_case(),)))
    (parsed,) = dd.parse_test_cases_document(RestrictedYamlAdapter().load(text)).cases

    results = compare_expected(parsed.expected.global_finals, DECLARED, ACTUAL)

    assert all(r.matched for r in results.values())


@pytest.mark.parametrize("section", ["globals", "out_parameters"])
@pytest.mark.parametrize("key", ["a.", "a[x]", "a..b", "a[01]"])
def test_malformed_paths_in_a_file_are_refused_with_the_key(section: str, key: str) -> None:
    doc = {
        "schema_version": "1",
        "test_cases": [
            {
                "id": "c1", "unit": "u.c", "function": "f", "inputs": {"parameters": {}}, "stubs": {},
                "expected": {section: {key: "1"}},
            }
        ],
    }
    with pytest.raises(InvalidTestCasesFileError) as excinfo:
        dd.parse_test_cases_document(doc)
    assert f"'{key}'" in excinfo.value.message and section in excinfo.value.message


def test_plain_and_dotted_names_that_were_valid_before_stay_valid() -> None:
    doc = {
        "schema_version": "1",
        "test_cases": [
            {
                "id": "c1", "unit": "u.c", "function": "f", "inputs": {"parameters": {}}, "stubs": {},
                "expected": {"globals": {"weird-name": "1", "g_adc_state.last_error": "0", "g_state": "3"}},
            }
        ],
    }
    (case,) = dd.parse_test_cases_document(doc).cases
    assert set(case.expected.global_finals) == {"weird-name", "g_adc_state.last_error", "g_state"}


def test_a_flat_file_dumps_byte_for_byte_as_before_and_keeps_its_digest() -> None:
    """Golden text and digest were produced by the code before this change (main at 7765236)."""
    golden = (Path(__file__).parent / "_golden_flat.txt").read_text(encoding="utf-8")
    doc = {
        "schema_version": "1",
        "test_cases": [
            {
                "id": "adc.scale.zero", "unit": "src/adc.c", "function": "adc_scale",
                "inputs": {"parameters": {"raw": "0", "gain": "2"}, "globals": {"g_mode": "1"}},
                "expected": {"return": "0", "globals": {"g_state": "3", "g_adc_state.last_error": "0"}, "out_parameters": {"result": "9"}},
                "stubs": {"hal_read": {"mode": "sequence", "returns": ["5", "6"], "expect_calls": "2", "out_parameters": {"v": "1"}}},
                "requirements": ["TOOL-X-1"], "suites": ["smoke"],
            }
        ],
    }
    parsed = dd.parse_test_cases_document(doc)
    parsed = replace(parsed, cases=tuple(dd.refresh_digest(c) for c in parsed.cases))

    assert dd.dump_test_cases_document(parsed) == golden
    assert parsed.cases[0].content_digest == "30f0d27bdca56b71f54d1eca91e528fd63e96162e589a6341eaeb3952faa253e"


# --- declared types from the analysis type graph -----------------------------------------------------------


def _graph() -> dict[str, TypeModel]:
    return {
        "type.uchar": TypeModel(kind="builtin", name="unsigned char"),
        "type.int": TypeModel(kind="builtin", name="int"),
        "type.float": TypeModel(kind="builtin", name="float"),
        "type.u8": TypeModel(kind="typedef", name="u8", underlying_type="ref:type.uchar"),
        "type.Header": TypeModel(
            kind="struct", name="Header", members=(StructMemberModel("len", "ref:type.u8"), StructMemberModel("flags", "ref:type.uchar"))
        ),
        "type.Payload": TypeModel(kind="array", element_type="ref:type.u8", size=3),
        "type.Grid": TypeModel(kind="array", element_type="ref:type.u8", dimensions=()),
        "type.Frame": TypeModel(
            kind="struct", name="Frame", members=(StructMemberModel("header", "ref:type.Header"), StructMemberModel("payload", "ref:type.Payload"))
        ),
        "type.Reading": TypeModel(
            kind="union", name="Reading", members=(StructMemberModel("as_int", "ref:type.int"), StructMemberModel("as_float", "ref:type.float"))
        ),
        "type.Mode": TypeModel(kind="enum", name="Mode", enumerators=(EnumeratorModel("OFF", 0), EnumeratorModel("ON", 1))),
        "type.Ptr": TypeModel(kind="pointer", target="ref:type.int"),
        "type.Node": TypeModel(kind="struct", name="Node", members=(StructMemberModel("next", "ref:type.Node"),)),
        "type.Empty": TypeModel(kind="enum", name="Empty"),
    }


def test_the_engines_declared_types_come_from_the_type_graph() -> None:
    types = _graph()

    assert ctype_from_model("ref:type.Frame", types) == FRAME
    assert ctype_from_model("ref:type.Reading", types) == READING
    assert ctype_from_model("ref:type.Mode", types) == EnumType({"OFF": "0", "ON": "1"})
    assert ctype_from_model("ref:type.u8", types) == UCHAR


def test_a_type_from_the_graph_drives_a_whole_comparison() -> None:
    declared = {"g_frame": ctype_from_model("ref:type.Frame", _graph())}
    entries = {k: v for k, v in EXPECTED.items() if k.startswith("g_frame")}

    assert compare_expected(entries, declared, {"g_frame": ACTUAL["g_frame"]})["g_frame"].matched
    bad = {"g_frame.header.nope": "1", **entries}
    assert _reason(lambda: compare_expected(bad, declared, {"g_frame": ACTUAL["g_frame"]})) == "unknown_member"


def test_multi_dimensional_arrays_are_built_outermost_first() -> None:
    types = {
        "type.u8": TypeModel(kind="builtin", name="unsigned char"),
        "type.Grid": TypeModel(kind="array", element_type="ref:type.u8", dimensions=(DimensionModel(size=2), DimensionModel(size=3))),
    }
    assert ctype_from_model("ref:type.Grid", types) == ArrayType(ArrayType(UCHAR, 3), 2)


@pytest.mark.parametrize("ref", ["ref:type.Ptr", "ref:type.Node", "ref:type.Grid", "ref:type.Empty", "ref:type.Missing"])
def test_types_the_graph_cannot_make_comparable_are_refused(ref: str) -> None:
    with pytest.raises(InvalidComparisonSpecError):
        ctype_from_model(ref, _graph())


def test_builtin_names_without_a_comparison_rule_are_refused() -> None:
    with pytest.raises(InvalidComparisonSpecError):
        ctype_from_model("ref:type.v", {"type.v": TypeModel(kind="builtin", name="void")})
