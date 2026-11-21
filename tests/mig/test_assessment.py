# implements: TOOL-MIG-090
"""Migration assessment mode (WP-MIG-07).

Verifies: TOOL-MIG-090 — expected fidelity and manual effort are reported before
migration is attempted; the assessment is read-only and fail-safe.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.mig.assessment import (
    OUTCOMES,
    assess_ceedling_project,
    assess_mapped_csv,
    dump_assessment,
)
from ectt.mig.coexistence import assert_no_interference, snapshot_tree
from tests.mig.test_ceedling import _make_project

MAPPING = {"Case": "id", "Module": "unit", "Func": "function", "Want": "expect_return"}
CLEAN_CSV = "Case,Module,Func,Want\nc1,a.c,f,1\nc2,a.c,g,2\n"
MESSY_CSV = (
    "Case,Module,Func,Want,Comment,Slot\n"
    "c1,a.c,f,1,,\n"
    "c2,a.c,f,2,remember this,\n"
    "c3,a.c,f,3,,4\n"
    ",a.c,f,5,,\n"
)


def test_a_clean_export_is_ready_with_full_fidelity() -> None:
    result = assess_mapped_csv(CLEAN_CSV, MAPPING)

    assert result.outcome == "ready"
    assert result.manual_items == ()
    assert result.expected_fidelity()["percentages"]["converted"] == 100.0


def test_a_messy_export_reports_expected_fidelity_with_denominators() -> None:
    result = assess_mapped_csv(MESSY_CSV, MAPPING, deferred_columns={"Slot": "slot"})

    assert result.outcome == "needs_manual_work"
    fidelity = result.expected_fidelity()
    assert fidelity["counts"] == {"converted": 1, "converted_lossy": 1, "not_converted": 2}
    assert fidelity["denominator"] == "4 artifacts"
    assert fidelity["percentages"] == {"converted": 25.0, "converted_lossy": 25.0, "not_converted": 50.0}


def test_manual_effort_is_one_item_per_finding_with_an_action() -> None:
    result = assess_mapped_csv(MESSY_CSV, MAPPING, deferred_columns={"Slot": "slot"})

    assert [(m.artifact, m.kind) for m in result.manual_items] == [
        ("row 2", "unmapped_column"),
        ("row 3", "deferred_structure"),
        ("row 4", "missing_id"),
    ]
    assert all(m.action for m in result.manual_items)
    assert result.effort_by_kind() == {"deferred_structure": 1, "missing_id": 1, "unmapped_column": 1}


def test_deferred_compound_structures_are_listed_with_location() -> None:
    result = assess_mapped_csv(MESSY_CSV, MAPPING, deferred_columns={"Slot": "slot"})

    assert result.deferred_set() == {("slot", "row 3", "row 3, column 'Slot'")}
    deferred = next(m for m in result.manual_items if m.kind == "deferred_structure")
    assert "C-source test" in deferred.action


def test_effort_is_counted_never_timed() -> None:
    document = json.loads(dump_assessment(assess_mapped_csv(MESSY_CSV, MAPPING)))

    assert document["effort"]["unit"] == "items (no durations are estimated)"
    text = dump_assessment(assess_mapped_csv(MESSY_CSV, MAPPING)).lower()
    assert "hour" not in text and "minute" not in text and "day" not in text


def test_ceedling_assessment_reports_losses_per_artifact(tmp_path: Path) -> None:
    result = assess_ceedling_project(_make_project(tmp_path / "ceed"))

    assert result.outcome == "needs_manual_work"
    kinds = {m.kind for m in result.manual_items}
    assert kinds == {"parameterised_test_attribute", "duplicate_test_name"}
    assert result.expected_fidelity()["counts"] == {"converted": 2, "converted_lossy": 1, "not_converted": 0}


def test_a_ceedling_project_without_losses_is_ready(tmp_path: Path) -> None:
    root = tmp_path / "p"
    (root / "test").mkdir(parents=True)
    (root / "project.yml").write_text(":paths:\n  :test:\n    - test\n", encoding="utf-8")
    (root / "test" / "test_a.c").write_text("void test_a(void) {}\n", encoding="utf-8")

    result = assess_ceedling_project(root)

    assert result.outcome == "ready" and result.manual_items == ()


def test_assessment_never_modifies_the_legacy_project(tmp_path: Path) -> None:
    root = _make_project(tmp_path / "ceed")
    before = snapshot_tree(root)

    assess_ceedling_project(root)

    assert_no_interference(before, snapshot_tree(root), context="ceedling assessment")


@pytest.mark.parametrize(
    ("text", "mapping", "reason"),
    [
        ("", MAPPING, "empty_input"),
        ("Case,Module\nc,m\n", MAPPING, "unknown_column"),
        (CLEAN_CSV, {}, "empty_mapping"),
    ],
)
def test_unreadable_exports_are_findings_not_exceptions(text: str, mapping: dict[str, str], reason: str) -> None:
    result = assess_mapped_csv(text, mapping)

    assert result.outcome == "not_assessable"
    assert result.reason is not None and result.reason.startswith(reason)
    assert result.fidelity is None and result.manual_items == ()
    assert result.expected_fidelity()["artifacts"] == 0


@pytest.mark.parametrize(
    ("setup", "reason"),
    [
        (None, "no_project_file"),
        ("- list\n", "invalid_project_file"),
        (":paths:\n  :test:\n    - ../outside\n", "path_escape"),
    ],
)
def test_unreadable_ceedling_projects_are_findings_not_exceptions(tmp_path: Path, setup: str | None, reason: str) -> None:
    if setup is not None:
        (tmp_path / "project.yml").write_text(setup, encoding="utf-8")

    result = assess_ceedling_project(tmp_path)

    assert result.outcome == "not_assessable"
    assert result.reason is not None and result.reason.startswith(reason)


def test_outcomes_are_a_closed_vocabulary() -> None:
    seen = {
        assess_mapped_csv(CLEAN_CSV, MAPPING).outcome,
        assess_mapped_csv(MESSY_CSV, MAPPING).outcome,
        assess_mapped_csv("", MAPPING).outcome,
    }
    assert seen == set(OUTCOMES)


def test_assessment_document_is_deterministic_and_embeds_the_fidelity_report() -> None:
    first = dump_assessment(assess_mapped_csv(MESSY_CSV, MAPPING, deferred_columns={"Slot": "slot"}))
    second = dump_assessment(assess_mapped_csv(MESSY_CSV, MAPPING, deferred_columns={"Slot": "slot"}))
    assert first == second

    document = json.loads(first)
    assert document["fidelity_report"]["report_version"] == "1"
    assert document["fidelity_report"]["counts"] == document["expected_fidelity"]["counts"]
    assert document["outcome"] == "needs_manual_work"


def test_findings_without_a_known_action_fall_back_to_review() -> None:
    from ectt.mig.assessment import _manual_items
    from ectt.mig.fidelity import ArtifactFidelity, FidelityNote, FidelityReport

    report = FidelityReport(
        "s",
        (ArtifactFidelity("a", "x", "converted_lossy", (FidelityNote("brand_new_kind", "d", "loss"), FidelityNote("fyi", "d", "info"))),),
        (),
    )
    (item,) = _manual_items(report)
    assert item.kind == "brand_new_kind" and item.action == "Review the finding by hand"
