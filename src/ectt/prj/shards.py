"""Diff-stable sharded project storage (WP-PRJ-02).

TOOL-PRJ-060: project data shall be structured so concurrent edits by
multiple users produce localized, resolvable version-control conflicts
rather than whole-file conflicts. The shard store maps independent concerns
to independent plain-text files under ``shards/``: editing one concern
touches one file.

Writes are diff-stable: an unchanged shard is left byte-identical (no diff
churn, no mtime noise), and a changed shard is rewritten atomically
(temp file + ``os.replace``), matching the project store's write discipline
(TOOL-PRJ-050).

TOOL-PRJ-030 (open earlier-version projects or report precisely why not)
is discharged by the schema dispatch/migration layer already tested under
``tests/prj/test_schema_dispatch.py`` and ``tests/prj/test_migration.py``;
this module does not duplicate it.

Satisfies: TOOL-PRJ-060.
Design: SDD-003 (project store layout), ADR-002 (plain-text YAML).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from ectt.prj.errors import InvalidRelativePathError

__all__ = [
    "ShardStore",
]

_SHARD_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ShardStore:
    """File-per-concern plain-text shards under ``<root>/shards``.

    One shard per concern is what makes concurrent edits localize: two users
    editing different shards touch different files, so the VCS merges or
    flags per shard, never per whole project.
    """

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root)
        self._shard_dir = self._root / "shards"

    def shard_path(self, name: str) -> Path:
        """Return the file path of shard ``name`` (validated, project-relative)."""
        if not _SHARD_NAME.match(name):
            raise InvalidRelativePathError(
                f"invalid shard name: {name!r}",
                reason="invalid_shard_name",
                path=name,
            )
        return self._shard_dir / f"{name}.yaml"

    def read_shard(self, name: str) -> str | None:
        """Return the shard's text, or ``None`` when the shard does not exist."""
        path = self.shard_path(name)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None

    def write_shard(self, name: str, content: str) -> bool:
        """Write ``content`` to shard ``name``; return whether bytes changed.

        Diff stability: an unchanged shard is not rewritten at all, so a run
        that touches every shard still diffs as only the shards whose
        meaning changed.
        """
        path = self.shard_path(name)
        try:
            previous = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            previous = None
        if previous == content:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".yaml.tmp")
        tmp.write_text(content, encoding="utf-8", newline="")
        os.replace(tmp, path)
        return True
