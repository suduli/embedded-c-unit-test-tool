# implements: DSN-ANA-020
"""Tests for function interface and global variable extraction (CMP-ANA).

Verifies: TOOL-PAR-030, TOOL-PAR-050, DSN-ANA-020.
"""

from __future__ import annotations

import os

import pytest

from ectt.ana.errors import ExtractionRefusedError
from ectt.ana.frontend import parse
from ectt.ana.interface import extract, extract_interfaces
from ectt.ana.model import AnalysisUnit, FunctionModel


def test_function_storage_class_and_linkage() -> None:
    """verifies: TOOL-PAR-030, DSN-ANA-020"""
    code = b"""
    int ext_fn(int a) {
        return a * 2;
    }

    static int static_fn(int b) {
        return b + 1;
    }

    inline int inline_fn(int c) {
        return c - 1;
    }

    static inline int static_inline_fn(int d) {
        return d * 3;
    }
    """
    ptu = parse("funcs.c", args=["-std=c99"], unsaved_files=[("funcs.c", code)])
    unit = extract_interfaces(ptu)

    assert isinstance(unit, AnalysisUnit)
    assert len(unit.functions) == 4

    fn_map = {f.name: f for f in unit.functions}

    # External function
    ext = fn_map["ext_fn"]
    assert ext.linkage == "external"
    assert ext.storage_class == "none"
    assert ext.location.file == "funcs.c"
    assert ext.location.line == 2

    # Static function
    st = fn_map["static_fn"]
    assert st.linkage == "internal"
    assert st.storage_class == "static"
    assert st.location.line == 6

    # Inline function (external linkage, storage none)
    inl = fn_map["inline_fn"]
    assert inl.linkage == "external"
    assert inl.storage_class == "none"

    # Static inline function (internal linkage, storage static)
    st_inl = fn_map["static_inline_fn"]
    assert st_inl.linkage == "internal"
    assert st_inl.storage_class == "static"


def test_function_declaration_without_definition_not_extracted() -> None:
    """verifies: TOOL-PAR-030, DSN-ANA-020"""
    code = b"""
    // Declarations only
    int declared_only_1(int x);
    extern void declared_only_2(double y);

    // Definitions
    int defined_fn(int z) {
        return z + 42;
    }
    """
    ptu = parse("unit.c", args=["-std=c99"], unsaved_files=[("unit.c", code)])
    unit = extract_interfaces(ptu)

    assert len(unit.functions) == 1
    assert unit.functions[0].name == "defined_fn"


def test_functions_defined_in_headers_not_extracted() -> None:
    """verifies: TOOL-PAR-030, DSN-ANA-020"""
    # Header contains a static inline function definition
    hdr_code = b"""
    #ifndef HDR_H
    #define HDR_H
    static inline int header_inline_helper(int a) {
        return a + 10;
    }
    void header_decl(void);
    #endif
    """
    main_code = b"""
    #include "hdr.h"
    int main_fn(int x) {
        return header_inline_helper(x);
    }
    """
    cur = os.path.abspath(".")
    hdr_path = os.path.join(cur, "hdr.h")

    ptu = parse(
        "main.c",
        args=["-std=c99", f"-I{cur}"],
        unsaved_files=[(hdr_path, hdr_code), ("main.c", main_code)],
    )
    unit = extract_interfaces(ptu)

    # Only main_fn defined in main.c is extracted; header_inline_helper is excluded
    assert len(unit.functions) == 1
    assert unit.functions[0].name == "main_fn"
    assert unit.functions[0].location.file == "main.c"


def test_parameter_types_and_directions() -> None:
    """verifies: TOOL-PAR-030, TOOL-PAR-040, DSN-ANA-020"""
    code = b"""
    struct Point {
        int x;
        int y;
    };

    typedef int (*math_op_t)(int a, int b);

    void process(
        int scalar_val,
        struct Point struct_val,
        const int *ptr_const,
        int *ptr_mut,
        int arr_param[10],
        math_op_t callback,
        const char * const const_ptr_to_const
    ) {
    }
    """
    ptu = parse("params.c", args=["-std=c99"], unsaved_files=[("params.c", code)])
    unit = extract_interfaces(ptu)

    assert len(unit.functions) == 1
    fn = unit.functions[0]
    p_map = {p.name: p for p in fn.parameters}

    # By-value scalar -> "in"
    assert p_map["scalar_val"].direction == "in"
    assert p_map["scalar_val"].type == "ref:type.int"

    # By-value struct -> "in"
    assert p_map["struct_val"].direction == "in"
    assert p_map["struct_val"].type == "ref:type.struct.Point"

    # Pointer-to-const -> "in"
    assert p_map["ptr_const"].direction == "in"
    assert p_map["ptr_const"].type == "ref:type.ptr.const_int"

    # Non-const pointer -> "unknown"
    assert p_map["ptr_mut"].direction == "unknown"
    assert p_map["ptr_mut"].type == "ref:type.ptr.int"

    # Array parameter -> "unknown" (decays to pointer)
    assert p_map["arr_param"].direction == "unknown"
    assert p_map["arr_param"].type == "ref:type.array.10.int"

    # Function pointer -> "unknown"
    assert p_map["callback"].direction == "unknown"
    assert p_map["callback"].type == "ref:type.math_op_t"

    # Const pointer to const char -> "in"
    assert p_map["const_ptr_to_const"].direction == "in"
    assert p_map["const_ptr_to_const"].type == "ref:type.ptr.const_char"


def test_globals_access_modes() -> None:
    """verifies: TOOL-PAR-050, DSN-ANA-020"""
    code = b"""
    int g_read_only = 1;
    int g_write_only = 2;
    int g_read_write = 3;
    int g_addr_taken = 4;
    int g_arr[5];
    static int g_file_static = 5;
    struct Config { int enabled; } g_struct;

    void external_call(int *p);

    void evaluate_globals(void) {
        int temp = g_read_only;
        g_write_only = 100;
        g_read_write = g_read_write + 1;
        external_call(&g_addr_taken);
        external_call(g_arr);
        g_file_static = temp + 5;
        g_struct.enabled = 1;
    }
    """
    ptu = parse("globals.c", args=["-std=c99"], unsaved_files=[("globals.c", code)])
    unit = extract_interfaces(ptu)

    assert len(unit.functions) == 1
    fn = unit.functions[0]
    g_map = {g.name: g.access for g in fn.globals}

    # Verified accesses
    assert g_map["g_read_only"] == "r"
    assert g_map["g_write_only"] == "w"
    assert g_map["g_read_write"] == "rw"
    assert g_map["g_addr_taken"] == "rw"  # &g_addr_taken taken
    assert g_map["g_arr"] == "rw"         # array decay passed to call
    assert g_map["g_file_static"] == "w"  # file-static written
    assert g_map["g_struct"] == "w"       # struct field written

    # Verify globals are sorted alphabetically
    names = [g.name for g in fn.globals]
    assert names == sorted(names)


def test_globals_compound_assignment_and_increment() -> None:
    """verifies: TOOL-PAR-050, DSN-ANA-020"""
    code = b"""
    int g_compound = 10;
    int g_inc = 20;

    void mutate(void) {
        g_compound += 5;
        g_inc++;
    }
    """
    ptu = parse("mutate.c", args=["-std=c99"], unsaved_files=[("mutate.c", code)])
    unit = extract_interfaces(ptu)

    g_map = {g.name: g.access for g in unit.functions[0].globals}
    assert g_map["g_compound"] == "rw"
    assert g_map["g_inc"] == "rw"


def test_extraction_refused_on_failed_parse() -> None:
    """verifies: TOOL-PAR-030, DSN-ANA-020, DSN-ANA-090"""
    code_with_syntax_error = b"""
    int bad_function(void) {
        return syntax error here !!!
    }
    """
    ptu = parse("broken.c", args=["-std=c99"], unsaved_files=[("broken.c", code_with_syntax_error)])
    assert ptu.status == "failed"
    assert ptu.is_failed is True

    with pytest.raises(ExtractionRefusedError) as exc_info:
        extract_interfaces(ptu)

    assert "broken.c" in str(exc_info.value)
    assert exc_info.value.reason == "extraction_refused_failed_unit"


def test_to_dict_matches_sdd002_exact_shape() -> None:
    """verifies: TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-020"""
    code = b"""
    enum State { IDLE, RUNNING };
    int g_flag = 0;

    enum State process(int code) {
        g_flag = code;
        return IDLE;
    }
    """
    ptu = parse("sdd.c", args=["-std=c99"], unsaved_files=[("sdd.c", code)])
    unit = extract(ptu)

    data = unit.to_dict()
    assert data["path"] == "sdd.c"
    assert data["status"] == "parsed"
    assert isinstance(data["diagnostics"], list)
    assert len(data["functions"]) == 1

    fn_data = data["functions"][0]
    assert fn_data["name"] == "process"
    assert fn_data["linkage"] == "external"
    assert fn_data["storage_class"] == "none"
    assert fn_data["location"] == {"file": "sdd.c", "line": 5, "origin": "project"}
    assert fn_data["return_type"] == "ref:type.enum.State"
    assert fn_data["parameters"] == [
        {"name": "code", "type": "ref:type.int", "direction": "in"}
    ]
    assert fn_data["globals"] == [
        {"name": "g_flag", "access": "w"}
    ]

    # Verify out-of-scope fields are absent
    for forbidden in ("calls", "decisions", "complexity", "cfg", "annotations"):
        assert forbidden not in fn_data
        assert forbidden not in data
