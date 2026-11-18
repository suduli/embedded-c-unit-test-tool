"""Tests for the WP-TCH-03 cross-toolchain support and shipped roster.

Verifies: TOOL-TCH-030, TOOL-TCH-040, TOOL-TCH-050.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.tch import (
    CompilerConfigRegistry,
    DuplicateCompilerConfigError,
    UnknownCompilerConfigError,
    load_compiler_config,
    register_host_builtins,
)

SHIPPED_ROSTER = (
    "arm-none-eabi-gcc",
    "avr-gcc",
    "clang",
    "gcc",
    "riscv64-unknown-elf-gcc",
    "sdcc",
)


def _full_registry() -> CompilerConfigRegistry:
    registry = CompilerConfigRegistry()
    register_host_builtins(registry)
    from ectt.tch.cross import register_cross_builtins

    register_cross_builtins(registry)
    return registry


def test_shipped_roster_covers_the_srs_minimum() -> None:
    """verifies: TOOL-TCH-050"""
    from ectt.tch.cross import shipped_roster

    assert shipped_roster() == SHIPPED_ROSTER
    registry = _full_registry()
    for name in SHIPPED_ROSTER:
        assert registry.lookup(name).invocation.executable.replace("-gcc", "-gcc")


def test_cross_configs_carry_triples_and_invocations() -> None:
    """verifies: TOOL-TCH-030"""
    registry = _full_registry()
    assert registry.lookup("arm-none-eabi-gcc").invocation.executable == "arm-none-eabi-gcc"
    assert registry.lookup("riscv64-unknown-elf-gcc").invocation.executable == "riscv64-unknown-elf-gcc"
    assert registry.lookup("avr-gcc").invocation.executable == "avr-gcc"
    assert registry.lookup("sdcc").invocation.executable == "sdcc"
    assert registry.lookup("arm-none-eabi-gcc").family == "gcc"
    assert registry.lookup("sdcc").output.executable_suffix == ".ihx"


def test_cross_configs_pass_the_user_validation_path() -> None:
    """verifies: TOOL-TCH-050"""
    from ectt.tch.cross import shipped_cross_configs

    configs = shipped_cross_configs()
    assert {c.name for c in configs} == {
        "arm-none-eabi-gcc",
        "riscv64-unknown-elf-gcc",
        "avr-gcc",
        "sdcc",
    }
    for config in configs:
        assert config.coverage_kinds
        for kind in config.coverage_kinds:
            assert config.coverage_flags[kind]


def test_additional_cross_compiler_via_config_file_only(tmp_path: Path) -> None:
    """verifies: TOOL-TCH-040"""
    user_yaml = tmp_path / "my-cross.yaml"
    user_yaml.write_text(
        """\
schema_version: 1
name: my-xtensa-gcc
family: gcc
invocation:
  executable: xtensa-esp32-elf-gcc
flags:
  debug: ["-g"]
  optimization:
    size: ["-Os"]
output:
  object_suffix: ".o"
  executable_suffix: ".elf"
coverage:
  kinds: [line]
  flags:
    line: ["--coverage"]
""",
        encoding="utf-8",
    )
    registry = _full_registry()
    registry.register(load_compiler_config(user_yaml))
    assert registry.lookup("my-xtensa-gcc").invocation.executable == "xtensa-esp32-elf-gcc"


def test_duplicate_cross_registration_refused() -> None:
    """verifies: TOOL-TCH-030"""
    from ectt.tch.cross import register_cross_builtins

    registry = _full_registry()
    with pytest.raises(DuplicateCompilerConfigError):
        register_cross_builtins(registry)


def test_roster_completeness_enforced() -> None:
    """verifies: TOOL-TCH-050"""
    from ectt.tch.cross import ensure_roster_complete

    ensure_roster_complete(_full_registry())
    partial = CompilerConfigRegistry()
    register_host_builtins(partial)
    with pytest.raises(UnknownCompilerConfigError):
        ensure_roster_complete(partial)
