"""Tests for the WP-BLD-03 cross-compiled target build planning.

Verifies: TOOL-TGT-010.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.bld import ArtifactSpec, IncrementalPlanner
from ectt.bld.crossbuild import CrossBuildPlan, plan_cross_build
from ectt.tch import (
    CompilerConfigRegistry,
    UnsupportedMetricError,
    register_cross_builtins,
    register_host_builtins,
)


def _arm_config():
    registry = CompilerConfigRegistry()
    register_cross_builtins(registry)
    return registry.lookup("arm-none-eabi-gcc")


def _specs() -> tuple[ArtifactSpec, ...]:
    return (
        ArtifactSpec(
            output_path="obj/harness.o",
            source_path="gen/harness.c",
            source_digest="a" * 64,
            compiler="arm-none-eabi-gcc",
            flags=(),
        ),
        ArtifactSpec(
            output_path="obj/uut.o",
            source_path="src/uut.c",
            source_digest="b" * 64,
            compiler="arm-none-eabi-gcc",
            flags=(),
        ),
    )


def test_cross_commands_use_the_cross_executable() -> None:
    """verifies: TOOL-TGT-010"""
    plan = plan_cross_build(_specs(), _arm_config(), build_root="build/arm")
    assert isinstance(plan, CrossBuildPlan)
    assert plan.toolchain == "arm-none-eabi-gcc"
    assert all(command.command_line.startswith("arm-none-eabi-gcc ") for command in plan.commands)


def test_command_composition_is_exact_and_deterministic() -> None:
    """verifies: TOOL-TGT-010"""
    plan = plan_cross_build(_specs(), _arm_config(), build_root="build/arm")
    assert [c.output_path for c in plan.commands] == ["build/arm/obj/harness.o", "build/arm/obj/uut.o"]
    first_command = plan.commands[0].command_line
    assert first_command == (
        "arm-none-eabi-gcc -g -c -O0 -o build/arm/obj/harness.o gen/harness.c"
    )
    again = plan_cross_build(_specs(), _arm_config(), build_root="build/arm")
    assert again.to_dict() == plan.to_dict()


def test_coverage_flags_included_for_declared_kinds() -> None:
    """verifies: TOOL-TGT-010"""
    plan = plan_cross_build(_specs(), _arm_config(), coverage_kinds=("line",))
    assert "--coverage" in plan.commands[0].command_line.split()
    without = plan_cross_build(_specs(), _arm_config())
    assert "--coverage" not in without.commands[0].command_line


def test_undeclared_metric_refused() -> None:
    """verifies: TOOL-TGT-010"""
    with pytest.raises(UnsupportedMetricError) as excinfo:
        plan_cross_build(_specs(), _arm_config(), coverage_kinds=("mcdc",))
    assert "arm-none-eabi-gcc" in str(excinfo.value)


def test_up_to_date_artifacts_not_replanned() -> None:
    """verifies: TOOL-TGT-010"""
    specs = _specs()
    planner = IncrementalPlanner(
        {
            "obj/harness.o": type(
                "R",
                (),
                {
                    "source_digest": "a" * 64,
                    "compiler": "arm-none-eabi-gcc",
                    "flags": (),
                },
            )(),
        }
    )
    plan = plan_cross_build(specs, _arm_config(), build_root="build/arm", planner=planner)
    assert [c.output_path for c in plan.commands] == ["build/arm/obj/uut.o"]


def test_plan_is_frozen_and_serialisable() -> None:
    """verifies: TOOL-TGT-010"""
    plan = plan_cross_build(_specs(), _arm_config())
    assert plan.to_dict() == plan.to_dict()
    with pytest.raises(dataclasses.FrozenInstanceError):
        plan.toolchain = "x"  # type: ignore[misc]


def test_host_config_also_plans() -> None:
    """verifies: TOOL-TGT-010"""
    registry = CompilerConfigRegistry()
    register_host_builtins(registry)
    plan = plan_cross_build(_specs(), registry.lookup("gcc"), build_root="build/host")
    assert plan.commands[0].command_line.startswith("gcc ")
