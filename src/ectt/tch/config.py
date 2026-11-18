"""Declarative compiler configuration format (WP-TCH-01).

A compiler configuration is a plain YAML document — data, not script — that
specifies how the tool drives one C compiler: the invocation, the flag syntax
for debug and optimization, the output conventions, and the coverage kinds the
compiler can deliver with per-kind flags. Adding a compiler means writing such
a file and registering it; no tool source changes.

Schema version 1 document shape::

    schema_version: 1
    name: acme-gcc
    family: gcc
    invocation:
      executable: gcc
      compile_only_flag: "-c"     # optional
      output_flag: "-o"           # optional
      default_output: a.out       # optional
    flags:
      debug: ["-g"]
      optimization:
        none: ["-O0"]
        speed: ["-O2"]
    output:
      object_suffix: ".o"
      executable_suffix: ""
    coverage:
      kinds: [line, branch]
      flags:
        line: ["--coverage"]
        branch: ["--coverage"]

Satisfies: TOOL-PLG-020, TOOL-TCH-020.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ectt.tch.errors import (
    CompilerConfigReadError,
    ConfigSchemaVersionError,
    DuplicateCompilerConfigError,
    InvalidCompilerConfigError,
    UnknownCompilerConfigError,
    UnknownCoverageKindError,
)

__all__ = [
    "CONFIG_SCHEMA_VERSION",
    "KNOWN_COVERAGE_KINDS",
    "InvocationSpec",
    "OutputSpec",
    "CompilerConfig",
    "CompilerConfigRegistry",
    "load_compiler_config",
    "validate_compiler_config_document",
]

CONFIG_SCHEMA_VERSION = 1

# The documented coverage-kind vocabulary. Declared kinds must come from this
# set; the set itself is part of the tool, not of any configuration.
KNOWN_COVERAGE_KINDS = frozenset(
    {"line", "branch", "condition", "decision", "mcdc"}
)


@dataclass(frozen=True)
class InvocationSpec:
    """How the tool invokes the compiler."""

    executable: str
    compile_only_flag: str = "-c"
    output_flag: str = "-o"
    default_output: str = "a.out"


@dataclass(frozen=True)
class OutputSpec:
    """Naming conventions for compiler outputs."""

    object_suffix: str
    executable_suffix: str


@dataclass(frozen=True)
class CompilerConfig:
    """One declarative compiler configuration."""

    name: str
    family: str
    invocation: InvocationSpec
    debug_flags: tuple[str, ...]
    optimization_flags: Mapping[str, tuple[str, ...]]
    output: OutputSpec
    coverage_kinds: frozenset[str]
    coverage_flags: Mapping[str, tuple[str, ...]]
    schema_version: int = CONFIG_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Canonical JSON-safe mapping (deterministic key order)."""
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "family": self.family,
            "invocation": {
                "executable": self.invocation.executable,
                "compile_only_flag": self.invocation.compile_only_flag,
                "output_flag": self.invocation.output_flag,
                "default_output": self.invocation.default_output,
            },
            "flags": {
                "debug": list(self.debug_flags),
                "optimization": {
                    level: list(flags)
                    for level, flags in sorted(self.optimization_flags.items())
                },
            },
            "output": {
                "object_suffix": self.output.object_suffix,
                "executable_suffix": self.output.executable_suffix,
            },
            "coverage": {
                "kinds": sorted(self.coverage_kinds),
                "flags": {
                    kind: list(flags)
                    for kind, flags in sorted(self.coverage_flags.items())
                },
            },
        }


def _expect_mapping(value: Any, what: str, path: Path | None) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InvalidCompilerConfigError(
            f"compiler config field '{what}' must be a mapping",
            path=path,
        )
    return value


def _expect_string(value: Any, what: str, path: Path | None) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidCompilerConfigError(
            f"compiler config field '{what}' must be a non-empty string",
            path=path,
        )
    return value


def _expect_flag_list(value: Any, what: str, path: Path | None) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise InvalidCompilerConfigError(
            f"compiler config field '{what}' must be a list of flag strings",
            path=path,
        )
    for item in value:
        if not isinstance(item, str):
            raise InvalidCompilerConfigError(
                f"compiler config field '{what}' must contain only strings",
                path=path,
            )
    return tuple(value)


def _expect_nonempty_flag_list(value: Any, what: str, path: Path | None) -> tuple[str, ...]:
    flags = _expect_flag_list(value, what, path)
    if not flags:
        raise InvalidCompilerConfigError(
            f"compiler config field '{what}' must not be empty",
            path=path,
        )
    return flags


def validate_compiler_config_document(
    document: Any, *, path: Path | None = None
) -> CompilerConfig:
    """Validate a parsed YAML document and build the immutable config object.

    Every structural problem raises a named :class:`TchError` subclass
    identifying the offending field.
    """
    doc = _expect_mapping(document, "document root", path)

    version = doc.get("schema_version")
    if version is None:
        raise ConfigSchemaVersionError(
            "compiler config is missing 'schema_version'", path=path
        )
    if not isinstance(version, int) or isinstance(version, bool):
        raise ConfigSchemaVersionError(
            f"compiler config 'schema_version' must be an integer, got {version!r}",
            path=path,
        )
    if version != CONFIG_SCHEMA_VERSION:
        raise ConfigSchemaVersionError(
            f"compiler config schema_version {version} is unsupported "
            f"(this tool supports {CONFIG_SCHEMA_VERSION})",
            path=path,
        )

    name = _expect_string(doc.get("name"), "name", path)
    family = _expect_string(doc.get("family"), "family", path)

    invocation_doc = _expect_mapping(doc.get("invocation"), "invocation", path)
    executable = _expect_string(invocation_doc.get("executable"), "invocation.executable", path)
    compile_only = invocation_doc.get("compile_only_flag", "-c")
    output_flag = invocation_doc.get("output_flag", "-o")
    default_output = invocation_doc.get("default_output", "a.out")
    invocation = InvocationSpec(
        executable=executable,
        compile_only_flag=_expect_string(compile_only, "invocation.compile_only_flag", path),
        output_flag=_expect_string(output_flag, "invocation.output_flag", path),
        default_output=_expect_string(default_output, "invocation.default_output", path),
    )

    flags_doc = _expect_mapping(doc.get("flags"), "flags", path)
    debug_flags = _expect_flag_list(flags_doc.get("debug"), "flags.debug", path)
    optimization_doc = _expect_mapping(flags_doc.get("optimization"), "flags.optimization", path)
    optimization_flags = {
        _expect_string(level, "flags.optimization level key", path): _expect_flag_list(
            value, f"flags.optimization.{level}", path
        )
        for level, value in optimization_doc.items()
    }

    output_doc = _expect_mapping(doc.get("output"), "output", path)
    object_suffix = output_doc.get("object_suffix")
    executable_suffix = output_doc.get("executable_suffix")
    if not isinstance(object_suffix, str):
        raise InvalidCompilerConfigError(
            "compiler config field 'output.object_suffix' must be a string",
            path=path,
        )
    if not isinstance(executable_suffix, str):
        raise InvalidCompilerConfigError(
            "compiler config field 'output.executable_suffix' must be a string",
            path=path,
        )
    output = OutputSpec(object_suffix=object_suffix, executable_suffix=executable_suffix)

    coverage_doc = _expect_mapping(doc.get("coverage"), "coverage", path)
    kinds_raw = coverage_doc.get("kinds")
    if not isinstance(kinds_raw, list) or not kinds_raw:
        raise InvalidCompilerConfigError(
            "compiler config field 'coverage.kinds' must be a non-empty list",
            path=path,
        )
    kinds: set[str] = set()
    for kind in kinds_raw:
        if not isinstance(kind, str) or not kind.strip():
            raise InvalidCompilerConfigError(
                "compiler config field 'coverage.kinds' must contain "
                "non-empty strings",
                path=path,
            )
        if kind not in KNOWN_COVERAGE_KINDS:
            raise UnknownCoverageKindError(
                f"coverage kind '{kind}' is outside the documented vocabulary "
                f"({', '.join(sorted(KNOWN_COVERAGE_KINDS))})",
                path=path,
            )
        kinds.add(kind)

    flags_for = _expect_mapping(coverage_doc.get("flags"), "coverage.flags", path)
    coverage_flags: dict[str, tuple[str, ...]] = {}
    for kind_value, flag_value in flags_for.items():
        if not isinstance(kind_value, str) or kind_value not in kinds:
            raise InvalidCompilerConfigError(
                f"coverage.flags entry '{kind_value}' does not match any "
                f"declared coverage kind",
                path=path,
            )
        coverage_flags[kind_value] = _expect_nonempty_flag_list(
            flag_value, f"coverage.flags.{kind_value}", path
        )
    for kind in sorted(kinds):
        if kind not in coverage_flags:
            raise InvalidCompilerConfigError(
                f"declared coverage kind '{kind}' has no coverage.flags entry",
                path=path,
            )

    return CompilerConfig(
        name=name,
        family=family,
        invocation=invocation,
        debug_flags=debug_flags,
        optimization_flags=optimization_flags,
        output=output,
        coverage_kinds=frozenset(kinds),
        coverage_flags=coverage_flags,
    )


def load_compiler_config(path: Path | str) -> CompilerConfig:
    """Load and validate a compiler configuration from a YAML file."""
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CompilerConfigReadError(
            f"cannot read compiler configuration file: {exc}",
            path=file_path,
        ) from exc
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise InvalidCompilerConfigError(
            f"compiler configuration is not valid YAML: {exc}",
            path=file_path,
        ) from exc
    if document is None:
        raise InvalidCompilerConfigError(
            "compiler configuration file is empty",
            path=file_path,
        )
    return validate_compiler_config_document(document, path=file_path)


class CompilerConfigRegistry:
    """Named registry of compiler configurations."""

    def __init__(self) -> None:
        self._configs: dict[str, CompilerConfig] = {}

    def register(self, config: CompilerConfig) -> None:
        """Register a validated configuration; reject a reused name."""
        if config.name in self._configs:
            raise DuplicateCompilerConfigError(
                f"compiler configuration '{config.name}' is already registered"
            )
        self._configs[config.name] = config

    def lookup(self, name: str) -> CompilerConfig:
        """Return the configuration registered under ``name``."""
        try:
            return self._configs[name]
        except KeyError:
            raise UnknownCompilerConfigError(
                f"no compiler configuration is registered under '{name}'"
            ) from None

    def list_names(self) -> tuple[str, ...]:
        """Registered names, ordered deterministically."""
        return tuple(sorted(self._configs))

    def __len__(self) -> int:
        return len(self._configs)
