# Mutation battery report — cov and rep (B7, overnight 2026-11-22)

Tests only; no `src/` edits (queue rule). Each mutant is a hand-written copy of one
critical contract with a single seeded fault, executed in isolation (the
repo-established mutation-battery pattern, TASK-107). The real implementation is the
oracle: a mutant is killed when its outcome differs from the real implementation on
the same probe — a named refusal counts as an outcome.

## Kill rates

| Module | Battery | Mutants | Killed | Survivors | Rate |
|---|---|---|---|---|---|
| `src/ectt/cov` (reader gates, merge rules, threshold range) | `tests/cov/test_mutation_strength.py` | 6 | 6 | 0 | 100% |
| `src/ectt/rep` (rate policy, JUnit counts, view semantics) | `tests/rep/test_mutation_strength.py` | 5 | 5 | 0 | 100% |
| **Total (B7 additions)** | | **11** | **11** | **0** | **100%** |

Pre-existing batteries (unchanged, still passing): `tests/core/test_mutation_strength.py`
(determinism contracts), `tests/core/test_mutation_strength_fs.py` + `tests/prj/…` +
`tests/mig/…` (20261121 lane B additions, reported in
`overnight-20261121/mutation-core-prj-mig.md`). This report covers the B7 additions.

## Mutants and the case that kills each

### cov (tests/cov/test_mutation_strength.py)

| Mutant | Seeded fault | Killed by |
|---|---|---|
| cov-m1-condition-sanity-dropped | the `covered <= count` reader gate removed | a condition with covered=9 over count=4: real refuses (`covered_above_count`), mutant loads it |
| cov-m2-duplicate-line-dropped | the duplicate-line-number reader gate removed | a document recording line 5 twice: real refuses (`duplicate_line`), mutant counts two lines |
| cov-m3-unknown-version-accepted | any numeric `format_version` is interpreted | version `"3"`: real refuses (`unknown_format_version`), mutant "loads" it |
| cov-m4-quarantine-dropped | the error/timeout quarantine removed | a complete run with outcome `error`: real excludes it from the aggregate (`excluded=1`), mutant merges it (`excluded=0`) |
| cov-m6-count-max-not-sum | merged counts take max instead of sum | counts 3+4: real sums to 7, mutant yields 4 |
| cov-m7-threshold-range-dropped | the threshold 0..1 range check removed | minimum 3/2: real refuses (`minimum_out_of_range`), mutant accepts |

cov-m5 was reserved for the condition-presence contract and is pinned as a named-
contract test instead: a mismatch must be the named refusal
`condition_presence_mismatch`, not an uncontrolled `ValueError` from an unguarded
zip — the real implementation's named error is the contract the battery protects.

### rep (tests/rep/test_mutation_strength.py)

| Mutant | Seeded fault | Killed by |
|---|---|---|
| rep-m7-rate-zero-total-fabricates | a zero-total Cobertura rate renders "1" | `cobertura_rate(0, 0)` must be "0" — no fabricated 100% |
| rep-m8-rate-rounds-up | the rate rounds up instead of half-even | `cobertura_rate(1, 3)` must be "0.333333" (the sixth decimal of 1/3 rounds down half-even) |
| rep-m9-junit-tests-count-drops-not-run | the JUnit `tests` attribute skips not_run | a run with 1 pass + 1 not_run must report `tests="2"` |
| rep-m10-no-data-displayed-pass | the view maps `no_data` to displayed "pass" | the threshold view must display `no_data` as `fail` (a broken coverage run never presents as a pass) |
| rep-m11-stale-minimization-accepted | the preserved-union refusal removed | a minimization whose kept union lost constructs must be refused (`stale_minimization`), never presented |

## Survivors and follow-ups

None — all eleven mutants were killed by the shipped case vectors, so no additional
tests were required. The kill vectors above are exactly the shipped behavioural
contracts, which the batteries now pin as regression-sensitive.
