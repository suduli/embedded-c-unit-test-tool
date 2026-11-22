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
from ectt.core.docindex import (
    STATUS_PENDING,
    STATUS_SHIPPED,
    DocEntry,
    DocIndexError,
    UserDocumentationIndex,
    documentation_index,
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
from ectt.core.logging import (
    DiagnosticBundle,
    EcttLogger,
    LogRecord,
    Verbosity,
    build_diagnostic_bundle,
)
from ectt.core.platform import (
    NETWORK_MODULES,
    VALIDATED_PLATFORMS,
    OfflineViolationError,
    Platform,
    PlatformError,
    assert_offline,
    current_platform,
    detect_platform,
    executable_suffix,
    find_network_imports,
    platform_report,
)
from ectt.core.selfverify import (
    SelfVerification,
    SelfVerificationError,
    verify_tree,
    write_manifest,
)
from ectt.core.text import (
    DEFAULT_CATALOG_NAME,
    MessageCatalog,
    TextFormatError,
    UnknownMessageKeyError,
    default_catalog,
)

__all__ = [
    # Self-verification (WP-CORE-08)
    "SelfVerification",
    "SelfVerificationError",
    "verify_tree",
    "write_manifest",
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
    # Logging & diagnostic bundle (WP-CORE-06)
    "Verbosity",
    "LogRecord",
    "EcttLogger",
    "DiagnosticBundle",
    "build_diagnostic_bundle",
    # Text externalisation & documentation index (WP-CORE-07)
    "DEFAULT_CATALOG_NAME",
    "MessageCatalog",
    "TextFormatError",
    "UnknownMessageKeyError",
    "default_catalog",
    "STATUS_PENDING",
    "STATUS_SHIPPED",
    "DocEntry",
    "DocIndexError",
    "UserDocumentationIndex",
    "documentation_index",
    "OutputRoot",
    "SourceTree",
    # Platform baseline & offline guarantee (WP-CORE-03)
    "NETWORK_MODULES",
    "VALIDATED_PLATFORMS",
    "Platform",
    "PlatformError",
    "OfflineViolationError",
    "assert_offline",
    "current_platform",
    "detect_platform",
    "executable_suffix",
    "find_network_imports",
    "platform_report",
]
