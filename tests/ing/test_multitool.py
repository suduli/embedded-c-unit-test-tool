"""Tests for the WP-ING-06 multi-toolchain ingestion.

Verifies: TOOL-ING-110.
"""

from __future__ import annotations

import pytest

from ectt.ing.model import CompilerInvocation, TranslationUnit
from ectt.ing.multitool import (
    MultiToolchainIngestion,
    ToolchainEntry,
    UnknownToolchainError,
    ingest_multi_toolchain,
)


def _unit(source: str, arguments: tuple[str, ...], working_dir: str = "/proj") -> TranslationUnit:
    return TranslationUnit(
        source_path=source,
        working_directory=working_dir,
        include_paths=tuple(a[2:] for a in arguments if a.startswith("-I")),
        compiler_invocation=CompilerInvocation(
            executable="cc", arguments=arguments, target_triple=None
        ),
    )


def _entries() -> tuple[ToolchainEntry, ...]:
    return (
        ToolchainEntry(
            toolchain="arm-gcc",
            unit=_unit("src/main.c", ("-Iarm_inc", "-DARM", "-mcpu=cortex-m4", "src/main.c")),
        ),
        ToolchainEntry(
            toolchain="riscv-gcc",
            unit=_unit("src/main.c", ("-Iriscv_inc", "-DRISCV", "-march=rv32i", "src/main.c")),
        ),
        ToolchainEntry(
            toolchain="arm-gcc",
            unit=_unit("src/util.c", ("-Iarm_inc", "-O2", "src/util.c")),
        ),
    )


def test_multi_toolchain_ingestion_groups_per_toolchain() -> None:
    """verifies: TOOL-ING-110"""
    ingestion = ingest_multi_toolchain(_entries())
    assert isinstance(ingestion, MultiToolchainIngestion)
    assert ingestion.toolchains == ("arm-gcc", "riscv-gcc")
    assert len(ingestion.database_for("arm-gcc")) == 2
    assert len(ingestion.database_for("riscv-gcc")) == 1


def test_same_source_stays_distinct_per_toolchain() -> None:
    """verifies: TOOL-ING-110"""
    ingestion = ingest_multi_toolchain(_entries())
    arm_flags = ingestion.flags_for("arm-gcc", "src/main.c")
    riscv_flags = ingestion.flags_for("riscv-gcc", "src/main.c")
    assert arm_flags != riscv_flags
    assert arm_flags == ("-Iarm_inc", "-DARM", "-mcpu=cortex-m4", "src/main.c")
    assert riscv_flags == ("-Iriscv_inc", "-DRISCV", "-march=rv32i", "src/main.c")


def test_per_toolchain_flags_retained_verbatim() -> None:
    """verifies: TOOL-ING-110"""
    ingestion = ingest_multi_toolchain(_entries())
    assert ingestion.flags_for("arm-gcc", "src/util.c") == ("-Iarm_inc", "-O2", "src/util.c")


def test_unknown_toolchain_is_named_error() -> None:
    """verifies: TOOL-ING-110"""
    ingestion = ingest_multi_toolchain(_entries())
    with pytest.raises(UnknownToolchainError):
        ingestion.database_for("avr-gcc")
    with pytest.raises(UnknownToolchainError):
        ingestion.flags_for("avr-gcc", "src/main.c")


def test_source_not_under_toolchain_is_named_error() -> None:
    """verifies: TOOL-ING-110"""
    ingestion = ingest_multi_toolchain(_entries())
    with pytest.raises(UnknownToolchainError):
        ingestion.flags_for("riscv-gcc", "src/util.c")


def test_build_tags_per_toolchain() -> None:
    """verifies: TOOL-ING-110"""
    ingestion = ingest_multi_toolchain(_entries())
    assert ingestion.database_for("arm-gcc").build_tag == "arm-gcc"
    assert ingestion.database_for("riscv-gcc").build_tag == "riscv-gcc"
    tagged = ingest_multi_toolchain(
        _entries(), build_tags={"arm-gcc": "fw-debug-arm", "riscv-gcc": "fw-debug-rv"}
    )
    assert tagged.database_for("arm-gcc").build_tag == "fw-debug-arm"


def test_ingestion_is_deterministic_and_serialisable() -> None:
    """verifies: TOOL-ING-110"""
    first = ingest_multi_toolchain(_entries())
    second = ingest_multi_toolchain(tuple(reversed(_entries())))
    assert first.to_dict() == second.to_dict()


def test_blank_toolchain_name_rejected() -> None:
    """verifies: TOOL-ING-110"""
    with pytest.raises(UnknownToolchainError):
        ToolchainEntry(toolchain="  ", unit=_unit("src/main.c", ("src/main.c",)))
