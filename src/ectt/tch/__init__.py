"""ECTT Toolchain abstraction.

Provides the declarative compiler configuration format, its loader and
validator, and the compiler configuration registry.
"""

from ectt.tch.config import (
    CONFIG_SCHEMA_VERSION,
    KNOWN_COVERAGE_KINDS,
    CompilerConfig,
    CompilerConfigRegistry,
    InvocationSpec,
    OutputSpec,
    load_compiler_config,
    validate_compiler_config_document,
)
from ectt.tch.errors import (
    CompilerConfigReadError,
    ConfigSchemaVersionError,
    DuplicateCompilerConfigError,
    InvalidCompilerConfigError,
    TchError,
    UnknownCompilerConfigError,
    UnknownCoverageKindError,
)

__all__ = [
    # Errors
    "TchError",
    "CompilerConfigReadError",
    "InvalidCompilerConfigError",
    "ConfigSchemaVersionError",
    "UnknownCoverageKindError",
    "DuplicateCompilerConfigError",
    "UnknownCompilerConfigError",
    # Format
    "CONFIG_SCHEMA_VERSION",
    "KNOWN_COVERAGE_KINDS",
    "InvocationSpec",
    "OutputSpec",
    "CompilerConfig",
    "CompilerConfigRegistry",
    "load_compiler_config",
    "validate_compiler_config_document",
]
