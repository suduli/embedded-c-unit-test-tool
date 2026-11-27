# implements: TOOL-NFR-100
"""Seeded property-style tests for ectt.core self-verification (A9, tests only;
no src/ edits).

Property: **manifest round trip** — for a random tree, the manifest written
from it verifies that tree clean, byte-stably; and for a random mutation of the
tree (edit, delete, plant), the verdict names exactly the mutated files against
an independently computed oracle. Fixed seeds; no wall clock.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from ectt.core import verify_tree, write_manifest

SEEDS = [0, 1, 7, 42, 1337]


def _random_tree(rng: random.Random, root: Path) -> dict[str, bytes]:
    """A random package tree; returns the relative POSIX path -> content map."""
    contents: dict[str, bytes] = {}
    for index in range(rng.randint(2, 8)):
        depth = rng.choice(["", "sub/", "sub/deeper/"])
        name = f"{depth}mod_{index}.py"
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        content = f"# module {index}\nVALUE = {rng.randint(0, 999)}\n".encode()
        path.write_bytes(content)
        contents[name] = content
    if rng.random() < 0.5:  # pycache noise that must never enter the manifest
        (root / "__pycache__").mkdir(exist_ok=True)
        (root / "__pycache__" / f"m{index}.pyc").write_bytes(b"junk")
    return contents


@pytest.mark.parametrize("seed", SEEDS)
def test_the_manifest_round_trips_clean(seed: int, tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — the tree the manifest was written from
    verifies clean, byte-stably, with the exact expected file set."""
    rng = random.Random(seed)
    tree = tmp_path / "tree"
    contents = _random_tree(rng, tree)
    manifest = write_manifest(tree)
    assert manifest == write_manifest(tree)  # byte-stable
    verdict = verify_tree(tree, manifest)
    assert verdict.ok is True
    manifest_files = __import__("json").loads(manifest)["files"]
    assert set(manifest_files.keys()) == set(contents)


@pytest.mark.parametrize("seed", SEEDS)
def test_random_mutations_are_named_exactly(seed: int, tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — for a random mutation (edit, delete, plant),
    the verdict matches an independently computed oracle, file for file."""
    rng = random.Random(seed)
    tree = tmp_path / "tree"
    contents = _random_tree(rng, tree)
    manifest = write_manifest(tree)

    names = sorted(contents)
    if len(names) < 2:
        pytest.skip("the draw produced a single-file tree")
    victim_edit, victim_delete = rng.sample(names, k=2)
    planted = f"planted_{seed}_{rng.randint(0, 99)}.py"

    (tree / victim_edit).write_bytes(b"EDITED\n")
    (tree / victim_delete).unlink()
    (tree / planted).write_bytes(b"PLANTED\n")

    verdict = verify_tree(tree, manifest)
    oracle_changed = {victim_edit}
    oracle_missing = {victim_delete}
    oracle_unexpected = {planted}
    assert set(verdict.missing) == oracle_missing
    assert set(verdict.unexpected) == oracle_unexpected
    assert oracle_changed <= set(verdict.changed)  # the edit is named
    assert verdict.ok is False
    # And the lists are sorted.
    assert verdict.changed == tuple(sorted(verdict.changed))
    assert verdict.missing == tuple(sorted(verdict.missing))
    assert verdict.unexpected == tuple(sorted(verdict.unexpected))


@pytest.mark.parametrize("seed", SEEDS)
def test_changed_excludes_missing_files(seed: int, tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-2 — a deleted file is missing, NOT changed: the
    two lists partition the differences without overlap."""
    rng = random.Random(seed)
    tree = tmp_path / "tree"  # type: ignore[operator]
    contents = _random_tree(rng, tree)
    manifest = write_manifest(tree)
    victim_edit, victim_delete = rng.sample(sorted(contents), k=2)
    (tree / victim_edit).write_bytes(b"EDITED\n")
    (tree / victim_delete).unlink()
    verdict = verify_tree(tree, manifest)
    assert set(verdict.changed) == {victim_edit}
    assert set(verdict.missing) == {victim_delete}
    assert not (set(verdict.changed) & set(verdict.missing))


@pytest.mark.parametrize("seed", SEEDS)
def test_pycache_noise_never_breaks_the_round_trip(seed: int, tmp_path: Path) -> None:
    """verifies: WP-CORE-08 AC-1 — pycache files planted before or after the
    manifest are invisible to the verdict."""
    rng = random.Random(seed)
    tree = tmp_path / "tree"
    _random_tree(rng, tree)
    manifest = write_manifest(tree)
    (tree / "__pycache__").mkdir(exist_ok=True)
    (tree / "__pycache__" / f"late_{seed}.pyc").write_bytes(b"junk")
    (tree / f"late_{seed}.pyc").write_bytes(b"junk")
    verdict = verify_tree(tree, manifest)
    assert verdict.ok is True
    assert verdict.unexpected == ()
