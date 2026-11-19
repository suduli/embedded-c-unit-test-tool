# Overnight GLM queue, lane A (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-a -b glm-night/20261119-a glm-night/20261119-plan
cd ../wt-night-a
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261119/SECOND_PASS_A.md` with header `| item | what is needed | why it needs a human | where |`.

## Gate block (run before every commit; all must exit 0)
```
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check src tests
.venv/Scripts/python.exe -m mypy src
.venv/Scripts/python.exe design/trace/plan_check.py
.venv/Scripts/python.exe design/trace/trace_check.py
```
Do not regenerate `design/trace/*` or the unified plan.

## Commit block
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261119-a`.

## Hard rules
1. Never decide an owner decision. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. Item N00 is the only exception for `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261119/SECOND_PASS_A.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when your lane's cumulative reaches 1,450k tokens OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261119/LANE_A_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. N00: Apply the D-02 answer to the design text (SDD only)

- Estimate 60k tokens, cap 78k. Lane A. Must be first.
- Decision (do not re-decide): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Goal: edit `design/SDD-003-data-model.md` sections 6 and 7 and the single sentence in `design/SDD-002` (S2/S3) so they record stable ids plus content digests. Apply the memo's option (a) patch text for D-02 from `docs/proposals/decision-memos-20261117.md` verbatim; adjust only for line drift.
- Allowed paths: `design/SDD-003-data-model.md`, `design/SDD-002*` (one sentence), `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`.
- Forbidden here: `SRS-001-requirements.md`, `LICENSE`, `LICENSEES`, any ADR file, the decision register, `design/trace/*` regeneration. D-01, D-03 and D-04 are NOT applied tonight; D-03 is carried as a constraint in item prompts only.
- Done when: the three sections state the answer, `plan_check.py` and `trace_check.py` pass, full gate green, commit `[GLM-NIGHT] N00: record D-02 identity model in SDD-003`.
- If the memo patch does not apply cleanly or the gates fail after one fix attempt: do not force it. Append a row to `docs/glm-night/overnight-20261119/SECOND_PASS_A.md` and continue; items that need SDD-003 section 6/7 continue against the memo text and note that in their ledger rows.

### 2. WP-TCM-02
[WP-TCM-02] Data-driven test case model and on-disk format  (board: CMP-TCM, phase P2, 5 person-weeks)

- Estimate 205k tokens, hard cap 266k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-02 (Data-driven test case model and on-disk format) for requirements TOOL-TCD-020, TOOL-TCD-030, TOOL-TCD-040, TOOL-TCD-140.
- Requirements: TOOL-TCD-020, TOOL-TCD-030, TOOL-TCD-040, TOOL-TCD-140
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ANA-04, WP-PRJ-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-02-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-02-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 3. WP-EXH-01
[WP-EXH-01] Host execution and per-test result reporting  (board: CMP-EXH, phase P1, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-EXH-01 (Host execution and per-test result reporting) for requirements TOOL-EXE-010, TOOL-EXE-020.
- Requirements: TOOL-EXE-010, TOOL-EXE-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-BLD-01, WP-TCM-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests". Also satisfy the run-integrity acceptance of T-14 (EXEC-PLAN-001 section 7.4, card T-14). It was waiting on D-02, which is now answered.
- Allowed paths: `src/ectt/exh/`, `tests/exh/`, `docs/verification/WP-EXH-01-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-EXH-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-EXH-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 4. WP-EXH-02
[WP-EXH-02] Crash isolation, timeout and process exit status  (board: CMP-EXH, phase P1, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-EXH-02 (Crash isolation, timeout and process exit status) for requirements TOOL-EXE-030, TOOL-EXE-040, TOOL-EXE-060.
- Requirements: TOOL-EXE-030, TOOL-EXE-040, TOOL-EXE-060
- Acceptance criteria (board): > A test case that segfaults, one that hangs past the timeout, and one that calls `abort()` are each reported as a failure with the remaining cases still executed  Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: WP-CORE-02, WP-EXH-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): Also satisfy the run-integrity acceptance of T-14 (EXEC-PLAN-001 section 7.4, card T-14). It was waiting on D-02, which is now answered.
- Allowed paths: `src/ectt/exh/`, `tests/exh/`, `docs/verification/WP-EXH-02-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-EXH-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 5. WP-TCM-03
[WP-TCM-03] Expected-value comparison engine  (board: CMP-TCM, phase P2, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-03 (Expected-value comparison engine) for requirements TOOL-TCD-050, TOOL-TCD-060.
- Requirements: TOOL-TCD-050, TOOL-TCD-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-03-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 6. WP-TCM-04
[WP-TCM-04] Suites, selective execution and test independence  (board: CMP-TCM, phase P2, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-04 (Suites, selective execution and test independence) for requirements TOOL-TCD-080, TOOL-TCD-090.
- Requirements: TOOL-TCD-080, TOOL-TCD-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-04-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-04-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-04-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 7. WP-EXH-03
[WP-EXH-03] Parallel test execution  (board: CMP-EXH, phase P1, 2 person-weeks)

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-EXH-03 (Parallel test execution) for requirements TOOL-EXE-050.
- Requirements: TOOL-EXE-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/exh/`, `tests/exh/`, `docs/verification/WP-EXH-03-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-EXH-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-EXH-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 8. WP-TCM-05
[WP-TCM-05] Ranged and robustness input generation  (board: CMP-TCM, phase P2, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-05 (Ranged and robustness input generation) for requirements TOOL-TCD-070, TOOL-TCD-130.
- Requirements: TOOL-TCD-070, TOOL-TCD-130
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-05-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-05-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-05-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 9. WP-TCM-06
[WP-TCM-06] Test case interchange import and export  (board: CMP-TCM, phase P2, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-06 (Test case interchange import and export) for requirements TOOL-TCD-100.
- Requirements: TOOL-TCD-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-06-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-06-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-06-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 10. WP-CBT-01
[WP-CBT-01] Suite re-execution without regeneration  (board: CMP-CBT, phase P2, 2 person-weeks)

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-CBT-01 (Suite re-execution without regeneration) for requirements TOOL-CBT-010.
- Requirements: TOOL-CBT-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests". Also satisfy the run-integrity acceptance of T-14 (EXEC-PLAN-001 section 7.4, card T-14). It was waiting on D-02, which is now answered.
- Allowed paths: `src/ectt/cbt/`, `tests/cbt/`, `docs/verification/WP-CBT-01-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-CBT-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-CBT-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 11. WP-TCM-07
[WP-TCM-07] Boundary, equivalence and classification-tree derivation  (board: CMP-TCM, phase P3, 5 person-weeks)

- Estimate 205k tokens, hard cap 266k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-07 (Boundary, equivalence and classification-tree derivation) for requirements TOOL-TCD-110, TOOL-TCD-120.
- Requirements: TOOL-TCD-110, TOOL-TCD-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ANA-02, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-07-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 12. WP-GEN-07
[WP-GEN-07] Stub behaviour programming  (board: CMP-GEN, phase P2, 5 person-weeks)

- Estimate 205k tokens, hard cap 266k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-GEN-07 (Stub behaviour programming) for requirements TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070.
- Requirements: TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-GEN-06, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-07-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-GEN-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-GEN-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 13. WP-ATG-01
[WP-ATG-01] Validation port and generated-case lifecycle  (board: CMP-ATG, phase P3, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-ATG-01 (Validation port and generated-case lifecycle) for requirements TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080.
- Requirements: TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/atg/`, `tests/atg/`, `docs/verification/WP-ATG-01-analysis.md`, `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-ATG-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-ATG-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

## End
Listed total 2095k tokens (stop rule above applies earlier).
