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
from ectt.tch.cross import (
    CROSS_CONFIG_NAMES,
    SHIPPED_CONFIG_NAMES,
    ensure_roster_complete,
    register_cross_builtins,
    shipped_cross_configs,
    shipped_roster,
)
from ectt.tch.environment import (
    STATUS_MISSING,
    STATUS_OK,
    STATUS_UNSUPPORTED,
    EnvironmentCheckResult,
    EnvironmentReport,
    EnvironmentRequirement,
    first_run_needed,
    verify_environment,
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
from ectt.tch.gating import (
    FEATURE_VERSION_REQUIREMENTS,
    MetricGate,
    UnknownFeatureError,
    UnsupportedMetricError,
    VersionGate,
    VersionRequirementError,
    check_version,
    gate_metrics,
    parse_compiler_version,
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
    # Environment verification (WP-TCH-07)
    "STATUS_OK",
    "STATUS_MISSING",
    "STATUS_UNSUPPORTED",
    "EnvironmentRequirement",
    "EnvironmentReport",
    "EnvironmentCheckResult",
    "verify_environment",
    "first_run_needed",
    # Capability & version gating (WP-TCH-04)
    "FEATURE_VERSION_REQUIREMENTS",
    "MetricGate",
    "VersionGate",
    "UnsupportedMetricError",
    "VersionRequirementError",
    "UnknownFeatureError",
    "gate_metrics",
    "check_version",
    "parse_compiler_version",
    # Cross-toolchain support (WP-TCH-03)
    "CROSS_CONFIG_NAMES",
    "SHIPPED_CONFIG_NAMES",
    "shipped_cross_configs",
    "shipped_roster",
    "register_cross_builtins",
    "ensure_roster_complete",
]
