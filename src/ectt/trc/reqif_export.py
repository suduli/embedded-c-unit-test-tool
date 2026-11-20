# implements: TOOL-TRC-070
"""ReqIF export of traceability data (WP-TRC-04, DSN-TRC-050).

TOOL-TRC-070: export traceability data in ReqIF for exchange with external
requirements management tools.

The document follows ReqIF 1.2 structure: a header, string datatype, object
and relation types, one ``SPEC-OBJECT`` per requirement and per linked test, one
``SPEC-RELATION`` per unique (requirement, test) pair, and one ``SPECIFICATION``
listing the requirements so tools that show a document tree have one.

* The requirement id travels in the ``ReqIF.Identifier`` attribute; the XML
  ``IDENTIFIER`` is derived from it (``r_`` / ``t_`` plus a digest) because a
  requirement id is not always a legal XML ``ID``.
* Requirements carry their title (``LONG-NAME``), text (``ReqIF.Description``)
  and the matrix verdict; tests carry their recorded status and whether they
  are unreviewed (TOOL-ATG-080).
* Test objects have their own object type, so :func:`ectt.trc.imports.import_reqif`
  reads the export back as exactly the requirement inventory it was built from.
* Deterministic: no wall clock. The caller supplies ``creation_time``.

Not verified against the OMG XSD or a live tool in this repository (neither is
available offline); structure follows the 1.2 schema's element order.

Satisfies: TOOL-TRC-070.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from datetime import datetime

from ectt.core.determinism import stable_id
from ectt.trc.errors import TrcError
from ectt.trc.imports import RequirementRecord
from ectt.trc.matrix import TraceabilityMatrix

__all__ = [
    "REQIF_NAMESPACE",
    "TEST_TYPE_ID",
    "export_reqif",
]

REQIF_NAMESPACE = "http://www.omg.org/spec/ReqIF/20110401/reqif.xsd"

#: Object type of exported test objects; the importer skips objects of this type.
TEST_TYPE_ID = "ectt.type.TestCase"
_REQUIREMENT_TYPE_ID = "ectt.type.Requirement"
_RELATION_TYPE_ID = "ectt.type.Verifies"
_SPECIFICATION_TYPE_ID = "ectt.type.Specification"
_STRING_TYPE_ID = "ectt.datatype.String"
_MAX_LENGTH = 100000

# Attribute-definition identifiers are unique per object type (ReqIF requires
# every IDENTIFIER in a document to be unique); both Identifier ids end with
# "ReqIF.Identifier" so the importer finds them.
_REQ_IDENTIFIER = "ectt.req.attr.ReqIF.Identifier"
_REQ_DESCRIPTION = "ectt.req.attr.ReqIF.Description"
_REQ_VERDICT = "ectt.req.attr.Verdict"
_TEST_IDENTIFIER = "ectt.test.attr.ReqIF.Identifier"
_TEST_STATUS = "ectt.test.attr.Status"
_TEST_UNREVIEWED = "ectt.test.attr.Unreviewed"

_REQUIREMENT_ATTRS = ((_REQ_IDENTIFIER, "ReqIF.Identifier"), (_REQ_DESCRIPTION, "ReqIF.Description"), (_REQ_VERDICT, "Verdict"))
_TEST_ATTRS = ((_TEST_IDENTIFIER, "ReqIF.Identifier"), (_TEST_STATUS, "Status"), (_TEST_UNREVIEWED, "Unreviewed"))

_ILLEGAL_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def _tag(name: str) -> str:
    return f"{{{REQIF_NAMESPACE}}}{name}"


def _sub(parent: ET.Element, name: str, text: str | None = None, **attrs: str) -> ET.Element:
    element = ET.SubElement(parent, _tag(name), attrs)
    if text is not None:
        element.text = text
    return element


def _checked_text(value: str, what: str) -> str:
    if _ILLEGAL_XML.search(value):
        raise TrcError(f"{what} contains a character that is not allowed in XML", reason="invalid_xml_character")
    if len(value) > _MAX_LENGTH:
        raise TrcError(f"{what} is longer than {_MAX_LENGTH} characters", reason="value_too_long")
    return value


def _checked_time(value: str) -> str:
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise TrcError(f"creation_time {value!r} is not an ISO-8601 timestamp", reason="invalid_creation_time") from exc
    if "T" not in value:
        raise TrcError(f"creation_time {value!r} must include a time (YYYY-MM-DDTHH:MM:SS+00:00)", reason="invalid_creation_time")
    return value


def _string_value(parent: ET.Element, definition: str, value: str) -> None:
    attr = _sub(parent, "ATTRIBUTE-VALUE-STRING", **{"THE-VALUE": value})
    ref = _sub(attr, "DEFINITION")
    _sub(ref, "ATTRIBUTE-DEFINITION-STRING-REF", definition)


def _type_with_attributes(parent: ET.Element, element: str, type_id: str, long_name: str, attrs: tuple[tuple[str, str], ...], when: str) -> None:
    spec_type = _sub(parent, element, IDENTIFIER=type_id, **{"LAST-CHANGE": when, "LONG-NAME": long_name})
    attributes = _sub(spec_type, "SPEC-ATTRIBUTES")
    for definition_id, name in attrs:
        definition = _sub(attributes, "ATTRIBUTE-DEFINITION-STRING", IDENTIFIER=definition_id, **{"LAST-CHANGE": when, "LONG-NAME": name})
        type_ref = _sub(definition, "TYPE")
        _sub(type_ref, "DATATYPE-DEFINITION-STRING-REF", _STRING_TYPE_ID)


def export_reqif(
    matrix: TraceabilityMatrix,
    requirements: Iterable[RequirementRecord] = (),
    *,
    creation_time: str,
    title: str = "ectt traceability export",
) -> str:
    """Render ``matrix`` (and requirement titles/text) as a ReqIF 1.2 document.

    ``creation_time`` is an ISO-8601 timestamp the caller supplies, so the
    output is byte-identical for identical inputs. Requirements in ``matrix``
    without a record are exported with an empty title and text.
    """
    when = _checked_time(creation_time)
    records = {r.requirement_id: r for r in requirements}

    ET.register_namespace("", REQIF_NAMESPACE)
    root = ET.Element(_tag("REQ-IF"))
    header = _sub(_sub(root, "THE-HEADER"), "REQ-IF-HEADER", IDENTIFIER=f"h_{stable_id('header', title)}")
    _sub(header, "CREATION-TIME", when)
    _sub(header, "REPOSITORY-ID", "ectt")
    _sub(header, "REQ-IF-TOOL-ID", "ectt")
    _sub(header, "REQ-IF-VERSION", "1.2")
    _sub(header, "SOURCE-TOOL-ID", "ectt")
    _sub(header, "TITLE", _checked_text(title, "title"))

    content = _sub(_sub(root, "CORE-CONTENT"), "REQ-IF-CONTENT")
    datatypes = _sub(content, "DATATYPES")
    _sub(datatypes, "DATATYPE-DEFINITION-STRING", IDENTIFIER=_STRING_TYPE_ID, **{"LAST-CHANGE": when, "LONG-NAME": "String", "MAX-LENGTH": str(_MAX_LENGTH)})

    spec_types = _sub(content, "SPEC-TYPES")
    _type_with_attributes(spec_types, "SPEC-OBJECT-TYPE", _REQUIREMENT_TYPE_ID, "Requirement", _REQUIREMENT_ATTRS, when)
    _type_with_attributes(spec_types, "SPEC-OBJECT-TYPE", TEST_TYPE_ID, "Test case", _TEST_ATTRS, when)
    _sub(spec_types, "SPEC-RELATION-TYPE", IDENTIFIER=_RELATION_TYPE_ID, **{"LAST-CHANGE": when, "LONG-NAME": "verified by"})
    _sub(spec_types, "SPECIFICATION-TYPE", IDENTIFIER=_SPECIFICATION_TYPE_ID, **{"LAST-CHANGE": when, "LONG-NAME": "Requirements"})

    objects = _sub(content, "SPEC-OBJECTS")
    requirement_ids: dict[str, str] = {}
    for row in matrix.rows:
        record = records.get(row.requirement_id, RequirementRecord(row.requirement_id))
        xml_id = f"r_{stable_id('requirement', row.requirement_id)}"
        requirement_ids[row.requirement_id] = xml_id
        obj = _sub(objects, "SPEC-OBJECT", IDENTIFIER=xml_id, **{"LAST-CHANGE": when, "LONG-NAME": _checked_text(record.title, "requirement title")})
        _sub(_sub(obj, "TYPE"), "SPEC-OBJECT-TYPE-REF", _REQUIREMENT_TYPE_ID)
        values = _sub(obj, "VALUES")
        _string_value(values, _REQ_IDENTIFIER, _checked_text(row.requirement_id, "requirement id"))
        _string_value(values, _REQ_DESCRIPTION, _checked_text(record.text, "requirement text"))
        _string_value(values, _REQ_VERDICT, row.verdict)

    tests: dict[str, tuple[str, str, bool]] = {}
    for row in matrix.rows:
        for link in row.links:
            tests.setdefault(link.test_id, (f"t_{stable_id('test', link.test_id)}", link.status, link.unreviewed))
    for test_id in sorted(tests):
        xml_id, status, unreviewed = tests[test_id]
        obj = _sub(objects, "SPEC-OBJECT", IDENTIFIER=xml_id, **{"LAST-CHANGE": when, "LONG-NAME": _checked_text(test_id, "test id")})
        _sub(_sub(obj, "TYPE"), "SPEC-OBJECT-TYPE-REF", TEST_TYPE_ID)
        values = _sub(obj, "VALUES")
        _string_value(values, _TEST_IDENTIFIER, test_id)
        _string_value(values, _TEST_STATUS, status)
        _string_value(values, _TEST_UNREVIEWED, "true" if unreviewed else "false")

    relations = _sub(content, "SPEC-RELATIONS")
    for row in matrix.rows:
        for link in row.links:
            relation = _sub(
                relations,
                "SPEC-RELATION",
                IDENTIFIER=f"x_{stable_id('relation', row.requirement_id, link.test_id)}",
                **{"LAST-CHANGE": when},
            )
            _sub(_sub(relation, "TYPE"), "SPEC-RELATION-TYPE-REF", _RELATION_TYPE_ID)
            _sub(_sub(relation, "SOURCE"), "SPEC-OBJECT-REF", requirement_ids[row.requirement_id])
            _sub(_sub(relation, "TARGET"), "SPEC-OBJECT-REF", tests[link.test_id][0])

    specifications = _sub(content, "SPECIFICATIONS")
    specification = _sub(
        specifications,
        "SPECIFICATION",
        IDENTIFIER=f"s_{stable_id('specification', title)}",
        **{"LAST-CHANGE": when, "LONG-NAME": "Requirements"},
    )
    _sub(_sub(specification, "TYPE"), "SPECIFICATION-TYPE-REF", _SPECIFICATION_TYPE_ID)
    children = _sub(specification, "CHILDREN")
    for requirement_id in sorted(requirement_ids):
        hierarchy = _sub(
            children,
            "SPEC-HIERARCHY",
            IDENTIFIER=f"p_{stable_id('hierarchy', requirement_id)}",
            **{"LAST-CHANGE": when},
        )
        _sub(_sub(hierarchy, "OBJECT"), "SPEC-OBJECT-REF", requirement_ids[requirement_id])

    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
