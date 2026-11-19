"""Standards objective mapping tests (WP-QUA-06).

Verifies: TOOL-QUA-080.
"""

from __future__ import annotations

import pytest

from ectt.qua.standards_mapping import (
    STANDARDS,
    ObjectiveMapping,
    ObjectiveMappingError,
    StandardsMapping,
    default_mapping,
    render,
)


def test_document_has_a_section_per_named_standard() -> None:
    """verifies: TOOL-QUA-080

    All five named standards get their own section, in order.
    """
    text = render(default_mapping())
    assert STANDARDS == ("ISO 26262", "IEC 61508", "IEC 62304", "EN 50128", "DO-178C")
    for standard in STANDARDS:
        assert f"{standard}:" in text


def test_every_row_cites_clause_and_evidence() -> None:
    """verifies: TOOL-QUA-080

    A well-formed row carries both the clause id and capability evidence and
    renders with both visible.
    """
    mapping = StandardsMapping(
        rows=(
            ObjectiveMapping(
                standard="ISO 26262",
                clause="5.4.7",
                capability_claim="addressed by the eligibility gate's machine-readable reasons",
                evidence="docs/verification/WP-ANA-06-analysis.md",
            ),
        ),
    )
    text = render(mapping)
    assert "clause 5.4.7" in text
    assert "docs/verification/WP-ANA-06-analysis.md" in text


def test_rows_cannot_claim_satisfaction() -> None:
    """verifies: TOOL-QUA-080 (fail-closed)

    A row claiming satisfaction/compliance is refused — only addressing
    language is permitted.
    """
    claiming = ObjectiveMapping(
        standard="ISO 26262",
        clause="5.4.7",
        capability_claim="tool satisfies the TCL requirement",
        evidence="somewhere.md",
    )
    with pytest.raises(ObjectiveMappingError, match=r"satisf"):
        render(StandardsMapping(rows=(claiming,)))


def test_default_mapping_is_empty_and_stated() -> None:
    """verifies: TOOL-QUA-080 (ADR-sensitive boundary)

    The default mapping is empty, says so explicitly, and claims no
    compliance — populating it is the classification-dependent work.
    """
    mapping = default_mapping()
    assert mapping.rows == ()
    text = render(mapping)
    assert "No objective mappings are recorded yet" in text
    assert "WP-QUA-01" in text
    assert "claims compliance" not in text.replace("Nothing below claims compliance.", "")


@pytest.mark.parametrize(
    "row",
    [
        ObjectiveMapping(standard="ISO 9999", clause="1", capability_claim="x", evidence="e.md"),
        ObjectiveMapping(standard="ISO 26262", clause="", capability_claim="x", evidence="e.md"),
        ObjectiveMapping(standard="ISO 26262", clause="1", capability_claim="x", evidence=""),
    ],
)
def test_unsourced_rows_are_refused(row: ObjectiveMapping) -> None:
    """verifies: TOOL-QUA-080 (fail-closed)

    Unknown standards, missing clauses and missing evidence are refused.
    """
    with pytest.raises(ObjectiveMappingError):
        render(StandardsMapping(rows=(row,)))


def test_render_is_deterministic() -> None:
    """verifies: TOOL-QUA-080

    Rendering twice is byte-identical.
    """
    assert render(default_mapping()) == render(default_mapping())
