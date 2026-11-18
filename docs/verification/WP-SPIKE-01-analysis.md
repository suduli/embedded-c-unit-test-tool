# WP-SPIKE-01 — Verification analysis: CFG sufficiency spike (python-clang against real embedded code)

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

WP-SPIKE-01 owns **no SRS requirements** (validation spike; PLAN-001 §5.5) and no package-specific
acceptance criterion is recorded in PLAN-001 §5.4. Per the board body, per-spike pass criteria are
defined in **PLAN-001 §4.4**; the criterion below is transcribed verbatim from there (not invented):

> **Pass criterion (PLAN-001 §4.4):** Function, type, global and call-graph extraction complete on a
> ≥20 kLOC embedded project with vendor headers, **with no construct requiring a CFG**. If a CFG is
> needed, §2.4 of ADR-001 fails and the C++ analyzer moves from "later" to "now".

The board additionally records the reconciliation flag ("write falsifiable, reviewable criteria before
moving to Ready") — that flag is an owner reconciliation task on the GitHub board and is **not** changed
by this night run (board writes are out of scope).

## Evidence chain (criterion → evidence)

| Criterion element | Recorded evidence | Status |
|---|---|---|
| Real embedded project ≥20 kLOC with vendor headers | STM32CubeF4 HAL + CMSIS, **151,558 lines** across 94 `.c` files — 7.5× the 20 kLOC floor (`spikes/spike-01-cfg-sufficiency/RESULTS.md` §Fixture) | met |
| Function extraction complete | 1,810 functions (deduplicated), 0 files with parse diagnostics | met |
| Type extraction complete | 506 types (struct/union/enum/typedef) | met |
| Global extraction complete | 16 globals | met |
| Call-graph extraction complete | 1,502 AST-resolved direct calls; 32 indirect (function-pointer dispatch) call sites recorded as explicit, located, unresolved edges — none silently dropped | met (with documented gap) |
| No construct requiring a CFG | All 32 unresolved sites are IRQ/DMA-completion callback dispatches through handle-struct function-pointer fields; a points-to/symbol-table problem, not a control-flow one (`RESULTS.md` §"The central question", ADR-001 §2.5) | met |
| Verdict recorded | `PASS WITH DOCUMENTED GAP` in `spikes/spike-01-cfg-sufficiency/RESULTS.md` §Verdict; ADR-001 §2.5 validation update and §4 item 1 "Done — held" | met |

## Test evidence

The spike artifact carries its own unit tests at `spikes/spike-01-cfg-sufficiency/tests/test_extract.py`
(target-argument construction for the `thumbv7em-none-eabi` bare-metal profile). Run result on this
worktree (`.venv`, 2026-11-18):

```
7 passed in 0.27s
```

Run from inside `spikes/spike-01-cfg-sufficiency/` — the module imports `extract` via the script
directory, so collection from the repository root fails with `ModuleNotFoundError: No module named
'extract'`. This is a property of the standalone spike artifact (it is not an installed package), not a
regression; noted for whoever relocates spike code into `src/ectt/ana/` under WP-ANA-05.

The spike has **no pytest coverage inside `tests/`** and owns no SRS requirement — this is expected and
correct for a P0 spike whose unblocks feed `WP-ANA-05` and ADR-001 §2, not any TOOL-* requirement.

## Constraint compliance

- No `src/` or `tests/` files edited (VERIFY lane).
- No ADR reopened or decided: the spike's decision-bearing part (ADR-001 §2.4 language choice) is
  already Accepted (2026-09-19); this note verifies the recorded evidence only.
- Shared files untouched.

## Result

**Verified against the PLAN-001 §4.4 pass criterion.** Every element of the criterion has recorded,
reviewable evidence (RESULTS.md with per-site file/line spot-check table, run stdout, `report.json`
totals); nothing requires a CFG; the documented gap (32 unresolved indirect calls) is bounded and
explicitly located. Historical-claim status on the board ("recorded complete in ADR-001, unverified")
can be moved to verified by the owner on the strength of this chain; the board itself is not edited
here.
