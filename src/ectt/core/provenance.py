"""Provenance record and version identification (WP-CORE-04, TASK-013).

Every generated artifact should say what produced it, so that the same inputs and
the same tool can reproduce it (TOOL-QUA-060), and so the tool can report its own
identity on request (TOOL-INS-110).

The record separates two parts. The hashed portion holds only deterministic facts:
tool version, build identifier, interpreter version, dependency versions, schema
versions and input digests. Its digest is stable across runs and machines that
share those facts. The wall-clock ``generated_at`` is carried beside the digest and
is never hashed, so it cannot make two identical productions look different.

This module is in ``core`` and must not import the analysis or ingestion layers.
Callers supply the library versions they know, such as libclang.

Satisfies: TOOL-QUA-060, TOOL-INS-110.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import platform
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ectt.core.determinism import Clock, canonical_json_bytes

__all__ = [
    "BUILD_ID_ENV",
    "UNKNOWN_BUILD_ID",
    "ProvenanceRecord",
    "build_provenance",
    "tool_version",
    "version_report",
]

BUILD_ID_ENV: str = "ECTT_BUILD_ID"
UNKNOWN_BUILD_ID: str = "unset"
_PACKAGE = "ectt"


def tool_version() -> str:
    """Version of the installed ``ectt`` distribution, or ``"unknown"`` when it is not installed.

    The source-tree ``__version__`` is not used as a substitute: a version the
    installation cannot prove is never reported as fact.
    """
    try:
        return importlib.metadata.version(_PACKAGE)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _build_id() -> str:
    """Build identifier supplied by the build that produced this installation.

    Read from the environment at call time; absent means the build did not record one.
    """
    value = os.environ.get(BUILD_ID_ENV, "").strip()
    return value or UNKNOWN_BUILD_ID


def _sorted_str_map(values: Mapping[str, str] | None) -> dict[str, str]:
    return {str(k): str(v) for k, v in sorted((values or {}).items())}


@dataclass(frozen=True)
class ProvenanceRecord:
    """What produced an artifact. ``generated_at`` is informational and is not hashed."""

    tool_version: str
    build_id: str
    python_version: str
    dependencies: Mapping[str, str] = field(default_factory=dict)
    schema_versions: Mapping[str, str] = field(default_factory=dict)
    input_digests: Mapping[str, str] = field(default_factory=dict)
    generated_at: str | None = None

    def hashed_portion(self) -> dict[str, Any]:
        """The deterministic facts. Excludes ``generated_at`` by design."""
        return {
            "tool_version": self.tool_version,
            "build_id": self.build_id,
            "python_version": self.python_version,
            "dependencies": _sorted_str_map(self.dependencies),
            "schema_versions": _sorted_str_map(self.schema_versions),
            "input_digests": _sorted_str_map(self.input_digests),
        }

    @property
    def digest(self) -> str:
        """SHA-256 over the canonical encoding of the hashed portion."""
        return hashlib.sha256(canonical_json_bytes(self.hashed_portion())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Full record: hashed portion, its digest, and the informational timestamp when present."""
        result: dict[str, Any] = {"digest": self.digest, **self.hashed_portion()}
        if self.generated_at is not None:
            result["generated_at"] = self.generated_at
        return result


def build_provenance(
    *,
    clock: Clock | None = None,
    dependencies: Mapping[str, str] | None = None,
    schema_versions: Mapping[str, str] | None = None,
    input_digests: Mapping[str, str] | None = None,
) -> ProvenanceRecord:
    """Assemble the provenance of an artifact being generated now.

    ``clock`` supplies the informational timestamp only. Passing no clock leaves it
    out, which keeps a record fully deterministic.

    Satisfies: TOOL-QUA-060.
    """
    return ProvenanceRecord(
        tool_version=tool_version(),
        build_id=_build_id(),
        python_version=platform.python_version(),
        dependencies=dict(dependencies or {}),
        schema_versions=dict(schema_versions or {}),
        input_digests=dict(input_digests or {}),
        generated_at=clock.isoformat() if clock is not None else None,
    )


def version_report(*, dependencies: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Identity of this tool and its principal dependencies, for a version request.

    Satisfies: TOOL-INS-110.
    """
    return {
        "tool": _PACKAGE,
        "tool_version": tool_version(),
        "build_id": _build_id(),
        "python_version": platform.python_version(),
        "dependencies": _sorted_str_map(dependencies),
    }
