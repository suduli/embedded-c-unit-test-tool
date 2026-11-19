"""Tests for the WP-BLD-02 sanitizer integration.

Covers: opt-in by default, flag/environment computation, unknown-mode
rejection, run-output classification into findings, and determinism.

Verifies: TOOL-EXE-090.
"""

from __future__ import annotations

import pytest

from ectt.bld import (
    SANITIZER_ADDRESS,
    SANITIZER_UNDEFINED,
    InvalidSanitizerModeError,
    SanitizerFinding,
    SanitizerSettings,
    classify_run_output,
    sanitizer_compile_flags,
    sanitizer_runtime_env,
)


def test_default_settings_enable_nothing() -> None:
    """verifies: TOOL-EXE-090"""
    settings = SanitizerSettings()
    assert settings.modes == frozenset()
    assert sanitizer_compile_flags(settings) == ()
    assert sanitizer_runtime_env(settings) == {}
    assert classify_run_output("all tests passed\n") == ()


def test_address_mode_produces_documented_flags() -> None:
    """verifies: TOOL-EXE-090"""
    settings = SanitizerSettings(modes=frozenset({SANITIZER_ADDRESS}))
    assert sanitizer_compile_flags(settings) == ("-fsanitize=address",)
    env = sanitizer_runtime_env(settings)
    assert env["ASAN_OPTIONS"] == "halt_on_error=1"


def test_combined_modes_produce_one_merged_flag() -> None:
    """verifies: TOOL-EXE-090"""
    settings = SanitizerSettings(modes=frozenset({SANITIZER_ADDRESS, SANITIZER_UNDEFINED}))
    assert sanitizer_compile_flags(settings) == ("-fsanitize=address,undefined",)


def test_halt_on_error_false_is_recorded_in_env() -> None:
    """verifies: TOOL-EXE-090"""
    settings = SanitizerSettings(modes=frozenset({SANITIZER_ADDRESS}), halt_on_error=False)
    assert sanitizer_runtime_env(settings)["ASAN_OPTIONS"] == "halt_on_error=0"


def test_unknown_mode_is_named_error() -> None:
    """verifies: TOOL-EXE-090"""
    with pytest.raises(InvalidSanitizerModeError) as excinfo:
        SanitizerSettings(modes=frozenset({"psychic"}))
    assert "psychic" in str(excinfo.value)


def test_settings_and_flags_are_deterministic() -> None:
    """verifies: TOOL-EXE-090"""
    settings = SanitizerSettings(modes=frozenset({SANITIZER_ADDRESS, SANITIZER_UNDEFINED}))
    assert settings.to_dict() == settings.to_dict()
    assert sanitizer_compile_flags(settings) == sanitizer_compile_flags(
        SanitizerSettings(modes=frozenset({SANITIZER_UNDEFINED, SANITIZER_ADDRESS}))
    )


ASAN_OUTPUT = """\
test_one PASSED
=================================================================
==123==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x60200000eff1
WRITE of size 4 at 0x60200000eff1 thread T0
    #0 0x4011f6 in compute src/uut.c:12
SUMMARY: AddressSanitizer: heap-buffer-overflow src/uut.c:12
=================================================================
"""

UBSAN_OUTPUT = """\
src/uut.c:44:9: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'
SUMMARY: UndefinedBehaviorSanitizer: signed-integer-overflow src/uut.c:44
"""


def test_asan_output_yields_structured_finding() -> None:
    """verifies: TOOL-EXE-090"""
    findings = classify_run_output(ASAN_OUTPUT)
    assert findings, "the ASan diagnostic block must produce findings"
    kinds = {f.sanitizer for f in findings}
    assert "address" in kinds
    summary = next(f for f in findings if f.sanitizer == "address")
    assert "heap-buffer-overflow" in summary.summary
    assert isinstance(summary, SanitizerFinding)


def test_ubsan_output_yields_structured_finding() -> None:
    """verifies: TOOL-EXE-090"""
    findings = classify_run_output(UBSAN_OUTPUT)
    assert findings
    assert {f.sanitizer for f in findings} == {"undefined"}
    assert "signed integer overflow" in findings[0].summary


def test_plain_output_yields_no_findings() -> None:
    """verifies: TOOL-EXE-090"""
    assert classify_run_output("PASS\nPASS\n2 tests, 0 failures\n") == ()
    assert classify_run_output("") == ()


def test_finding_does_not_depend_on_test_verdict() -> None:
    """verifies: TOOL-EXE-090"""
    # A run whose tests all "passed" but whose process printed a sanitizer
    # diagnostic still yields the finding: sanitizers report independently.
    findings = classify_run_output("2 tests, 0 failures\n" + ASAN_OUTPUT)
    assert any(f.sanitizer == "address" for f in findings)


def test_finding_order_follows_output_order() -> None:
    """verifies: TOOL-EXE-090"""
    findings = classify_run_output(UBSAN_OUTPUT)
    assert [f.summary for f in findings] == [
        line.strip()
        for line in UBSAN_OUTPUT.splitlines()
        if "runtime error" in line or "SUMMARY" in line
    ]
