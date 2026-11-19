"""Hardware execution and flashing via debug probe (WP-EXT-02).

Probe execution and flashing plans are composed from declarative, frozen
probe descriptors covering the documented flashing-tool support: OpenOCD,
pyOCD and J-Link.

Satisfies: TOOL-TGT-030, TOOL-TGT-040.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.ext.errors import ExtError

__all__ = [
    "PROBE_FAMILIES",
    "ProbeDescriptor",
    "ProbePlan",
    "UnknownProbeError",
    "openocd_descriptor",
    "pyocd_descriptor",
    "jlink_descriptor",
    "plan_probe_run",
    "plan_flash",
]

FAMILY_OPENOCD = "openocd"
FAMILY_PYOCD = "pyocd"
FAMILY_JLINK = "jlink"

PROBE_FAMILIES = (FAMILY_OPENOCD, FAMILY_PYOCD, FAMILY_JLINK)


class UnknownProbeError(ExtError):
    """Raised when a probe family is unknown or a plan lacks required data."""

    def __init__(self, message: str, *, reason: str = "unknown_probe") -> None:
        super().__init__(message, reason=reason)


@dataclass(frozen=True)
class ProbeDescriptor:
    """One declarative debug-probe tool descriptor."""

    family: str
    executable: str
    flash_command_template: str  # must contain {target} and {harness}
    run_command_template: str  # must contain {target} and {harness}

    def __post_init__(self) -> None:
        if self.family not in PROBE_FAMILIES:
            raise UnknownProbeError(
                f"probe family '{self.family}' is outside the documented "
                f"families {PROBE_FAMILIES}"
            )
        if not self.executable.strip():
            raise UnknownProbeError(
                f"probe '{self.family}' requires a non-empty executable"
            )
        for template_name, template in (
            ("flash", self.flash_command_template),
            ("run", self.run_command_template),
        ):
            if "{target}" not in template or "{harness}" not in template:
                raise UnknownProbeError(
                    f"probe '{self.family}' {template_name} template must include "
                    f"{{target}} and {{harness}} slots"
                )

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "executable": self.executable,
            "family": self.family,
            "flash_command_template": self.flash_command_template,
            "run_command_template": self.run_command_template,
        }


def openocd_descriptor(config_file: str = "board/stm32f4discovery.cfg") -> ProbeDescriptor:
    """The OpenOCD descriptor."""
    return ProbeDescriptor(
        family=FAMILY_OPENOCD,
        executable="openocd",
        flash_command_template=(
            f"{{executable}} -f {config_file} "
            f"-c \"program {{harness}} verify reset exit\" -c \"target {{target}}\""
        ),
        run_command_template=(
            f"{{executable}} -f {config_file} -c \"target {{target}}\" "
            f"-c \"reset run\" -c \"shutdown\"  # harness: {{harness}}"
        ),
    )


def pyocd_descriptor(target: str = "stm32f407vg") -> ProbeDescriptor:
    """The pyOCD descriptor."""
    return ProbeDescriptor(
        family=FAMILY_PYOCD,
        executable="pyocd",
        flash_command_template=(
            f"{{executable}} flash --target {target} {{harness}}  # probe target: {{target}}"
        ),
        run_command_template=(
            f"{{executable}} gdbserver --target {target} --persist  # harness: {{harness}}, probe target: {{target}}"
        ),
    )


def jlink_descriptor(device: str = "STM32F407VG") -> ProbeDescriptor:
    """The J-Link descriptor."""
    return ProbeDescriptor(
        family=FAMILY_JLINK,
        executable="JLinkExe",
        flash_command_template=(
            f"{{executable}} -device {device} -if swd -speed 4000 "
            f"-CommandFile flash.jlink  # image: {{harness}}, target: {{target}}"
        ),
        run_command_template=(
            f"{{executable}} -device {device} -if swd -speed 4000 -AutoConnect 1 "
            f"-CommandFile run.jlink  # harness: {{harness}}, target: {{target}}"
        ),
    )


@dataclass(frozen=True)
class ProbePlan:
    """The composed plan for one probe action on one target."""

    family: str
    action: str  # "flash" | "run"
    target: str
    harness: str
    command_line: str

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "action": self.action,
            "command_line": self.command_line,
            "family": self.family,
            "harness": self.harness,
            "target": self.target,
        }


def _compose(
    descriptor: ProbeDescriptor,
    template: str,
    action: str,
    target: str,
    harness: str,
) -> ProbePlan:
    if not target.strip():
        raise UnknownProbeError(f"{action} requires a non-empty target name")
    if not harness.strip():
        raise UnknownProbeError(f"{action} requires a non-empty harness path")
    command_line = (
        template.replace("{executable}", descriptor.executable)
        .replace("{target}", target)
        .replace("{harness}", harness)
    )
    return ProbePlan(
        family=descriptor.family,
        action=action,
        target=target,
        harness=harness,
        command_line=command_line,
    )


def plan_probe_run(descriptor: ProbeDescriptor, target: str, harness: str) -> ProbePlan:
    """Compose the probe execution plan for one harness on one target."""
    return _compose(descriptor, descriptor.run_command_template, "run", target, harness)


def plan_flash(descriptor: ProbeDescriptor, target: str, harness: str) -> ProbePlan:
    """Compose the flashing plan for one harness image onto one target."""
    return _compose(descriptor, descriptor.flash_command_template, "flash", target, harness)
