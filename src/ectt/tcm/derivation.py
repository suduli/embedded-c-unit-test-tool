# implements: TOOL-TCD-110, TOOL-TCD-120
"""Test case derivation: boundary values, equivalence classes, classification trees (WP-TCM-07).

TOOL-TCD-110: derive test cases by boundary value analysis and equivalence class
partitioning of input parameters. TOOL-TCD-120: support classification-tree-based
test case design.

Derivation produces **input vectors**, not finished tests. It never invents an
expected value (the user, or observation of a generated case, supplies that), and
it never invents a domain: a parameter's range comes from authored data
(``ParameterModel.value_range``, which the analyser round-trips but never
manufactures) or from the caller, and a parameter without one is reported as
unbounded rather than guessed.

* **Boundary value analysis.** For an inclusive integer range ``[lo, hi]``:
  ``lo``, ``lo+1``, a nominal midpoint, ``hi-1``, ``hi``; with ``robust=True`` also
  ``lo-1`` and ``hi+1`` (invalid values). Duplicates collapse (a one-value range
  gives one value) and every value keeps the role it was derived for.
* **Equivalence class partitioning.** A range gives a valid class (representative:
  the nominal midpoint) and two invalid classes (below, above; representatives
  ``lo-1`` and ``hi+1``). An enumeration gives one valid class per member. Callers
  may declare their own classes.
* **Classification trees.** A tree is classifications, each with classes; a class
  may be refined by sub-classifications. A test case selects one leaf class per
  classification (recursively into refinements). ``each_choice`` covers every class
  at least once with the fewest vectors; ``all_combinations`` is the full product.
* **Combination strategies** for several parameters: ``one_at_a_time`` (vary one
  parameter through its values, the others at nominal), ``each_choice`` and
  ``all_combinations``. ``all_combinations`` is capped (``max_vectors``); exceeding
  the cap raises instead of silently truncating.

Vectors carrying an invalid value are marked ``invalid`` and become
robustness-marked cases (TOOL-TCD-130), so the tool's own range check does not
refuse the very cases derivation produced.

Satisfies: TOOL-TCD-110, TOOL-TCD-120.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import product

from ectt.ana.model import ParameterModel
from ectt.tcm.datacases import (
    DataDrivenTestCase,
    TestCaseExpected,
    TestCaseInputs,
    refresh_digest,
)
from ectt.tcm.errors import DerivationError
from ectt.tcm.ranged import mark_robustness

__all__ = [
    "DEFAULT_MAX_VECTORS",
    "STRATEGIES",
    "ClassificationNode",
    "TreeClass",
    "DerivedValue",
    "DerivedVector",
    "EquivalenceClass",
    "IntegerDomain",
    "boundary_values",
    "classification_vectors",
    "derive_vectors",
    "domains_from_parameters",
    "equivalence_classes",
    "vectors_to_cases",
]

DEFAULT_MAX_VECTORS = 1000
STRATEGIES: tuple[str, ...] = ("one_at_a_time", "each_choice", "all_combinations")


@dataclass(frozen=True)
class IntegerDomain:
    """An inclusive integer range for one parameter."""

    parameter: str
    low: int
    high: int

    def __post_init__(self) -> None:
        if not self.parameter or any(c.isspace() for c in self.parameter):
            raise DerivationError("parameter name must be a non-empty token", reason="invalid_parameter")
        if self.low > self.high:
            raise DerivationError(
                f"range of '{self.parameter}' has lower bound {self.low} above upper bound {self.high}",
                reason="invalid_range",
            )

    @property
    def nominal(self) -> int:
        return self.low + (self.high - self.low) // 2


@dataclass(frozen=True)
class DerivedValue:
    """One value for one parameter, with the role it was derived for."""

    value: str
    role: str  # below_min | min | above_min | nominal | below_max | max | above_max | class name
    valid: bool = True


@dataclass(frozen=True)
class EquivalenceClass:
    """One class of inputs with a representative; ``representative`` may be absent for an unrepresentable invalid class."""

    name: str
    valid: bool
    representative: str | None


@dataclass(frozen=True)
class TreeClass:
    """One class of a classification.

    ``value`` is what the classification's parameter receives when the class is
    chosen (``None`` for a class that only refines); ``refinements`` are the
    sub-classifications that must then also be decided; ``valid`` is False for a
    class of invalid inputs.
    """

    name: str
    value: str | None = None
    refinements: tuple[ClassificationNode, ...] = ()
    valid: bool = True


@dataclass(frozen=True)
class ClassificationNode:
    """A classification (an aspect of the input) and its classes."""

    parameter: str
    classes: tuple[TreeClass, ...]


@dataclass(frozen=True)
class DerivedVector:
    """One derived input vector: parameter values plus the role of each."""

    vector_id: str
    values: Mapping[str, DerivedValue] = field(default_factory=dict)

    @property
    def parameters(self) -> dict[str, str]:
        return {name: v.value for name, v in sorted(self.values.items())}

    @property
    def invalid(self) -> bool:
        return any(not v.valid for v in self.values.values())


# --- boundary value analysis -------------------------------------------------------------


def boundary_values(domain: IntegerDomain, *, robust: bool = False) -> tuple[DerivedValue, ...]:
    """Boundary values of ``domain`` in ascending order, duplicates collapsed.

    A value that falls on more than one role keeps the first role in the order
    below_min, nominal, min, above_min, below_max, max, above_max, so the nominal
    value always carries the ``nominal`` role (``one_at_a_time`` holds the other
    parameters at it, even for a range as small as 0..1). ``robust`` adds the two
    invalid values just outside the range.
    """
    lo, hi = domain.low, domain.high
    candidates: list[tuple[int, str, bool]] = []
    if robust:
        candidates.append((lo - 1, "below_min", False))
    candidates += [
        (domain.nominal, "nominal", True),
        (lo, "min", True),
        (lo + 1, "above_min", True),
        (hi - 1, "below_max", True),
        (hi, "max", True),
    ]
    if robust:
        candidates.append((hi + 1, "above_max", False))
    seen: dict[int, DerivedValue] = {}
    for number, role, valid in candidates:
        if number < lo - 1 or number > hi + 1:
            continue
        if valid and not lo <= number <= hi:
            continue
        seen.setdefault(number, DerivedValue(str(number), role, valid))
    return tuple(seen[n] for n in sorted(seen))


# --- equivalence class partitioning ------------------------------------------------------


def equivalence_classes(domain: IntegerDomain) -> tuple[EquivalenceClass, ...]:
    """The valid class and the two invalid classes of an integer range."""
    return (
        EquivalenceClass("below_range", False, str(domain.low - 1)),
        EquivalenceClass("in_range", True, str(domain.nominal)),
        EquivalenceClass("above_range", False, str(domain.high + 1)),
    )


def domains_from_parameters(parameters: Sequence[ParameterModel]) -> tuple[tuple[IntegerDomain, ...], tuple[str, ...]]:
    """Integer domains from authored ``value_range`` data; unranged parameters are returned by name.

    A parameter with only one bound, a non-integer bound or no range cannot be
    partitioned from authored data; it is reported in the second element, never
    given an invented range.
    """
    domains: list[IntegerDomain] = []
    unbounded: list[str] = []
    for parameter in parameters:
        value_range = parameter.value_range
        if value_range is None or value_range.low is None or value_range.high is None:
            unbounded.append(parameter.name)
            continue
        try:
            low, high = int(value_range.low, 10), int(value_range.high, 10)
        except ValueError:
            unbounded.append(parameter.name)
            continue
        domains.append(IntegerDomain(parameter.name, low, high))
    return tuple(domains), tuple(unbounded)


# --- combination -------------------------------------------------------------------------


def _vector_id(prefix: str, values: Mapping[str, DerivedValue]) -> str:
    return f"{prefix}." + "+".join(f"{name}={v.value}" for name, v in sorted(values.items()))


def derive_vectors(
    choices: Mapping[str, Sequence[DerivedValue]],
    *,
    strategy: str = "one_at_a_time",
    id_prefix: str = "derived",
    max_vectors: int = DEFAULT_MAX_VECTORS,
) -> tuple[DerivedVector, ...]:
    """Combine per-parameter ``choices`` into vectors.

    ``one_at_a_time`` needs a ``nominal`` value for every parameter that has more
    than one choice; each other parameter is held at it. ``each_choice`` uses the
    fewest vectors that include every value of every parameter at least once.
    ``all_combinations`` is the product, refused above ``max_vectors``. The result
    is sorted by vector id and free of duplicates.
    """
    if strategy not in STRATEGIES:
        raise DerivationError(f"unknown strategy '{strategy}' (expected one of {', '.join(STRATEGIES)})", reason="unknown_strategy")
    if not id_prefix or any(c.isspace() for c in id_prefix):
        raise DerivationError("id prefix must be a non-empty token", reason="invalid_prefix")
    if max_vectors < 1:
        raise DerivationError("max_vectors must be at least 1", reason="invalid_bound")
    names = sorted(choices)
    for name in names:
        if not choices[name]:
            raise DerivationError(f"parameter '{name}' has no choices to derive from", reason="empty_choices")

    rows: list[dict[str, DerivedValue]] = []
    if strategy == "all_combinations":
        size = 1
        for name in names:
            size *= len(choices[name])
        if size > max_vectors:
            raise DerivationError(
                f"all_combinations would produce {size} vectors, above max_vectors={max_vectors}; use each_choice or raise the bound",
                reason="too_many_combinations",
            )
        rows = [dict(zip(names, combo, strict=True)) for combo in product(*(choices[n] for n in names))]
    elif strategy == "each_choice":
        longest = max((len(choices[n]) for n in names), default=0)
        rows = [{n: choices[n][i % len(choices[n])] for n in names} for i in range(longest)]
    else:
        nominal: dict[str, DerivedValue] = {}
        for name in names:
            options = choices[name]
            pick = next((v for v in options if v.role == "nominal"), options[0] if len(options) == 1 else None)
            if pick is None:
                raise DerivationError(
                    f"one_at_a_time needs a nominal value for '{name}', which has {len(options)} choices",
                    reason="no_nominal",
                )
            nominal[name] = pick
        rows = [dict(nominal)] if names else []
        for name in names:
            for value in choices[name]:
                if value != nominal[name]:
                    rows.append({**nominal, name: value})

    unique: dict[str, DerivedVector] = {}
    for row in rows:
        vector = DerivedVector(_vector_id(id_prefix, row), row)
        unique.setdefault(vector.vector_id, vector)
    return tuple(unique[key] for key in sorted(unique))


# --- classification trees ----------------------------------------------------------------


def _selections(node: ClassificationNode) -> list[list[tuple[str, str, DerivedValue | None]]]:
    """Every way to decide ``node`` (one class, then its refinements): lists of (parameter, class, value)."""
    results: list[list[tuple[str, str, DerivedValue | None]]] = []
    for tree_class in node.classes:
        value = DerivedValue(tree_class.value, tree_class.name, tree_class.valid) if tree_class.value is not None else None
        own: tuple[str, str, DerivedValue | None] = (node.parameter, tree_class.name, value)
        sub_choices = [_selections(child) for child in tree_class.refinements]
        combos = product(*sub_choices) if sub_choices else [()]
        results.extend([own, *[item for part in combo for item in part]] for combo in combos)
    return results


def classification_vectors(
    tree: Sequence[ClassificationNode],
    *,
    strategy: str = "each_choice",
    id_prefix: str = "ctree",
    max_vectors: int = DEFAULT_MAX_VECTORS,
) -> tuple[DerivedVector, ...]:
    """Test cases of a classification tree: one leaf class per classification.

    ``each_choice`` picks the fewest combinations covering every class at least
    once; ``all_combinations`` is the full product (capped). A class with no value
    only refines; it contributes no parameter value of its own.
    """
    if strategy not in ("each_choice", "all_combinations"):
        raise DerivationError("classification trees support each_choice and all_combinations", reason="unknown_strategy")
    if not tree:
        raise DerivationError("a classification tree needs at least one classification", reason="empty_tree")
    per_node = [_selections(node) for node in tree]
    if any(not options for options in per_node):
        raise DerivationError("every classification needs at least one class", reason="empty_classification")

    if strategy == "all_combinations":
        size = 1
        for options in per_node:
            size *= len(options)
        if size > max_vectors:
            raise DerivationError(
                f"all_combinations would produce {size} test cases, above max_vectors={max_vectors}",
                reason="too_many_combinations",
            )
        picks = [list(combo) for combo in product(*per_node)]
    else:
        longest = max(len(options) for options in per_node)
        picks = [[options[i % len(options)] for options in per_node] for i in range(longest)]

    unique: dict[str, DerivedVector] = {}
    for pick in picks:
        values: dict[str, DerivedValue] = {}
        labels: list[str] = []
        for selection in pick:
            for parameter, class_name, value in selection:
                labels.append(f"{parameter}:{class_name}")
                if value is not None:
                    existing = values.get(parameter)
                    if existing is not None and (existing.value, existing.valid) != (value.value, value.valid):
                        raise DerivationError(
                            f"classification tree assigns '{parameter}' different values in one test case", reason="conflicting_assignment"
                        )
                    values.setdefault(parameter, value)
        vector_id = f"{id_prefix}." + "+".join(labels)
        unique.setdefault(vector_id, DerivedVector(vector_id, values))
    return tuple(unique[key] for key in sorted(unique))


# --- to test cases -----------------------------------------------------------------------


def vectors_to_cases(
    vectors: Sequence[DerivedVector],
    *,
    unit: str,
    function: str,
    fixed_parameters: Mapping[str, str] | None = None,
) -> tuple[DataDrivenTestCase, ...]:
    """Turn derived vectors into ordinary cases with **no expected value**.

    The user supplies expectations (or runs the cases through ``ectt.atg`` to
    observe them). A vector carrying an invalid value becomes a robustness case
    so the tool's range check does not refuse it. ``fixed_parameters`` supplies
    values for parameters the derivation does not vary. Ids are the vector ids.
    """
    if not unit.strip() or not function.strip():
        raise DerivationError("cases need a unit and a function", reason="invalid_target")
    fixed = dict(fixed_parameters or {})
    cases: list[DataDrivenTestCase] = []
    for vector in vectors:
        overlap = sorted(set(fixed) & set(vector.values))
        if overlap:
            raise DerivationError(f"fixed parameters repeat derived ones: {', '.join(overlap)}", reason="fixed_overlap")
        case = refresh_digest(
            DataDrivenTestCase(
                case_id=vector.vector_id,
                unit=unit,
                function=function,
                inputs=TestCaseInputs(parameters={**fixed, **vector.parameters}),
                expected=TestCaseExpected(),
                stubs=(),
            )
        )
        cases.append(mark_robustness(case) if vector.invalid else case)
    return tuple(cases)

