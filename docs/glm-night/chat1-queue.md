# Chat 1 queue (41 items)

Work through the items in this order. For each item, read its block, do the lane steps, write one ledger row, commit, then move to the next. Do not revisit finished items.

## Setup (once, before item 1)
```
git worktree add ../wt-chat1 -b glm-night/chat1 glm-night/20261117
cd ../wt-chat1
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
If `CHAT1_LEDGER.md` does not exist, create it with the header row `| WP | state | commit | tests | notes |` and `|---|---|---|---|---|`.

**Gate block (run from your worktree root with `.venv`):**
```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy src
.venv/Scripts/python.exe design/trace/plan_check.py
.venv/Scripts/python.exe design/trace/trace_check.py
```
All must exit 0 except failures that existed before your change (record them). Do not regenerate `design/trace/*` or the unified plan; those files are owned by the morning merge.

**Commit block:** `git add <only your allowed paths>` then `git commit -m "[GLM-NIGHT-CHAT1] <WP id>: <one-line summary>"` with the body line `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>`. Never `git add -A`. Never push. Never amend.

**Shared files (do not edit; report needed changes in your ledger instead):** `EXEC-PLAN-001-tracker.html`, `EXEC-PLAN-001-unified-execution-plan.md`, `docs/glm-night/GLM_NIGHT_LOG.md`, `docs/glm-night/parallel-plan.md`, `docs/glm-night/build_parallel_plan.py`, `docs/glm-night/board-snapshot.json`, `docs/glm-night/chat1-queue.md`, `docs/glm-night/chat2-queue.md`, `SRS-001-requirements.md`, `PLAN-001-specification-analysis-and-work-breakdown.md`, `design/`, `pyproject.toml`, `src/ectt/__init__.py`, `tests/conftest.py`, `BACKLOG_GLM_NIGHT.md`.

## Final item
After the last item, write `docs/glm-night/chat1-summary.md`: counts per state, every PARTIAL/SKIPPED/BLOCKED item with its reason, and the list of shared-file changes you need the owner to make in the morning. Commit it. Then stop.

### 1. WP-PLG-01: [WP-PLG-01] Extension point definition and versioning

- Board: CMP-PLG · phase P1 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PLG-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-02` (already implemented in repo)
- Files you may change: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-01-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PLG-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-PLG-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-PLG-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-PLG-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 2. WP-TCH-01: [WP-TCH-01] Declarative compiler configuration format

- Board: CMP-TCH · phase P1 · effort 3 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PLG-020
  - TOOL-TCH-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PLG-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-01-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 3. WP-TCH-02: [WP-TCH-02] Host compiler support: GCC and Clang

- Board: CMP-TCH · phase P1 · effort 2 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TCH-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-TCH-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-02-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 4. WP-GEN-01: [WP-GEN-01] Harness generation core

- Board: CMP-GEN · phase P1 · effort 5 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-HAR-010
  - TOOL-HAR-020
  - TOOL-HAR-040
  - TOOL-HAR-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-04` (already implemented in repo)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-01-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 5. WP-TCM-01: [WP-TCM-01] Test cases authored in C

- Board: CMP-TCM · phase P1 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TCD-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-GEN-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-01-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCM-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCM-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCM-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCM-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 6. WP-BLD-01: [WP-BLD-01] Host build orchestration and incremental rebuild

- Board: CMP-BLD · phase P1 · effort 4 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-EXE-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-GEN-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-TCH-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/bld/`, `tests/bld/`, `docs/verification/WP-BLD-01-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-BLD-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-BLD-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-BLD-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-BLD-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 7. WP-SEC-05: [WP-SEC-05] Security disclosure process and supported-version policy

- Board: CMP-SEC · phase P2 · effort 1 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-SEC-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none
- Files you may change: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-05-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SEC-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-SEC-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-SEC-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-SEC-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 8. WP-BLD-02: [WP-BLD-02] Sanitizer integration

- Board: CMP-BLD · phase P2 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-EXE-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-BLD-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/bld/`, `tests/bld/`, `docs/verification/WP-BLD-02-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-BLD-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-BLD-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-BLD-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-BLD-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 9. WP-SEC-04: [WP-SEC-04] Log and diagnostic content control

- Board: CMP-SEC · phase P2 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-SEC-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-01` (already implemented in repo)
- Files you may change: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-04-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SEC-04`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-SEC-04 and the requirement text in SRS-001. Write them into `docs/verification/WP-SEC-04-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-SEC-04-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 10. WP-CORE-06: [WP-CORE-06] Logging and diagnostic bundle

- Board: CMP-CORE · phase P2 · effort 2 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-NFR-130
  - TOOL-NFR-160
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-02` (already implemented in repo); `WP-SEC-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-06-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CORE-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-CORE-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-CORE-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-CORE-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 11. WP-TCH-07: [WP-TCH-07] First-run environment verification

- Board: CMP-TCH · phase P2 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-INS-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-TCH-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-07-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-07`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-07 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-07-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-07-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 12. WP-ING-02: [WP-ING-02] Alternative ingestion paths

- Board: CMP-ING · phase P2 · effort 3 person-weeks · status `In Progress`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-050
  - TOOL-ING-060
  - TOOL-ING-080
  - TOOL-ING-210
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ING-01` (already implemented in repo)
- Files you may change: `src/ectt/ing/`, `tests/ing/`, `docs/verification/WP-ING-02-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-ING-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-ING-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-ING-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 13. WP-ING-03: [WP-ING-03] Ingestion diagnostics, persistence and staleness

- Board: CMP-ING · phase P2 · effort 3 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-070
  - TOOL-ING-090
  - TOOL-ING-100
  - TOOL-ING-220
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ING-01` (already implemented in repo)
- Files you may change: `src/ectt/ing/`, `tests/ing/`, `docs/verification/WP-ING-03-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-ING-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-ING-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-ING-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 14. WP-PLG-04: [WP-PLG-04] AI provider extension protocol, registration and capability negotiation

- Board: CMP-PLG · phase P2 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD**
- Requirements owned:
  - TOOL-PLG-100
- Acceptance criteria (board): > A third-party provider registers via the public extension API, negotiates capabilities and version compatibility, and an incompatible provider is rejected without loading it into a feature

Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: `WP-PLG-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-04-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PLG-04`).

Steps:
1. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
2. Write `docs/verification/WP-PLG-04-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
3. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
4. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 15. WP-SEC-03: [WP-SEC-03] Untrusted-project warning and configuration-is-data

- Board: CMP-SEC · phase P2 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-SEC-050
  - TOOL-SEC-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PRJ-01` (already implemented in repo)
- Files you may change: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-03-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SEC-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-SEC-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-SEC-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-SEC-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 16. WP-CORE-07: [WP-CORE-07] User documentation and text externalisation

- Board: CMP-CORE · phase P2 · effort 4 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-NFR-120
  - TOOL-NFR-190
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none
- Files you may change: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-07-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CORE-07`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-CORE-07 and the requirement text in SRS-001. Write them into `docs/verification/WP-CORE-07-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-CORE-07-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 17. WP-GEN-02: [WP-GEN-02] Framework back-ends: Unity and cmocka

- Board: CMP-GEN · phase P2 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-HAR-060
  - TOOL-HAR-070
  - TOOL-PLG-030
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-GEN-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-PLG-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-02-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 18. WP-GEN-04: [WP-GEN-04] Regeneration contract and conflict reporting

- Board: CMP-GEN · phase P2 · effort 5 person-weeks · status `Needs reconciliation`
- Lane: **BUILD**
- Requirements owned:
  - TOOL-CBT-070
  - TOOL-HAR-090
  - TOOL-HAR-100
  - TOOL-HAR-110
- Acceptance criteria (board): > Regenerating a harness whose user region is still valid preserves it byte-for-byte; regenerating one whose UUT signature changed incompatibly reports a conflict and writes nothing

Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: `WP-GEN-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-04-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-04`).

Steps:
1. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
2. Write `docs/verification/WP-GEN-04-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
3. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
4. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 19. WP-ING-04: [WP-ING-04] Test scope model and resolution

- Board: CMP-ING · phase P2 · effort 5 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-120
  - TOOL-ING-130
  - TOOL-ING-140
  - TOOL-ING-150
  - TOOL-ING-190
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ING-01` (already implemented in repo)
- Files you may change: `src/ectt/ing/`, `tests/ing/`, `docs/verification/WP-ING-04-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-04`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-ING-04 and the requirement text in SRS-001. Write them into `docs/verification/WP-ING-04-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-ING-04-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 20. WP-ING-05: [WP-ING-05] Scope conflict detection and external dependency reporting

- Board: CMP-ING · phase P2 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-160
  - TOOL-ING-170
  - TOOL-ING-180
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-03` (already implemented in repo); `WP-ING-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ing/`, `tests/ing/`, `docs/verification/WP-ING-05-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-ING-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-ING-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-ING-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 21. WP-GEN-03: [WP-GEN-03] Static exposure and integration-scope harness

- Board: CMP-GEN · phase P2 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-HAR-030
  - TOOL-HAR-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-06` (already implemented in repo); `WP-GEN-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-ING-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-03-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 22. WP-GEN-06: [WP-GEN-06] Stub generation core

- Board: CMP-GEN · phase P2 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-STB-010
  - TOOL-STB-020
  - TOOL-STB-030
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-04` (already implemented in repo); `WP-ING-05` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-06-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 23. WP-GEN-05: [WP-GEN-05] Link closure and unresolved reference reporting

- Board: CMP-GEN · phase P2 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-HAR-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-03` (already implemented in repo); `WP-BLD-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-GEN-06` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-05-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 24. WP-GEN-08: [WP-GEN-08] Stub scope control and indirect-call stubbing

- Board: CMP-GEN · phase P2 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-STB-080
  - TOOL-STB-100
  - TOOL-STB-140
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-03` (already implemented in repo); `WP-GEN-06` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-08-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-08`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-08 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-08-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-08-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 25. WP-GEN-09: [WP-GEN-09] Stub regeneration and unsupported-construct flagging

- Board: CMP-GEN · phase P2 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-STB-110
  - TOOL-STB-120
  - TOOL-STB-130
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-GEN-04` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-GEN-06` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-09-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-09`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-09 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-09-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-09-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 26. WP-ING-06: [WP-ING-06] Multi-toolchain ingestion

- Board: CMP-ING · phase P3 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-110
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ING-01` (already implemented in repo); `WP-TCH-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ing/`, `tests/ing/`, `docs/verification/WP-ING-06-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-ING-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-ING-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-ING-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 27. WP-SEC-07: [WP-SEC-07] Target-supplied data treated as untrusted

- Board: CMP-SEC · phase P3 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-SEC-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-02` (already implemented in repo)
- Files you may change: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-07-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SEC-07`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-SEC-07 and the requirement text in SRS-001. Write them into `docs/verification/WP-SEC-07-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-SEC-07-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 28. WP-GEN-10: [WP-GEN-10] GoogleTest back-end (host only)

- Board: CMP-GEN · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-HAR-065
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-GEN-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-10-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-10`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-10 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-10-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-10-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 29. WP-GEN-11: [WP-GEN-11] Call wrapping of intra-unit calls

- Board: CMP-GEN · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-STB-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-03` (already implemented in repo); `WP-GEN-08` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-11-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-GEN-11`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-GEN-11 and the requirement text in SRS-001. Write them into `docs/verification/WP-GEN-11-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-GEN-11-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 30. WP-PLG-02: [WP-PLG-02] Extension discovery and load failure isolation

- Board: CMP-PLG · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PLG-070
  - TOOL-PLG-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PLG-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-02-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PLG-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-PLG-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-PLG-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-PLG-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 31. WP-TCH-04: [WP-TCH-04] Capability declaration and compiler version gating

- Board: CMP-TCH · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TCH-060
  - TOOL-TCH-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-TCH-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-04-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-04`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-04 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-04-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-04-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 32. WP-TCH-03: [WP-TCH-03] Cross-toolchain support and shipped configurations

- Board: CMP-TCH · phase P3 · effort 5 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TCH-030
  - TOOL-TCH-040
  - TOOL-TCH-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-TCH-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-03-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 33. WP-BLD-03: [WP-BLD-03] Cross-compiled target build

- Board: CMP-BLD · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TGT-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-BLD-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-TCH-03` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/bld/`, `tests/bld/`, `docs/verification/WP-BLD-03-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-BLD-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-BLD-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-BLD-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-BLD-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 34. WP-TCH-05: [WP-TCH-05] Multi-toolchain builds and reproducible containers

- Board: CMP-TCH · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TCH-080
  - TOOL-TCH-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-BLD-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-TCH-03` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-05-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 35. WP-TCH-06: [WP-TCH-06] Proprietary compiler support

- Board: CMP-TCH · phase P3 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TCH-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-TCH-03` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-06-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-TCH-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-TCH-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-TCH-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-TCH-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 36. WP-EXT-01: [WP-EXT-01] Simulator execution: QEMU and Renode

- Board: CMP-EXT · phase P3 · effort 5 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TGT-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-BLD-03` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-01-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-EXT-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-EXT-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-EXT-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-EXT-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 37. WP-EXT-03: [WP-EXT-03] Target result retrieval channels and protocol

- Board: CMP-EXT · phase P3 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TGT-050
  - TOOL-TGT-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-EXT-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-SEC-07` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-03-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-EXT-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-EXT-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-EXT-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-EXT-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 38. WP-EXT-02: [WP-EXT-02] Hardware execution and flashing via debug probe

- Board: CMP-EXT · phase P3 · effort 6 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TGT-030
  - TOOL-TGT-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-BLD-03` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-02-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-EXT-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-EXT-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-EXT-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-EXT-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 39. WP-EXT-07: [WP-EXT-07] User-supplied target execution methods

- Board: CMP-EXT · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PLG-040
  - TOOL-TGT-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-EXT-02` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-PLG-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-07-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-EXT-07`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-EXT-07 and the requirement text in SRS-001. Write them into `docs/verification/WP-EXT-07-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-EXT-07-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 40. WP-EXT-05: [WP-EXT-05] Hardware inventory and target failure classification

- Board: CMP-EXT · phase P3 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TGT-080
  - TOOL-TGT-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-EXT-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-05-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-EXT-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-EXT-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-EXT-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-EXT-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 41. WP-EXT-06: [WP-EXT-06] Suite splitting and on-target footprint documentation

- Board: CMP-EXT · phase P3 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-TGT-100
  - TOOL-TGT-110
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-EXT-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-06-analysis.md`, `docs/glm-night/CHAT1_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-EXT-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-EXT-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-EXT-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-EXT-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT1_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.
