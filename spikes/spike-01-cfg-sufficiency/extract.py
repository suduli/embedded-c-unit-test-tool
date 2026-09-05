"""
extract.py — the CFG-sufficiency spike's extraction engine.

Uses libclang's AST/cursor API only (no CFG) to pull functions, types,
globals, and a direct/indirect call graph out of a translation unit. See
docs/superpowers/plans/2026-09-05-spike-01-cfg-sufficiency.md for the plan
this implements (WP-SPIKE-01, PLAN-001 SS4.4).
"""
import os
from dataclasses import dataclass, field

from clang.cindex import CursorKind

# DEVIATION FROM THE PLAN (documented in RESULTS.md): the `libclang` PyPI
# wheel ships only libclang.dll, not clang's resource-dir freestanding
# headers (stdint.h, stddef.h, ...). CMSIS's core_cm4.h needs <stdint.h>
# unconditionally, so without this the very first #include chain fails
# with a fatal error on every file. freestanding_stubs/ supplies minimal
# clang-builtin-backed replacements (see comments in those files) — this
# is a packaging gap in the wheel, not a CFG- or AST-related limitation.
_FREESTANDING_STUBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "freestanding_stubs")


def parse_args_for(file_path: str, fixture_root: str) -> list[str]:
    """
    Build clang args to parse one STM32F4 HAL/CMSIS source file.
    Uses clang's own ARM target so vendor keywords like __weak, __packed
    and ARM-specific attribute extensions resolve without GCC-compat hacks
    — this is the same technique the real CMP-ANA would use per SDD-005 SS5.3.
    """
    cmsis_core = os.path.join(fixture_root, "Drivers", "CMSIS", "Include")
    cmsis_device = os.path.join(
        fixture_root, "Drivers", "CMSIS", "Device", "ST", "STM32F4xx", "Include"
    )
    hal_inc = os.path.join(fixture_root, "Drivers", "STM32F4xx_HAL_Driver", "Inc")
    return [
        "-target", "thumbv7em-none-eabi",
        "-mcpu=cortex-m4",
        "-DSTM32F407xx",
        "-DUSE_HAL_DRIVER",
        f"-I{cmsis_core}",
        f"-I{cmsis_device}",
        f"-I{hal_inc}",
        f"-isystem{_FREESTANDING_STUBS}",
        "-std=c11",
        "-ferror-limit=0",
    ]


@dataclass
class FunctionInfo:
    name: str
    return_type: str
    params: list[tuple[str, str]]
    is_static: bool
    file: str
    line: int


@dataclass
class TypeInfo:
    name: str
    kind: str
    fields: list[tuple[str, str]]
    nesting_depth: int
    file: str


@dataclass
class GlobalInfo:
    name: str
    type: str
    is_static: bool
    file: str
    line: int


@dataclass
class IndirectCallInfo:
    caller: str
    expr_text: str
    declared_fn_ptr_type: str
    file: str
    line: int


@dataclass
class ExtractionResult:
    functions: list[FunctionInfo] = field(default_factory=list)
    types: list[TypeInfo] = field(default_factory=list)
    globals: list[GlobalInfo] = field(default_factory=list)
    direct_calls: list[tuple[str, str]] = field(default_factory=list)
    indirect_calls: list[IndirectCallInfo] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def _loc(cursor):
    f = cursor.location.file
    return (str(f) if f else "<unknown>", cursor.location.line)


def _record_fields(cursor, depth=0):
    fields = []
    max_depth = depth
    for child in cursor.get_children():
        if child.kind == CursorKind.FIELD_DECL:
            fields.append((child.type.spelling, child.spelling))
            if child.type.get_declaration().kind in (
                CursorKind.STRUCT_DECL, CursorKind.UNION_DECL
            ):
                _, inner_depth = _record_fields(child.type.get_declaration(), depth + 1)
                max_depth = max(max_depth, inner_depth)
    return fields, max_depth


def _walk_calls(cursor, caller_name, result: ExtractionResult):
    for child in cursor.walk_preorder():
        if child.kind == CursorKind.CALL_EXPR:
            callee = child.referenced
            if callee is not None and callee.kind == CursorKind.FUNCTION_DECL:
                result.direct_calls.append((caller_name, callee.spelling))
            else:
                target_expr = next(child.get_children(), None)
                file_, line_ = _loc(child)
                result.indirect_calls.append(IndirectCallInfo(
                    caller=caller_name,
                    expr_text=child.spelling or (target_expr.spelling if target_expr else "<unknown>"),
                    declared_fn_ptr_type=(target_expr.type.spelling if target_expr else "<unknown>"),
                    file=file_, line=line_,
                ))


def extract_translation_unit(tu) -> ExtractionResult:
    """
    Extracts everything visible in this one translation unit's top-level
    cursor list — both declared directly in the compiled file and pulled
    in transitively via #include. That second part is intentional here:
    vendor headers (CMSIS/HAL) are where almost all real types (e.g.
    ADC_HandleTypeDef, GPIO_TypeDef) and many `static inline` functions
    live, and PAR-030 needs those extracted, not just .c-file-local
    content.

    NOTE for callers running this over MANY files of the same project
    (see run_spike.py): a header included by N translation units produces
    N structurally-identical cursors for each of its declarations — one
    per TU. This function does not deduplicate across calls (it only sees
    one TU at a time); run_spike.py deduplicates project-wide by
    (file, line, name) identity when aggregating multiple calls' results,
    which is the correct point to do it — this is standard clang-tooling
    practice (per-TU indexing + a project-wide merge pass), not something
    a single-TU function can know about on its own.
    """
    result = ExtractionResult()
    for d in tu.diagnostics:
        if d.severity >= d.Error:
            result.diagnostics.append(str(d))

    for cursor in tu.cursor.get_children():
        file_, line_ = _loc(cursor)

        if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
            params = [(a.type.spelling, a.spelling) for a in cursor.get_arguments()]
            result.functions.append(FunctionInfo(
                name=cursor.spelling,
                return_type=cursor.result_type.spelling,
                params=params,
                is_static=cursor.storage_class.name == "STATIC",
                file=file_, line=line_,
            ))
            _walk_calls(cursor, cursor.spelling, result)

        elif cursor.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL, CursorKind.ENUM_DECL):
            fields, depth = _record_fields(cursor)
            result.types.append(TypeInfo(
                name=cursor.spelling or "<anonymous>",
                kind=cursor.kind.name.replace("_DECL", "").lower(),
                fields=fields, nesting_depth=depth, file=file_,
            ))

        elif cursor.kind == CursorKind.TYPEDEF_DECL:
            underlying = cursor.underlying_typedef_type.get_declaration()
            fields, depth = _record_fields(underlying) if underlying.kind in (
                CursorKind.STRUCT_DECL, CursorKind.UNION_DECL
            ) else ([], 0)
            result.types.append(TypeInfo(
                name=cursor.spelling,
                kind="typedef",
                fields=fields, nesting_depth=depth, file=file_,
            ))

        elif cursor.kind == CursorKind.VAR_DECL:
            result.globals.append(GlobalInfo(
                name=cursor.spelling,
                type=cursor.type.spelling,
                is_static=cursor.storage_class.name == "STATIC",
                file=file_, line=line_,
            ))

    return result
