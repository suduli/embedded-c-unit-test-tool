# implements: DSN-ANA-070, DSN-ANA-040, DSN-ANA-090
"""Tests for Analysis Model persistence, assembly, type merging, and schema version gate.

Satisfies: TOOL-PAR-100, TOOL-PAR-110, DSN-ANA-070, DSN-ANA-040, DSN-ANA-090.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from ectt.ana.errors import (
    AnalysisModelError,
    IncompatibleSchemaVersionError,
    InvalidSchemaVersionOrderError,
    MalformedSchemaVersionError,
    MissingSchemaVersionError,
    TypeClosureError,
    TypeDefinitionConflictError,
)
from ectt.ana.frontend import ClangFrontend
from ectt.ana.interface import extract_interfaces
from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    Diagnostic,
    FunctionModel,
    SourceLocation,
    TypeModel,
)
from ectt.ana.persist import (
    READER_MAJOR,
    READER_MIN_MINOR,
    assemble_analysis_model,
    compute_model_digest,
    load_analysis_model,
    read_analysis_model,
    write_analysis_model,
)
from ectt.core.determinism import FixedClock
from ectt.core.fs import OutputRoot


@pytest.fixture
def sample_c_project(tmp_path: Path) -> tuple[Path, Path]:
    """Create two real C translation units sharing a header and types."""
    src_dir = tmp_path / "src"
    inc_dir = tmp_path / "include"
    src_dir.mkdir(parents=True)
    inc_dir.mkdir(parents=True)

    header = inc_dir / "common.h"
    header.write_text(
        """#ifndef COMMON_H
#define COMMON_H

typedef unsigned short uint16_t;

typedef enum {
    ADC_CH0 = 0,
    ADC_CH1 = 1,
    ADC_CH_MAX
} adc_channel_t;

typedef struct {
    uint16_t raw_value;
    adc_channel_t channel;
} adc_sample_t;

#endif
""",
        encoding="utf-8",
    )

    unit_a = src_dir / "driver.c"
    unit_a.write_text(
        """#include "common.h"

static uint16_t s_last_value = 0;
adc_sample_t g_current_sample;

static uint16_t filter_sample(uint16_t raw) {
    s_last_value = raw;
    return raw;
}

adc_sample_t adc_read(adc_channel_t ch) {
    adc_sample_t sample;
    sample.channel = ch;
    sample.raw_value = filter_sample(1024);
    g_current_sample = sample;
    return sample;
}
""",
        encoding="utf-8",
    )

    unit_b = src_dir / "monitor.c"
    unit_b.write_text(
        """#include "common.h"

static int s_alert_count = 0;

int monitor_check(const adc_sample_t *sample) {
    if (sample->raw_value > 2000) {
        s_alert_count++;
        return 1;
    }
    return 0;
}
""",
        encoding="utf-8",
    )

    return src_dir, inc_dir


def test_real_extraction_assemble_write_read_roundtrip(
    tmp_path: Path,
    sample_c_project: tuple[Path, Path],
) -> None:
    """Verifies: TOOL-PAR-100, TOOL-PAR-110, DSN-ANA-070.

    Real extraction of multiple TUs, model assembly, atomic write through OutputRoot,
    and verified read round-trip.
    """
    src_dir, inc_dir = sample_c_project
    out_dir = tmp_path / "build"
    output_root = OutputRoot(out_dir, source_roots=[src_dir])

    fe = ClangFrontend()
    tu_a = fe.parse(
        src_dir / "driver.c",
        args=["-I", str(inc_dir)],
        working_directory=tmp_path,
    )
    tu_b = fe.parse(
        src_dir / "monitor.c",
        args=["-I", str(inc_dir)],
        working_directory=tmp_path,
    )

    unit_a = extract_interfaces(tu_a, working_directory=tmp_path)
    unit_b = extract_interfaces(tu_b, working_directory=tmp_path)

    clock = FixedClock("2026-09-27T12:00:00Z")
    model = assemble_analysis_model(
        [unit_a, unit_b],
        clock=clock,
        source_root=tmp_path,
    )

    # 1. Document shape assertions per SDD-002 §4.1
    doc = model.to_dict()
    keys = list(doc.keys())
    assert keys[0] == "schema_version"
    assert doc["schema_version"] == "1.0"
    assert "provenance" in doc
    assert "units" in doc
    assert "types" in doc
    assert "capabilities" in doc
    assert doc["capabilities"] == {"cfg": False}

    # Units must not have per-unit types map and cfg must be null
    for u in doc["units"]:
        assert "types" not in u
        assert u["cfg"] is None

    # Write through OutputRoot
    model_path = write_analysis_model(output_root, "analysis/model.json", model)
    assert model_path.exists()

    # Verify on-disk file text formatting (first key is schema_version)
    raw_content = model_path.read_text(encoding="utf-8")
    first_data_line = [line.strip() for line in raw_content.splitlines() if line.strip()][1]
    assert first_data_line.startswith('"schema_version": "1.0"')

    # Read back and verify round-trip
    loaded = read_analysis_model(model_path)
    assert isinstance(loaded, AnalysisModel)
    assert loaded.schema_version == "1.0"
    assert len(loaded.units) == 2
    assert loaded.capabilities == {"cfg": False}
    assert loaded.provenance.generated_at == "2026-09-27T12:00:00+00:00"
    assert len(loaded.provenance.inputs) == 2

    # Check functions and types
    funcs = {f.name for u in loaded.units for f in u.functions}
    assert "adc_read" in funcs
    assert "filter_sample" in funcs
    assert "monitor_check" in funcs


def test_failed_unit_emitted_in_model(tmp_path: Path) -> None:
    """Verifies: DSN-ANA-090, TOOL-PAR-100.

    A translation unit whose parse fails appears in the model with status: 'failed',
    diagnostics, empty functions, and cfg: null.
    """
    src = tmp_path / "broken.c"
    src.write_text("int broken_syntax( { ;;;", encoding="utf-8")

    fe = ClangFrontend()
    parsed_tu = fe.parse(src, working_directory=tmp_path)
    assert parsed_tu.status == "failed"

    clock = FixedClock("2026-09-27T12:00:00Z")
    model = assemble_analysis_model([parsed_tu], clock=clock, source_root=tmp_path)

    doc = model.to_dict()
    assert len(doc["units"]) == 1
    u = doc["units"][0]
    assert u["status"] == "failed"
    assert len(u["diagnostics"]) > 0
    assert u["functions"] == []
    assert u["cfg"] is None


def test_model_wide_types_deduplication(
    sample_c_project: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Verifies: SDD-002 §4.1, TOOL-PAR-100.

    Identical definitions under the same type id across multiple units are deduplicated.
    """
    src_dir, inc_dir = sample_c_project
    fe = ClangFrontend()
    tu_a = fe.parse(src_dir / "driver.c", args=["-I", str(inc_dir)], working_directory=tmp_path)
    tu_b = fe.parse(src_dir / "monitor.c", args=["-I", str(inc_dir)], working_directory=tmp_path)

    unit_a = extract_interfaces(tu_a, working_directory=tmp_path)
    unit_b = extract_interfaces(tu_b, working_directory=tmp_path)

    # Both units share common.h (adc_sample_t, uint16_t, adc_channel_t)
    assert any("adc_sample_t" in k for k in unit_a.types)
    assert any("adc_sample_t" in k for k in unit_b.types)

    clock = FixedClock("2026-09-27T12:00:00Z")
    model = assemble_analysis_model([unit_a, unit_b], clock=clock, source_root=tmp_path)

    # In merged model, shared types exist exactly once
    assert "type.adc_sample_t" in model.types
    assert "type.uint16_t" in model.types
    assert len(model.types) < len(unit_a.types) + len(unit_b.types)
    assert set(model.types.keys()) == set(unit_a.types.keys()) | set(unit_b.types.keys())


def test_type_definition_conflict_raises_error() -> None:
    """Verifies: SDD-002 §4.1.

    Conflicting definitions for the same type ID between two units raises
    TypeDefinitionConflictError naming the ID and both units.
    """
    type_id = "type.struct.Widget"
    loc_a = SourceLocation("src/a.c", 10)
    loc_b = SourceLocation("src/b.c", 20)

    # Two different struct definitions with the same ID
    type_a = TypeModel(kind="struct", name="Widget", location=loc_a, size=4)
    type_b = TypeModel(kind="struct", name="Widget", location=loc_b, size=8)

    unit_a = AnalysisUnit(
        path="src/a.c",
        status="parsed",
        functions=(),
        types={type_id: type_a},
    )
    unit_b = AnalysisUnit(
        path="src/b.c",
        status="parsed",
        functions=(),
        types={type_id: type_b},
    )

    clock = FixedClock()
    with pytest.raises(TypeDefinitionConflictError) as exc_info:
        assemble_analysis_model(
            [unit_a, unit_b],
            clock=clock,
            input_digests={"src/a.c": "a" * 64, "src/b.c": "b" * 64},
        )

    err_str = str(exc_info.value)
    assert type_id in err_str
    assert "src/a.c" in err_str
    assert "src/b.c" in err_str
    assert exc_info.value.type_id == type_id
    assert exc_info.value.unit_a == "src/a.c"
    assert exc_info.value.unit_b == "src/b.c"


def test_type_closure_validation_on_write_and_read() -> None:
    """Verifies: SDD-002 §4.2.

    Dangling type reference (ref:type.*) is rejected on write AND on read.
    """
    # 1. Validation on write
    dangling_func = FunctionModel(
        name="do_work",
        linkage="external",
        storage_class="none",
        location=SourceLocation("src/a.c", 5),
        return_type="ref:type.nonexistent_type",
    )
    unit = AnalysisUnit(
        path="src/a.c",
        status="parsed",
        functions=(dangling_func,),
        types={},
    )
    clock = FixedClock()

    with pytest.raises(TypeClosureError) as exc_info:
        assemble_analysis_model(
            [unit],
            clock=clock,
            input_digests={"src/a.c": "a" * 64},
        )
    assert "ref:type.nonexistent_type" in str(exc_info.value)

    # 2. Validation on read
    valid_doc = {
        "schema_version": "1.0",
        "provenance": {
            "tool_version": "0.1.0",
            "front_end": "libclang 18.1.8",
            "generated_at": "2026-09-27T12:00:00+00:00",
            "inputs": [{"path": "src/a.c", "digest": "0" * 64}],
        },
        "units": [{
            "path": "src/a.c",
            "status": "parsed",
            "diagnostics": [],
            "functions": [{
                "name": "foo",
                "linkage": "external",
                "storage_class": "none",
                "location": {"file": "src/a.c", "line": 1},
                "return_type": "ref:type.missing",
                "parameters": [],
                "globals": [],
            }],
            "cfg": None,
        }],
        "types": {},
        "capabilities": {"cfg": False},
    }

    with pytest.raises(TypeClosureError) as exc_read:
        read_analysis_model(valid_doc)
    assert "ref:type.missing" in str(exc_read.value)


def test_content_digest_stability_under_different_clocks(
    sample_c_project: tuple[Path, Path],
    tmp_path: Path,
) -> None:
    """Verifies: TOOL-PAR-100, SDD-003 §9, TOOL-HAR-110.

    Two runs on the same inputs yield the identical content digest even when clocks differ.
    """
    src_dir, inc_dir = sample_c_project
    fe = ClangFrontend()
    tu = fe.parse(src_dir / "driver.c", args=["-I", str(inc_dir)], working_directory=tmp_path)
    unit = extract_interfaces(tu, working_directory=tmp_path)

    clock_1 = FixedClock("2026-01-01T00:00:00Z")
    clock_2 = FixedClock("2026-12-31T23:59:59Z")

    model_1 = assemble_analysis_model([unit], clock=clock_1, source_root=tmp_path)
    model_2 = assemble_analysis_model([unit], clock=clock_2, source_root=tmp_path)

    # Provenance timestamps differ
    assert model_1.provenance.generated_at != model_2.provenance.generated_at

    # Content digests MUST be identical
    digest_1 = compute_model_digest(model_1)
    digest_2 = compute_model_digest(model_2)
    assert digest_1 == digest_2
    assert len(digest_1) == 64


def test_schema_version_gate_exact_match() -> None:
    """Verifies: TOOL-PAR-110, SDD-002 §3. Exact match accepted."""
    doc = {
        "schema_version": "1.0",
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [],
        "types": {},
        "capabilities": {"cfg": False},
    }
    model = read_analysis_model(doc)
    assert model.schema_version == "1.0"


def test_schema_version_gate_newer_minor_accepted_and_unknown_fields_ignored() -> None:
    """Verifies: TOOL-PAR-110, SDD-002 §3.

    Newer minor version (1.5) with unknown extra fields is accepted and extra fields are ignored.
    """
    doc = {
        "schema_version": "1.5",
        "scope": {"id": "scope.all"},  # unknown extra top-level field
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [{
            "path": "src/a.c",
            "status": "parsed",
            "diagnostics": [],
            "functions": [],
            "cfg": None,
            "future_metadata": {"foo": "bar"},  # unknown extra unit field
        }],
        "types": {},
        "capabilities": {"cfg": False},
    }
    model = read_analysis_model(doc)
    assert model.schema_version == "1.5"
    assert len(model.units) == 1
    assert model.units[0].path == "src/a.c"


@pytest.mark.parametrize("incompatible_version", ["2.0", "0.9", "3.1"])
def test_schema_version_gate_different_major_rejected(incompatible_version: str) -> None:
    """Verifies: TOOL-PAR-110, SDD-002 §3.

    Different major version in both directions (higher or lower) is rejected,
    naming both reader version and document version in the error.
    """
    doc = {
        "schema_version": incompatible_version,
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [],
        "types": {},
        "capabilities": {"cfg": False},
    }
    with pytest.raises(IncompatibleSchemaVersionError) as exc_info:
        read_analysis_model(doc)

    err = exc_info.value
    assert err.reader_version == f"{READER_MAJOR}.{READER_MIN_MINOR}"
    assert err.document_version == incompatible_version
    assert incompatible_version in str(err)
    assert f"{READER_MAJOR}.{READER_MIN_MINOR}" in str(err)


def test_schema_version_gate_missing_rejected() -> None:
    """Verifies: TOOL-PAR-110, SDD-002 §3. Missing schema_version rejected with named reason."""
    doc = {
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [],
        "types": {},
        "capabilities": {"cfg": False},
    }
    with pytest.raises(MissingSchemaVersionError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "missing_schema_version"


def test_schema_version_gate_not_first_key_rejected() -> None:
    """Verifies: TOOL-PAR-110, SDD-002 §3.

    schema_version must be the first key where the encoding has an order.
    """
    json_text = json.dumps({
        "capabilities": {"cfg": False},
        "schema_version": "1.0",
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [],
        "types": {},
    })
    with pytest.raises(InvalidSchemaVersionOrderError) as exc_info:
        read_analysis_model(json_text)
    assert exc_info.value.reason == "schema_version_not_first"


@pytest.mark.parametrize("bad_version", ["v1.0", "1", "1.0.0", "", "1.x", 1.0])
def test_schema_version_gate_malformed_rejected(bad_version: Any) -> None:
    """Verifies: TOOL-PAR-110, SDD-002 §3. Malformed version format rejected with named error."""
    doc = {
        "schema_version": bad_version,
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [],
        "types": {},
        "capabilities": {"cfg": False},
    }
    with pytest.raises(MalformedSchemaVersionError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "malformed_schema_version"


def test_seam_rule_reader_does_not_import_clang() -> None:
    """Verifies: SDD-002 §4 Seam Rule, DSN-ANA-070.

    Downstream loader import graph must never load clang or clang.cindex into sys.modules.
    Tested in an isolated subprocess.
    """
    check_code = """
import sys
import ectt.ana.persist
from ectt.ana.persist import load_analysis_model, read_analysis_model

loaded_clang_modules = [m for m in sys.modules if m == "clang" or m.startswith("clang.")]
assert not loaded_clang_modules, f"Seam violation: clang modules loaded: {loaded_clang_modules}"
"""
    result = subprocess.run(
        [sys.executable, "-c", check_code],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Subprocess failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"


@pytest.mark.parametrize(
    "source",
    [b"{not json", b"\xff\xfe{}", '{"schema_version": "1.0",'],
    ids=["bad-json-bytes", "bad-utf8", "truncated-json-text"],
)
def test_malformed_document_raises_named_error(source: Any) -> None:
    """verifies: TOOL-PAR-110 -- unreadable input is rejected by name, never a bare JSONDecodeError."""
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(source)
    assert exc_info.value.reason == "invalid_json"


def test_missing_model_file_raises_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-PAR-100"""
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(tmp_path / "absent.json")
    assert exc_info.value.reason == "model_read_error"
