"""Tests for the WP-EXT-05 hardware inventory and failure classification.

Verifies: TOOL-TGT-080, TOOL-TGT-090.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.ext import (
    FAILURE_FLASH,
    FAILURE_NO_OUTPUT,
    FAILURE_TARGET_RESET,
    FAILURE_WATCHDOG,
    HardwareInventory,
    TargetDescriptor,
    UnknownTargetError,
    classify_target_failure,
)


def _target(identifier: str = "discovery-1") -> TargetDescriptor:
    return TargetDescriptor(
        identifier=identifier,
        platform="stm32f407vg",
        probe_type="openocd",
        serial_device="/dev/ttyUSB0",
        flash_timeout_seconds=30,
    )


def test_inventory_describes_connected_targets() -> None:
    """verifies: TOOL-TGT-080"""
    inventory = HardwareInventory(
        targets=(
            _target("discovery-1"),
            TargetDescriptor(
                identifier="nucleo-2",
                platform="stm32f411re",
                probe_type="pyocd",
                serial_device="COM3",
                flash_timeout_seconds=45,
            ),
        )
    )
    assert inventory.lookup("discovery-1").serial_device == "/dev/ttyUSB0"
    assert inventory.lookup("nucleo-2").probe_type == "pyocd"
    assert inventory.to_dict()["targets"][0]["identifier"] == "discovery-1"


def test_duplicate_identifier_is_named_error() -> None:
    """verifies: TOOL-TGT-080"""
    with pytest.raises(UnknownTargetError) as excinfo:
        HardwareInventory(targets=(_target("same"), _target("same")))
    assert "same" in str(excinfo.value)


def test_unknown_probe_type_is_named_error() -> None:
    """verifies: TOOL-TGT-080"""
    with pytest.raises(UnknownTargetError) as excinfo:
        TargetDescriptor(
            identifier="x",
            platform="p",
            probe_type="magic_probe",
            serial_device="/dev/tty",
            flash_timeout_seconds=10,
        )
    assert "magic_probe" in str(excinfo.value)


def test_blank_fields_and_bad_timeout_are_named_errors() -> None:
    """verifies: TOOL-TGT-080"""
    with pytest.raises(UnknownTargetError):
        TargetDescriptor(identifier="  ", platform="p", probe_type="openocd", serial_device="s", flash_timeout_seconds=1)
    with pytest.raises(UnknownTargetError):
        TargetDescriptor(identifier="x", platform="p", probe_type="openocd", serial_device="", flash_timeout_seconds=1)
    with pytest.raises(UnknownTargetError):
        TargetDescriptor(identifier="x", platform="p", probe_type="openocd", serial_device="s", flash_timeout_seconds=0)


def test_lookup_unknown_id_is_named_error() -> None:
    """verifies: TOOL-TGT-080"""
    inventory = HardwareInventory(targets=(_target(),))
    with pytest.raises(UnknownTargetError):
        inventory.lookup("ghost")


def test_inventory_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-TGT-080"""
    inventory = HardwareInventory(targets=(_target("b"), _target("a")))
    assert inventory.to_dict() == HardwareInventory(
        targets=(_target("a"), _target("b"))
    ).to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        inventory.targets = ()  # type: ignore[misc]


def test_flash_failure_classified() -> None:
    """verifies: TOOL-TGT-090"""
    verdict = classify_target_failure(
        "Open On-Chip Debugger\nError: flash failed at 0x08000000\n"
    )
    assert verdict is not None
    assert verdict.kind == FAILURE_FLASH
    assert "flash failed" in verdict.detail


def test_no_output_classified() -> None:
    """verifies: TOOL-TGT-090"""
    verdict = classify_target_failure("   \n")
    assert verdict is not None
    assert verdict.kind == FAILURE_NO_OUTPUT


def test_target_reset_classified() -> None:
    """verifies: TOOL-TGT-090"""
    verdict = classify_target_failure("PASS test_one\nINFO: target reset occurred\n")
    assert verdict is not None
    assert verdict.kind == FAILURE_TARGET_RESET


def test_watchdog_classified() -> None:
    """verifies: TOOL-TGT-090"""
    verdict = classify_target_failure("watchdog expired while running test_x\n")
    assert verdict is not None
    assert verdict.kind == FAILURE_WATCHDOG


def test_test_failures_never_classify_as_target_failures() -> None:
    """verifies: TOOL-TGT-090"""
    # A pure test-failure stream has no target-level signature.
    assert classify_target_failure("PASS test_one\nFAIL test_two expected=1 actual=2\n") is None
    assert classify_target_failure("PASS test_one\n") is None


def test_classification_is_deterministic() -> None:
    """verifies: TOOL-TGT-090"""
    stream = "Error: flash failed\n"
    assert classify_target_failure(stream) == classify_target_failure(stream)
    assert classify_target_failure(stream).to_dict() == {
        "detail": "Error: flash failed",
        "kind": FAILURE_FLASH,
    }
