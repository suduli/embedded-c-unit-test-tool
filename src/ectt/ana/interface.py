# implements: DSN-ANA-020
"""Function interface and global variable extraction for CMP-ANA.

Satisfies: TOOL-PAR-030, TOOL-PAR-050, DSN-ANA-020.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import clang.cindex  # type: ignore[import-not-found,import-untyped]
from clang.cindex import CursorKind, LinkageKind, StorageClass, TypeKind

from ectt.ana.errors import ExtractionRefusedError
from ectt.ana.frontend import normalize_path, resolve_source_location_path
from ectt.ana.model import (
    AnalysisUnit,
    FunctionModel,
    GlobalAccessModel,
    ParameterModel,
    ParsedTranslationUnit,
    SourceLocation,
)
from ectt.ana.types import TypeGraphBuilder

__all__ = [
    "extract_interfaces",
    "extract",
]


def _is_in_main_file(
    cursor_loc: Any,
    main_source_path: str,
    working_dir: str | Path | None = None,
) -> bool:
    """Determine whether a cursor's source location resides in the main translation unit file."""
    if cursor_loc is None or cursor_loc.file is None:
        return False
    loc_file = cursor_loc.file.name
    if not loc_file:
        return False

    norm_loc = normalize_path(loc_file, working_dir)
    norm_main = normalize_path(main_source_path, working_dir)
    if norm_loc == norm_main:
        return True

    # Check filename match or filesystem resolution
    try:
        p1 = Path(loc_file)
        p2 = Path(main_source_path)
        if not p1.is_absolute() and working_dir:
            p1 = Path(working_dir) / p1
        if not p2.is_absolute() and working_dir:
            p2 = Path(working_dir) / p2
        return p1.resolve() == p2.resolve()
    except (OSError, ValueError, RuntimeError):
        return False


def _is_global_or_file_static(cursor: Any) -> bool:
    """Check if a VAR_DECL represents a global or file-static variable."""
    if cursor.kind != CursorKind.VAR_DECL:
        return False
    sem_parent = cursor.semantic_parent
    if sem_parent is not None and sem_parent.kind == CursorKind.TRANSLATION_UNIT:
        return True
    if cursor.linkage in (LinkageKind.EXTERNAL, LinkageKind.INTERNAL, LinkageKind.UNIQUE_EXTERNAL):
        if sem_parent is None or sem_parent.kind == CursorKind.TRANSLATION_UNIT:
            return True
    return False


def _determine_global_access(cursor: Any, ancestors: tuple[Any, ...], target_var: Any) -> str:
    """Determine the access mode ('r', 'w', 'rw') for a reference to a global variable."""
    # Check if target is an array decaying to a pointer in a function call
    if target_var.type.kind in (
        TypeKind.CONSTANTARRAY,
        TypeKind.INCOMPLETEARRAY,
        TypeKind.VARIABLEARRAY,
        TypeKind.DEPENDENTSIZEDARRAY,
    ):
        for a in reversed(ancestors):
            if a.kind == CursorKind.CALL_EXPR:
                return "rw"
            if a.kind in (CursorKind.COMPOUND_STMT, CursorKind.DECL_STMT):
                break

    # Ascend through transparent wrappers (casts, parens, struct field dot-access, array subscript)
    idx = len(ancestors) - 1
    curr = cursor
    while idx >= 0:
        parent = ancestors[idx]
        if parent.kind in (CursorKind.UNEXPOSED_EXPR, CursorKind.PAREN_EXPR):
            curr = parent
            idx -= 1
            continue
        if parent.kind == CursorKind.MEMBER_REF_EXPR:
            tokens = [t.spelling for t in parent.get_tokens()]
            if "." in tokens:
                curr = parent
                idx -= 1
                continue
        if parent.kind == CursorKind.ARRAY_SUBSCRIPT_EXPR:
            children = list(parent.get_children())
            if children and children[0] == curr:
                curr = parent
                idx -= 1
                continue
        break

    if idx >= 0:
        op_parent = ancestors[idx]
        children = list(op_parent.get_children())

        # Unary operators: &g (address taken -> rw), ++g / g++ / --g / g-- (rw)
        if op_parent.kind == CursorKind.UNARY_OPERATOR:
            toks = [t.spelling for t in op_parent.get_tokens()]
            if "&" in toks or "++" in toks or "--" in toks:
                return "rw"
            return "r"

        # Compound assignment: g += ... (LHS is rw, RHS is r)
        elif op_parent.kind == CursorKind.COMPOUND_ASSIGNMENT_OPERATOR:
            if children and children[0] == curr:
                return "rw"
            return "r"

        # Binary operator: g = ... (LHS is w, RHS is r)
        elif op_parent.kind == CursorKind.BINARY_OPERATOR:
            if len(children) >= 2:
                lhs = children[0]
                lhs_tokens = [t.spelling for t in lhs.get_tokens()]
                all_tokens = [t.spelling for t in op_parent.get_tokens()]
                if len(all_tokens) > len(lhs_tokens):
                    op = all_tokens[len(lhs_tokens)]
                    if op == "=":
                        if lhs == curr:
                            return "w"
            return "r"

    return "r"


def _extract_globals(func_cursor: Any) -> tuple[GlobalAccessModel, ...]:
    """Identify all global and file-static variables read or written by a function."""
    accesses: dict[str, str] = {}

    def walk(cursor: Any, ancestors: tuple[Any, ...] = ()) -> None:
        if cursor.kind == CursorKind.DECL_REF_EXPR and cursor.referenced:
            target = cursor.referenced
            if _is_global_or_file_static(target):
                name = target.spelling
                if name:
                    acc = _determine_global_access(cursor, ancestors, target)
                    cur = accesses.get(name)
                    if cur is None:
                        accesses[name] = acc
                    elif cur == "rw" or acc == "rw" or cur != acc:
                        accesses[name] = "rw"

        for child in cursor.get_children():
            walk(child, ancestors + (cursor,))

    walk(func_cursor)

    # Deterministic sorting by variable name
    return tuple(
        GlobalAccessModel(name=name, access=accesses[name])
        for name in sorted(accesses.keys())
    )


def extract_interfaces(
    parsed_tu: ParsedTranslationUnit,
    *,
    working_directory: str | Path | None = None,
    include_dirs: Sequence[str | Path] | None = None,
) -> AnalysisUnit:
    """Extract function signatures, transitive type closure, and global accesses.

    Refuses extraction with ExtractionRefusedError if parse status is 'failed'.
    Restricts extracted functions to definitions in the translation unit's main file.
    Transitively extracts all reachable user-defined types.

    Implements: TOOL-PAR-030, TOOL-PAR-040, TOOL-PAR-050, DSN-ANA-020.
    """
    if parsed_tu.is_failed or parsed_tu.status == "failed":
        raise ExtractionRefusedError(
            f"Cannot extract interface and types from failed translation unit '{parsed_tu.source_path}'",
            path=parsed_tu.source_path,
        )

    if parsed_tu.translation_unit is None:
        raise ExtractionRefusedError(
            f"Parsed translation unit has no libclang AST handle: '{parsed_tu.source_path}'",
            path=parsed_tu.source_path,
        )

    tu_handle = parsed_tu.translation_unit
    norm_source_path = parsed_tu.source_path

    if include_dirs is None:
        include_dirs = getattr(parsed_tu, "include_dirs", ())

    type_builder = TypeGraphBuilder(
        working_directory=working_directory,
        include_dirs=include_dirs,
    )

    functions: list[FunctionModel] = []

    for child in tu_handle.cursor.get_children():
        # Unit boundary: only functions defined in the main file of the TU
        if child.kind == CursorKind.FUNCTION_DECL and child.is_definition():
            if not _is_in_main_file(child.location, norm_source_path, working_directory):
                continue

            name = child.spelling
            linkage = "internal" if child.linkage == LinkageKind.INTERNAL else "external"
            storage_class = "static" if child.storage_class == StorageClass.STATIC else "none"

            if child.location and child.location.file:
                loc_file, origin = resolve_source_location_path(
                    child.location.file.name,
                    working_directory,
                    include_dirs=include_dirs,
                )
            else:
                loc_file, origin = norm_source_path, "project"
            location = SourceLocation(file=loc_file, line=child.location.line, origin=origin)

            # Return type
            return_type_ref = type_builder.resolve_type(
                child.result_type,
                context=f"{name}_return",
                cursor=child,
            )

            # Parameters
            parameters: list[ParameterModel] = []
            for p in child.get_arguments():
                p_name = p.spelling
                p_type_ref = type_builder.resolve_type(
                    p.type,
                    context=f"{name}_{p_name}" if p_name else name,
                    cursor=p,
                )
                direction = "in" if type_builder._is_certainly_in(p.type) else "unknown"
                parameters.append(
                    ParameterModel(
                        name=p_name,
                        type=p_type_ref,
                        direction=direction,
                    )
                )

            # Globals and file-static variable accesses
            globals_accessed = _extract_globals(child)

            functions.append(
                FunctionModel(
                    name=name,
                    linkage=linkage,
                    storage_class=storage_class,
                    location=location,
                    return_type=return_type_ref,
                    parameters=tuple(parameters),
                    globals=globals_accessed,
                )
            )

    return AnalysisUnit(
        path=norm_source_path,
        status=parsed_tu.status,
        diagnostics=parsed_tu.diagnostics,
        functions=tuple(functions),
        types=dict(type_builder.types),
    )


# Alias matching ectt design conventions
extract = extract_interfaces
