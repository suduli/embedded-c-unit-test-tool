# implements: TOOL-TRC-050, TOOL-TRC-060
"""Requirement import from ReqIF, CSV, and a documented plain-text format (WP-TRC-03).

Three importers, one output shape: ``RequirementRecord`` rows (id, title,
text) that feed the WP-TRC-01 matrix and the WP-TRC-02 unlinked report via
``requirement_universe``. Duplicate ids are refused (a requirement inventory
with two rows for one id is ambiguous input, not a set to silently merge);
ids follow the association id discipline (non-empty, whitespace-free).

- ReqIF (TOOL-TRC-050): the documented subset of ReqIF 1.x — ``SPEC-OBJECT``
  elements (test objects written by ``reqif_export`` are skipped; attribute
  definitions are read from a ``REF`` attribute or a ``-REF`` element); the requirement id is the ``ReqIF.Identifier`` attribute value
  when present, else the ``SPEC-OBJECT`` ``IDENTIFIER``; title from
  ``LONG-NAME``; text from a ``ReqIF.Description`` attribute value. Matching
  is by local name, so namespaced and namespace-less documents both parse.
- CSV (TOOL-TRC-060): a strict header row naming the columns; ``id`` is
  required, ``title``/``text`` optional (absent columns stay empty).
- Plain text (TOOL-TRC-060): the documented line format ``ID: title text`` —
  one requirement per non-blank line, ``#`` comments allowed, no colon on a
  line is an error naming the line.

Malformed input fails with the offending location, never silently skipped.

Satisfies: TOOL-TRC-050, TOOL-TRC-060.
"""

from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass

from ectt.trc.associations import AssociationSet
from ectt.trc.errors import TrcError

__all__ = [
    "CSV_COLUMNS",
    "RequirementRecord",
    "import_reqif",
    "ReqIfImport",
    "import_reqif_with_associations",
    "import_requirements_csv",
    "import_requirements_text",
    "requirement_universe",
]

#: The documented CSV column set (TOOL-TRC-060): ``id`` required in the
#: header, ``title``/``text`` optional, order free, no other columns.
CSV_COLUMNS: tuple[str, ...] = ("id", "text", "title")

#: Object-type id suffix of test objects written by ``ectt.trc.reqif_export``.
_TEST_TYPE_SUFFIX = "ectt.type.TestCase"

_TEXT_LINE = re.compile(r"^(?P<id>[^\s:]+):\s*(?P<rest>.*)$")


@dataclass(frozen=True, order=True)
class RequirementRecord:
    """One imported requirement: stable id plus descriptive text."""

    requirement_id: str
    title: str = ""
    text: str = ""


def _checked_id(value: object, where: str) -> str:
    if not isinstance(value, str) or not value or any(char.isspace() for char in value):
        raise TrcError(f"{where}: requirement id must be a non-empty string without whitespace", reason="invalid_id")
    return value


def _deduplicated(records: list[RequirementRecord]) -> tuple[RequirementRecord, ...]:
    seen: dict[str, RequirementRecord] = {}
    for record in records:
        if record.requirement_id in seen:
            raise TrcError(
                f"duplicate requirement id '{record.requirement_id}' in the imported inventory",
                reason="duplicate_requirement",
            )
        seen[record.requirement_id] = record
    return tuple(seen[key] for key in sorted(seen))


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _attribute_values(spec_object: ET.Element) -> dict[str, str]:
    """Map a SPEC-OBJECT's attribute definitions (by their REF) to values."""
    values: dict[str, str] = {}
    for element in spec_object.iter():
        if _local_name(element.tag) != "ATTRIBUTE-VALUE-STRING":
            continue
        the_value = element.get("THE-VALUE")
        if the_value is None:
            continue
        for child in element.iter():
            local = _local_name(child.tag)
            if local == "ATTRIBUTE-DEFINITION-STRING":
                ref = child.get("REF")  # documented-subset form: REF attribute
            elif local == "ATTRIBUTE-DEFINITION-STRING-REF":
                ref = (child.text or "").strip() or None  # schema form: element text
            else:
                continue
            if ref is not None:
                values[ref] = the_value
    return values


def _is_test_object(spec_object: ET.Element) -> bool:
    """True for objects of the exporter's test-case type (not requirements)."""
    return any(
        _local_name(child.tag) == "SPEC-OBJECT-TYPE-REF" and (child.text or "").strip().endswith(_TEST_TYPE_SUFFIX)
        for child in spec_object.iter()
    )


def import_reqif(text: str) -> tuple[RequirementRecord, ...]:
    """Import requirements from a ReqIF 1.x document (documented subset).

    Records only; use :func:`import_reqif_with_associations` when the
    document's ``SPEC-RELATIONS`` should come back as associations too.
    """
    return import_reqif_with_associations(text).records


def import_reqif_with_associations(text: str) -> ReqIfImport:
    """Import requirements and associations from a ReqIF 1.x document (B7).

    Everything :func:`import_reqif` reads, plus the ``SPEC-RELATIONS``: each
    relation's SOURCE and TARGET ``SPEC-OBJECT-REF`` is resolved through the
    document's ``SPEC-OBJECT`` identifiers to the real requirement/test ids
    (the ``ReqIF.Identifier`` attribute value when present, else the
    ``IDENTIFIER``), giving the requirement-to-test associations the exporter
    wrote from the matrix — export then import is lossless. A relation whose
    SOURCE or TARGET names no ``SPEC-OBJECT`` in the same document is refused
    with a named reason (``dangling_relation``); duplicate relations for the
    same pair merge once (the association set deduplicates by construction).
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise TrcError(f"ReqIF document is not well-formed XML: {exc}", reason="malformed_reqif") from exc

    records: list[RequirementRecord] = []
    real_id_by_xml: dict[str, str] = {}
    test_xml_ids: set[str] = set()
    for element in root.iter():
        if _local_name(element.tag) != "SPEC-OBJECT" or _is_test_object(element):
            continue
        identifier = element.get("IDENTIFIER")
        long_name = element.get("LONG-NAME", "")
        attributes = _attribute_values(element)
        reqif_identifier = next(
            (value for ref, value in attributes.items() if ref.endswith("ReqIF.Identifier")),
            None,
        )
        requirement_id = reqif_identifier if reqif_identifier is not None else identifier
        description = next(
            (value for ref, value in attributes.items() if ref.endswith("ReqIF.Description")),
            "",
        )
        if requirement_id is None:
            raise TrcError(
                f"ReqIF SPEC-OBJECT (LONG-NAME '{long_name}') carries neither a "
                "ReqIF.Identifier attribute value nor an IDENTIFIER",
                reason="missing_requirement_id",
            )
        real_id = _checked_id(requirement_id, "ReqIF SPEC-OBJECT")
        records.append(
            RequirementRecord(
                requirement_id=real_id,
                title=long_name,
                text=description,
            )
        )
        if identifier is not None:
            real_id_by_xml[identifier] = real_id

    # Test objects: their real id is the ReqIF.Identifier attribute value when
    # present (the exporter writes it), else the IDENTIFIER.
    for element in root.iter():
        if _local_name(element.tag) != "SPEC-OBJECT" or not _is_test_object(element):
            continue
        identifier = element.get("IDENTIFIER")
        if identifier is None:
            continue
        attributes = _attribute_values(element)
        test_id = next(
            (value for ref, value in attributes.items() if ref.endswith("ReqIF.Identifier")),
            None,
        )
        real_id_by_xml[identifier] = _checked_id(test_id if test_id is not None else identifier, "ReqIF test object")
        test_xml_ids.add(identifier)

    # SPEC-RELATIONS back as requirement-to-test associations.
    associations = AssociationSet()
    for element in root.iter():
        if _local_name(element.tag) != "SPEC-RELATION":
            continue
        source_ref = _relation_ref(element, "SOURCE")
        target_ref = _relation_ref(element, "TARGET")
        for ref in (source_ref, target_ref):
            if ref not in real_id_by_xml:
                raise TrcError(
                    f"SPEC-RELATION references SPEC-OBJECT '{ref}' which the document does not define",
                    reason="dangling_relation",
                )
        requirement_id = real_id_by_xml[source_ref]
        test_id = real_id_by_xml[target_ref]
        if target_ref not in test_xml_ids:
            raise TrcError(
                f"SPEC-RELATION TARGET '{target_ref}' is not a test-case object",
                reason="relation_target_not_a_test",
            )
        associations.add(requirement_id, test_id)

    return ReqIfImport(records=_deduplicated(records), associations=associations)


def _relation_ref(relation: ET.Element, side: str) -> str:
    """The SPEC-OBJECT-REF text under the relation's SOURCE or TARGET."""
    for child in relation:
        if _local_name(child.tag) != side:
            continue
        for grandchild in child:
            if _local_name(grandchild.tag) == "SPEC-OBJECT-REF":
                ref = (grandchild.text or "").strip()
                if ref:
                    return ref
        ref_attr = child.get("REF")
        if ref_attr:
            return ref_attr.strip()
    raise TrcError(
        f"SPEC-RELATION carries no {side} SPEC-OBJECT-REF",
        reason="malformed_relation",
    )


@dataclass(frozen=True)
class ReqIfImport:
    """Requirements plus the associations read back from SPEC-RELATIONS (B7)."""

    records: tuple[RequirementRecord, ...]
    associations: AssociationSet


def import_requirements_csv(text: str) -> tuple[RequirementRecord, ...]:
    """Import requirements from strict CSV with a header row.

    The header must name the columns; ``id`` is required, ``title`` and
    ``text`` are optional and default to empty. Column order is free.
    """
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames
    names = [name.strip() for name in header] if header else []
    if "id" not in names:
        raise TrcError(
            f"requirements CSV header must name an 'id' column (got {header!r})",
            reason="missing_id_column",
        )
    if len(names) != len(set(names)):
        raise TrcError(f"requirements CSV header repeats a column: {header!r}", reason="duplicate_column")
    unknown = [name for name in names if name not in CSV_COLUMNS]
    if unknown:
        raise TrcError(
            f"requirements CSV header names undocumented columns {unknown} (documented: {', '.join(CSV_COLUMNS)})",
            reason="unknown_column",
        )

    records: list[RequirementRecord] = []
    for row_number, row in enumerate(reader, start=2):
        raw_id = (row.get("id") or "").strip()
        requirement_id = _checked_id(raw_id, f"CSV row {row_number}")
        records.append(
            RequirementRecord(
                requirement_id=requirement_id,
                title=(row.get("title") or "").strip(),
                text=(row.get("text") or "").strip(),
            )
        )

    return _deduplicated(records)


def import_requirements_text(text: str) -> tuple[RequirementRecord, ...]:
    """Import requirements from the documented plain-text line format.

    Each non-blank, non-comment line is ``ID: title text`` (the part after
    the first colon is the requirement's title; the text stays empty — the
    plain-text format trades richness for editability).
    """
    records: list[RequirementRecord] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = _TEXT_LINE.match(line)
        if match is None:
            raise TrcError(
                f"plain-text requirements line {line_number} does not match 'ID: title': {line!r}",
                reason="malformed_line",
            )
        records.append(
            RequirementRecord(
                requirement_id=_checked_id(match.group("id"), f"plain-text line {line_number}"),
                title=match.group("rest").strip(),
                text="",
            )
        )

    return _deduplicated(records)


def requirement_universe(records: Iterable[RequirementRecord]) -> tuple[str, ...]:
    """The requirement universe the WP-TRC-01 matrix and WP-TRC-02 report consume."""
    return tuple(sorted({record.requirement_id for record in records}))
