"""Development process documentation tests (WP-QUA-05).

Verifies: TOOL-QUA-070.
"""

from __future__ import annotations

import pathlib

import pytest

from ectt.qua.process_documentation import (
    ProcessClaim,
    ProcessDocumentation,
    ProcessDocumentationError,
    _citation_exists,
    default_documentation,
    render,
)


def test_document_has_the_three_required_sections() -> None:
    """verifies: TOOL-QUA-070

    The rendered document carries all three required sections.
    """
    text = render(default_documentation())
    assert "Development process:" in text
    assert "Change control:" in text
    assert "Defect management:" in text


def test_every_claim_cites_an_existing_repository_artifact() -> None:
    """verifies: TOOL-QUA-070

    Every claim's citation resolves to an artifact that exists in the
    repository — a user can actually assess the process from them.
    """
    documentation = default_documentation()
    all_claims = [
        *documentation.development_process,
        *documentation.change_control,
        *documentation.defect_management,
    ]
    assert all_claims
    for claim in all_claims:
        assert _citation_exists(claim), f"missing citation: {claim.citation}"


def test_render_is_deterministic() -> None:
    """verifies: TOOL-QUA-070

    Rendering twice is byte-identical.
    """
    assert render(default_documentation()) == render(default_documentation())


def test_unsourced_claims_are_refused() -> None:
    """verifies: TOOL-QUA-070 (fail-closed)

    A claim without a citation is refused.
    """
    bad = ProcessDocumentation(
        development_process=(ProcessClaim(statement="we test everything", citation=""),),
    )
    with pytest.raises(ProcessDocumentationError):
        render(bad)


def test_no_compliance_claim_is_made() -> None:
    """verifies: TOOL-QUA-070 (no-overclaim)

    The default document asserts no process certification (ISO 26262 /
    CMMI) — compliance statements belong to the classification package.
    """
    text = render(default_documentation())
    assert "ISO 26262 certified" not in text
    assert "CMMI" not in text
    with pytest.raises(ProcessDocumentationError):
        render(
            ProcessDocumentation(
                development_process=(
                    ProcessClaim(
                        statement="Process is ISO 26262 certified",
                        citation=".github/workflows/tests.yml",
                    ),
                ),
            )
        )


def test_citation_paths_are_repo_relative(tmp_path: pathlib.Path) -> None:
    """verifies: TOOL-QUA-070

    The citation resolver strips section suffixes like '§9' before checking
    existence.
    """
    claim = ProcessClaim(statement="s", citation="pyproject.toml (§anything)")
    assert _citation_exists(claim) is True
    assert _citation_exists(ProcessClaim(statement="s", citation="no/such/file.md")) is False
