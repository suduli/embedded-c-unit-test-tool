"""bootstrap: preview is mutation-free; apply creates the project, fields,
views and label idempotently; Status option updates preserve option ids."""
from __future__ import annotations

import pytest

from conftest import REPO, OWNER, register_components

import github_projects as gp

REPO_ROOT = gp.Path(__file__).resolve().parents[2]


def test_bootstrap_preview_makes_no_writes(fake_gh):
    ops, notes = gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, None, apply_changes=False)
    kinds = {op["op"] for op in ops}
    assert {"ensure_field", "ensure_status_options", "ensure_view", "ensure_label"} <= kinds
    assert fake_gh.project is None        # nothing created
    assert fake_gh.labels == {}
    assert fake_gh.mutations == []
    ensure_fields = [op for op in ops if op["op"] == "ensure_field"]
    by_name = {op["name"]: op for op in ensure_fields}
    assert by_name[gp.FIELD_WORK_PACKAGE]["dataType"] == "TEXT"
    assert by_name[gp.FIELD_COMPONENT]["options"] == register_components()
    assert by_name[gp.FIELD_PHASE]["options"] == gp.PHASE_OPTIONS
    assert by_name[gp.FIELD_EFFORT]["dataType"] == "NUMBER"
    assert by_name[gp.FIELD_DEPENDS_ON]["dataType"] == "TEXT"
    status = next(op for op in ops if op["op"] == "ensure_status_options")
    assert status["options"] == gp.STATUS_OPTIONS


def test_bootstrap_apply_creates_everything_then_is_idempotent(fake_gh):
    ops, notes = gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, None, apply_changes=True)
    assert fake_gh.project is not None
    assert fake_gh.project["title"] == gp.PROJECT_TITLE
    assert {gp.FIELD_WORK_PACKAGE, gp.FIELD_COMPONENT, gp.FIELD_PHASE,
            gp.FIELD_EFFORT, gp.FIELD_DEPENDS_ON} <= set(fake_gh.fields)
    assert [o["name"] for o in fake_gh.fields["Status"]["options"]] == gp.STATUS_OPTIONS
    assert [o["name"] for o in fake_gh.fields[gp.FIELD_COMPONENT]["options"]] == register_components()
    assert set(fake_gh.views) == {spec["name"] for spec in gp.VIEW_SPECS}
    assert fake_gh.labels["blocked"]["color"] == gp.BLOCKED_LABEL["color"]
    # Views carry their filters; grouping is reported as the manual step.
    recon = fake_gh.views["Reconciliation"]
    assert recon["filter"] == f'Status:"{gp.INITIAL_STATUS}"'
    delivery = fake_gh.views["Delivery"]
    assert delivery["filter"] == f'-Status:"{gp.INITIAL_STATUS}"'
    assert any("group by Status" in n for n in notes)
    # Second run: nothing new is created.
    creations_before = len(fake_gh.mutations)
    _, notes2 = gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, None, apply_changes=True)
    assert "Status options already match" in notes2
    assert len(fake_gh.mutations) == creations_before


def test_bootstrap_updates_status_options_preserving_ids(fake_gh):
    """An existing project's Status options keep their ids where names match,
    so item selections survive a bootstrap re-run."""
    fake_gh.project = {"id": "PROJ_1", "number": 1, "title": gp.PROJECT_TITLE, "resourcePath": "/x"}
    fake_gh.fields["Status"] = {"id": "FIELD_STATUS", "dataType": "SINGLE_SELECT", "options": [
        {"id": "OPT_T", "name": "Todo"},
        {"id": "OPT_IP", "name": "In Progress"},
        {"id": "OPT_D", "name": "Done"},
    ]}
    _, notes = gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, None, apply_changes=True)
    options = {o["name"]: o["id"] for o in fake_gh.fields["Status"]["options"]}
    assert set(options) == set(gp.STATUS_OPTIONS)
    assert options["In Progress"] == "OPT_IP"   # preserved
    assert "Todo" not in options                # replaced
    assert any("Status options set to" in n for n in notes)


def test_bootstrap_with_explicit_project_number(fake_gh):
    fake_gh.project = {"id": "PROJ_1", "number": 7, "title": gp.PROJECT_TITLE, "resourcePath": "/x"}
    fake_gh.fields["Status"] = {"id": "FIELD_STATUS", "dataType": "SINGLE_SELECT", "options": [
        {"id": "OPT_T", "name": "Todo"}, {"id": "OPT_IP", "name": "In Progress"}, {"id": "OPT_D", "name": "Done"},
    ]}
    ops, notes = gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, 7, apply_changes=True)
    assert any("configuring existing project" in n for n in notes)
    assert fake_gh.project["number"] == 7
    # No createProjectV2 mutation was issued.
    assert "createProjectV2" not in [name for name, _ in fake_gh.mutations]
    assert [o["name"] for o in fake_gh.fields["Status"]["options"]] == gp.STATUS_OPTIONS


def test_bootstrap_refuses_a_mistitled_project(fake_gh):
    fake_gh.project = {"id": "PROJ_1", "number": 7, "title": "Wrong board", "resourcePath": "/x"}
    with pytest.raises(gp.ProjectsError, match="titled 'Wrong board'"):
        gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, 7, apply_changes=True)


def test_bootstrap_component_options_follow_the_register(fake_gh, tmp_path):
    """A new CMP-* component in the register gains an option on the next run."""
    fake_gh.project = {"id": "PROJ_1", "number": 1, "title": gp.PROJECT_TITLE, "resourcePath": "/x"}
    fake_gh.fields["Status"] = {"id": "FIELD_STATUS", "dataType": "SINGLE_SELECT", "options": [
        {"id": f"OPT_S{i}", "name": o} for i, o in enumerate(gp.STATUS_OPTIONS)
    ]}
    fake_gh.fields[gp.FIELD_COMPONENT] = {"id": "FIELD_COMP", "dataType": "SINGLE_SELECT",
                                          "options": [{"id": "OPT_0", "name": "CMP-ANA"}]}
    _, notes = gp.bootstrap(fake_gh, REPO_ROOT, REPO, OWNER, None, apply_changes=True)
    names = {o["name"] for o in fake_gh.fields[gp.FIELD_COMPONENT]["options"]}
    assert names == set(register_components())
    assert any("added options to 'Component'" in n for n in notes)
