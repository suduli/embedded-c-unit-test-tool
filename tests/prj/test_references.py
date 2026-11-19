# implements: DSN-PRJ-050
"""Dangling reference detection (WP-PRJ-04, TASK-011).

Verifies: TOOL-PRJ-090, DSN-PRJ-050.

Cases: none, one, many, and cyclic (a symlink loop, skipped where the platform
will not create symlinks). Also: the report never raises, and output is stable.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from ectt.prj.project import Project
from ectt.prj.references import DanglingReference, find_dangling_references


def _project(tmp_path: Path, source_roots: list[str], output_root: str | None = None) -> Project:
    return Project.create(tmp_path / "proj", source_roots=source_roots, output_root=output_root)


def _make_dirs(project: Project, *names: str) -> None:
    for name in names:
        (project.root / name).mkdir(parents=True, exist_ok=True)


def test_none_when_every_reference_resolves(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — a project whose references all exist reports nothing."""
    project = _project(tmp_path, ["src", "include"], output_root="build/out")
    _make_dirs(project, "src", "include", "build/out")

    assert project.dangling_references() == ()


def test_one_missing_source_root_is_reported_as_required(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — the report names the referencing file, the target, and that it is required."""
    project = _project(tmp_path, ["src", "gone"])
    _make_dirs(project, "src")

    assert project.dangling_references() == (
        DanglingReference(owner="ectt.project", kind="source_root", target="gone", required=True, reason="missing_target"),
    )


def test_missing_output_root_is_reported_as_optional(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — an output root is created by generation, so its absence is optional."""
    project = _project(tmp_path, [], output_root="build/out")

    [ref] = project.dangling_references()
    assert ref.kind == "output_root"
    assert ref.required is False
    assert ref.reason == "missing_target"


def test_many_failures_are_sorted_and_stable(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — several broken references come back in a deterministic order."""
    project = _project(tmp_path, ["zeta", "alpha", "mid"], output_root="out")
    (project.root / "mid").mkdir()
    (project.root / "mid_file.txt").write_text("x", encoding="utf-8")

    first = project.dangling_references()
    second = project.dangling_references()

    assert first == second
    assert [(r.kind, r.target) for r in first] == [
        ("output_root", "out"),
        ("source_root", "alpha"),
        ("source_root", "zeta"),
    ]


def test_source_root_that_is_a_file_is_not_a_directory(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — a reference that resolves to the wrong kind of object is reported."""
    project = _project(tmp_path, ["notes.txt"])
    (project.root / "notes.txt").write_text("x", encoding="utf-8")

    [ref] = project.dangling_references()
    assert ref.reason == "not_a_directory"


@pytest.mark.parametrize("bad", ["../outside", "/abs/path"])
def test_unsafe_stored_path_is_reported_not_followed(tmp_path: Path, bad: str) -> None:
    """verifies: TOOL-PRJ-090, DSN-PRJ-040 — a stored path that is not project-relative is reported, never followed."""
    refs = find_dangling_references(tmp_path, [bad], None)

    assert [r.reason for r in refs] == ["invalid_path"]


def test_symlink_pointing_outside_the_project_is_reported(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — a link that resolves outside the root is refused as outside_project."""
    project = _project(tmp_path, ["escape"])
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    try:
        os.symlink(outside, project.root / "escape", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available on this platform or account")

    [ref] = project.dangling_references()
    assert ref.reason == "outside_project"


def test_cyclic_symlink_terminates_and_is_reported(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — a symlink that points at itself cannot hang the check; it is reported."""
    project = _project(tmp_path, ["loop"])
    try:
        os.symlink(project.root / "loop", project.root / "loop", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not available on this platform or account")

    refs = project.dangling_references()

    assert len(refs) == 1
    assert refs[0].reason in {"unresolvable", "missing_target", "not_a_directory"}


def test_directory_junction_cycle_terminates_and_is_not_dangling(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-090 — a junction that loops back to its parent resolves to a directory, so it is not dangling.

    Windows directory junctions need no elevated rights, so this case runs where
    symlinks do not. It skips on other platforms.
    """
    if os.name != "nt":
        pytest.skip("directory junctions are a Windows mechanism")
    project = _project(tmp_path, ["a/back"])
    (project.root / "a").mkdir()
    proc = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(project.root / "a" / "back"), str(project.root / "a")],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        pytest.skip("could not create a directory junction")

    assert project.dangling_references() == ()


def test_project_with_broken_references_still_opens(tmp_path: Path) -> None:
    """verifies: DSN-PRJ-050 — the check reports; loading the project never fails because of it."""
    project = _project(tmp_path, ["gone"])

    reopened = Project.open(project.root)

    assert [r.target for r in reopened.dangling_references()] == ["gone"]
