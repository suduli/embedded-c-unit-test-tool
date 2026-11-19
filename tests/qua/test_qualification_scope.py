"""Tests for the qualification-scope statement (WP-QUA-07).

Verifies: TOOL-QUA-090 and the PLAN-001 §5.4 exit criterion for WP-QUA-07.
"""

from __future__ import annotations

import pathlib

import pytest

from ectt.qua.qualification_scope import (
    NON_CLAIM_SENTENCE,
    OverclaimError,
    ProvidedItem,
    QualificationScope,
    default_scope,
    render,
)


def test_statement_is_single_deterministic_render() -> None:
    """verifies: TOOL-QUA-090 (§5.4: "in one place")

    Rendering twice is byte-identical: one canonical statement, no drift.
    """
    assert render(default_scope()) == render(default_scope())


def test_every_provided_item_cites_existing_verification_note() -> None:
    """verifies: TOOL-QUA-090 (§5.4: evidence "provided")

    Each provided claim cites verification notes that actually exist in the
    repository — no evidence-free claims.
    """
    scope = default_scope()
    assert scope.provided, "statement must provide evidence"
    for item in scope.provided:
        citations = [chunk.strip() for chunk in item.evidence.split(",")]
        assert citations, item.claim
        for citation in citations:
            path = pathlib.Path(citation)
            assert path.is_file(), f"missing evidence file: {citation}"


def test_user_responsibility_section_is_explicit() -> None:
    """verifies: TOOL-QUA-090 (§5.4: "user's responsibility")

    The responsibility section is non-empty and each entry is a full sentence.
    """
    scope = default_scope()
    assert scope.user_responsibility
    for entry in scope.user_responsibility:
        assert entry.strip() != ""
        assert entry.endswith(".")


def test_no_certification_claim_is_present() -> None:
    """verifies: TOOL-QUA-090

    The provided-evidence section contains exactly one certification-related
    sentence: the fixed non-claim. (The user-responsibility section may name
    certification as something that stays with the user.)
    """
    text = render(default_scope())
    provided_section = text.split("What remains the user's responsibility:")[0].lower()
    assert NON_CLAIM_SENTENCE in text
    # Only the fixed non-claim sentence names certification/certificate.
    assert provided_section.count("certification") == 1
    assert provided_section.count("certificate") == 1
    assert "is certified" not in provided_section
    assert "certified tool" not in provided_section


def test_renderer_refuses_uncited_certification_claim() -> None:
    """verifies: TOOL-QUA-090 (overclaim guard)

    A provided item claiming certification raises OverclaimError instead of
    rendering — fail closed.
    """
    bad_scope = QualificationScope(
        provided=(ProvidedItem(claim="Tool is ISO 26262 certified", evidence="nowhere.md"),),
    )
    with pytest.raises(OverclaimError):
        render(bad_scope)


def test_classification_is_recorded_as_open_not_decided() -> None:
    """verifies: TOOL-QUA-090 (ADR-sensitive boundary)

    The classification line is an open question reference, never a chosen
    class: the night run must not decide ADR-sensitive questions.
    """
    scope = default_scope()
    assert scope.classification.startswith("OPEN")
    assert "WP-QUA-01" in scope.classification


def test_statement_names_user_responsibility_in_render() -> None:
    """verifies: TOOL-QUA-090 (§5.4 wording)

    The rendered output carries both section headers required by the
    criterion: provided evidence and user responsibility.
    """
    text = render(default_scope())
    assert "What the tool provides" in text
    assert "What remains the user's responsibility" in text
