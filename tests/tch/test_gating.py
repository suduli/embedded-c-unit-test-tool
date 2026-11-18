"""Tests for the WP-TCH-04 capability and version gating.

Verifies: TOOL-TCH-060, TOOL-TCH-070.
"""

from __future__ import annotations

import dataclasses

import pytest

from ectt.tch import (
    CompilerConfig,
    TchError,
    UnsupportedMetricError,
    load_compiler_config_text,
)
from ectt.tch.gating import (
    FEATURE_VERSION_REQUIREMENTS,
    UnknownFeatureError,
    VersionGate,
    VersionRequirementError,
    check_version,
    gate_metrics,
    parse_compiler_version,
)

_GCC_CONFIG = """\
schema_version: 1
name: gcc
family: gcc
invocation:
  executable: gcc
flags:
  debug: ["-g"]
  optimization:
    none: ["-O0"]
output:
  object_suffix: ".o"
  executable_suffix: ""
coverage:
  kinds: [line, branch]
  flags:
    line: ["--coverage"]
    branch: ["--coverage"]
"""


def _gcc() -> CompilerConfig:
    return load_compiler_text()


def load_compiler_text() -> CompilerConfig:
    return load_compiler_config_text(_GCC_CONFIG)


def test_supported_metrics_pass_the_gate() -> None:
    """verifies: TOOL-TCH-060"""
    gate = gate_metrics(_gcc(), ("line", "branch"))
    assert gate.granted == ("line", "branch")
    assert gate.refused == ()
    assert gate.config == "gcc"


def test_unsupported_metric_refused_with_names() -> None:
    """verifies: TOOL-TCH-060"""
    with pytest.raises(UnsupportedMetricError) as excinfo:
        gate_metrics(_gcc(), ("line", "mcdc"))
    assert "gcc" in str(excinfo.value)
    assert "mcdc" in str(excinfo.value)


def test_version_parsed_from_realistic_compiler_output() -> None:
    """verifies: TOOL-TCH-070"""
    assert parse_compiler_version("gcc (GCC) 14.1.0") == (14, 1)
    assert parse_compiler_version("Ubuntu clang version 18.1.3") == (18, 1)
    assert parse_compiler_version("gcc (GCC) 13.2.1 20230909") == (13, 2)


def test_version_without_number_is_named_error() -> None:
    """verifies: TOOL-TCH-070"""
    with pytest.raises(VersionRequirementError):
        parse_compiler_version("no version here")


def test_mcdc_requires_gcc_14() -> None:
    """verifies: TOOL-TCH-070"""
    gate = check_version("mcdc", "gcc", "gcc (GCC) 14.1.0")
    assert isinstance(gate, VersionGate)
    assert gate.supported is True
    assert "14.1" in gate.message
    refused = check_version("mcdc", "gcc", "gcc (GCC) 13.2.1")
    assert refused.supported is False
    assert ">= 14.0" in refused.message


def test_mcdc_requires_clang_18() -> None:
    """verifies: TOOL-TCH-070"""
    assert check_version("mcdc", "clang", "Ubuntu clang version 18.1.3").supported
    assert not check_version("mcdc", "clang", "Ubuntu clang version 17.0.6").supported


def test_unknown_feature_is_named_error() -> None:
    """verifies: TOOL-TCH-070"""
    with pytest.raises(UnknownFeatureError):
        check_version("psychic_coverage", "gcc", "gcc (GCC) 14.1.0")
    with pytest.raises(UnknownFeatureError):
        check_version("mcdc", "icc", "icc 2021.1")
    assert set(FEATURE_VERSION_REQUIREMENTS) == {"mcdc"}


def test_gate_verdicts_are_frozen_and_deterministic() -> None:
    """verifies: TOOL-TCH-070"""
    first = check_version("mcdc", "gcc", "gcc (GCC) 14.1.0")
    second = check_version("mcdc", "gcc", "gcc (GCC) 14.1.0")
    assert first.message == second.message
    assert dataclasses.is_dataclass(first)
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.supported = False  # type: ignore[misc]


def test_gating_errors_derive_from_tch_error() -> None:
    """verifies: TOOL-TCH-060"""
    for cls in (UnsupportedMetricError, VersionRequirementError, UnknownFeatureError):
        assert issubclass(cls, TchError)
