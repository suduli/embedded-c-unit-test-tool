# implements: DSN-CORE-010, DSN-CORE-060
"""ECTT Core Platform Services.

Provides determinism, canonical serialization, filesystem isolation,
output confinement, and source immutability.
"""

from ectt.core.determinism import (
    Clock,
    FixedClock,
    SystemClock,
    canonical_bytes,
    canonical_float_repr,
    canonical_json,
    canonical_json_bytes,
    canonical_text,
    canonicalize,
    neutralize_hash_seed,
    stable_id,
)
from ectt.core.fs import (
    DEFAULT_OUTPUT_REL_PATH,
    GITIGNORE_FILENAME,
    MARKER_FILENAME,
    CoreError,
    CoreFsError,
    OutputRoot,
    PathConfinementError,
    RootOverlapError,
    SourceMutationError,
    SourceTree,
    UnmarkedOutputRootError,
)

__all__ = [
    # Determinism
    "Clock",
    "SystemClock",
    "FixedClock",
    "stable_id",
    "canonical_float_repr",
    "canonicalize",
    "canonical_text",
    "canonical_bytes",
    "canonical_json",
    "canonical_json_bytes",
    "neutralize_hash_seed",
    # Filesystem & Confinement
    "DEFAULT_OUTPUT_REL_PATH",
    "MARKER_FILENAME",
    "GITIGNORE_FILENAME",
    "CoreError",
    "CoreFsError",
    "RootOverlapError",
    "PathConfinementError",
    "SourceMutationError",
    "UnmarkedOutputRootError",
    "OutputRoot",
    "SourceTree",
]
