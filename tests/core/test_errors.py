# implements: DSN-CORE-010
"""Tests for the WP-CORE-02 structured error model (TASK-006).

Covers: the EcttError root and package hierarchy, stable category/code fields,
deterministic JSON serialisation, cooperative cancellation, and the fail-safe
transaction that leaves no partial output in the confined root.

Verifies: TOOL-NFR-090, TOOL-NFR-180.
"""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path

import pytest

from ectt.core import fs as fs_module
from ectt.core.determinism import CoreError, canonical_json
from ectt.core.errors import CancellationToken, CancelledError, EcttError
from ectt.core.fs import CoreFsError, OutputRoot

PACKAGE_ERROR_MODULES = [
    "ectt.prj.errors",
    "ectt.ing.errors",
    "ectt.ana.errors",
]


def _all_error_classes() -> list[type[EcttError]]:
    found: set[type[EcttError]] = {CoreError, CoreFsError, EcttError, CancelledError}
    for module_name in PACKAGE_ERROR_MODULES:
        module = importlib.import_module(module_name)
        for name in module.__all__:
            obj = getattr(module, name)
            if inspect.isclass(obj) and issubclass(obj, BaseException):
                found.add(obj)
    return sorted(found, key=lambda cls: cls.__name__)


def test_every_package_error_derives_from_ectt_error() -> None:
    """verifies: TOOL-NFR-090"""
    classes = _all_error_classes()

    assert len(classes) > 40
    for cls in classes:
        assert issubclass(cls, EcttError), cls.__name__


def test_public_names_and_messages_unchanged_by_root_change() -> None:
    """verifies: TOOL-NFR-090 — str() format is preserved for the CoreError family."""
    err = CoreError("disk problem", reason="io_failed", path=Path("out/a.bin"))
    assert str(err) == f"disk problem [reason=io_failed, path={Path('out/a.bin')}]"

    bare = CoreError("no path", reason="core_error")
    assert str(bare) == "no path [reason=core_error]"


@pytest.mark.parametrize(
    ("factory", "expected_category"),
    [
        (lambda: CoreError("x"), "core"),
        (lambda: CoreFsError("x"), "filesystem"),
        (lambda: CancelledError("x"), "cancelled"),
    ],
)
def test_category_mapping_for_core_bases(factory: object, expected_category: str) -> None:
    """verifies: TOOL-NFR-090"""
    err = factory()  # type: ignore[operator]
    assert isinstance(err, EcttError)
    assert err.category == expected_category


def test_category_is_inherited_by_package_subclasses() -> None:
    """verifies: TOOL-NFR-090"""
    from ectt.ana.errors import LibclangNotFoundError
    from ectt.ing.errors import CompilationDatabaseNotFoundError
    from ectt.prj.errors import YamlSyntaxError

    assert YamlSyntaxError("bad").category == "project"
    assert CompilationDatabaseNotFoundError("missing").category == "ingestion"
    assert LibclangNotFoundError("absent").category == "analysis"


def test_code_is_the_concrete_class_name() -> None:
    """verifies: TOOL-NFR-090"""
    from ectt.prj.errors import DuplicateKeyError

    assert DuplicateKeyError("dup").code == "DuplicateKeyError"
    assert CoreError("x").code == "CoreError"


def test_to_dict_is_json_safe_and_deterministic() -> None:
    """verifies: TOOL-NFR-090 — same error serialises to identical canonical bytes."""
    def build() -> CoreError:
        return CoreError(
            "bad field",
            reason="invalid_field",
            path=Path("project") / "scope.yaml",
            context={"zeta": 1.5, "alpha": {"b": True, "a": None}, "tags": {"y", "x"}},
        )

    first = canonical_json(build().to_dict())
    second = canonical_json(build().to_dict())
    assert first == second

    payload = json.loads(first)
    assert payload["code"] == "CoreError"
    assert payload["category"] == "core"
    assert payload["path"] == "project/scope.yaml"
    assert payload["context"]["tags"] == ["x", "y"]
    assert payload["context"]["zeta"] == "1.5"
    assert list(payload["context"]["alpha"]) == ["a", "b"]


def test_to_dict_without_path_or_context_is_still_valid() -> None:
    """verifies: TOOL-NFR-090"""
    payload = CoreError("plain", reason="core_error").to_dict()

    assert payload["path"] is None
    assert payload["context"] == {}
    json.dumps(payload)


def test_cancellation_token_is_inert_until_cancelled() -> None:
    """verifies: TOOL-NFR-180"""
    token = CancellationToken()
    token.raise_if_cancelled()
    assert token.cancelled is False

    token.cancel()
    assert token.cancelled is True
    with pytest.raises(CancelledError) as exc_info:
        token.raise_if_cancelled()
    assert exc_info.value.reason == "cancelled"
    assert exc_info.value.category == "cancelled"


def test_transaction_rolls_back_created_and_overwritten_files(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180 — a failing operation leaves prior state exactly as it was."""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.write_text("keep/existing.txt", "original")
    before = root.manifest()

    with pytest.raises(RuntimeError, match="boom"), root.transaction():
        root.write_text("keep/existing.txt", "overwritten")
        root.write_text("new/dir/created.txt", "new")
        raise RuntimeError("boom")

    assert root.manifest() == before
    assert not (tmp_path / "out" / "new").exists()


def test_cancellation_mid_operation_leaves_no_partial_output(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180 — cancellation between writes removes this operation's output."""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.write_text("stable/prior.txt", "prior")
    before = root.manifest()
    token = CancellationToken()

    with pytest.raises(CancelledError), root.transaction(token):
        root.write_text("run/part1.txt", "one")
        root.write_text("run/part2.txt", "two")
        token.cancel()
        root.write_text("run/part3.txt", "three")

    assert root.manifest() == before
    assert not (tmp_path / "out" / "run").exists()


def test_transaction_refuses_to_start_when_already_cancelled(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180"""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    token = CancellationToken()
    token.cancel()

    with pytest.raises(CancelledError), root.transaction(token):
        root.write_text("never.txt", "x")

    assert not (tmp_path / "out" / "never.txt").exists()


def test_successful_transaction_keeps_writes(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    with root.transaction():
        root.write_text("done/result.txt", "ok")

    assert root.read_text("done/result.txt") == "ok\n"


def test_rollback_failure_is_attached_as_note_not_swallowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-180 — rollback problems are reported with the original error."""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.write_text("fixed.txt", "before")

    def failing_restore(self: OutputRoot, file_path: Path, data: bytes) -> None:
        raise OSError("disk went away")

    monkeypatch.setattr(OutputRoot, "_write_file_direct", failing_restore)

    with pytest.raises(RuntimeError) as exc_info, root.transaction():
        root.write_text("fixed.txt", "during")
        raise RuntimeError("original failure")

    assert str(exc_info.value) == "original failure"
    notes = getattr(exc_info.value, "__notes__", [])
    assert any("could not restore" in note for note in notes)


def test_transaction_keeps_root_marker_on_rollback(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180 — root initialisation is setup, not output, and survives rollback."""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    token = CancellationToken()
    token.cancel()

    with pytest.raises(CancelledError), root.transaction(token):
        pass

    assert (tmp_path / "out" / fs_module.MARKER_FILENAME).exists()
