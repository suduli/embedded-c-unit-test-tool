# implements: TOOL-TCD-110, TOOL-TCD-120
"""Boundary, equivalence and classification-tree derivation (WP-TCM-07).

Verifies: TOOL-TCD-110 (boundary value analysis and equivalence class
partitioning of input parameters) and TOOL-TCD-120 (classification-tree design).
"""

from __future__ import annotations

import pytest

from ectt.ana.model import ParameterModel, RangeModel
from ectt.tcm.derivation import (
    STRATEGIES,
    ClassificationNode,
    DerivedValue,
    IntegerDomain,
    TreeClass,
    boundary_values,
    classification_vectors,
    derive_vectors,
    domains_from_parameters,
    equivalence_classes,
    vectors_to_cases,
)
from ectt.tcm.errors import DerivationError
from ectt.tcm.ranged import ValidRange, ensure_range_checking


def _values(domain: IntegerDomain, *, robust: bool = False) -> list[tuple[str, str, bool]]:
    return [(v.value, v.role, v.valid) for v in boundary_values(domain, robust=robust)]


# --- boundary value analysis ---------------------------------------------------------------


def test_bva_of_a_normal_range_gives_the_five_classic_values() -> None:
    assert _values(IntegerDomain("x", 0, 255)) == [
        ("0", "min", True),
        ("1", "above_min", True),
        ("127", "nominal", True),
        ("254", "below_max", True),
        ("255", "max", True),
    ]


def test_robust_bva_adds_the_two_invalid_values_just_outside() -> None:
    values = _values(IntegerDomain("x", 0, 255), robust=True)

    assert values[0] == ("-1", "below_min", False)
    assert values[-1] == ("256", "above_max", False)
    assert len(values) == 7
    assert [v for v in values if not v[2]] == [("-1", "below_min", False), ("256", "above_max", False)]


@pytest.mark.parametrize(
    ("low", "high", "expected"),
    [
        (5, 5, ["5"]),
        (0, 1, ["0", "1"]),
        (0, 2, ["0", "1", "2"]),
        (0, 3, ["0", "1", "2", "3"]),
        (-10, 10, ["-10", "-9", "0", "9", "10"]),
        (-3, -1, ["-3", "-2", "-1"]),
    ],
)
def test_bva_of_narrow_negative_and_degenerate_ranges(low: int, high: int, expected: list[str]) -> None:
    got = [v[0] for v in _values(IntegerDomain("x", low, high))]
    assert got == sorted(set(got), key=int)  # ascending, no duplicates
    assert set(expected) <= set(got) and len(got) == len(set(expected))


def test_robust_bva_of_a_one_value_range_has_both_neighbours() -> None:
    assert [(v[0], v[2]) for v in _values(IntegerDomain("x", 5, 5), robust=True)] == [("4", False), ("5", True), ("6", False)]


def test_bva_handles_values_beyond_sixty_four_bits() -> None:
    big = 2**70
    assert next(v[0] for v in _values(IntegerDomain("x", big, big + 10))) == str(big)


def test_every_boundary_value_keeps_the_role_it_was_derived_for() -> None:
    roles = {v.value: v.role for v in boundary_values(IntegerDomain("x", 0, 10), robust=True)}
    assert roles == {"-1": "below_min", "0": "min", "1": "above_min", "5": "nominal", "9": "below_max", "10": "max", "11": "above_max"}


def test_an_inverted_range_is_refused() -> None:
    with pytest.raises(DerivationError) as excinfo:
        IntegerDomain("x", 10, 0)
    assert excinfo.value.reason == "invalid_range"


@pytest.mark.parametrize("name", ["", "two words"])
def test_parameter_names_are_single_tokens(name: str) -> None:
    with pytest.raises(DerivationError) as excinfo:
        IntegerDomain(name, 0, 1)
    assert excinfo.value.reason == "invalid_parameter"


# --- equivalence class partitioning ---------------------------------------------------------


def test_a_range_has_one_valid_and_two_invalid_classes_with_representatives() -> None:
    classes = equivalence_classes(IntegerDomain("x", 10, 20))

    assert [(c.name, c.valid, c.representative) for c in classes] == [
        ("below_range", False, "9"),
        ("in_range", True, "15"),
        ("above_range", False, "21"),
    ]


def test_domains_come_from_authored_ranges_and_unranged_parameters_are_reported() -> None:
    parameters = [
        ParameterModel("a", "ref:type.int", value_range=RangeModel("0", "10")),
        ParameterModel("b", "ref:type.int"),
        ParameterModel("c", "ref:type.int", value_range=RangeModel("0", None)),
        ParameterModel("d", "ref:type.int", value_range=RangeModel("LOW", "HIGH")),
        ParameterModel("e", "ref:type.int", value_range=RangeModel("-5", "5")),
    ]

    domains, unbounded = domains_from_parameters(parameters)

    assert [(d.parameter, d.low, d.high) for d in domains] == [("a", 0, 10), ("e", -5, 5)]
    assert unbounded == ("b", "c", "d")


# --- combination strategies -----------------------------------------------------------------


def _choices() -> dict[str, tuple[DerivedValue, ...]]:
    return {
        "a": boundary_values(IntegerDomain("a", 0, 10)),
        "b": boundary_values(IntegerDomain("b", 0, 4)),
    }


def test_one_at_a_time_varies_each_parameter_with_the_others_nominal() -> None:
    vectors = derive_vectors(_choices(), strategy="one_at_a_time")

    assert len(vectors) == 1 + 4 + 4
    base = next(v for v in vectors if v.parameters == {"a": "5", "b": "2"})
    assert base.vector_id == "derived.a=5+b=2"
    for vector in vectors:
        differing = [n for n in ("a", "b") if vector.parameters[n] != base.parameters[n]]
        assert len(differing) <= 1


def test_each_choice_covers_every_value_with_the_fewest_vectors() -> None:
    choices = _choices()
    vectors = derive_vectors(choices, strategy="each_choice")

    assert len(vectors) == max(len(c) for c in choices.values())
    for name, options in choices.items():
        assert {v.parameters[name] for v in vectors} >= {o.value for o in options}


def test_all_combinations_is_the_full_product() -> None:
    assert len(derive_vectors(_choices(), strategy="all_combinations")) == 25


def test_all_combinations_beyond_the_bound_is_refused_not_truncated() -> None:
    with pytest.raises(DerivationError) as excinfo:
        derive_vectors(_choices(), strategy="all_combinations", max_vectors=24)
    assert excinfo.value.reason == "too_many_combinations"
    assert len(derive_vectors(_choices(), strategy="all_combinations", max_vectors=25)) == 25


def test_vectors_are_sorted_by_id_and_free_of_duplicates() -> None:
    vectors = derive_vectors(_choices(), strategy="one_at_a_time")
    ids = [v.vector_id for v in vectors]
    assert ids == sorted(ids) and len(ids) == len(set(ids))


def test_derivation_is_deterministic_and_independent_of_parameter_insertion_order() -> None:
    forward = _choices()
    backward = dict(reversed(list(forward.items())))
    assert derive_vectors(forward) == derive_vectors(backward)


def test_a_single_parameter_without_a_nominal_still_derives() -> None:
    only = {"m": (DerivedValue("7", "in_range"),)}
    (vector,) = derive_vectors(only, strategy="one_at_a_time")
    assert vector.parameters == {"m": "7"}


def test_one_at_a_time_without_a_nominal_for_a_multi_choice_parameter_is_refused() -> None:
    choices = {"m": (DerivedValue("1", "in_range"), DerivedValue("2", "other"))}
    with pytest.raises(DerivationError) as excinfo:
        derive_vectors(choices, strategy="one_at_a_time")
    assert excinfo.value.reason == "no_nominal"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"strategy": "pairwise"}, "unknown_strategy"),
        ({"id_prefix": ""}, "invalid_prefix"),
        ({"id_prefix": "a b"}, "invalid_prefix"),
        ({"max_vectors": 0}, "invalid_bound"),
    ],
)
def test_bad_derivation_settings_are_refused(kwargs: dict[str, object], reason: str) -> None:
    with pytest.raises(DerivationError) as excinfo:
        derive_vectors(_choices(), **kwargs)  # type: ignore[arg-type]
    assert excinfo.value.reason == reason


def test_a_parameter_with_no_choices_is_refused() -> None:
    with pytest.raises(DerivationError) as excinfo:
        derive_vectors({"a": ()})
    assert excinfo.value.reason == "empty_choices"


def test_strategies_are_the_documented_set() -> None:
    assert STRATEGIES == ("one_at_a_time", "each_choice", "all_combinations")


# --- classification trees -------------------------------------------------------------------


def _tree() -> list[ClassificationNode]:
    reason = ClassificationNode("reason", (TreeClass("sensor", "10"), TreeClass("supply", "11")))
    mode = ClassificationNode(
        "mode",
        (TreeClass("normal", "0"), TreeClass("degraded", None, (reason,)), TreeClass("off", "2")),
    )
    channel = ClassificationNode("channel", (TreeClass("adc0", "0"), TreeClass("adc1", "1")))
    return [mode, channel]


def test_each_choice_covers_every_leaf_class_with_the_fewest_cases() -> None:
    vectors = classification_vectors(_tree(), strategy="each_choice")

    assert len(vectors) == 4  # mode has four leaf selections: normal, degraded/sensor, degraded/supply, off
    labels = " ".join(v.vector_id for v in vectors)
    for expected in ("mode:normal", "mode:degraded", "reason:sensor", "reason:supply", "mode:off", "channel:adc0", "channel:adc1"):
        assert expected in labels


def test_a_class_that_only_refines_assigns_no_value_of_its_own() -> None:
    vectors = classification_vectors(_tree(), strategy="all_combinations")
    degraded = [v for v in vectors if "mode:degraded" in v.vector_id]

    assert all("mode" not in v.parameters for v in degraded)
    assert {v.parameters["reason"] for v in degraded} == {"10", "11"}


def test_all_combinations_of_a_tree_is_the_product_of_the_leaf_selections() -> None:
    assert len(classification_vectors(_tree(), strategy="all_combinations")) == 4 * 2


def test_tree_cases_are_capped_not_truncated() -> None:
    with pytest.raises(DerivationError) as excinfo:
        classification_vectors(_tree(), strategy="all_combinations", max_vectors=7)
    assert excinfo.value.reason == "too_many_combinations"


def test_invalid_classes_make_invalid_vectors() -> None:
    tree = [ClassificationNode("level", (TreeClass("ok", "5"), TreeClass("negative", "-1", valid=False)))]
    vectors = classification_vectors(tree)
    assert {v.vector_id: v.invalid for v in vectors} == {"ctree.level:negative": True, "ctree.level:ok": False}


def test_conflicting_assignments_to_one_parameter_are_refused() -> None:
    clash = [
        ClassificationNode("p", (TreeClass("a", "1"),)),
        ClassificationNode("p", (TreeClass("b", "2"),)),
    ]
    with pytest.raises(DerivationError) as excinfo:
        classification_vectors(clash)
    assert excinfo.value.reason == "conflicting_assignment"


def test_the_same_assignment_twice_is_not_a_conflict() -> None:
    same = [
        ClassificationNode("p", (TreeClass("a", "1"),)),
        ClassificationNode("p", (TreeClass("b", "1"),)),
    ]
    (vector,) = classification_vectors(same)
    assert vector.parameters == {"p": "1"}


@pytest.mark.parametrize(
    ("tree", "kwargs", "reason"),
    [
        ([], {}, "empty_tree"),
        ([ClassificationNode("p", ())], {}, "empty_classification"),
        (_tree(), {"strategy": "one_at_a_time"}, "unknown_strategy"),
    ],
)
def test_unusable_trees_are_refused(tree: list[ClassificationNode], kwargs: dict[str, str], reason: str) -> None:
    with pytest.raises(DerivationError) as excinfo:
        classification_vectors(tree, **kwargs)
    assert excinfo.value.reason == reason


def test_tree_derivation_is_deterministic_and_sorted() -> None:
    first = classification_vectors(_tree(), strategy="all_combinations")
    assert first == classification_vectors(_tree(), strategy="all_combinations")
    ids = [v.vector_id for v in first]
    assert ids == sorted(ids) and len(ids) == len(set(ids))


# --- vectors become ordinary cases ----------------------------------------------------------


def test_vectors_become_cases_without_an_invented_expected_value() -> None:
    vectors = derive_vectors({"a": boundary_values(IntegerDomain("a", 0, 10))}, strategy="each_choice")

    cases = vectors_to_cases(vectors, unit="src/a.c", function="f", fixed_parameters={"mode": "1"})

    assert [c.case_id for c in cases] == [v.vector_id for v in vectors]
    assert all(c.expected.return_value is None and not c.expected.global_finals for c in cases)
    assert all(c.inputs.parameters["mode"] == "1" for c in cases)
    assert all(not c.stale and (c.unit, c.function) == ("src/a.c", "f") for c in cases)


def test_invalid_values_become_robustness_cases_that_the_range_check_accepts() -> None:
    domain = IntegerDomain("a", 0, 10)
    vectors = derive_vectors({"a": boundary_values(domain, robust=True)}, strategy="each_choice")
    cases = vectors_to_cases(vectors, unit="src/a.c", function="f")

    by_value = {c.inputs.parameters["a"]: c for c in cases}
    assert by_value["-1"].robustness and by_value["11"].robustness
    assert not by_value["5"].robustness
    for case in cases:  # the tool's own range check must not refuse what derivation produced
        ensure_range_checking(case, {"a": ValidRange("0", "10")})


def test_fixed_parameters_may_not_repeat_derived_ones() -> None:
    vectors = derive_vectors({"a": boundary_values(IntegerDomain("a", 0, 10))}, strategy="each_choice")
    with pytest.raises(DerivationError) as excinfo:
        vectors_to_cases(vectors, unit="u", function="f", fixed_parameters={"a": "1"})
    assert excinfo.value.reason == "fixed_overlap"


@pytest.mark.parametrize(("unit", "function"), [("", "f"), ("u", " ")])
def test_cases_need_a_unit_and_a_function(unit: str, function: str) -> None:
    with pytest.raises(DerivationError) as excinfo:
        vectors_to_cases([], unit=unit, function=function)
    assert excinfo.value.reason == "invalid_target"


def test_equivalence_representatives_flow_into_cases() -> None:
    classes = equivalence_classes(IntegerDomain("a", 10, 20))
    choices = {"a": tuple(DerivedValue(c.representative or "", c.name, c.valid) for c in classes)}

    cases = vectors_to_cases(derive_vectors(choices, strategy="each_choice"), unit="u", function="f")

    assert sorted(c.inputs.parameters["a"] for c in cases) == ["15", "21", "9"]
    assert sum(1 for c in cases if c.robustness) == 2


@pytest.mark.parametrize(("low", "high"), [(0, 1), (0, 2), (0, 3), (-3, -1), (5, 5), (0, 4)])
def test_the_nominal_value_always_carries_the_nominal_role_so_small_ranges_derive_one_at_a_time(low: int, high: int) -> None:
    domain = IntegerDomain("p", low, high)

    assert [v.value for v in boundary_values(domain) if v.role == "nominal"] == [str(domain.nominal)]
    other = boundary_values(IntegerDomain("q", 0, 10))
    vectors = derive_vectors({"p": boundary_values(domain), "q": other}, strategy="one_at_a_time")
    assert {v.parameters["p"] for v in vectors} == {v.value for v in boundary_values(domain)}
