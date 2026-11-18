# implements: DSN-PRJ-050
"""Broken-reference detection for the project store (WP-PRJ-04, TASK-011).

Every reference the project stores is resolved and each failure is reported with
the referencing file, the missing target, and whether the reference is required.
The check reports; it never raises, so a project with a broken reference still
opens and the caller decides what to do.

Stored references in the current schema:
- ``source_roots`` entries (required: a source root must exist).
- ``output_root`` (optional: an output root is created by generation).

Satisfies: TOOL-PRJ-090.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ectt.prj.errors import InvalidRelativePathError, ProjectConfinementError
from ectt.prj.paths import resolve_project_path, validate_project_path

__all__ = [
    "DanglingReference",
    "find_dangling_references",
]

OWNER_FILE = "ectt.project"


@dataclass(frozen=True, order=True)
class DanglingReference:
    """One stored reference that does not resolve to a usable target.

    ``reason``: ``missing_target`` (does not exist), ``not_a_directory``,
    ``outside_project`` (escapes the root), ``invalid_path`` (not a relative
    POSIX path) or ``unresolvable`` (the filesystem cannot resolve it, for
    example a symlink loop).
    """

    owner: str
    kind: str
    target: str
    required: bool
    reason: str


def _classify(root: Path, rel: str) -> str | None:
    """Return the failure reason for one stored path, or None when it resolves to a directory."""
    try:
        normalized = validate_project_path(rel)
    except InvalidRelativePathError:
        return "invalid_path"
    try:
        target = resolve_project_path(root, normalized)
    except ProjectConfinementError:
        return "outside_project"
    except (OSError, RuntimeError):
        return "unresolvable"
    try:
        if not target.exists():
            return "missing_target"
        if not target.is_dir():
            return "not_a_directory"
    except (OSError, RuntimeError):
        return "unresolvable"
    return None


def find_dangling_references(
    root: Path,
    source_roots: Sequence[str],
    output_root: str | None,
) -> tuple[DanglingReference, ...]:
    """Resolve every stored reference under ``root`` and return the failures, sorted.

    Sorting follows the field order of ``DanglingReference``, so the output is the
    same for the same project on every run.

    Implements: DSN-PRJ-050. Satisfies: TOOL-PRJ-090.
    """
    found: list[DanglingReference] = []

    for rel in source_roots:
        reason = _classify(root, rel)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="source_root", target=rel, required=True, reason=reason)
            )

    if output_root:
        reason = _classify(root, output_root)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="output_root", target=output_root, required=False, reason=reason)
            )

    return tuple(sorted(found))
