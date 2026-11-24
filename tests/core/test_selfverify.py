# implements: TOOL-NFR-100
"""Self-verification of the tool's own source (WP-CORE-08).

The tests build their own temp trees (no manifest generated from this
repository is committed as a fixed file): clean, changed, missing, unexpected,
and a tampered manifest refused by name.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.core import SelfVerificationError, verify_tree, write_manifest


def _tree(tmp_path: Path) -> Path:
    """A small package tree: nested modules, a data file, a pycache to ignore."""
    (tmp_path / "ectt" / "sub").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ectt" / "__init__.py").write_text("VERSION = '1'\n", encoding="utf-8")
    (tmp_path / "ectt" / "core.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (tmp_path / "ectt" / "sub" / "leaf.py").write_text("X = 2\n", encoding="utf-8")
    (tmp_path / "ectt" / "data.txt").write_text("payload\n", encoding="utf-8")
    (tmp_path / "ectt" / "__pycache__").mkdir(exist_ok=True)
    (tmp_path / "ectt" / "__pycache__" / "core.cpython-313.pyc").write_bytes(b"junk")
    (tmp_path / "ectt" / "stray.pyc").write_bytes(b"junk")
    return tmp_path


def test_a_clean_tree_verifies(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — the tree it was written from verifies clean."""
    tree = _tree(tmp_path / "clean")
    manifest = write_manifest(tree)
    verdict = verify_tree(tree, manifest)
    assert verdict.ok is True
    assert (verdict.changed, verdict.missing, verdict.unexpected) == ((), (), ())
    assert json.loads(manifest)["manifest_version"] == "1"


def test_a_changed_file_is_named(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — an edited file is reported as changed, by its
    project-relative path."""
    tree = _tree(tmp_path / "changed")
    manifest = write_manifest(tree)
    (tree / "ectt" / "core.py").write_text("def f():\n    return 2\n", encoding="utf-8")
    verdict = verify_tree(tree, manifest)
    assert verdict.ok is False
    assert verdict.changed == ("ectt/core.py",)
    assert verdict.missing == () and verdict.unexpected == ()


def test_a_missing_file_is_named(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — a deleted file is reported as missing."""
    tree = _tree(tmp_path / "missing")
    manifest = write_manifest(tree)
    (tree / "ectt" / "data.txt").unlink()
    verdict = verify_tree(tree, manifest)
    assert verdict.missing == ("ectt/data.txt",)
    assert verdict.ok is False


def test_an_unexpected_file_is_named(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — a planted extra file is reported as
    unexpected."""
    tree = _tree(tmp_path / "extra")
    manifest = write_manifest(tree)
    (tree / "ectt" / "planted.py").write_text("import os  # planted\n", encoding="utf-8")
    verdict = verify_tree(tree, manifest)
    assert verdict.unexpected == ("ectt/planted.py",)
    assert verdict.ok is False


def test_pycache_is_ignored(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-1 — __pycache__ directories and .pyc files never
    enter the manifest, and planting them does not break verification."""
    manifest = write_manifest(_tree(tmp_path / "ignored"))
    document = json.loads(manifest)
    assert not any("__pycache__" in path or path.endswith(".pyc") for path in document["files"])
    # Planting MORE pycache noise after the manifest stays clean (a fresh tree
    # with the same content, plus an extra ignored file).
    tree = _tree(tmp_path / "ignored2")
    _tree(tree)
    (tree / "ectt" / "__pycache__" / "more.pyc").write_bytes(b"junk")
    assert verify_tree(tree, manifest) == verify_tree(tree, write_manifest(tree))
    assert verify_tree(tree, manifest).ok is True


def test_a_tampered_manifest_is_refused(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-3 — a malformed digest, an unknown version or a
    broken document is refused by name, never accepted as clean."""
    tree = _tree(tmp_path / "tampered")
    manifest = write_manifest(tree)
    document = json.loads(manifest)
    document["files"]["ectt/core.py"] = "z" * 64  # not hex
    with pytest.raises(SelfVerificationError) as tampered:
        verify_tree(tree, json.dumps(document))
    assert tampered.value.reason == "manifest_tampered"

    document = json.loads(manifest)
    document["manifest_version"] = "9"
    with pytest.raises(SelfVerificationError) as version:
        verify_tree(tree, json.dumps(document))
    assert version.value.reason == "manifest_version"

    with pytest.raises(SelfVerificationError) as malformed:
        verify_tree(tree, "{not json")
    assert malformed.value.reason == "manifest_malformed"


def test_the_manifest_is_deterministic_and_round_trips(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-1 — same tree, byte-identical manifest; the
    digest map is sorted and every digest is 64 hex."""
    first = write_manifest(_tree(tmp_path / "a"))
    second = write_manifest(_tree(tmp_path / "b"))
    assert first == second
    files = json.loads(first)["files"]
    assert list(files.keys()) == sorted(files.keys())
    assert all(len(digest) == 64 for digest in files.values())


def test_nested_directories_are_covered(tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-1 — files at every depth are digested under
    their POSIX relative path."""
    manifest = write_manifest(_tree(tmp_path / "nested"))
    files = json.loads(manifest)["files"]
    assert "ectt/sub/leaf.py" in files
    assert "ectt/__init__.py" in files
    assert "\\" not in manifest  # project-relative POSIX paths only
