"""Untrusted-project trust decisions and warnings (WP-SEC-03).

Before executing user-supplied code — test cases, stub bodies, build
scripts, extension modules — the tool warns when the project has not been
opened before. Trust is bound to the project's content: the record stores a
digest of every file under the project, so a change to any of them (for
example after a ``git pull``) makes the project untrusted again. The record
is a deterministic, sorted JSON file under user control; the decision surface
is what the command layer consults before running anything.

Satisfies: TOOL-SEC-050.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.sec.errors import SecError

__all__ = [
    "TRUST_RECORD_SCHEMA_VERSION",
    "TrustDecision",
    "TrustRecordError",
    "UntrustedProjectTracker",
    "content_digest",
    "warning_text",
]

TRUST_RECORD_SCHEMA_VERSION = 2

# Schema 1 recorded paths only, with no content binding. It is accepted on
# read so an old record does not break the tool, but it trusts nothing: every
# project in it is untrusted until it is opened again under schema 2.
_READABLE_SCHEMA_VERSIONS = (1, 2)

_CODE_KINDS = ("test cases", "stub bodies", "build scripts", "extension modules")

_SKIP_DIRS = frozenset({".git", ".venv", "__pycache__"})


class TrustRecordError(SecError):
    """Raised when the trust record file is malformed."""

    def __init__(
        self,
        message: str,
        *,
        reason: str = "trust_record_error",
        path: Path | str | None = None,
    ) -> None:
        super().__init__(message, reason=reason, path=path)


@dataclass(frozen=True)
class TrustDecision:
    """The outcome of consulting the trust record for one project."""

    project_root: str
    known: bool

    @property
    def requires_warning(self) -> bool:
        """Whether user-code execution must be preceded by the warning."""
        return not self.known


def warning_text(decision: TrustDecision) -> str:
    """The warning shown before executing user code from an untrusted project."""
    return (
        f"Warning: project '{decision.project_root}' has not been opened with "
        f"this tool before, or its contents changed since it was last opened. "
        f"Running it will execute user-supplied code "
        f"({', '.join(_CODE_KINDS)}). Review the project, then confirm to "
        f"continue."
    )


def _normalise(root: Path | str) -> str:
    return Path(root).resolve().as_posix()


def content_digest(root: Path | str, *, exclude: Path | str | None = None) -> str:
    """SHA-256 over every file under ``root``, in a fixed order.

    ``exclude`` names one file to leave out (the trust record itself, which
    lives in some projects and changes whenever the project is marked
    opened). Build and VCS caches are skipped because they change on every
    run and carry no user code.
    """
    base = Path(root).resolve()
    skip = Path(exclude).resolve() if exclude is not None else None
    entries: list[tuple[str, Path]] = []
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(base)
        if any(part in _SKIP_DIRS for part in relative.parts):
            continue
        if skip is not None and path.resolve() == skip:
            continue
        entries.append((relative.as_posix(), path))
    digest = hashlib.sha256()
    for relative_name, file_path in sorted(entries):
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        digest.update(f"{relative_name}\0{file_hash}\n".encode())
    return digest.hexdigest()


class UntrustedProjectTracker:
    """Consults and maintains the persisted record of opened projects."""

    def __init__(self, record_path: Path | str) -> None:
        self._record_path = Path(record_path)

    def _load(self) -> dict[str, Any]:
        try:
            text = self._record_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {
                "schema_version": TRUST_RECORD_SCHEMA_VERSION,
                "projects": [],
                "digests": {},
            }
        except OSError as exc:
            raise TrustRecordError(
                f"cannot read trust record: {exc}",
                path=self._record_path,
            ) from exc
        try:
            document = json.loads(text)
        except json.JSONDecodeError as exc:
            raise TrustRecordError(
                f"trust record is not valid JSON: {exc}",
                path=self._record_path,
            ) from exc
        if not isinstance(document, dict) or not isinstance(
            document.get("projects"), list
        ):
            raise TrustRecordError(
                "trust record must be an object with a 'projects' list",
                path=self._record_path,
            )
        if document.get("schema_version") not in _READABLE_SCHEMA_VERSIONS:
            raise TrustRecordError(
                f"trust record schema {document.get('schema_version')!r} is not supported",
                path=self._record_path,
            )
        digests = document.get("digests", {})
        if not isinstance(digests, dict):
            raise TrustRecordError(
                "trust record 'digests' must be an object",
                path=self._record_path,
            )
        document["digests"] = digests
        return document

    def decision(self, project_root: Path | str) -> TrustDecision:
        """Trusted only if the project is recorded AND its contents are unchanged."""
        root = _normalise(project_root)
        document = self._load()
        if root not in document["projects"] or not Path(root).is_dir():
            return TrustDecision(project_root=root, known=False)
        current = content_digest(root, exclude=self._record_path)
        known = document["digests"].get(root) == current
        return TrustDecision(project_root=root, known=known)

    def mark_opened(self, project_root: Path | str) -> TrustDecision:
        """Persist the project as opened with its current content digest."""
        root = _normalise(project_root)
        if not Path(root).is_dir():
            raise TrustRecordError(
                f"cannot trust '{root}': it is not a directory",
                path=self._record_path,
            )
        document = self._load()
        projects = list(document["projects"])
        if root not in projects:
            projects.append(root)
        projects.sort()
        digests = dict(document["digests"])
        digests[root] = content_digest(root, exclude=self._record_path)
        document["schema_version"] = TRUST_RECORD_SCHEMA_VERSION
        document["projects"] = projects
        document["digests"] = dict(sorted(digests.items()))
        text = json.dumps(document, indent=2, sort_keys=True) + "\n"
        self._record_path.parent.mkdir(parents=True, exist_ok=True)
        self._record_path.write_text(text, encoding="utf-8")
        return TrustDecision(project_root=root, known=True)
