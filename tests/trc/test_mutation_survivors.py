# implements: TOOL-TRC-050, TOOL-TRC-060, TOOL-TRC-070, TOOL-TRC-080, TOOL-TRC-090, TOOL-TRC-110
"""Tests added for mutants of ``ectt.trc`` that the first battery did not kill (TEST-MUT2).

Each test names the seeded fault it was written against (see
``docs/glm-night/overnight-20261120/mutation-rep-trc.md``).
"""

from __future__ import annotations

import pytest

from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    FunctionModel,
    ProvenanceModel,
    SourceLocation,
)
from ectt.trc import (
    AssociationSet,
    RequirementRecord,
    SourceLink,
    TrcError,
    build_matrix,
    export_reqif,
    import_requirements_csv,
    import_requirements_text,
    requirement_digest,
    resolve_source_links,
)


def _model() -> AnalysisModel:
    def fn(name: str, line: int) -> FunctionModel:
        return FunctionModel(name, "external", "none", SourceLocation("src/adc.c", line), "ref:type.int")

    unit = AnalysisUnit(path="src/adc.c", status="parsed", functions=(fn("first", 10), fn("second", 30), fn("third", 60)))
    return AnalysisModel(provenance=ProvenanceModel("0", "t", "t"), units=(unit,))


def _resolve(start: int, end: int):
    (result,) = resolve_source_links([SourceLink("REQ-1", "src/adc.c", start_line=start, end_line=end)], _model()).links
    return result


def test_verdict_percentages_keep_one_decimal() -> None:
    """M07: one of three requirements passing is 33.3 percent, not 33."""
    associations = AssociationSet()
    associations.add("R1", "t1")
    matrix = build_matrix(associations, {"t1": "pass"}, requirement_universe=["R1", "R2", "R3"])

    percentages = matrix.verdict_figures()["percentages"]

    assert percentages["pass"]["value"] == 33.3
    assert percentages["unverified"]["value"] == 66.7


def test_csv_error_messages_name_the_spreadsheet_row() -> None:
    """M20: the header is row 1, so the first data row is row 2."""
    with pytest.raises(TrcError) as excinfo:
        import_requirements_csv("id\nOK-1\nbad id\n")
    assert "CSV row 3" in str(excinfo.value)
    with pytest.raises(TrcError) as first:
        import_requirements_csv("id\nbad id\n")
    assert "CSV row 2" in str(first.value)


def test_csv_titles_and_text_are_stripped() -> None:
    """M23: surrounding blanks in a CSV cell are not part of the title."""
    (record,) = import_requirements_csv("id,title,text\nR1,  Spaced title  ,  body  \n")
    assert (record.title, record.text) == ("Spaced title", "body")


def test_plain_text_titles_are_trimmed_on_both_sides() -> None:
    """M24 is an equivalent mutant (the line is stripped and the regex consumes leading blanks);
    this pins the observable behaviour all the same."""
    (record,) = import_requirements_text("R1:    Spaced title   \n")
    assert record.title == "Spaced title"


def test_lone_carriage_returns_are_not_a_requirement_change() -> None:
    """M25: an old-Mac line ending normalises like LF and CRLF."""
    lf = RequirementRecord("R", "T", "one\ntwo")
    assert requirement_digest(RequirementRecord("R", "T", "one\rtwo")) == requirement_digest(lf)
    assert requirement_digest(RequirementRecord("R", "T", "one\r\ntwo")) == requirement_digest(lf)


def test_a_range_starting_on_a_function_line_belongs_to_that_function() -> None:
    """M32: starting exactly at line 30 is inside ``second``."""
    result = _resolve(30, 35)
    assert (result.status, result.function) == ("resolved", "second")


def test_a_range_ending_on_the_next_function_line_spans_functions() -> None:
    """M31: ending exactly at line 30 reaches ``second``, so it is refused."""
    result = _resolve(25, 30)
    assert (result.status, result.reason) == ("unresolved", "range_spans_functions")
    assert _resolve(25, 29).function == "first"


def test_a_single_line_range_is_valid() -> None:
    """M36: start equal to end is one line, not an empty range."""
    link = SourceLink("REQ-1", "src/adc.c", start_line=5, end_line=5)
    assert (link.start_line, link.end_line) == (5, 5)
    with pytest.raises(TrcError):
        SourceLink("REQ-1", "src/adc.c", start_line=5, end_line=4)


def test_reqif_accepts_text_of_exactly_the_maximum_length() -> None:
    """M37: 100000 characters is the limit itself and is allowed; one more is not."""
    associations = AssociationSet()
    associations.add("R1", "t1")
    matrix = build_matrix(associations, {"t1": "pass"})

    export_reqif(matrix, [RequirementRecord("R1", "", "x" * 100000)], creation_time="2026-11-21T00:00:00+00:00")
    with pytest.raises(TrcError) as excinfo:
        export_reqif(matrix, [RequirementRecord("R1", "", "x" * 100001)], creation_time="2026-11-21T00:00:00+00:00")
    assert excinfo.value.reason == "value_too_long"
