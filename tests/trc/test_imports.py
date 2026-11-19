# implements: TOOL-TRC-050, TOOL-TRC-060
"""Requirement import from ReqIF, CSV, and plain text (WP-TRC-03).

PAIRWISE over format x content-shape for the ReqIF subset (TRC-050's
verification method); equivalence partitions for CSV and plain text
(TRC-060). Every importer feeds the same record shape, so the WP-TRC-01
matrix and the WP-TRC-02 unlinked report consume all three identically.
"""

from __future__ import annotations

import pytest

from ectt.trc.associations import AssociationSet
from ectt.trc.errors import TrcError
from ectt.trc.imports import (
    import_reqif,
    import_requirements_csv,
    import_requirements_text,
    requirement_universe,
)
from ectt.trc.matrix import build_matrix
from ectt.trc.unlinked import find_unlinked

_REQIF_NAMESPACED = """\
<REQ-IF xmlns="http://www.reqif.org/reqif/1.0">
  <CORE-CONTENT>
    <REQ-IF-CONTENT>
      <SPECIFICATIONS>
        <SPEC-OBJECT IDENTIFIER="machine-1" LONG-NAME="First requirement">
          <VALUES>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="REQ-1">
              <DEFINITION><ATTRIBUTE-DEFINITION-STRING REF="http://example.com/ReqIF.Identifier"/></DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="Shall read the ADC.">
              <DEFINITION><ATTRIBUTE-DEFINITION-STRING REF="http://example.com/ReqIF.Description"/></DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
          </VALUES>
        </SPEC-OBJECT>
        <SPEC-OBJECT IDENTIFIER="machine-2" LONG-NAME="Second requirement">
          <VALUES/>
        </SPEC-OBJECT>
      </SPECIFICATIONS>
    </REQ-IF-CONTENT>
  </CORE-CONTENT>
</REQ-IF>
"""

_REQIF_NO_NAMESPACE = _REQIF_NAMESPACED.replace(' xmlns="http://www.reqif.org/reqif/1.0"', "")

_REQIF_PLAIN_IDS = """\
<REQ-IF>
  <CORE-CONTENT><REQ-IF-CONTENT><SPECIFICATIONS>
    <SPEC-OBJECT IDENTIFIER="REQ-PLAIN" LONG-NAME="Identifier-only object">
      <VALUES/>
    </SPEC-OBJECT>
  </SPECIFICATIONS></REQ-IF-CONTENT></CORE-CONTENT>
</REQ-IF>
"""


# --- TOOL-TRC-050: ReqIF (pairwise: namespace x identifier source) ---------------------


@pytest.mark.parametrize("document", [_REQIF_NAMESPACED, _REQIF_NO_NAMESPACE], ids=["namespaced", "no-namespace"])
def test_reqif_namespaced_and_bare_documents_parse_identically(document: str) -> None:
    records = import_reqif(document)

    assert [r.requirement_id for r in records] == ["REQ-1", "machine-2"]
    assert records[0].title == "First requirement"
    assert records[0].text == "Shall read the ADC."
    assert records[1].title == "Second requirement"
    assert records[1].text == ""


def test_reqif_identifier_only_object_uses_the_machine_identifier() -> None:
    records = import_reqif(_REQIF_PLAIN_IDS)

    assert [r.requirement_id for r in records] == ["REQ-PLAIN"]


def test_reqif_object_without_any_identifier_is_refused() -> None:
    document = (
        "<REQ-IF><CORE-CONTENT><REQ-IF-CONTENT><SPECIFICATIONS>"
        '<SPEC-OBJECT LONG-NAME="no identifier"><VALUES/></SPEC-OBJECT>'
        "</SPECIFICATIONS></REQ-IF-CONTENT></CORE-CONTENT></REQ-IF>"
    )

    with pytest.raises(TrcError) as excinfo:
        import_reqif(document)
    assert excinfo.value.reason == "missing_requirement_id"


def test_reqif_malformed_xml_is_refused() -> None:
    with pytest.raises(TrcError) as excinfo:
        import_reqif("<REQ-IF><oops>")
    assert excinfo.value.reason == "malformed_reqif"


# --- TOOL-TRC-060: CSV and plain text --------------------------------------------------


def test_csv_import_with_free_column_order() -> None:
    records = import_requirements_csv(
        "title,text,id\nSecond,Other text,REQ-2\nFirst,,REQ-1\n"
    )

    assert [r.requirement_id for r in records] == ["REQ-1", "REQ-2"]  # sorted, not row order
    assert records[0].title == "First"
    assert records[1].text == "Other text"


def test_csv_without_id_column_is_refused() -> None:
    with pytest.raises(TrcError) as excinfo:
        import_requirements_csv("title,text\nA,B\n")
    assert excinfo.value.reason == "missing_id_column"


def test_csv_duplicate_ids_are_refused() -> None:
    with pytest.raises(TrcError) as excinfo:
        import_requirements_csv("id\nREQ-1\nREQ-1\n")
    assert excinfo.value.reason == "duplicate_requirement"


def test_csv_id_whitespace_is_refused() -> None:
    with pytest.raises(TrcError) as excinfo:
        import_requirements_csv("id\nREQ 1\n")
    assert excinfo.value.reason == "invalid_id"


def test_plain_text_import_with_comments_and_blanks() -> None:
    records = import_requirements_text(
        "# requirement inventory\n"
        "\n"
        "REQ-1: First requirement\n"
        "REQ-2: Second one, with punctuation.\n"
    )

    assert [r.requirement_id for r in records] == ["REQ-1", "REQ-2"]
    assert records[0].title == "First requirement"
    assert records[1].title == "Second one, with punctuation."


def test_plain_text_line_without_colon_is_refused_with_the_line_number() -> None:
    with pytest.raises(TrcError) as excinfo:
        import_requirements_text("REQ-1: fine\nno colon here\n")
    assert excinfo.value.reason == "malformed_line"
    assert "line 2" in str(excinfo.value)


def test_all_three_importers_feed_the_same_record_shape() -> None:
    reqif = import_reqif(_REQIF_PLAIN_IDS)
    csv_rows = import_requirements_csv("id,title\nREQ-PLAIN,Identifier-only object\n")
    plain = import_requirements_text("REQ-PLAIN: Identifier-only object\n")

    assert reqif == csv_rows == plain


# --- integration with TRC-01 / TRC-02 --------------------------------------------------


def test_imported_universe_feeds_matrix_and_unlinked_report() -> None:
    records = import_requirements_text("REQ-1: covered\nREQ-2: uncovered\n")
    universe = requirement_universe(records)
    associations = AssociationSet.from_rows([("REQ-1", "case.one")])

    matrix = build_matrix(associations, {"case.one": "pass"}, requirement_universe=universe)
    report = find_unlinked(associations, requirement_universe=universe, test_universe=("case.one", "case.two"))

    assert [row.verdict for row in matrix.rows] == ["pass", "unverified"]
    assert report.unlinked_requirements == ("REQ-2",)
    assert report.unlinked_tests == ("case.two",)


def test_csv_undocumented_columns_are_refused() -> None:
    with pytest.raises(TrcError) as excinfo:
        import_requirements_csv("id,priority\nREQ-1,high\n")
    assert excinfo.value.reason == "unknown_column"
