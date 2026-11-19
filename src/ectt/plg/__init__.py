"""ECTT Extension Points.

Provides the documented extension-point surface: descriptors for the built-in
extension seams and an open registry that accepts user-defined points without
modifying tool source.
"""

from ectt.plg.aiprovider import (
    AI_PROVIDER_CONTRACT,
    AI_PROVIDER_POINT_ID,
    AiProviderDescriptor,
    AiProviderRegistry,
    define_ai_provider_extension_point,
)
from ectt.plg.discovery import (
    KIND_IMPORT_ERROR,
    KIND_INCOMPATIBLE,
    KIND_RUNTIME_ERROR,
    KIND_SYNTAX_ERROR,
    DiscoveryReport,
    ExtensionsDirError,
    LoadFailure,
    discover_extensions,
    load_extension_file,
)
from ectt.plg.errors import (
    DuplicateAiProviderError,
    DuplicateExtensionPointError,
    IncompatibleAiProviderError,
    InvalidAiProviderError,
    InvalidExtensionPointError,
    PlgError,
    UnknownAiProviderError,
    UnknownExtensionPointError,
    UntrustedExtensionsError,
)
from ectt.plg.points import (
    BUILTIN_EXTENSION_POINTS,
    CONTRACT_COMPILER_CONFIG,
    CONTRACT_FRAMEWORK_BACKEND,
    CONTRACT_REPORT_FORMAT,
    CONTRACT_TARGET_EXECUTION,
    ExtensionPoint,
    ExtensionPointRegistry,
    default_registry,
)

__all__ = [
    # Errors
    "PlgError",
    "InvalidExtensionPointError",
    "DuplicateExtensionPointError",
    "UnknownExtensionPointError",
    "UntrustedExtensionsError",
    # Points
    "CONTRACT_COMPILER_CONFIG",
    "CONTRACT_FRAMEWORK_BACKEND",
    "CONTRACT_TARGET_EXECUTION",
    "CONTRACT_REPORT_FORMAT",
    "BUILTIN_EXTENSION_POINTS",
    "ExtensionPoint",
    "ExtensionPointRegistry",
    "default_registry",
    # AI-provider protocol (WP-PLG-04)
    "AI_PROVIDER_POINT_ID",
    "AI_PROVIDER_CONTRACT",
    "AiProviderDescriptor",
    "AiProviderRegistry",
    "define_ai_provider_extension_point",
    "InvalidAiProviderError",
    "DuplicateAiProviderError",
    "UnknownAiProviderError",
    "IncompatibleAiProviderError",
]
