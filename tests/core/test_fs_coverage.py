"""Gap-filling behaviour tests for ectt.core.fs (TASK-004).

Covers the error, cleanup and read-side paths that the original fs tests did not
exercise: input type refusal, directory collisions, failed-write cleanup, the
read helpers, the manifest, and the source-tree query helpers.

Verifies: TOOL-NFR-070, TOOL-NFR-080, TOOL-PRJ-050, DSN-CORE-060.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.core import fs as fs_module
from ectt.core.fs import (
    CoreFsError,
    OutputRoot,
    PathConfinementError,
    SourceTree,
)


def test_write_bytes_refuses_text_payload(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    with pytest.raises(TypeError, match="bytes-like"):
        root.write_bytes("a.bin", "not bytes")  # type: ignore[arg-type]
    assert not (tmp_path / "out" / "a.bin").exists()


def test_write_text_refuses_bytes_payload(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    with pytest.raises(TypeError, match="Expected str"):
        root.write_text("a.txt", b"not str")  # type: ignore[arg-type]


def test_write_bytes_accepts_bytearray_and_memoryview(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    root.write_bytes("from_bytearray.bin", bytearray(b"\x00\x01"))
    root.write_bytes("from_memoryview.bin", memoryview(b"\x02\x03"))

    assert root.read_bytes("from_bytearray.bin") == b"\x00\x01"
    assert root.read_bytes("from_memoryview.bin") == b"\x02\x03"


def test_write_bytes_refuses_to_overwrite_directory(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.ensure_initialized()
    (tmp_path / "out" / "occupied").mkdir()

    with pytest.raises(CoreFsError) as exc_info:
        root.write_bytes("occupied", b"payload")
    assert exc_info.value.reason == "is_directory"
    assert (tmp_path / "out" / "occupied").is_dir()


def test_failed_replace_leaves_no_temp_file_and_no_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060

    A crash between temp-file write and rename must not leave a partial target
    or a stray temp file behind.
    """
    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.ensure_initialized()

    def failing_replace(src: object, dst: object) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(fs_module.os, "replace", failing_replace)

    with pytest.raises(OSError, match="simulated rename failure"):
        root.write_bytes("generated/out.bin", b"payload")

    assert not (tmp_path / "out" / "generated" / "out.bin").exists()
    assert list((tmp_path / "out" / "generated").glob("*.tmp")) == []


def test_direct_write_helper_cleans_up_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    target = tmp_path / "out" / "marker.txt"

    def failing_replace(src: object, dst: object) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(fs_module.os, "replace", failing_replace)

    with pytest.raises(OSError, match="simulated rename failure"):
        root._write_file_direct(target, b"marker")

    assert not target.exists()
    assert list((tmp_path / "out").glob("*.tmp")) == []


def test_write_json_is_canonical_and_round_trips(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    payload = {"zeta": [1.5, None], "alpha": {"b": True, "a": "x"}}

    written = root.write_json("cfg/data.json", payload)

    text = written.read_text(encoding="utf-8")
    assert json.loads(text) == payload
    assert text.index('"alpha"') < text.index('"zeta"')
    assert text.endswith("\n")
    assert root.read_text("cfg/data.json") == text


def test_read_and_existence_helpers_on_output_root(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.write_text("notes/readme.txt", "hello")
    (tmp_path / "out" / "notes" / "sub").mkdir()

    assert root.exists("notes/readme.txt")
    assert root.is_file("notes/readme.txt")
    assert not root.is_dir("notes/readme.txt")

    assert root.is_dir("notes/sub")
    assert not root.is_file("notes/sub")

    assert not root.exists("notes/missing.txt")
    assert not root.is_file("notes/missing.txt")
    assert not root.is_dir("notes/missing.txt")

    assert root.read_text("notes/readme.txt") == "hello\n"
    assert root.read_bytes("notes/readme.txt") == b"hello\n"


def test_read_helpers_refuse_escape(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    with pytest.raises(PathConfinementError) as exc_info:
        root.read_bytes("../secret.bin")
    assert exc_info.value.reason == "path_escape"

    with pytest.raises(PathConfinementError):
        root.exists("../secret.bin")


def test_manifest_empty_before_first_write(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    assert not root.root.exists()
    assert root.manifest() == {}


def test_manifest_maps_posix_paths_to_sha256_in_sorted_order(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    import hashlib

    root = OutputRoot(tmp_path / "out", source_roots=[])
    root.write_text("b/second.txt", "two")
    root.write_text("a/first.txt", "one")

    manifest = root.manifest()

    assert list(manifest) == sorted(manifest)
    assert manifest["a/first.txt"] == hashlib.sha256(b"one\n").hexdigest()
    assert manifest["b/second.txt"] == hashlib.sha256(b"two\n").hexdigest()
    assert all("\\" not in key for key in manifest)


def test_source_tree_rejects_drive_relative_path(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    tree = SourceTree(src_dir)

    with pytest.raises(PathConfinementError) as exc_info:
        tree.resolve_path("C:relative.c")
    assert exc_info.value.reason == "drive_letter"


def test_source_tree_resolution_failure_is_confinement_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    tree = SourceTree(src_dir)

    def looping_resolve(self: Path, strict: bool = False) -> Path:
        raise RuntimeError("symlink loop")

    monkeypatch.setattr(Path, "resolve", looping_resolve)

    with pytest.raises(PathConfinementError) as exc_info:
        tree.resolve_path("main.c")
    assert exc_info.value.reason == "resolution_failed"


def test_output_root_resolution_failure_is_confinement_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    root = OutputRoot(tmp_path / "out", source_roots=[])

    def looping_resolve(self: Path, strict: bool = False) -> Path:
        raise RuntimeError("symlink loop")

    monkeypatch.setattr(Path, "resolve", looping_resolve)

    with pytest.raises(PathConfinementError) as exc_info:
        root.resolve_path("generated.bin")
    assert exc_info.value.reason == "resolution_failed"


def test_source_tree_existence_and_stat_helpers(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    (src_dir / "pkg").mkdir(parents=True)
    (src_dir / "pkg" / "unit.c").write_bytes(b"int x;\n")
    tree = SourceTree(src_dir)

    assert tree.exists("pkg/unit.c")
    assert tree.is_file("pkg/unit.c")
    assert not tree.is_dir("pkg/unit.c")
    assert tree.is_dir("pkg")
    assert not tree.exists("pkg/absent.c")
    assert tree.stat("pkg/unit.c").st_size == 7

    names = sorted(entry.name for entry in tree.iterdir("pkg"))
    assert names == ["unit.c"]


def test_source_tree_helpers_refuse_escape(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    tree = SourceTree(src_dir)

    with pytest.raises(PathConfinementError):
        tree.exists("../outside.c")
    with pytest.raises(PathConfinementError):
        tree.is_dir("../outside")
    with pytest.raises(PathConfinementError):
        tree.stat("../outside.c")


def test_source_tree_walk_files_is_sorted_and_relative(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    (src_dir / "deep" / "er").mkdir(parents=True)
    (src_dir / "z.c").write_text("z", encoding="utf-8")
    (src_dir / "a.c").write_text("a", encoding="utf-8")
    (src_dir / "deep" / "er" / "m.c").write_text("m", encoding="utf-8")
    tree = SourceTree(src_dir)

    walked = list(tree.walk_files())

    assert all(not p.is_absolute() for p in walked)
    assert [p.as_posix() for p in walked] == sorted(p.as_posix() for p in walked)
    assert {p.as_posix() for p in walked} == {"a.c", "z.c", "deep/er/m.c"}
