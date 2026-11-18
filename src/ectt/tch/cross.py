"""Cross-toolchain support and shipped configurations (WP-TCH-03).

The shipped configuration roster covers the SRS minimum: GCC (host), Clang
(host), arm-none-eabi-gcc, riscv64-unknown-elf-gcc, avr-gcc and SDCC — all
built through the same schema-version-1 validation as user-authored files.
Additional cross compilers are supported by authoring a configuration file;
no tool source change is involved.

Satisfies: TOOL-TCH-030, TOOL-TCH-040, TOOL-TCH-050.
"""

from __future__ import annotations

from ectt.tch.builtin import built_in_host_configs
from ectt.tch.config import (
    CompilerConfig,
    CompilerConfigRegistry,
    load_compiler_config_text,
)

__all__ = [
    "CROSS_CONFIG_NAMES",
    "SHIPPED_CONFIG_NAMES",
    "shipped_cross_configs",
    "shipped_roster",
    "register_cross_builtins",
]

ARM_YAML = """\
schema_version: 1
name: arm-none-eabi-gcc
family: gcc
invocation:
  executable: arm-none-eabi-gcc
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Os"]
output:
  object_suffix: ".o"
  executable_suffix: ".elf"
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""

RISCV_YAML = """\
schema_version: 1
name: riscv64-unknown-elf-gcc
family: gcc
invocation:
  executable: riscv64-unknown-elf-gcc
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Os"]
output:
  object_suffix: ".o"
  executable_suffix: ".elf"
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""

AVR_YAML = """\
schema_version: 1
name: avr-gcc
family: gcc
invocation:
  executable: avr-gcc
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Os"]
output:
  object_suffix: ".o"
  executable_suffix: ".elf"
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""

# The SDCC coverage flag is an owner-review draft (see the WP-TCH-03 note):
# the config is declarative data and correctable without tool source changes.
SDCC_YAML = """\
schema_version: 1
name: sdcc
family: sdcc
invocation:
  executable: sdcc
flags:
  debug: ["--debug"]
  optimization:
    size: ["--opt-code-size"]
output:
  object_suffix: ".rel"
  executable_suffix: ".ihx"
coverage:
  kinds: [line]
  flags:
    line: ["--debug"]
"""

_CROSS_YAMLS: tuple[str, ...] = (ARM_YAML, RISCV_YAML, AVR_YAML, SDCC_YAML)

CROSS_CONFIG_NAMES: tuple[str, ...] = (
    "arm-none-eabi-gcc",
    "riscv64-unknown-elf-gcc",
    "avr-gcc",
    "sdcc",
)

SHIPPED_CONFIG_NAMES: tuple[str, ...] = ("gcc", "clang", *CROSS_CONFIG_NAMES)


def shipped_cross_configs() -> tuple[CompilerConfig, ...]:
    """The shipped cross-toolchain configurations, validated like user files."""
    return tuple(load_compiler_config_text(text) for text in _CROSS_YAMLS)


def shipped_roster() -> tuple[str, ...]:
    """The full shipped roster: host built-ins plus cross configs."""
    host_names = tuple(config.name for config in built_in_host_configs())
    return tuple(sorted((*host_names, *CROSS_CONFIG_NAMES)))


def register_cross_builtins(registry: CompilerConfigRegistry) -> None:
    """Register the cross configurations through the public registry surface."""
    for config in shipped_cross_configs():
        registry.register(config)


def ensure_roster_complete(registry: CompilerConfigRegistry) -> None:
    """Refuse a registry that misses any shipped configuration name.

    Raises :class:`DuplicateCompilerConfigError`'s sibling error semantics via
    the standard unknown-config error when a roster entry is absent.
    """

    for name in shipped_roster():
        registry.lookup(name)  # raises UnknownCompilerConfigError when absent
