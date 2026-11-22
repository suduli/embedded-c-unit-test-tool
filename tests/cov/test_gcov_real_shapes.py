# implements: TOOL-COV-010, TOOL-COV-020
"""gcov reader against the document shapes real GCC produces (B6).

Fixtures follow the GCC gcov documentation (GCC 14.4, "Invoking Gcov → GCOV
JSON Format") key-for-key — template/inline functions, declarations-only
files, unexecuted blocks, throw branches, version 1 and version 2 documents.
There is still no C compiler on this machine: **real GCC output has not been
checked**; these fixtures exercise the documented shapes the first reader
fixtures did not cover.

Take-aways recorded in the lane ledger: shapes the reader already handles
need no product change; anything these fixtures exposed would be fixed in
src/ectt/cov only.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from ectt.cov.gcov import read_gcov_document
from ectt.cov.metrics import call_coverage, function_coverage
from ectt.cov.model import GcovDocument

# --- C++ shapes: template instantiations and inlined copies ------------------------


def _cpp_template_document() -> dict[str, Any]:
    """A C++ translation unit: two template instantiations (distinct mangled
    names, demangled forms carry the template arguments) plus an inlined copy
    of another file's function. Per the documented function form."""
    return {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "templates.gcda",
        "files": [
            {
                "file": "templates.cpp",
                "functions": [
                    {
                        "blocks": 2,
                        "blocks_executed": 1,
                        "demangled_name": "int maxi<int>(int, int)",
                        "end_column": 1,
                        "end_line": 6,
                        "execution_count": 3,
                        "name": "_Z4maxiIiET_S0_S0_",
                        "start_column": 5,
                        "start_line": 3,
                    },
                    {
                        "blocks": 2,
                        "blocks_executed": 0,
                        "demangled_name": "int maxi<long>(int, int)",
                        "end_column": 1,
                        "end_line": 6,
                        "execution_count": 0,
                        "name": "_Z4maxiIlET_S0_S0_",
                        "start_column": 5,
                        "start_line": 3,
                    },
                    {
                        "blocks": 1,
                        "blocks_executed": 1,
                        "demangled_name": "void helper[with clone inline]",
                        "end_column": 1,
                        "end_line": 2,
                        "execution_count": 3,
                        "name": "_Z6helperv.constprop.0",
                        "start_column": 12,
                        "start_line": 2,
                    },
                ],
                "lines": [
                    {"line_number": 3, "count": 3, "unexecuted_block": False, "function_name": "_Z4maxiIiET_S0_S0_"},
                    {
                        "line_number": 4,
                        "count": 3,
                        "unexecuted_block": False,
                        "function_name": "_Z4maxiIiET_S0_S0_",
                        "branches": [
                            {"count": 3, "destination_block_id": 4, "fallthrough": True, "source_block_id": 2, "throw": False},
                            {"count": 0, "destination_block_id": 5, "fallthrough": False, "source_block_id": 2, "throw": False},
                        ],
                    },
                    {"line_number": 5, "count": 0, "unexecuted_block": True, "function_name": "_Z4maxiIlET_S0_S0_"},
                ],
            }
        ],
    }


def test_cpp_template_instantiations_parse_with_demangled_names() -> None:
    doc = read_gcov_document(_cpp_template_document())
    assert isinstance(doc, GcovDocument)
    (file,) = doc.files
    assert len(file.functions) == 3
    by_name = {fn.name: fn for fn in file.functions}
    assert by_name["_Z4maxiIiET_S0_S0_"].demangled_name == "int maxi<int>(int, int)"
    assert by_name["_Z4maxiIiET_S0_S0_"].execution_count == 3
    assert by_name["_Z4maxiIlET_S0_S0_"].execution_count == 0
    # inlined clone: the demangled form records the inline, the mangled name
    # carries the compiler's clone suffix (documented: name is the function name)
    assert by_name["_Z6helperv.constprop.0"].start_column == 12
    totals = function_coverage([file])
    assert totals == function_coverage([file])
    assert (totals.covered, totals.total) == (2, 3)


def test_same_inline_function_seen_in_several_files() -> None:
    """An inline function in a header is instrumented into every including
    object; each file's functions[] carries its own copy with its own counts."""
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "inline.gcda",
        "files": [
            {
                "file": "a.cpp",
                "functions": [
                    {"blocks": 1, "blocks_executed": 1, "demangled_name": "int sq(int)",
                     "end_column": 1, "end_line": 2, "execution_count": 4,
                     "name": "_Z2sqi", "start_column": 9, "start_line": 1}
                ],
                "lines": [{"line_number": 1, "count": 4, "unexecuted_block": False, "function_name": "_Z2sqi"}],
            },
            {
                "file": "b.cpp",
                "functions": [
                    {"blocks": 1, "blocks_executed": 1, "demangled_name": "int sq(int)",
                     "end_column": 1, "end_line": 2, "execution_count": 1,
                     "name": "_Z2sqi", "start_column": 9, "start_line": 1}
                ],
                "lines": [{"line_number": 1, "count": 1, "unexecuted_block": False, "function_name": "_Z2sqi"}],
            },
        ],
    }
    doc = read_gcov_document(payload)
    assert len(doc.files) == 2
    assert all(file.functions[0].name == "_Z2sqi" for file in doc.files)
    # per-file function coverage counts each object's copy separately
    assert function_coverage(doc.files).total == 2
    assert function_coverage(doc.files).covered == 2


# --- declarations-only file and empty documents -------------------------------------


def test_declarations_only_file_yields_empty_records() -> None:
    """A file whose declarations produced no instrumented code carries empty
    functions[] and lines[] (documented file form; nothing is fabricated)."""
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "decls.gcda",
        "files": [
            {"file": "decls.h", "functions": [], "lines": []},
            {"file": "empty.c", "lines": []},
        ],
    }
    doc = read_gcov_document(payload)
    assert [f.file for f in doc.files] == ["decls.h", "empty.c"]
    assert all(f.functions == () and f.lines == () for f in doc.files)
    assert function_coverage(doc.files).total is None
    assert call_coverage(doc.files).total is None


# --- unexecuted blocks and throw branches -------------------------------------------


def test_unexecuted_blocks_and_throw_branches_are_carried() -> None:
    """verifies: TOOL-COV-010/020 — unexecuted_block flags and throw branches."""
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "throwing.gcda",
        "files": [
            {
                "file": "throwing.cpp",
                "lines": [
                    {
                        "line_number": 7,
                        "count": 2,
                        "unexecuted_block": True,  # not all statements on the line ran
                        "branches": [
                            {"count": 2, "destination_block_id": 9, "fallthrough": True, "source_block_id": 5, "throw": False},
                            # an exceptional branch: present with throw=true, never taken
                            {"count": 0, "destination_block_id": 12, "fallthrough": False, "source_block_id": 5, "throw": True},
                        ],
                    },
                    {"line_number": 9, "count": 0, "unexecuted_block": True},
                ],
            }
        ],
    }
    doc = read_gcov_document(payload)
    (file,) = doc.files
    assert file.lines[0].unexecuted_block is True
    assert file.lines[1].count == 0 and file.lines[1].unexecuted_block is True
    normal, exceptional = file.lines[0].branches
    assert normal.throw is False and normal.count == 2
    assert exceptional.throw is True and exceptional.count == 0
    assert exceptional.fallthrough is False


# --- version 1 and version 2 documents -----------------------------------------------


def test_version_1_document_with_branches() -> None:
    """Version 1 (GCC 9-10) carries branches with -b but no calls/conditions."""
    payload = {
        "format_version": "1",
        "gcc_version": "9.3.0",
        "data_file": "v1.gcda",
        "files": [
            {
                "file": "main.c",
                "functions": [
                    {"blocks": 3, "blocks_executed": 2, "end_column": 1, "end_line": 8,
                     "execution_count": 1, "name": "main", "start_column": 5, "start_line": 3}
                ],
                "lines": [
                    {"line_number": 3, "count": 1, "unexecuted_block": False, "function_name": "main"},
                    {
                        "line_number": 5,
                        "count": 1,
                        "unexecuted_block": False,
                        "function_name": "main",
                        "branches": [
                            {"count": 1, "fallthrough": True, "throw": False},
                            {"count": 0, "fallthrough": False, "throw": False},
                        ],
                    },
                    {"line_number": 8, "count": 0, "unexecuted_block": True, "function_name": "main"},
                ],
            }
        ],
    }
    doc = read_gcov_document(payload)
    assert doc.format_version == "1"
    (file,) = doc.files
    assert file.lines[1].branches[1].count == 0
    assert all(line.calls == () and line.conditions == () for line in file.lines)


def test_version_2_document_with_calls_and_conditions() -> None:
    """Version 2 adds calls; GCC >= 14 adds conditions while staying at v2."""
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "v2.gcda",
        "files": [
            {
                "file": "mixed.c",
                "lines": [
                    {
                        "line_number": 10,
                        "count": 2,
                        "unexecuted_block": False,
                        "block_ids": [3],
                        "calls": [
                            {"destination_block_id": 7, "returned": 2, "source_block_id": 3},
                            {"destination_block_id": 8, "returned": 0, "source_block_id": 3},
                        ],
                        "conditions": [
                            {"count": 2, "covered": 1, "not_covered_false": [], "not_covered_true": [1]}
                        ],
                    },
                    {"line_number": 11, "count": 0, "unexecuted_block": True, "block_ids": [6]},
                ],
            }
        ],
    }
    doc = read_gcov_document(payload)
    (file,) = doc.files
    line = file.lines[0]
    assert line.calls[0].returned == 2 and line.calls[1].returned == 0
    assert call_coverage([file]).covered == 1
    assert line.conditions[0].not_covered_true == (1,)
    # block_ids is accepted on input and deliberately not modelled (documented
    # key, ignored, never interpreted)
    assert not hasattr(file.lines[1], "block_ids")
    assert file.lines[1].line_number == 11


def test_version_2_shape_dumps_canonically_and_round_trips() -> None:
    doc = read_gcov_document(_cpp_template_document())
    dumped = json.loads(doc.to_json_bytes().decode("utf-8"))
    assert next(iter(dumped.keys())) == "schema_version"
    assert doc.to_json_bytes() == read_gcov_document(_cpp_template_document()).to_json_bytes()


@pytest.mark.parametrize(
    "mutation, expected_reason",
    [
        (lambda d: d["files"][0]["functions"][0].__setitem__("execution_count", -1), "missing_or_invalid_key"),
        (lambda d: d["files"][0].__setitem__("functions", "no"), "invalid_optional_key"),
        (lambda d: d["files"][0]["functions"][0].__setitem__("name", ""), "missing_or_invalid_key"),
        (lambda d: d["files"][0]["lines"][0].__setitem__("line_number", 0), "missing_or_invalid_key"),
    ],
)
def test_documented_shapes_still_fail_closed(mutation: Any, expected_reason: str) -> None:
    """The new shapes do not loosen the fail-closed discipline."""
    payload = _cpp_template_document()
    mutation(payload)
    from ectt.cov.errors import CoverageParseError

    with pytest.raises(CoverageParseError) as exc_info:
        read_gcov_document(payload)
    assert exc_info.value.reason == expected_reason
