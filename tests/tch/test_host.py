"""Tests for the WP-TCH-02 built-in host compiler configurations.

Covers: GCC and Clang host configs shipped through the WP-TCH-01 format and
registry, no privileged code path, registry discipline (no overwrite), and
determinism.

Verifies: TOOL-TCH-010.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ectt.tch import (
    CLANG_HOST_CONFIG_NAME,
    GCC_HOST_CONFIG_NAME,
    CompilerConfigRegistry,
    DuplicateCompilerConfigError,
    UnknownCompilerConfigError,
    built_in_host_configs,
    load_compiler_config_text,
    register_host_builtins,
)

if TYPE_CHECKING:
    from ectt.tch.config import CompilerConfig as CompilerConfigLike

_USER_GCC_YAML = """\
schema_version: 1
name: gcc
family: gcc
invocation:
  executable: my-gcc
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
output:
  object_suffix: ".o"
  executable_suffix: ""
coverage:
  kinds: [line]
  flags:
    line: ["--coverage"]
"""


def test_two_builtin_host_configs_are_shipped() -> None:
    """verifies: TOOL-TCH-010"""
    configs = built_in_host_configs()
    assert {c.name for c in configs} == {GCC_HOST_CONFIG_NAME, CLANG_HOST_CONFIG_NAME}
    assert {c.family for c in configs} == {"gcc", "clang"}


def test_gcc_host_config_specifies_every_format_aspect() -> None:
    """verifies: TOOL-TCH-010"""
    config = built_in_host_configs()[0]
    assert config.name == "gcc"
    assert config.invocation.executable == "gcc"
    assert config.debug_flags
    assert len(config.optimization_flags) >= 2
    assert config.output.object_suffix
    assert config.coverage_kinds
    for kind in config.coverage_kinds:
        assert config.coverage_flags[kind]


def test_clang_host_config_specifies_every_format_aspect() -> None:
    """verifies: TOOL-TCH-010"""
    config = built_in_host_configs()[1]
    assert config.name == "clang"
    assert config.invocation.executable == "clang"
    assert config.debug_flags
    assert len(config.optimization_flags) >= 2
    assert config.output.object_suffix
    assert config.coverage_kinds
    for kind in config.coverage_kinds:
        assert config.coverage_flags[kind]


def test_builtins_are_produced_by_the_public_loader() -> None:
    """verifies: TOOL-TCH-010"""
    # The builtins are constructed by validating embedded YAML with the same
    # loader a user file goes through; a structural mistake in a built-in
    # would raise the same named error at import time. Rebuilding a document
    # from the loaded fields must round-trip the identifying aspects.
    configs = built_in_host_configs()
    for config in configs:
        rebuilt = load_compiler_config_text(_render(config))
        assert rebuilt.name == config.name
        assert rebuilt.family == config.family
        assert rebuilt.invocation == config.invocation
        assert rebuilt.output == config.output
        assert rebuilt.coverage_kinds == config.coverage_kinds
        assert dict(rebuilt.coverage_flags) == dict(config.coverage_flags)


def _render(config: CompilerConfigLike) -> str:
    kind_flags = "\n".join(
        f"    {kind}: ['--coverage']" for kind in sorted(config.coverage_kinds)
    )
    optimization = "\n".join(
        f"    {level}: [{', '.join(flags)}]"
        for level, flags in sorted(config.optimization_flags.items())
    )
    return (
        "schema_version: 1\n"
        f"name: {config.name}\n"
        f"family: {config.family}\n"
        "invocation:\n"
        f"  executable: {config.invocation.executable}\n"
        "flags:\n"
        "  debug: []\n"
        "  optimization:\n"
        f"{optimization}\n"
        "output:\n"
        f"  object_suffix: '{config.output.object_suffix}'\n"
        "  executable_suffix: ''\n"
        "coverage:\n"
        f"  kinds: [{', '.join(sorted(config.coverage_kinds))}]\n"
        "  flags:\n"
        f"{kind_flags}\n"
    )


def test_builtins_register_and_lookup_by_name() -> None:
    """verifies: TOOL-TCH-010"""
    registry = CompilerConfigRegistry()
    register_host_builtins(registry)
    gcc = registry.lookup("gcc")
    clang = registry.lookup("clang")
    assert gcc.family == "gcc"
    assert clang.family == "clang"


def test_lookup_before_registration_is_unknown() -> None:
    """verifies: TOOL-TCH-010"""
    registry = CompilerConfigRegistry()
    with pytest.raises(UnknownCompilerConfigError):
        registry.lookup(GCC_HOST_CONFIG_NAME)


def test_builtins_never_overwrite_user_configs() -> None:
    """verifies: TOOL-TCH-010"""
    registry = CompilerConfigRegistry()
    registry.register(load_compiler_config_text(_USER_GCC_YAML))
    with pytest.raises(DuplicateCompilerConfigError):
        register_host_builtins(registry)
    assert registry.lookup("gcc").invocation.executable == "my-gcc"


def test_builtin_set_is_deterministic() -> None:
    """verifies: TOOL-TCH-010"""
    first = built_in_host_configs()
    second = built_in_host_configs()
    assert [c.to_dict() for c in first] == [c.to_dict() for c in second]
    assert [c.name for c in first] == ["gcc", "clang"]
