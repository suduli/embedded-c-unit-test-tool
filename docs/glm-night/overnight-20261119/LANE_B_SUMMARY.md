# Lane B summary — overnight 2026-11-19

Branch `glm-night/20261119-b` (worktree `wt-night-b`, off `glm-night/20261119-plan` 46fa7e2;
baseline local main 353b9b4: 970 passed, 4 skipped, gates clean). Run: 2026-11-19 ~21:05 → ~22:45.

## Counts per state

| state | count | items |
|---|---|---|
| DONE | 20 / 20 | WP-CORE-03 e7d6994, WP-CORE-02 a73a129, WP-ANA-07 1d1e089, WP-ANA-06 0d10f95 (PAR-090 scope), TASK-107 613588f, WP-REP-01 babdb69, WP-REP-11 e702d76, WP-REP-06 f21c2fc, WP-REP-08 abb69df, WP-PLG-03 533ddb3, WP-CORE-04 375ea56 (in-scope), WP-PRJ-05 842b30f, WP-REP-09 eb05bc2, WP-CLI-05 ea0038b, WP-TRC-01 5db85e7, WP-TRC-02 f59c481, TASK-108 a583059, WP-REP-12 c92ee14, WP-MIG-01 9748b96, WP-TRC-03 e1257fd |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 | — (all items landed; 17 SECOND_PASS rows record human follow-ups, none blocked code) |

No item hit its hard cap or 3 failed gate attempts. No test was deleted or weakened; two
WP-REP-06 adjustments to lane-B's own WP-REP-01 tests are contract evolutions, documented in
the analysis docs (creation-timestamp exclusion narrowed to `generated_at`; dump version
pinned to the current format constant). Cross-lane retries: not needed — no item was
SKIPPED (dep).

## Cross-lane protocol execution

- Before WP-REP-01: checked `../wt-night-a` LANE_A_LEDGER.md — WP-EXH-01 DONE (98fe972);
  merged `glm-night/20261119-a` (c5d1c9c), post-merge gate green before implementing.
- Before WP-REP-12: WP-TCM-06 DONE (2288a0d, plus WP-EXH-02 0963a0d and lane A's summary +
  hygiene commits, tip 69ed8e0); merged again, post-merge gate green (1339 passed at merge,
  1351 at commit).

## FINAL GATE OUTPUT (last full run, after WP-TRC-03 e1257fd)

```
pytest -q -p no:cacheprovider  →  1379 passed, 5 skipped, 0 warnings in ~22s
ruff check src tests           →  All checks passed!
mypy src                       →  Success: no issues found in 142 source files
plan_check.py                  →  PLAN check passed: 346 requirements; 344 unique primary
                                  allocations; 191 packages; 642 person-weeks
trace_check.py                 →  OK: every in-scope requirement is allocated and the
                                  design graph is well formed
```

Net: +409 passing tests over the baseline (970 → 1379), +1 skip (the Linux-CI evidence hook
`test_linux_x86_64_baseline`). Budget: cumulative estimate ~1410k tokens (< 1450k stop rule);
clock ~22:45 (< 05:30). All work is on `glm-night/20261119-b`, unpushed, one commit per item
plus two lane-A merges and this summary.

## SECOND_PASS rows (17) — every PARTIAL/SKIPPED/SECOND-PASS with reason

Full table in `SECOND_PASS_B.md`. Grouped, with reasons:

- **Owner decisions / register territory (no code allowed):** PLAN-001 §5.4 CMP-CORE and
  CMP-TRC-03-area acceptance-criteria reconciliation; ana multi-file analysis driver shape;
  PAR-080 static-exposure mechanism (ADR-003 is an open owner decision); S1-embedding option
  for macro-resolution records; owner review of the WP-REP-01 acceptance evidence.
- **Outside an item's allowed paths (queued with the owning item):** prj/ana transaction
  routing (SDD-003 §3); rep 1.1 reader `execution`-optional fix + public digest-bound model
  factory (merged reports currently refuse to load — fail-safe, exact change queued);
  `CATEGORY_EXIT_CODES` additions for the new `report`/`traceability`/`migration` categories
  (total-by-fallback already covers them); provenance blocks for exh/tcm/prj artifacts.
- **Hardware / release engineering:** macOS runner evidence for NFR-020; Linux CI lane
  wiring (`.github/` outside allowed paths; the in-repo hook is
  `test_linux_x86_64_baseline`); release build sets `ECTT_BUILD_ID`.
- **Scope instructions honoured:** multi-file analysis driver not added (WP-ANA-07
  instruction); TASK-108's ana-schema-reader fuzz stays with the ana queue (queue paths).

## Shared-file changes needed (for the morning merge owner)

1. `src/ectt/rep/model.py` — reader: make `execution` optional in 1.1 (provenance stays
   required) and expose a public digest-bound model factory; until then merged reports dump
   but refuse to load (`missing_field`), fail-safe.
2. `src/ectt/cli/exit_codes.py` — add `"report"`, `"traceability"`, `"migration"` to
   `CATEGORY_EXIT_CODES` (all → EXIT_TOOL_ERROR; the total-by-fallback path already covers
   them, so nothing is broken meanwhile).
3. PLAN-001 §5.4 — record the derived acceptance criteria for CMP-CORE and the packages that
   had none (see each analysis doc's RECON section); reviewed evidence for WP-REP-01.
4. `.github/` CI — a Linux lane running the gate block (D-03: "Linux CI kept green").
5. Release engineering — set `ECTT_BUILD_ID` so provenance stops reporting `unset`.

## Assumptions taken (conservative readings, per the unattended contract)

- D-03 implemented exactly as quoted: `VALIDATED_PLATFORMS = {windows, linux}`; macOS
  recognised, reported unvalidated, SECOND_PASS row for runner evidence.
- The WP-CORE-02 "existing long-running operation" routed through `OutputRoot.transaction`
  is the multi-write fixture pipeline (the only such operation inside that item's allowed
  paths); product-operation routing queued per SECOND_PASS.
- WP-CORE-04's embedding closed for the report artifact (its allowed paths) and documented
  per-artifact for the rest; producers outside the paths are skipped and listed, per the
  item's own instruction.
- TASK-108's "schema reader" covered as the prj schema-version reader (queue allowed paths
  exclude tests/ana); noted in the ledger.
- cmocka FAILED records normalise to `error` (the stream carries no expected/actual);
  detail extraction queued.

## Not done (explicitly out of scope tonight)

Nothing from the queue was dropped. Items NOT-STARTED by lane A (WP-TCM-07, WP-GEN-07) are
lane A's ledger entries, not lane B's.
