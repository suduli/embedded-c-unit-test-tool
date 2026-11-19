"""Capability declaration gating and compiler version gating (WP-TCH-04).

Metric requests are gated against what a compiler configuration declares it
can deliver (TOOL-TCH-060), and feature requests are gated against the
compiler version using the documented requirement table (TOOL-TCH-070 —
MC/DC requires GCC ≥ 14 or Clang ≥ 18). Versions are parsed from real
compiler-version output text.

Satisfies: TOOL-TCH-060, TOOL-TCH-070.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from ectt.tch.config import CompilerConfig
from ectt.tch.errors import TchError

__all__ = [
    "FEATURE_VERSION_REQUIREMENTS",
    "UnsupportedMetricError",
    "VersionRequirementError",
    "UnknownFeatureError",
    "MetricGate",
    "VersionGate",
    "gate_metrics",
    "check_version",
    "parse_compiler_version",
]

# The documented per-feature minimum versions, per compiler family
# (TOOL-TCH-070: MC/DC requires GCC ≥ 14 or Clang ≥ 18).
FEATURE_VERSION_REQUIREMENTS: Mapping[str, Mapping[str, tuple[int, int]]] = {
    "mcdc": {"gcc": (14, 0), "clang": (18, 0)},
}

_VERSION_IN_OUTPUT = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


class UnsupportedMetricError(TchError):
    """Raised when a coverage metric is not declared by the configuration."""

    def __init__(self, message: str, *, reason: str = "unsupported_metric") -> None:
        super().__init__(message, reason=reason)


class VersionRequirementError(TchError):
    """Raised when the compiler version cannot support a requested feature."""

    def __init__(self, message: str, *, reason: str = "version_requirement") -> None:
        super().__init__(message, reason=reason)


class UnknownFeatureError(TchError):
    """Raised when a feature has no documented version requirement."""

    def __init__(self, message: str, *, reason: str = "unknown_feature") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class MetricGate:
    """The verdict of one metric request against one configuration."""

    config: str
    granted: tuple[str, ...]
    refused: tuple[str, ...]


@dataclass(frozen=True)
class VersionGate:
    """The verdict of one feature request against one compiler version."""

    feature: str
    family: str
    version: tuple[int, int]
    supported: bool
    message: str


def gate_metrics(
    config: CompilerConfig, requested: tuple[str, ...]
) -> MetricGate:
    """Gate the requested coverage kinds against the declared kinds (TCH-060)."""
    granted: list[str] = []
    refused: list[str] = []
    for kind in requested:
        if kind in config.coverage_kinds:
            granted.append(kind)
        else:
            refused.append(kind)
    if refused:
        raise UnsupportedMetricError(
            f"configuration '{config.name}' does not declare coverage kind(s) "
            f"{', '.join(sorted(refused))}; declared: "
            f"{', '.join(sorted(config.coverage_kinds))}"
        )
    return MetricGate(config=config.name, granted=tuple(granted), refused=())


def parse_compiler_version(output_text: str) -> tuple[int, int]:
    """Parse the version tuple from compiler-version output text."""
    match = _VERSION_IN_OUTPUT.search(output_text)
    if match is None:
        raise VersionRequirementError(
            f"no version number found in compiler output: {output_text.strip()[:60]!r}"
        )
    return int(match.group(1)), int(match.group(2))


def check_version(feature: str, family: str, version_text: str) -> VersionGate:
    """Non-raising feature gate: is this version sufficient for the feature?"""
    requirements = FEATURE_VERSION_REQUIREMENTS.get(feature)
    if requirements is None:
        raise UnknownFeatureError(
            f"feature '{feature}' has no documented version requirement"
        )
    minimum = requirements.get(family)
    if minimum is None:
        raise UnknownFeatureError(
            f"feature '{feature}' has no documented requirement for compiler "
            f"family '{family}'"
        )
    version = parse_compiler_version(version_text)
    supported = version >= minimum
    if supported:
        message = (
            f"{family} {version[0]}.{version[1]} supports {feature} "
            f"(requires >= {minimum[0]}.{minimum[1]})"
        )
    else:
        message = (
            f"{family} {version[0]}.{version[1]} does not support {feature}; "
            f"requires >= {minimum[0]}.{minimum[1]}"
        )
    return VersionGate(
        feature=feature,
        family=family,
        version=version,
        supported=supported,
        message=message,
    )
