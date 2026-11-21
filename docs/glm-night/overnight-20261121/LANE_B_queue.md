# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-21b -b glm-night/20261121-b main
cd ../wt-night-21b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` a690b3f): 3097 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261121/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261121-b`.

## Hard rules
1. Never decide an owner decision. No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261121/SECOND_PASS_B.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261121/LANE_B_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. B1: Analysis model schema bump: function extent, all unsupported occurrences, global types

- Estimate 200k tokens, hard cap 260k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: One additive schema bump (next minor after the current one; add the new schema file, keep every older reader rule working): (1) add start and end line to FunctionModel; (2) record every occurrence (owner function and location) of an unsupported construct, not only the first; (3) record global variable types and initial-value presence so a harness can reach file-static data. Update the version constant and tests. Then use (2) in src/ectt/ana/eligibility.py so each owner is named. Tests: old files still load, new fields validate, two runs byte-identical.
- Allowed paths: `src/ectt/ana/`, `tests/ana/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. B3: Re-entrant safe-write transaction

- Estimate 100k tokens, hard cap 130k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Make OutputRoot.transaction in src/ectt/core/fs.py re-entrant (nested scopes join the outer one), then remove the private-attribute check in src/ectt/ana/persist.py that reads output_root._journal. Keep public names and error messages. Tests: nested commit, nested failure rolls back everything, cancellation inside nested scope.
- Allowed paths: `src/ectt/core/`, `tests/core/`, `src/ectt/ana/persist.py`, `tests/ana/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. WP-COV-01
[WP-COV-01] Statement and branch coverage from compiler backend  (board: CMP-COV, phase P1, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-01 (Statement and branch coverage from compiler backend) for requirements TOOL-COV-010, TOOL-COV-020.
- Requirements: TOOL-COV-010, TOOL-COV-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-TCH-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first". GCC is the primary coverage path (gcov --json-format, condition coverage via -fcondition-coverage); Clang support is added later and must not shape this item. There is no C compiler on this machine: build parsers and readers against hand-written gcov JSON fixtures taken from the documented GCC format (check key names against the GCC gcov documentation, not your memory), and say in the ledger that real GCC output has not been checked.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-01-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-COV-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-COV-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 4. WP-COV-02
[WP-COV-02] Coverage merge and per-test attribution  (board: CMP-COV, phase P1, 4 person-weeks)

- Estimate 170k tokens, hard cap 221k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-02 (Coverage merge and per-test attribution) for requirements TOOL-COV-110, TOOL-COV-120, TOOL-COV-180.
- Requirements: TOOL-COV-110, TOOL-COV-120, TOOL-COV-180
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first". GCC is the primary coverage path (gcov --json-format, condition coverage via -fcondition-coverage); Clang support is added later and must not shape this item. There is no C compiler on this machine: build parsers and readers against hand-written gcov JSON fixtures taken from the documented GCC format (check key names against the GCC gcov documentation, not your memory), and say in the ledger that real GCC output has not been checked.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-02-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-COV-02-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-COV-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 5. WP-COV-03
[WP-COV-03] Coverage threshold enforcement  (board: CMP-COV, phase P1, 1 person-weeks)

- Estimate 80k tokens, hard cap 104k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-03 (Coverage threshold enforcement) for requirements TOOL-COV-130.
- Requirements: TOOL-COV-130
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-03-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-COV-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-COV-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 6. WP-COV-04
[WP-COV-04] Function and function-call coverage  (board: CMP-COV, phase P3, 2 person-weeks)

- Estimate 110k tokens, hard cap 143k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-04 (Function and function-call coverage) for requirements TOOL-COV-030, TOOL-COV-040.
- Requirements: TOOL-COV-030, TOOL-COV-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first". GCC is the primary coverage path (gcov --json-format, condition coverage via -fcondition-coverage); Clang support is added later and must not shape this item. There is no C compiler on this machine: build parsers and readers against hand-written gcov JSON fixtures taken from the documented GCC format (check key names against the GCC gcov documentation, not your memory), and say in the ledger that real GCC output has not been checked.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-04-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-COV-04-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-COV-04-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 7. WP-REP-02
[WP-REP-02] Machine-readable outputs: JUnit and Cobertura/LCOV  (board: CMP-REP, phase P1, 3 person-weeks)

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-02 (Machine-readable outputs: JUnit and Cobertura/LCOV) for requirements TOOL-REP-010, TOOL-REP-020.
- Requirements: TOOL-REP-010, TOOL-REP-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-02, WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-02-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-02-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 8. WP-COV-08
[WP-COV-08] Unit-under-test versus harness coverage separation  (board: CMP-COV, phase P3, 2 person-weeks)

- Estimate 110k tokens, hard cap 143k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-08 (Unit-under-test versus harness coverage separation) for requirements TOOL-COV-160.
- Requirements: TOOL-COV-160
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-01, WP-ING-04. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-08-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-COV-08-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-COV-08-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 9. WP-COV-09
[WP-COV-09] Coverage-by-analysis justification with digest binding  (board: CMP-COV, phase P4, 4 person-weeks)

- Estimate 170k tokens, hard cap 221k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-09 (Coverage-by-analysis justification with digest binding) for requirements TOOL-COV-140, TOOL-COV-150.
- Requirements: TOOL-COV-140, TOOL-COV-150
- Acceptance criteria (board): > Editing a source line under an accepted justification invalidates that justification, and the next report shows the construct as uncovered rather than justified  Recorded in PLAN-001 §5.4. Done requires reviewed acceptance evidence against this criterion.
- Dependencies: WP-COV-01, WP-PRJ-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-09-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
2. Write or update `docs/verification/WP-COV-09-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
3. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 10. WP-REP-03
[WP-REP-03] HTML report with annotated source  (board: CMP-REP, phase P1, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-03 (HTML report with annotated source) for requirements TOOL-REP-030, TOOL-REP-040.
- Requirements: TOOL-REP-030, TOOL-REP-040
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-01, WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-03-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 11. WP-REP-10
[WP-REP-10] Coverage interchange import and export  (board: CMP-REP, phase P4, 3 person-weeks)

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-10 (Coverage interchange import and export) for requirements TOOL-MIG-080.
- Requirements: TOOL-MIG-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-02, WP-REP-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-10-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-10-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-10-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 12. WP-REP-07
[WP-REP-07] Paginated PDF archival rendering  (board: CMP-REP, phase P4, 4 person-weeks)

- Estimate 170k tokens, hard cap 221k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-REP-07 (Paginated PDF archival rendering) for requirements TOOL-REP-080.
- Requirements: TOOL-REP-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-REP-03. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-07-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-REP-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-REP-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 13. WP-COV-07
[WP-COV-07] Bare-metal coverage retrieval  (board: CMP-COV, phase P3, 5 person-weeks)

- Estimate 190k tokens, hard cap 247k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-COV-07 (Bare-metal coverage retrieval) for requirements TOOL-COV-100.
- Requirements: TOOL-COV-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-COV-01, WP-EXT-03. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first". GCC is the primary coverage path (gcov --json-format, condition coverage via -fcondition-coverage); Clang support is added later and must not shape this item. There is no C compiler on this machine: build parsers and readers against hand-written gcov JSON fixtures taken from the documented GCC format (check key names against the GCC gcov documentation, not your memory), and say in the ledger that real GCC output has not been checked.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-07-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-COV-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-COV-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 14. B2: Exact range links for requirements using function extent

- Estimate 110k tokens, hard cap 143k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: After B1: make source-element links in ectt.trc resolve range links exactly using the new function extent, and keep approximate behaviour only for models without it. Tests: exact hit, boundary lines, model without extent still works.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 15. B4: Report renderers show machine-generated and unreviewed marks

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Call report_marks and format_mark (from ectt.atg) in the ectt.rep renderers so reports show machine-generated and unreviewed marks. Import only the narrow function; do not make rep depend on the rest of atg. Tests: marked case shows mark, unmarked case unchanged, ordering deterministic.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 16. B5: Publish the interchange format reference

- Estimate 70k tokens, hard cap 91k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Write the output of render_format_reference() to docs/reference/interchange-format.md (generated by a small script in the same folder, with a test that the file matches the generator), and fix docs/verification/WP-MIG-01-analysis.md for the cmocka OK spelling. Allowed to create docs/reference/ only.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/reference/`, `docs/verification/WP-MIG-01-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 17. B6: Project.save integration of the sharded store

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Finish WP-PRJ-02: make Project.save able to write the sharded layout from ectt.prj.shards while the single-file manifest stays the default. Choose layout by an explicit argument only; no automatic switch. Tests: both layouts round-trip, unchanged save is byte-stable, interrupted save leaves the original.
- Allowed paths: `src/ectt/prj/`, `tests/prj/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 18. B7: Re-import SPEC-RELATIONS from ReqIF as associations

- Estimate 100k tokens, hard cap 130k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.trc, make import_reqif read SPEC-RELATIONS back as requirement-to-test associations, so export then import is lossless. Tests: round trip, dangling relation refused with a named reason, duplicate relation merged once.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 19. B8: Mutation-style tests for core, prj and mig

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. For src/ectt/core, src/ectt/prj and src/ectt/mig, hand-written mutants in a temp copy, confirm kills, add tests for survivors; kill rate in docs/glm-night/overnight-20261121/mutation-core-prj-mig.md. No src/ edits.
- Allowed paths: `tests/core/`, `tests/prj/`, `tests/mig/`, `docs/glm-night/overnight-20261121/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 20. B9: Seeded property-style tests for trc and rep

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random inputs for the traceability matrix, ReqIF export and import round trip, and report merge. No wall clock. No src/ edits.
- Allowed paths: `tests/trc/`, `tests/rep/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 2770k tokens.
