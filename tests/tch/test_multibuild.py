"""Tests for the WP-TCH-05 multi-toolchain builds and container specs.

Verifies: TOOL-TCH-080, TOOL-TCH-090.
"""

from __future__ import annotations

import pytest

from ectt.bld import ArtifactSpec
from ectt.tch import (
    CompilerConfigRegistry,
    register_cross_builtins,
    register_host_builtins,
)
from ectt.tch.multibuild import (
    ContainerSpecError,
    DuplicateToolchainError,
    MultiBuildPlan,
    container_spec,
    plan_multi_toolchain_builds,
)


def _registry() -> CompilerConfigRegistry:
    registry = CompilerConfigRegistry()
    register_host_builtins(registry)
    register_cross_builtins(registry)
    return registry


def _specs() -> tuple[ArtifactSpec, ...]:
    return (
        ArtifactSpec(
            output_path="obj/harness.o",
            source_path="gen/harness.c",
            source_digest="a" * 64,
            compiler="gcc",
            flags=(),
        ),
    )


def _toolchains() -> tuple[str, ...]:
    return ("gcc", "arm-none-eabi-gcc", "riscv64-unknown-elf-gcc")


def test_same_suite_planned_per_toolchain_in_isolated_dirs() -> None:
    """verifies: TOOL-TCH-080"""
    plan = plan_multi_toolchain_builds(_toolchains(), _specs(), _registry())
    assert isinstance(plan, MultiBuildPlan)
    assert [p.toolchain for p in plan.plans] == sorted(_toolchains())
    assert plan.plans[0].commands[0].output_path == "build/arm-none-eabi-gcc/obj/harness.o"
    assert plan.plans[1].commands[0].output_path == "build/gcc/obj/harness.o"
    assert plan.plans[2].commands[0].output_path == "build/riscv64-unknown-elf-gcc/obj/harness.o"


def test_per_toolchain_commands_use_per_toolchain_executables() -> None:
    """verifies: TOOL-TCH-080"""
    plan = plan_multi_toolchain_builds(_toolchains(), _specs(), _registry())
    assert plan.plans[0].commands[0].command_line.startswith("arm-none-eabi-gcc ")
    assert plan.plans[1].commands[0].command_line.startswith("gcc ")
    assert plan.plans[2].commands[0].command_line.startswith("riscv64-unknown-elf-gcc ")


def test_duplicate_toolchain_is_named_error() -> None:
    """verifies: TOOL-TCH-080"""
    with pytest.raises(DuplicateToolchainError):
        plan_multi_toolchain_builds(("gcc", "gcc"), _specs(), _registry())


def test_unknown_toolchain_is_named_error() -> None:
    """verifies: TOOL-TCH-080"""
    with pytest.raises(Exception):  # noqa: B017 - UnknownCompilerConfigError
        plan_multi_toolchain_builds(("gcc", "ghost-cc"), _specs(), _registry())


def test_multi_plan_is_deterministic() -> None:
    """verifies: TOOL-TCH-080"""
    first = plan_multi_toolchain_builds(_toolchains(), _specs(), _registry())
    second = plan_multi_toolchain_builds(tuple(reversed(_toolchains())), _specs(), _registry())
    assert first.to_dict() == second.to_dict()


def test_container_spec_pins_base_image_by_digest() -> None:
    """verifies: TOOL-TCH-090"""
    text = container_spec(
        _toolchains(),
        base_image="registry.example.com/ectt-base",
        base_image_digest="sha256:" + "c" * 64,
    )
    assert f"FROM registry.example.com/ectt-base@sha256:{'c' * 64}" in text
    for name in sorted(_toolchains()):
        assert f"#   - {name}" in text
    assert "WORKDIR /work" in text


def test_container_spec_is_deterministic() -> None:
    """verifies: TOOL-TCH-090"""
    first = container_spec(
        _toolchains(), base_image="b", base_image_digest="sha256:" + "c" * 64
    )
    second = container_spec(
        tuple(reversed(_toolchains())), base_image="b", base_image_digest="sha256:" + "c" * 64
    )
    assert first == second


def test_container_spec_without_digest_is_named_error() -> None:
    """verifies: TOOL-TCH-090"""
    with pytest.raises(ContainerSpecError) as excinfo:
        container_spec(_toolchains(), base_image="b", base_image_digest="")
    assert "digest" in str(excinfo.value)
    with pytest.raises(ContainerSpecError):
        container_spec(_toolchains(), base_image="", base_image_digest="sha256:x")
    with pytest.raises(ContainerSpecError):
        container_spec((), base_image="b", base_image_digest="sha256:x")
