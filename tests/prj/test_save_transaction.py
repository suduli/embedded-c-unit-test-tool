# implements: DSN-PRJ-030
"""Project saves are fail-safe: failure or cancellation leaves originals untouched.

Verifies: TOOL-NFR-180, TOOL-PRJ-070.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ectt.core.errors import CancellationToken, CancelledError
from ectt.prj.project import Project


def _project(tmp_path: Path) -> Project:
    return Project.create(tmp_path / "p", name="alpha", source_roots=["src"], output_root="build")


def test_transaction_commits_all_saves_on_success(tmp_path: Path) -> None:
    project = _project(tmp_path)
    with project.transaction():
        project.save_file("a.yaml", {"x": 1})
        project.save_file("sub/b.yaml", {"y": 2})
    assert (project.root / "a.yaml").is_file()
    assert (project.root / "sub" / "b.yaml").is_file()


def test_injected_failure_mid_save_restores_original_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _project(tmp_path)
    project.save_file("a.yaml", {"x": 1})
    before = (project.root / "a.yaml").read_bytes()
    marker_before = project.marker_path.read_bytes()

    real_replace = os.replace
    calls = {"n": 0}

    def flaky(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError("injected failure")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    with pytest.raises(OSError, match="injected"), project.transaction():
        project.save_file("a.yaml", {"x": 99})
        project.save_file("new/c.yaml", {"z": 3})

    assert (project.root / "a.yaml").read_bytes() == before
    assert not (project.root / "new").exists()
    assert project.marker_path.read_bytes() == marker_before
    assert not list(project.root.rglob("*.tmp"))


def test_cancellation_between_saves_leaves_no_partial_file(tmp_path: Path) -> None:
    project = _project(tmp_path)
    project.save_file("a.yaml", {"x": 1})
    before = (project.root / "a.yaml").read_bytes()
    token = CancellationToken()

    with pytest.raises(CancelledError), project.transaction(token):
        project.save_file("a.yaml", {"x": 2})
        token.cancel()
        project.save_file("later.yaml", {"y": 1})

    assert (project.root / "a.yaml").read_bytes() == before
    assert not (project.root / "later.yaml").exists()


def test_already_cancelled_token_refuses_before_any_write(tmp_path: Path) -> None:
    project = _project(tmp_path)
    token = CancellationToken()
    token.cancel()
    with pytest.raises(CancelledError):
        project.save_file("a.yaml", {"x": 1}, token=token)
    assert not (project.root / "a.yaml").exists()
    with pytest.raises(CancelledError), project.transaction(token):
        pass


def test_nested_transaction_joins_the_outer_scope(tmp_path: Path) -> None:
    project = _project(tmp_path)
    with pytest.raises(RuntimeError), project.transaction():
        with project.transaction():
            project.save_file("a.yaml", {"x": 1})
        project.save_file("b.yaml", {"y": 1})
        raise RuntimeError("late failure")
    assert not (project.root / "a.yaml").exists()
    assert not (project.root / "b.yaml").exists()
