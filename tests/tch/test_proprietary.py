"""Tests for the WP-TCH-06 proprietary compiler support.

Verifies: TOOL-TCH-100.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from ectt.tch import (
    CompilerConfigRegistry,
    load_compiler_config,
    load_compiler_config_text,
)
from ectt.tch.proprietary import (
    PROPRIETARY_FAMILIES,
    ProprietaryConfigError,
    ProprietaryFamily,
    proprietary_families,
)

_ARMCLANG_YAML = """\
schema_version: 1
name: keil-armclang
family: armclang
invocation:
  executable: armclang
  compile_only_flag: "-c"
  output_flag: "-o"
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
    size: ["-Oz"]
    speed: ["-O2"]
output:
  object_suffix: ".o"
  executable_suffix: ".axf"
coverage:
  kinds: [line]
  flags:
    line: ["--coverage"]
"""

_IAR_YAML = """\
schema_version: 1
name: iar-iccarm
family: iar
invocation:
  executable: iccarm
flags:
  debug: ["--debug"]
  optimization:
    size: ["-Oz"]
output:
  object_suffix: ".o"
  executable_suffix: ".out"
coverage:
  kinds: [line]
  flags:
    line: ["--coverage"]
"""


def test_proprietary_roster_covers_the_srs_families() -> None:
    """verifies: TOOL-TCH-100"""
    families = proprietary_families()
    assert {item.family for item in families} == {
        "armcc",
        "armclang",
        "iar",
        "tasking",
        "greenhills",
    }
    assert {item.family for item in families} == PROPRIETARY_FAMILIES


def test_every_roster_family_documents_scriptability() -> None:
    """verifies: TOOL-TCH-100"""
    for item in proprietary_families():
        assert isinstance(item, ProprietaryFamily)
        assert item.compilers
        assert item.note.strip()
        assert isinstance(item.externally_scriptable, bool)


def test_keil_armclang_config_loads_end_to_end(tmp_path: Path) -> None:
    """verifies: TOOL-TCH-100"""
    config_path = tmp_path / "keil-armclang.yaml"
    config_path.write_text(_ARMCLANG_YAML, encoding="utf-8")
    registry = CompilerConfigRegistry()
    registry.register(load_compiler_config(config_path))
    config = registry.lookup("keil-armclang")
    assert config.family == "armclang"
    assert config.invocation.executable == "armclang"
    assert config.output.executable_suffix == ".axf"
    assert config.coverage_kinds == {"line"}


def test_iar_config_loads_through_the_public_text_path() -> None:
    """verifies: TOOL-TCH-100"""
    config = load_compiler_config_text(_IAR_YAML)
    assert config.family == "iar"
    assert config.invocation.executable == "iccarm"


def test_roster_is_frozen_and_deterministic() -> None:
    """verifies: TOOL-TCH-100"""
    first = [item.to_dict() for item in proprietary_families()]
    second = [item.to_dict() for item in proprietary_families()]
    assert first == second
    assert dataclasses.is_dataclass(ProprietaryFamily)
    item = proprietary_families()[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.family = "mutated"  # type: ignore[misc]


def test_proprietary_error_derives_from_tch_error() -> None:
    """verifies: TOOL-TCH-100"""
    from ectt.tch import TchError

    assert issubclass(ProprietaryConfigError, TchError)
