# implements: TOOL-TRC-070, TOOL-TRC-110
"""ReqIF SPEC-RELATIONS import back as associations (B7): lossless round trip.

export_reqif writes one SPEC-RELATION per unique (requirement, test) pair;
import_reqif_with_associations reads them back, so export then import
reproduces the matrix's associations exactly.
"""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET

import pytest

from ectt.trc import (
    Association,
    AssociationSet,
    RequirementRecord,
    TrcError,
    build_matrix,
    export_reqif,
    import_reqif,
    import_reqif_with_associations,
)

WHEN = "2026-11-21T00:00:00+00:00"


def _matrix():
    associations = AssociationSet()
    for requirement, test in (("REQ-1", "t.a"), ("REQ-1", "t.b"), ("REQ-2", "t.a"), ("REQ-3", "t.gen")):
        associations.add(requirement, test)
    statuses = {"t.a": "pass", "t.b": "fail", "t.gen": "pass"}
    return build_matrix(
        associations,
        statuses,
        requirement_universe=["REQ-1", "REQ-2", "REQ-3"],
        unreviewed_tests=["t.gen"],
    )


def _expected_pairs():
    matrix = _matrix()
    return tuple(
        sorted(
            Association(row.requirement_id, link.test_id)
            for row in matrix.rows
            for link in row.links
        )
    )


RECORDS = (
    RequirementRecord("REQ-1", "First", "one"),
    RequirementRecord("REQ-2", "Second", "two"),
    RequirementRecord("REQ-3", "", ""),
)


def _export() -> str:
    return export_reqif(_matrix(), RECORDS, creation_time=WHEN)


def _mutated(mutate) -> str:
    """Parse the export, mutate it, and serialize back with the namespace."""
    root = ET.fromstring(_export())
    mutate(root)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def _relations_element(root: ET.Element) -> ET.Element:
    return next(el for el in root.iter() if el.tag.endswith("SPEC-RELATIONS"))


def _set_relation_target(root: ET.Element, index: int, new_ref: str) -> None:
    relations = _relations_element(root)
    relation = [r for r in relations if r.tag.endswith("SPEC-RELATION")][index]
    for child in relation:
        if child.tag.endswith("TARGET"):
            for grandchild in child:
                if grandchild.tag.endswith("SPEC-OBJECT-REF"):
                    grandchild.text = new_ref


# --- lossless round trip ----------------------------------------------------------


def test_export_then_import_is_lossless_for_associations() -> None:
    """verifies: B7 — the SPEC-RELATIONS come back as the exact pair set."""
    imported = import_reqif_with_associations(_export())
    assert imported.associations.pairs == _expected_pairs()
    assert imported.associations.pair_count == 4
    assert sorted(r.requirement_id for r in imported.records) == ["REQ-1", "REQ-2", "REQ-3"]


def test_import_reqif_keeps_its_records_only_contract() -> None:
    """The existing records-only entry point is unchanged."""
    assert import_reqif(_export()) == tuple(sorted(RECORDS))


def test_duplicate_relation_merges_once() -> None:
    """verifies: B7 — a duplicated SPEC-RELATION yields one association."""

    def mutate(root: ET.Element) -> None:
        relations = _relations_element(root)
        first = next(r for r in relations if r.tag.endswith("SPEC-RELATION"))
        duplicate = copy.deepcopy(first)
        duplicate.set("IDENTIFIER", first.get("IDENTIFIER") + "_dup")
        relations.append(duplicate)

    imported = import_reqif_with_associations(_mutated(mutate))
    assert imported.associations.pairs == _expected_pairs()
    assert imported.associations.pair_count == 4


# --- fail-closed relations ----------------------------------------------------------


def test_dangling_relation_is_refused_with_a_named_reason() -> None:
    """verifies: B7 — a relation to an undefined SPEC-OBJECT is refused."""

    def mutate(root: ET.Element) -> None:
        _set_relation_target(root, 0, "t_ghost")

    with pytest.raises(TrcError) as exc_info:
        import_reqif_with_associations(_mutated(mutate))
    assert exc_info.value.reason == "dangling_relation"


def test_relation_targeting_a_requirement_is_refused() -> None:
    """A SPEC-RELATION whose TARGET is a requirement object is not an association."""

    def mutate(root: ET.Element) -> None:
        objects = [el for el in root.iter() if el.tag.endswith("SPEC-OBJECT")]
        requirement_xml = next(
            obj.get("IDENTIFIER")
            for obj in objects
            if not any(
                ref.text and ref.text.endswith("ectt.type.TestCase")
                for ref in obj.iter()
                if ref.tag.endswith("SPEC-OBJECT-TYPE-REF")
            )
        )
        _set_relation_target(root, 0, requirement_xml)

    with pytest.raises(TrcError) as exc_info:
        import_reqif_with_associations(_mutated(mutate))
    assert exc_info.value.reason == "relation_target_not_a_test"


def test_relation_without_a_source_is_refused() -> None:
    def mutate(root: ET.Element) -> None:
        relations = _relations_element(root)
        relation = next(r for r in relations if r.tag.endswith("SPEC-RELATION"))
        for child in list(relation):
            if child.tag.endswith("SOURCE"):
                relation.remove(child)

    with pytest.raises(TrcError) as exc_info:
        import_reqif_with_associations(_mutated(mutate))
    assert exc_info.value.reason == "malformed_relation"
