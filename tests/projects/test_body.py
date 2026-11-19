"""Issue-body rendering and hashing: markers, generated/human split, unverified
historical claims, dependency annotations, and hash-driven write suppression."""
from __future__ import annotations

import re

import pytest

import github_projects as gp

REPO_ROOT = gp.Path(__file__).resolve().parents[2]
REPO = "suduli/embedded-c-unit-test-tool"


def _package(wid: str) -> gp.Package:
    packages = gp.load_source(REPO_ROOT)
    return next(p for p in packages if p.wid == wid)


def test_body_carries_hidden_marker_and_block_boundaries():
    pkg = _package("WP-CORE-01")
    body = gp.render_body(pkg, REPO, "rev0", gp.content_hash(pkg, REPO))
    assert body.startswith(f"<!-- ectt-work-package:{pkg.wid} -->")
    before, after = gp.split_generated(body)
    assert before.startswith(f"<!-- ectt-work-package:{pkg.wid} -->")
    assert "## Reconciliation notes" in after
    assert after.strip().endswith("_Initial status: Needs reconciliation. Review requirements, dependencies and acceptance criteria before moving to Backlog._")


def test_title_follows_register():
    pkg = _package("WP-CORE-01")
    assert pkg.title == f"[{pkg.wid}] {pkg.capability}"


def test_requirements_table_lists_srs_attributes():
    pkg = _package("WP-PRJ-01")
    body = gp.render_body(pkg, REPO, "rev0", gp.content_hash(pkg, REPO))
    assert "## Requirements owned (5)" in body
    assert "| `TOOL-PRJ-010` | M | P2 | I |" in body
    assert "| `TOOL-UIX-320` | M | P1 | I |" in body
    assert "[SRS-001-requirements.md]" in body


def test_dependency_annotations_preserved_in_body():
    pkg = _package("WP-CORE-05")
    body = gp.render_body(pkg, REPO, "rev0", gp.content_hash(pkg, REPO))
    assert "- `~ANA-04` → [WP-ANA-04]" in body
    assert "schedule-only" in body
    atg04 = _package("WP-ATG-04")
    body = gp.render_body(atg04, REPO, "rev0", gp.content_hash(atg04, REPO))
    assert "- `^COV-01` → [WP-COV-01]" in body
    assert "port-mediated" in body


def test_dependency_links_resolve_without_issue_numbers():
    """Links are issue-search URLs, so they work regardless of import order and
    the body stays a pure function of the register (zero-write reruns)."""
    pkg = _package("WP-CORE-05")
    body = gp.render_body(pkg, REPO, "rev0", gp.content_hash(pkg, REPO))
    assert "https://github.com/suduli/embedded-c-unit-test-tool/issues?q=" in body
    assert "%22ectt-work-package%3AWP-ANA-04%22" in body


def test_missing_acceptance_criterion_flagged_for_reconciliation():
    pkg = _package("WP-CORE-02")  # not in §5.4
    body = gp.render_body(pkg, REPO, "rev0", gp.content_hash(pkg, REPO))
    assert "flagged for reconciliation" in body
    recorded = _package("WP-CORE-01")
    body = gp.render_body(recorded, REPO, "rev0", gp.content_hash(recorded, REPO))
    assert "> Two runs from identical inputs on different machines" in body
    assert "flagged for reconciliation" not in body


def test_historical_completion_claims_shown_unverified():
    spike = _package("WP-SPIKE-02")
    body = gp.render_body(spike, REPO, "rev0", gp.content_hash(spike, REPO))
    assert "## Historical references (unverified)" in body
    assert "PLAN-001 §4.4 records this spike complete in ADR-001" in body
    regular = _package("WP-CORE-01")
    body = gp.render_body(regular, REPO, "rev0", gp.content_hash(regular, REPO))
    assert "Historical references" not in body


def test_content_hash_stable_and_independent_of_revision():
    pkg = _package("WP-CORE-01")
    assert gp.content_hash(pkg, REPO) == gp.content_hash(pkg, REPO)
    other = gp.Package(**{**pkg.__dict__})
    other.effort = pkg.effort + 1
    assert gp.content_hash(other, REPO) != gp.content_hash(pkg, REPO)


def test_capability_change_changes_hash():
    pkg = _package("WP-CORE-01")
    other = gp.Package(**{**pkg.__dict__})
    other.capability = "Renamed capability"
    assert gp.content_hash(other, REPO) != gp.content_hash(pkg, REPO)


def test_stored_hash_read_back_from_body():
    pkg = _package("WP-CORE-01")
    digest = gp.content_hash(pkg, REPO)
    body = gp.render_body(pkg, REPO, "rev0", digest)
    assert gp.stored_hash(body) == digest


def test_update_preserves_the_human_tail():
    pkg = _package("WP-CORE-01")
    digest = gp.content_hash(pkg, REPO)
    original = gp.render_body(pkg, REPO, "rev0", digest)
    before, after = gp.split_generated(original)
    human = after.replace("## Reconciliation notes",
                          "## Reconciliation notes\n\nHuman decision: reconciled on 2026-11-12, keep in Review.")
    rebuild = before + gp.render_generated_block(pkg, REPO, "rev1", digest) + human
    assert "Human decision: reconciled on 2026-11-12" in rebuild
    assert rebuild.count(gp.GENERATED_BEGIN) == 1
    assert rebuild.count(gp.GENERATED_END) == 1


def test_marker_without_generated_block_is_detectable():
    body = "<!-- ectt-work-package:WP-CORE-01 -->\n\nFree-form human content."
    assert gp.split_generated(body) is None
    assert gp.stored_hash(body) is None
