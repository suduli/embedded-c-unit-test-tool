# implements: TOOL-MIG-080, TOOL-REP-010, TOOL-REP-020
"""Interchange round trips, and imports of files in the styles real tools produce.

Two claims are pinned here:

- **Round trip.** ``export_lcov`` -> ``import_lcov`` reproduces everything the
  LCOV format carries (counts, branches, functions; the format has no
  condition records, so conditions do not survive, and the import carries
  none). ``export_cobertura`` -> ``import_cobertura`` reproduces the
  statement counts (the interchange import is statement-level by design).
- **Real-tool styles.** Hand-written files following the *documented* output
  structure of real tools are read correctly, or refused with a named reason.
  The structures are taken from the public format descriptions, fetched
  2026-11-27 and named in the ledger:

  - LCOV: ``linux-test-project/lcov``, ``docs/man/geninfo.rst`` (the
    geninfo(1) man page: tracefile grammar, comment records, ``VER:``,
    ``SF:[<index>,]<path>``, the deprecated two-field ``FN:``, ``DA`` with
    optional checksum).
  - Cobertura XML: gcovr 8.8 documentation, "Cobertura XML Output" (the
    example document: ``<sources>``, methods whose ``<lines>`` repeat the
    class-level listing, ``condition-coverage`` attributes, ``version=
    "gcovr 8.8"``).

  Files produced by the real tools themselves have not been checked — there
  is no coverage toolchain on this machine (recorded in the lane ledger).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

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
from ectt.rep.machine_formats import render_cobertura, render_junit
from ectt.rep.model import CoverageEntry, build_report_model
from tests.rep.test_renderers import CLOCK, _result_set


def _document() -> Any:
    return read_gcov_document(
        {
            "format_version": "2",
            "gcc_version": "14.1.0",
            "data_file": "d.gcda",
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
                            "conditions": [
                                {
                                    "count": 2,
                                    "covered": 1,
                                    "not_covered_false": [],
                                    "not_covered_true": [1],
                                }
                            ],
                        },
                        {"line_number": 3, "count": 1, "unexecuted_block": False},
                        {"line_number": 7, "count": 0, "unexecuted_block": False},
                    ],
                }
            ],
        }
    )


# --- round trips (REP-10; REP-02 Cobertura) ------------------------------------------


def test_lcov_round_trip_reproduces_everything_the_format_carries() -> None:
    """Counts, branches and functions come back as written. The LCOV format has
    no condition records, so the import carries none - stated, not filled."""
    original = _document()
    (original_file,) = original.files
    (line_with_conditions,) = [line for line in original_file.lines if line.conditions]
    imported = import_lcov(export_lcov(original), gcc_version="14.1.0")
    (file,) = imported.files
    assert file.file == original_file.file
    assert [(line.line_number, line.count) for line in file.lines] == [
        (line.line_number, line.count) for line in original_file.lines
    ]
    # the BRDA record carries only the taken count: fallthrough flags do not
    # survive, and the import carries none rather than a guess
    assert [(b.count) for line in file.lines for b in line.branches] == [
        b.count for line in original_file.lines for b in line.branches
    ]
    assert all(b.fallthrough is None and b.throw is None for line in file.lines for b in line.branches)
    assert {
        fn.name: (fn.start_line, fn.end_line, fn.execution_count) for fn in file.functions
    } == {fn.name: (fn.start_line, fn.end_line, fn.execution_count) for fn in original_file.functions}
    # the format carries no condition records: none come back, none are invented
    assert all(line.conditions == () and line.calls == () for line in file.lines)
    assert line_with_conditions.conditions  # the input had conditions to lose


def test_cobertura_round_trip_reproduces_statement_counts() -> None:
    original = _document()
    imported = import_cobertura(export_cobertura(original), gcc_version="14.1.0")
    (file,) = imported.files
    assert [line.count for line in file.lines] == [2, 1, 0]
    assert file.lines[0].branches == ()  # the interchange import is statement-level


def test_report_model_cobertura_is_refused_by_the_interchange_reader() -> None:
    """The REP-02 report-model Cobertura carries aggregate counters only - its
    ``<lines>`` element is empty because the model has no per-line data. The
    interchange reader refuses such a document (``empty_tracefile``) instead of
    pretending to import an empty measurement."""
    model = build_report_model(
        _result_set(()),
        coverage=(CoverageEntry(unit="src/adc.c", covered=2, total=3),),
        clock=CLOCK,
    )
    with pytest.raises(ReportModelError) as exc_info:
        import_cobertura(render_cobertura(model), gcc_version="14.1.0")
    assert exc_info.value.reason == "empty_tracefile"


def test_junit_output_has_no_importer_by_design() -> None:
    """REP-02's JUnit output is an output: test results enter the tool through
    the harness RESULT stream (WP-EXH-01), not through a JUnit reader, so no
    round trip is claimed. The document is checked to be parseable and to
    carry every test."""
    model = build_report_model(
        _result_set(
            (finalize_executed("t.a", "pass"), finalize_executed("t.b", "fail")),
            not_executed=("t.c",),
        ),
        clock=CLOCK,
    )
    suite = ET.fromstring(render_junit(model)).find("testsuite")
    assert suite is not None
    assert suite.get("tests") == "3" and suite.get("failures") == "1" and suite.get("skipped") == "1"
    assert sorted(case.get("name") for case in suite.iter("testcase")) == ["t.a", "t.b", "t.c"]


# --- LCOV in the style real tools write (geninfo(1)) -----------------------------------
#
# Structure from linux-test-project/lcov docs/man/geninfo.rst: comment records
# anywhere; an optional TN: before SF:; FNDA/FNF/FNH beside FN; BRDA whose taken
# field is '-' when the block never executed; DA with an optional checksum;
# LF/LH beside DA; end_of_record per section.

_LCOV_1X_REAL_STYLE = """\
#comment record at the top, as geninfo writes with --comment
TN:the-test-name
SF:/build/src/adc.c
FN:1,4,convert
FN:6,8,clamp
FNDA:2,convert
FNDA:0,clamp
FNF:2
FNH:1
BRDA:2,0,0,1
BRDA:2,0,1,1
BRF:2
BRH:2
DA:2,2,md5checksumignored
DA:3,1
DA:7,0
LF:3
LH:2
end_of_record
"""


def test_lcov_file_in_real_tool_style_is_read_correctly() -> None:
    document = import_lcov(_LCOV_1X_REAL_STYLE, gcc_version="geninfo")
    (file,) = document.files
    assert file.file == "/build/src/adc.c"
    assert {fn.name: fn.execution_count for fn in file.functions} == {"convert": 2, "clamp": 0}
    assert [line.count for line in file.lines] == [2, 1, 0]
    assert [branch.count for branch in file.lines[0].branches] == [1, 1]


def test_lcov_summary_mismatch_in_a_real_style_file_is_refused() -> None:
    """geninfo writes LF/LH as a measurement; a file whose summary disagrees
    with its records is refused rather than silently trusted."""
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov(_LCOV_1X_REAL_STYLE.replace("LF:3", "LF:4"))
    assert exc_info.value.reason == "summary_mismatch"


def test_lcov_da_checksum_field_is_ignored() -> None:
    """geninfo writes an optional checksum as the third DA field (--checksum):
    the same records with and without it read identically."""
    without = import_lcov(_LCOV_1X_REAL_STYLE.replace(",md5checksumignored", ""))
    with_checksum = import_lcov(_LCOV_1X_REAL_STYLE)
    assert without.files == with_checksum.files


def test_lcov_comment_records_are_ignored_anywhere() -> None:
    """The format allows a comment record anywhere, inside or outside a section.
    Only a whole-line comment is a comment: a '#' on a DA record line is part
    of that record's fields and is refused as the malformed field it is."""
    with_comments = "\n".join(
        [
            "#top comment",
            "TN:the-test-name",
            "SF:a.c",
            "#comment inside a section",
            "FN:1,4,f",
            "FNDA:1,f",
            "FNF:1",
            "FNH:1",
            "DA:1,1",
            "LF:1",
            "LH:1",
            "#comment between sections",
            "end_of_record",
        ]
    )
    (file,) = import_lcov(with_comments).files
    assert file.file == "a.c"
    assert file.lines[0].count == 1
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("SF:a.c\nDA:1,1#x\nLF:1\nLH:1\nend_of_record\n")
    assert exc_info.value.reason == "malformed_count"


def test_lcov_file_with_fn_without_end_line_is_refused() -> None:
    """Compilers too old to know a function's end line write a two-field FN
    record; the model cannot represent an unknown end line, so the file is
    refused with the reason named."""
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov("SF:a.c\nFN:5,f\nFNDA:1,f\nFNF:1\nFNH:1\nDA:5,1\nLF:1\nLH:1\nend_of_record\n")
    assert exc_info.value.reason == "malformed_record"


# --- lcov 2.x (VER records, indexed SF, new BRDA layout) --------------------------------


def test_lcov_2x_file_is_refused_naming_the_version() -> None:
    """A geninfo 2.x tracefile starts its section with VER and carries records
    this reader does not read (FNL/FNA/FNC/MCDC, a reworked BRDA). The refusal
    names the version and the cause."""
    lcov_2x = "\n".join(
        [
            "TN:the-test-name",
            "SF:0,src/adc.c",
            "VER:2",
            "FNL:1#3,convert",
            "FNDA:2,convert",
            "FNF:1",
            "FNH:1",
            "BRDA:2,e-fu0^7,0,1",
            "BRF:1",
            "BRH:1",
            "DA:2,2",
            "LF:1",
            "LH:1",
            "end_of_record",
        ]
    )
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov(lcov_2x)
    assert exc_info.value.reason == "unsupported_lcov_version"
    assert "'2'" in str(exc_info.value)


def test_lcov_indexed_sf_record_is_read_as_its_path() -> None:
    """lcov 2.x writes SF:<index>,<path> when later records name the file by
    index; the index is resolved on reading and is not part of the data."""
    indexed = "\n".join(
        [
            "SF:0,src/adc.c",
            "FN:1,4,convert",
            "FNDA:2,convert",
            "FNF:1",
            "FNH:1",
            "DA:2,2",
            "LF:1",
            "LH:1",
            "end_of_record",
        ]
    )
    (file,) = import_lcov(indexed).files
    assert file.file == "src/adc.c"


def test_lcov_indexed_sf_records_are_deduplicated_by_path() -> None:
    """Two sections naming the same path through different indices are one file
    twice, not two files; the duplicate is refused as the un-indexed form is."""
    duplicated = "\n".join(
        [
            "SF:0,src/adc.c",
            "DA:1,1",
            "LF:1",
            "LH:1",
            "end_of_record",
            "SF:1,src/adc.c",
            "DA:1,1",
            "LF:1",
            "LH:1",
            "end_of_record",
        ]
    )
    with pytest.raises(ReportModelError) as exc_info:
        import_lcov(duplicated)
    assert exc_info.value.reason == "duplicate_file"


# --- Cobertura in the style real tools write (gcovr) -----------------------------------
#
# Structure from the gcovr 8.8 documentation ("Cobertura XML Output"): a
# <sources> listing, methods whose <lines> repeat the class-level listing,
# condition-coverage text attributes, a non-zero timestamp and a gcovr version.

_GCOVR_STYLE = """\
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE coverage SYSTEM 'https://github.com/cobertura/cobertura/blob/master/cobertura/src/site/htdocs/xml/coverage-04.dtd'>
<coverage line-rate="0.8571428571428571" branch-rate="0.5" lines-covered="2" lines-valid="3" branches-covered="0" branches-valid="0" complexity="0.0" timestamp="1793099975" version="gcovr 8.8">
  <sources>
    <source>/gcovr/example</source>
  </sources>
  <packages>
    <package name="" line-rate="0.8571428571428571" branch-rate="0.5" complexity="0.0">
      <classes>
        <class name="example_cpp" filename="example.cpp" line-rate="0.8571428571428571" branch-rate="0.5" complexity="0.0">
          <methods>
            <method name="foo" signature="(int)" line-rate="0.75" branch-rate="0.5" complexity="0.0">
              <lines>
                <line number="2" hits="2" branch="false"/>
                <line number="3" hits="1" branch="false"/>
                <line number="7" hits="0" branch="false"/>
              </lines>
            </method>
          </methods>
          <lines>
            <line number="2" hits="2" branch="false"/>
            <line number="3" hits="1" branch="false"/>
            <line number="7" hits="0" branch="false"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""


def test_a_gcovr_style_cobertura_file_reads_each_line_once() -> None:
    """gcovr repeats every instrumented line under its method and at class
    level. The class-level listing is the data; reading both would double the
    statement counts (the defect this test pins)."""
    document = import_cobertura(_GCOVR_STYLE, gcc_version="gcovr 8.8")
    (file,) = document.files
    assert file.file == "example.cpp"
    assert [(line.line_number, line.count) for line in file.lines] == [(2, 2), (3, 1), (7, 0)]


def test_a_gcovr_style_file_aggregates_without_double_counting() -> None:
    """The reason the duplication mattered: an aggregate built from a
    gcovr-style import shows each statement's true count, not twice that."""
    imported = import_cobertura(_GCOVR_STYLE, gcc_version="gcovr 8.8")
    runs = [
        RunCoverage(test_id="t.gcvr", outcome="pass", completeness="complete", document=imported),
        RunCoverage(test_id="t.again", outcome="pass", completeness="complete", document=imported),
    ]
    result = merge_run_coverage(runs)
    (file,) = result.document.files
    assert [line.count for line in file.lines] == [4, 2, 0]  # 2 x (2, 1, 0), not 4 x


def test_a_cobertura_file_without_any_class_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_cobertura(
            '<coverage line-rate="0" timestamp="0"><packages><package name="p">'
            "<classes /></package></packages></coverage>"
        )
    assert exc_info.value.reason == "empty_tracefile"


def test_a_cobertura_line_without_hits_is_refused() -> None:
    with pytest.raises(ReportModelError) as exc_info:
        import_cobertura(
            '<coverage><packages><package><classes><class filename="a.c"><lines>'
            '<line number="1" branch="false"/>'
            "</lines></class></classes></package></packages></coverage>"
        )
    assert exc_info.value.reason == "invalid_xml"


# --- helpers ------------------------------------------------------------------------------


def finalize_executed(test_id: str, outcome: str) -> Any:
    from ectt.exh.results import AssertionFailure, SourceLocation, finalize_result

    if outcome == "fail":
        return finalize_result(
            test_id,
            "fail",
            test_id.encode("ascii").hex() * 24,
            failures=(
                AssertionFailure(
                    assertion="assert_equal",
                    expected="0",
                    actual="1",
                    location=SourceLocation(file=f"test_{test_id}.c", line=7),
                ),
            ),
        )
    return finalize_result(test_id, outcome, test_id.encode("ascii").hex() * 24)


def test_the_helper_matches_the_shape_build_report_model_consumes() -> None:
    """The helper produces records the model accepts, digest and all."""
    model = build_report_model(_result_set((finalize_executed("t.a", "pass"),)), clock=CLOCK)
    assert model.tests[0].digest == "t.a".encode("ascii").hex() * 24
