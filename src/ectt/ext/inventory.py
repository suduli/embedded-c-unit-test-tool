"""Hardware inventory and target failure classification (WP-EXT-05).

A declarative inventory describes connected targets (identifier, platform,
probe type, serial device, flash timeout). Target execution failures — flash
failure, no output, target reset, watchdog — are classified from output text
and distinguished from test failures.

Satisfies: TOOL-TGT-080, TOOL-TGT-090.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final

from ectt.ext.errors import ExtError
from ectt.ext.probe import PROBE_FAMILIES

__all__ = [
    "FAILURE_FLASH",
    "FAILURE_NO_OUTPUT",
    "FAILURE_TARGET_RESET",
    "FAILURE_WATCHDOG",
    "HardwareInventory",
    "TargetDescriptor",
    "TargetFailure",
    "UnknownTargetError",
    "classify_target_failure",
]

FAILURE_FLASH = "flash_failure"
FAILURE_NO_OUTPUT = "no_output"
FAILURE_TARGET_RESET = "target_reset"
FAILURE_WATCHDOG = "watchdog"

_SIGNATURES: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    (FAILURE_FLASH, re.compile(r"flash (?:failed|failure|error)|error.*flash(?:ing)?", re.IGNORECASE)),
    (FAILURE_TARGET_RESET, re.compile(r"target (?:reset|rebooted)| system reset\b|nvic_systemreset", re.IGNORECASE)),
    (FAILURE_WATCHDOG, re.compile(r"watchdog(?: reset| expired| timeout)?\b", re.IGNORECASE)),
)


class UnknownTargetError(ExtError):
    """Raised when an inventory record is malformed or an id is not present."""

    def __init__(self, message: str, *, reason: str = "unknown_target") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class TargetDescriptor:
    """One connected target: identifier, platform, probe, serial, flash timeout."""

    identifier: str
    platform: str
    probe_type: str  # one of PROBE_FAMILIES
    serial_device: str
    flash_timeout_seconds: int

    def __post_init__(self) -> None:
        if not self.identifier.strip() or not self.platform.strip():
            raise UnknownTargetError("target requires non-empty identifier and platform")
        if self.probe_type not in PROBE_FAMILIES:
            raise UnknownTargetError(
                f"target '{self.identifier}' has unknown probe type "
                f"'{self.probe_type}' (documented: {PROBE_FAMILIES})"
            )
        if not self.serial_device.strip():
            raise UnknownTargetError(
                f"target '{self.identifier}' requires a serial device"
            )
        if self.flash_timeout_seconds <= 0:
            raise UnknownTargetError(
                f"target '{self.identifier}' requires a positive flash timeout"
            )

    def to_dict(self) -> dict[str, Any]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "flash_timeout_seconds": self.flash_timeout_seconds,
            "identifier": self.identifier,
            "platform": self.platform,
            "probe_type": self.probe_type,
            "serial_device": self.serial_device,
        }


@dataclass(frozen=True)
class HardwareInventory:
    """A declarative inventory of connected targets."""

    targets: tuple[TargetDescriptor, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for target in self.targets:
            if target.identifier in seen:
                raise UnknownTargetError(
                    f"duplicate target identifier '{target.identifier}'"
                )
            seen.add(target.identifier)

    def lookup(self, identifier: str) -> TargetDescriptor:
        """The target registered under ``identifier``."""
        for target in self.targets:
            if target.identifier == identifier:
                return target
        raise UnknownTargetError(f"no target '{identifier}' in the inventory")

    def to_dict(self) -> dict[str, list[dict[str, Any]]]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "targets": [
                target.to_dict()
                for target in sorted(self.targets, key=lambda t: t.identifier)
            ]
        }


@dataclass(frozen=True)
class TargetFailure:
    """One classified target-level failure, distinct from any test failure."""

    kind: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {"detail": self.detail, "kind": self.kind}


def classify_target_failure(output_text: str) -> TargetFailure | None:
    """Classify target execution failures from output text.

    Returns the first matching target-level failure (flash failure, target
    reset, watchdog), or ``no_output`` for an empty stream; test-failure lines
    and clean output classify as no target failure.
    """
    if not output_text.strip():
        return TargetFailure(kind=FAILURE_NO_OUTPUT, detail="target produced no output")
    for kind, pattern in _SIGNATURES:
        match = pattern.search(output_text)
        if match is not None:
            return TargetFailure(
                kind=kind,
                detail=output_text[match.start() :].splitlines()[0].strip(),
            )
    return None
