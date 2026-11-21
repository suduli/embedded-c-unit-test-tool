# implements: TOOL-PRJ-060
"""Project.save layouts: single-file manifest default and sharded store (B6/WP-PRJ-02).

The layout is chosen by an explicit argument only; there is no automatic
switch. Both layouts round-trip; an unchanged save is byte-stable; an
interrupted save leaves the original.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ectt.core.errors import CancellationToken, CancelledError
from ectt.prj.project import PROJECT_LAYOUTS, Project
from ectt.prj.shards import ShardStore


def _project(tmp_path: Path) -> Project:
    return Project.create(tmp_path / "p", name="alpha", source_roots=["src"], output_root="build")


def _with_settings(project: Project) -> Project:
    """A project document with an extra concern so several shards are written."""
    # plain-text values: the adapter's YAML discipline round-trips strings exactly
    project.document.data["settings"] = {"timeout": "30", "strict": "true"}
    project.document.data["suites"] = ["smoke", "full"]
    return project


# --- both layouts round-trip ------------------------------------------------------


def test_single_layout_round_trips_and_stays_the_default(tmp_path: Path) -> None:
    """verifies: B6 — save() with no argument stays the single-file manifest."""
    project = _project(tmp_path)
    path = project.save()
    assert path == project.root / "ectt.project"
    assert not (project.root / "shards").exists()  # no automatic switch
    reloaded = Project(project.root, project.document)
    # the adapter normalises empty mappings away on the round trip
    expected = {k: v for k, v in project.document.data.items() if v != {}}
    assert reloaded.read_file("ectt.project").data == expected


def test_sharded_layout_round_trips(tmp_path: Path) -> None:
    project = _with_settings(_project(tmp_path))
    before = dict(project.document.data)
    project.save(layout="sharded")

    # every top-level concern is its own shard
    store = ShardStore(project.root)
    for key in before:
        assert store.read_shard(key) is not None, key
    # the manifest is still present and unchanged in meaning
    assert (project.root / "ectt.project").is_file()

    reloaded = Project(project.root, project.document)
    assert reloaded.read_shards() == before
    assert reloaded.read_file("ectt.project").data == before


def test_unknown_layout_is_refused(tmp_path: Path) -> None:
    project = _project(tmp_path)
    with pytest.raises(Exception) as exc_info:
        project.save(layout="auto")  # type: ignore[arg-type]
    assert getattr(exc_info.value, "reason", "") == "unknown_layout"
    assert PROJECT_LAYOUTS == ("single", "sharded")


# --- byte stability ----------------------------------------------------------------


def test_unchanged_sharded_save_is_byte_stable(tmp_path: Path) -> None:
    """verifies: B6 — an unchanged save rewrites nothing (bytes and mtimes)."""
    project = _with_settings(_project(tmp_path))
    project.save(layout="sharded")

    shard_files = sorted((project.root / "shards").glob("*.yaml"))
    assert len(shard_files) == 6  # schema_version, name, source_roots, output_root, settings, suites
    before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in shard_files}
    marker_before = (project.root / "ectt.project").read_bytes()

    project.save(layout="sharded")

    after = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in shard_files}
    assert after == before  # byte-identical AND mtime preserved: not rewritten
    assert (project.root / "ectt.project").read_bytes() == marker_before


# --- interrupted save leaves the original -------------------------------------------


def test_injected_failure_during_sharded_save_leaves_original(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project = _project(tmp_path)
    project.save(layout="sharded")
    original_shards = {
        p.name: p.read_bytes() for p in sorted((project.root / "shards").glob("*.yaml"))
    }
    original_marker = (project.root / "ectt.project").read_bytes()

    # mutate the document, then fail the manifest write (the commit point):
    # only the changed shard ("name") and the manifest reach os.replace
    project.document.data["name"] = "renamed"
    real_replace = os.replace
    calls = {"n": 0}

    def flaky(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        calls["n"] += 1
        if calls["n"] == 2:  # first replace is the changed shard, second is the manifest
            raise OSError("injected failure")
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", flaky)
    with pytest.raises(OSError, match="injected"):
        project.save(layout="sharded")

    assert (project.root / "ectt.project").read_bytes() == original_marker
    assert {
        p.name: p.read_bytes() for p in sorted((project.root / "shards").glob("*.yaml"))
    } == original_shards
    assert not list(project.root.rglob("*.tmp"))


def test_cancellation_before_sharded_save_writes_nothing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    project.save()  # single layout
    original = (project.root / "ectt.project").read_bytes()
    token = CancellationToken()
    token.cancel()
    with pytest.raises(CancelledError):
        project.save(layout="sharded", token=token)
    assert (project.root / "ectt.project").read_bytes() == original
    assert not (project.root / "shards").exists()
