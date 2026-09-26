# implements: DSN-CORE-060
"""Filesystem isolation, output confinement, and source immutability.

Enforces the two-tree architectural boundary:
- All generated writes are strictly confined to a designated OutputRoot.
- User source trees are protected behind a read-only SourceTree guard.
- OutputRoot rejects paths that escape or overlap with declared source roots.
- Writes are atomic (temporary file in target directory + os.replace) and byte-deterministic.
- Writing identical content leaves existing files and mtimes untouched (null operations are no-ops).
- On first use, OutputRoot installs an ectt marker file and a .gitignore ('*') to exclude the tree
  from version control by location.

Satisfies: TOOL-NFR-070, TOOL-NFR-080, TOOL-PRJ-050, TOOL-PRJ-080.
"""

from __future__ import annotations

import hashlib
import io
import os
import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

from ectt.core.determinism import CoreError, canonical_json, canonical_text

__all__ = [
    "DEFAULT_OUTPUT_REL_PATH",
    "MARKER_FILENAME",
    "GITIGNORE_FILENAME",
    "CoreError",
    "CoreFsError",
    "RootOverlapError",
    "PathConfinementError",
    "SourceMutationError",
    "UnmarkedOutputRootError",
    "OutputRoot",
    "SourceTree",
]

DEFAULT_OUTPUT_REL_PATH = Path("build/ectt")
MARKER_FILENAME = ".ectt-marker"
GITIGNORE_FILENAME = ".gitignore"


class CoreFsError(CoreError):
    """Base exception for filesystem operations."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "fs_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class RootOverlapError(CoreFsError):
    """Raised when an OutputRoot overlaps with (equals, contains, or is contained by) a source root."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "root_overlap",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class PathConfinementError(CoreFsError):
    """Raised when a relative path attempts to escape the root boundary."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "path_escape",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class SourceMutationError(CoreFsError):
    """Raised when a write, modify, delete, or chmod operation is attempted on a SourceTree."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "source_mutation_disallowed",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnmarkedOutputRootError(CoreFsError):
    """Raised when an existing non-empty directory lacks the ectt marker file."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "unmarked_output_root",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class OutputRoot:
    """Designated output directory root enforcing path confinement and atomic writes.

    All generated tool files must be written through an OutputRoot instance.
    """

    def __init__(
        self,
        root: Path | str,
        *,
        source_roots: Sequence[Path | str],
    ) -> None:
        self.root = Path(root).resolve()
        self._source_roots: list[Path] = [Path(s).resolve() for s in source_roots]
        self._check_source_overlap()
        self._check_unmarked_directory()
        self._initialized = False

    def _check_source_overlap(self) -> None:
        """Refuse construction if output root equals, contains, or is contained by any source root."""
        for src in self._source_roots:
            if self.root == src:
                raise RootOverlapError(
                    f"Output root '{self.root}' cannot equal source root '{src}'.",
                    reason="root_overlap",
                    path=self.root,
                )
            if self.root.is_relative_to(src):
                raise RootOverlapError(
                    f"Output root '{self.root}' cannot be contained inside source root '{src}'.",
                    reason="root_overlap",
                    path=self.root,
                )
            if src.is_relative_to(self.root):
                raise RootOverlapError(
                    f"Output root '{self.root}' cannot contain source root '{src}'.",
                    reason="root_overlap",
                    path=self.root,
                )

    def _check_unmarked_directory(self) -> None:
        """Refuse construction or use if an existing non-empty directory lacks the ectt marker."""
        if self.root.exists() and any(self.root.iterdir()):
            marker_file = self.root / MARKER_FILENAME
            if not marker_file.exists():
                raise UnmarkedOutputRootError(
                    f"Output root '{self.root}' is an existing non-empty directory without '{MARKER_FILENAME}'. "
                    f"Refusing to take over an existing directory.",
                    reason="unmarked_output_root",
                    path=self.root,
                )

    def ensure_initialized(self) -> None:
        """Initialize the output root with marker file and .gitignore on first write."""
        if self._initialized and self.root.exists():
            return

        self._check_unmarked_directory()
        self.root.mkdir(parents=True, exist_ok=True)

        marker_file = self.root / MARKER_FILENAME
        if not marker_file.exists():
            content = (
                "# ECTT Output Root Marker\n"
                "# This directory contains generated artifacts produced by ECTT.\n"
                "# It is separable from user source code and safely regenerable.\n"
            )
            self._write_file_direct(marker_file, content.encode("utf-8"))

        gitignore_file = self.root / GITIGNORE_FILENAME
        if not gitignore_file.exists():
            self._write_file_direct(gitignore_file, b"*\n")

        self._initialized = True

    def _write_file_direct(self, file_path: Path, data: bytes) -> None:
        """Internal direct write helper for root initialization."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path_str = tempfile.mkstemp(
            prefix=f".{file_path.name}.",
            suffix=".tmp",
            dir=file_path.parent,
        )
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, file_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

    def resolve_path(self, rel_path: Path | str) -> Path:
        """Validate and resolve a relative path, rejecting any escape beyond the output root.

        Rejects absolute paths, drive letters, '..' escapes, and symlink/junction escapes.
        """
        p = Path(rel_path)
        if p.is_absolute():
            raise PathConfinementError(
                f"Absolute path '{rel_path}' is forbidden; paths must be relative to output root.",
                reason="absolute_path",
                path=p,
            )
        if bool(p.drive):
            raise PathConfinementError(
                f"Path with drive letter '{rel_path}' is forbidden.",
                reason="drive_letter",
                path=p,
            )

        candidate = self.root / p
        try:
            resolved = candidate.resolve()
        except Exception as exc:
            raise PathConfinementError(
                f"Failed to resolve path '{rel_path}': {exc}",
                reason="resolution_failed",
                path=p,
            ) from exc

        if not resolved.is_relative_to(self.root):
            raise PathConfinementError(
                f"Path '{rel_path}' escapes output root '{self.root}'.",
                reason="path_escape",
                path=p,
            )

        if resolved == self.root:
            raise PathConfinementError(
                f"Cannot target the root directory itself as a file: '{rel_path}'",
                reason="root_target",
                path=p,
            )

        return resolved

    def write_bytes(self, rel_path: Path | str, data: bytes) -> Path:
        """Atomically write binary data to a file inside the output root.

        - If the file exists with identical bytes, it is left untouched (same mtime).
        - Writes are atomic via temporary file in the same directory + os.replace.
        """
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f"Expected bytes-like object, got {type(data).__name__}")

        data_bytes = bytes(data)
        self.ensure_initialized()
        target_path = self.resolve_path(rel_path)

        if target_path.exists():
            if target_path.is_dir():
                raise CoreFsError(
                    f"Cannot write file over directory: '{target_path}'",
                    reason="is_directory",
                    path=target_path,
                )
            try:
                with target_path.open("rb") as f:
                    if f.read() == data_bytes:
                        # Null-operation: byte-identical, preserve mtime and file identity
                        return target_path
            except OSError:
                pass

        parent_dir = target_path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path_str = tempfile.mkstemp(
            prefix=f".{target_path.name}.",
            suffix=".tmp",
            dir=parent_dir,
        )
        temp_path = Path(temp_path_str)
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(data_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

        return target_path

    def write_text(
        self,
        rel_path: Path | str,
        content: str,
        *,
        encoding: str = "utf-8",
    ) -> Path:
        """Atomically write text content inside the output root.

        Normalizes text to canonical form (LF line endings, no trailing whitespace, single trailing LF).
        """
        if not isinstance(content, str):
            raise TypeError(f"Expected str, got {type(content).__name__}")
        normalized = canonical_text(content)
        return self.write_bytes(rel_path, normalized.encode(encoding))

    def write_json(
        self,
        rel_path: Path | str,
        data: Any,
        *,
        indent: int | None = 2,
    ) -> Path:
        """Atomically write data as canonical JSON inside the output root."""
        json_str = canonical_json(data, indent=indent)
        return self.write_bytes(rel_path, json_str.encode("utf-8"))

    def read_bytes(self, rel_path: Path | str) -> bytes:
        """Read binary data from a file inside the output root."""
        target_path = self.resolve_path(rel_path)
        return target_path.read_bytes()

    def read_text(self, rel_path: Path | str, encoding: str = "utf-8") -> str:
        """Read text from a file inside the output root."""
        target_path = self.resolve_path(rel_path)
        return target_path.read_text(encoding=encoding)

    def exists(self, rel_path: Path | str) -> bool:
        """Check if a relative path exists inside the output root."""
        target_path = self.resolve_path(rel_path)
        return target_path.exists()

    def is_file(self, rel_path: Path | str) -> bool:
        """Check if a relative path is a file inside the output root."""
        target_path = self.resolve_path(rel_path)
        return target_path.is_file()

    def is_dir(self, rel_path: Path | str) -> bool:
        """Check if a relative path is a directory inside the output root."""
        target_path = self.resolve_path(rel_path)
        return target_path.is_dir()

    def manifest(self) -> dict[str, str]:
        """Return a sorted dictionary of all files in the output root mapping relative POSIX path to SHA-256."""
        if not self.root.exists():
            return {}
        result: dict[str, str] = {}
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                rel_posix = path.relative_to(self.root).as_posix()
                sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
                result[rel_posix] = sha256
        return result


class SourceTree:
    """Read-only guard enforcing source immutability.

    Opens user source files for inspection while forbidding any modification,
    creation, truncation, deletion, renaming, or permission change.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root).resolve()
        if not self.root.exists():
            raise CoreFsError(
                f"Source root does not exist: '{self.root}'",
                reason="source_root_not_found",
                path=self.root,
            )
        if not self.root.is_dir():
            raise CoreFsError(
                f"Source root must be a directory: '{self.root}'",
                reason="source_root_not_directory",
                path=self.root,
            )

    def resolve_path(self, rel_path: Path | str) -> Path:
        """Resolve a path within the source tree, rejecting any path that escapes."""
        p = Path(rel_path)
        if p.is_absolute():
            raise PathConfinementError(
                f"Absolute path '{rel_path}' is forbidden; paths must be relative to source root.",
                reason="absolute_path",
                path=p,
            )
        if bool(p.drive):
            raise PathConfinementError(
                f"Path with drive letter '{rel_path}' is forbidden.",
                reason="drive_letter",
                path=p,
            )

        candidate = self.root / p
        try:
            resolved = candidate.resolve()
        except Exception as exc:
            raise PathConfinementError(
                f"Failed to resolve path '{rel_path}': {exc}",
                reason="resolution_failed",
                path=p,
            ) from exc

        if not resolved.is_relative_to(self.root):
            raise PathConfinementError(
                f"Path '{rel_path}' escapes source root '{self.root}'.",
                reason="path_escape",
                path=p,
            )

        return resolved

    def read_bytes(self, rel_path: Path | str) -> bytes:
        """Read binary data from a source file."""
        target = self.resolve_path(rel_path)
        return target.read_bytes()

    def read_text(self, rel_path: Path | str, encoding: str = "utf-8") -> str:
        """Read text from a source file."""
        target = self.resolve_path(rel_path)
        return target.read_text(encoding=encoding)

    def open(
        self,
        rel_path: Path | str,
        mode: str = "r",
        encoding: str | None = None,
        errors: str | None = None,
    ) -> io.IOBase:
        """Open a source file for reading only. Any mutating mode raises SourceMutationError."""
        for mutating_char in ("w", "a", "+", "x"):
            if mutating_char in mode:
                raise SourceMutationError(
                    f"Cannot open '{rel_path}' in mutating mode '{mode}' on read-only SourceTree.",
                    reason="source_mutation_disallowed",
                    path=Path(rel_path),
                )
        target = self.resolve_path(rel_path)
        return target.open(mode=mode, encoding=encoding, errors=errors)

    def exists(self, rel_path: Path | str) -> bool:
        """Check if a relative path exists inside the source tree."""
        target = self.resolve_path(rel_path)
        return target.exists()

    def is_file(self, rel_path: Path | str) -> bool:
        """Check if a relative path is a file inside the source tree."""
        target = self.resolve_path(rel_path)
        return target.is_file()

    def is_dir(self, rel_path: Path | str) -> bool:
        """Check if a relative path is a directory inside the source tree."""
        target = self.resolve_path(rel_path)
        return target.is_dir()

    def stat(self, rel_path: Path | str) -> os.stat_result:
        """Return stat result for a file or directory inside the source tree."""
        target = self.resolve_path(rel_path)
        return target.stat()

    def iterdir(self, rel_path: Path | str = "") -> Iterator[Path]:
        """Iterate over entries in a source directory."""
        target = self.resolve_path(rel_path)
        return target.iterdir()

    def walk_files(self) -> Iterator[Path]:
        """Recursively yield all relative file paths inside the source tree in sorted order."""
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                yield path.relative_to(self.root)

    # Explicit mutation guard methods raising SourceMutationError
    def write_text(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"write_text is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def write_bytes(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"write_bytes is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def append_text(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"append_text is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def append_bytes(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"append_bytes is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def truncate(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"truncate is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def delete(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"delete is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def unlink(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"unlink is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def rename(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"rename is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def chmod(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"chmod is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def mkdir(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"mkdir is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )

    def rmdir(self, rel_path: Path | str, *args: Any, **kwargs: Any) -> None:
        raise SourceMutationError(
            f"rmdir is forbidden on read-only SourceTree: '{rel_path}'",
            reason="source_mutation_disallowed",
            path=Path(rel_path),
        )
