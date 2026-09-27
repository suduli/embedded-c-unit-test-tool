# implements: DSN-ANA-020
"""Transitive type closure and deterministic type-graph builder for CMP-ANA.

Satisfies: TOOL-PAR-040, DSN-ANA-020.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import clang.cindex  # type: ignore[import-not-found,import-untyped]
from clang.cindex import CursorKind, TypeKind

from ectt.ana.frontend import normalize_path, resolve_source_location_path
from ectt.ana.model import (
    EnumeratorModel,
    ParameterModel,
    SourceLocation,
    StructMemberModel,
    TypeModel,
)
from ectt.core.determinism import stable_id

__all__ = [
    "TypeGraphBuilder",
]

# Mapping of primitive type kind names to normalized builtin type identifiers
_BUILTIN_KINDS: frozenset[TypeKind] = frozenset({
    TypeKind.VOID,
    TypeKind.BOOL,
    TypeKind.CHAR_U,
    TypeKind.UCHAR,
    TypeKind.CHAR16,
    TypeKind.CHAR32,
    TypeKind.USHORT,
    TypeKind.UINT,
    TypeKind.ULONG,
    TypeKind.ULONGLONG,
    TypeKind.UINT128,
    TypeKind.CHAR_S,
    TypeKind.SCHAR,
    TypeKind.WCHAR,
    TypeKind.SHORT,
    TypeKind.INT,
    TypeKind.LONG,
    TypeKind.LONGLONG,
    TypeKind.INT128,
    TypeKind.FLOAT,
    TypeKind.DOUBLE,
    TypeKind.LONGDOUBLE,
    TypeKind.FLOAT128,
    TypeKind.HALF,
    TypeKind.IBM128,
})


def _sanitize_ident(name: str) -> str:
    """Normalize a C type identifier for use in stable type IDs."""
    clean = re.sub(r"[^A-Za-z0-9_.]", "_", name.strip())
    clean = re.sub(r"_+", "_", clean)
    return clean.strip("_")


class TypeGraphBuilder:
    """Extracts transitive type closures with stable, machine-independent type IDs.

    Implements: TOOL-PAR-040, DSN-ANA-020.
    """

    def __init__(
        self,
        *,
        working_directory: str | Path | None = None,
        include_dirs: Sequence[str | Path] | None = None,
    ) -> None:
        self.working_directory = working_directory
        self.include_dirs = tuple(include_dirs) if include_dirs else ()
        self._types: dict[str, TypeModel] = {}
        self._resolving: set[str] = set()

    @property
    def types(self) -> dict[str, TypeModel]:
        """Return the dictionary of extracted types keyed by 'type.<id>'."""
        return self._types

    def resolve_type(
        self,
        type_obj: Any,
        *,
        context: str | None = None,
        cursor: Any = None,
    ) -> str:
        """Resolve a libclang Type or Cursor and return a 'ref:type.<id>' reference string.

        Recursively resolves all referenced sub-types (pointer targets, array element
        types, struct/union members, enum enumerators, function-pointer signatures,
        and typedef targets), ensuring transitive type closure.
        """
        if type_obj is None:
            return self._resolve_builtin("void", TypeKind.VOID)

        # 1. Pointers (including function pointers and pointers-to-const)
        if type_obj.kind == TypeKind.POINTER:
            return self._resolve_pointer(type_obj, context=context, cursor=cursor)

        # 2. Arrays
        if type_obj.kind in (
            TypeKind.CONSTANTARRAY,
            TypeKind.INCOMPLETEARRAY,
            TypeKind.VARIABLEARRAY,
            TypeKind.DEPENDENTSIZEDARRAY,
        ):
            return self._resolve_array(type_obj, context=context, cursor=cursor)

        # 3. Typedef, Struct, Union, Enum via declaration cursor
        decl = type_obj.get_declaration()
        if decl is not None and decl.kind != CursorKind.NO_DECL_FOUND:
            if decl.kind == CursorKind.TYPEDEF_DECL:
                return self._resolve_typedef(decl, context=context)
            elif decl.kind == CursorKind.STRUCT_DECL:
                return self._resolve_struct(decl, context=context)
            elif decl.kind == CursorKind.UNION_DECL:
                return self._resolve_union(decl, context=context)
            elif decl.kind == CursorKind.ENUM_DECL:
                return self._resolve_enum(decl, context=context)

        # 4. Function prototype directly (e.g. decayed function pointer or block)
        if type_obj.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO):
            return self._resolve_function_proto(type_obj, context=context, cursor=cursor)

        # 5. Builtin / Primitive types
        if type_obj.kind in _BUILTIN_KINDS:
            return self._resolve_builtin(type_obj.spelling, type_obj.kind)

        # 6. Elaborated / Unexposed types fallback
        canonical = type_obj.get_canonical()
        if canonical is not None and canonical != type_obj and canonical.kind != TypeKind.INVALID:
            canon_decl = canonical.get_declaration()
            if canon_decl is not None and canon_decl.kind != CursorKind.NO_DECL_FOUND:
                if canon_decl.kind == CursorKind.TYPEDEF_DECL:
                    return self._resolve_typedef(canon_decl, context=context)
                elif canon_decl.kind == CursorKind.STRUCT_DECL:
                    return self._resolve_struct(canon_decl, context=context)
                elif canon_decl.kind == CursorKind.UNION_DECL:
                    return self._resolve_union(canon_decl, context=context)
                elif canon_decl.kind == CursorKind.ENUM_DECL:
                    return self._resolve_enum(canon_decl, context=context)
            if canonical.kind in _BUILTIN_KINDS:
                return self._resolve_builtin(canonical.spelling, canonical.kind)

        # Final fallback to sanitized spelling
        raw_name = type_obj.spelling.replace("const ", "").replace(" const", "").strip()
        if not raw_name:
            raw_name = "void"
        return self._resolve_builtin(raw_name, type_obj.kind)

    def _resolve_builtin(self, spelling: str, kind: TypeKind) -> str:
        """Resolve a primitive/builtin C type."""
        clean = spelling.replace("const ", "").replace(" const", "").strip()
        if not clean:
            clean = "void"
        ident = _sanitize_ident(clean)
        key = f"type.{ident}"
        if key not in self._types:
            self._types[key] = TypeModel(kind="builtin", name=clean)
        return f"ref:{key}"

    def _resolve_pointer(self, ptr_type: Any, *, context: str | None, cursor: Any) -> str:
        """Resolve a pointer type (data pointer or function pointer)."""
        pointee = ptr_type.get_pointee()

        # Check for function pointer
        if pointee.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO):
            return self._resolve_function_proto(pointee, context=context, cursor=cursor)

        is_const = pointee.is_const_qualified()
        target_ref = self.resolve_type(pointee, context=context)
        target_id = target_ref.removeprefix("ref:type.")

        if is_const:
            ptr_id = f"ptr.const_{target_id}"
        else:
            ptr_id = f"ptr.{target_id}"

        key = f"type.{ptr_id}"
        if key not in self._types:
            self._types[key] = TypeModel(
                kind="pointer",
                target=target_ref,
                is_const=is_const,
            )
        return f"ref:{key}"

    def _resolve_array(self, arr_type: Any, *, context: str | None, cursor: Any) -> str:
        """Resolve an array type."""
        elem_type = arr_type.element_type
        elem_ref = self.resolve_type(elem_type, context=context)
        elem_id = elem_ref.removeprefix("ref:type.")

        if arr_type.kind == TypeKind.CONSTANTARRAY and arr_type.element_count >= 0:
            size: int | None = arr_type.element_count
            arr_id = f"array.{size}.{elem_id}"
        else:
            size = None
            arr_id = f"array.incomplete.{elem_id}"

        key = f"type.{arr_id}"
        if key not in self._types:
            self._types[key] = TypeModel(
                kind="array",
                element_type=elem_ref,
                size=size,
            )
        return f"ref:{key}"

    def _resolve_function_proto(self, proto_type: Any, *, context: str | None, cursor: Any) -> str:
        """Resolve an un-typedef'd function pointer signature."""
        ret_ref = self.resolve_type(proto_type.get_result(), context=f"{context}_ret" if context else None)
        param_models: list[ParameterModel] = []

        arg_types = list(proto_type.argument_types())
        param_names: list[str] = []
        if cursor is not None:
            for child in cursor.get_children():
                if child.kind == CursorKind.PARM_DECL:
                    param_names.append(child.spelling)

        for idx, arg_t in enumerate(arg_types):
            p_name = param_names[idx] if idx < len(param_names) else ""
            p_ref = self.resolve_type(
                arg_t,
                context=f"{context}_{p_name}" if context and p_name else (context or "fn"),
            )
            param_models.append(
                ParameterModel(
                    name=p_name,
                    type=p_ref,
                    direction="in" if self._is_certainly_in(arg_t) else "unknown",
                )
            )

        hash_parts = [ret_ref] + [f"{p.name}:{p.type}:{p.direction}" for p in param_models]
        fn_id = f"fn_ptr_{stable_id(*hash_parts)[:8]}"
        key = f"type.{fn_id}"

        if key not in self._types:
            self._types[key] = TypeModel(
                kind="function_pointer",
                return_type=ret_ref,
                parameters=tuple(param_models),
            )
        return f"ref:{key}"

    def _resolve_typedef(self, decl: Any, *, context: str | None) -> str:
        """Resolve a typedef declaration and its underlying type."""
        name = decl.spelling
        key = f"type.{name}"

        if key in self._resolving:
            return f"ref:{key}"
        if key in self._types:
            return f"ref:{key}"

        self._resolving.add(key)
        location = self._get_location(decl)

        underlying_type = decl.underlying_typedef_type
        und_ref = self.resolve_type(underlying_type, context=name, cursor=decl)

        self._types[key] = TypeModel(
            kind="typedef",
            name=name,
            location=location,
            underlying_type=und_ref,
        )
        self._resolving.discard(key)
        return f"ref:{key}"

    def _resolve_struct(self, decl: Any, *, context: str | None) -> str:
        """Resolve a struct declaration, its members, and recursive references."""
        is_anon = self._is_tag_anonymous(decl)

        if is_anon:
            type_id = self._build_anonymous_id("struct", context, decl)
            type_name = None
        else:
            type_name = decl.spelling
            type_id = f"struct.{type_name}"

        key = f"type.{type_id}"
        if key in self._resolving:
            return f"ref:{key}"
        if key in self._types:
            return f"ref:{key}"

        self._resolving.add(key)
        location = self._get_location(decl)

        defn = decl.get_definition() if hasattr(decl, "get_definition") else None
        target_decl = defn if defn is not None and defn.is_definition() else decl

        # Pre-populate to terminate recursive struct pointer cycles
        self._types[key] = TypeModel(
            kind="struct",
            name=type_name,
            location=location,
            members=(),
            is_anonymous=is_anon,
        )

        members: list[StructMemberModel] = []
        for child in target_decl.get_children():
            if child.kind == CursorKind.FIELD_DECL:
                field_name = child.spelling
                enclosing_name = type_name or context or "struct"
                field_context = f"{enclosing_name}.{field_name}" if field_name else enclosing_name
                field_ref = self.resolve_type(child.type, context=field_context, cursor=child)
                bit_width = child.get_bitfield_width() if child.is_bitfield() else None
                members.append(
                    StructMemberModel(
                        name=field_name,
                        type=field_ref,
                        bit_width=bit_width,
                    )
                )
            elif child.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL) and self._is_tag_anonymous(child):
                enclosing_name = type_name or context or "struct"
                nested_ref = self.resolve_type(child.type, context=enclosing_name, cursor=child)
                members.append(
                    StructMemberModel(
                        name="",
                        type=nested_ref,
                    )
                )

        self._types[key] = TypeModel(
            kind="struct",
            name=type_name,
            location=location,
            members=tuple(members),
            is_anonymous=is_anon,
        )

        self._resolving.discard(key)
        return f"ref:{key}"

    def _resolve_union(self, decl: Any, *, context: str | None) -> str:
        """Resolve a union declaration and its members."""
        is_anon = self._is_tag_anonymous(decl)

        if is_anon:
            type_id = self._build_anonymous_id("union", context, decl)
            type_name = None
        else:
            type_name = decl.spelling
            type_id = f"union.{type_name}"

        key = f"type.{type_id}"
        if key in self._resolving:
            return f"ref:{key}"
        if key in self._types:
            return f"ref:{key}"

        self._resolving.add(key)
        location = self._get_location(decl)

        defn = decl.get_definition() if hasattr(decl, "get_definition") else None
        target_decl = defn if defn is not None and defn.is_definition() else decl

        self._types[key] = TypeModel(
            kind="union",
            name=type_name,
            location=location,
            members=(),
            is_anonymous=is_anon,
        )

        members: list[StructMemberModel] = []
        for child in target_decl.get_children():
            if child.kind == CursorKind.FIELD_DECL:
                field_name = child.spelling
                enclosing_name = type_name or context or "union"
                field_context = f"{enclosing_name}.{field_name}" if field_name else enclosing_name
                field_ref = self.resolve_type(child.type, context=field_context, cursor=child)
                members.append(
                    StructMemberModel(
                        name=field_name,
                        type=field_ref,
                    )
                )
            elif child.kind in (CursorKind.STRUCT_DECL, CursorKind.UNION_DECL) and self._is_tag_anonymous(child):
                enclosing_name = type_name or context or "union"
                nested_ref = self.resolve_type(child.type, context=enclosing_name, cursor=child)
                members.append(
                    StructMemberModel(
                        name="",
                        type=nested_ref,
                    )
                )

        self._types[key] = TypeModel(
            kind="union",
            name=type_name,
            location=location,
            members=tuple(members),
            is_anonymous=is_anon,
        )

        self._resolving.discard(key)
        return f"ref:{key}"

    def _resolve_enum(self, decl: Any, *, context: str | None) -> str:
        """Resolve an enum declaration and its enumerator constants."""
        is_anon = self._is_tag_anonymous(decl)

        if is_anon:
            type_id = self._build_anonymous_id("enum", context, decl)
            type_name = None
        else:
            type_name = decl.spelling
            type_id = f"enum.{type_name}"

        key = f"type.{type_id}"
        if key in self._resolving:
            return f"ref:{key}"
        if key in self._types:
            return f"ref:{key}"

        self._resolving.add(key)
        location = self._get_location(decl)

        defn = decl.get_definition() if hasattr(decl, "get_definition") else None
        target_decl = defn if defn is not None and defn.is_definition() else decl

        enumerators: list[EnumeratorModel] = []
        for child in target_decl.get_children():
            if child.kind == CursorKind.ENUM_CONSTANT_DECL:
                enumerators.append(
                    EnumeratorModel(
                        name=child.spelling,
                        value=child.enum_value,
                    )
                )

        underlying_ref: str | None = None
        if hasattr(target_decl, "enum_type") and target_decl.enum_type.kind != TypeKind.INVALID:
            underlying_ref = self.resolve_type(target_decl.enum_type, context=type_name)
        else:
            underlying_ref = "ref:type.int"

        self._types[key] = TypeModel(
            kind="enum",
            name=type_name,
            location=location,
            enumerators=tuple(enumerators),
            underlying_type=underlying_ref,
            is_anonymous=is_anon,
        )

        self._resolving.discard(key)
        return f"ref:{key}"

    def _is_tag_anonymous(self, cursor: Any) -> bool:
        """Check whether a struct, union, or enum has no declared tag name."""
        if hasattr(cursor, "is_anonymous") and cursor.is_anonymous():
            return True
        spelling = cursor.spelling or ""
        if not spelling or spelling.startswith(("(", "<")):
            return True
        tokens = list(cursor.get_tokens())
        if tokens:
            first_tok = tokens[0].spelling
            if first_tok in ("struct", "union", "enum") and len(tokens) > 1:
                if tokens[1].spelling == "{":
                    return True
        return False

    def _build_anonymous_id(self, kind_name: str, context: str | None, cursor: Any) -> str:
        """Derive a deterministic, machine-independent identifier for an anonymous type."""
        loc_file = ""
        line = 0
        column = 0

        if cursor.location and cursor.location.file:
            loc_file = normalize_path(
                cursor.location.file.name,
                self.working_directory,
                include_dirs=self.include_dirs,
            )
            line = cursor.location.line
            column = cursor.location.column

        ctx = _sanitize_ident(context) if context else "anon"
        loc_hash = stable_id(loc_file, str(line), str(column), kind_name, ctx)[:8]
        return f"anon.{kind_name}.{ctx}_{loc_hash}"

    def _get_location(self, cursor: Any) -> SourceLocation | None:
        """Extract machine-independent source location with origin marker."""
        if cursor.location and cursor.location.file:
            norm_path, origin = resolve_source_location_path(
                cursor.location.file.name,
                self.working_directory,
                include_dirs=self.include_dirs,
            )
            return SourceLocation(file=norm_path, line=cursor.location.line, origin=origin)
        return None

    def _is_certainly_in(self, type_obj: Any) -> bool:
        """Determine if a type passed as parameter is certainly an 'in' parameter."""
        canonical = type_obj.get_canonical() if hasattr(type_obj, "get_canonical") else type_obj
        if canonical is None or canonical.kind == TypeKind.INVALID:
            canonical = type_obj

        if canonical.kind == TypeKind.POINTER:
            pointee = canonical.get_pointee()
            if pointee.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO):
                return False
            return bool(pointee.is_const_qualified())
        if canonical.kind in (
            TypeKind.CONSTANTARRAY,
            TypeKind.INCOMPLETEARRAY,
            TypeKind.VARIABLEARRAY,
            TypeKind.DEPENDENTSIZEDARRAY,
        ):
            return False
        if canonical.kind in (TypeKind.FUNCTIONPROTO, TypeKind.FUNCTIONNOPROTO):
            return False
        return True
