# implements: TOOL-TCD-040, TOOL-TCD-050
"""Nested path keys for inputs.globals and the composite return value (A3).

Extends the FIX-TCMNEST path-key form to (1) initial global values
(``inputs.globals``) — validated against the declared types, completeness not
required (C zero-initializes what an initializer omits) — and (2) a composite
return value: ``expected.return`` becomes a mapping of path keys *relative to
the return* (``header.len: "4"``) beside the unchanged flat scalar string.
Older flat files stay valid and byte-stable.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any

import pytest

from ectt.prj.yaml_adapter import RestrictedYamlAdapter
from ectt.tcm import datacases as dd
from ectt.tcm.compare import ArrayType, Member, ScalarType, StructType, UnionType
from ectt.tcm.errors import InterchangeError, InvalidTestCasesFileError, ValueParseError
from ectt.tcm.interchange import export_cases, import_cases
from ectt.tcm.nested import compare_return, resolve_input_values

UCHAR = ScalarType("unsigned char")
INT = ScalarType("int")
HEADER = StructType((Member("len", UCHAR), Member("flags", UCHAR)))
FRAME = StructType((Member("header", HEADER), Member("payload", ArrayType(UCHAR, 3))))
READING = UnionType((Member("as_int", INT), Member("as_float", ScalarType("float"))))
DECLARED = {"g_frame": FRAME, "g_reading": READING, "g_count": INT}
RETURN_HEADER = StructType((Member("len", UCHAR), Member("flags", UCHAR)))

INPUT_KEYS = {
    "g_frame.header.len": "0",
    "g_frame.header.flags": "0",
    "g_frame.payload[0]": "0x01",
    "g_frame.payload[1]": "0x02",
    "g_frame.payload[2]": "0x03",
    "g_count": "5",
}
RETURN_KEYS = {"len": "4", "flags": "1"}


def _reason(call: Any) -> str:
    with pytest.raises(ValueParseError) as excinfo:
        call()
    return str(excinfo.value.reason)


# --- inputs.globals -----------------------------------------------------------------------------------------


def test_nested_initial_values_validate_against_the_declared_types() -> None:
    """verifies: TOOL-TCD-040 — initial values follow the expected-value rules."""
    trees = resolve_input_values(INPUT_KEYS, DECLARED)
    assert trees["g_count"] == "5"
    assert trees["g_frame"]["header"]["len"] == "0"
    assert trees["g_frame"]["payload"][0] == "0x01"


def test_a_partial_initializer_is_a_valid_initial_state() -> None:
    """verifies: TOOL-TCD-040 — completeness is not required for inputs: C
    zero-initializes what the initializer omits."""
    trees = resolve_input_values({"g_frame.header.len": "2"}, DECLARED)
    assert trees["g_frame"] == {"header": {"len": "2"}}


def test_an_unknown_input_member_is_refused_with_its_path() -> None:
    """verifies: TOOL-TCD-040 — a typo in an initializer is refused, not stored."""
    assert (
        _reason(lambda: resolve_input_values({"g_frame.header.widht": "1"}, DECLARED))
        == "unknown_member"
    )
    assert (
        _reason(lambda: resolve_input_values({"g_ghost": "1"}, DECLARED)) == "unknown_variable"
    )


def test_an_out_of_range_input_index_is_refused() -> None:
    """verifies: TOOL-TCD-040 — initial values cannot write past the array."""
    assert (
        _reason(lambda: resolve_input_values({"g_frame.payload[3]": "1"}, DECLARED))
        == "index_out_of_range"
    )


def test_a_scalar_input_given_member_paths_is_refused() -> None:
    """verifies: TOOL-TCD-040 — composite paths under a scalar are refused."""
    assert (
        _reason(lambda: resolve_input_values({"g_count.low": "1"}, DECLARED))
        == "composite_for_scalar"
    )


# --- the composite return value -----------------------------------------------------------------------------


def test_a_struct_return_compares_with_its_declared_type() -> None:
    """verifies: TOOL-TCD-050 — the path-key return compares member-wise."""
    result = compare_return(RETURN_KEYS, RETURN_HEADER, {"len": "4", "flags": "1"})
    assert result.matched is True and result.mismatches == ()


def test_a_return_mismatch_is_reported_with_its_path() -> None:
    """verifies: TOOL-TCD-050 — a wrong member reports the full relative path."""
    result = compare_return(RETURN_KEYS, RETURN_HEADER, {"len": "9", "flags": "1"})
    assert result.matched is False
    assert [m.path for m in result.mismatches] == ["return.len"]


def test_an_unknown_return_member_is_refused() -> None:
    """verifies: TOOL-TCD-050 — a typo in the return paths is refused."""
    assert (
        _reason(lambda: compare_return({"widht": "1"}, RETURN_HEADER, {}))
        == "unknown_member"
    )


def test_an_incomplete_return_is_refused() -> None:
    """verifies: TOOL-TCD-050 — expected values must be complete, unlike inputs."""
    assert (
        _reason(lambda: compare_return({"len": "4"}, RETURN_HEADER, {"len": "4", "flags": "1"}))
        == "missing_member"
    )


def test_member_paths_under_a_scalar_return_are_refused() -> None:
    """verifies: TOOL-TCD-050 — the flat scalar return does not take paths."""
    assert _reason(lambda: compare_return({"low": "1"}, INT, "1")) == "composite_for_scalar"


def test_a_union_return_names_exactly_one_active_member() -> None:
    """verifies: TOOL-TCD-050 — the union rules carry over to the return."""
    result = compare_return({"as_int": "7"}, READING, {"as_int": "7"})
    assert result.matched is True
    assert _reason(lambda: compare_return({"as_int": "7", "as_float": "0.5"}, READING, {"as_int": "7"})) == "ambiguous_union"


# --- the .tests file -----------------------------------------------------------------------------------------


def _nested_case() -> dd.DataDrivenTestCase:
    return dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id="frame.init",
            unit="src/frame.c",
            function="frame_fill",
            inputs=dd.TestCaseInputs(global_inits=INPUT_KEYS),
            expected=dd.TestCaseExpected(return_value=RETURN_KEYS, global_finals={"g_count": "3"}),
            stubs=(),
        )
    )


def test_nested_inputs_and_return_round_trip_through_the_tests_file() -> None:
    """verifies: TOOL-TCD-140 — parse -> dump -> parse is lossless and stable."""
    case = _nested_case()
    text = dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(case,)))
    (parsed,) = dd.parse_test_cases_document(RestrictedYamlAdapter().load(text)).cases
    assert parsed == case
    text_again = dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(parsed,)))
    assert text_again == text  # byte-stable across a round trip
    assert "g_frame.payload[1]" in text and "return" in text


def test_dumped_return_keys_are_in_deterministic_order() -> None:
    """verifies: TOOL-NFR-060 — insertion order never reaches the dumped text."""
    forward = dd.dump_test_cases_document(
        dd.TestCasesFile(
            schema_version=1,
            cases=(
                dd.refresh_digest(
                    dd.DataDrivenTestCase(
                        case_id="r1",
                        unit="u.c",
                        function="f",
                        inputs=dd.TestCaseInputs(),
                        expected=dd.TestCaseExpected(return_value={"flags": "1", "len": "4"}),
                        stubs=(),
                    )
                ),
            ),
        )
    )
    reverse = dd.dump_test_cases_document(
        dd.TestCasesFile(
            schema_version=1,
            cases=(
                dd.refresh_digest(
                    dd.DataDrivenTestCase(
                        case_id="r1",
                        unit="u.c",
                        function="f",
                        inputs=dd.TestCaseInputs(),
                        expected=dd.TestCaseExpected(return_value={"len": "4", "flags": "1"}),
                        stubs=(),
                    )
                ),
            ),
        )
    )
    assert forward == reverse


def test_malformed_return_path_keys_are_refused_at_parse() -> None:
    """verifies: TOOL-TCD-140 — a malformed path key cannot enter the model."""
    doc: dict[str, Any] = {
        "schema_version": "1",
        "test_cases": [
            {
                "id": "c1",
                "unit": "u.c",
                "function": "f",
                "inputs": {"parameters": {}},
                "stubs": {},
                "expected": {"return": {"a..b": "1"}},
            }
        ],
    }
    with pytest.raises(InvalidTestCasesFileError) as excinfo:
        dd.parse_test_cases_document(doc)
    assert "expected.return" in excinfo.value.message and "a..b" in excinfo.value.message


def test_malformed_input_globals_paths_are_refused_at_parse() -> None:
    """verifies: TOOL-TCD-140 — inputs.globals path keys are validated on parse."""
    doc: dict[str, Any] = {
        "schema_version": "1",
        "test_cases": [
            {
                "id": "c1",
                "unit": "u.c",
                "function": "f",
                "inputs": {"parameters": {}, "globals": {"g[": "1"}},
                "stubs": {},
                "expected": {},
            }
        ],
    }
    with pytest.raises(InvalidTestCasesFileError) as excinfo:
        dd.parse_test_cases_document(doc)
    assert "inputs.globals" in excinfo.value.message


def test_a_return_that_is_neither_scalar_nor_mapping_is_refused() -> None:
    """verifies: TOOL-TCD-140 — the return accepts exactly the two authored forms."""
    doc: dict[str, Any] = {
        "schema_version": "1",
        "test_cases": [
            {
                "id": "c1",
                "unit": "u.c",
                "function": "f",
                "inputs": {"parameters": {}},
                "stubs": {},
                "expected": {"return": [1, 2]},
            }
        ],
    }
    with pytest.raises(InvalidTestCasesFileError) as excinfo:
        dd.parse_test_cases_document(doc)
    assert "expected 'return'" in excinfo.value.message


def test_the_old_flat_file_is_unchanged_and_byte_stable(tmp_path: Path) -> None:
    """verifies: TOOL-TCD-140 — a flat file (scalar return, plain names) parses,
    dumps byte-identically, and keeps its digest."""
    flat_case = dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id="flat.one",
            unit="src/adc.c",
            function="adc_scale",
            inputs=dd.TestCaseInputs(parameters={"raw": "0"}, global_inits={"g_mode": "1"}),
            expected=dd.TestCaseExpected(return_value="0", global_finals={"g_state": "3"}),
            stubs=(),
        )
    )
    text = dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(flat_case,)))
    (parsed,) = dd.parse_test_cases_document(RestrictedYamlAdapter().load(text)).cases
    assert parsed == flat_case
    assert parsed.expected.return_value == "0"  # stays a plain string
    assert parsed.recorded_digest == flat_case.recorded_digest  # digest did not move
    assert dd.dump_test_cases_document(dd.TestCasesFile(schema_version=1, cases=(parsed,))) == text


# --- the CSV interchange -------------------------------------------------------------------------------------


def test_the_interchange_round_trips_a_composite_return() -> None:
    """verifies: interchange — the path-key return travels as a JSON cell and
    reconstructs with the same digest."""
    case = _nested_case()
    exported = export_cases((case,))
    (imported,) = import_cases(exported.text).cases
    assert imported.expected.return_value == dict(RETURN_KEYS)
    assert imported.content_digest == case.content_digest


def test_the_interchange_keeps_plain_scalar_returns() -> None:
    """verifies: interchange — the flat scalar return cell is unchanged text."""
    flat = dd.refresh_digest(
        dd.DataDrivenTestCase(
            case_id="flat.csv",
            unit="u.c",
            function="f",
            inputs=dd.TestCaseInputs(),
            expected=dd.TestCaseExpected(return_value="42"),
            stubs=(),
        )
    )
    exported = export_cases((flat,))
    assert '"42"' not in exported.text  # not JSON-encoded: a bare cell
    (imported,) = import_cases(exported.text).cases
    assert imported.expected.return_value == "42"
    assert imported.content_digest == flat.content_digest


def test_an_interchange_return_object_cell_must_map_strings_to_strings() -> None:
    """verifies: interchange — a malformed composite-return cell is refused."""
    case = _nested_case()
    exported = export_cases((case,))
    rows = list(csv.reader(io.StringIO(exported.text)))
    column = rows[0].index("expected_return")
    assert rows[1][column].startswith("{")
    rows[1][column] = '{"len": 4}'  # a non-string member value
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    with pytest.raises(InterchangeError) as excinfo:
        import_cases(buffer.getvalue())
    assert "expected_return" in str(excinfo.value)
