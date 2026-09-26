# implements: DSN-CORE-060
"""Tests for ectt.core.fs.

Verifies: TOOL-NFR-070, TOOL-NFR-080, TOOL-PRJ-050, TOOL-PRJ-080, DSN-CORE-060.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest

from ectt.core.fs import (
    DEFAULT_OUTPUT_REL_PATH,
    GITIGNORE_FILENAME,
    MARKER_FILENAME,
    CoreFsError,
    OutputRoot,
    PathConfinementError,
    RootOverlapError,
    SourceMutationError,
    SourceTree,
    UnmarkedOutputRootError,
)


def test_output_root_default_path() -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    assert DEFAULT_OUTPUT_REL_PATH == Path("build/ectt")


def test_overlap_refusal_equal(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    with pytest.raises(RootOverlapError) as exc_info:
        OutputRoot(src_dir, source_roots=[src_dir])

    assert exc_info.value.reason == "root_overlap"
    assert exc_info.value.path == src_dir.resolve()


def test_overlap_refusal_output_contained_in_source(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    out_dir = src_dir / "build" / "ectt"

    with pytest.raises(RootOverlapError) as exc_info:
        OutputRoot(out_dir, source_roots=[src_dir])

    assert exc_info.value.reason == "root_overlap"


def test_overlap_refusal_source_contained_in_output(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "workspace"
    out_dir.mkdir()
    src_dir = out_dir / "src"
    src_dir.mkdir()

    with pytest.raises(RootOverlapError) as exc_info:
        OutputRoot(out_dir, source_roots=[src_dir])

    assert exc_info.value.reason == "root_overlap"


def test_overlap_multiple_source_roots(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    src1 = tmp_path / "src1"
    src2 = tmp_path / "src2"
    src1.mkdir()
    src2.mkdir()
    out_dir = tmp_path / "out"

    # Non-overlapping passes
    root = OutputRoot(out_dir, source_roots=[src1, src2])
    assert root.root == out_dir.resolve()

    # Overlapping with second source root fails
    with pytest.raises(RootOverlapError):
        OutputRoot(src2 / "sub", source_roots=[src1, src2])


def test_first_use_initialization(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-080, DSN-CORE-060"""
    out_dir = tmp_path / "build" / "ectt"
    root = OutputRoot(out_dir, source_roots=[])

    assert not out_dir.exists()

    # On first write, initialization occurs
    root.write_text("artifacts/test.txt", "artifact content")

    assert out_dir.exists()
    marker_path = out_dir / MARKER_FILENAME
    gitignore_path = out_dir / GITIGNORE_FILENAME

    assert marker_path.exists()
    assert "ECTT Output Root Marker" in marker_path.read_text(encoding="utf-8")

    assert gitignore_path.exists()
    assert gitignore_path.read_text(encoding="utf-8") == "*\n"


def test_output_root_requires_keyword_source_roots(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    # Calling without source_roots keyword argument raises TypeError
    with pytest.raises(TypeError):
        OutputRoot(out_dir)  # type: ignore[call-arg]


def test_output_root_refuses_non_empty_unmarked_dir(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "user_dir"
    out_dir.mkdir()
    (out_dir / "important.txt").write_text("user data", encoding="utf-8")

    # Construction refuses taking over an existing non-empty directory lacking marker
    with pytest.raises(UnmarkedOutputRootError) as exc_info:
        OutputRoot(out_dir, source_roots=[])

    assert exc_info.value.reason == "unmarked_output_root"
    assert not (out_dir / GITIGNORE_FILENAME).exists()


def test_output_root_accepts_empty_preexisting_dir(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "empty_dir"
    out_dir.mkdir()

    root = OutputRoot(out_dir, source_roots=[])
    root.write_text("file.txt", "content")

    assert (out_dir / MARKER_FILENAME).exists()
    assert (out_dir / GITIGNORE_FILENAME).exists()
    assert (out_dir / "file.txt").exists()


def test_output_root_recreates_missing_gitignore(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-080, DSN-CORE-060"""
    out_dir = tmp_path / "marked_dir"
    out_dir.mkdir()
    (out_dir / MARKER_FILENAME).write_text("marker", encoding="utf-8")
    (out_dir / "existing.txt").write_text("existing", encoding="utf-8")
    assert not (out_dir / GITIGNORE_FILENAME).exists()

    root = OutputRoot(out_dir, source_roots=[])
    root.write_text("new.txt", "new")

    # .gitignore is recreated on first write
    assert (out_dir / GITIGNORE_FILENAME).exists()
    assert (out_dir / GITIGNORE_FILENAME).read_text(encoding="utf-8") == "*\n"


def test_confinement_parent_escape(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])
    outside_file = tmp_path / "outside.txt"

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text("../outside.txt", "injected")

    assert exc_info.value.reason == "path_escape"
    assert not outside_file.exists()


def test_confinement_nested_parent_escape(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])
    outside_file = tmp_path / "escape.txt"

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text("sub/dir/../../../escape.txt", "injected")

    assert exc_info.value.reason == "path_escape"
    assert not outside_file.exists()


def test_confinement_absolute_path_rejected(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])
    abs_path = (tmp_path / "secret.txt").resolve()

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text(str(abs_path), "forbidden")

    assert exc_info.value.reason == "absolute_path"
    assert not abs_path.exists()


def test_confinement_drive_letter_rejected(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text("C:escape.txt", "forbidden")

    assert exc_info.value.reason in ("drive_letter", "absolute_path")


def test_confinement_junction_escape_on_windows(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    if sys.platform != "win32":
        pytest.skip("Windows-specific junction test")

    import _winapi

    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])
    root.ensure_initialized()

    target_outside = tmp_path / "outside_dir"
    target_outside.mkdir()
    junction_point = out_dir / "junction_link"

    try:
        _winapi.CreateJunction(str(target_outside), str(junction_point))
    except Exception as exc:
        pytest.skip(f"Junction creation not supported in this environment: {exc}")

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text("junction_link/escaped.txt", "payload")

    assert exc_info.value.reason == "path_escape"
    assert not (target_outside / "escaped.txt").exists()


def test_confinement_symlink_escape(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])
    root.ensure_initialized()

    target_outside = tmp_path / "target_outside"
    target_outside.mkdir()
    symlink_point = out_dir / "symlink_dir"

    try:
        symlink_point.symlink_to(target_outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation privilege missing: {exc}")

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text("symlink_dir/escaped.txt", "payload")

    assert exc_info.value.reason == "path_escape"
    assert not (target_outside / "escaped.txt").exists()


def test_null_operation_leaves_bytes_and_mtime_untouched(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-050, TOOL-NFR-060, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])

    content = "deterministic content\n"
    target_file = root.write_text("generated/code.c", content)
    initial_stat = target_file.stat()
    initial_bytes = target_file.read_bytes()

    # Small pause to guarantee mtime resolution step if file were rewritten
    time.sleep(0.05)

    # Write identical content
    second_path = root.write_text("generated/code.c", content)
    assert second_path == target_file

    second_stat = target_file.stat()
    assert target_file.read_bytes() == initial_bytes
    assert second_stat.st_mtime_ns == initial_stat.st_mtime_ns

    # Also verify write_bytes null operation
    time.sleep(0.05)
    root.write_bytes("generated/code.c", initial_bytes)
    third_stat = target_file.stat()
    assert third_stat.st_mtime_ns == initial_stat.st_mtime_ns

    # Now write different content: mtime MUST update
    time.sleep(0.05)
    root.write_text("generated/code.c", "modified content\n")
    modified_stat = target_file.stat()
    assert modified_stat.st_mtime_ns != initial_stat.st_mtime_ns
    assert target_file.read_bytes() == b"modified content\n"


def test_atomic_write_creates_parent_directories(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])

    target = root.write_text("deeply/nested/dir/structure/file.txt", "nested")
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "nested\n"


def test_output_root_write_to_root_itself_refused(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-080, DSN-CORE-060"""
    out_dir = tmp_path / "out"
    root = OutputRoot(out_dir, source_roots=[])

    with pytest.raises(PathConfinementError) as exc_info:
        root.write_text(".", "content")
    assert exc_info.value.reason == "root_target"


def test_source_tree_read_only_access(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    c_file = src_dir / "main.c"
    c_file.write_text("int main(void) { return 0; }\n", encoding="utf-8")

    source_tree = SourceTree(src_dir)
    initial_mtime = c_file.stat().st_mtime_ns
    initial_bytes = c_file.read_bytes()

    # Reading text and bytes
    text = source_tree.read_text("main.c")
    raw = source_tree.read_bytes("main.c")
    assert "int main" in text
    assert raw == initial_bytes

    # Reading via open
    with source_tree.open("main.c", mode="r", encoding="utf-8") as f:
        read_stream = f.read()
    assert read_stream == text

    # Assert mtime and content are unchanged
    assert c_file.stat().st_mtime_ns == initial_mtime
    assert c_file.read_bytes() == initial_bytes


def test_source_tree_mutating_operations_raise_error(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    c_file = src_dir / "driver.c"
    c_file.write_text("void init(void) {}\n", encoding="utf-8")

    source_tree = SourceTree(src_dir)

    mutating_calls = [
        lambda: source_tree.write_text("driver.c", "mutated"),
        lambda: source_tree.write_bytes("driver.c", b"mutated"),
        lambda: source_tree.append_text("driver.c", "more"),
        lambda: source_tree.append_bytes("driver.c", b"more"),
        lambda: source_tree.truncate("driver.c"),
        lambda: source_tree.delete("driver.c"),
        lambda: source_tree.unlink("driver.c"),
        lambda: source_tree.rename("driver.c", "driver_old.c"),
        lambda: source_tree.chmod("driver.c", 0o777),
        lambda: source_tree.mkdir("new_dir"),
        lambda: source_tree.rmdir("driver.c"),
        lambda: source_tree.open("driver.c", mode="w"),
        lambda: source_tree.open("driver.c", mode="a"),
        lambda: source_tree.open("driver.c", mode="r+"),
    ]

    for call in mutating_calls:
        with pytest.raises(SourceMutationError) as exc_info:
            call()
        assert exc_info.value.reason == "source_mutation_disallowed"


def test_source_tree_confinement(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    source_tree = SourceTree(src_dir)

    with pytest.raises(PathConfinementError):
        source_tree.read_text("../outside.txt")

    with pytest.raises(PathConfinementError):
        source_tree.resolve_path(str(tmp_path.resolve() / "outside.txt"))


def test_source_tree_invalid_root(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-070, DSN-CORE-060"""
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(CoreFsError) as exc_info:
        SourceTree(non_existent)
    assert exc_info.value.reason == "source_root_not_found"

    file_root = tmp_path / "file.txt"
    file_root.write_text("not a dir")
    with pytest.raises(CoreFsError) as exc_info:
        SourceTree(file_root)
    assert exc_info.value.reason == "source_root_not_directory"
