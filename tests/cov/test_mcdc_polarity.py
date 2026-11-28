# implements: TOOL-COV-070
"""Which way round a condition was seen, checked against the values really passed.

Every function in the two fixtures is called exactly once, so each condition had
one real value. A reported direction must be that value, or None (unknown).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.ana.frontend import parse
from ectt.ana.interface import extract
from ectt.cov.gcov import read_gcov_document
from ectt.cov.mcdc import measure_mcdc

FIXTURES = Path(__file__).parent / "fixtures" / "gcc14"

T, F = True, False
# The value each condition AS WRITTEN really had, in source order.
REAL = {
    "polarity1": {
        "n1": [F], "n2": [T], "n3": [F], "and_not": [T, F], "or_not": [F, T], "not_and": [T, T],
        "not_or": [F, F], "not_and_not": [F, F], "value_not_and": [T, T], "value_and_not": [T, F],
        "value_arg_not": [F, T], "eq0": [T, T], "tern_not": [F], "nested": [T, F, T],
        "cmp_not": [F, T], "ptr_not": [F, F],
    },
    "polarity2": {
        "if_else_not": [T], "if_empty_then": [T], "while_not": [T], "do_not": [T, T], "for_not": [T],
        "tern_const": [T], "tern_call": [T], "tern_and": [T, T], "tern_and_not": [T, T], "tern_plain": [T],
        "if_eq_zero": [F], "if_ne_zero": [T], "not_eq": [F], "cast_not": [F], "not_cast": [T],
        "comma_not": [F], "not_not_and": [T, T],
    },
}


@pytest.mark.parametrize("name", sorted(REAL))
def test_a_reported_direction_is_the_real_value_or_unknown(name: str) -> None:
    unit = extract(parse(FIXTURES / f"{name}.c", args=["-std=gnu11"]), working_directory=FIXTURES)
    document = read_gcov_document((FIXTURES / f"{name}.gcov.json").read_bytes())
    result = measure_mcdc(document, f"{name}.c", decisions=unit.decisions)
    checked = 0
    for decision in result.decisions:
        values = REAL[name].get(decision.function or "")
        if values is None:
            continue
        assert decision.expression is not None, decision.function
        for condition in decision.conditions:
            seen = {True: condition.seen_true, False: condition.seen_false}
            if condition.seen_true is None:
                assert decision.function and decision.function.startswith("tern")
                continue
            other = not values[condition.index]
            assert not seen[other], (decision.function, condition.expression)
            checked += seen[values[condition.index]] or 0
    assert checked >= 14  # the rest are unknown or were masked
