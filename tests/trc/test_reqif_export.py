# implements: TOOL-TRC-070
"""ReqIF export of traceability data (WP-TRC-04).

Verifies: TOOL-TRC-070. TOOL-TRC-100 (a named open-source tool adapter) is a
recorded second-pass item; ReqIF is the exchange the export provides.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import pytest

from ectt.trc import (
    REQIF_NAMESPACE,
    AssociationSet,
    RequirementRecord,
    TrcError,
    build_matrix,
    export_reqif,
    import_reqif,
)

WHEN = "2026-11-21T00:00:00+00:00"
NS = {"r": REQIF_NAMESPACE}


def _matrix():
    associations = AssociationSet()
    for requirement, test in (("REQ-1", "t.a"), ("REQ-1", "t.b"), ("REQ-2", "t.a"), ("REQ-3", "t.gen")):
        associations.add(requirement, test)
    statuses = {"t.a": "pass", "t.b": "fail", "t.gen": "pass"}
    return build_matrix(
        associations,
        statuses,
        requirement_universe=["REQ-1", "REQ-2", "REQ-3", "REQ-4"],
        unreviewed_tests=["t.gen"],
    )


RECORDS = (
    RequirementRecord("REQ-1", "First", "The tool shall <do> & more\nover two lines\tand a tab."),
    RequirementRecord("REQ-2", "Second", "Plain."),
    RequirementRecord("REQ-3", "", ""),
    RequirementRecord("REQ-4", "Unlinked", "No tests."),
)


def _export() -> str:
    return export_reqif(_matrix(), RECORDS, creation_time=WHEN)


def test_export_roundtrips_to_exactly_the_requirement_inventory() -> None:
    assert import_reqif(_export()) == tuple(sorted(RECORDS))


def test_text_with_markup_newlines_and_tabs_survives() -> None:
    first = next(r for r in import_reqif(_export()) if r.requirement_id == "REQ-1")
    assert first.text == "The tool shall <do> & more\nover two lines\tand a tab."


def test_requirements_without_a_record_are_exported_with_empty_text() -> None:
    text = export_reqif(_matrix(), (), creation_time=WHEN)
    imported = {r.requirement_id: r for r in import_reqif(text)}
    assert sorted(imported) == ["REQ-1", "REQ-2", "REQ-3", "REQ-4"]
    assert imported["REQ-1"].title == "" and imported["REQ-1"].text == ""


def test_document_is_well_formed_reqif_with_the_schema_element_order() -> None:
    root = ET.fromstring(_export())
    assert root.tag == f"{{{REQIF_NAMESPACE}}}REQ-IF"
    assert [c.tag.rsplit("}", 1)[1] for c in root] == ["THE-HEADER", "CORE-CONTENT"]
    content = root.find("r:CORE-CONTENT/r:REQ-IF-CONTENT", NS)
    assert content is not None
    assert [c.tag.rsplit("}", 1)[1] for c in content] == [
        "DATATYPES",
        "SPEC-TYPES",
        "SPEC-OBJECTS",
        "SPEC-RELATIONS",
        "SPECIFICATIONS",
    ]
    header = root.find("r:THE-HEADER/r:REQ-IF-HEADER", NS)
    assert header is not None
    assert [c.tag.rsplit("}", 1)[1] for c in header] == [
        "CREATION-TIME",
        "REPOSITORY-ID",
        "REQ-IF-TOOL-ID",
        "REQ-IF-VERSION",
        "SOURCE-TOOL-ID",
        "TITLE",
    ]


def test_every_reference_resolves_and_identifiers_are_unique_xml_ids() -> None:
    root = ET.fromstring(_export())
    ids = [e.get("IDENTIFIER") for e in root.iter() if e.get("IDENTIFIER")]
    assert len(ids) == len(set(ids))
    assert all(i and (i[0].isalpha() or i[0] == "_") and ":" not in i and " " not in i for i in ids)
    refs = [e.text for e in root.iter() if e.tag.rsplit("}", 1)[1].endswith("-REF")]
    assert refs and all(ref in set(ids) for ref in refs)


def test_one_relation_per_unique_requirement_test_pair_with_direction() -> None:
    root = ET.fromstring(_export())
    relations = root.findall(".//r:SPEC-RELATION", NS)
    assert len(relations) == _matrix().pair_count == 4
    by_id = {e.get("IDENTIFIER"): e for e in root.iter() if e.get("IDENTIFIER")}
    for relation in relations:
        source = by_id[relation.find("r:SOURCE/r:SPEC-OBJECT-REF", NS).text]  # type: ignore[union-attr]
        target = by_id[relation.find("r:TARGET/r:SPEC-OBJECT-REF", NS).text]  # type: ignore[union-attr]
        assert source.get("IDENTIFIER", "").startswith("r_")
        assert target.get("IDENTIFIER", "").startswith("t_")


def test_verdicts_statuses_and_unreviewed_flags_are_carried() -> None:
    root = ET.fromstring(_export())
    values: dict[tuple[str, str], str] = {}
    for obj in root.findall(".//r:SPEC-OBJECT", NS):
        ident = None
        found: dict[str, str] = {}
        for attr in obj.findall("r:VALUES/r:ATTRIBUTE-VALUE-STRING", NS):
            definition = attr.find("r:DEFINITION/r:ATTRIBUTE-DEFINITION-STRING-REF", NS).text  # type: ignore[union-attr]
            found[definition] = attr.get("THE-VALUE", "")
            if definition.endswith("ReqIF.Identifier"):
                ident = attr.get("THE-VALUE")
        for definition, value in found.items():
            values[(ident or "", definition.rsplit(".", 1)[1])] = value
    assert values[("REQ-1", "Verdict")] == "failed"
    assert values[("REQ-2", "Verdict")] == "pass"
    assert values[("REQ-3", "Verdict")] == "unverified"  # only an unreviewed test
    assert values[("REQ-4", "Verdict")] == "unverified"
    assert values[("t.b", "Status")] == "fail"
    assert values[("t.gen", "Unreviewed")] == "true"
    assert values[("t.a", "Unreviewed")] == "false"


def test_export_is_deterministic_and_input_order_free() -> None:
    assert _export() == _export()
    assert export_reqif(_matrix(), tuple(reversed(RECORDS)), creation_time=WHEN) == _export()


def test_creation_time_is_the_only_time_in_the_document() -> None:
    other = export_reqif(_matrix(), RECORDS, creation_time="2027-01-01T00:00:00+00:00")
    assert other != _export()
    assert other.replace("2027-01-01T00:00:00+00:00", WHEN) == _export()


def test_empty_matrix_exports_a_valid_empty_document() -> None:
    text = export_reqif(build_matrix(AssociationSet(), {}), creation_time=WHEN)
    assert import_reqif(text) == ()
    assert ET.fromstring(text).findall(".//r:SPEC-RELATION", NS) == []


def test_standard_ref_element_form_is_read_by_the_importer() -> None:
    doc = (
        f'<REQ-IF xmlns="{REQIF_NAMESPACE}"><CORE-CONTENT><REQ-IF-CONTENT><SPEC-OBJECTS>'
        '<SPEC-OBJECT IDENTIFIER="x1" LONG-NAME="T"><VALUES><ATTRIBUTE-VALUE-STRING THE-VALUE="R-9">'
        "<DEFINITION><ATTRIBUTE-DEFINITION-STRING-REF>d.ReqIF.Identifier</ATTRIBUTE-DEFINITION-STRING-REF></DEFINITION>"
        "</ATTRIBUTE-VALUE-STRING></VALUES></SPEC-OBJECT></SPEC-OBJECTS></REQ-IF-CONTENT></CORE-CONTENT></REQ-IF>"
    )
    assert import_reqif(doc) == (RequirementRecord("R-9", "T", ""),)


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"creation_time": "yesterday"}, "invalid_creation_time"),
        ({"creation_time": "2026-11-21"}, "invalid_creation_time"),
        ({"creation_time": WHEN, "title": "bad\x01title"}, "invalid_xml_character"),
    ],
)
def test_bad_header_inputs_are_refused(kwargs: dict[str, str], reason: str) -> None:
    with pytest.raises(TrcError) as excinfo:
        export_reqif(_matrix(), RECORDS, **kwargs)
    assert excinfo.value.reason == reason


def test_text_that_xml_cannot_carry_is_refused_not_corrupted() -> None:
    bad = (RequirementRecord("REQ-1", "", "ctrl\x0bchar"),)
    with pytest.raises(TrcError) as excinfo:
        export_reqif(_matrix(), bad, creation_time=WHEN)
    assert excinfo.value.reason == "invalid_xml_character"


def test_oversized_text_is_refused() -> None:
    huge = (RequirementRecord("REQ-1", "", "x" * 100001),)
    with pytest.raises(TrcError) as excinfo:
        export_reqif(_matrix(), huge, creation_time=WHEN)
    assert excinfo.value.reason == "value_too_long"


def test_requirement_ids_that_are_not_legal_xml_ids_still_roundtrip() -> None:
    associations = AssociationSet()
    associations.add("TOOL-X:1/\u03b1", "t.1")
    records = (RequirementRecord("TOOL-X:1/\u03b1", "Odd id", "text"),)
    text = export_reqif(build_matrix(associations, {"t.1": "pass"}), records, creation_time=WHEN)
    assert import_reqif(text) == records


def test_the_header_carries_the_version_the_schema_fixes() -> None:
    """The OMG schema fixes REQ-IF-VERSION to 1.0; an earlier draft wrote 1.2 and failed validation."""
    version = ET.fromstring(_export()).find("r:THE-HEADER/r:REQ-IF-HEADER/r:REQ-IF-VERSION", NS)
    assert version is not None and version.text == "1.0"


def test_exports_validate_against_the_omg_schema_when_a_copy_is_supplied() -> None:
    """Optional conformance check: set ECTT_REQIF_XSD to a local reqif.xsd and install xmlschema."""
    xmlschema = pytest.importorskip("xmlschema")
    path = os.environ.get("ECTT_REQIF_XSD")
    if not path:
        pytest.skip("ECTT_REQIF_XSD is not set (the schema is not vendored in this repository)")
    schema = xmlschema.XMLSchema(path, validation="lax")
    empty = export_reqif(build_matrix(AssociationSet(), {}), creation_time=WHEN)

    for document in (_export(), empty):
        assert [e.reason for e in schema.iter_errors(document)] == []
