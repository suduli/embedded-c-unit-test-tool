"""Tests for the WP-EXT-07 user-supplied execution methods.

Verifies: TOOL-PLG-040, TOOL-TGT-120.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.ext import (
    DuplicateMethodError,
    ExecutionMethodDescriptor,
    MethodRegistry,
    UnknownMethodError,
    plan_user_execution,
)


def _descriptor(method_id: str = "bare-metal-script") -> ExecutionMethodDescriptor:
    return ExecutionMethodDescriptor(
        method_id=method_id,
        script_path="tools/flash_and_talk.py",
        command_template="python {script} --target {target} --image {harness}",
    )


def _registry() -> MethodRegistry:
    registry = MethodRegistry()
    registry.register(_descriptor())
    return registry


def test_method_added_through_documented_interface_and_script() -> None:
    """verifies: TOOL-PLG-040"""
    registry = _registry()
    assert registry.list_ids() == ("bare-metal-script",)
    assert registry.lookup("bare-metal-script").script_path == "tools/flash_and_talk.py"


def test_duplicate_and_unknown_methods_are_named_errors() -> None:
    """verifies: TOOL-PLG-040"""
    registry = _registry()
    with pytest.raises(DuplicateMethodError):
        registry.register(_descriptor())
    with pytest.raises(UnknownMethodError):
        registry.lookup("ghost")
    with pytest.raises(UnknownMethodError):
        registry.register(
            ExecutionMethodDescriptor(method_id="  ", script_path="s", command_template="{script} {target} {harness}")
        )


def test_listing_is_deterministic() -> None:
    """verifies: TOOL-PLG-040"""
    registry = MethodRegistry()
    for name in ("zeta", "alpha", "mid"):
        registry.register(_descriptor(name))
    assert registry.list_ids() == ("alpha", "mid", "zeta")


def test_script_composition_supports_probeless_targets() -> None:
    """verifies: TOOL-TGT-120"""
    plan = plan_user_execution(
        "bare-metal-script", _registry(), target="custom_board", harness="build/h.elf"
    )
    assert plan.command_line == (
        "python tools/flash_and_talk.py --target custom_board --image build/h.elf"
    )
    assert plan.to_dict()["target"] == "custom_board"


def test_method_without_template_slots_is_named_error() -> None:
    """verifies: TOOL-PLG-040"""
    for missing in (
        "python {script} --target {target}",
        "python --target {target} --image {harness}",
        "python {script} --image {harness}",
    ):
        with pytest.raises(UnknownMethodError):
            ExecutionMethodDescriptor(
                method_id="bad", script_path="s.py", command_template=missing
            )


def test_script_content_is_never_executed_at_plan_time() -> None:
    """verifies: TOOL-TGT-120"""
    # The script path need not exist: plan time composes text only.
    descriptor = ExecutionMethodDescriptor(
        method_id="no_such_file",
        script_path="definitely/not/here.py",
        command_template="{script} {target} {harness}",
    )
    registry = MethodRegistry()
    registry.register(descriptor)
    plan = plan_user_execution("no_such_file", registry, target="t", harness="h")
    assert plan.command_line == "definitely/not/here.py t h"


def test_blank_target_or_harness_is_named_error() -> None:
    """verifies: TOOL-TGT-120"""
    with pytest.raises(UnknownMethodError):
        plan_user_execution("bare-metal-script", _registry(), target="  ", harness="h")
    with pytest.raises(UnknownMethodError):
        plan_user_execution("bare-metal-script", _registry(), target="t", harness="")


def test_descriptor_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-PLG-040"""
    descriptor = _descriptor()
    assert descriptor.to_dict() == _descriptor().to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        descriptor.script_path = "x"  # type: ignore[misc]
