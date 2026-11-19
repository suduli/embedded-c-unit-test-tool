# implements: DSN-TCM-040, DSN-TCM-100
"""Ranged input expansion and robustness cases (WP-TCM-05).

A ranged input expands to one executed case per value in the range
(TOOL-TCD-070), at build time (DSN-TCM-040). Each expanded case carries a
derived identifier ``<base id>.r.<param>=<value>[+...]`` that is stable under
re-expansion — expanding the same base case with the same range always
yields the same identifiers, so results remain comparable across runs. The
expanded value rides the case's inputs, and the record is digest-bound per
D-02 option (a).

A case may be marked robustness (TOOL-TCD-130, DSN-TCM-100): it supplies
out-of-range or invalid inputs with the tool's own range checking disabled,
so the tool does not refuse to express exactly the case the user needs.
The range check is :func:`ensure_range_checking`; it rejects out-of-range
inputs on normal cases and passes robustness-marked ones.

Satisfies: TOOL-TCD-070, TOOL-TCD-130; DSN-TCM-040, DSN-TCM-100.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from itertools import product

from ectt.tcm.datacases import DataDrivenTestCase, compute_case_digest
from ectt.tcm.errors import RangeCheckingError, RangeExpansionError

__all__ = [
    "RangedInput",
    "ValidRange",
    "expand_integer_range",
    "expand_case",
    "mark_robustness",
    "ensure_range_checking",
]


@dataclass(frozen=True)
class RangedInput:
    """One ranged input: the parameter name and its expanded value texts."""

    parameter: str
    values: tuple[str, ...]


@dataclass(frozen=True)
class ValidRange:
    """A declared valid integer range, inclusive of both ends."""

    lo: str
    hi: str


def _parse_range_int(text: str, *, what: str) -> int:
    stripped = text.strip()
    body = stripped[1:] if stripped[:1] in "+-" else stripped
    if not body.isdigit() or (len(body) > 1 and body[0] == "0"):
        raise RangeExpansionError(f"{what} must be decimal integer text, got '{text}'")
    return int(stripped, 10)


def expand_integer_range(lo: str, hi: str, step: str) -> tuple[str, ...]:
    """Expand an inclusive integer range into one value text per value.

    ``step`` must be >= 1 and ``lo <= hi``; both bounds are included when the
    range lands on them.
    """
    lo_num = _parse_range_int(lo, what="range lower bound")
    hi_num = _parse_range_int(hi, what="range upper bound")
    step_num = _parse_range_int(step, what="range step")
    if step_num < 1:
        raise RangeExpansionError(f"range step must be >= 1, got {step_num}")
    if lo_num > hi_num:
        raise RangeExpansionError(
            f"range lower bound {lo_num} exceeds upper bound {hi_num}"
        )
    return tuple(str(value) for value in range(lo_num, hi_num + 1, step_num))


def _derived_case_id(base_id: str, combination: Sequence[tuple[str, str]]) -> str:
    """The stable derived identifier for one expansion combination."""
    return base_id + ".r." + "+".join(f"{param}={value}" for param, value in combination)


def expand_case(
    case: DataDrivenTestCase,
    ranged_inputs: Sequence[RangedInput],
) -> tuple[DataDrivenTestCase, ...]:
    """Expand a case's ranged inputs into one case per value combination.

    The cartesian product is taken in declared spec order. Each expanded
    case merges the value into ``inputs.parameters`` (overriding the base
    value for that parameter), keeps every other field of the base case, and
    carries a fresh matching digest binding (D-02 option a).
    """
    if not ranged_inputs:
        return ()
    for spec in ranged_inputs:
        if not spec.parameter.strip():
            raise RangeExpansionError("ranged input requires a non-empty parameter name")
        if not spec.values:
            raise RangeExpansionError(
                f"ranged input '{spec.parameter}' expands to no values"
            )
    axes = [(spec.parameter, spec.values) for spec in ranged_inputs]
    expanded: list[DataDrivenTestCase] = []
    for combination in product(*[axis[1] for axis in axes]):
        pairs = tuple((axes[i][0], value) for i, value in enumerate(combination))
        overrides = dict(pairs)
        parameters = dict(case.inputs.parameters)
        parameters.update(overrides)
        derived = DataDrivenTestCase(
            case_id=_derived_case_id(case.case_id, pairs),
            unit=case.unit,
            function=case.function,
            inputs=type(case.inputs)(parameters=parameters, global_inits=case.inputs.global_inits),
            expected=case.expected,
            stubs=case.stubs,
            origin=case.origin,
            requirements=case.requirements,
            suites=case.suites,
            robustness=case.robustness,
        )
        digest = compute_case_digest(derived.content_payload())
        expanded.append(replace(derived, recorded_digest=digest, content_digest=digest))
    return tuple(expanded)


def mark_robustness(case: DataDrivenTestCase) -> DataDrivenTestCase:
    """Mark a case robustness: out-of-range inputs become expressible."""
    if case.robustness:
        return case
    marked = replace(case, robustness=True)
    digest = compute_case_digest(marked.content_payload())
    return replace(marked, recorded_digest=digest, content_digest=digest)


def ensure_range_checking(
    case: DataDrivenTestCase,
    valid_ranges: Mapping[str, ValidRange],
) -> None:
    """The tool's own range check (TOOL-TCD-130).

    Every parameter with a declared valid range must carry an in-range value.
    A robustness-marked case is exempt: its out-of-range or invalid inputs
    are exactly the point (DSN-TCM-100).
    """
    if case.robustness:
        return
    for parameter, valid_range in valid_ranges.items():
        value = case.inputs.parameters.get(parameter)
        if value is None:
            continue
        lo = _parse_range_int(valid_range.lo, what=f"valid range lower bound for '{parameter}'")
        hi = _parse_range_int(valid_range.hi, what=f"valid range upper bound for '{parameter}'")
        try:
            actual = _parse_range_int(value, what=f"parameter '{parameter}'")
        except RangeExpansionError as exc:
            raise RangeCheckingError(
                f"parameter '{parameter}' of case '{case.case_id}' has invalid "
                f"value text: {exc}",
            ) from exc
        if not lo <= actual <= hi:
            raise RangeCheckingError(
                f"parameter '{parameter}' of case '{case.case_id}' carries "
                f"{actual}, outside the valid range [{lo}, {hi}]; mark the case "
                "robustness to express out-of-range inputs (TOOL-TCD-130)"
            )
