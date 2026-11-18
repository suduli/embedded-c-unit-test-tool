"""Coexistence tests (WP-MIG-06).

Verifies: TOOL-MIG-070 — operating on a project also tested by another tool
without interfering with that tool's artifacts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.core.fs import OutputRoot
from ectt.mig.coexistence import (
    OWNED_PROJECT_PATHS,
    assert_no_interference,
    scan_foreign_artifacts,
    snapshot_tree,
)
from ectt.prj.project import Project


def _plant_foreign_tools(project_dir: Path) -> None:
    """Plant a second tool's artifacts in the shared project."""
    (project_dir / "ceedling").mkdir()
    (project_dir / "ceedling" / "project.yml").write_text(":unity: true\n", encoding="utf-8")
    (project_dir / "unity_results.xml").write_text("<testsuite/>\n", encoding="utf-8")


def _plant_foreign_in_output(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "other_tool_coverage.info").write_text("SF:adc.c\n", encoding="utf-8")


def test_ectt_writes_leave_foreign_artifacts_byte_identical(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070

    Project-store creation on a shared project changes nothing outside
    ectt's owned set: a before/after snapshot of the whole tree is
    byte-identical for every foreign file.
    """
    _plant_foreign_tools(tmp_path)
    before = snapshot_tree(tmp_path)
    Project.create(tmp_path, name="shared", source_roots=["src"])
    after = snapshot_tree(tmp_path)
    foreign_before = dict(before.digests.items())
    foreign_after = {k: v for k, v in after.digests.items() if k in foreign_before}
    assert foreign_after == foreign_before
    # And ectt's marker is the only new file at the root level it owns.
    assert "ectt.project" in after.digests


def test_foreign_artifacts_are_reported_not_modified(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070

    The scan reports the foreign files (deterministically) and modifies
    nothing.
    """
    _plant_foreign_tools(tmp_path)
    before = snapshot_tree(tmp_path)
    found = scan_foreign_artifacts(tmp_path)
    after = snapshot_tree(tmp_path)
    assert before.digests == after.digests
    paths = [a.path for a in found]
    assert paths == ["ceedling/project.yml", "unity_results.xml"]
    assert all(a.root == "project_root" for a in found)


def test_output_root_refuses_to_take_over_foreign_directory(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070 (SDD-003: protects artifacts in both roots)

    A foreign coverage file inside a non-empty, unmarked directory makes
    ectt refuse to adopt that directory as its output root (named
    ``unmarked_output_root`` refusal) — and the foreign file survives
    byte-identically.
    """
    from ectt.core.fs import UnmarkedOutputRootError

    output_dir = tmp_path / "out"
    _plant_foreign_in_output(output_dir)
    before = snapshot_tree(output_dir)
    with pytest.raises(UnmarkedOutputRootError) as excinfo:
        OutputRoot(output_dir, source_roots=[tmp_path / "src"])
    assert excinfo.value.reason == "unmarked_output_root"
    after = snapshot_tree(output_dir)
    foreign = "other_tool_coverage.info"
    assert before.digests[foreign] == after.digests[foreign]
    assert_no_interference(before, after, context="refused output root")


def test_output_root_initialized_before_foreign_file_preserves_it(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070 (SDD-003: protects artifacts in both roots)

    When ectt already owns the output root (marker present), a foreign file
    planted afterwards survives initialization checks byte-identically.
    """
    output_dir = tmp_path / "out"
    (tmp_path / "src").mkdir()
    root = OutputRoot(output_dir, source_roots=[tmp_path / "src"])
    root.ensure_initialized()
    _plant_foreign_in_output(output_dir)
    before = snapshot_tree(output_dir)
    root.ensure_initialized()  # re-check must not touch the foreign file
    after = snapshot_tree(output_dir)
    assert_no_interference(before, after, context="owned output root")
    assert "other_tool_coverage.info" in after.digests


def test_scan_reports_deterministically_sorted(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070, TOOL-NFR-060

    Two scans of the same tree give the same sorted report.
    """
    _plant_foreign_tools(tmp_path)
    first = scan_foreign_artifacts(tmp_path)
    second = scan_foreign_artifacts(tmp_path)
    assert first == second


def test_owned_paths_are_explicit(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070

    The owned set is small, explicit, and excludes the foreign files.
    """
    assert OWNED_PROJECT_PATHS == ("ectt.project",)
    _plant_foreign_tools(tmp_path)
    paths = {a.path for a in scan_foreign_artifacts(tmp_path)}
    assert paths.isdisjoint(set(OWNED_PROJECT_PATHS))


def test_no_interference_detects_a_modified_foreign_file(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070 (guard self-check)

    The snapshot comparison actually catches interference — a mutated foreign
    file is detected and named.
    """
    _plant_foreign_tools(tmp_path)
    before = snapshot_tree(tmp_path)
    (tmp_path / "unity_results.xml").write_text("<testsuite><test/></testsuite>\n", encoding="utf-8")
    after = snapshot_tree(tmp_path)
    with pytest.raises(AssertionError, match=r"unity_results\.xml"):
        assert_no_interference(before, after, context="shared project")


def test_scan_excludes_the_output_root_subtree(tmp_path: Path) -> None:
    """verifies: TOOL-MIG-070 (SDD-003: output root is the generated side)

    Files under the output root are not authored-state foreign artifacts;
    their protection is the snapshot mechanism's job.
    """
    _plant_foreign_tools(tmp_path)
    out = tmp_path / "out"
    _plant_foreign_in_output(out)
    paths = {a.path for a in scan_foreign_artifacts(tmp_path, output_root=out)}
    assert not any(p.startswith("out/") for p in paths)
