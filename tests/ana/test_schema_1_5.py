# implements: TOOL-PAR-050, TOOL-PAR-140, DSN-ANA-070
"""Schema 1.5 additions: function extent, per-occurrence unsupported-construct
records, and the global-variable inventory.

All three are additive: a pre-1.5 document still loads, the new fields are
omitted from emitted documents while unset, and a present field is validated
fail-closed on read (SDD-002 §3).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.ana.eligibility import (
    UnattributedConstruct,
    assess_eligibility,
    find_unattributed_constructs,
)
from ectt.ana.errors import AnalysisModelError, TypeClosureError
from ectt.ana.frontend import parse
from ectt.ana.interface import extract_interfaces
from ectt.ana.model import (
    AnalysisUnit,
    ConstructOccurrenceModel,
    FunctionModel,
    SourceLocation,
    UnsupportedConstructModel,
)
from ectt.ana.persist import (
    SCHEMA_VERSION_CURRENT,
    assemble_analysis_model,
    read_analysis_model,
    write_analysis_model,
)
from ectt.core.determinism import FixedClock, canonical_json_bytes
from ectt.core.fs import OutputRoot

MULTILINE = (
    b"int add(int a, int b)\n"
    b"{\n"
    b"    int sum = a + b;\n"
    b"    return sum;\n"
    b"}\n"
)
VARIADIC_TWICE = (
    b"int first(int n, ...) { return n; }\n"
    b"int second(int n, ...) { return n; }\n"
)
GLOBALS_UNIT = (
    b"int g_plain;\n"
    b"static int s_plain;\n"
    b"int g_init = 42;\n"
    b"static int s_init = 7;\n"
    b"extern int g_extern;\n"
    b"struct box { int v; };\n"
    b"struct box g_box = {3};\n"
    b"int use(void) { return g_plain + s_plain + g_init + s_init + g_extern + g_box.v; }\n"
)


def _unit(code: bytes, std: str = "c11") -> Any:
    parsed = parse("probe.c", args=[f"-std={std}"], unsaved_files=[("probe.c", code)])
    return extract_interfaces(parsed)


def _model(code: bytes, std: str = "c11") -> Any:
    parsed = parse("probe.c", args=[f"-std={std}"], unsaved_files=[("probe.c", code)])
    return assemble_analysis_model(
        [parsed],
        clock=FixedClock("2026-11-21T00:00:00Z"),
        tool_version="test",
        input_digests={"probe.c": "0" * 64},
    )


def _base_doc() -> dict[str, Any]:
    """A minimal parsed unit in the pre-1.5 shape (no 1.5 fields anywhere)."""
    return {
        "schema_version": "1.4",
        "provenance": {"tool_version": "0.1.0", "front_end": "libclang 18.1.8", "generated_at": "...", "inputs": []},
        "units": [
            {
                "path": "src/adc.c",
                "status": "parsed",
                "diagnostics": [],
                "functions": [
                    {
                        "name": "adc",
                        "linkage": "external",
                        "storage_class": "none",
                        "location": {"file": "src/adc.c", "line": 1},
                        "return_type": "ref:type.builtin.int",
                        "parameters": [],
                        "globals": [],
                        "calls": [],
                    }
                ],
                "cfg": None,
                "unsupported_constructs": [
                    {"kind": "variadic_function", "count": 2, "detail": "first",
                     "location": {"file": "src/adc.c", "line": 1}}
                ],
            }
        ],
        "types": {"type.builtin.int": {"kind": "builtin", "name": "int"}},
        "capabilities": {"cfg": False},
        "decision_inventory": {"status": "not_extracted"},
    }


# --- 1. Function extent ------------------------------------------------------


def test_function_extent_populated_from_extraction() -> None:
    unit = _unit(MULTILINE)
    (fn,) = unit.functions
    assert fn.start_line == 1
    assert fn.end_line == 5


def test_extent_round_trips_through_the_reader() -> None:
    model = _model(MULTILINE)
    reloaded = read_analysis_model(canonical_json_bytes(model.to_dict(), first_keys=("schema_version",)))
    (fn,) = reloaded.units[0].functions
    assert (fn.start_line, fn.end_line) == (1, 5)


def test_extent_omitted_while_unset() -> None:
    """A FunctionModel without an extent keeps the pre-1.5 emitted shape."""
    fn = FunctionModel(
        name="adc",
        linkage="external",
        storage_class="none",
        location=SourceLocation("src/adc.c", 1),
        return_type="ref:type.builtin.int",
    )
    doc = fn.to_dict()
    assert "start_line" not in doc and "end_line" not in doc
    restored = FunctionModel.from_dict(doc)
    assert restored.start_line is None and restored.end_line is None


# --- 2. Per-occurrence unsupported-construct records -------------------------


def test_every_occurrence_records_its_owner() -> None:
    unit = _unit(VARIADIC_TWICE)
    (entry,) = unit.unsupported_constructs
    assert entry.count == 2
    assert entry.detail == "first"  # first occurrence in walk order
    owners = [occ.function for occ in entry.occurrences]
    assert owners == ["first", "second"]
    assert [occ.location.line if occ.location else None for occ in entry.occurrences] == [1, 2]
    # entry dict carries the occurrences; count matches
    doc = entry.to_dict()
    assert doc["count"] == len(doc["occurrences"]) == 2


def test_occurrences_round_trip_through_the_reader() -> None:
    model = _model(VARIADIC_TWICE)
    reloaded = read_analysis_model(canonical_json_bytes(model.to_dict(), first_keys=("schema_version",)))
    (entry,) = reloaded.units[0].unsupported_constructs
    assert [occ.function for occ in entry.occurrences] == ["first", "second"]


# --- 3. Global-variable inventory --------------------------------------------


def test_global_variables_recorded_with_type_and_initializer_presence() -> None:
    unit = _unit(GLOBALS_UNIT)
    by_name = {g.name: g for g in unit.global_variables}
    assert set(by_name) == {"g_plain", "s_plain", "g_init", "s_init", "g_extern", "g_box"}
    assert by_name["g_init"].has_initializer is True
    assert by_name["g_box"].has_initializer is True  # INIT_LIST_EXPR
    assert by_name["g_plain"].has_initializer is False  # tentative definition
    assert by_name["s_plain"].has_initializer is False
    assert by_name["g_extern"].has_initializer is False
    assert by_name["s_plain"].storage_class == "static"
    assert by_name["s_init"].storage_class == "static"
    assert by_name["g_extern"].storage_class == "extern"
    assert by_name["g_init"].storage_class == "none"
    for g in by_name.values():
        assert g.type.startswith("ref:type.")
    # every referenced type resolves in the unit type graph
    for g in by_name.values():
        assert g.type[4:] in unit.types
    # deterministic order: sorted by name
    assert [g.name for g in unit.global_variables] == sorted(g.name for g in unit.global_variables)


def test_global_variables_omitted_while_empty() -> None:
    unit = _unit(b"int add(int a, int b) { return a + b; }\n")
    assert unit.global_variables == ()
    assert "global_variables" not in unit.to_dict()


def test_failed_unit_carries_no_global_variables() -> None:
    parsed = parse(
        "bad.c",
        args=["-std=c11"],
        unsaved_files=[("bad.c", b"int broken(void) { return undeclared_symbol; }\n")],
    )
    model = assemble_analysis_model(
        [parsed],
        clock=FixedClock("2026-11-21T00:00:00Z"),
        tool_version="test",
        input_digests={},
    )
    (unit,) = model.units
    assert unit.status == "failed"
    assert unit.global_variables == ()


# --- 4. Older documents still load -------------------------------------------


def test_pre_1_5_document_still_loads() -> None:
    """verifies: SDD-002 §3 -- a historical 1.4 document (no 1.5 fields) reads."""
    model = read_analysis_model(_base_doc())
    assert model.schema_version == "1.4"
    (fn,) = model.units[0].functions
    assert fn.start_line is None and fn.end_line is None
    (entry,) = model.units[0].unsupported_constructs
    assert entry.occurrences == ()
    assert model.units[0].global_variables == ()


def test_current_version_constant_is_1_5() -> None:
    assert SCHEMA_VERSION_CURRENT == "1.6"


# --- 5. Fail-closed reader rules for present 1.5 fields ----------------------


def test_reader_rejects_end_line_before_start_line() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    doc["units"][0]["functions"][0]["start_line"] = 5
    doc["units"][0]["functions"][0]["end_line"] = 2
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "invalid_function_extent"


def test_reader_rejects_non_positive_extent() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    doc["units"][0]["functions"][0]["start_line"] = 0
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "invalid_function_extent"


def test_reader_rejects_occurrence_without_owner_function() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    doc["units"][0]["unsupported_constructs"][0]["occurrences"] = [
        {"function": "first"},
        {"detail": "second"},  # no named owner
    ]
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "invalid_construct_occurrence"


def test_reader_rejects_count_occurrence_mismatch() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    doc["units"][0]["unsupported_constructs"][0]["occurrences"] = [{"function": "first"}]
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)  # count says 2, one occurrence recorded
    assert exc_info.value.reason == "occurrence_count_mismatch"


def test_reader_rejects_invalid_global_variable_record() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    doc["units"][0]["global_variables"] = [
        {"name": "g", "type": "ref:type.builtin.int", "has_initializer": True, "storage_class": "auto"}
    ]
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "invalid_global_variable_record"


def test_reader_rejects_failed_unit_with_global_variables() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    unit = doc["units"][0]
    unit["status"] = "failed"
    unit.pop("functions")
    unit["failure"] = {"reason": "frontend_parse_error", "code": "FrontendParseError",
                       "category": "analysis", "message": "unit not analysed: frontend_parse_error"}
    unit["global_variables"] = [
        {"name": "g", "type": "ref:type.builtin.int", "has_initializer": False, "storage_class": "none"}
    ]
    with pytest.raises(AnalysisModelError) as exc_info:
        read_analysis_model(doc)
    assert exc_info.value.reason == "failed_unit_has_global_variables"


def test_reader_closes_type_refs_of_global_variables() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    doc["units"][0]["global_variables"] = [
        {"name": "g", "type": "ref:type.missing", "has_initializer": False, "storage_class": "none"}
    ]
    with pytest.raises(TypeClosureError):
        read_analysis_model(doc)


def test_valid_1_5_document_round_trips() -> None:
    doc = _base_doc()
    doc["schema_version"] = "1.5"
    fn = doc["units"][0]["functions"][0]
    fn["start_line"] = 1
    fn["end_line"] = 3
    doc["units"][0]["unsupported_constructs"][0]["occurrences"] = [
        {"function": "adc", "detail": "first",
         "location": {"file": "src/adc.c", "line": 1}},
        {"function": "adc", "detail": "second",
         "location": {"file": "src/adc.c", "line": 2}},
    ]
    doc["units"][0]["global_variables"] = [
        {"name": "g_level", "type": "ref:type.builtin.int", "has_initializer": False,
         "storage_class": "none", "location": {"file": "src/adc.c", "line": 2}},
    ]
    model = read_analysis_model(doc)
    reloaded_doc: dict[str, Any] = model.to_dict()
    assert reloaded_doc["units"][0]["functions"][0]["start_line"] == 1
    assert reloaded_doc["units"][0]["functions"][0]["end_line"] == 3
    assert len(reloaded_doc["units"][0]["unsupported_constructs"][0]["occurrences"]) == 2
    assert reloaded_doc["units"][0]["global_variables"][0]["name"] == "g_level"


# --- 6. Determinism ----------------------------------------------------------


def test_two_runs_byte_identical(tmp_path: Any) -> None:
    """Two full extract-assemble-write runs produce byte-identical documents."""
    (tmp_path / "in").mkdir()
    digests: list[bytes] = []
    for run in (1, 2):
        parsed = parse("probe.c", args=["-std=c11"], unsaved_files=[("probe.c", GLOBALS_UNIT)])
        model = assemble_analysis_model(
            [parsed],
            clock=FixedClock("2026-11-21T00:00:00Z"),
            tool_version="test",
            input_digests={"probe.c": "0" * 64},
        )
        out = OutputRoot(tmp_path / f"out{run}", source_roots=[tmp_path / "in"])
        path = write_analysis_model(out, "analysis/model.json", model)
        digests.append(path.read_bytes())
    assert digests[0] == digests[1]
    doc = json.loads(digests[0].decode("utf-8"))
    (fn,) = doc["units"][0]["functions"]
    assert fn["start_line"] == 8 and fn["end_line"] == 8  # `use` is the unit's only function
    assert doc["units"][0]["global_variables"]


# --- 7. Eligibility names every occurrence owner -----------------------------


def test_eligibility_attributes_each_occurrence_owner() -> None:
    unit = _unit(VARIADIC_TWICE)
    records = {r.function: r for r in assess_eligibility([unit])}
    assert records["first"].reasons == ("unsupported_construct:variadic_function",)
    assert records["second"].reasons == ("unsupported_construct:variadic_function",)
    assert find_unattributed_constructs([unit]) == ()


def test_eligibility_falls_back_for_models_without_occurrences() -> None:
    """A pre-1.5 unit (occurrences empty) keeps the first-occurrence heuristic:
    the construct detail names the owner, the first occurrence is attributed,
    and the remaining count stays unattributed."""
    doc = _base_doc()
    doc["units"][0]["unsupported_constructs"][0]["detail"] = "adc"
    model = read_analysis_model(doc)
    records = {r.function: r for r in assess_eligibility(model.units)}
    assert records["adc"].reasons == ("unsupported_construct:variadic_function",)
    assert find_unattributed_constructs(model.units) == (UnattributedConstruct("src/adc.c", "variadic_function", 1),)


def test_unattributed_remainder_counts_unnamed_occurrences() -> None:
    """Occurrences naming functions absent from the unit stay unattributed:
    the owning function gets no gate reason and the full count remains."""
    unit = AnalysisUnit(
        path="src/adc.c",
        status="parsed",
        functions=(FunctionModel(
            name="adc",
            linkage="external",
            storage_class="none",
            location=SourceLocation("src/adc.c", 1),
            return_type="ref:type.builtin.int",
        ),),
        unsupported_constructs=(
            UnsupportedConstructModel(
                kind="variadic_function",
                count=2,
                detail="first",
                location=SourceLocation("src/adc.c", 1),
                occurrences=(
                    ConstructOccurrenceModel(function="first", detail="first", location=SourceLocation("src/adc.c", 1)),
                    ConstructOccurrenceModel(function="ghost", detail="ghost", location=SourceLocation("src/adc.c", 2)),
                ),
            ),
        ),
    )
    records = {r.function: r for r in assess_eligibility([unit])}
    assert records["adc"].reasons == ()
    assert find_unattributed_constructs([unit]) == (UnattributedConstruct("src/adc.c", "variadic_function", 2),)
