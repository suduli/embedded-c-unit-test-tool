"""Extension-point definitions for ectt (WP-PLG-01).

An extension point is a named, documented seam of the tool that third parties
can extend without modifying tool source. Each extension point is described by
an immutable descriptor carrying a stable identifier, a human-readable title
and description, the interface contract a provider must implement, and an
interface version.

Satisfies: TOOL-PLG-010.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ectt.plg.errors import (
    DuplicateExtensionPointError,
    InvalidExtensionPointError,
    UnknownExtensionPointError,
)

__all__ = [
    "CONTRACT_COMPILER_CONFIG",
    "CONTRACT_FRAMEWORK_BACKEND",
    "CONTRACT_TARGET_EXECUTION",
    "CONTRACT_REPORT_FORMAT",
    "BUILTIN_EXTENSION_POINTS",
    "ExtensionPoint",
    "ExtensionPointRegistry",
    "default_registry",
]

# Standard contract names. The set is open: a new extension point may declare
# any non-empty contract name, which keeps the registry usable without
# modifying tool source.
CONTRACT_COMPILER_CONFIG = "compiler_config"
CONTRACT_FRAMEWORK_BACKEND = "framework_backend"
CONTRACT_TARGET_EXECUTION = "target_execution"
CONTRACT_REPORT_FORMAT = "report_format"

_VERSION_RE = re.compile(r"^[0-9]+(\.[0-9]+)*$")


@dataclass(frozen=True)
class ExtensionPoint:
    """Immutable description of one extension point.

    - ``point_id``          stable identifier, e.g. ``"compiler_configs"``
    - ``title``             short human-readable name
    - ``description``       one-paragraph documentation of the seam
    - ``contract``          name of the provider contract this point hands out
    - ``interface_version`` dotted integer version of the provider contract
    """

    point_id: str
    title: str
    description: str
    contract: str
    interface_version: str


def _validate(point: ExtensionPoint) -> None:
    for field in (
        "point_id",
        "title",
        "description",
        "contract",
        "interface_version",
    ):
        value = getattr(point, field)
        if not isinstance(value, str):
            raise InvalidExtensionPointError(
                f"extension point field '{field}' must be a string, "
                f"got {type(value).__name__}"
            )
        if not value.strip():
            raise InvalidExtensionPointError(
                f"extension point field '{field}' must not be empty or whitespace"
            )
    if not _VERSION_RE.match(point.interface_version):
        raise InvalidExtensionPointError(
            f"extension point '{point.point_id}' interface_version "
            f"'{point.interface_version}' must be a dotted integer version "
            f"(for example '1' or '1.0')"
        )


BUILTIN_EXTENSION_POINTS: tuple[ExtensionPoint, ...] = (
    ExtensionPoint(
        point_id="compiler_configs",
        title="Compiler configurations",
        description=(
            "Declarative compiler configuration files describing invocation, "
            "flag syntax, output conventions and supported coverage kinds for "
            "a C compiler."
        ),
        contract=CONTRACT_COMPILER_CONFIG,
        interface_version="1",
    ),
    ExtensionPoint(
        point_id="framework_backends",
        title="Test framework back-ends",
        description=(
            "Template-driven back-ends that render a generated harness onto a "
            "specific C test framework such as Unity or cmocka."
        ),
        contract=CONTRACT_FRAMEWORK_BACKEND,
        interface_version="1",
    ),
    ExtensionPoint(
        point_id="target_execution_methods",
        title="Target execution methods",
        description=(
            "Execution methods that run a built test harness on a target, "
            "from an instruction-set simulator to a debug probe or a "
            "user-supplied flashing and communication script."
        ),
        contract=CONTRACT_TARGET_EXECUTION,
        interface_version="1",
    ),
    ExtensionPoint(
        point_id="report_formats",
        title="Report formats",
        description=(
            "Renderers that consume the documented intermediate report model "
            "and produce an output format, without re-executing tests."
        ),
        contract=CONTRACT_REPORT_FORMAT,
        interface_version="1",
    ),
)


class ExtensionPointRegistry:
    """A named set of extension points, open to user registration."""

    def __init__(self) -> None:
        self._points: dict[str, ExtensionPoint] = {}

    @classmethod
    def with_builtins(cls) -> ExtensionPointRegistry:
        """A registry pre-populated with the built-in extension points."""
        registry = cls()
        for point in BUILTIN_EXTENSION_POINTS:
            registry.register(point)
        return registry

    def register(self, point: ExtensionPoint) -> None:
        """Validate and register a descriptor; reject a reused identifier."""
        _validate(point)
        if point.point_id in self._points:
            raise DuplicateExtensionPointError(
                f"extension point '{point.point_id}' is already registered"
            )
        self._points[point.point_id] = point

    def lookup(self, point_id: str) -> ExtensionPoint:
        """Return the descriptor registered under ``point_id``."""
        try:
            return self._points[point_id]
        except KeyError:
            raise UnknownExtensionPointError(
                f"no extension point is registered under '{point_id}'"
            ) from None

    def list_points(self) -> tuple[ExtensionPoint, ...]:
        """All registered descriptors, ordered deterministically by identifier."""
        return tuple(self._points[key] for key in sorted(self._points))


def default_registry() -> ExtensionPointRegistry:
    """A fresh registry containing exactly the built-in extension points.

    A new instance is returned on every call so callers cannot mutate shared
    module state.
    """
    return ExtensionPointRegistry.with_builtins()
