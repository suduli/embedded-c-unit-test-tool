"""Sharded storage tests (WP-PRJ-02).

Verifies: TOOL-PRJ-060 (localized conflicts, diff stability).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.prj.errors import InvalidRelativePathError
from ectt.prj.shards import ShardStore


def test_shards_are_independent_plain_text_files(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-060

    Each concern is its own plain-text file: the store creates exactly one
    file per shard, no shared whole-project blob.
    """
    store = ShardStore(tmp_path)
    assert store.write_shard("settings", "key: value\n")
    assert store.write_shard("scopes", "- adc\n")
    shard_files = sorted(p.name for p in (tmp_path / "shards").iterdir())
    assert shard_files == ["scopes.yaml", "settings.yaml"]
    assert (tmp_path / "shards" / "settings.yaml").read_text(encoding="utf-8") == "key: value\n"


def test_editing_one_shard_leaves_other_shards_untouched(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-060

    The localized-conflict property: rewriting one shard leaves the other
    shard's file byte-identical — a concurrent editor of the other concern
    sees no conflict.
    """
    store = ShardStore(tmp_path)
    store.write_shard("settings", "key: value\n")
    store.write_shard("scopes", "- adc\n")
    before = (tmp_path / "shards" / "scopes.yaml").read_bytes()
    store.write_shard("settings", "key: changed\n")
    after = (tmp_path / "shards" / "scopes.yaml").read_bytes()
    assert before == after


def test_unchanged_shard_rewrite_is_byte_identical(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-060 (diff stability)

    Writing the same content again returns False and leaves the file
    byte-identical — no diff churn from meaning-preserving operations
    (TOOL-PRJ-050 alignment).
    """
    store = ShardStore(tmp_path)
    store.write_shard("settings", "key: value\n")
    first = (tmp_path / "shards" / "settings.yaml").read_bytes()
    assert store.write_shard("settings", "key: value\n") is False
    second = (tmp_path / "shards" / "settings.yaml").read_bytes()
    assert first == second


def test_changed_shard_rewrites_atomically(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-060

    A meaning change rewrites the shard (True) and no temp file survives.
    """
    store = ShardStore(tmp_path)
    assert store.write_shard("settings", "key: v1\n") is True
    assert store.write_shard("settings", "key: v2\n") is True
    assert (tmp_path / "shards" / "settings.yaml").read_text(encoding="utf-8") == "key: v2\n"
    leftovers = [p.name for p in (tmp_path / "shards").iterdir() if p.suffix == ".tmp"]
    assert leftovers == []


def test_missing_shard_reads_none(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-060

    An absent shard reads as None, never as empty content (absence stays
    distinguishable from emptiness).
    """
    assert ShardStore(tmp_path).read_shard("settings") is None


@pytest.mark.parametrize("bad", ["../escape", "/absolute", "a/b", "", ".hidden", "sp ace"])
def test_invalid_shard_names_are_refused(tmp_path: Path, bad: str) -> None:
    """verifies: TOOL-PRJ-060, TOOL-PRJ-070 alignment

    Shard names cannot steer the path outside the shard directory.
    """
    store = ShardStore(tmp_path)
    with pytest.raises(InvalidRelativePathError):
        store.shard_path(bad)
