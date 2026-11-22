# implements: TOOL-MIG-080
"""Coverage interchange import/export: LCOV and Cobertura (WP-REP-10)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from ectt.cov.gcov import read_gcov_document
from ectt.cov.merge import RunCoverage, merge_run_coverage
from ectt.rep.coverage_interchange import (
    export_cobertura,
    export_lcov,
    import_cobertura,
    import_lcov,
)
from ectt.rep.errors import ReportModelError

PAYLOAD = {
    "format_version": "2",
    "gcc_version": "14.1.0",
    "data_file": "adc.gcda",
    "files": [
        {
            "file": "src/adc.c",
            "functions": [
                {"name": "convert", "start_line": 1, "end_line": 4, "execution_count": 2},
                {"name": "clamp", "start_line": 6, "end_line": 8, "execution_count": 0},
            ],
            "lines": [
                {
                    "line_number": 2,
                    "count": 2,
                    "unexecuted_block": False,
                    "branches": [
                        {"count": 1, "fallthrough": True, "throw": False},
                        {"count": 1, "fallthrough": False, "throw": False},
                    ],
                },
                {"line_number": 3, "count": 1, "unexecuted_block": False},
                {"line_number": 7, "count": 0, "unexecuted_block": False},
            ],
        }
    ],
}


def _document():
    return read_gcov_document(PAYLOAD)


# --- export: LCOV -----------------------------------------------------------------


def test_lcov_export_carries_functions_branches_lines() -> None:
    """verifies: TOOL-MIG-080 — FN/FNDA/FNF/FNH/BRDA/BRF/BRH/DA/LF/LH records."""
    trace = export_lcov(_document())
    assert "TN:adc.gcda" in trace
    assert "SF:src/adc.c" in trace
    assert "FN:1,4,convert" in trace
    assert "FNDA:2,convert" in trace
    assert "FNF:2" in trace
    assert "FNH:1" in trace
    assert "BRDA:2,2,0,1" in trace
    assert "BRDA:2,2,1,1" in trace
    assert "BRF:2" in trace
    assert "BRH:2" in trace
    assert "DA:2,2" in trace and "DA:3,1" in trace and "DA:7,0" in trace
    assert "LF:3" in trace and "LH:2" in trace
    assert trace.count("end_of_record") == 1


def test_lcov_export_marks_never_executed_branch_taken_as_dash() -> None:
    """A branch on a never-executed line reports taken as '-' (LCOV convention)."""
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "a.c",
                "lines": [
                    {
                        "line_number": 9,
                        "count": 0,
                        "unexecuted_block": False,
                        "branches": [{"count": 0, "fallthrough": True, "throw": False}],
                    }
                ],
            }
        ],
    }
    trace = export_lcov(read_gcov_document(payload))
    assert "BRDA:9,9,0,-" in trace
    assert "BRH:0" in trace


def test_lcov_export_is_deterministic() -> None:
    assert export_lcov(_document()) == export_lcov(_document())


# --- import: LCOV ------------------------------------------------------------------


def test_lcov_round_trip_reproduces_counts() -> None:
    """verifies: AC-5 — export → import reproduces the exported counts."""
    original = _document()
    imported = import_lcov(export_lcov(original), gcc_version="14.1.0")
    assert [f.file for f in imported.files] == ["src/adc.c"]
    (file,) = imported.files
    assert [line.count for line in file.lines] == [2, 1, 0]
    assert [b.count for b in file.lines[0].branches] == [1, 1]
    assert {fn.name: fn.execution_count for fn in file.functions} == {"convert": 2, "clamp": 0}


def test_imported_lcov_documents_aggregate_through_the_merge() -> None:
    """verifies: AC-5 — imported documents are ordinary GcovDocument values."""
    trace = export_lcov(_document())
    a = import_lcov(trace, gcc_version="other-tool")
    b = import_lcov(trace, gcc_version="other-tool")
    result = merge_run_coverage(
        [RunCoverage(test_id="t1", outcome="pass", completeness="complete", document=a),
         RunCoverage(test_id="t2", outcome="pass", completeness="complete", document=b)]
    )
    (file,) = result.document.files
    assert [line.count for line in file.lines] == [4, 2, 0]


def test_lcov_summary_mismatch_is_refused() -> None:
    trace = export_lcov(_document()).replace("LF:3", "LF:9")
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov(trace)
    assert exc_info.value.reason == "summary_mismatch"


def test_lcov_negative_count_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("SF:a.c\nDA:1,-2\nLF:1\nLH:0\nend_of_record\n")
    assert exc_info.value.reason == "negative_count"


def test_lcov_unterminated_record_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("SF:a.c\nDA:1,1\n")
    assert exc_info.value.reason == "unterminated_record"


def test_lcov_unknown_tag_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("SF:a.c\nZZ:1\nend_of_record\n")
    assert exc_info.value.reason == "unknown_record"


def test_lcov_empty_tracefile_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("\n")
    assert exc_info.value.reason == "empty_tracefile"


def test_lcov_duplicate_da_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("SF:a.c\nDA:1,1\nDA:1,1\nLF:2\nLH:1\nend_of_record\n")
    assert exc_info.value.reason == "duplicate_line"


# --- export/import: Cobertura --------------------------------------------------------


def test_cobertura_export_carries_per_line_hits_and_condition_coverage() -> None:
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [
            {
                "file": "src/adc.c",
                "lines": [
                    {
                        "line_number": 5,
                        "count": 3,
                        "unexecuted_block": False,
                        "conditions": [{"count": 4, "covered": 2, "not_covered_false": [], "not_covered_true": [0, 1]}],
                    },
                    {"line_number": 6, "count": 1, "unexecuted_block": False},
                ],
            }
        ],
    }
    xml_text = export_cobertura(read_gcov_document(payload))
    root = ET.fromstring(xml_text)
    assert root.get("timestamp") == "0"
    lines = {ln.get("number"): ln for ln in root.iter("line")}
    assert lines["5"].get("hits") == "3"
    assert lines["5"].get("branch") == "true"
    assert lines["5"].get("condition-coverage") == "50% (2/4)"
    assert lines["6"].get("branch") == "false"


def test_cobertura_statement_level_round_trip() -> None:
    """verifies: AC-5 — statement counts survive the Cobertura round trip."""
    original = _document()
    imported = import_cobertura(export_cobertura(original), gcc_version="cobertura-tool")
    (file,) = imported.files
    assert [line.count for line in file.lines] == [2, 1, 0]
    assert file.lines[0].branches == ()  # branch data not invented from the aggregate form


def test_cobertura_import_refuses_malformed_xml() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_cobertura("<coverage><packages>")
    assert exc_info.value.reason == "invalid_xml"


def test_cobertura_import_refuses_negative_hits() -> None:
    xml_text = (
        '<coverage><packages><package><classes><class filename="a.c"><lines>'
        '<line number="1" hits="-1" branch="false" />'
        "</lines></class></classes></package></packages></coverage>"
    )
    with pytest.raises(ReportModelError) as exc_info:
        import_cobertura(xml_text)
    assert exc_info.value.reason == "malformed_count"


def test_cobertura_import_refuses_empty_document() -> None:
    xml_text = '<coverage><packages><package><classes></classes></package></packages></coverage>'
    with pytest.raises(ReportModelError) as exc_info:
        import_cobertura(xml_text)
    assert exc_info.value.reason == "empty_tracefile"
