"""write_analysis_model runs inside OutputRoot.transaction.

Verifies: TOOL-NFR-180, TOOL-PAR-100.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.ana.persist import write_analysis_model
from ectt.core.errors import CancellationToken, CancelledError
from ectt.core.fs import OutputRoot
from tests.ana.test_persist import _model_doc_1_1


def _root(tmp_path: Path) -> OutputRoot:
    src = tmp_path / "src"
    src.mkdir()
    return OutputRoot(tmp_path / "out", source_roots=[src])


def test_write_succeeds_and_is_byte_stable(tmp_path: Path) -> None:
    root = _root(tmp_path)
    first = write_analysis_model(root, "model.json", _model_doc_1_1()).read_bytes()
    again = write_analysis_model(root, "model.json", _model_doc_1_1()).read_bytes()
    assert first == again


def test_cancelled_token_leaves_original_untouched(tmp_path: Path) -> None:
    root = _root(tmp_path)
    path = write_analysis_model(root, "model.json", _model_doc_1_1())
    original = path.read_bytes()
    changed = _model_doc_1_1()
    changed["extra_note"] = "x"
    token = CancellationToken()
    token.cancel()
    with pytest.raises(CancelledError):
        write_analysis_model(root, "model.json", changed, token=token)
    assert path.read_bytes() == original


def test_failure_in_caller_transaction_rolls_back_the_model_write(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(RuntimeError), root.transaction():
        write_analysis_model(root, "nested/model.json", _model_doc_1_1())
        raise RuntimeError("later step failed")
    assert not (root.root / "nested").exists()


def test_write_inside_caller_transaction_does_not_end_it(tmp_path: Path) -> None:
    root = _root(tmp_path)
    with pytest.raises(RuntimeError), root.transaction():
        write_analysis_model(root, "one.json", _model_doc_1_1())
        write_analysis_model(root, "two.json", _model_doc_1_1())
        raise RuntimeError("boom")
    assert not (root.root / "one.json").exists()
    assert not (root.root / "two.json").exists()
