# Lane B summary — overnight 2026-11-21

Branch `glm-night/20261121-b`, worktree `wt-night-21b`, branched from local `main`
26e4330 (the queue text named a690b3f; main had moved one docs-only commit further —
branched from current main as instructed; baseline gates identical to the stated one:
3097 passed / 6 skipped, ruff, mypy, plan_check, trace_check clean).

## Counts per state

| State | Count | Items |
|---|---|---|
| DONE | 20 | B1, B3, WP-COV-01, WP-COV-02, WP-COV-03, WP-COV-04, WP-REP-02, WP-COV-08, WP-COV-09, WP-REP-03, WP-REP-10, WP-REP-07, WP-COV-07, B2, B4, B5, B6, B7, B8, B9 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 (all items landed; open second-pass rows are follow-ups recorded for owners, see below) | — |

Every item: full gate block green at its commit, one commit, one ledger row
(`LANE_B_LEDGER.md`; commit hashes backfilled there). 20 commits, never pushed, no
amend/force/`--no-verify`, no `git add -A`.

## Commits (in order)

| Item | Commit | One-line |
|---|---|---|
| B1 | 55da684 | analysis-model schema 1.5: function extent, per-occurrence constructs, global-variable inventory |
| B3 | 3aed670 | OutputRoot.transaction re-entrant; ana writer's private-state read removed |
| WP-COV-01 | d885acd | ectt.cov: gcov JSON reader (versions 1/2, gzip), statement + branch metrics |
| WP-COV-02 | 1386d4f | coverage merge, per-test attribution, completeness, quarantine (COV-180/220) |
| WP-COV-03 | af00f90 | per-metric coverage thresholds (exact fractions) |
| WP-COV-04 | faf52d3 | function and function-call coverage (functions[], calls[]) |
| WP-REP-02 | 0f29855 | JUnit XML and Cobertura XML renderers over the report model |
| WP-COV-08 | c60c67a | UUT vs harness/stub/framework coverage separation (explicit roles, conservation) |
| WP-COV-09 | 04e441e | coverage-by-analysis justification with source-digest binding (recorded §5.4 criterion) |
| WP-REP-03 | 0345eea | HTML report with annotated source (per-line statuses, justified marks) |
| WP-REP-10 | 2eccf2e | LCOV/Cobertura interchange export + import (statement-level Cobertura) |
| WP-REP-07 | 56ade58 | paginated PDF archival rendering (hand-written PDF 1.4 writer, no new deps) |
| WP-COV-07 | ce4ced6 | bare-metal coverage retrieval over the console dump protocol |
| B2 | d4c6118 | exact requirement range links via the function extent (legacy fallback kept) |
| B4 | 66e39f2 | report renderers show machine-generated/unreviewed marks (narrow atg import) |
| B5 | c86efd7 | published interchange-format reference; mig FormatSpec to 1.5; cmocka OK spelling |
| B6 | 3f6feae | Project.save sharded layout behind an explicit argument; read_shards |
| B7 | 71e2aa0 | ReqIF SPEC-RELATIONS import as associations (lossless round trip) |
| B8 | ac7c81e | mutation batteries core/fs + prj shards + mig parsers: 9/9 killed, report written |
| B9 | 4f7e4b9 | seeded property tests: matrix, ReqIF round trip, coverage merge |

Tests: 3097 (baseline) → 3342 passed; 6 skipped; 0 xfail (the two B1 mig xfails were
resolved for real under B5). ~245 new tests across the 20 items.

## PARTIAL / SKIPPED / SECOND-PASS with reasons

- **No item ended PARTIAL or SKIPPED.** No gate ever hit 3 failed attempts; no per-item
  cap was reached.
- **SECOND_PASS_B rows** (`docs/glm-night/overnight-20261121/SECOND_PASS_B.md`):
  1. *B1 row — RESOLVED during the run.* The mig FormatSpec `analysis-model` version
     pointer (1.4 → 1.5) was outside B1's allowed paths, so B1 recorded it here and
     marked the two affected mig checks `xfail(strict=True)` per queue rule 5. Item B5's
     allowed paths include `src/ectt/mig/`, so B5 moved the spec to 1.5, pointed it at
     `analysis-model-1.5.schema.json`, removed both markers, and both checks now pass
     for real. No human action left for this row.
  2. *B9 row — OPEN, cov owner.* The coverage merge takes its representative `data_file`
     from the first admitted run in **input order** (`src/ectt/cov/merge.py`,
     `_merge_documents`), so merging the same run set in a different order yields a
     different aggregate provenance field (counts unaffected). A conservative fix is a
     canonical-order representative (e.g. sorted by (gcc_version, data_file)) so the
     merge is a pure function of the run set. Found by the B9 seeded order-independence
     property; `src/ectt/cov/` was outside B9's allowed paths, so the merge was left
     untouched and the fixture models one build's runs (shared data_file).
  3. Standing recorded limits (not new): real GCC gcov output has **not** been checked
     (no C compiler on this machine, ADR-004 fixtures approach) — WP-COV-01/02/04/07
     fixtures were taken key-for-key from the GCC 14.4 documentation (verified against
     gcc.gnu.org, not memory). LCOV per-line export from the aggregate-only report model
     (WP-REP-02) — satisfied by Cobertura per TOOL-REP-020's "and/or"; per-line data
     lands with WP-REP-03's annotated-source work.

## Shared-file changes needed

- None forced by the lane. `design/` and the unified plan were never regenerated
  (queue instruction); plan_check/trace_check are byte-identical green (346 reqs / 344
  allocations / 191 packages). The mig FormatSpec change (B5) and the `tests/mig`
  xfail removal are committed within this lane's allowed paths and are the only files
  outside `src/ectt/{ana,cov,rep,trc,prj,core}/`+`tests/` besides lane docs.
- Owner edits suggested (not made): reconcile the derived acceptance criteria in
  `docs/verification/WP-COV-0{1,2,3,4,7,8,9}-analysis.md` and
  `WP-REP-0{2,3,7}-analysis.md` / `WP-REP-10-analysis.md` into PLAN-001 §5.4
  (each analysis doc flags this); the open B9 second-pass row above.

## Final gate output (at 4f7e4b9 + ledger bookkeeping)

```
pytest -q:     3342 passed, 6 skipped  (0 failed, 0 xfailed)
ruff:          All checks passed!
mypy src:      Success: no issues found in 177 source files
plan_check:    PLAN check passed: 346 requirements; 344 unique primary allocations;
               191 packages; 642 person-weeks; dependency lower bound 52 weeks
               (all priorities/phases/categories ok; UNALLOCATED 0)
trace_check:   OK: every in-scope requirement is allocated and the design graph is
               well formed
```

Stop condition: all 20 queue items landed before the 05:30 local cutoff; no token
counter was available (per queue, the token limit is ignored in that case). Lane B is
complete; nothing was pushed.
