# implements: DSN-ING-010
"""Tests for compilation database and translation unit models.

Verifies: TOOL-ING-010, TOOL-ING-020, TOOL-ING-030, DSN-ING-010.
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from ectt.ing.model import (
    CompilationDatabase,
    CompilerInvocation,
    TranslationUnit,
)


def test_compiler_invocation_properties_and_serialization() -> None:
    """verifies: TOOL-ING-030, DSN-ING-010"""
    inv = CompilerInvocation(
        executable="gcc",
        arguments=("gcc", "-Wall", "-O2", "-c", "main.c"),
        residual_flags=("-Wall", "-O2"),
    )
    assert inv.executable == "gcc"
    assert inv.arguments == ("gcc", "-Wall", "-O2", "-c", "main.c")
    assert inv.residual_flags == ("-Wall", "-O2")

    d = inv.to_dict()
    assert d == {
        "executable": "gcc",
        "arguments": ["gcc", "-Wall", "-O2", "-c", "main.c"],
        "residual_flags": ["-Wall", "-O2"],
    }

    # Verify frozen immutability
    with pytest.raises(FrozenInstanceError):
        inv.executable = "clang"  # type: ignore[misc]


def test_translation_unit_properties_and_definitions_map() -> None:
    """verifies: TOOL-ING-030, DSN-ING-010"""
    inv = CompilerInvocation(
        executable="arm-none-eabi-gcc",
        arguments=("arm-none-eabi-gcc", "-c", "src/adc/adc.c"),
        residual_flags=("-mcpu=cortex-m4",),
    )
    tu = TranslationUnit(
        source_path="src/adc/adc.c",
        working_directory="build",
        include_paths=("include", "src/adc"),
        preprocessor_definitions=("DEBUG", "CHANNELS=4", "VERSION=\"1.0\""),
        compiler_invocation=inv,
        language_standard="c99",
        output_file="build/adc.o",
    )

    assert tu.file == "src/adc/adc.c"
    assert tu.directory == "build"
    assert tu.compiler == "arm-none-eabi-gcc"
    assert tu.arguments == ("arm-none-eabi-gcc", "-c", "src/adc/adc.c")
    assert tu.residual_flags == ("-mcpu=cortex-m4",)
    assert tu.language_standard == "c99"
    assert tu.output_file == "build/adc.o"

    # Verify definitions_map parsing
    defs = tu.definitions_map
    assert defs["DEBUG"] is None
    assert defs["CHANNELS"] == "4"
    assert defs["VERSION"] == "\"1.0\""

    # Verify to_dict structure
    d = tu.to_dict()
    assert d["source_path"] == "src/adc/adc.c"
    assert d["working_directory"] == "build"
    assert d["include_paths"] == ["include", "src/adc"]
    assert d["preprocessor_definitions"] == ["DEBUG", "CHANNELS=4", "VERSION=\"1.0\""]
    assert d["language_standard"] == "c99"
    assert d["output_file"] == "build/adc.o"
    assert d["compiler_invocation"]["executable"] == "arm-none-eabi-gcc"

    # Verify frozen immutability
    with pytest.raises(FrozenInstanceError):
        tu.source_path = "other.c"  # type: ignore[misc]


def test_compilation_database_queries_and_determinism() -> None:
    """verifies: TOOL-ING-010, TOOL-ING-030, DSN-ING-010"""
    tu1 = TranslationUnit(
        source_path="src/adc/adc.c",
        working_directory="build",
        compiler_invocation=CompilerInvocation(executable="gcc"),
    )
    tu2 = TranslationUnit(
        source_path="src/pwm/pwm.c",
        working_directory="build",
        compiler_invocation=CompilerInvocation(executable="gcc"),
    )
    db = CompilationDatabase(translation_units=(tu1, tu2))

    assert len(db) == 2
    assert list(db) == [tu1, tu2]
    assert db[0] == tu1
    assert db[1] == tu2

    # Query by source path
    assert db.get("src/adc/adc.c") == tu1
    assert db.get(r"src\adc\adc.c") == tu1  # Windows backslash query
    assert db.get("nonexistent.c") is None

    assert db.filter_by_source("src/pwm/pwm.c") == [tu2]
    assert db.source_paths == ["src/adc/adc.c", "src/pwm/pwm.c"]

    # Test canonical JSON determinism
    json_repr1 = db.canonical_json()
    json_repr2 = db.canonical_json()
    assert json_repr1 == json_repr2

    parsed = json.loads(json_repr1)
    assert len(parsed["translation_units"]) == 2
    assert parsed["translation_units"][0]["source_path"] == "src/adc/adc.c"
