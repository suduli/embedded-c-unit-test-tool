# implements: TOOL-COV-190
"""MC/DC version gate and the probed condition limit."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.tch.builtin import built_in_host_configs
from ectt.tch.config import CompilerConfig
from ectt.tch.mcdc import plan_mcdc, probe_condition_limit

EVIDENCE = Path(__file__).parent / "fixtures" / "gcc-14.4.0-condition-limit.json"


def _config(name: str) -> CompilerConfig:
    return next(config for config in built_in_host_configs() if config.name == name)


def _fake_compiler(limit: int):
    def run(source: str, flags: tuple[str, ...]) -> tuple[bool, str]:
        assert "-fcondition-coverage" in flags
        count = source.count("int c")
        warning = "warning: Too many conditions [-Wcoverage-too-many-conditions]"
        return True, warning if count > limit else ""

    return run


@pytest.mark.parametrize("limit", [2, 63, 64, 65, 700])
def test_the_probe_finds_the_compiler_limit(limit: int) -> None:
    assert probe_condition_limit(_fake_compiler(limit)).max_conditions == limit


def test_a_failing_compiler_is_unknown_never_a_number() -> None:
    probe = probe_condition_limit(lambda source, flags: (False, "error"))
    assert probe.max_conditions is None
    assert "did not compile" in probe.detail


def test_no_limit_found_is_unknown() -> None:
    assert probe_condition_limit(lambda source, flags: (True, "")).max_conditions is None


def test_recorded_real_probe_of_gcc_14() -> None:
    """The committed evidence of a probe run on GCC 14.4.0."""
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["max_conditions"] == 64
    assert {"conditions": 65, "instrumented": False} in evidence["attempts"]


def test_gcc_14_gets_the_flags_and_the_stated_form() -> None:
    probe = probe_condition_limit(_fake_compiler(64))
    plan = plan_mcdc(_config("gcc"), "gcc (GCC) 14.4.0", probe)
    assert plan.available and plan.reason is None
    assert plan.compile_flags == ("--coverage", "-fcondition-coverage")
    assert plan.gcov_flags == ("--conditions",)
    assert (plan.form, plan.compiler_version, plan.max_conditions) == ("masking", "14.4", 64)


@pytest.mark.parametrize(
    ("name", "version", "reason"),
    [
        ("gcc", "gcc (GCC) 13.3.0", "mcdc_not_available"),
        ("clang", "clang version 18.1.8", "mcdc_not_available"),
        ("gcc", "no digits here", "mcdc_version_unknown"),
    ],
)
def test_unsuitable_compilers_are_named_and_add_no_flags(name: str, version: str, reason: str) -> None:
    plan = plan_mcdc(_config(name), version)
    assert not plan.available
    assert plan.reason == reason
    assert plan.compile_flags == () and plan.gcov_flags == ()
