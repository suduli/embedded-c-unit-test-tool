# Lane B summary — overnight 2026-11-22

Branch `glm-night/20261122-b`, worktree `wt-night-22b`, branched from local `main`
fc0631c (the queue text named e5184df; main had moved one docs-only commit further —
branched from current main as instructed; baseline gates identical to the stated one:
3558 passed / 6 skipped, ruff, mypy, plan_check, trace_check clean).

## Counts per state

| State | Count | Items |
|---|---|---|
| DONE | 8 | B2, B1, B3, B6, B4, B5, B7, B8 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 (all items landed; open owner follow-ups recorded, see below) | — |

Every item: full gate block green at its commit, one ledger row
(`LANE_B_LEDGER.md`; commit hashes backfilled there). 11 commits, never pushed, no
amend/force/`--no-verify`, no `git add -A`. Two lint-only follow-up commits (1e46988,
1680212) and one battery-structure correction (d3372d1) were made when a chained gate
masked a ruff finding or a collection error at the first commit; each follow-up was
committed only after all five gates were re-run and checked **individually**.

## Commits (in order)

| Item | Commit(s) | One-line |
|---|---|---|
| B2 | 487a112 (+1e46988) | five stable report views (subset run, run comparison + coverage delta, minimized suite, host profile label, thresholds with no_data shown as failure) |
| B1 | 02a67a1 | coverage merge provenance order-independent (data_file = sorted joined list; cwd = sorted-first distinct); counts unchanged; all permutations byte-identical |
| B3 | 7884dca | optional coverage_thresholds project section (exact fraction strings; floats refused; loaded into ectt.cov.MetricThreshold; absent = no-op) |
| B6 | 8200ef9 | gcov reader fixtures for documented real-GCC shapes (templates, inlines in several files, declarations-only, unexecuted blocks, throw branches, v1+v2); NO reader bugs exposed |
| B4 | aaf16b9 | all 15 docs/user pages drafted (DRAFT-marked, surface-checked) + the index/commands/APIs test |
| B5 | 393e747 | SECURITY policy draft at docs/proposals (OWNER-CONTACT-REQUIRED placeholder; not promoted to root) |
| B7 | efb7232 (+1680212, d3372d1) | mutation batteries cov+rep: 11/11 killed, report written |
| B8 | 9cbca1e | seeded property tests: thresholds vs exact-fraction oracle, rep views over seeded run sets |

Tests: 3558 (baseline) → 3627 passed; 6 skipped. ~69 new tests across the 8 items.

## PARTIAL / SKIPPED / SECOND-PASS with reasons

- **No item ended PARTIAL or SKIPPED.** No gate hit 3 failed attempts; no per-item cap
  was reached.
- **SECOND_PASS_B rows:** none were needed this run — no item was blocked, and the one
  review finding this lane had recorded last night (merge data_file order-dependence)
  was this run's B1 item and is now fixed in the product (`02a67a1`), closing the
  20261121 SECOND_PASS_B row it came from.
- Standing recorded limits (carried from previous runs, unchanged): real GCC gcov
  output has **not** been checked (no C compiler on this machine; B6's fixtures are
  key-for-key from the GCC 14.4 documentation); docs/user pages and SECURITY-draft are
  DRAFTS awaiting owner wording (B4/B5 ledger rows say so explicitly).

## Shared-file changes needed

- None forced by the lane. `design/` and the unified plan were never regenerated;
  plan_check/trace_check are byte-identical green (3558→3627 tests, requirements
  untouched at 346/344/191).
- Owner actions suggested (not made), also flagged in the ledger rows:
  - final wording of the 15 `docs/user/` DRAFT pages (B4);
  - review the SECURITY commitments, replace `OWNER-CONTACT-REQUIRED`, and copy
    `docs/proposals/SECURITY-draft.md` to the root `SECURITY.md` (B5);
  - other lanes consume the five stable view names listed in
    `docs/verification/WP-REP-views-analysis.md` — keep those names when touching
    `ectt.rep.views`.

## Final gate output (at 9cbca1e + ledger bookkeeping)

```
pytest -q:     3627 passed, 6 skipped  (0 failed, 0 xfailed)
ruff:          All checks passed!
mypy src:      Success: no issues found in 186 source files
plan_check:    PLAN check passed: 346 requirements; 344 unique primary allocations;
               191 packages (all priorities/phases/categories ok; UNALLOCATED 0)
trace_check:   OK: every in-scope requirement is allocated and the design graph is
               well formed
```

Stop condition: all 8 queue items landed well before the 05:30 local cutoff; no token
counter was available (per queue, the token limit is ignored in that case). Lane B is
complete; nothing was pushed.
