"""Coexistence with another tool on one project (WP-MIG-06).

TOOL-MIG-070: the tool shall support coexistence — operating on a project
that is also tested by another tool, without interfering with that tool's
artifacts. SDD-003 (write authorities): "Coexistence (TOOL-MIG-070)
protects existing artifacts in both roots."

The non-interference contract is mechanical here: ectt's owned authored-state
set is explicit data; everything else in the project root is foreign and
protected — detected, reported, never modified. Protection of the output
root is byte-level: callers snapshot before and after their run and assert
non-interference, which covers foreign files there without needing a
registry of ectt's own output names.

Satisfies: TOOL-MIG-070.
Design: SDD-003 (two write authorities), TOOL-PRJ-080 (generated vs
user-authored separation).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "OWNED_PROJECT_PATHS",
    "ForeignArtifact",
    "TreeSnapshot",
    "assert_no_interference",
    "scan_foreign_artifacts",
    "snapshot_tree",
]

#: Files ectt owns in the project root (authored-state side). Everything
#: else found there belongs to someone else (the user or another tool).
OWNED_PROJECT_PATHS: tuple[str, ...] = (
    "ectt.project",  # PROJECT_ROOT_MARKER
)


@dataclass(frozen=True)
class ForeignArtifact:
    """A file in the authored-state side of a project that ectt does not own."""

    path: str  # project-relative POSIX path
    root: str  # "project_root"


@dataclass(frozen=True)
class TreeSnapshot:
    """Relative path → SHA-256 digest map of a directory tree."""

    digests: dict[str, str]


def _walk_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


def snapshot_tree(root: Path) -> TreeSnapshot:
    """Digest every file under ``root`` into a deterministic snapshot."""
    digests: dict[str, str] = {}
    for path in _walk_files(root):
        rel = path.relative_to(root).as_posix()
        digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return TreeSnapshot(digests=dict(sorted(digests.items())))


def assert_no_interference(
    before: TreeSnapshot,
    after: TreeSnapshot,
    *,
    context: str,
) -> None:
    """Assert a tree snapshot is unchanged, naming the differing file.

    The coexistence guarantee is byte-level: an ectt run must not change,
    create, or delete anything it does not own — in either root.
    """
    if before.digests == after.digests:
        return
    changed = sorted(
        set(before.digests) ^ set(after.digests)
        | {key for key in before.digests if before.digests.get(key) != after.digests.get(key)}
    )
    raise AssertionError(f"ectt modified foreign artifacts in {context}: {changed}")


def scan_foreign_artifacts(
    project_root: Path,
    output_root: Path | None = None,
) -> tuple[ForeignArtifact, ...]:
    """Report foreign files in the authored state of ``project_root``.

    A file is foreign when it is not in ectt's explicit owned set and not
    inside the output-root subtree (the generated side is governed by the
    snapshot mechanism, and is also never an authored-state destination per
    SDD-003). Results are sorted for determinism; nothing is modified.
    """
    artifacts: list[ForeignArtifact] = []
    resolved_output = output_root.resolve() if output_root is not None else None
    for path in _walk_files(project_root):
        if resolved_output is not None and path.is_relative_to(resolved_output):
            continue
        rel = path.relative_to(project_root).as_posix()
        if rel in OWNED_PROJECT_PATHS:
            continue
        artifacts.append(ForeignArtifact(path=rel, root="project_root"))
    return tuple(sorted(artifacts, key=lambda a: a.path))
