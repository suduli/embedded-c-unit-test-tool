# WP-ANA-08 — Decision and condition inventory (schema 1.6)

TOOL-PAR-150, written 2026-11-28.

## What is a decision

The controlling expression of `if`, `while`, `do`, `for` and `?:`, and any
other outermost `&&` / `||` expression. Conditions are the leaves after
removing `&&`, `||`, `!`, parentheses and implicit casts. Nested decisions
(inside a call argument or a cast) are separate records.

## Observed GCC 14.4.0 behaviour (fixtures in `tests/cov/fixtures/gcc14/`)

- Single-condition controlling expressions get a record; `switch`, plain
  comparisons assigned to a variable and `sizeof` operands do not.
- Constant operands are dropped (`a && 1` records one condition; `if (0)`
  records nothing). The model keeps them and marks them `constant`.
- Record line: `if` keyword; loop condition; `?` of a ternary; top operator
  of a value expression. `while` line placement is checked for one-line
  conditions only.

## Evidence

`tests/ana/test_decisions.py`: function, line and condition count agree with
GCC for every record in `mcdc.c` and `shapes.c` (24), and for 11 of 12 in
`lines.c`.

## Limits

- GNU `a ?: b` is not extracted; the unit is marked incomplete and the
  inventory `partial`.
- A `for` header produced by a macro cannot be split; same handling.
- Condition ORDER inside a decision is source order. It matches GCC on the
  cases checked; GCC does not publish it as a guarantee.
- Only functions in the unit's main file are walked.
