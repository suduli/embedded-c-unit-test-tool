"""Simulator execution planning: QEMU and Renode (WP-EXT-01).

Execution commands are composed per harness binary from declarative,
frozen simulator descriptors for both documented families; simulator output
is consumed strictly through the WP-SEC-07 untrusted boundary — nothing a
simulator prints is ever executed or interpreted beyond the data parse.

Satisfies: TOOL-TGT-020.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ectt.ext.errors import ExtError
from ectt.sec import UntrustedPayload, mark_untrusted, parse_target_output

__all__ = [
    "SIMULATOR_FAMILIES",
    "QEMU_SIMULATOR",
    "RENODE_SIMULATOR",
    "SimulatorDescriptor",
    "SimulatorPlan",
    "UnknownSimulatorError",
    "qemu_descriptor",
    "renode_descriptor",
    "plan_simulator_run",
    "consume_simulator_output",
]

FAMILY_QEMU = "qemu"
FAMILY_RENODE = "renode"

SIMULATOR_FAMILIES = (FAMILY_QEMU, FAMILY_RENODE)

QEMU_SIMULATOR = "qemu-system-generic"
RENODE_SIMULATOR = "renode"


class UnknownSimulatorError(ExtError):
    """Raised when a simulator family is unknown or a descriptor is malformed."""

    def __init__(self, message: str, *, reason: str = "unknown_simulator") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class SimulatorDescriptor:
    """One declarative simulator family descriptor."""

    family: str
    executable: str
    machine: str
    command_template: str  # must contain {harness} and {machine}

    def __post_init__(self) -> None:
        if self.family not in SIMULATOR_FAMILIES:
            raise UnknownSimulatorError(
                f"simulator family '{self.family}' is outside the documented "
                f"families {SIMULATOR_FAMILIES}"
            )
        if not self.executable.strip() or not self.machine.strip():
            raise UnknownSimulatorError(
                f"simulator '{self.family}' requires a non-empty executable and machine"
            )
        if "{harness}" not in self.command_template or "{machine}" not in self.command_template:
            raise UnknownSimulatorError(
                f"simulator '{self.family}' command template must include "
                f"{{harness}} and {{machine}} slots"
            )

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "command_template": self.command_template,
            "executable": self.executable,
            "family": self.family,
            "machine": self.machine,
        }


@dataclass(frozen=True)
class SimulatorPlan:
    """The composed run plan for one harness on one simulator."""

    family: str
    harness: str
    command_line: str

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "command_line": self.command_line,
            "family": self.family,
            "harness": self.harness,
        }


def qemu_descriptor(machine: str = "mps2-an385") -> SimulatorDescriptor:
    """The QEMU descriptor (ARM family machines by default)."""
    return SimulatorDescriptor(
        family=FAMILY_QEMU,
        executable="qemu-system-arm",
        machine=machine,
        command_template="{executable} -M {machine} -nographic -kernel {harness}",
    )


def renode_descriptor(machine: str = "@script:boards/stm32f4_discovery.resc") -> SimulatorDescriptor:
    """The Renode descriptor (platform script default)."""
    return SimulatorDescriptor(
        family=FAMILY_RENODE,
        executable="renode",
        machine=machine,
        command_template="{executable} --disable-xwt -e \"i {machine}\" -e \"sysbus LoadELF {harness}\"",
    )


def plan_simulator_run(descriptor: SimulatorDescriptor, harness: str) -> SimulatorPlan:
    """Compose the simulator run command for one built harness."""
    if not harness.strip():
        raise UnknownSimulatorError("simulator run requires a harness binary path")
    command_line = (
        descriptor.command_template.replace("{executable}", descriptor.executable)
        .replace("{machine}", descriptor.machine)
        .replace("{harness}", harness)
    )
    return SimulatorPlan(
        family=descriptor.family,
        harness=harness,
        command_line=command_line,
    )


def consume_simulator_output(output_text: str, origin: str) -> tuple[Any, ...]:
    """Consume simulator output strictly as untrusted data (WP-SEC-07 boundary)."""
    payload: UntrustedPayload = mark_untrusted(output_text, origin)
    return parse_target_output(payload)
