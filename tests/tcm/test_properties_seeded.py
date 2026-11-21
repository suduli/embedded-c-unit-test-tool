# implements: TOOL-TCD-080, TOOL-TCD-070, TOOL-TCD-100
"""Seeded property-style tests for ectt.tcm (TEST-PROP-TCM, tests only).

Inputs come from ``random.Random(seed)`` with fixed seeds (the seed is the test id), so a
failure is reproducible with one number and nothing depends on the clock or hash order.
Each property is stated as an invariant and checked against an independently written
oracle where one is needed.

* CSV interchange (TOOL-TCD-100): export then import is lossless for content the format
  can express; content it cannot express is reported as a loss, never dropped; output is
  deterministic and independent of case order; a tampered row is flagged.
* Range expansion (TOOL-TCD-070): length, bounds, step and ordering of an integer range;
  the expanded case set is the cartesian product with stable, unique ids.
* Suite selection (TOOL-TCD-080): the selection expression is an OR of dimensions with an
  independent set-logic oracle; the partition is complete, disjoint and order-preserving.
"""

from __future__ import annotations

import csv
import io
import json
import random
from itertools import pairwise, product
from typing import Any

import pytest

from ectt.tcm import datacases as dd
from ectt.tcm.errors import InterchangeError, RangeExpansionError
from ectt.tcm.interchange import export_cases, import_cases
from ectt.tcm.ranged import RangedInput, expand_case, expand_integer_range
from ectt.tcm.selection import Selection, partition_cases

SEEDS = range(40)

_WORDS = ["adc", "scale", "zero", "max", "min", "gain", "raw", "mode", "tick", "read", "frame", "len"]
_SAFE_VALUES = ["0", "1", "-1", "42", "0x10", "'a'", "3.5f", "(char *)0", "NULL", "1 << 4", "a,b", 'say "hi"', "two words", "line1\nline2", "tab\there", "ünïcode", ""]
_LIST_SAFE = ["TOOL-A-1", "REQ_7", "smoke", "full", "nightly", "x y"]


def _ident(rng: random.Random, n: int = 2) -> str:
    return "_".join(rng.choice(_WORDS) for _ in range(n))


def _mapping(rng: random.Random, pool: list[str]) -> dict[str, str]:
    return {f"{_ident(rng, 1)}{i}": rng.choice(pool) for i in range(rng.randint(0, 3))}


def _random_case(rng: random.Random, index: int, *, allow_semicolon: bool = False) -> dd.DataDrivenTestCase:
    pool = _LIST_SAFE + (["has;semi"] if allow_semicolon else [])
    stubs = tuple(
        dd.StubSpec(
            name=f"stub{j}",
            mode=rng.choice(["fixed", "sequence", "callback"]),
            returns=tuple(rng.choice(_SAFE_VALUES[:8]) for _ in range(rng.randint(0, 3))),
            expect_calls=rng.choice([None, "0", "2", "10"]),
            out_parameters=_mapping(rng, _SAFE_VALUES[:8]),
        )
        for j in range(rng.randint(0, 2))
    )
    case = dd.DataDrivenTestCase(
        case_id=f"case.{index}.{_ident(rng)}",
        unit=f"src/{_ident(rng, 1)}.c",
        function=_ident(rng),
        inputs=dd.TestCaseInputs(parameters=_mapping(rng, _SAFE_VALUES), global_inits=_mapping(rng, _SAFE_VALUES)),
        expected=dd.TestCaseExpected(
            return_value=rng.choice([None, *_SAFE_VALUES[:8]]),
            global_finals=_mapping(rng, _SAFE_VALUES),
            out_parameters=_mapping(rng, _SAFE_VALUES),
        ),
        stubs=stubs,
        origin=dd.TestCaseOrigin(author=rng.choice(["human", "atg", "ai"])),
        requirements=tuple(rng.sample(pool, rng.randint(0, 3))),
        suites=tuple(rng.sample(pool, rng.randint(0, 2))),
        robustness=rng.random() < 0.3,
    )
    return dd.refresh_digest(case)


def _cases(rng: random.Random, **kw: Any) -> list[dd.DataDrivenTestCase]:
    return [_random_case(rng, i, **kw) for i in range(rng.randint(1, 8))]


# --- CSV interchange ----------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_export_then_import_is_lossless_for_expressible_content(seed: int) -> None:
    cases = _cases(random.Random(seed))

    exported = export_cases(cases)
    imported = import_cases(exported.text)

    assert exported.losses == ()
    assert sorted(imported.cases, key=lambda c: c.case_id) == sorted(cases, key=lambda c: c.case_id)
    assert imported.digest_mismatches == ()


@pytest.mark.parametrize("seed", SEEDS)
def test_export_is_deterministic_and_independent_of_case_order(seed: int) -> None:
    rng = random.Random(seed)
    cases = _cases(rng)
    shuffled = list(cases)
    rng.shuffle(shuffled)

    assert export_cases(cases).text == export_cases(shuffled).text == export_cases(cases).text


@pytest.mark.parametrize("seed", SEEDS)
def test_export_import_export_is_a_fixed_point(seed: int) -> None:
    first = export_cases(_cases(random.Random(seed))).text
    assert export_cases(import_cases(first).cases).text == first


@pytest.mark.parametrize("seed", SEEDS)
def test_content_the_format_cannot_express_is_reported_not_dropped(seed: int) -> None:
    rng = random.Random(seed)
    cases = _cases(rng)
    carrier = rng.choice(range(len(cases)))
    victim = cases[carrier]
    risky = dd.refresh_digest(dd.DataDrivenTestCase(
        victim.case_id, victim.unit, victim.function, victim.inputs, victim.expected, victim.stubs,
        origin=victim.origin, requirements=("has;semi", *victim.requirements), suites=victim.suites,
    ))
    cases[carrier] = risky

    exported = export_cases(cases)

    assert exported.losses, "a ';' inside a list value must be reported as a loss"
    assert any(victim.case_id in loss for loss in exported.losses)
    clean = [c for i, c in enumerate(cases) if i != carrier]
    others = {c.case_id: c for c in import_cases(exported.text).cases if c.case_id != victim.case_id}
    assert all(others[c.case_id] == c for c in clean)  # the loss is confined to the case it names


@pytest.mark.parametrize("seed", SEEDS)
def test_a_value_edited_in_the_csv_is_flagged_by_its_digest(seed: int) -> None:
    rng = random.Random(seed)
    cases = [replace_param(c, "tamper_me", "1") for c in _cases(rng)]
    cases = [dd.refresh_digest(c) for c in cases]
    target = rng.choice(cases)
    rows = list(csv.reader(io.StringIO(export_cases(cases).text, newline="")))
    header = rows[0]
    for row in rows[1:]:
        if row[header.index("id")] == target.case_id:
            parameters = json.loads(row[header.index("input_parameters")])
            parameters["tamper_me"] = "2"
            row[header.index("input_parameters")] = json.dumps(parameters, sort_keys=True)
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)

    imported = import_cases(out.getvalue())

    assert imported.digest_mismatches == (target.case_id,)
    assert len(imported.cases) == len(cases)  # the edited row is reported, not dropped


def replace_param(case: dd.DataDrivenTestCase, name: str, value: str) -> dd.DataDrivenTestCase:
    from dataclasses import replace

    return replace(case, inputs=replace(case.inputs, parameters={**case.inputs.parameters, name: value}))


@pytest.mark.parametrize("seed", SEEDS[:10])
def test_a_duplicate_case_id_is_always_refused(seed: int) -> None:
    cases = _cases(random.Random(seed))
    with pytest.raises(InterchangeError):
        export_cases([*cases, cases[0]])


# --- range expansion ------------------------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_an_integer_range_has_the_right_length_bounds_step_and_order(seed: int) -> None:
    rng = random.Random(seed)
    lo = rng.randint(-50, 50)
    hi = lo + rng.randint(0, 120)
    step = rng.randint(1, 15)

    values = [int(v) for v in expand_integer_range(str(lo), str(hi), str(step))]

    assert values[0] == lo
    assert len(values) == (hi - lo) // step + 1
    assert all(b - a == step for a, b in pairwise(values))
    assert all(lo <= v <= hi for v in values)
    assert (hi in values) == ((hi - lo) % step == 0)
    assert values == [lo + i * step for i in range(len(values))]


@pytest.mark.parametrize("seed", SEEDS)
def test_a_range_of_step_one_is_every_integer(seed: int) -> None:
    rng = random.Random(seed)
    lo = rng.randint(-20, 20)
    hi = lo + rng.randint(0, 30)
    assert expand_integer_range(str(lo), str(hi), "1") == tuple(str(v) for v in range(lo, hi + 1))


@pytest.mark.parametrize("seed", SEEDS)
def test_invalid_ranges_are_always_refused(seed: int) -> None:
    rng = random.Random(seed)
    lo = rng.randint(-10, 10)
    bad = rng.choice(
        [
            (str(lo + rng.randint(1, 9)), str(lo), "1"),  # lower above upper
            (str(lo), str(lo + 5), str(-rng.randint(0, 5))),  # step below one
            (str(lo), str(lo + 5), "0"),
            (str(lo), "x" * rng.randint(1, 3), "1"),  # not integer text
            (f"0{abs(lo) + 1}", "99", "1"),  # leading zero
            (str(lo), f"{lo}.5", "1"),
            ("", "5", "1"),
        ]
    )
    with pytest.raises(RangeExpansionError):
        expand_integer_range(*bad)


@pytest.mark.parametrize("seed", SEEDS)
def test_expanding_a_case_gives_the_cartesian_product_with_stable_unique_ids(seed: int) -> None:
    rng = random.Random(seed)
    base = _random_case(rng, 0)
    axes = [
        RangedInput(f"p{i}", tuple(str(v) for v in range(rng.randint(0, 3), rng.randint(4, 7))))
        for i in range(rng.randint(1, 3))
    ]

    expanded = expand_case(base, axes)
    again = expand_case(base, axes)

    expected_count = 1
    for axis in axes:
        expected_count *= len(axis.values)
    assert len(expanded) == expected_count
    assert [c.case_id for c in expanded] == [c.case_id for c in again]  # stable under re-expansion
    assert len({c.case_id for c in expanded}) == len(expanded)
    assert all(c.case_id.startswith(base.case_id + ".r.") for c in expanded)
    combos = [tuple(c.inputs.parameters[a.parameter] for a in axes) for c in expanded]
    assert combos == list(product(*[a.values for a in axes]))  # declared order, last axis fastest
    assert all(not c.stale and c.expected == base.expected and c.stubs == base.stubs for c in expanded)


@pytest.mark.parametrize("seed", SEEDS[:15])
def test_an_axis_overrides_only_its_own_parameter(seed: int) -> None:
    rng = random.Random(seed)
    base = replace_param(replace_param(_random_case(rng, 0), "keep", "k"), "vary", "old")
    expanded = expand_case(base, [RangedInput("vary", ("1", "2", "3"))])

    assert [c.inputs.parameters["vary"] for c in expanded] == ["1", "2", "3"]
    assert all(c.inputs.parameters["keep"] == "k" for c in expanded)


# --- suite selection ----------------------------------------------------------------------------------


def _selection_pool(rng: random.Random) -> list[dd.DataDrivenTestCase]:
    suites = ["smoke", "full", "nightly", "slow"]
    units = ["a.c", "b.c", "c.c"]
    functions = ["f", "g", "h", "k"]
    cases = []
    for i in range(rng.randint(5, 25)):
        case = dd.DataDrivenTestCase(
            f"t{i}", rng.choice(units), rng.choice(functions), dd.TestCaseInputs(), dd.TestCaseExpected(), (),
            suites=tuple(rng.sample(suites, rng.randint(0, 3))),
        )
        cases.append(dd.refresh_digest(case))
    return cases


def _random_selection(rng: random.Random, cases: list[dd.DataDrivenTestCase]) -> Selection:
    def pick(pool: list[str]) -> tuple[str, ...]:
        return tuple(rng.sample(pool, rng.randint(0, min(2, len(pool)))))

    return Selection(
        suites=pick(["smoke", "full", "nightly", "slow"]),
        units=pick(["a.c", "b.c", "c.c"]),
        functions=pick(["f", "g", "h", "k"]),
        test_ids=pick([c.case_id for c in cases]),
    )


def _oracle(selection: Selection, case: dd.DataDrivenTestCase) -> bool:
    criteria = [
        (selection.suites, bool(set(case.suites) & set(selection.suites))),
        (selection.units, case.unit in selection.units),
        (selection.functions, case.function in selection.functions),
        (selection.test_ids, case.case_id in selection.test_ids),
    ]
    active = [hit for values, hit in criteria if values]
    return True if not active else any(active)


@pytest.mark.parametrize("seed", SEEDS)
def test_selection_equals_an_independent_or_of_dimensions_oracle(seed: int) -> None:
    rng = random.Random(seed)
    cases = _selection_pool(rng)
    selection = _random_selection(rng, cases)

    selected, excluded = partition_cases(cases, selection)

    assert [c.case_id for c in selected] == [c.case_id for c in cases if _oracle(selection, c)]
    assert [c.case_id for c in excluded] == [c.case_id for c in cases if not _oracle(selection, c)]


@pytest.mark.parametrize("seed", SEEDS)
def test_the_partition_is_complete_disjoint_and_order_preserving(seed: int) -> None:
    rng = random.Random(seed)
    cases = _selection_pool(rng)
    selected, excluded = partition_cases(cases, _random_selection(rng, cases))

    ids = [c.case_id for c in cases]
    assert sorted(c.case_id for c in selected + excluded) == sorted(ids)
    assert not {c.case_id for c in selected} & {c.case_id for c in excluded}
    for part in (selected, excluded):
        positions = [ids.index(c.case_id) for c in part]
        assert positions == sorted(positions)


@pytest.mark.parametrize("seed", SEEDS)
def test_an_empty_selection_selects_everything_never_nothing(seed: int) -> None:
    cases = _selection_pool(random.Random(seed))
    selected, excluded = partition_cases(cases, Selection())
    assert selected == tuple(cases) and excluded == ()


@pytest.mark.parametrize("seed", SEEDS)
def test_adding_values_to_a_dimension_never_removes_a_selected_case(seed: int) -> None:
    rng = random.Random(seed)
    cases = _selection_pool(rng)
    smaller = Selection(units=("a.c",), test_ids=(cases[0].case_id,))
    larger = Selection(units=("a.c", "b.c"), test_ids=(cases[0].case_id, cases[-1].case_id))

    small_ids = {c.case_id for c in partition_cases(cases, smaller)[0]}
    large_ids = {c.case_id for c in partition_cases(cases, larger)[0]}

    assert small_ids <= large_ids


@pytest.mark.parametrize("seed", SEEDS)
def test_selecting_by_test_ids_is_a_union(seed: int) -> None:
    rng = random.Random(seed)
    cases = _selection_pool(rng)
    ids = [c.case_id for c in cases]
    a = tuple(rng.sample(ids, rng.randint(1, len(ids))))
    b = tuple(rng.sample(ids, rng.randint(1, len(ids))))

    def chosen(selection: Selection) -> set[str]:
        return {c.case_id for c in partition_cases(cases, selection)[0]}

    assert chosen(Selection(test_ids=a)) | chosen(Selection(test_ids=b)) == chosen(Selection(test_ids=a + b)) == set(a) | set(b)
