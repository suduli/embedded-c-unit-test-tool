# implements: TOOL-TCD-040, TOOL-TCD-050
"""Nested struct, array and union expectations in test case files (FIX-TCMNEST, DSN-TCM-030).

A ``.tests`` expectation (``globals`` or ``out_parameters``) maps names to *strings*.
Nested values are authored in that same flat form, with a **path** as the key::

    expected:
      globals:
        g_frame.header.len: "4"        # struct member
        g_frame.payload[0]: "0x10"     # array element
        g_frame.payload[1]: "0x20"
        g_reading.as_int: "7"          # union: the member named is the active member

A key with no ``.`` and no ``[`` is a plain name, exactly as before, so existing flat
files remain valid and, because the file model is unchanged, byte-stable (the content
digest and the dumped text do not move).

The path syntax covers three kinds of authored value:

* **expected.globals / expected.out_parameters** — as above, complete values,
  compared by :func:`compare_expected`;
* **inputs.globals** (initial nested values) — validated by
  :func:`resolve_input_values` with the same structural rules, but completeness
  is not required (C zero-initializes what an initializer omits);
* **a composite return value** — ``expected.return`` is a mapping of path keys
  *relative to the return value* (``header.len: "4"``), compared by
  :func:`compare_return`; the flat scalar return (a plain string) is unchanged.

``compare_expected`` turns the paths of one name into the nested value the comparison
engine (``ectt.tcm.compare``) takes, **validated against the declared type**:

* an unknown struct or union member is refused, naming its path;
* an array needs every index ``0 .. length-1`` exactly once (no gaps, nothing beyond);
* every declared struct member must be given (the engine compares declared members);
* a union is given exactly one member, and that member is the active one;
* a scalar where a composite is declared (or the reverse), and a path that is both a
  value and a parent, are refused.

A mismatch is reported by the engine with the full path (``g_frame.payload[1]``).

``ctype_from_model`` builds the engine's declared type from the analysis type graph.
Pointers are refused there: how a pointer compares (null, address, pointee) is an
authored per-field choice, not something the graph can supply.

``flatten_expected`` is the inverse for tools that hold a nested value and need the
flat authored form.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ectt.ana.model import TypeModel
from ectt.tcm.compare import (
    ArrayType,
    ComparisonResult,
    CType,
    EnumType,
    Member,
    PointerType,
    ScalarType,
    StructType,
    Tolerance,
    UnionType,
    compare,
)
from ectt.tcm.errors import InvalidComparisonSpecError, ValueParseError

__all__ = [
    "ExpectedPath",
    "compare_expected",
    "compare_return",
    "ctype_from_model",
    "expected_trees",
    "flatten_expected",
    "is_nested_key",
    "parse_expected_path",
    "resolve_input_values",
    "validate_expected_keys",
]

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_INDEX = re.compile(r"\[(0|[1-9][0-9]*)\]")
_SIMPLE_BUILTINS = frozenset(
    {
        "_Bool", "char", "signed char", "unsigned char", "short", "unsigned short", "int", "unsigned int",
        "long", "unsigned long", "long long", "unsigned long long", "float", "double", "long double",
    }
)

Node = str | dict[str | int, Any]


def is_nested_key(key: str) -> bool:
    """True when ``key`` uses the path syntax (it contains ``.`` or ``[``)."""
    return "." in key or "[" in key


@dataclass(frozen=True)
class ExpectedPath:
    """A parsed expectation key: the root name and the steps below it."""

    root: str
    steps: tuple[str | int, ...]  # member names (str) and array indices (int)


def parse_expected_path(key: str) -> ExpectedPath:
    """Parse ``name``, ``name.member`` or ``name[3].member[0]``; a plain key is just a root."""
    if not is_nested_key(key):
        if not key:
            raise ValueParseError("an expectation name must not be empty", reason="invalid_value_path")
        return ExpectedPath(key, ())
    match = _IDENTIFIER.match(key)
    if match is None:
        raise ValueParseError(f"expectation path '{key}' must start with an identifier", reason="invalid_value_path")
    root, position = match.group(0), match.end()
    steps: list[str | int] = []
    while position < len(key):
        if key[position] == ".":
            member = _IDENTIFIER.match(key, position + 1)
            if member is None:
                raise ValueParseError(f"expectation path '{key}' has an empty or invalid member after '.'", reason="invalid_value_path")
            steps.append(member.group(0))
            position = member.end()
        elif key[position] == "[":
            index = _INDEX.match(key, position)
            if index is None:
                raise ValueParseError(f"expectation path '{key}' has an invalid array index (digits only, no leading zeros)", reason="invalid_value_path")
            steps.append(int(index.group(1)))
            position = index.end()
        else:
            raise ValueParseError(f"expectation path '{key}' has an unexpected character '{key[position]}'", reason="invalid_value_path")
    return ExpectedPath(root, tuple(steps))


def validate_expected_keys(entries: Mapping[str, str]) -> None:
    """Refuse malformed path keys; plain keys (no ``.``/``[``) are accepted as before."""
    for key in entries:
        parse_expected_path(key)


def expected_trees(entries: Mapping[str, str]) -> dict[str, Node]:
    """Group authored entries by root into nested nodes (string leaves, dict branches).

    Array steps become integer keys. A path that is both a value and a parent, or
    that mixes member and index steps under one node, is refused.
    """
    trees: dict[str, Node] = {}
    for key in sorted(entries):
        value = entries[key]
        path = parse_expected_path(key)
        if not path.steps:
            if path.root in trees:
                raise ValueParseError(f"'{path.root}' is given both as a value and with member or element paths", reason="conflicting_path")
            trees[path.root] = value
            continue
        node = trees.setdefault(path.root, {})
        if isinstance(node, str):
            raise ValueParseError(f"'{path.root}' is given both as a value and with member or element paths", reason="conflicting_path")
        walked = path.root
        for position, step in enumerate(path.steps):
            last = position == len(path.steps) - 1
            if any(isinstance(k, int) != isinstance(step, int) for k in node):
                raise ValueParseError(f"'{walked}' mixes member and element paths", reason="mixed_path")
            walked += f"[{step}]" if isinstance(step, int) else f".{step}"
            if last:
                if step in node:
                    raise ValueParseError(f"'{walked}' is given both as a value and with member or element paths", reason="conflicting_path")
                node[step] = value
            else:
                child = node.setdefault(step, {})
                if isinstance(child, str):
                    raise ValueParseError(f"'{walked}' is given both as a value and with member or element paths", reason="conflicting_path")
                node = child
    return trees


def _validate(node: Node, declared: CType, path: str) -> None:
    """Structural checks, run first so a typo is reported before anything about completeness.

    Refuses unknown members, indices outside an array, member paths under an array (and
    element paths under a struct or union), a union given more than one member, and a
    single value where a composite is declared (or the reverse).
    """
    if isinstance(declared, PointerType) and declared.policy == "pointee":
        assert declared.pointee is not None
        _validate(node, declared.pointee, path)
        return
    if isinstance(declared, ScalarType | EnumType | PointerType):
        if not isinstance(node, str):
            raise ValueParseError(f"'{path}' is a scalar but member or element paths were given", reason="composite_for_scalar")
        return
    if isinstance(node, str):
        raise ValueParseError(f"'{path}' is a struct, array or union and needs member or element paths, not a single value", reason="scalar_for_composite")
    if isinstance(declared, ArrayType):
        for key in sorted(node, key=str):
            if not isinstance(key, int):
                raise ValueParseError(f"'{path}.{key}': '{path}' is an array; member paths are not allowed", reason="member_in_array")
            if key >= declared.length:
                raise ValueParseError(f"'{path}[{key}]' is outside the array (length {declared.length})", reason="index_out_of_range")
            _validate(node[key], declared.element, f"{path}[{key}]")
        return
    members = {m.name: m.type for m in declared.members}
    for key in sorted(node, key=str):
        if not isinstance(key, str):
            raise ValueParseError(f"'{path}[{key}]': '{path}' is a struct or union; element paths are not allowed", reason="index_in_struct")
        if key not in members:
            raise ValueParseError(
                f"'{path}.{key}' names '{key}', which is not a declared member (declared: {', '.join(sorted(members))})",
                reason="unknown_member",
            )
        _validate(node[key], members[key], f"{path}.{key}")
    if isinstance(declared, UnionType) and len(node) != 1:
        raise ValueParseError(f"union '{path}' needs exactly one member (the active one); got {len(node)}", reason="ambiguous_union")


def _resolve(node: Node, declared: CType, path: str, active: dict[str, str]) -> Any:
    """Build the engine's nested value from a validated node; requires completeness."""
    if isinstance(declared, PointerType):
        return _resolve(node, declared.pointee, path, active) if declared.policy == "pointee" and declared.pointee is not None else node
    if isinstance(declared, ScalarType | EnumType):
        return node
    assert isinstance(node, dict)
    if isinstance(declared, ArrayType):
        missing = [i for i in range(declared.length) if i not in node]
        if missing:
            raise ValueParseError(f"'{path}[{missing[0]}]' is missing: every element 0..{declared.length - 1} must be given", reason="missing_element")
        return [_resolve(node[i], declared.element, f"{path}[{i}]", active) for i in range(declared.length)]
    if isinstance(declared, UnionType):
        (name,) = node
        active[path] = str(name)
        member_type = next(m.type for m in declared.members if m.name == name)
        return {name: _resolve(node[name], member_type, f"{path}.{name}", active)}
    missing_members = [m.name for m in declared.members if m.name not in node]
    if missing_members:
        raise ValueParseError(f"'{path}.{missing_members[0]}' is missing: every declared member must be given", reason="missing_member")
    return {m.name: _resolve(node[m.name], m.type, f"{path}.{m.name}", active) for m in declared.members}


def compare_expected(
    entries: Mapping[str, str],
    declared: Mapping[str, CType],
    actual: Mapping[str, Any],
    *,
    tolerances: Mapping[str, Tolerance] | None = None,
) -> dict[str, ComparisonResult]:
    """Compare every authored expectation with the observed values, one result per root name.

    ``declared`` gives each root's C type, ``actual`` its observed nested value (text
    leaves, lists for arrays, mappings for structs and unions). Mismatches carry the
    full path. Authoring errors raise instead of becoming a mismatch.
    """
    results: dict[str, ComparisonResult] = {}
    for root, node in sorted(expected_trees(entries).items()):
        if root not in declared:
            raise ValueParseError(f"expectation names '{root}', which has no declared type", reason="unknown_variable")
        if root not in actual:
            raise ValueParseError(f"no observed value was supplied for '{root}'", reason="missing_actual")
        _validate(node, declared[root], root)
        active: dict[str, str] = {}
        expected = _resolve(node, declared[root], root, active)
        results[root] = compare(declared[root], expected, actual[root], path=root, tolerances=tolerances, active_members=active)
    return results


def _relative_tree(entries: Mapping[str, str]) -> Node:
    """One nested node from keys relative to an unnamed value (the return).

    ``header.len`` means member ``header`` then member ``len``; a plain key is
    the first member. The value/parent and member/index conflicts of
    :func:`expected_trees` apply unchanged, reported with the authored key.
    """
    node: dict[str | int, Any] = {}
    for key in sorted(entries):
        path = parse_expected_path(key)
        steps: list[str | int] = [path.root, *path.steps]
        cursor: dict[str | int, Any] = node
        walked = ""
        for position, step in enumerate(steps):
            last = position == len(steps) - 1
            walked = str(step) if position == 0 else (f"{walked}[{step}]" if isinstance(step, int) else f"{walked}.{step}")
            if any(isinstance(k, int) != isinstance(step, int) for k in cursor):
                raise ValueParseError(f"'{key}': '{walked}' mixes member and element paths", reason="mixed_path")
            if last:
                if step in cursor:
                    raise ValueParseError(f"'{key}': '{walked}' is given more than once", reason="conflicting_path")
                cursor[step] = entries[key]
            else:
                child = cursor.setdefault(step, {})
                if not isinstance(child, dict):
                    raise ValueParseError(
                        f"'{key}': '{walked}' is given both as a value and with member or element paths",
                        reason="conflicting_path",
                    )
                cursor = child
    if not node:
        raise ValueParseError("a return expectation needs at least one path key", reason="empty_value")
    return node


def compare_return(
    entries: Mapping[str, str],
    declared: CType,
    actual: Any,
    *,
    tolerances: Mapping[str, Tolerance] | None = None,
) -> ComparisonResult:
    """Compare a composite return expectation with the observed return value.

    Path keys are relative to the return value itself (``header.len: "4"``);
    the flat scalar return (a plain string, no paths) is authored as before and
    never enters here. Validation is the expected-value discipline — unknown
    members, indices outside the array, scalar/composite confusion and an
    ambiguous union are refused — and every declared member must be given.
    Mismatches carry the full path (``return.header.len``).
    """
    node = _relative_tree(entries)
    _validate(node, declared, "return")
    active: dict[str, str] = {}
    expected = _resolve(node, declared, "return", active)
    return compare(declared, expected, actual, path="return", tolerances=tolerances, active_members=active)


def resolve_input_values(
    entries: Mapping[str, str],
    declared: Mapping[str, CType],
) -> dict[str, Node]:
    """Validate initial global values (``inputs.globals``) against the declared types.

    The structural rules are the expected-value rules: an unknown member, an
    index outside the array, a scalar where a composite is declared (or the
    reverse) and a union given more than one member are refused. Completeness
    is **not** required: C zero-initializes what an initializer omits, so a
    partial initializer is a valid initial state. Returns, per root, the
    validated tree (string leaves, member/index dict nodes) for the initializer
    rendering.
    """
    trees = expected_trees(entries)
    for root, node in trees.items():
        if root not in declared:
            raise ValueParseError(f"initial value names '{root}', which has no declared type", reason="unknown_variable")
        _validate(node, declared[root], root)
    return trees


def flatten_expected(root: str, value: Any) -> dict[str, str]:
    """The flat authored form of a nested value: ``root.member`` / ``root[i]`` keys to strings."""
    if not _IDENTIFIER.fullmatch(root):
        raise ValueParseError(f"'{root}' is not an identifier", reason="invalid_value_path")
    flat: dict[str, str] = {}

    def walk(path: str, node: Any) -> None:
        if isinstance(node, str):
            flat[path] = node
        elif isinstance(node, Mapping):
            for name in sorted(node):
                if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
                    raise ValueParseError(f"'{path}' has member name {name!r}, which is not an identifier", reason="invalid_value_path")
                walk(f"{path}.{name}", node[name])
        elif isinstance(node, Sequence):
            for index, item in enumerate(node):
                walk(f"{path}[{index}]", item)
        else:
            raise ValueParseError(f"'{path}' holds a {type(node).__name__}; expected values are text", reason="invalid_value")

    walk(root, value)
    if not flat:
        raise ValueParseError(f"'{root}' has no values to author", reason="empty_value")
    return flat


# --- declared types from the analysis type graph -------------------------------------------------------


def ctype_from_model(type_ref: str, types: Mapping[str, TypeModel]) -> CType:
    """The comparison engine's declared type for ``type_ref`` (``ref:type.<id>``) in the type graph."""
    return _from_model(type_ref, types, ())


def _from_model(ref: str, types: Mapping[str, TypeModel], visiting: tuple[str, ...]) -> CType:
    key = ref.removeprefix("ref:")
    if key in visiting:
        raise InvalidComparisonSpecError(f"type '{key}' refers to itself; recursive types cannot be compared member-wise", )
    model = types.get(key)
    if model is None:
        text = ref.removeprefix("ref:").removeprefix("type.")
        if text in _SIMPLE_BUILTINS:
            return ScalarType(text)
        raise InvalidComparisonSpecError(f"type '{ref}' is not in the type graph and is not a builtin scalar")
    trail = (*visiting, key)
    if model.kind == "builtin":
        name = model.name or ""
        if name not in _SIMPLE_BUILTINS:
            raise InvalidComparisonSpecError(f"builtin type '{name}' has no comparison rule")
        return ScalarType(name)
    if model.kind == "typedef":
        if not model.underlying_type:
            raise InvalidComparisonSpecError(f"typedef '{key}' has no underlying type")
        return _from_model(model.underlying_type, types, trail)
    if model.kind in ("struct", "union"):
        members = tuple(Member(m.name, _from_model(m.type, types, trail)) for m in model.members)
        return StructType(members) if model.kind == "struct" else UnionType(members)
    if model.kind == "enum":
        if not model.enumerators:
            raise InvalidComparisonSpecError(f"enum '{key}' has no enumerators")
        return EnumType({e.name: str(e.value) for e in model.enumerators})
    if model.kind == "array":
        if model.element_type is None:
            raise InvalidComparisonSpecError(f"array '{key}' has no element type")
        element = _from_model(model.element_type, types, trail)
        lengths = [d.size for d in model.dimensions] if model.dimensions else [model.size]
        if any(length is None for length in lengths):
            raise InvalidComparisonSpecError(f"array '{key}' has no fixed length and cannot be compared element-wise")
        result: CType = element
        for length in reversed(lengths):
            assert length is not None
            result = ArrayType(result, length)
        return result
    raise InvalidComparisonSpecError(
        f"type kind '{model.kind}' of '{key}' cannot be derived from the type graph "
        "(pointer comparison policy is authored per field)"
    )
