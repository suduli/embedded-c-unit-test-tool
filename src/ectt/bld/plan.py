"""Incremental rebuild planning (WP-BLD-01).

Decides, from requested artifact specifications and the records of a previous
build, exactly which artifacts must be recompiled and why. An artifact is up
to date when a record exists with the same source content digest, the same
compiler configuration and the same flag tuple; every other difference
schedules a rebuild with a recorded reason.

Staleness is content-based: digests, not mtimes, so planning is a pure
function of (requested specs, prior records) and identical inputs yield
byte-identical plans.

Satisfies: TOOL-EXE-080.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ectt.bld.errors import DuplicateArtifactError, InvalidArtifactSpecError

__all__ = [
    "REASON_NO_RECORD",
    "REASON_SOURCE_CHANGED",
    "REASON_CONFIG_CHANGED",
    "REASON_FLAGS_CHANGED",
    "ArtifactSpec",
    "BuildRecord",
    "RebuildDecision",
    "IncrementalPlanner",
]

REASON_NO_RECORD = "no_record"
REASON_SOURCE_CHANGED = "source_changed"
REASON_CONFIG_CHANGED = "config_changed"
REASON_FLAGS_CHANGED = "flags_changed"


def _require_nonempty(value: str, what: str, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InvalidArtifactSpecError(
            f"artifact '{path}' has an invalid {what}",
            path=path,
        )


@dataclass(frozen=True)
class ArtifactSpec:
    """One artifact the build must produce.

    - ``output_path``   the artifact file the build writes
    - ``source_path``   the primary source the artifact is compiled from
    - ``source_digest`` content digest of the source (sha256 hex or equivalent)
    - ``compiler``      compiler configuration name (WP-TCH-01 registry entry)
    - ``flags``         the exact flag tuple used for the compilation
    """

    output_path: str
    source_path: str
    source_digest: str
    compiler: str
    flags: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in ("output_path", "source_path", "source_digest", "compiler"):
            _require_nonempty(getattr(self, field_name), field_name, self.output_path)
        for flag in self.flags:
            if not isinstance(flag, str) or not flag.strip():
                raise InvalidArtifactSpecError(
                    f"artifact '{self.output_path}' has a non-string flag",
                    path=self.output_path,
                )

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "compiler": self.compiler,
            "flags": list(self.flags),
            "output_path": self.output_path,
            "source_digest": self.source_digest,
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class BuildRecord:
    """What was recorded the last time an artifact was built."""

    source_digest: str
    compiler: str
    flags: tuple[str, ...]


@dataclass(frozen=True)
class RebuildDecision:
    """The planner's verdict for one requested artifact."""

    spec: ArtifactSpec
    rebuild: bool
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "reasons": list(self.reasons),
            "rebuild": self.rebuild,
            "spec": self.spec.to_dict(),
        }


class IncrementalPlanner:
    """Plans which artifacts to recompile from prior build records."""

    def __init__(self, records: Mapping[str, BuildRecord] | None = None) -> None:
        self._records: dict[str, BuildRecord] = dict(records or {})

    def record(self, output_path: str, record: BuildRecord) -> None:
        """Record a completed build for one output path."""
        self._records[output_path] = record

    def plan(self, specs: tuple[ArtifactSpec, ...]) -> tuple[RebuildDecision, ...]:
        """Return one decision per spec, ordered by output path."""
        seen: set[str] = set()
        for spec in specs:
            if spec.output_path in seen:
                raise DuplicateArtifactError(
                    f"two artifacts claim output path '{spec.output_path}'",
                    path=spec.output_path,
                )
            seen.add(spec.output_path)
        decisions = [self._decide(spec) for spec in sorted(specs, key=lambda item: item.output_path)]
        return tuple(decisions)

    def _decide(self, spec: ArtifactSpec) -> RebuildDecision:
        record = self._records.get(spec.output_path)
        if record is None:
            return RebuildDecision(
                spec=spec, rebuild=True, reasons=(REASON_NO_RECORD,)
            )
        reasons: list[str] = []
        if record.source_digest != spec.source_digest:
            reasons.append(REASON_SOURCE_CHANGED)
        if record.compiler != spec.compiler:
            reasons.append(REASON_CONFIG_CHANGED)
        if record.flags != spec.flags:
            reasons.append(REASON_FLAGS_CHANGED)
        if reasons:
            return RebuildDecision(spec=spec, rebuild=True, reasons=tuple(reasons))
        return RebuildDecision(spec=spec, rebuild=False, reasons=())
