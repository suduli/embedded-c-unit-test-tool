# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-b -b glm-night/20261119-b glm-night/20261119-plan
cd ../wt-night-b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` 353b9b4): 970 passed, 4 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261119/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261119-b`.

## Hard rules
1. Never decide an owner decision. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. Item N00 is the only exception for `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261119/SECOND_PASS_B.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when your lane's cumulative reaches 1,450k tokens OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261119/LANE_B_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. WP-CORE-03
[WP-CORE-03] Platform baseline and offline guarantee  (board: CMP-CORE, phase P1, 2 person-weeks)

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-CORE-03 (Platform baseline and offline guarantee) for requirements TOOL-NFR-010, TOOL-NFR-020, TOOL-NFR-100.
- Requirements: TOOL-NFR-010, TOOL-NFR-020, TOOL-NFR-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: none. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-03 Platform order (owner answer, 2026-11-19, memo option (a)): "Windows first, Linux CI kept green".
- Allowed paths: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-03-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-CORE-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-CORE-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 2. WP-CORE-02
[WP-CORE-02] Structured error model, fail-safe termination and cancellation  (board: CMP-CORE, phase P1, 3 person-weeks)

- Estimate 90k tokens, hard cap 117k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: WP-CORE-02 is PARTIAL (see CHAT2_LEDGER.md row). Close the decision-free remainder: (1) adopt the stable exit-code table from WP-CLI-02 (src/ectt/cli) for every EcttError category, with a test per category; (2) route at least one existing long-running operation through OutputRoot.transaction so a cancelled or failed run leaves no partial output (test with a cancellation token and with an injected failure). Prior ledger state `PARTIAL`: mechanisms verified; CLI exit-code + op adoption open
- Requirements: TOOL-NFR-090, TOOL-NFR-180
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-CORE-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/core/`, `tests/core/`, `src/ectt/cli/`, `tests/cli/`, `docs/verification/WP-CORE-02-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-CORE-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 3. WP-ANA-07
[WP-ANA-07] Partial-failure resilience  (board: CMP-ANA, phase P2, 2 person-weeks)

- Estimate 90k tokens, hard cap 117k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: WP-ANA-07 is PARTIAL. Close the decision-free remainder: PAR-140 unsupported-construct inventory is carried and schema-gated but never populated (always []). Populate it from extraction for constructs the extractor already recognises as unsupported, deterministic and sorted, with fixtures. Do not add a multi-file driver. Prior ledger state `PARTIAL`: PAR-130 done; PAR-140 inventory unpopulated + no multi-file driver
- Requirements: TOOL-PAR-130, TOOL-PAR-140
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ANA-01, WP-CORE-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/ana/`, `tests/ana/`, `docs/verification/WP-ANA-07-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-ANA-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 4. WP-ANA-06
[WP-ANA-06] Static function testability and macro resolution  (board: CMP-ANA, phase P2, 4 person-weeks)

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: WP-ANA-06 is PARTIAL. Implement PAR-090 only (macro resolution) with libclang fixtures. Do NOT touch PAR-080 (exposure mechanism; ADR-sensitive, belongs with WP-GEN-03). If a fixture cannot be made deterministic, record PARTIAL with the reason. Prior ledger state `PARTIAL`: PAR-170 done; PAR-080 exposure open; PAR-090 unimplemented
- Requirements: TOOL-PAR-080, TOOL-PAR-090, TOOL-PAR-170
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ANA-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/ana/`, `tests/ana/`, `docs/verification/WP-ANA-06-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-ANA-06-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 5. TASK-107

- Estimate 150k tokens, cap 195k. Lane B. Filler: tests only.
- Goal: Run EXEC-PLAN-001 section 7.2 card TASK-107 (mutation-style test strengthening for ectt.core and ectt.prj). Tests only; no src changes.
- Allowed paths: `tests/core/`, `tests/prj/`, `docs/glm-night/overnight-20261119/`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`. No `src/` edits.
- Done when: new tests pass, no existing test changed, full gate green, one commit.

### 6. WP-REP-01
[WP-REP-01] Single intermediate report model  (board: CMP-REP, phase P1, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-01 (Single intermediate report model) for requirements TOOL-REP-090, TOOL-REP-100.
- Requirements: TOOL-REP-090, TOOL-REP-100
- Acceptance criteria (board): > Two different renderers over one persisted report model cannot disagree on any test's status or any coverage figure; re-running the renderer produces byte-identical output excluding timestamps  Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: WP-CORE-01, WP-EXH-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- CROSS-LANE DEPENDENCY on `WP-EXH-01` (lane A). Before starting: check `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md` in the lane A worktree (`../wt-night-a`) for a `WP-EXH-01` row that is DONE (PARTIAL only if its remainder is unrelated). If so: `git merge --no-edit glm-night/20261119-a`, run the full gate; if it is red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: SKIP this item for now and retry it once after the last queue item before writing the summary; if still unsatisfied record `SKIPPED (dep)` in the ledger and the second-pass file.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-01-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-REP-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 7. WP-REP-11
[WP-REP-11] Report format extension point  (board: CMP-REP, phase P3, 2 person-weeks)

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-11 (Report format extension point) for requirements TOOL-PLG-050.
- Requirements: TOOL-PLG-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-PLG-01, WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-11-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-11-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-11-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 8. WP-REP-06
[WP-REP-06] Report provenance and format version stability  (board: CMP-REP, phase P4, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-06 (Report provenance and format version stability) for requirements TOOL-REP-070, TOOL-REP-130.
- Requirements: TOOL-REP-070, TOOL-REP-130
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-CORE-04, WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-06-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-06-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-06-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 9. WP-REP-08
[WP-REP-08] Cross-unit summary and coverage trend  (board: CMP-REP, phase P3, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-08 (Cross-unit summary and coverage trend) for requirements TOOL-REP-110, TOOL-REP-120.
- Requirements: TOOL-REP-110, TOOL-REP-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-08-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-08-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-08-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 10. WP-PLG-03
[WP-PLG-03] Built-ins implemented through public extension points  (board: CMP-PLG, phase P3, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-PLG-03 (Built-ins implemented through public extension points) for requirements TOOL-PLG-090.
- Requirements: TOOL-PLG-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-GEN-02, WP-PLG-01, WP-REP-11, WP-TCH-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-03-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-PLG-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-PLG-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 11. WP-CORE-04
[WP-CORE-04] Provenance record and version identification  (board: CMP-CORE, phase P2, 2 person-weeks)

- Estimate 60k tokens, hard cap 78k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: WP-CORE-04 is PARTIAL. Now that the report model (WP-REP-01) exists in your branch, embed the provenance record in the artifacts the producing packages already emit, per TOOL-QUA-060. Skip any artifact whose producer is not yet in the branch and list it. Prior ledger state `PARTIAL`: facility done; in-every-artifact embedding open
- Requirements: TOOL-INS-110, TOOL-QUA-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-CORE-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/core/`, `tests/core/`, `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-CORE-04-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-CORE-04-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 12. WP-PRJ-05
[WP-PRJ-05] Archival export and reproduction verification  (board: CMP-PRJ, phase P4, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-PRJ-05 (Archival export and reproduction verification) for requirements TOOL-PRJ-100, TOOL-PRJ-110.
- Requirements: TOOL-PRJ-100, TOOL-PRJ-110
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-CORE-04, WP-PRJ-01, WP-REP-06. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/prj/`, `tests/prj/`, `docs/verification/WP-PRJ-05-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-PRJ-05-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-PRJ-05-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 13. WP-REP-09
[WP-REP-09] Report generation from archived result data  (board: CMP-REP, phase P4, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-09 (Report generation from archived result data) for requirements TOOL-REP-150.
- Requirements: TOOL-REP-150
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-PRJ-05, WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-09-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-09-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-09-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 14. WP-CLI-05
[WP-CLI-05] CI sharding and report merge  (board: CMP-CLI, phase P3, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-CLI-05 (CI sharding and report merge) for requirements TOOL-CIC-060.
- Requirements: TOOL-CIC-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-CLI-04, WP-REP-08. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/cli/`, `tests/cli/`, `docs/verification/WP-CLI-05-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-CLI-05-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-CLI-05-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 15. WP-TRC-01
[WP-TRC-01] Requirement association and bidirectional matrix  (board: CMP-TRC, phase P4, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TRC-01 (Requirement association and bidirectional matrix) for requirements TOOL-TRC-010, TOOL-TRC-020, TOOL-TRC-030.
- Requirements: TOOL-TRC-010, TOOL-TRC-020, TOOL-TRC-030
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-REP-01, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- CROSS-LANE DEPENDENCY on `WP-TCM-02` (lane A). Before starting: check `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md` in the lane A worktree (`../wt-night-a`) for a `WP-TCM-02` row that is DONE (PARTIAL only if its remainder is unrelated). If so: `git merge --no-edit glm-night/20261119-a`, run the full gate; if it is red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: SKIP this item for now and retry it once after the last queue item before writing the summary; if still unsatisfied record `SKIPPED (dep)` in the ledger and the second-pass file.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/verification/WP-TRC-01-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TRC-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TRC-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 16. WP-TRC-02
[WP-TRC-02] Unlinked requirement and unlinked test reporting  (board: CMP-TRC, phase P4, 2 person-weeks)

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TRC-02 (Unlinked requirement and unlinked test reporting) for requirements TOOL-TRC-040.
- Requirements: TOOL-TRC-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TRC-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/verification/WP-TRC-02-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TRC-02-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TRC-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 17. TASK-108

- Estimate 150k tokens, cap 195k. Lane B. Filler: tests only.
- Goal: Run EXEC-PLAN-001 section 7.2 card TASK-108 (seeded property-style tests for the YAML adapter and schema reader). Tests only; deterministic seeds only.
- Allowed paths: `tests/core/`, `tests/prj/`, `docs/glm-night/overnight-20261119/`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`. No `src/` edits.
- Done when: new tests pass, no existing test changed, full gate green, one commit.

### 18. WP-REP-12
[WP-REP-12] Reconstructable open result export with test-case coordination  (board: CMP-REP, phase P2, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-12 (Reconstructable open result export with test-case coordination) for requirements TOOL-MIG-060.
- Requirements: TOOL-MIG-060
- Acceptance criteria (board): > Export passing, failing, crashed, timed-out and partial-run cases plus result identities, expected/actual values, diagnostics and provenance; an independent reader reconstructs the test cases from TCM-06 and complete results without a private project database. Publish the versioned JSON interchange schema, examples and explicit loss/error handling; coverage export remains REP-10/P4  Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: WP-REP-01, WP-TCM-06. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- CROSS-LANE DEPENDENCY on `WP-TCM-06` (lane A). Before starting: check `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md` in the lane A worktree (`../wt-night-a`) for a `WP-TCM-06` row that is DONE (PARTIAL only if its remainder is unrelated). If so: `git merge --no-edit glm-night/20261119-a`, run the full gate; if it is red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: SKIP this item for now and retry it once after the last queue item before writing the summary; if still unsatisfied record `SKIPPED (dep)` in the ledger and the second-pass file.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-12-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-REP-12-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 19. WP-MIG-01
[WP-MIG-01] Execution of existing Unity and cmocka suites  (board: CMP-MIG, phase P2, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-MIG-01 (Execution of existing Unity and cmocka suites) for requirements TOOL-MIG-010.
- Requirements: TOOL-MIG-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-GEN-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- CROSS-LANE DEPENDENCY on `WP-EXH-01` (lane A). Before starting: check `docs/glm-night/overnight-20261119/LANE_A_LEDGER.md` in the lane A worktree (`../wt-night-a`) for a `WP-EXH-01` row that is DONE (PARTIAL only if its remainder is unrelated). If so: `git merge --no-edit glm-night/20261119-a`, run the full gate; if it is red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: SKIP this item for now and retry it once after the last queue item before writing the summary; if still unsatisfied record `SKIPPED (dep)` in the ledger and the second-pass file.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-01-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-MIG-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-MIG-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 20. WP-TRC-03
[WP-TRC-03] Requirement import from ReqIF, CSV and plain text  (board: CMP-TRC, phase P4, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TRC-03 (Requirement import from ReqIF, CSV and plain text) for requirements TOOL-TRC-050, TOOL-TRC-060.
- Requirements: TOOL-TRC-050, TOOL-TRC-060
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TRC-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/verification/WP-TRC-03-analysis.md`, `docs/glm-night/overnight-20261119/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261119/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TRC-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TRC-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

## End
Listed total 2935k tokens (stop rule above applies earlier).
