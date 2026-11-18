# Chat 2 queue (35 items)

Work through the items in this order. For each item, read its block, do the lane steps, write one ledger row, commit, then move to the next. Do not revisit finished items.

## Setup (once, before item 1)
```
git worktree add ../wt-chat2 -b glm-night/chat2 glm-night/20261117
cd ../wt-chat2
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
If `CHAT2_LEDGER.md` does not exist, create it with the header row `| WP | state | commit | tests | notes |` and `|---|---|---|---|---|`.

**Gate block (run from your worktree root with `.venv`):**
```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy src
.venv/Scripts/python.exe design/trace/plan_check.py
.venv/Scripts/python.exe design/trace/trace_check.py
```
All must exit 0 except failures that existed before your change (record them). Do not regenerate `design/trace/*` or the unified plan; those files are owned by the morning merge.

**Commit block:** `git add <only your allowed paths>` then `git commit -m "[GLM-NIGHT-CHAT2] <WP id>: <one-line summary>"` with the body line `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>`. Never `git add -A`. Never push. Never amend.

**Shared files (do not edit; report needed changes in your ledger instead):** `EXEC-PLAN-001-tracker.html`, `EXEC-PLAN-001-unified-execution-plan.md`, `docs/glm-night/GLM_NIGHT_LOG.md`, `docs/glm-night/parallel-plan.md`, `docs/glm-night/build_parallel_plan.py`, `docs/glm-night/board-snapshot.json`, `docs/glm-night/chat1-queue.md`, `docs/glm-night/chat2-queue.md`, `SRS-001-requirements.md`, `PLAN-001-specification-analysis-and-work-breakdown.md`, `design/`, `pyproject.toml`, `src/ectt/__init__.py`, `tests/conftest.py`, `BACKLOG_GLM_NIGHT.md`.

## Final item
After the last item, write `docs/glm-night/chat2-summary.md`: counts per state, every PARTIAL/SKIPPED/BLOCKED item with its reason, and the list of shared-file changes you need the owner to make in the morning. Commit it. Then stop.

### 1. WP-SPIKE-01: [WP-SPIKE-01] CFG sufficiency spike: python-clang against real embedded code

- Board: Validation spikes · phase P0 · effort 1 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - none listed on the board
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none
- Files you may change: `docs/verification/WP-SPIKE-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SPIKE-01`).

Steps:
1. Read the existing verification note and the code/tests named for WP-SPIKE-01.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-SPIKE-01-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 2. WP-SPIKE-03: [WP-SPIKE-03] PyInstaller distribution spike onto clean Windows

- Board: Validation spikes · phase P0 · effort 1 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - none listed on the board
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none
- Files you may change: `docs/verification/WP-SPIKE-03-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SPIKE-03`).

Steps:
1. Read the existing verification note and the code/tests named for WP-SPIKE-03.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-SPIKE-03-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 3. WP-SPIKE-02: [WP-SPIKE-02] Nested type-aware test data editor spike in PySide6

- Board: Validation spikes · phase P0 · effort 2 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - none listed on the board
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none
- Files you may change: `docs/verification/WP-SPIKE-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-SPIKE-02`).

Steps:
1. Read the existing verification note and the code/tests named for WP-SPIKE-02.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-SPIKE-02-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 4. WP-CORE-01: [WP-CORE-01] Determinism, source immutability and output confinement

- Board: CMP-CORE · phase P1 · effort 3 person-weeks · status `Review`
- Lane: **VERIFY**
- Requirements owned:
  - TOOL-NFR-060
  - TOOL-NFR-070
  - TOOL-NFR-080
  - TOOL-PRJ-050
  - TOOL-PRJ-080
- Acceptance criteria (board): > Two runs from identical inputs on different machines produce byte-identical generated artifacts; a write attempted outside the configured output root fails and is reported; no user source file's mtime or content changes across a full run

Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: none
- Files you may change: `docs/verification/WP-CORE-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CORE-01`).

Steps:
1. Read the existing verification note and the code/tests named for WP-CORE-01.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-CORE-01-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 5. WP-CORE-02: [WP-CORE-02] Structured error model, fail-safe termination and cancellation

- Board: CMP-CORE · phase P1 · effort 3 person-weeks · status `In Progress`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-NFR-090
  - TOOL-NFR-180
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-CORE-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CORE-02`).

Steps:
1. Read the existing verification note and the code/tests named for WP-CORE-02.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-CORE-02-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 6. WP-API-01: [WP-API-01] Engine API protocol, operation catalogue and versioning

- Board: CMP-API · phase P1 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PLG-060
  - TOOL-UIX-010
  - TOOL-UIX-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/api/`, `tests/api/`, `docs/verification/WP-API-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-API-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-API-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-API-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-API-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 7. WP-CLI-01: [WP-CLI-01] Non-interactive CLI generated from the operation catalogue

- Board: CMP-CLI · phase P1 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-CIC-010
  - TOOL-CIC-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-API-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/cli/`, `tests/cli/`, `docs/verification/WP-CLI-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CLI-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-CLI-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-CLI-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-CLI-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 8. WP-CLI-02: [WP-CLI-02] Stable documented exit codes

- Board: CMP-CLI · phase P1 · effort 1 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-CIC-030
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CLI-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-CORE-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/cli/`, `tests/cli/`, `docs/verification/WP-CLI-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CLI-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-CLI-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-CLI-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-CLI-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 9. WP-CLI-03: [WP-CLI-03] Container execution

- Board: CMP-CLI · phase P1 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-CIC-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CLI-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/cli/`, `tests/cli/`, `docs/verification/WP-CLI-03-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CLI-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-CLI-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-CLI-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-CLI-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 10. WP-PRJ-01: [WP-PRJ-01] Plain-text schema-versioned project store

- Board: CMP-PRJ · phase P1 · effort 4 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-CIC-080
  - TOOL-PRJ-010
  - TOOL-PRJ-020
  - TOOL-PRJ-070
  - TOOL-UIX-320
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-PRJ-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PRJ-01`).

Steps:
1. Read the existing verification note and the code/tests named for WP-PRJ-01.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-PRJ-01-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 11. WP-ING-01: [WP-ING-01] Compilation database ingestion

- Board: CMP-ING · phase P1 · effort 3 person-weeks · status `Review`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-010
  - TOOL-ING-020
  - TOOL-ING-030
  - TOOL-ING-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PRJ-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ING-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-01`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ING-01.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ING-01-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 12. WP-ANA-01: [WP-ANA-01] C front-end binding and dialect support

- Board: CMP-ANA · phase P1 · effort 4 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-010
  - TOOL-PAR-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ING-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-01`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-01.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-01-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 13. WP-ANA-02: [WP-ANA-02] Interface and type extraction

- Board: CMP-ANA · phase P1 · effort 5 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-030
  - TOOL-PAR-040
  - TOOL-PAR-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-02`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-02.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-02-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 14. WP-ANA-04: [WP-ANA-04] Analysis model persistence and schema versioning

- Board: CMP-ANA · phase P1 · effort 3 person-weeks · status `Review`
- Lane: **VERIFY**
- Requirements owned:
  - TOOL-PAR-100
  - TOOL-PAR-110
- Acceptance criteria (board): > A model emitted by the analyzer validates against its published schema, carries a schema version, and is rejected with a named reason by a consumer pinned to an incompatible version

Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: `WP-ANA-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-04-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-04`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-04.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-04-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 15. WP-ANA-08: [WP-ANA-08] Analysis model decision inventory

- Board: CMP-ANA · phase P2 · effort 1 person-weeks · status `Review`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-150
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-08-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-08`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-08.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-08-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 16. WP-ANA-09: [WP-ANA-09] Value ranges and dimension metadata in the analysis model

- Board: CMP-ANA · phase P2 · effort 1 person-weeks · status `Review`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-160
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-09-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-09`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-09.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-09-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 17. WP-ANA-07: [WP-ANA-07] Partial-failure resilience

- Board: CMP-ANA · phase P2 · effort 2 person-weeks · status `Backlog`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-130
  - TOOL-PAR-140
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-CORE-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-07-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-07`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-07.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-07-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 18. WP-API-02: [WP-API-02] Local-only transport with no network listener

- Board: CMP-API · phase P2 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-UIX-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-API-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/api/`, `tests/api/`, `docs/verification/WP-API-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-API-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-API-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-API-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-API-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 19. WP-CORE-04: [WP-CORE-04] Provenance record and version identification

- Board: CMP-CORE · phase P2 · effort 2 person-weeks · status `Backlog`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-INS-110
  - TOOL-QUA-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-CORE-04-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CORE-04`).

Steps:
1. Read the existing verification note and the code/tests named for WP-CORE-04.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-CORE-04-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 20. WP-QUA-07: [WP-QUA-07] Explicit statement of what is and is not qualified

- Board: CMP-QUA · phase P2 · effort 1 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · ADR-sensitive (decision-free part only)
- Requirements owned:
  - TOOL-QUA-090
- Acceptance criteria (board): > Documentation states, in one place, what qualification evidence is provided and what remains the user's responsibility, and no other document claims more

Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: `WP-CORE-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-07-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-QUA-07`).

Steps:
1. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
2. Write `docs/verification/WP-QUA-07-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
3. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
3. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
4. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 21. WP-ING-07: [WP-ING-07] Authored link plan ingestion and validation

- Board: CMP-ING · phase P2 · effort 2 person-weeks · status `Needs reconciliation`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-ING-200
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ING-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ING-07-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ING-07`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ING-07.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ING-07-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 22. WP-ANA-03: [WP-ANA-03] Call graph and scope classification

- Board: CMP-ANA · phase P2 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-03-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-03`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-03.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-03-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 23. WP-API-03: [WP-API-03] CLI and GUI round-trip equivalence

- Board: CMP-API · phase P2 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-UIX-330
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-API-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-CLI-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/api/`, `tests/api/`, `docs/verification/WP-API-03-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-API-03`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-API-03 and the requirement text in SRS-001. Write them into `docs/verification/WP-API-03-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-API-03-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 24. WP-CLI-04: [WP-CLI-04] Reference CI pipelines and artifact caching

- Board: CMP-CLI · phase P2 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-CIC-050
  - TOOL-CIC-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CLI-03` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/cli/`, `tests/cli/`, `docs/verification/WP-CLI-04-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-CLI-04`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-CLI-04 and the requirement text in SRS-001. Write them into `docs/verification/WP-CLI-04-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-CLI-04-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 25. WP-PRJ-02: [WP-PRJ-02] Diff-stable sharded storage for concurrent edit

- Board: CMP-PRJ · phase P2 · effort 3 person-weeks · status `Backlog`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PRJ-030
  - TOOL-PRJ-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PRJ-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/prj/`, `tests/prj/`, `docs/verification/WP-PRJ-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PRJ-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-PRJ-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-PRJ-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-PRJ-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 26. WP-PRJ-03: [WP-PRJ-03] Schema migration with explicit confirmation

- Board: CMP-PRJ · phase P2 · effort 3 person-weeks · status `In Progress`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PRJ-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PRJ-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-PRJ-03-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PRJ-03`).

Steps:
1. Read the existing verification note and the code/tests named for WP-PRJ-03.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-PRJ-03-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 27. WP-ANA-06: [WP-ANA-06] Static function testability and macro resolution

- Board: CMP-ANA · phase P2 · effort 4 person-weeks · status `Review`
- Lane: **VERIFY** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-080
  - TOOL-PAR-090
  - TOOL-PAR-170
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-ANA-06-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-06`).

Steps:
1. Read the existing verification note and the code/tests named for WP-ANA-06.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-ANA-06-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 28. WP-QUA-02: [WP-QUA-02] Tool operational requirements specification

- Board: CMP-QUA · phase P2 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-QUA-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-02-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-QUA-02`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-QUA-02 and the requirement text in SRS-001. Write them into `docs/verification/WP-QUA-02-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-QUA-02-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 29. WP-ANA-05: [WP-ANA-05] Control flow graph capability

- Board: CMP-ANA · phase P2 · effort 6 person-weeks · status `Backlog`
- Lane: **BUILD** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PAR-070
  - TOOL-PAR-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-ANA-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-SPIKE-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/ana/`, `tests/ana/`, `docs/verification/WP-ANA-05-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-ANA-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-ANA-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-ANA-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-ANA-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 30. WP-PRJ-04: [WP-PRJ-04] Dangling reference detection

- Board: CMP-PRJ · phase P3 · effort 1 person-weeks · status `Backlog`
- Lane: **VERIFY** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-PRJ-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-PRJ-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `docs/verification/WP-PRJ-04-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-PRJ-04`).

Steps:
1. Read the existing verification note and the code/tests named for WP-PRJ-04.
2. Run those tests. For each requirement above, confirm a real test name exists and passes.
3. Do not edit `src/` or `tests/`. If a test fails or a requirement has no test, record PARTIAL with the test name or requirement id and move on.
4. Write or update `docs/verification/WP-PRJ-04-analysis.md` (requirement → implementation → test evidence).
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 31. WP-MIG-06: [WP-MIG-06] Coexistence with another tool on one project

- Board: CMP-MIG · phase P3 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-MIG-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-01` (earlier in this queue; must be DONE/PARTIAL in ledger first); `WP-PRJ-01` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-06-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-MIG-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-MIG-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-MIG-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-MIG-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 32. WP-QUA-01: [WP-QUA-01] Tool classification analysis and confidence level

- Board: CMP-QUA · phase P4 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-QUA-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-CORE-04` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-01-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-QUA-01`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-QUA-01 and the requirement text in SRS-001. Write them into `docs/verification/WP-QUA-01-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-QUA-01-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 33. WP-QUA-05: [WP-QUA-05] Development process and change control documentation

- Board: CMP-QUA · phase P4 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-QUA-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none
- Files you may change: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-05-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-QUA-05`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-QUA-05 and the requirement text in SRS-001. Write them into `docs/verification/WP-QUA-05-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-QUA-05-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 34. WP-QUA-06: [WP-QUA-06] Standards objective mapping

- Board: CMP-QUA · phase P4 · effort 4 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-QUA-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-QUA-02` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-06-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-QUA-06`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-QUA-06 and the requirement text in SRS-001. Write them into `docs/verification/WP-QUA-06-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-QUA-06-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.

### 35. WP-QUA-08: [WP-QUA-08] Templates for user tool qualification artifacts

- Board: CMP-QUA · phase P4 · effort 3 person-weeks · status `Needs reconciliation`
- Lane: **BUILD** · ADR-sensitive (decision-free part only) · **RECON** (no acceptance criteria recorded)
- Requirements owned:
  - TOOL-QUA-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: `WP-QUA-06` (earlier in this queue; must be DONE/PARTIAL in ledger first)
- Files you may change: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-08-analysis.md`, `docs/glm-night/CHAT2_LEDGER.md`
- Full board text: `docs/glm-night/board-snapshot.json` (find the item by `work Package` = `WP-QUA-08`).

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 §5.4 row for WP-QUA-08 and the requirement text in SRS-001. Write them into `docs/verification/WP-QUA-08-analysis.md` under `## Acceptance criteria` before writing code. If they cannot be derived without inventing scope, stop and record SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria, inside the allowed paths only, with tests that include error and edge cases.
3. Write `docs/verification/WP-QUA-08-analysis.md` with a requirement → implementation → test-evidence table. Mark anything not covered as not covered.
4. The item is ADR-sensitive. Implement only the decision-free part. Record each open ADR question in your ledger row. Never choose an option.
4. Run the gates (see Gate block below). Commit locally with the message in the Commit block.
5. Append one row to `docs/glm-night/CHAT2_LEDGER.md`.

Completion (choose exactly one state in the ledger):
- DONE: all criteria met, gates green, verification note complete.
- PARTIAL: an increment landed and gates are green; list what remains.
- SKIPPED: a reason is recorded (for example `no derivable AC`, `unknown dependency state`).
- BLOCKED: a decision or ADR is needed; no code written for the blocked part.
Stop this item after 150k tokens or three failed gate attempts. Record PARTIAL and move on. Never stall the queue.
