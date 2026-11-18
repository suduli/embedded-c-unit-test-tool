"""ECTT Toolchain abstraction.

Provides the declarative compiler configuration format, its loader and
validator, and the compiler configuration registry.
"""

from ectt.tch.builtin import (
    CLANG_HOST_CONFIG_NAME,
    GCC_HOST_CONFIG_NAME,
    built_in_host_configs,
    register_host_builtins,
)
from ectt.tch.config import (
    CONFIG_SCHEMA_VERSION,
    KNOWN_COVERAGE_KINDS,
    CompilerConfig,
    CompilerConfigRegistry,
    InvocationSpec,
    OutputSpec,
    load_compiler_config,
    load_compiler_config_text,
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
    "load_compiler_config_text",
    "validate_compiler_config_document",
    # Built-in host compilers
    "GCC_HOST_CONFIG_NAME",
    "CLANG_HOST_CONFIG_NAME",
    "built_in_host_configs",
    "register_host_builtins",
]
