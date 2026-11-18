"""ECTT Extension Points.

Provides the documented extension-point surface: descriptors for the built-in
extension seams and an open registry that accepts user-defined points without
modifying tool source.
"""

from ectt.plg.errors import (
    DuplicateExtensionPointError,
    InvalidExtensionPointError,
    PlgError,
    UnknownExtensionPointError,
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
    # Points
    "CONTRACT_COMPILER_CONFIG",
    "CONTRACT_FRAMEWORK_BACKEND",
    "CONTRACT_TARGET_EXECUTION",
    "CONTRACT_REPORT_FORMAT",
    "BUILTIN_EXTENSION_POINTS",
    "ExtensionPoint",
    "ExtensionPointRegistry",
    "default_registry",
]
