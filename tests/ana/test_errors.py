# implements: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090
"""Unit tests for ectt.ana error hierarchy.

Verifies: TOOL-PAR-010, TOOL-PAR-020, DSN-ANA-090.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.ana.errors import (
    AnalysisError,
    DialectError,
    ExtractionError,
    ExtractionRefusedError,
    FrontendParseError,
    LibclangError,
    LibclangLoadError,
    LibclangNotFoundError,
    LibclangVersionError,
    SourceFileNotFoundError,
    UnsupportedDialectError,
)
from ectt.core.determinism import CoreError


def test_error_hierarchy_inherits_core_error() -> None:
    """verifies: TOOL-PAR-010, DSN-ANA-090"""
    err = AnalysisError("Base analysis error", reason="analysis_failure", path="src/main.c")
    assert isinstance(err, CoreError)
    assert isinstance(err, Exception)
    assert err.reason == "analysis_failure"
    assert err.path == Path("src/main.c")
    assert "Base analysis error" in str(err)
    assert "reason=analysis_failure" in str(err)
    assert "path=src" in str(err)


def test_libclang_errors() -> None:
    """verifies: TOOL-PAR-010"""
    not_found = LibclangNotFoundError()
    assert isinstance(not_found, LibclangError)
    assert isinstance(not_found, AnalysisError)
    assert not_found.reason == "libclang_not_found"

    load_err = LibclangLoadError("DLL load failed", path="libclang.dll")
    assert isinstance(load_err, LibclangError)
    assert load_err.reason == "libclang_load_error"
    assert "DLL load failed" in str(load_err)

    ver_err = LibclangVersionError(
        "Version 16.0 below floor",
        version="16.0.0",
        floor="18.1",
        reason="libclang_version_below_floor",
    )
    assert isinstance(ver_err, LibclangError)
    assert ver_err.version == "16.0.0"
    assert ver_err.floor == "18.1"
    assert "floor=18.1" in str(ver_err)
    assert "version=16.0.0" in str(ver_err)


def test_dialect_errors() -> None:
    """verifies: TOOL-PAR-020"""
    dia_err = DialectError("Dialect issue", dialect="c99", path="foo.c")
    assert isinstance(dia_err, AnalysisError)
    assert dia_err.dialect == "c99"
    assert "dialect=c99" in str(dia_err)

    unsupported = UnsupportedDialectError(
        "Unsupported C standard: c999",
        dialect="c999",
        path="foo.c",
    )
    assert isinstance(unsupported, DialectError)
    assert unsupported.dialect == "c999"
    assert unsupported.reason == "unsupported_dialect"


def test_parse_and_source_file_errors() -> None:
    """verifies: TOOL-PAR-010, DSN-ANA-090"""
    fnf = SourceFileNotFoundError("File not found: nonexistent.c", path="nonexistent.c")
    assert isinstance(fnf, AnalysisError)
    assert fnf.reason == "source_file_not_found"
    assert fnf.path == Path("nonexistent.c")

    fpe = FrontendParseError("Fatal parse error", path="corrupt.c")
    assert isinstance(fpe, AnalysisError)
    assert fpe.reason == "frontend_parse_error"


def test_extraction_errors() -> None:
    """verifies: TOOL-PAR-030, DSN-ANA-020, DSN-ANA-090"""
    exc = ExtractionError("General extraction error", path="src/main.c", reason="extraction_error")
    assert isinstance(exc, AnalysisError)
    assert exc.reason == "extraction_error"
    assert exc.path == Path("src/main.c")
    assert "General extraction error" in str(exc)

    refused = ExtractionRefusedError(
        "Unit parse failed with diagnostics",
        path="src/main.c",
        reason="extraction_refused_failed_unit",
    )
    assert isinstance(refused, ExtractionError)
    assert isinstance(refused, AnalysisError)
    assert refused.reason == "extraction_refused_failed_unit"
    assert refused.path == Path("src/main.c")
    assert "extraction_refused_failed_unit" in str(refused)
