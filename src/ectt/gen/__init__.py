"""ECTT Harness Generation.

Provides the framework-agnostic harness generation core: UUT selection from an
analysis model, exposure of non-static functions, global access records, and
per-test setup/teardown hooks.
"""

from ectt.gen.backends import (
    CMOCKA_BACKEND_ID,
    UNITY_BACKEND_ID,
    BackendRegistry,
    CppConstructInOutputError,
    DuplicateBackendError,
    FrameworkBackend,
    FrameworkBackendError,
    UnknownBackendError,
    register_framework_builtins,
    render_framework_test,
)
from ectt.gen.errors import (
    AmbiguousUnitError,
    GenError,
    NoUnitError,
    UnitNotParsedError,
    UnknownUnitError,
)
from ectt.gen.exposure import (
    STATIC_EXPOSURE_MARKER,
    STUB_REQUIRED_MARKER,
    IntegrationHarness,
    IntegrationScopeTooSmallError,
    generate_integration_harness,
    generate_with_statics,
)
from ectt.gen.harness import (
    UNRESOLVED_TYPE_MARKER,
    ExposedFunction,
    ExposedVariable,
    GeneratedHarness,
    HarnessGenerator,
)
from ectt.gen.regen import (
    STATUS_CONFLICT,
    STATUS_PRESERVED,
    HarnessRegenerationConflictError,
    HarnessStaleness,
    RegenerationResult,
    TestInterfaceBinding,
    apply_regeneration,
    check_harness_staleness,
    check_test_case_staleness,
    regenerate,
)

__all__ = [
    # Errors
    "GenError",
    "NoUnitError",
    "AmbiguousUnitError",
    "UnknownUnitError",
    "UnitNotParsedError",
    # Harness core
    "UNRESOLVED_TYPE_MARKER",
    "ExposedFunction",
    "ExposedVariable",
    "GeneratedHarness",
    "HarnessGenerator",
    # Framework back-ends (WP-GEN-02)
    "UNITY_BACKEND_ID",
    "CMOCKA_BACKEND_ID",
    "FrameworkBackendError",
    "CppConstructInOutputError",
    "UnknownBackendError",
    "DuplicateBackendError",
    "FrameworkBackend",
    "BackendRegistry",
    "register_framework_builtins",
    "render_framework_test",
    # Regeneration contract (WP-GEN-04)
    "STATUS_PRESERVED",
    "STATUS_CONFLICT",
    "HarnessRegenerationConflictError",
    "HarnessStaleness",
    "RegenerationResult",
    "TestInterfaceBinding",
    "apply_regeneration",
    "check_harness_staleness",
    "check_test_case_staleness",
    "regenerate",
    # Static exposure & integration harness (WP-GEN-03)
    "STATIC_EXPOSURE_MARKER",
    "STUB_REQUIRED_MARKER",
    "IntegrationHarness",
    "IntegrationScopeTooSmallError",
    "generate_integration_harness",
    "generate_with_statics",
]
