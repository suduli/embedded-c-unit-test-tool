"""plan/apply flows against an in-memory GitHub: creation, zero-write reruns,
human-edit survival, interruption recovery, conflicts, retired packages,
stale previews, and actionable failures."""
from __future__ import annotations

import pytest

from conftest import REPO, OWNER, FakeGh, json_roundtrip, seeded_project

import github_projects as gp

REPO_ROOT = gp.Path(__file__).resolve().parents[2]


def run_plan(fake: FakeGh, root=REPO_ROOT, only=None) -> dict:
    return gp.plan_import(fake, root, REPO, OWNER, 1, only=only)


def run_apply(fake: FakeGh, preview: dict, root=REPO_ROOT, only=None) -> dict:
    return gp.apply_operations(fake, json_roundtrip(preview), root, REPO, OWNER, 1, only=only)


# ---------------------------------------------------------------------------
# Creation
# ---------------------------------------------------------------------------


def test_plan_on_empty_remote_proposes_191_creations(bootstrapped):
    preview = run_plan(bootstrapped)
    assert preview["counts"]["create"] == 191
    assert preview["totals"]["packages"] == 191
    creates = [op for op in preview["operations"] if op["op"] == "create_issue"]
    assert len(creates) == 191
    first = creates[0]
    assert first["title"].startswith("[WP-")
    assert f"<!-- ectt-work-package:{first['wp']} -->" in first["body"]
    assert first["initial_status"] == "Needs reconciliation"
    assert first["fields"][gp.FIELD_COMPONENT] in ("Validation spikes",) or first["fields"][gp.FIELD_COMPONENT].startswith("CMP-")


def test_apply_creates_issues_items_fields_and_initial_status(bootstrapped):
    preview = run_plan(bootstrapped)
    report = run_apply(bootstrapped, preview)
    assert len(report["created"]) == 191
    managed, conflicts = gp.fetch_managed_issues(bootstrapped, REPO)
    assert conflicts == []
    assert len(managed) == 191
    assert all(i.state == "open" for i in managed.values())  # never closed
    assert len(bootstrapped.items) == 191
    core01 = managed["WP-CORE-01"]
    item = bootstrapped.item_for_issue(core01.number)
    assert item["field_values"]["Status"] == "Needs reconciliation"
    assert item["field_values"][gp.FIELD_WORK_PACKAGE] == "WP-CORE-01"
    assert item["field_values"][gp.FIELD_COMPONENT] == "CMP-CORE"
    assert item["field_values"][gp.FIELD_PHASE] == "P1"
    assert item["field_values"][gp.FIELD_EFFORT] == 3
    core05 = managed["WP-CORE-05"]
    item = bootstrapped.item_for_issue(core05.number)
    assert item["field_values"][gp.FIELD_DEPENDS_ON] == "~ANA-04 ~GEN-01"
    spike = managed["WP-SPIKE-01"]
    item = bootstrapped.item_for_issue(spike.number)
    assert item["field_values"][gp.FIELD_COMPONENT] == "Validation spikes"
    assert item["field_values"][gp.FIELD_DEPENDS_ON] == "—"


def test_all_nineteen_issues_get_unique_numbers_and_markers(bootstrapped):
    preview = run_plan(bootstrapped)
    run_apply(bootstrapped, preview)
    numbers = [i["number"] for i in bootstrapped.issues]
    assert len(numbers) == len(set(numbers)) == 191
    markers = []
    for issue in bootstrapped.issues:
        markers.extend(gp.MARKER_RE.findall(issue["body"]))
    assert len(markers) == len(set(markers)) == 191


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_repeated_plan_after_full_apply_makes_zero_writes(bootstrapped):
    run_apply(bootstrapped, run_plan(bootstrapped))
    preview = run_plan(bootstrapped)
    assert preview["counts"] == {"create": 0, "update": 0, "unchanged": 191,
                                 "conflict": 0, "retired_source": 0}
    assert preview["operations"] == []
    assert preview["remote_digest"]


def test_applying_a_consumed_preview_is_rejected_as_stale(bootstrapped):
    """The digest re-check makes a replayed preview fail visibly instead of
    re-running completed operations."""
    preview = run_plan(bootstrapped)
    run_apply(bootstrapped, preview)
    with pytest.raises(gp.ProjectsError) as excinfo:
        run_apply(bootstrapped, preview)
    assert excinfo.value.code == 2
    fresh = run_plan(bootstrapped)
    assert fresh["counts"]["create"] == 0 and fresh["counts"]["update"] == 0


def test_unchanged_rerun_after_partial_import_writes_nothing_for_settled_packages(bootstrapped):
    preview = run_plan(bootstrapped)
    spike_ops = [op for op in preview["operations"] if op["wp"] == "WP-SPIKE-01"]
    run_apply(bootstrapped, {**preview, "operations": spike_ops})
    fresh = run_plan(bootstrapped)
    assert fresh["counts"]["create"] == 190
    by_wp = {op["wp"]: op for op in fresh["operations"]}
    assert "WP-SPIKE-01" not in by_wp


# ---------------------------------------------------------------------------
# Human edits survive synchronization
# ---------------------------------------------------------------------------


def _fixture_repo_with_changed_effort(tmp_path, effort: str, weeks_total: str) -> gp.Path:
    """A copy of the register with WP-CORE-01's effort changed (and its layer
    rollup line adjusted so the source stays self-consistent)."""
    fixture = tmp_path / "fixture-repo"
    fixture.mkdir()
    plan_text = (REPO_ROOT / "PLAN-001-specification-analysis-and-work-breakdown.md").read_text(encoding="utf-8")
    srs_text = (REPO_ROOT / "SRS-001-requirements.md").read_text(encoding="utf-8")
    changed = plan_text.replace(
        "| `WP-CORE-01` | Determinism, source immutability and output confinement | CMP-CORE | P1 | 3w |",
        f"| `WP-CORE-01` | Determinism, source immutability and output confinement | CMP-CORE | P1 | {effort} |",
    ).replace("13 work packages · 33 requirements · 38 person-weeks",
              f"13 work packages · 33 requirements · {weeks_total} person-weeks")
    (fixture / "PLAN-001-changed.md").write_text(changed, encoding="utf-8", newline="\n")
    (fixture / "SRS-001-changed.md").write_text(srs_text, encoding="utf-8", newline="\n")
    return fixture


def _raw_issue(fake: FakeGh, number: int) -> dict:
    return next(i for i in fake.issues if i["number"] == number)


def test_human_notes_and_status_survive_an_update(bootstrapped, tmp_path, monkeypatch):
    run_apply(bootstrapped, run_plan(bootstrapped))
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    issue = managed["WP-CORE-01"]
    # A human reconciles the item and leaves notes in the human-owned tail.
    item = bootstrapped.item_for_issue(issue.number)
    item["field_values"]["Status"] = "In Progress"
    raw = _raw_issue(bootstrapped, issue.number)
    raw["body"] = raw["body"].replace(
        "_Initial status: Needs reconciliation. Review requirements, dependencies and acceptance criteria "
        "before moving to Backlog._",
        "Reconciled 2026-11-12: acceptance criteria agreed in comment thread.",
    )
    # A register change forces the importer to rewrite the generated block.
    fixture = _fixture_repo_with_changed_effort(tmp_path, "4w", 39)
    monkeypatch.setenv("GITHUB_SHA", "fixture-rev-1")   # fixture root is not a git checkout
    preview = run_plan(bootstrapped, root=fixture)
    touched = {op["wp"] for op in preview["operations"]}
    assert touched == {"WP-CORE-01"}                    # only the changed package
    assert preview["counts"]["update"] == 2             # one body rewrite + one field update
    run_apply(bootstrapped, preview, root=fixture)
    updated = bootstrapped.item_for_issue(issue.number)
    assert updated["field_values"]["Status"] == "In Progress"          # human status preserved
    assert updated["field_values"][gp.FIELD_EFFORT] == 4               # source-owned value updated
    assert "Reconciled 2026-11-12" in raw["body"]                      # human notes preserved
    assert "**Effort:** 4 person-weeks" in raw["body"]                 # generated block refreshed


def test_unrelated_packages_are_not_rewritten_by_another_packages_change(bootstrapped, tmp_path, monkeypatch):
    run_apply(bootstrapped, run_plan(bootstrapped))
    fixture = _fixture_repo_with_changed_effort(tmp_path, "5w", 40)
    monkeypatch.setenv("GITHUB_SHA", "fixture-rev-1")
    preview = run_plan(bootstrapped, root=fixture)
    assert {op["wp"] for op in preview["operations"]} == {"WP-CORE-01"}


def test_title_edits_on_unchanged_packages_are_respected(bootstrapped):
    """The importer only owns the title's content when the package changed;
    an unchanged package with a human-edited title must not be rewritten."""
    run_apply(bootstrapped, run_plan(bootstrapped))
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    issue = managed["WP-CORE-01"]
    _raw_issue(bootstrapped, issue.number)["title"] = (
        "[WP-CORE-01] Determinism, source immutability and output confinement (pinned)"
    )
    preview = run_plan(bootstrapped)
    assert preview["counts"]["update"] == 0


# ---------------------------------------------------------------------------
# Interruption recovery
# ---------------------------------------------------------------------------


def test_interrupted_creation_resumes_without_duplicates(bootstrapped):
    """A previous run created the issue but crashed before adding it to the
    project: the next run must adopt the issue, not create a replacement."""
    pkg = gp.load_source(REPO_ROOT)[0]
    digest = gp.content_hash(pkg, REPO)
    revision = gp.source_revision(REPO_ROOT)
    bootstrapped.seed_issue(pkg.title, gp.render_body(pkg, REPO, revision, digest))
    preview = run_plan(bootstrapped)
    assert preview["counts"]["create"] == 190
    ops = preview["operations"]
    assert [op["op"] for op in ops if op["wp"] == pkg.wid] == ["add_item"]
    run_apply(bootstrapped, preview)
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    assert len(managed) == 191
    assert len(bootstrapped.issues) == 191  # no duplicate was created
    assert pkg.wid in managed


def test_mid_run_failure_leaves_recoverable_state(bootstrapped):
    """An apply that dies after some creations leaves them in place; the rerun
    rediscovers them and finishes without duplicates."""
    preview = run_plan(bootstrapped)
    bootstrapped.fail_after_n_creates = 5
    with pytest.raises(gp.GhError):
        run_apply(bootstrapped, preview)
    bootstrapped.fail_after_n_creates = None
    fresh = run_plan(bootstrapped)
    assert fresh["counts"]["create"] == 186  # the five created issues are adopted
    run_apply(bootstrapped, fresh)
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    assert len(managed) == 191 and len(bootstrapped.issues) == 191


def test_interrupted_item_add_is_completed_on_rerun(bootstrapped):
    """An add that failed mid-run (issue already in the project list) is
    completed by the next apply without side effects on other items."""
    run_apply(bootstrapped, run_plan(bootstrapped))
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    # Simulate a crash between issue creation and project item creation for one
    # package: drop the item while keeping the issue.
    orphan = managed["WP-CORE-01"]
    item = bootstrapped.item_for_issue(orphan.number)
    bootstrapped.items = {k: v for k, v in bootstrapped.items.items() if k != next(iter(k for k in bootstrapped.items if bootstrapped.items[k] is item))}
    preview = run_plan(bootstrapped)
    ops = [op for op in preview["operations"] if op["wp"] == "WP-CORE-01"]
    assert [op["op"] for op in ops] == ["add_item"]
    bootstrapped.fail_on = ["addProjectV2ItemById"]     # the rerun's add fails again
    with pytest.raises(gp.GhError):
        run_apply(bootstrapped, preview)
    bootstrapped.fail_on = []
    fresh = run_plan(bootstrapped)
    assert [op["op"] for op in fresh["operations"] if op["wp"] == "WP-CORE-01"] == ["add_item"]
    run_apply(bootstrapped, fresh)
    assert len(bootstrapped.items) == 191


# ---------------------------------------------------------------------------
# Pagination and state coverage
# ---------------------------------------------------------------------------


def test_pagination_finds_open_and_closed_issues(bootstrapped):
    packages = gp.load_source(REPO_ROOT)
    revision = gp.source_revision(REPO_ROOT)
    for index, pkg in enumerate(packages[:130]):
        digest = gp.content_hash(pkg, REPO)
        state = "closed" if index % 2 else "open"
        bootstrapped.seed_issue(pkg.title, gp.render_body(pkg, REPO, revision, digest), state=state)
    managed, conflicts = gp.fetch_managed_issues(bootstrapped, REPO)
    assert conflicts == []
    assert len(managed) == 130  # >100 forces a second page
    closed = [i for i in managed.values() if i.state == "closed"]
    assert len(closed) == 65
    preview = run_plan(bootstrapped)
    assert preview["counts"]["create"] == 61  # 130 found, 61 to go


def test_closed_managed_issue_is_not_reopened(bootstrapped):
    packages = gp.load_source(REPO_ROOT)
    pkg = packages[0]
    revision = gp.source_revision(REPO_ROOT)
    bootstrapped.seed_issue(pkg.title, gp.render_body(pkg, REPO, revision, gp.content_hash(pkg, REPO)),
                            state="closed")
    preview = run_plan(bootstrapped)
    ops = [op for op in preview["operations"] if op["wp"] == pkg.wid]
    assert [op["op"] for op in ops] == ["add_item"]
    run_apply(bootstrapped, preview)
    assert next(i for i in bootstrapped.issues if i["number"] == ops[0]["issue_number"])["state"] == "closed"


# ---------------------------------------------------------------------------
# Conflicts and retired packages
# ---------------------------------------------------------------------------


def test_duplicate_markers_stop_the_run(bootstrapped):
    body = "<!-- ectt-work-package:WP-CORE-01 -->\n\ncopy one"
    bootstrapped.seed_issue("[WP-CORE-01] first", body)
    bootstrapped.seed_issue("[WP-CORE-01] second", body.replace("copy one", "copy two"))
    with pytest.raises(gp.ProjectsError, match="duplicate work-package marker WP-CORE-01"):
        run_plan(bootstrapped)


def test_title_match_without_marker_is_a_conflict(bootstrapped):
    bootstrapped.seed_issue("[WP-ANA-01] C front-end binding and dialect support", "hand-written issue")
    with pytest.raises(gp.ProjectsError, match="titled for WP-ANA-01 but carries no ectt-work-package marker"):
        run_plan(bootstrapped)


def test_multiple_markers_in_one_body_stop_the_run(bootstrapped):
    bootstrapped.seed_issue("[WP-CORE-01] mixed",
                            "<!-- ectt-work-package:WP-CORE-01 -->\n<!-- ectt-work-package:WP-CORE-02 -->")
    with pytest.raises(gp.ProjectsError, match="multiple work-package markers"):
        run_plan(bootstrapped)


def test_marker_without_generated_block_is_a_conflict(bootstrapped):
    bootstrapped.seed_issue("[WP-CORE-01] Determinism, source immutability and output confinement",
                            "<!-- ectt-work-package:WP-CORE-01 -->\n\nsomeone rebuilt this body")
    with pytest.raises(gp.ProjectsError, match="conflicting match.*not the importer's generated block"):
        run_plan(bootstrapped)


def test_retired_packages_reported_without_destructive_changes(bootstrapped):
    bootstrapped.seed_issue("[WP-GONE-01] Package that left the register",
                            "<!-- ectt-work-package:WP-GONE-01 -->\n\n" + gp.GENERATED_BEGIN + "\n"
                            "<!-- ectt-content-hash:sha256:" + "0" * 64 + " -->\n" + gp.GENERATED_END)
    preview = run_plan(bootstrapped)
    assert preview["counts"]["retired_source"] == 1
    assert preview["retired_source"] == [{"wp": "WP-GONE-01", "issue_number": 101, "state": "open"}]
    run_apply(bootstrapped, preview)
    issue = bootstrapped.issues[0]
    assert issue["state"] == "open"           # never closed
    assert issue["title"] == "[WP-GONE-01] Package that left the register"  # never touched
    summary = gp.render_summary(preview)
    assert "WP-GONE-01" in summary and "never closed or deleted" in summary


# ---------------------------------------------------------------------------
# Stale previews and conflicting changes
# ---------------------------------------------------------------------------


def test_stale_preview_rejected_when_remote_changed(bootstrapped):
    preview = run_plan(bootstrapped)
    bootstrapped.seed_issue("[WP-NEW-01] Somebody imported a package meanwhile",
                            "<!-- ectt-work-package:WP-NEW-01 -->\n" + gp.GENERATED_BEGIN + "\n"
                            "<!-- ectt-content-hash:sha256:" + "1" * 64 + " -->\n" + gp.GENERATED_END)
    with pytest.raises(gp.ProjectsError) as excinfo:
        run_apply(bootstrapped, preview)
    assert excinfo.value.code == 2
    assert "preview is stale" in str(excinfo.value)


def test_stale_preview_rejected_when_source_revision_changed(bootstrapped):
    preview = run_plan(bootstrapped)
    preview["source_revision"] = "0000000000000000000000000000000000000000"
    with pytest.raises(gp.ProjectsError) as excinfo:
        run_apply(bootstrapped, preview, root=REPO_ROOT)
    assert excinfo.value.code == 2


def test_preview_for_another_repository_is_rejected(bootstrapped):
    preview = run_plan(bootstrapped)
    preview["repo"] = "someone/else"
    with pytest.raises(gp.ProjectsError, match="different repository"):
        run_apply(bootstrapped, preview)


def test_project_title_mismatch_is_actionable(bootstrapped):
    bootstrapped.project["title"] = "Some other board"
    with pytest.raises(gp.ProjectsError, match="titled 'Some other board'"):
        run_plan(bootstrapped)


# ---------------------------------------------------------------------------
# Source-owned metadata correctness
# ---------------------------------------------------------------------------


def test_status_written_only_during_item_initialization(bootstrapped):
    run_apply(bootstrapped, run_plan(bootstrapped))
    item = next(iter(bootstrapped.items.values()))
    item["field_values"]["Status"] = "Review"
    preview = run_plan(bootstrapped)
    run_apply(bootstrapped, preview)
    assert item["field_values"]["Status"] == "Review"


def test_assignees_never_touched(monkeypatch, bootstrapped):
    """The importer has no assignee mutation in its vocabulary at all."""
    source = (REPO_ROOT / "tools" / "github_projects.py").read_text(encoding="utf-8")
    assert "assignee_ids" not in source and "addAssignees" not in source


# ---------------------------------------------------------------------------
# Failure surfaces
# ---------------------------------------------------------------------------


def test_missing_project_number_is_actionable(monkeypatch, capsys):
    monkeypatch.delenv("ECTT_PROJECT_NUMBER", raising=False)
    code = gp.main(["plan"])
    assert code == 1
    assert "no project number" in capsys.readouterr().err


def test_missing_gh_binary_is_actionable(capsys):
    code = gp.main(["plan", "--gh-path", "definitely-not-a-real-gh-binary-xyz",
                    "--repo", REPO, "--project-number", "1", "--skip-gates"])
    assert code == 3
    err = capsys.readouterr().err
    assert "not found" in err and "gh auth login" in err


def test_api_failure_is_actionable(bootstrapped):
    preview = run_plan(bootstrapped)
    bootstrapped.fail_on = ["fetch_project"]
    with pytest.raises(gp.GhError) as excinfo:
        run_apply(bootstrapped, preview)
    assert excinfo.value.code == 3


def test_gate_failure_stops_the_plan(tmp_path, capsys):
    """A failing source gate must stop the importer before any GitHub call."""
    root = tmp_path / "repo"
    (root / "design" / "trace").mkdir(parents=True)
    (root / "design" / "trace" / "plan_check.py").write_text(
        "print('PLAN check failed: synthetic breakage')\nraise SystemExit(1)\n", encoding="utf-8"
    )
    code = gp.main(["plan", "--repo", REPO, "--root", str(root), "--project-number", "1"])
    assert code == 1
    err = capsys.readouterr().err
    assert "source gate" in err and "synthetic breakage" in err


def test_passing_gates_allow_the_plan_to_reach_source_parsing(tmp_path, capsys):
    root = tmp_path / "repo"
    (root / "design" / "trace").mkdir(parents=True)
    (root / "design" / "trace" / "plan_check.py").write_text(
        "print('PLAN check passed: stub')\n", encoding="utf-8"
    )
    (root / "PLAN-001-x.md").write_text("# nothing\n", encoding="utf-8")
    code = gp.main(["plan", "--repo", REPO, "--root", str(root), "--project-number", "1"])
    assert code == 1  # gates pass; the stub source itself is what fails
    assert "skipped design/trace/trace_check.py" in capsys.readouterr().err


def test_cli_plan_writes_preview_file(bootstrapped, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(gp, "Gh", lambda *a, **k: bootstrapped)  # never touch the real API from tests
    out = tmp_path / "preview.json"
    code = gp.main(["plan", "--repo", REPO, "--project-number", "1",
                    "--root", str(REPO_ROOT), "--skip-gates", "--output", str(out)])
    assert code == 0
    import json
    preview = json.loads(out.read_text(encoding="utf-8"))
    assert preview["counts"]["create"] == 191
    assert "preview written to" in capsys.readouterr().err


def test_smoke_test_subset_via_wp_filter(bootstrapped):
    """Rollout step 4: a three-package smoke covering spike, completed, planned."""
    smoke = ["WP-SPIKE-01", "WP-PRJ-01", "WP-ANA-01"]
    preview = run_plan(bootstrapped, only=smoke)
    assert preview["counts"]["create"] == 3
    run_apply(bootstrapped, preview, only=smoke)
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    assert set(managed) == set(smoke)
    assert len(bootstrapped.items) == 3
    fresh = run_plan(bootstrapped, only=smoke)
    assert fresh["counts"]["unchanged"] == 3 and fresh["operations"] == []


def test_interrupted_initialization_status_is_completed_on_rerun(bootstrapped):
    """A crash between add_item and the initial-status write leaves an item
    with no Status; the next run completes the initialization. An item whose
    status exists is never touched."""
    run_apply(bootstrapped, run_plan(bootstrapped))
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    issue = managed["WP-CORE-01"]
    item = bootstrapped.item_for_issue(issue.number)
    del item["field_values"]["Status"]              # simulate the crash window
    preview = run_plan(bootstrapped)
    ops = [op for op in preview["operations"] if op["wp"] == "WP-CORE-01"]
    assert [op["op"] for op in ops] == ["init_status"]
    assert ops[0]["status"] == "Needs reconciliation"
    run_apply(bootstrapped, preview)
    assert bootstrapped.item_for_issue(issue.number)["field_values"]["Status"] == "Needs reconciliation"
    # A deliberately cleared status gets re-initialized on the next run; a set
    # human status never does.
    preview = run_plan(bootstrapped)
    assert preview["operations"] == []


def test_existing_human_status_is_never_overwritten_after_init_status_fix(bootstrapped):
    run_apply(bootstrapped, run_plan(bootstrapped))
    managed, _ = gp.fetch_managed_issues(bootstrapped, REPO)
    issue = managed["WP-CORE-02"]
    bootstrapped.item_for_issue(issue.number)["field_values"]["Status"] = "Review"
    preview = run_plan(bootstrapped)
    assert [op["op"] for op in preview["operations"] if op["wp"] == "WP-CORE-02"] == []
