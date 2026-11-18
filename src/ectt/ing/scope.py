"""Test scope model and resolution (WP-ING-04).

A test scope is a named, first-class set of translation units treated as the
code under test; every dependency outside the set is external. Membership can
be defined by explicit file list, directory, glob pattern, or named
build-system target, and persists as plain-text JSON.

Satisfies: TOOL-ING-120, TOOL-ING-130, TOOL-ING-140, TOOL-ING-150, TOOL-ING-190.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.ing.errors import IngestionError

__all__ = [
    "SCOPE_SCHEMA_VERSION",
    "ScopeTooSmallError",
    "UnknownScopeTargetError",
    "DuplicateScopeNameError",
    "ScopeRecordError",
    "TestScope",
    "ScopeSet",
    "expand_directory",
    "expand_glob",
    "expand_target",
    "classify_calls",
    "external_dependencies",
    "save_scope",
    "load_scope",
]

SCOPE_SCHEMA_VERSION = 1

KIND_INTRA = "intra-scope"
KIND_EXTERNAL = "external"


class ScopeTooSmallError(IngestionError):
    """Raised when a scope is created with fewer than two sources (TOOL-ING-120)."""

    def __init__(
        self, message: str, *, reason: str = "scope_too_small", path: Path | str | None = None
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class UnknownScopeTargetError(IngestionError):
    """Raised when a named build target is not in the declared mapping (TOOL-ING-150)."""

    def __init__(
        self, message: str, *, reason: str = "unknown_scope_target", path: Path | str | None = None
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class DuplicateScopeNameError(IngestionError):
    """Raised when two scopes share a name."""

    def __init__(
        self, message: str, *, reason: str = "duplicate_scope_name", path: Path | str | None = None
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class ScopeRecordError(IngestionError):
    """Raised when a persisted scope file is malformed."""

    def __init__(
        self, message: str, *, reason: str = "scope_record_error", path: Path | str | None = None
    ) -> None:
        super().__init__(message, reason=reason, path=path)


@dataclass(frozen=True)
class TestScope:
    """A named set of translation units treated as the code under test."""

    name: str
    members: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ScopeTooSmallError("scope name must be a non-empty string")
        if len(self.members) < 2:
            raise ScopeTooSmallError(
                f"scope '{self.name}' needs two or more source files, "
                f"got {len(self.members)}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {"members": list(self.members), "name": self.name}


def expand_files(files: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Explicit file list, deduplicated and deterministically ordered."""
    return tuple(sorted(dict.fromkeys(files)))


def expand_directory(directory: Path | str) -> tuple[str, ...]:
    """All `.c` files under ``directory``, recursively, deterministically ordered."""
    root = Path(directory)
    if not root.is_dir():
        raise ScopeRecordError(f"scope directory '{directory}' does not exist", path=root)
    return tuple(sorted(path.as_posix() for path in root.rglob("*.c")))


def expand_glob(pattern: Path | str) -> tuple[str, ...]:
    """All files matching a glob pattern, deterministically ordered."""
    matches = sorted(Path().glob(str(pattern)))
    return tuple(sorted(match.as_posix() for match in matches if match.is_file()))


def expand_target(target: str, targets: Mapping[str, list[str] | tuple[str, ...]]) -> tuple[str, ...]:
    """Named build-system target resolved against a declared mapping."""
    if target not in targets:
        raise UnknownScopeTargetError(
            f"build-system target '{target}' is not declared in the target mapping"
        )
    return expand_files(list(targets[target]))


def classify_calls(
    calls: Mapping[str, tuple[str, ...]],
    defined_functions: Mapping[str, tuple[str, ...] | set[str]],
) -> dict[str, dict[str, str]]:
    """Classify each call as intra-scope or external (TOOL-ING-140).

    ``calls`` maps caller unit to the callees it references; ``defined_functions``
    maps unit to the functions that unit defines. A callee defined by any unit
    (here: any unit in the caller's scope, which for a single-scope run is the
    whole mapping) is intra-scope.
    """
    defined: set[str] = set()
    for functions in defined_functions.values():
        defined.update(functions)
    result: dict[str, dict[str, str]] = {}
    for unit, callees in calls.items():
        result[unit] = {callee: (KIND_INTRA if callee in defined else KIND_EXTERNAL) for callee in callees}
    return result


def external_dependencies(
    calls: Mapping[str, tuple[str, ...]],
    defined_functions: Mapping[str, tuple[str, ...] | set[str]],
) -> tuple[str, ...]:
    """Functions referenced by members but defined by none of them (TOOL-ING-130)."""
    classification = classify_calls(calls, defined_functions)
    external: set[str] = set()
    for unit_calls in classification.values():
        for callee, kind in unit_calls.items():
            if kind == KIND_EXTERNAL:
                external.add(callee)
    return tuple(sorted(external))


class ScopeSet:
    """Named scopes with unique names and deterministic listing."""

    def __init__(self) -> None:
        self._scopes: dict[str, TestScope] = {}

    def add(self, scope: TestScope) -> None:
        """Add a scope; reject a reused name."""
        if scope.name in self._scopes:
            raise DuplicateScopeNameError(f"scope '{scope.name}' already exists")
        self._scopes[scope.name] = scope

    def lookup(self, name: str) -> TestScope:
        """The scope registered under ``name``."""
        try:
            return self._scopes[name]
        except KeyError:
            raise ScopeRecordError(f"no scope is registered under '{name}'") from None

    def list_names(self) -> tuple[str, ...]:
        """Scope names, ordered deterministically."""
        return tuple(sorted(self._scopes))


def save_scope(scope: TestScope, path: Path | str) -> None:
    """Persist a scope as plain-text JSON with a schema version (TOOL-ING-190)."""
    document: dict[str, Any] = {
        "schema_version": SCOPE_SCHEMA_VERSION,
        "scope": scope.to_dict(),
    }
    Path(path).write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_scope(path: Path | str) -> TestScope:
    """Reload a persisted scope; named errors for malformed files."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScopeRecordError(f"cannot read scope file: {exc}", path=file_path) from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ScopeRecordError(f"scope file is not valid JSON: {exc}", path=file_path) from exc
    if not isinstance(document, dict) or document.get("schema_version") != SCOPE_SCHEMA_VERSION:
        raise ScopeRecordError(
            f"scope file schema version is missing or unsupported "
            f"(expected {SCOPE_SCHEMA_VERSION})",
            path=file_path,
        )
    scope_data = document.get("scope")
    if not isinstance(scope_data, dict) or not isinstance(scope_data.get("members"), list):
        raise ScopeRecordError("scope file has no 'scope.members' list", path=file_path)
    return TestScope(
        name=str(scope_data.get("name", "")),
        members=tuple(str(member) for member in scope_data["members"]),
    )
