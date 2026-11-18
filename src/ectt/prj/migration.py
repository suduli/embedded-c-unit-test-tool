# implements: DSN-PRJ-020
"""Explicit, confirmed, backed-up schema migration (WP-PRJ-03, TASK-012).

A project file below the reader's minimum version is never migrated as a side
effect. Migration is three separate steps:

1. ``inspect_migration`` reads the file and reports the plan. It writes nothing.
2. ``migrate_file`` runs only when the caller passes ``confirmed=True``. It first
   copies the original bytes into the archive, then replaces the file atomically.
3. ``revert_migration`` restores the archived bytes. It also needs confirmation.

Each migration step is a pure function over the parsed document. A step that has
no inverse declares itself irreversible before anything runs, and the plan shows
that to the caller. The archived original is the reversal path that always exists.

No production project kind has a migration yet: the project manifest is at
version 1, its only version. The machinery is exercised with a test kind.

Satisfies: TOOL-PRJ-040, DSN-PRJ-020.
"""

from __future__ import annotations

import contextlib
import copy
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.prj.errors import ProjectError
from ectt.prj.model import FileKind, dispatch_schema_version
from ectt.prj.yaml_adapter import RestrictedYamlAdapter

__all__ = [
    "Migration",
    "MigrationPlan",
    "MigrationRegistry",
    "MigrationResult",
    "MigrationError",
    "MigrationNotConfirmedError",
    "MigrationChainError",
    "MigrationFailedError",
    "BackupExistsError",
    "inspect_migration",
    "migrate_file",
    "revert_migration",
]

ARCHIVE_DIR_NAME = "archive"

StepFn = Callable[[dict[str, Any]], dict[str, Any]]


class MigrationError(ProjectError):
    """Base error for schema migration."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "migration_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


class MigrationNotConfirmedError(MigrationError):
    """A migration was requested without explicit confirmation. Nothing was written."""

    def __init__(self, message: str, *, path: Path | str | None = None) -> None:
        super().__init__(message, reason="migration_not_confirmed", path=path)


class MigrationChainError(MigrationError):
    """No registered step connects the file's version to the target version."""

    def __init__(self, message: str, *, path: Path | str | None = None) -> None:
        super().__init__(message, reason="migration_chain_missing", path=path)


class MigrationFailedError(MigrationError):
    """A migration step raised. Nothing was written."""

    def __init__(self, message: str, *, path: Path | str | None = None) -> None:
        super().__init__(message, reason="migration_failed", path=path)


class BackupExistsError(MigrationError):
    """The archive already holds a different original for this migration. Nothing was written."""

    def __init__(self, message: str, *, path: Path | str | None = None) -> None:
        super().__init__(message, reason="backup_exists", path=path)


@dataclass(frozen=True)
class Migration:
    """One forward step, from ``from_version`` to ``to_version`` of a file kind.

    ``forward`` maps the parsed old document to the new one. ``inverse``, when
    given, maps the new document back to the old one. Without it the step is
    irreversible, and the plan says so before anything runs.
    """

    kind: str
    from_version: int
    to_version: int
    description: str
    forward: StepFn
    inverse: StepFn | None = None

    @property
    def reversible(self) -> bool:
        return self.inverse is not None


class MigrationRegistry:
    """Known migration steps, keyed by (kind, from_version). One step per source version."""

    def __init__(self) -> None:
        self._steps: dict[tuple[str, int], Migration] = {}

    def register(self, step: Migration) -> None:
        key = (step.kind, step.from_version)
        if key in self._steps:
            raise ValueError(
                f"migration from version {step.from_version} of '{step.kind}' is already registered"
            )
        self._steps[key] = step

    def step_from(self, kind: str, version: int) -> Migration | None:
        return self._steps.get((kind, version))


@dataclass(frozen=True)
class MigrationPlan:
    """What a migration would do. Built before anything is written; shown to the user."""

    kind: str
    from_version: int
    to_version: int
    steps: tuple[Migration, ...]

    @property
    def irreversible_steps(self) -> tuple[str, ...]:
        return tuple(step.description for step in self.steps if not step.reversible)

    @property
    def reversible(self) -> bool:
        return not self.irreversible_steps

    def describe(self) -> tuple[str, ...]:
        return tuple(
            f"v{step.from_version} -> v{step.to_version}: {step.description}"
            + ("" if step.reversible else " [irreversible]")
            for step in self.steps
        )


@dataclass(frozen=True)
class MigrationResult:
    """What a confirmed migration did, including where the original was archived."""

    from_version: int
    to_version: int
    backup_path: Path
    steps: tuple[str, ...]
    reversible: bool


def _plan(
    kind: FileKind,
    from_version: int,
    to_version: int,
    registry: MigrationRegistry,
    path: Path,
) -> MigrationPlan:
    if not kind.is_version_supported(to_version):
        raise MigrationError(
            f"Target version {to_version} is not supported by '{kind.name}' "
            f"(supported {kind.min_version}..{kind.max_version})",
            reason="target_unsupported",
            path=path,
        )
    if to_version <= from_version:
        raise MigrationError(
            f"Migration only moves forward: file is at version {from_version}, target {to_version}",
            reason="migration_not_forward",
            path=path,
        )
    steps: list[Migration] = []
    current = from_version
    while current < to_version:
        step = registry.step_from(kind.name, current)
        if step is None:
            raise MigrationChainError(
                f"No migration registered from version {current} of '{kind.name}'; "
                f"cannot reach version {to_version}",
                path=path,
            )
        steps.append(step)
        current = step.to_version
    if current != to_version:
        raise MigrationChainError(
            f"Migration chain overshoots target {to_version} (reaches {current})",
            path=path,
        )
    return MigrationPlan(
        kind=kind.name,
        from_version=from_version,
        to_version=to_version,
        steps=tuple(steps),
    )


def _read_document(
    path: Path, kind: FileKind, adapter: RestrictedYamlAdapter
) -> tuple[bytes, dict[str, Any], int]:
    original = path.read_bytes()
    data = adapter.load(original.decode("utf-8"), path=path)
    # Read the version without the reader's minimum check: this function is the one place
    # that is allowed to see a file below the minimum.
    version = dispatch_schema_version(data, _open_floor(kind), file_path=path)
    return original, data, version


def _open_floor(kind: FileKind) -> FileKind:
    return FileKind(
        name=kind.name,
        file_pattern=kind.file_pattern,
        min_version=0,
        max_version=kind.max_version,
        canonical_keys=kind.canonical_keys,
        default_values=kind.default_values,
    )


def inspect_migration(
    path: Path,
    kind: FileKind,
    to_version: int,
    registry: MigrationRegistry,
    *,
    adapter: RestrictedYamlAdapter | None = None,
) -> MigrationPlan:
    """Report the migration that would run. Reads the file; writes nothing.

    Implements: DSN-PRJ-020. Satisfies: TOOL-PRJ-040.
    """
    active = adapter or RestrictedYamlAdapter()
    _, _, version = _read_document(path, kind, active)
    if version == to_version:
        raise MigrationError(
            f"File is already at version {to_version}; nothing to migrate",
            reason="migration_not_needed",
            path=path,
        )
    return _plan(kind, version, to_version, registry, path)


def _atomic_write(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except Exception:
        if temp_path is not None and temp_path.exists():
            with contextlib.suppress(OSError):
                temp_path.unlink()
        raise


def migrate_file(
    path: Path,
    kind: FileKind,
    to_version: int,
    registry: MigrationRegistry,
    *,
    archive_root: Path,
    confirmed: bool,
    adapter: RestrictedYamlAdapter | None = None,
) -> MigrationResult:
    """Migrate one project file, but only when ``confirmed`` is exactly ``True``.

    Order of effects: validate the plan, run every step on a copy, check the
    result, archive the original, then replace the file atomically. Any failure
    before the replace leaves the file and the archive as they were.

    Implements: DSN-PRJ-020. Satisfies: TOOL-PRJ-040.
    """
    active = adapter or RestrictedYamlAdapter()
    original, data, from_version = _read_document(path, kind, active)
    if from_version == to_version:
        raise MigrationError(
            f"File is already at version {to_version}; nothing to migrate",
            reason="migration_not_needed",
            path=path,
        )
    plan = _plan(kind, from_version, to_version, registry, path)

    if confirmed is not True:
        raise MigrationNotConfirmedError(
            f"Migration of '{path.name}' from v{from_version} to v{to_version} needs explicit confirmation. "
            f"Steps: {'; '.join(plan.describe())}",
            path=path,
        )

    migrated = copy.deepcopy(data)
    try:
        for step in plan.steps:
            migrated = step.forward(migrated)
    except Exception as exc:
        raise MigrationFailedError(
            f"A migration step failed ({type(exc).__name__}); the file was not changed",
            path=path,
        ) from exc

    migrated["schema_version"] = str(to_version)
    new_bytes = active.dump_bytes(
        migrated,
        canonical_keys=kind.canonical_keys,
        default_values=kind.default_values,
    )

    backup_dir = (
        archive_root / ARCHIVE_DIR_NAME / f"migration-v{from_version}-to-v{to_version}"
    )
    backup_path = backup_dir / path.name
    if backup_path.exists():
        if backup_path.read_bytes() != original:
            raise BackupExistsError(
                f"Archive already holds a different original at '{backup_path.name}'; refusing to overwrite it",
                path=backup_path,
            )
    else:
        _atomic_write(backup_path, original)

    _atomic_write(path, new_bytes)
    return MigrationResult(
        from_version=from_version,
        to_version=to_version,
        backup_path=backup_path,
        steps=plan.describe(),
        reversible=plan.reversible,
    )


def revert_migration(path: Path, result: MigrationResult, *, confirmed: bool) -> None:
    """Restore the archived original over a migrated file. Needs ``confirmed is True``.

    Implements: DSN-PRJ-020. Satisfies: TOOL-PRJ-040.
    """
    if confirmed is not True:
        raise MigrationNotConfirmedError(
            f"Reverting to v{result.from_version} needs explicit confirmation; nothing was changed",
            path=path,
        )
    _atomic_write(path, result.backup_path.read_bytes())
