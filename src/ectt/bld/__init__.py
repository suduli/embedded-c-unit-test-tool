"""ECTT Build Orchestration.

Provides the incremental rebuild planner: content-based staleness decisions
for build artifacts, with recorded reasons and deterministic output.
"""

from ectt.bld.errors import (
    BldError,
    DuplicateArtifactError,
    InvalidArtifactSpecError,
)
from ectt.bld.plan import (
    REASON_CONFIG_CHANGED,
    REASON_FLAGS_CHANGED,
    REASON_NO_RECORD,
    REASON_SOURCE_CHANGED,
    ArtifactSpec,
    BuildRecord,
    IncrementalPlanner,
    RebuildDecision,
)

__all__ = [
    # Errors
    "BldError",
    "DuplicateArtifactError",
    "InvalidArtifactSpecError",
    # Planning
    "REASON_NO_RECORD",
    "REASON_SOURCE_CHANGED",
    "REASON_CONFIG_CHANGED",
    "REASON_FLAGS_CHANGED",
    "ArtifactSpec",
    "BuildRecord",
    "RebuildDecision",
    "IncrementalPlanner",
]
