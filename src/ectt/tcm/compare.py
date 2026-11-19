# implements: DSN-TCM-030
"""Expected-value comparison engine (WP-TCM-03).

Type-directed expected-value comparison (SDD-002 §5.1, DSN-TCM-030): how a
value is compared follows from its declared C type.

- Scalars and enums compare by value (TOOL-TCD-050). Integer text is decimal
  or ``0x`` hex; C octal text is rejected with a named error rather than
  silently misread.
- Pointers compare by the per-field policy: ``null`` (nullness only),
  ``address`` (recorded address text), or ``pointee`` (recursive comparison
  with the pointee type).
- Arrays and structs compare member-wise; only declared members participate,
  so padding is excluded by construction.
- Unions compare only the member the test names active.
- Floating-point comparison takes an explicit absolute or relative tolerance
  and defaults to exact (TOOL-TCD-060, DSN-TCM-030).

The engine is the semantics oracle: it evaluates comparisons in memory and
produces deterministic, path-addressed diagnostics that feed EXE-020 failure
records. It is pure — no time, no randomness, no I/O. Rendering the
semantics into harness C is CMP-GEN scope.

Satisfies: TOOL-TCD-050, TOOL-TCD-060; DSN-TCM-030; SDD-002 §5.1.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from ectt.core.determinism import canonical_float_repr, canonical_json
from ectt.tcm.errors import InvalidComparisonSpecError, ValueParseError

__all__ = [
    "ScalarType",
    "EnumType",
    "PointerType",
    "ArrayType",
    "StructType",
    "UnionType",
    "CType",
    "Member",
    "Tolerance",
    "Mismatch",
    "ComparisonResult",
    "compare",
]

ScalarKind = Literal["integral", "float"]
PointerPolicy = Literal["null", "address", "pointee"]

_INTEGRAL_TYPES = frozenset(
    {
        "_Bool",
        "char",
        "signed char",
        "unsigned char",
        "short",
        "unsigned short",
        "int",
        "unsigned int",
        "long",
        "unsigned long",
        "long long",
        "unsigned long long",
    }
)
_FLOAT_TYPES = frozenset({"float", "double", "long double"})
_MISMATCH_REASONS = (
    "value_mismatch",
    "element_count",
    "missing_member",
    "unexpected_member",
)


@dataclass(frozen=True)
class ScalarType:
    """A scalar C type: integrals (incl. ``_Bool``, ``char``) and floats."""

    c_type: str

    def __post_init__(self) -> None:
        if self.c_type not in _INTEGRAL_TYPES and self.c_type not in _FLOAT_TYPES:
            raise InvalidComparisonSpecError(
                f"unknown scalar C type '{self.c_type}'; expected one of "
                f"{sorted(_INTEGRAL_TYPES | _FLOAT_TYPES)}"
            )

    @property
    def kind(self) -> ScalarKind:
        if self.c_type in _FLOAT_TYPES:
            return "float"
        return "integral"


@dataclass(frozen=True)
class EnumType:
    """An enum: comparison is by value, with declared enumerator names accepted."""

    enumerators: Mapping[str, str]

    def __post_init__(self) -> None:
        if not self.enumerators:
            raise InvalidComparisonSpecError("an enum must declare at least one enumerator")


@dataclass(frozen=True)
class PointerType:
    """A pointer with the per-field comparison policy (SDD-002 §5.1)."""

    policy: PointerPolicy
    pointee: CType | None = None

    def __post_init__(self) -> None:
        if self.policy == "pointee" and self.pointee is None:
            raise InvalidComparisonSpecError(
                "pointer policy 'pointee' requires the pointee's declared type"
            )


@dataclass(frozen=True)
class Member:
    """One struct/union member: declared name and type."""

    name: str
    type: CType


@dataclass(frozen=True)
class ArrayType:
    """An array: element-wise comparison with the declared element type."""

    element: CType
    length: int

    def __post_init__(self) -> None:
        if self.length < 0:
            raise InvalidComparisonSpecError("array length must be non-negative")


@dataclass(frozen=True)
class StructType:
    """A struct: member-wise comparison in declared member order."""

    members: tuple[Member, ...]


@dataclass(frozen=True)
class UnionType:
    """A union: only the active member the test names is compared."""

    members: tuple[Member, ...]


CType = ScalarType | EnumType | PointerType | ArrayType | StructType | UnionType


@dataclass(frozen=True)
class Tolerance:
    """An explicit float tolerance (TOOL-TCD-060); exact when absent."""

    mode: Literal["absolute", "relative"]
    value: float

    def __post_init__(self) -> None:
        if self.mode not in ("absolute", "relative"):
            raise InvalidComparisonSpecError(
                f"tolerance mode must be 'absolute' or 'relative', got '{self.mode}'"
            )
        if not math.isfinite(self.value) or self.value < 0:
            raise InvalidComparisonSpecError(
                "tolerance value must be a finite non-negative number"
            )


@dataclass(frozen=True)
class Mismatch:
    """One diagnostic: path, expected, actual, and a reason from a fixed set."""

    path: str
    expected: str
    actual: str
    reason: str


@dataclass(frozen=True)
class ComparisonResult:
    """Outcome of one comparison: matched flag plus deterministic diagnostics."""

    matched: bool
    mismatches: tuple[Mismatch, ...]


def _parse_int_text(text: str, *, path: str) -> int:
    """Parse integer text with C-compatible decimal/hex; octal is rejected."""
    stripped = text.strip()
    body = stripped[1:] if stripped[:1] in "+-" else stripped
    if body[:2].lower() == "0x":
        digits = body[2:]
        if digits and all(c in "0123456789abcdefABCDEF" for c in digits):
            return int(stripped, 16)
    elif body.isdigit():
        if len(body) > 1 and body[0] == "0":
            raise ValueParseError(
                f"'{text}' at '{path}' looks like C octal text; leading-zero "
                "integers are rejected to avoid silent misreads"
            )
        return int(stripped, 10)
    raise ValueParseError(
        f"'{text}' at '{path}' is not valid integer text (decimal or 0x hex; "
        "C octal text is rejected to avoid silent misreads)"
    )


def _parse_bool_text(text: str, *, path: str) -> int:
    lowered = text.strip().lower()
    if lowered in ("true", "1"):
        return 1
    if lowered in ("false", "0"):
        return 0
    raise ValueParseError(f"'{text}' at '{path}' is not valid _Bool text (true/false/0/1)")


def _parse_char_text(text: str, *, path: str) -> int:
    if len(text) == 1 and not text.isdigit():
        return ord(text)
    return _parse_int_text(text, path=path)


def _parse_float_text(text: str, *, path: str) -> float:
    try:
        return float(text.strip())
    except ValueError:
        raise ValueParseError(
            f"'{text}' at '{path}' is not valid floating-point text"
        ) from None


def _parse_enum_value(text: str, declared: EnumType, *, path: str) -> int:
    stripped = text.strip()
    if stripped in declared.enumerators:
        return _parse_int_text(declared.enumerators[stripped], path=path)
    if stripped.lstrip("+-").isdigit() or stripped[:2].lower() in ("0x", "-0x", "+0x"):
        return _parse_int_text(stripped, path=path)
    raise ValueParseError(
        f"'{text}' at '{path}' is neither a declared enumerator "
        f"({sorted(declared.enumerators)}) nor integer text"
    )


def _render(value: Any) -> str:
    """Deterministic diagnostic rendering: scalars verbatim, composites canonical."""
    if isinstance(value, str):
        return value
    return canonical_json(value)


def _float_mismatch(
    expected: float,
    actual: float,
    tolerance: Tolerance | None,
    path: str,
    expected_text: str,
    actual_text: str,
) -> list[Mismatch]:
    expected_nan = math.isnan(expected)
    actual_nan = math.isnan(actual)
    if expected_nan or actual_nan:
        if expected_nan and actual_nan:
            return []
        return [
            Mismatch(
                path=path,
                expected=canonical_float_repr(expected),
                actual=canonical_float_repr(actual),
                reason="value_mismatch",
            )
        ]
    matched = False
    if tolerance is None:
        matched = expected == actual
    elif tolerance.mode == "absolute":
        matched = abs(actual - expected) <= tolerance.value
    else:  # relative
        matched = abs(actual - expected) <= tolerance.value * abs(expected)
    if matched:
        return []
    return [
        Mismatch(
            path=path,
            expected=expected_text or canonical_float_repr(expected),
            actual=actual_text or canonical_float_repr(actual),
            reason="value_mismatch",
        )
    ]


def _compare_scalar(
    declared: ScalarType,
    expected: str,
    actual: str,
    *,
    path: str,
    tolerance: Tolerance | None,
) -> list[Mismatch]:
    if tolerance is not None and declared.kind != "float":
        raise InvalidComparisonSpecError(
            f"tolerance at '{path}' applies only to float types, not '{declared.c_type}'"
        )
    if declared.kind == "float":
        expected_num = _parse_float_text(expected, path=path)
        actual_num = _parse_float_text(actual, path=path)
        return _float_mismatch(expected_num, actual_num, tolerance, path, expected, actual)
    if declared.c_type == "_Bool":
        expected_num = _parse_bool_text(expected, path=path)
        actual_num = _parse_bool_text(actual, path=path)
    elif declared.c_type == "char":
        expected_num = _parse_char_text(expected, path=path)
        actual_num = _parse_char_text(actual, path=path)
    else:
        expected_num = _parse_int_text(expected, path=path)
        actual_num = _parse_int_text(actual, path=path)
    if expected_num == actual_num:
        return []
    return [Mismatch(path=path, expected=expected, actual=actual, reason="value_mismatch")]


def _is_null_text(text: str) -> bool:
    return text.strip() in ("NULL", "0")


def _compare_pointer(
    declared: PointerType,
    expected: Any,
    actual: Any,
    *,
    path: str,
    tolerances: Mapping[str, Tolerance],
    active_members: Mapping[str, str],
) -> list[Mismatch]:
    if declared.policy == "null":
        if isinstance(expected, str) and isinstance(actual, str):
            if _is_null_text(expected) == _is_null_text(actual):
                return []
            return [Mismatch(path=path, expected=expected, actual=actual, reason="value_mismatch")]
        raise InvalidComparisonSpecError(
            f"pointer policy 'null' at '{path}' compares address text; got non-text values"
        )
    if declared.policy == "address":
        if isinstance(expected, str) and isinstance(actual, str):
            if expected.strip() == actual.strip():
                return []
            return [Mismatch(path=path, expected=expected, actual=actual, reason="value_mismatch")]
        raise InvalidComparisonSpecError(
            f"pointer policy 'address' at '{path}' compares recorded address text; "
            "got non-text values"
        )
    # pointee: expected/actual carry the pointee values
    if declared.pointee is None:  # guarded by __post_init__; kept for the type checker
        raise InvalidComparisonSpecError(f"pointer at '{path}' has no pointee type")
    return _compare(
        declared.pointee, expected, actual, path=path,
        tolerances=tolerances, active_members=active_members,
    )


def _compare_array(
    declared: ArrayType,
    expected: Sequence[Any],
    actual: Sequence[Any],
    *,
    path: str,
    tolerances: Mapping[str, Tolerance],
    active_members: Mapping[str, str],
) -> list[Mismatch]:
    if len(expected) != len(actual) or len(expected) != declared.length:
        return [
            Mismatch(
                path=path,
                expected=f"{declared.length} elements",
                actual=f"{len(actual)} elements",
                reason="element_count",
            )
        ]
    for index in range(declared.length):
        mismatch = _compare(
            declared.element,
            expected[index],
            actual[index],
            path=f"{path}[{index}]",
            tolerances=tolerances,
            active_members=active_members,
        )
        if mismatch:
            return mismatch  # first failing element: deterministic, path-indexed
    return []


def _compare_struct(
    declared: StructType,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    path: str,
    tolerances: Mapping[str, Tolerance],
    active_members: Mapping[str, str],
) -> list[Mismatch]:
    declared_names = [member.name for member in declared.members]
    for name in expected:
        if name not in declared_names:
            raise ValueParseError(
                f"struct value at '{path}' names '{name}', which is not a declared member"
            )
    for name in declared_names:
        if name not in expected:
            raise ValueParseError(f"struct value at '{path}' is missing declared member '{name}'")
    if sorted(actual) != sorted(declared_names):
        missing = sorted(set(declared_names) - set(actual))
        extra = sorted(set(actual) - set(declared_names))
        if missing:
            return [
                Mismatch(
                    path=path,
                    expected=f"members {missing}",
                    actual="absent",
                    reason="missing_member",
                )
            ]
        return [
            Mismatch(
                path=path,
                expected="no extra members",
                actual=f"members {extra}",
                reason="unexpected_member",
            )
        ]
    mismatches: list[Mismatch] = []
    for member in declared.members:  # declared order: deterministic diagnostics
        mismatch = _compare(
            member.type,
            expected[member.name],
            actual[member.name],
            path=f"{path}.{member.name}" if path else member.name,
            tolerances=tolerances,
            active_members=active_members,
        )
        if mismatch:
            mismatches.extend(mismatch)
    return mismatches


def _compare(
    declared: CType,
    expected: Any,
    actual: Any,
    *,
    path: str,
    tolerances: Mapping[str, Tolerance],
    active_members: Mapping[str, str],
) -> list[Mismatch]:
    tolerance = tolerances.get(path)
    if isinstance(declared, ScalarType):
        if not isinstance(expected, str) or not isinstance(actual, str):
            raise ValueParseError(
                f"scalar value at '{path}' must be text; got {type(expected).__name__}/"
                f"{type(actual).__name__}"
            )
        return _compare_scalar(declared, expected, actual, path=path, tolerance=tolerance)
    if isinstance(declared, EnumType):
        if not isinstance(expected, str) or not isinstance(actual, str):
            raise ValueParseError(f"enum value at '{path}' must be text")
        if _parse_enum_value(expected, declared, path=path) == _parse_enum_value(
            actual, declared, path=path
        ):
            return []
        return [Mismatch(path=path, expected=expected, actual=actual, reason="value_mismatch")]
    if isinstance(declared, PointerType):
        return _compare_pointer(
            declared, expected, actual, path=path, tolerances=tolerances,
            active_members=active_members,
        )
    if isinstance(declared, ArrayType):
        if not isinstance(expected, Sequence) or isinstance(expected, str):
            raise ValueParseError(f"array value at '{path}' must be a sequence")
        if not isinstance(actual, Sequence) or isinstance(actual, str):
            raise ValueParseError(f"array value at '{path}' must be a sequence (actual)")
        return _compare_array(
            declared, expected, actual, path=path, tolerances=tolerances,
            active_members=active_members,
        )
    if isinstance(declared, StructType):
        if not isinstance(expected, Mapping) or not isinstance(actual, Mapping):
            raise ValueParseError(f"struct value at '{path}' must be a mapping")
        return _compare_struct(
            declared, expected, actual, path=path, tolerances=tolerances,
            active_members=active_members,
        )
    return _compare_union(
        declared, expected, actual, path=path,
        tolerances=tolerances, active_members=active_members,
    )


def _compare_union(
    declared: UnionType,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    path: str,
    tolerances: Mapping[str, Tolerance],
    active_members: Mapping[str, str],
) -> list[Mismatch]:
    declared_members = {member.name: member.type for member in declared.members}
    if len(declared_members) != len(declared.members):
        raise InvalidComparisonSpecError(
            f"union at '{path}' declares duplicate member names"
        )
    active = active_members.get(path)
    if active is None or not isinstance(active, str):
        raise InvalidComparisonSpecError(
            f"union comparison at '{path}' requires the test to name the active "
            "member (SDD-002 §5.1)"
        )
    if active not in declared_members:
        raise InvalidComparisonSpecError(
            f"union at '{path}' has no member '{active}' "
            f"(declared: {sorted(declared_members)})"
        )
    for value, side in ((expected, "expected"), (actual, "actual")):
        if not isinstance(value, Mapping):
            raise ValueParseError(f"union {side} value at '{path}' must be a mapping")
        unexpected = sorted(k for k in value if k not in declared_members)
        if unexpected:
            raise ValueParseError(
                f"union {side} value at '{path}' names non-member(s) {unexpected}"
            )
    if active not in expected or active not in actual:
        raise ValueParseError(
            f"union comparison at '{path}' is missing the active member '{active}' "
            "value in expected or actual"
        )
    return _compare(
        declared_members[active],
        expected[active],
        actual[active],
        path=f"{path}.{active}" if path else active,
        tolerances=tolerances,
        active_members=active_members,
    )


def compare(
    declared: CType,
    expected: Any,
    actual: Any,
    *,
    path: str = "value",
    tolerances: Mapping[str, Tolerance] | None = None,
    active_members: Mapping[str, str] | None = None,
) -> ComparisonResult:
    """Compare an actual value against the expected value under its declared type.

    ``path`` is the diagnostic root (e.g. ``expected_return`` or the global's
    name). ``tolerances`` maps comparison paths to explicit float tolerances
    (TOOL-TCD-060); ``active_members`` maps union comparison paths to the
    member the test names active (SDD-002 §5.1). Diagnostics are
    deterministic and emitted in declared member order.
    """
    mismatches = _compare(
        declared,
        expected,
        actual,
        path=path,
        tolerances=tolerances or {},
        active_members=active_members or {},
    )
    return ComparisonResult(matched=not mismatches, mismatches=tuple(mismatches))
