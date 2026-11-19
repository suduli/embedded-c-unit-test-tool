# implements: TOOL-PAR-140
"""Unsupported-construct inventory population from extraction (WP-ANA-07).

The inventory is carried and schema-gated (1.1+, mandatory per unit) and is
now populated from extraction for the constructs the extractor recognises as
unsupported: variadic tails (not representable in the parameter model) and
variable-length array parameters (not expressible in the type graph).
Deterministic, sorted, emitted even when empty.
"""

from __future__ import annotations

from typing import Any

import pytest

from ectt.ana.frontend import parse
from ectt.ana.interface import extract_interfaces
from ectt.ana.persist import assemble_analysis_model, read_analysis_model
from ectt.core.determinism import FixedClock, canonical_json_bytes

CLEAN = b"int add(int a, int b) { return a + b; }\n"
VARIADIC_DEF = b"int vdef(int n, ...) { return n; }\n"
VARIADIC_TWICE = (
    b"int first(int n, ...) { return n; }\n"
    b"int second(int n, ...) { return n; }\n"
)
VLA_PARAM = b"int vla_sum(int n, int a[n]) { return a[0]; }\n"
SUPPORTED_ARRAYS = (
    b"int fixed_sum(int a[4]) { return a[0]; }\n"
    b"int open_sum(int n, int a[]) { return a[0]; }\n"
)
BOTH_KINDS = b"int mixed(int n, int a[n], ...) { return a[0]; }\n"


def _unit(code: bytes, std: str = "gnu89") -> Any:
    parsed = parse("probe.c", args=[f"-std={std}"], unsaved_files=[("probe.c", code)])
    return extract_interfaces(parsed)


def _assembled_doc(code: bytes, std: str = "gnu89") -> dict[str, Any]:
    parsed = parse("probe.c", args=[f"-std={std}"], unsaved_files=[("probe.c", code)])
    model = assemble_analysis_model(
        [parsed],
        clock=FixedClock("2026-11-19T00:00:00Z"),
        tool_version="test",
        input_digests={"probe.c": "0" * 64},
    )
    doc: dict[str, Any] = model.to_dict()
    return doc


def test_variadic_definition_is_recorded() -> None:
    unit = _unit(VARIADIC_DEF)

    entries = unit.unsupported_constructs
    assert len(entries) == 1
    entry = entries[0]
    assert entry.kind == "variadic_function"
    assert entry.count == 1
    assert entry.detail == "vdef"
    assert entry.location is not None
    assert entry.location.file.endswith("probe.c")
    assert entry.location.line == 1


def test_variadic_occurrences_group_by_count() -> None:
    unit = _unit(VARIADIC_TWICE)

    assert len(unit.unsupported_constructs) == 1
    entry = unit.unsupported_constructs[0]
    assert entry.kind == "variadic_function"
    assert entry.count == 2
    assert entry.detail == "first"  # first occurrence in walk order
    assert entry.location is not None
    assert entry.location.line == 1


def test_vla_parameter_is_recorded() -> None:
    unit = _unit(VLA_PARAM, std="c99")

    entries = [e for e in unit.unsupported_constructs if e.kind == "variable_length_array_parameter"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry.count == 1
    assert entry.detail == "vla_sum.a"
    assert entry.location is not None
    assert entry.location.line == 1


def test_supported_array_kinds_are_not_recorded() -> None:
    """int a[4] (CONSTANTARRAY) and int a[] (INCOMPLETEARRAY) are supported."""
    unit = _unit(SUPPORTED_ARRAYS)

    assert unit.unsupported_constructs == ()


def test_clean_unit_emits_an_empty_inventory() -> None:
    """verifies: TOOL-PAR-140 — emitted even when empty."""
    unit = _unit(CLEAN)
    assert unit.unsupported_constructs == ()

    doc = _assembled_doc(CLEAN)
    assert doc["units"][0]["unsupported_constructs"] == []


def test_inventory_is_sorted_by_kind() -> None:
    unit = _unit(BOTH_KINDS, std="c99")

    kinds = [e.kind for e in unit.unsupported_constructs]
    assert len(kinds) == 2
    assert kinds == sorted(kinds)


def test_inventory_is_deterministic_across_runs() -> None:
    first = tuple(e.to_dict() for e in _unit(VARIADIC_TWICE).unsupported_constructs)
    second = tuple(e.to_dict() for e in _unit(VARIADIC_TWICE).unsupported_constructs)

    assert first == second
    assert len(first) == 1
    assert first[0]["count"] == 2


def test_inventory_flows_through_assembly_and_reader() -> None:
    parsed = parse("probe.c", args=["-std=c99"], unsaved_files=[("probe.c", BOTH_KINDS)])
    model = assemble_analysis_model(
        [parsed],
        clock=FixedClock("2026-11-19T00:00:00Z"),
        tool_version="test",
        input_digests={"probe.c": "0" * 64},
    )
    assert len(model.units[0].unsupported_constructs) == 2

    blob = canonical_json_bytes(model.to_dict(), first_keys=("schema_version",))
    reloaded = read_analysis_model(blob)

    kinds = [e.kind for e in reloaded.units[0].unsupported_constructs]
    assert kinds == sorted(kinds)
    counts = {e.kind: e.count for e in reloaded.units[0].unsupported_constructs}
    assert counts == {"variadic_function": 1, "variable_length_array_parameter": 1}


@pytest.mark.parametrize("std", ["c99"])
def test_vla_and_variadic_mixed_function_detail_locations(std: str) -> None:
    unit = _unit(BOTH_KINDS, std=std)

    for entry in unit.unsupported_constructs:
        assert entry.location is not None
        assert entry.location.file.endswith("probe.c")
        assert entry.location.line == 1
