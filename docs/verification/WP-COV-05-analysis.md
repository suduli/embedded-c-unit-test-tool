# WP-COV-05 / WP-COV-06 — Masking MC/DC measurement (core part)

TOOL-COV-050/060/070/080/190; written 2026-11-28. Module `ectt.cov.mcdc`.

## What is delivered

- Per decision, which conditions were not seen true / false, with totals.
- Form (`masking`), mechanism (`gcc -fcondition-coverage`) and compiler
  version on every result.
- Decisions without a record are `unmeasured` with a reason. Over the limit
  is claimed only against the probed maximum passed in.

## Evidence

Real GCC 14.4.0 output in `tests/cov/fixtures/gcc14/`; expected condition
status computed by hand from the calls in `mcdc.c`.

## Fixed on the way

`merge_run_coverage` subtracted a condition unseen both true and false only
once, so merged runs reported more coverage than happened (an uncalled
`a || b` merged as 2 of 4 covered).

## Observed

GCC records nothing for `x == 1 ? 0 : 1` (main in `limit65.c`); such a
decision reads `no_condition_record`.

## Not done (WP-COV-05/06 are NOT complete)

- COV-210 known-answer corpus: only the cases above; no nested witness pairs,
  no written masking-versus-unique-cause divergent case.
- No MC/DC thresholds, project setting, report rendering, user page or CLI.
- No build step applies the MC/DC flags yet.
- Condition-index order matching source order is observed, not documented by GCC.
- GCC reports a condition under an odd number of `!` inverted; undone from the
  analyzer's `negated` flag. A ternary with a negated condition reports unknown
  direction, because GCC may swap its arms. Verified at -O0 only
  (`tests/cov/test_mcdc_polarity.py`).
