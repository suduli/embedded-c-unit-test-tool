# implements: TOOL-NFR-180
"""Re-entrant OutputRoot.transaction scopes (WP-CORE-02 follow-up).

A nested ``transaction`` joins the outermost active scope instead of replacing
it: writes are durable only when the outermost scope exits without error, a
failure unwinding past the outermost scope rolls back the whole stack, and any
active token (outer or nested) refuses writes while cancelled.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.core.errors import CancellationToken, CancelledError
from ectt.core.fs import OutputRoot


def _root(tmp_path: Path) -> OutputRoot:
    src = tmp_path / "src"
    src.mkdir()
    return OutputRoot(tmp_path / "out", source_roots=[src])


def test_nested_scope_joins_and_outer_commit_makes_writes_durable(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with root.transaction():
        root.write_text("outer/a.txt", "outer")
        with root.transaction():
            root.write_text("nested/b.txt", "nested")
            root.write_text("outer/a.txt", "overwritten")
        # nested scope exited without error: nothing is durable yet, but
        # nothing was lost either — the outer scope still owns the journal
        assert (root.root / "nested" / "b.txt").exists()
    assert (root.root / "nested" / "b.txt").read_text() == "nested\n"
    assert (root.root / "outer" / "a.txt").read_text() == "overwritten\n"


def test_nested_failure_rolls_back_everything(tmp_path: Path) -> None:
    root = _root(tmp_path)
    root.write_text("keep/existing.txt", "original")
    before = root.manifest()
    with pytest.raises(RuntimeError, match="inner boom"), root.transaction():
        root.write_text("keep/existing.txt", "overwritten-by-outer")
        with root.transaction():
            root.write_text("keep/existing.txt", "overwritten-by-nested")
            root.write_text("nested/created.txt", "new")
            raise RuntimeError("inner boom")
    assert root.manifest() == before
    assert not (root.root / "nested").exists()


def test_outer_failure_after_nested_commit_rolls_back_nested_writes(tmp_path: Path) -> None:
    root = _root(tmp_path)
    root.write_text("stable/prior.txt", "prior")
    before = root.manifest()
    with pytest.raises(RuntimeError, match="outer boom"), root.transaction():
        with root.transaction():
            root.write_text("nested/done.txt", "nested")
        root.write_text("outer/done.txt", "outer")
        raise RuntimeError("outer boom")
    assert root.manifest() == before
    assert not (root.root / "nested").exists()
    assert not (root.root / "outer").exists()


def test_caught_nested_failure_keeps_the_outer_scope_usable(tmp_path: Path) -> None:
    """A nested failure caught inside the outer body does not end the outer
    scope: the nested scope joined it, so the outer commit decides durability."""
    root = _root(tmp_path)
    with root.transaction():
        root.write_text("outer/before.txt", "before")
        with pytest.raises(RuntimeError, match="inner boom"), root.transaction():
            root.write_text("inner/attempt.txt", "attempt")
            raise RuntimeError("inner boom")
        root.write_text("outer/after.txt", "after")
    assert (root.root / "outer" / "before.txt").exists()
    assert (root.root / "outer" / "after.txt").exists()
    assert (root.root / "inner" / "attempt.txt").exists()


def test_cancellation_inside_nested_scope_rolls_back_everything(tmp_path: Path) -> None:
    root = _root(tmp_path)
    root.write_text("stable/prior.txt", "prior")
    before = root.manifest()
    token = CancellationToken()
    with pytest.raises(CancelledError), root.transaction():
        root.write_text("outer/part1.txt", "one")
        with root.transaction(token):
            root.write_text("nested/part2.txt", "two")
            token.cancel()
            root.write_text("nested/part3.txt", "three")
    assert root.manifest() == before
    assert not (root.root / "nested").exists()
    assert not (root.root / "outer").exists()


def test_cancelled_outer_token_refuses_writes_inside_nested_scope(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outer_token = CancellationToken()
    with pytest.raises(CancelledError), root.transaction(outer_token):
        root.write_text("outer/a.txt", "one")
        with root.transaction():
            outer_token.cancel()
            root.write_text("nested/b.txt", "two")
    assert not (root.root / "outer").exists()
    assert not (root.root / "nested").exists()


def test_cancelled_nested_token_refuses_entry(tmp_path: Path) -> None:
    root = _root(tmp_path)
    token = CancellationToken()
    token.cancel()
    with root.transaction():
        root.write_text("outer/a.txt", "one")
        with pytest.raises(CancelledError), root.transaction(token):
            root.write_text("nested/b.txt", "two")
        # the outer scope survived the refused nested entry
        root.write_text("outer/c.txt", "three")
    assert (root.root / "outer" / "a.txt").exists()
    assert (root.root / "outer" / "c.txt").exists()
    assert not (root.root / "nested").exists()


def test_three_levels_deep_join_one_journal(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with root.transaction():
        root.write_text("level1/a.txt", "1")
        with root.transaction():
            root.write_text("level2/b.txt", "2")
            with root.transaction():
                root.write_text("level3/c.txt", "3")
        assert (root.root / "level3" / "c.txt").exists()
    assert (root.root / "level1" / "a.txt").exists()
    assert (root.root / "level2" / "b.txt").exists()
    assert (root.root / "level3" / "c.txt").exists()


def test_write_analysis_model_inside_transaction_no_longer_reads_private_state(
    tmp_path: Path,
) -> None:
    """The ana writer opens a plain nested scope; no caller-visible behavior change."""
    from ectt.ana.persist import write_analysis_model

    root = _root(tmp_path)
    doc = {
        "schema_version": "1.0",
        "provenance": {"tool_version": "t", "front_end": "fe", "generated_at": "...", "inputs": []},
        "units": [{"path": "a.c", "status": "parsed", "diagnostics": [], "functions": [], "cfg": None}],
        "types": {},
        "capabilities": {"cfg": False},
    }
    with root.transaction():
        write_analysis_model(root, "nested/model.json", doc)
    assert (root.root / "nested" / "model.json").exists()

    from pathlib import Path as _Path

    import ectt.ana.persist as persist_module

    assert "_journal" not in _Path(persist_module.__file__).read_text(encoding="utf-8")
