# implements: TOOL-SEC-080
"""The SECURITY draft matches the machine-readable policy (B5).

docs/proposals/SECURITY-draft.md is the owner-review draft the owner copies
to the repository root as SECURITY.md. The draft must stay consistent with
the frozen policy data in ectt.sec.policy, must carry the DRAFT state, must
not invent contact addresses (reporting goes through GitHub), and
must not exist at the repository root yet (that promotion is the owner's).
"""

from __future__ import annotations

from pathlib import Path

from ectt.sec.policy import (
    ACKNOWLEDGEMENT_COMMITMENT,
    POLICY_STATE,
    REPORT_CONTENT_ITEMS,
    RESOLUTION_COMMITMENT_DAYS,
    SUPPORTED_VERSIONS_RULE,
    disclosure_policy,
)

REPO_ROOT = Path(__file__).parents[2]
DRAFT = REPO_ROOT / "docs" / "proposals" / "SECURITY-draft.md"
ROOT_SECURITY = REPO_ROOT / "SECURITY.md"


def _draft_text() -> str:
    assert DRAFT.is_file(), "the SECURITY draft is missing"
    return DRAFT.read_text(encoding="utf-8")


def test_draft_is_present_and_marked_owner_review() -> None:
    text = _draft_text()
    assert "# DRAFT: Security Policy" in text
    assert POLICY_STATE in text  # "owner-review-draft"
    assert "owner" in text.lower()


def test_draft_names_github_reporting_and_invents_no_contact() -> None:
    """verifies: B5 — the owner chose GitHub private reporting; no address is published."""
    text = _draft_text()
    assert "Report a vulnerability" in text
    assert "OWNER-CONTACT-REQUIRED" not in text
    # no plausible email or @handle crept in
    assert "@" not in text


def test_draft_is_not_promoted_to_the_root() -> None:
    """The promotion to SECURITY.md is the owner's action, not the draft wave's."""
    assert not ROOT_SECURITY.exists()


def test_draft_commitments_match_the_machine_readable_policy() -> None:
    text = _draft_text()
    policy = disclosure_policy()
    assert policy.state == POLICY_STATE
    # the four expected report items all appear
    for item in REPORT_CONTENT_ITEMS:
        key = item.split(" ")[0].replace("version(s)", "version")
        assert key in text or item in text, item
    # the commitments' numbers appear with their units
    assert "5 business" in text and "5" in ACKNOWLEDGEMENT_COMMITMENT
    assert "90 days" in text and str(RESOLUTION_COMMITMENT_DAYS) in text
    # the supported-version rule is the pre-1.0 rule, and the draft says so
    assert "pre-1.0" in text
    assert "latest release line" in text
    assert SUPPORTED_VERSIONS_RULE.split(":")[0] in text
