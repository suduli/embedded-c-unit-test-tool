# implements: DSN-PRJ-020
"""Explicit, confirmed, backed-up schema migration (WP-PRJ-03, TASK-012).

Verifies: TOOL-PRJ-040, DSN-PRJ-020.

The project manifest is at its only version (1), so the machinery is exercised with
a test kind whose minimum is 2. Cases: nothing happens on open, inspection writes
nothing, confirmation is required, a confirmed migration archives then replaces,
failures leave both files alone, irreversible steps are declared, and revert restores.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ectt.prj.errors import MigrationRequiredError
from ectt.prj.migration import (
    BackupExistsError,
    Migration,
    MigrationChainError,
    MigrationError,
    MigrationFailedError,
    MigrationNotConfirmedError,
    MigrationRegistry,
    inspect_migration,
    migrate_file,
    revert_migration,
)
from ectt.prj.model import FileKind, dispatch_schema_version
from ectt.prj.project import Project

V1_TEXT = 'schema_version: "1"\nlabel: "alpha"\n'

FIXTURE = FileKind(
    name="fixture",
    file_pattern="fixture.project",
    min_version=2,
    max_version=2,
    canonical_keys=("schema_version", "name"),
    default_values={},
)
LOSSY = FileKind(
    name="lossy",
    file_pattern="lossy.project",
    min_version=2,
    max_version=2,
    canonical_keys=("schema_version", "name"),
    default_values={},
)


def _rename_forward(doc: dict[str, Any]) -> dict[str, Any]:
    out = dict(doc)
    out["name"] = out.pop("label")
    return out


def _rename_inverse(doc: dict[str, Any]) -> dict[str, Any]:
    out = dict(doc)
    out["label"] = out.pop("name")
    return out


def _registry() -> MigrationRegistry:
    registry = MigrationRegistry()
    registry.register(
        Migration(
            kind="fixture",
            from_version=1,
            to_version=2,
            description="rename label to name",
            forward=_rename_forward,
            inverse=_rename_inverse,
        )
    )
    return registry


def _lossy_registry() -> MigrationRegistry:
    def drop_label(doc: dict[str, Any]) -> dict[str, Any]:
        out = dict(doc)
        out.pop("label", None)
        out["name"] = "migrated"
        return out

    registry = MigrationRegistry()
    registry.register(
        Migration(
            kind="lossy",
            from_version=1,
            to_version=2,
            description="drop label",
            forward=drop_label,
            inverse=None,
        )
    )
    return registry


def _write(path: Path, text: str) -> Path:
    path.write_bytes(text.encode("utf-8"))
    return path


def test_opening_an_old_file_reports_migration_and_changes_nothing(
    tmp_path: Path,
) -> None:
    """verifies: DSN-PRJ-020 — the reader refuses below its minimum; it does not migrate on open."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)
    before = target.read_bytes()

    with pytest.raises(MigrationRequiredError):
        dispatch_schema_version({"schema_version": "1"}, FIXTURE, file_path=target)

    assert target.read_bytes() == before


def test_inspection_reports_the_plan_and_writes_nothing(tmp_path: Path) -> None:
    """verifies: DSN-PRJ-020 — the migration is reported before anything is written."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)
    before = target.read_bytes()

    plan = inspect_migration(target, FIXTURE, 2, _registry())

    assert plan.describe() == ("v1 -> v2: rename label to name",)
    assert plan.reversible is True
    assert target.read_bytes() == before
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize("not_confirmed", [False, None, "yes", 1])
def test_migration_refuses_without_exact_confirmation(
    tmp_path: Path, not_confirmed: object
) -> None:
    """verifies: TOOL-PRJ-040 — only the literal True confirms; anything else refuses and writes nothing."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)
    before = target.read_bytes()

    with pytest.raises(MigrationNotConfirmedError):
        migrate_file(
            target,
            FIXTURE,
            2,
            _registry(),
            archive_root=tmp_path,
            confirmed=not_confirmed,  # type: ignore[arg-type]
        )

    assert target.read_bytes() == before
    assert not (tmp_path / "archive").exists()


def test_confirmed_migration_archives_original_then_replaces_file(
    tmp_path: Path,
) -> None:
    """verifies: DSN-PRJ-020 — the original is archived byte-for-byte; the file is now at the new version."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)

    result = migrate_file(
        target, FIXTURE, 2, _registry(), archive_root=tmp_path, confirmed=True
    )

    assert (
        result.backup_path
        == tmp_path / "archive" / "migration-v1-to-v2" / "fixture.project"
    )
    assert result.backup_path.read_bytes() == V1_TEXT.encode("utf-8")
    migrated = target.read_text(encoding="utf-8")
    assert "name" in migrated and "label" not in migrated
    assert (
        dispatch_schema_version({"schema_version": "2"}, FIXTURE, file_path=target) == 2
    )
    assert result.reversible is True


def test_migration_is_deterministic(tmp_path: Path) -> None:
    """verifies: TOOL-PRJ-050 — the same input migrates to byte-identical output."""
    first_dir = tmp_path / "a"
    second_dir = tmp_path / "b"
    first_dir.mkdir()
    second_dir.mkdir()
    first = _write(first_dir / "fixture.project", V1_TEXT)
    second = _write(second_dir / "fixture.project", V1_TEXT)

    migrate_file(first, FIXTURE, 2, _registry(), archive_root=first_dir, confirmed=True)
    migrate_file(
        second, FIXTURE, 2, _registry(), archive_root=second_dir, confirmed=True
    )

    assert first.read_bytes() == second.read_bytes()


def test_failing_step_leaves_file_and_archive_untouched(tmp_path: Path) -> None:
    """verifies: DSN-PRJ-020 — a step that raises changes nothing and archives nothing."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)
    before = target.read_bytes()

    def broken(doc: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("step blew up")

    registry = MigrationRegistry()
    registry.register(
        Migration(
            kind="fixture",
            from_version=1,
            to_version=2,
            description="broken",
            forward=broken,
        )
    )

    with pytest.raises(MigrationFailedError) as exc_info:
        migrate_file(
            target, FIXTURE, 2, registry, archive_root=tmp_path, confirmed=True
        )

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert target.read_bytes() == before
    assert not (tmp_path / "archive").exists()


def test_missing_step_in_the_chain_is_refused_before_anything_runs(
    tmp_path: Path,
) -> None:
    """verifies: DSN-PRJ-020 — migrations chain; a missing link is refused up front."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)

    with pytest.raises(MigrationChainError):
        migrate_file(
            target,
            FIXTURE,
            2,
            MigrationRegistry(),
            archive_root=tmp_path,
            confirmed=True,
        )

    assert target.read_text(encoding="utf-8") == V1_TEXT


def test_irreversible_step_is_declared_before_running(tmp_path: Path) -> None:
    """verifies: DSN-PRJ-020 — a step without an inverse says so in the plan, before it runs."""
    target = _write(tmp_path / "lossy.project", V1_TEXT)

    plan = inspect_migration(target, LOSSY, 2, _lossy_registry())
    assert plan.reversible is False
    assert plan.irreversible_steps == ("drop label",)

    with pytest.raises(MigrationNotConfirmedError) as exc_info:
        migrate_file(
            target, LOSSY, 2, _lossy_registry(), archive_root=tmp_path, confirmed=False
        )
    assert "[irreversible]" in str(exc_info.value)

    result = migrate_file(
        target, LOSSY, 2, _lossy_registry(), archive_root=tmp_path, confirmed=True
    )
    assert result.reversible is False


def test_existing_archive_with_different_content_is_never_overwritten(
    tmp_path: Path,
) -> None:
    """verifies: DSN-PRJ-020 — the archive is evidence; a different original refuses the migration."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)
    archive = tmp_path / "archive" / "migration-v1-to-v2"
    archive.mkdir(parents=True)
    (archive / "fixture.project").write_text(
        "someone else's original", encoding="utf-8"
    )

    with pytest.raises(BackupExistsError):
        migrate_file(
            target, FIXTURE, 2, _registry(), archive_root=tmp_path, confirmed=True
        )

    assert target.read_text(encoding="utf-8") == V1_TEXT
    assert (archive / "fixture.project").read_text(
        encoding="utf-8"
    ) == "someone else's original"


def test_revert_restores_the_archived_original_only_when_confirmed(
    tmp_path: Path,
) -> None:
    """verifies: TOOL-PRJ-040 — reversal is possible, and it too needs confirmation."""
    target = _write(tmp_path / "fixture.project", V1_TEXT)
    result = migrate_file(
        target, FIXTURE, 2, _registry(), archive_root=tmp_path, confirmed=True
    )
    migrated = target.read_bytes()

    with pytest.raises(MigrationNotConfirmedError):
        revert_migration(target, result, confirmed=False)
    assert target.read_bytes() == migrated

    revert_migration(target, result, confirmed=True)
    assert target.read_bytes() == V1_TEXT.encode("utf-8")


def test_migration_is_refused_when_already_current_or_going_backwards(
    tmp_path: Path,
) -> None:
    """verifies: DSN-PRJ-020 — no-op and downgrade requests are refused with named reasons."""
    target = _write(tmp_path / "fixture.project", 'schema_version: "2"\nname: "x"\n')

    with pytest.raises(MigrationError) as exc_info:
        inspect_migration(target, FIXTURE, 2, _registry())
    assert exc_info.value.reason == "migration_not_needed"

    with pytest.raises(MigrationError) as exc_info:
        inspect_migration(target, FIXTURE, 1, _registry())
    assert exc_info.value.reason in {
        "migration_not_needed",
        "migration_not_forward",
        "target_unsupported",
    }


def test_project_manifest_is_at_its_only_version_so_no_migration_applies(
    tmp_path: Path,
) -> None:
    """verifies: TOOL-PRJ-040 — the real project kind has no older version to migrate from."""
    project = Project.create(tmp_path / "proj")

    assert project.schema_version == 1
    with pytest.raises(MigrationChainError):
        migrate_file(
            project.marker_path,
            FileKind(
                name="project",
                file_pattern="ectt.project",
                min_version=1,
                max_version=2,
                canonical_keys=(
                    "schema_version",
                    "name",
                    "source_roots",
                    "output_root",
                    "settings",
                ),
                default_values={},
            ),
            2,
            MigrationRegistry(),
            archive_root=tmp_path,
            confirmed=True,
        )
