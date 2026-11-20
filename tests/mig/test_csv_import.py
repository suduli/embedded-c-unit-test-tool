# implements: TOOL-MIG-050
"""Column-mapped CSV / plain-text import (WP-MIG-04).

Verifies: TOOL-MIG-050 (CSV interchange), TOOL-MIG-030 (tabular plain-text
exports: inputs, expected values, stub configuration), TOOL-MIG-040 discipline
(every row and column accounted for).
"""

from __future__ import annotations

import pytest

from ectt.mig.csv_import import DELIMITERS, import_mapped_csv, validate_mapping
from ectt.mig.errors import MigError

MAPPING = {
    "Case": "id",
    "Module": "unit",
    "Func": "function",
    "Arg x": "input:x",
    "Arg y": "input:y",
    "Init g": "global_init:g_mode",
    "Want": "expect_return",
    "Want g": "expect_global:g_mode",
    "Reqs": "requirements",
    "Suites": "suites",
    "Stub rc": "stub:hal_read:returns",
    "Stub mode": "stub:hal_read:mode",
    "Stub calls": "stub:hal_read:expect_calls",
}

CSV = (
    "Case,Module,Func,Arg x,Arg y,Init g,Want,Want g,Reqs,Suites,Stub rc,Stub mode,Stub calls,Comment\n"
    "c1,adc.c,adc_scale,0,1,2,0,3,TOOL-A-1;TOOL-A-2,smoke;full,5;6,sequence,2,first\n"
    "c2,adc.c,adc_scale,4095,1,,4095,,,,,,,second\n"
)


def test_rows_become_cases_with_inputs_expected_stubs_and_links() -> None:
    result = import_mapped_csv(CSV, MAPPING)

    assert [c.case_id for c in result.cases] == ["c1", "c2"]
    c1, c2 = result.cases
    assert c1.unit == "adc.c" and c1.function == "adc_scale"
    assert dict(c1.inputs.parameters) == {"x": "0", "y": "1"}
    assert dict(c1.inputs.global_inits) == {"g_mode": "2"}
    assert c1.expected.return_value == "0"
    assert dict(c1.expected.global_finals) == {"g_mode": "3"}
    assert c1.requirements == ("TOOL-A-1", "TOOL-A-2")
    assert c1.suites == ("smoke", "full")
    (stub,) = c1.stubs
    assert (stub.name, stub.mode, stub.returns, stub.expect_calls) == ("hal_read", "sequence", ("5", "6"), "2")
    assert c2.stubs == () and dict(c2.inputs.global_inits) == {}


def test_imported_cases_carry_a_fresh_content_digest() -> None:
    first, second = import_mapped_csv(CSV, MAPPING).cases
    assert first.recorded_digest == first.content_digest and not first.stale
    assert first.content_digest != second.content_digest


def test_unmapped_columns_are_listed_not_dropped_silently() -> None:
    assert import_mapped_csv(CSV, MAPPING).unmapped_columns == ("Comment",)


def test_every_row_is_accounted_for() -> None:
    result = import_mapped_csv(CSV, MAPPING)
    assert [(r.row, r.status, r.case_id) for r in result.rows] == [(1, "converted", "c1"), (2, "converted", "c2")]


@pytest.mark.parametrize("delimiter", DELIMITERS)
def test_every_supported_delimiter_gives_the_same_cases(delimiter: str) -> None:
    rows = [["Case", "Module", "Func", "Want"], ["c1", "adc.c", "f", "1"], ["c2", "adc.c", "g", "2"]]
    text = "\n".join(delimiter.join(row) for row in rows) + "\n"
    mapping = {"Case": "id", "Module": "unit", "Func": "function", "Want": "expect_return"}

    result = import_mapped_csv(text, mapping, delimiter=delimiter)

    assert [(c.case_id, c.function, c.expected.return_value) for c in result.cases] == [("c1", "f", "1"), ("c2", "g", "2")]


def test_bom_crlf_and_blank_lines_are_tolerated() -> None:
    text = "﻿" + CSV.replace("\n", "\r\n") + "\r\n\r\n"
    assert [c.case_id for c in import_mapped_csv(text, MAPPING).cases] == ["c1", "c2"]


def test_quoted_cells_with_delimiters_and_newlines_survive() -> None:
    text = 'Case,Module,Func,Want\nc1,adc.c,f,"a,b\nc"\n'
    result = import_mapped_csv(text, {"Case": "id", "Module": "unit", "Func": "function", "Want": "expect_return"})
    assert result.cases[0].expected.return_value == "a,b\nc"


def test_formula_like_cells_are_stored_literally_never_evaluated() -> None:
    text = "Case,Module,Func,Want\nc1,adc.c,f,=1+1\nc2,adc.c,f,-1\n"
    result = import_mapped_csv(text, {"Case": "id", "Module": "unit", "Func": "function", "Want": "expect_return"})
    assert [c.expected.return_value for c in result.cases] == ["=1+1", "-1"]


def test_rows_missing_required_values_are_rejected_with_reason() -> None:
    text = "Case,Module,Func\n,adc.c,f\nc2,,f\nc3,adc.c,\nc4,adc.c,f\n"
    result = import_mapped_csv(text, {"Case": "id", "Module": "unit", "Func": "function"})

    assert [c.case_id for c in result.cases] == ["c4"]
    assert [(r.row, r.reason) for r in result.rejected] == [(1, "missing_id"), (2, "missing_unit"), (3, "missing_function")]


def test_duplicate_ids_reject_the_later_row_and_name_the_first() -> None:
    text = "Case,Module,Func\nc1,a.c,f\nc1,b.c,g\n"
    result = import_mapped_csv(text, {"Case": "id", "Module": "unit", "Func": "function"})

    assert [c.unit for c in result.cases] == ["a.c"]
    (rejected,) = result.rejected
    assert (rejected.row, rejected.reason, rejected.detail) == (2, "duplicate_id", "id already used by row 1")


def test_ragged_rows_are_rejected_not_padded() -> None:
    text = "Case,Module,Func\nc1,a.c\nc2,a.c,f\n"
    result = import_mapped_csv(text, {"Case": "id", "Module": "unit", "Func": "function"})
    assert [r.reason for r in result.rejected] == ["ragged_row"]
    assert [c.case_id for c in result.cases] == ["c2"]


def test_stub_values_without_a_mode_are_rejected_never_assumed() -> None:
    mapping = {"Case": "id", "Module": "unit", "Func": "function", "Rc": "stub:s:returns"}
    result = import_mapped_csv("Case,Module,Func,Rc\nc1,a.c,f,1\n", mapping)
    assert result.cases == ()
    assert result.rejected[0].reason == "stub_mode_missing"


def test_invalid_stub_call_count_is_rejected() -> None:
    mapping = {"Case": "id", "Module": "unit", "Func": "function", "M": "stub:s:mode", "N": "stub:s:expect_calls"}
    result = import_mapped_csv("Case,Module,Func,M,N\nc1,a.c,f,fixed,many\n", mapping)
    assert result.rejected[0].reason == "invalid_expect_calls"


def test_stub_out_parameters_and_expected_out_parameters_map() -> None:
    mapping = {
        "Case": "id",
        "Module": "unit",
        "Func": "function",
        "M": "stub:s:mode",
        "O": "stub:s:out:buf",
        "E": "expect_out:result",
    }
    (case,) = import_mapped_csv("Case,Module,Func,M,O,E\nc1,a.c,f,fixed,7,9\n", mapping).cases
    assert dict(case.stubs[0].out_parameters) == {"buf": "7"}
    assert dict(case.expected.out_parameters) == {"result": "9"}


def test_result_does_not_depend_on_row_order() -> None:
    lines = CSV.splitlines()
    reordered = "\n".join([lines[0], lines[2], lines[1]]) + "\n"
    assert import_mapped_csv(reordered, MAPPING).cases == import_mapped_csv(CSV, MAPPING).cases


def test_import_is_deterministic() -> None:
    assert import_mapped_csv(CSV, MAPPING) == import_mapped_csv(CSV, MAPPING)


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("", "empty_input"),
        ("   \n \n", "empty_input"),
        ("Case,Case,Func\nc,c,f\n", "duplicate_column"),
        ("Case,Module\nc,m\n", "unknown_column"),
    ],
)
def test_unusable_input_is_refused(text: str, reason: str) -> None:
    mapping = {"Case": "id", "Module": "unit", "Func": "function"}
    with pytest.raises(MigError) as excinfo:
        import_mapped_csv(text, mapping)
    assert excinfo.value.reason == reason


def test_unsupported_delimiter_is_refused() -> None:
    with pytest.raises(MigError) as excinfo:
        import_mapped_csv(CSV, MAPPING, delimiter="x")
    assert excinfo.value.reason == "unsupported_delimiter"


@pytest.mark.parametrize(
    ("mapping", "reason"),
    [
        ({}, "empty_mapping"),
        ({"A": "id", "B": "unit", "C": "bogus"}, "unknown_target"),
        ({"A": "id", "B": "id", "C": "unit", "D": "function"}, "duplicate_target"),
        ({"A": "id", "B": "unit"}, "missing_required_target"),
        ({"A": "id", "B": "unit", "C": "function", "D": "stub:s:wrong"}, "unknown_target"),
    ],
)
def test_bad_mappings_are_refused(mapping: dict[str, str], reason: str) -> None:
    with pytest.raises(MigError) as excinfo:
        validate_mapping(mapping)
    assert excinfo.value.reason == reason


def test_imported_cases_survive_the_tests_file_writer_and_parser() -> None:
    """The result is a valid ``.tests`` document: dump, parse back, same cases."""
    from ectt.prj.yaml_adapter import RestrictedYamlAdapter
    from ectt.tcm.datacases import (
        TestCasesFile,
        dump_test_cases_document,
        parse_test_cases_document,
    )

    imported = import_mapped_csv(CSV, MAPPING)
    text = dump_test_cases_document(TestCasesFile(schema_version=1, cases=imported.cases))

    parsed = parse_test_cases_document(RestrictedYamlAdapter().load(text))

    assert [(c.case_id, c.content_digest) for c in parsed.cases] == [(c.case_id, c.content_digest) for c in imported.cases]
    assert not any(c.stale for c in parsed.cases)
