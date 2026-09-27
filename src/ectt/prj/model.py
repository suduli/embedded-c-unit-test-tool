# implements: DSN-PRJ-010, DSN-PRJ-030
"""Document model, kind registry, and schema version dispatch for ectt project files.

Implements SDD-003 §5 schema versioning discipline and extensible file kinds.

Satisfies: TOOL-PRJ-020, TOOL-PRJ-030, DSN-PRJ-010.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ectt.prj.errors import (
    InvalidSchemaVersionError,
    MigrationRequiredError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
)

__all__ = [
    "FileKind",
    "KindRegistry",
    "PROJECT_KIND",
    "DEFAULT_KIND_REGISTRY",
    "dispatch_schema_version",
    "ProjectDocument",
]

_INT_RE = re.compile(r"^-?\d+$")


@dataclass(frozen=True)
class FileKind:
    """Declaration of a project file kind, its version boundaries, and emission rules."""

    name: str
    file_pattern: str
    min_version: int
    max_version: int
    canonical_keys: tuple[str, ...] = ("schema_version",)
    default_values: dict[str, Any] = field(default_factory=dict)

    def is_version_supported(self, version: int) -> bool:
        return self.min_version <= version <= self.max_version


PROJECT_KIND = FileKind(
    name="project",
    file_pattern="ectt.project",
    min_version=1,
    max_version=1,
    canonical_keys=(
        "schema_version",
        "name",
        "source_roots",
        "output_root",
        "settings",
    ),
    default_values={
        "source_roots": [],
        "output_root": "",
        "settings": {},
    },
)


class KindRegistry:
    """Registry of known project file kinds and their supported schema version ranges."""

    def __init__(self) -> None:
        self._kinds: dict[str, FileKind] = {}

    def register(self, kind: FileKind) -> None:
        """Register a new file kind."""
        self._kinds[kind.name] = kind

    def get(self, name: str) -> FileKind:
        """Retrieve a file kind by name."""
        if name not in self._kinds:
            raise KeyError(f"Unknown file kind: '{name}'")
        return self._kinds[name]

    def find_by_filename(self, filename: str) -> FileKind | None:
        """Find a registered file kind matching the given filename."""
        for kind in self._kinds.values():
            if kind.file_pattern.startswith("*"):
                suffix = kind.file_pattern[1:]
                if filename.endswith(suffix):
                    return kind
            elif filename == kind.file_pattern:
                return kind
        return None


DEFAULT_KIND_REGISTRY = KindRegistry()
DEFAULT_KIND_REGISTRY.register(PROJECT_KIND)


def dispatch_schema_version(
    doc: Mapping[str, Any],
    kind: FileKind,
    *,
    file_path: Path | str | None = None,
) -> int:
    """Validate schema_version and dispatch per SDD-003 §5.

    Pseudocode logic:
    - absent -> refuse (MissingSchemaVersionError)
    - non-integer -> refuse (InvalidSchemaVersionError)
    - v > max_supported -> refuse, naming both versions (UnsupportedSchemaVersionError)
    - v < min_supported -> report migration required, perform nothing (MigrationRequiredError)
    - supported -> return version integer
    """
    loc = str(file_path) if file_path is not None else "<memory>"
    if "schema_version" not in doc:
        raise MissingSchemaVersionError(
            f"Missing 'schema_version' in '{loc}'; project files must declare schema_version",
            path=file_path,
        )

    raw_val = doc["schema_version"]

    if isinstance(raw_val, int):
        v = raw_val
    elif isinstance(raw_val, str) and _INT_RE.match(raw_val.strip()):
        v = int(raw_val.strip())
    else:
        raise InvalidSchemaVersionError(
            f"Invalid schema_version '{raw_val}' in '{loc}'; schema version must be an integer",
            path=file_path,
        )

    if v > kind.max_version:
        raise UnsupportedSchemaVersionError(
            f"Unsupported schema_version {v} in '{loc}'. "
            f"Maximum version supported by this tool is {kind.max_version}; "
            f"a newer version of ectt is required to open this project file",
            path=file_path,
            version=v,
            min_version=kind.min_version,
            max_version=kind.max_version,
        )

    if v < kind.min_version:
        raise MigrationRequiredError(
            f"Schema version {v} in '{loc}'. "
            f"Minimum version supported is {kind.min_version}; explicit migration is required",
            path=file_path,
            version=v,
            min_version=kind.min_version,
        )

    return v


class ProjectDocument:
    """Format-agnostic in-memory representation of a project file."""

    def __init__(
        self,
        kind: FileKind,
        data: dict[str, Any],
        *,
        schema_version: int,
        path: Path | None = None,
    ) -> None:
        self.kind = kind
        self.data = data
        self.schema_version = schema_version
        self.path = path

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
