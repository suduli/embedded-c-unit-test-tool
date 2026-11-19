"""Built-in host compiler configurations: GCC and Clang (WP-TCH-02).

The two configurations are embedded as schema-version-1 YAML documents and
built through the same validator as user-authored files, so the built-ins
exercise the public format instead of a private code path.

Satisfies: TOOL-TCH-010.
"""

from __future__ import annotations

from ectt.tch.config import (
    CompilerConfig,
    CompilerConfigRegistry,
    load_compiler_config_text,
)

__all__ = [
    "GCC_HOST_CONFIG_NAME",
    "CLANG_HOST_CONFIG_NAME",
    "built_in_host_configs",
    "register_host_builtins",
]

GCC_HOST_CONFIG_NAME = "gcc"
CLANG_HOST_CONFIG_NAME = "clang"

_GCC_HOST_YAML = """\
schema_version: 1
name: gcc
family: gcc
invocation:
  executable: gcc
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Os"]
    speed: ["-O2"]
output:
  object_suffix: ".o"
  executable_suffix: ""
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""

_CLANG_HOST_YAML = """\
schema_version: 1
name: clang
family: clang
invocation:
  executable: clang
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Oz"]
    speed: ["-O2"]
output:
  object_suffix: ".o"
  executable_suffix: ""
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""


def built_in_host_configs() -> tuple[CompilerConfig, ...]:
    """The shipped host configurations, in deterministic order.

    Every returned config has passed schema-version-1 validation.
    """
    return tuple(
        load_compiler_config_text(text) for text in (_GCC_HOST_YAML, _CLANG_HOST_YAML)
    )


def register_host_builtins(registry: CompilerConfigRegistry) -> None:
    """Register the host built-ins through the public registry surface.

    A name already taken by a user configuration is never overwritten; the
    duplicate rejection of the registry applies unchanged.
    """
    for config in built_in_host_configs():
        registry.register(config)
