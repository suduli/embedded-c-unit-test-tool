# Lane A summary — overnight 2026-11-19

Branch: `glm-night/20261119-a` (cut from `glm-night/20261119-plan` at 46fa7e2; branch point main 353b9b4).
Baseline verified before item 1: 970 passed, 4 skipped; ruff, mypy, plan_check, trace_check all clean.

## Counts per state

| State | Count | Items |
|---|---|---|
| DONE | 9 | N00, WP-TCM-02, WP-EXH-01, WP-EXH-02, WP-TCM-03, WP-TCM-04, WP-EXH-03, WP-TCM-05, WP-TCM-06 |
| NOT-STARTED (budget) | 4 | WP-CBT-01, WP-TCM-07, WP-GEN-07, WP-ATG-01 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 (no item was blocked; 16 second-pass rows recorded along the way) | — |

Cumulative estimate: **1,375k of the 1,450k stop line**. The stop rule fired
before WP-CBT-01: 1,375k + 130k > 1,450k. Note: actual token consumption ran
well below the queue's estimates (calibrated for the GLM harness), so the
owner may requeue the four remaining items immediately — WP-CBT-01,
WP-TCM-07 and WP-ATG-01 have their dependencies met tonight; WP-GEN-07 needs
WP-GEN-06's trunk state confirmed.

## Commits (in order)

| Commit | Item |
|---|---|
| 15719e4 | N00 — D-02 identity model recorded in SDD-003 §6/§7 + SDD-002 S2 §5.1 |
| ffacfce | WP-TCM-02 — data-driven case model, restricted-YAML `.tests`, digest binding |
| 98fe972 | WP-EXH-01 — run-attempt lifecycle, binding check, normalized result records |
| 0963a0d | WP-EXH-02 — crash isolation, distinct timeout, exit-code contract |
| 845500b | WP-TCM-03 — type-directed expected-value comparison engine |
| 23a3a2f | WP-TCM-04 — suites, selection expression, order planning, independence check |
| af0fcee | WP-EXH-03 — parallel execution with per-worker output directories |
| b63a54f | WP-TCM-05 — ranged input expansion, robustness marking + range-check gate |
| 2288a0d | WP-TCM-06 — CSV-class interchange with loss reporting and byte-identical round trip |

Never pushed; no PR or board writes; no decisions taken (D-02 was applied
verbatim as answered; D-01/D-03/D-04, ADR-003/004/005/007, SRS-Q2/Q9 and
PR #4 untouched).

## Every PARTIAL / SKIPPED / SECOND-PASS with reason

No item ended PARTIAL or SKIPPED. The 16 SECOND-PASS rows in
`SECOND_PASS_A.md` are all *document-side* needs that the lane was forbidden
to edit (PLAN-001 §5.4 acceptance criteria for five work packages; T-14's
PLAN/SRS wording; SRS §27 q6 closure; CMP-GEN harness obligations: RESULT/
FAILURE protocol emission, comparison codegen, setup-hook reset, build-time
range expansion; CMP-COV per-worker coverage merge; SDD-002 crash-diagnostics
channel question; requeue decision for the four budget-stopped items).

## Shared-file changes needed

None. Lane A touched only its own packages (`src/ectt/tcm/`, `src/ectt/exh/`
+ tests), its own verification docs (`docs/verification/WP-TCM-0{2..6}-*`,
`WP-EXH-0{1..3}-*`), the two SDD files N00 was explicitly allowed, and lane
A's ledger/second-pass/summary files. No overlap with lane B's packages
(api, cli, qua, mig, plg, tch, core, prj, ing, sec, bld, ext, ana).

## Final gate output

```
pytest:   1083 passed, 4 skipped (baseline 970 + 113 new)
ruff:     All checks passed!
mypy:     Success: no issues found in 121 source files (baseline 111)
plan_check: PLAN check passed: 346 requirements; 344 unique primary
            allocations; 191 packages; 642 person-weeks; dependency lower
            bound 52 weeks
trace_check: OK: every in-scope requirement is allocated and the design
            graph is well formed
```

Design gates unchanged: no trace regeneration was performed (per the lane
contract); the N00 SDD edits are prose amendments that the register does not
check.
