"""Untrusted-project trust decisions and warnings (WP-SEC-03).

Before executing user-supplied code — test cases, stub bodies, build
scripts — the tool warns when the project has not been opened before. The
trust record is a deterministic, sorted JSON file under user control; the
decision surface is what the command layer consults before running anything.

Satisfies: TOOL-SEC-050.
"""

from __future__ import annotations

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
    "warning_text",
]

TRUST_RECORD_SCHEMA_VERSION = 1

_CODE_KINDS = ("test cases", "stub bodies", "build scripts")


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
        f"this tool before. Running it will execute user-supplied code "
        f"({', '.join(_CODE_KINDS)}). Review the project, then confirm to "
        f"continue."
    )


def _normalise(root: Path | str) -> str:
    return Path(root).resolve().as_posix()


class UntrustedProjectTracker:
    """Consults and maintains the persisted record of opened projects."""

    def __init__(self, record_path: Path | str) -> None:
        self._record_path = Path(record_path)

    def _load(self) -> dict[str, Any]:
        try:
            text = self._record_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {"schema_version": TRUST_RECORD_SCHEMA_VERSION, "projects": []}
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
        return document

    def decision(self, project_root: Path | str) -> TrustDecision:
        """Whether the project is known (previously opened) or untrusted."""
        root = _normalise(project_root)
        document = self._load()
        known = root in document["projects"]
        return TrustDecision(project_root=root, known=known)

    def mark_opened(self, project_root: Path | str) -> TrustDecision:
        """Persist the project as opened; idempotent per project."""
        root = _normalise(project_root)
        document = self._load()
        projects = list(document["projects"])
        if root not in projects:
            projects.append(root)
        projects.sort()
        document["schema_version"] = TRUST_RECORD_SCHEMA_VERSION
        document["projects"] = projects
        text = json.dumps(document, indent=2, sort_keys=True) + "\n"
        self._record_path.parent.mkdir(parents=True, exist_ok=True)
        self._record_path.write_text(text, encoding="utf-8")
        return TrustDecision(project_root=root, known=True)
