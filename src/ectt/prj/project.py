# implements: DSN-PRJ-010, DSN-PRJ-040, DSN-PRJ-030
"""Project root management, lifecycle, atomic persistence, and path confinement.

Satisfies: TOOL-PRJ-010, TOOL-PRJ-020, TOOL-PRJ-050, TOOL-PRJ-070, TOOL-UIX-320, TOOL-CIC-080.
"""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from ectt.prj.errors import (
    CommentPreservationError,
    ProjectError,
    ProjectLocationError,
    ProjectRootNotFoundError,
)
from ectt.prj.model import (
    DEFAULT_KIND_REGISTRY,
    PROJECT_KIND,
    FileKind,
    KindRegistry,
    ProjectDocument,
    dispatch_schema_version,
)
from ectt.prj.paths import normalize_posix_path, resolve_project_path, validate_project_path
from ectt.prj.yaml_adapter import (
    RestrictedYamlAdapter,
    SerializationAdapter,
    detect_yaml_comments,
)

__all__ = [
    "PROJECT_ROOT_MARKER",
    "Project",
]

PROJECT_ROOT_MARKER = "ectt.project"


class Project:
    """Project root abstraction owning configuration, relative path references, and storage."""

    def __init__(
        self,
        root: Path | str,
        document: ProjectDocument,
        *,
        adapter: SerializationAdapter | None = None,
        registry: KindRegistry | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.document = document
        self.adapter = adapter or RestrictedYamlAdapter()
        self.registry = registry or DEFAULT_KIND_REGISTRY

    @property
    def marker_path(self) -> Path:
        return self.root / PROJECT_ROOT_MARKER

    @property
    def name(self) -> str:
        return str(self.document.get("name", self.root.name))

    @property
    def schema_version(self) -> int:
        return self.document.schema_version

    @property
    def source_roots(self) -> list[str]:
        val = self.document.get("source_roots", [])
        if isinstance(val, (list, tuple)):
            return [str(v) for v in val]
        return []

    @property
    def output_root(self) -> str | None:
        val = self.document.get("output_root", None)
        return str(val) if val else None

    @property
    def settings(self) -> dict[str, Any]:
        val = self.document.get("settings", {})
        return dict(val) if isinstance(val, Mapping) else {}

    @classmethod
    def find(
        cls,
        start_dir: Path | str,
        *,
        adapter: SerializationAdapter | None = None,
        registry: KindRegistry | None = None,
    ) -> Project:
        """Locate project root by walking upward until ectt.project marker is found."""
        current = Path(start_dir).resolve()
        while True:
            candidate = current / PROJECT_ROOT_MARKER
            if candidate.is_file():
                return cls.open(current, adapter=adapter, registry=registry)
            parent = current.parent
            if parent == current:
                # Hit filesystem root
                raise ProjectRootNotFoundError(
                    f"No '{PROJECT_ROOT_MARKER}' found in '{start_dir}' or any parent directories",
                    path=start_dir,
                )
            current = parent

    @classmethod
    def open(
        cls,
        root_dir: Path | str,
        *,
        adapter: SerializationAdapter | None = None,
        registry: KindRegistry | None = None,
    ) -> Project:
        """Open an existing project from its root directory."""
        resolved_root = Path(root_dir).resolve()
        marker = resolved_root / PROJECT_ROOT_MARKER
        if not marker.is_file():
            raise ProjectRootNotFoundError(
                f"Project root marker '{PROJECT_ROOT_MARKER}' not found in '{resolved_root}'",
                path=resolved_root,
            )

        active_adapter = adapter or RestrictedYamlAdapter()
        active_registry = registry or DEFAULT_KIND_REGISTRY

        content = marker.read_text(encoding="utf-8")
        data = active_adapter.load(content, path=marker)
        version = dispatch_schema_version(data, PROJECT_KIND, file_path=marker)

        doc = ProjectDocument(PROJECT_KIND, data, schema_version=version, path=marker)
        return cls(resolved_root, doc, adapter=active_adapter, registry=active_registry)

    @classmethod
    def create(
        cls,
        root_dir: Path | str,
        *,
        name: str | None = None,
        source_roots: Sequence[str | Path] = (),
        output_root: str | Path | None = None,
        settings: Mapping[str, Any] | None = None,
        adapter: SerializationAdapter | None = None,
        registry: KindRegistry | None = None,
        overwrite: bool = False,
    ) -> Project:
        """Create a new project store in root_dir, writing ectt.project."""
        resolved_root = Path(root_dir).resolve()
        resolved_root.mkdir(parents=True, exist_ok=True)
        marker = resolved_root / PROJECT_ROOT_MARKER

        if marker.exists() and not overwrite:
            raise ProjectError(
                f"Project already exists at '{resolved_root}'",
                reason="project_already_exists",
                path=resolved_root,
            )

        norm_sources = [validate_project_path(s) for s in source_roots]
        norm_output = validate_project_path(output_root) if output_root else ""

        # Strictly no timestamps, hostnames, or usernames
        data: dict[str, Any] = {
            "schema_version": "1",
            "name": name or resolved_root.name,
            "source_roots": norm_sources,
            "output_root": norm_output,
            "settings": dict(settings or {}),
        }

        active_adapter = adapter or RestrictedYamlAdapter()
        active_registry = registry or DEFAULT_KIND_REGISTRY

        doc = ProjectDocument(PROJECT_KIND, data, schema_version=1, path=marker)
        project = cls(resolved_root, doc, adapter=active_adapter, registry=active_registry)
        project.save()
        return project

    def resolve_path(self, rel_path: str | Path) -> Path:
        """Resolve a project-relative path string, guaranteeing it stays within project root."""
        return resolve_project_path(self.root, rel_path)

    def add_source_root(self, rel_path: str | Path) -> str:
        """Add a relative source root path and normalize to POSIX format."""
        posix_rel = validate_project_path(rel_path)
        sources = self.source_roots
        if posix_rel not in sources:
            sources.append(posix_rel)
            self.document["source_roots"] = sources
        return posix_rel

    def set_output_root(self, rel_path: str | Path | None) -> str | None:
        """Set output root relative path and normalize to POSIX format."""
        if rel_path is None:
            self.document["output_root"] = ""
            return None
        posix_rel = validate_project_path(rel_path)
        self.document["output_root"] = posix_rel
        return posix_rel

    def read_file(self, rel_path: str | Path) -> ProjectDocument:
        """Read and parse an authored project file, dispatching on its schema_version."""
        target_path = self.resolve_path(rel_path)
        if not target_path.is_file():
            raise FileNotFoundError(f"Project file '{target_path}' not found")

        content = target_path.read_text(encoding="utf-8")
        data = self.adapter.load(content, path=target_path)

        kind = self.registry.find_by_filename(target_path.name)
        if kind is None:
            # Fallback dynamic kind
            kind = FileKind(
                name=target_path.name,
                file_pattern=target_path.name,
                min_version=1,
                max_version=1,
            )

        version = dispatch_schema_version(data, kind, file_path=target_path)
        return ProjectDocument(kind, data, schema_version=version, path=target_path)

    def save_file(
        self,
        rel_path: str | Path,
        data: Mapping[str, Any],
        *,
        kind: FileKind | None = None,
        discard_comments: bool = False,
    ) -> Path:
        """Atomically save a project file in the project tree.

        Enforces:
        - Must never write into user source roots or output root.
        - Refuses overwrite if existing file contains comments, unless discard_comments=True.
        - Leaves identical content untouched (byte-identical no-op).
        - Atomic write via temporary file in target directory + os.replace.
        """
        target_path = self.resolve_path(rel_path)

        # 1. Path confinement guards: reject writes into user source roots or output root
        for src in self.source_roots:
            resolved_src = self.resolve_path(src)
            if target_path == resolved_src or target_path.is_relative_to(resolved_src):
                raise ProjectLocationError(
                    f"Forbidden project file write: '{target_path}' is inside user source root '{resolved_src}'",
                    path=target_path,
                )

        if self.output_root:
            resolved_out = self.resolve_path(self.output_root)
            if target_path == resolved_out or target_path.is_relative_to(resolved_out):
                raise ProjectLocationError(
                    f"Forbidden project file write: '{target_path}' is inside output root '{resolved_out}'",
                    path=target_path,
                )

        # 2. Check for comments in existing file before overwrite
        if target_path.exists():
            if target_path.is_dir():
                raise ProjectError(
                    f"Cannot write project file over directory: '{target_path}'",
                    reason="is_directory",
                    path=target_path,
                )
            try:
                existing_text = target_path.read_text(encoding="utf-8")
                comments = detect_yaml_comments(existing_text)
                if comments and not discard_comments:
                    comment_line, comment_col = comments[0]
                    raise CommentPreservationError(
                        f"Cannot overwrite file '{target_path}' containing YAML comment at line {comment_line}: "
                        f"comments cannot be preserved on rewrite. Pass discard_comments=True to allow.",
                        path=target_path,
                        line=comment_line,
                        column=comment_col,
                    )
            except UnicodeDecodeError:
                pass

        # 3. Serialize to deterministic bytes
        active_kind = kind or self.registry.find_by_filename(target_path.name)
        canonical_keys = active_kind.canonical_keys if active_kind else ()
        default_values = active_kind.default_values if active_kind else None

        new_bytes = self.adapter.dump_bytes(
            data,
            canonical_keys=canonical_keys,
            default_values=default_values,
        )

        # 4. Byte-identical check: if content identical, leave untouched (preserving mtime)
        if target_path.exists():
            try:
                with target_path.open("rb") as f:
                    if f.read() == new_bytes:
                        return target_path
            except OSError:
                pass

        # 5. Atomic write
        target_dir = target_path.parent
        target_dir.mkdir(parents=True, exist_ok=True)

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=target_dir,
                prefix=f".{target_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as f:
                temp_path = Path(f.name)
                f.write(new_bytes)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, target_path)
        except Exception:
            if temp_path is not None and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

        return target_path

    def save(self, *, discard_comments: bool = False) -> Path:
        """Save the root ectt.project marker file."""
        return self.save_file(
            PROJECT_ROOT_MARKER,
            self.document.data,
            kind=PROJECT_KIND,
            discard_comments=discard_comments,
        )
