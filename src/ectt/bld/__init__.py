"""ECTT Build Orchestration.

Provides the incremental rebuild planner: content-based staleness decisions
for build artifacts, with recorded reasons and deterministic output.
"""

from ectt.bld.errors import (
    BldError,
    DuplicateArtifactError,
    InvalidArtifactSpecError,
    InvalidSanitizerModeError,
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
from ectt.bld.sanitize import (
    KNOWN_SANITIZER_MODES,
    SANITIZER_ADDRESS,
    SANITIZER_NONE,
    SANITIZER_UNDEFINED,
    SanitizerFinding,
    SanitizerSettings,
    classify_run_output,
    sanitizer_compile_flags,
    sanitizer_runtime_env,
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
    # Sanitizer integration
    "InvalidSanitizerModeError",
    "SANITIZER_NONE",
    "SANITIZER_ADDRESS",
    "SANITIZER_UNDEFINED",
    "KNOWN_SANITIZER_MODES",
    "SanitizerSettings",
    "SanitizerFinding",
    "sanitizer_compile_flags",
    "sanitizer_runtime_env",
    "classify_run_output",
]
