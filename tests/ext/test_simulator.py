"""Tests for the WP-EXT-01 simulator execution planning.

Verifies: TOOL-TGT-020.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.ext import (
    FAMILY_QEMU,
    FAMILY_RENODE,
    SIMULATOR_FAMILIES,
    UnknownSimulatorError,
    consume_simulator_output,
    plan_simulator_run,
    qemu_descriptor,
    renode_descriptor,
)


def test_both_documented_simulator_families_have_descriptors() -> None:
    """verifies: TOOL-TGT-020"""
    assert set(SIMULATOR_FAMILIES) == {"qemu", "renode"}
    qemu = qemu_descriptor()
    renode = renode_descriptor()
    assert qemu.family == FAMILY_QEMU
    assert renode.family == FAMILY_RENODE
    assert qemu.executable.startswith("qemu-system-")
    assert renode.executable == "renode"


def test_qemu_command_composed_with_machine_and_harness() -> None:
    """verifies: TOOL-TGT-020"""
    plan = plan_simulator_run(qemu_descriptor("mps2-an385"), "build/arm/harness.elf")
    assert plan.command_line == (
        "qemu-system-arm -M mps2-an385 -nographic -kernel build/arm/harness.elf"
    )
    assert plan.family == "qemu"


def test_renode_command_composed_with_script_and_harness() -> None:
    """verifies: TOOL-TGT-020"""
    plan = plan_simulator_run(renode_descriptor(), "build/arm/harness.elf")
    assert plan.command_line.startswith("renode --disable-xwt")
    assert "boards/stm32f4_discovery.resc" in plan.command_line
    assert "LoadELF build/arm/harness.elf" in plan.command_line


def test_custom_machine_selection() -> None:
    """verifies: TOOL-TGT-020"""
    plan = plan_simulator_run(qemu_descriptor("virt"), "h.elf")
    assert "-M virt" in plan.command_line


def test_unknown_family_is_named_error() -> None:
    """verifies: TOOL-TGT-020"""
    with pytest.raises(UnknownSimulatorError) as excinfo:
        qemu_descriptor().__class__(family="bochs", executable="bochs", machine="m", command_template="{harness} {machine}")
    assert "bochs" in str(excinfo.value)


def test_blank_machine_is_named_error() -> None:
    """verifies: TOOL-TGT-020"""
    with pytest.raises(UnknownSimulatorError):
        qemu_descriptor(machine="   ")


def test_template_without_slots_is_named_error() -> None:
    """verifies: TOOL-TGT-020"""
    with pytest.raises(UnknownSimulatorError):
        qemu_descriptor().__class__(
            family="qemu", executable="qemu-system-arm", machine="m", command_template="run {harness}"
        )


def test_empty_harness_is_named_error() -> None:
    """verifies: TOOL-TGT-020"""
    with pytest.raises(UnknownSimulatorError):
        plan_simulator_run(qemu_descriptor(), "  ")


def test_simulator_output_consumed_as_untrusted_data() -> None:
    """verifies: TOOL-TGT-020"""
    results = consume_simulator_output(
        "PASS test_one\nFAIL test_two\njunk noise\n", "qemu-mps2-an385"
    )
    assert [r.kind for r in results] == ["PASS", "FAIL", "unparsed"]
    assert all(r.origin == "qemu-mps2-an385" for r in results)


def test_descriptors_are_frozen_and_serialisable() -> None:
    """verifies: TOOL-TGT-020"""
    descriptor = qemu_descriptor()
    assert descriptor.to_dict() == qemu_descriptor().to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        descriptor.machine = "virt"  # type: ignore[misc]
