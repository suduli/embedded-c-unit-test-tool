"""ECTT Harness Generation.

Provides the framework-agnostic harness generation core: UUT selection from an
analysis model, exposure of non-static functions, global access records, and
per-test setup/teardown hooks.
"""

from ectt.gen.errors import (
    AmbiguousUnitError,
    GenError,
    NoUnitError,
    UnitNotParsedError,
    UnknownUnitError,
)
from ectt.gen.harness import (
    UNRESOLVED_TYPE_MARKER,
    ExposedFunction,
    ExposedVariable,
    GeneratedHarness,
    HarnessGenerator,
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
]
