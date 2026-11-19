"""Tests for the WP-EXT-02 debug-probe execution and flashing.

Verifies: TOOL-TGT-030, TOOL-TGT-040.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.ext import (
    PROBE_FAMILIES,
    UnknownProbeError,
    jlink_descriptor,
    openocd_descriptor,
    plan_flash,
    plan_probe_run,
    pyocd_descriptor,
)


def test_documented_flashing_tools_have_descriptors() -> None:
    """verifies: TOOL-TGT-040"""
    assert set(PROBE_FAMILIES) == {"openocd", "pyocd", "jlink"}
    assert openocd_descriptor().executable == "openocd"
    assert pyocd_descriptor().executable == "pyocd"
    assert jlink_descriptor().executable == "JLinkExe"


def test_flash_plan_composed_for_each_tool() -> None:
    """verifies: TOOL-TGT-040"""
    target, harness = "stm32f407", "build/harness.elf"
    openocd = plan_flash(openocd_descriptor(), target, harness)
    pyocd = plan_flash(pyocd_descriptor(), target, harness)
    jlink = plan_flash(jlink_descriptor(), target, harness)
    assert openocd.action == "flash" and "program build/harness.elf" in openocd.command_line
    assert pyocd.command_line.startswith("pyocd flash --target stm32f407vg build/harness.elf")
    assert "-device STM32F407VG" in jlink.command_line and "harness.elf" in jlink.command_line
    assert all(plan.target == target for plan in (openocd, pyocd, jlink))


def test_probe_run_plan_composed() -> None:
    """verifies: TOOL-TGT-030"""
    plan = plan_probe_run(openocd_descriptor(), "stm32f407", "build/harness.elf")
    assert plan.action == "run"
    assert "reset run" in plan.command_line
    assert "build/harness.elf" in plan.command_line
    assert plan.to_dict()["target"] == "stm32f407"


def test_unknown_probe_family_is_named_error() -> None:
    """verifies: TOOL-TGT-030"""
    with pytest.raises(UnknownProbeError) as excinfo:
        openocd_descriptor().__class__(
            family="stlink_magic",
            executable="x",
            flash_command_template="{target} {harness}",
            run_command_template="{target} {harness}",
        )
    assert "stlink_magic" in str(excinfo.value)


def test_blank_target_or_harness_are_named_errors() -> None:
    """verifies: TOOL-TGT-040"""
    with pytest.raises(UnknownProbeError):
        plan_flash(openocd_descriptor(), "  ", "h.elf")
    with pytest.raises(UnknownProbeError):
        plan_flash(openocd_descriptor(), "target", "")
    with pytest.raises(UnknownProbeError):
        plan_probe_run(pyocd_descriptor(), "target", "")


def test_template_without_slots_is_named_error() -> None:
    """verifies: TOOL-TGT-040"""
    with pytest.raises(UnknownProbeError):
        openocd_descriptor().__class__(
            family="openocd",
            executable="openocd",
            flash_command_template="program {harness}",  # no {target}
            run_command_template="{target} {harness}",
        )


def test_descriptors_are_frozen_and_deterministic() -> None:
    """verifies: TOOL-TGT-030"""
    descriptor = jlink_descriptor()
    assert descriptor.to_dict() == jlink_descriptor().to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        descriptor.executable = "x"  # type: ignore[misc]
