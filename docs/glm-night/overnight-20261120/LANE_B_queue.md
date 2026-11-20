# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-b -b glm-night/20261120-b main
cd ../wt-night-b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` f044ef1): 1457 passed, 5 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261120/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261120-b`.

## Hard rules
1. Never decide an owner decision. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261120/SECOND_PASS_B.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. Last night the estimates ran high, so expect to finish the whole list. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261120/LANE_B_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. FIX-REP: Report model reader and merge fix

- Estimate 110k tokens, hard cap 143k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In src/ectt/rep/model.py (format 1.1): make the reader's 'execution' field optional (provenance stays required) so merged reports, which have no single runner, load through load_report_model; expose a public factory for digest-bound models built outside a ResultSet and switch the CI-merge code to it instead of the private helper; add 'report', 'traceability' and 'migration' to CATEGORY_EXIT_CODES in ectt.cli.exit_codes. Keep the old behaviour for reports that do have execution. Tests: merged report round trip, missing provenance still refused, exit code per new category.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `src/ectt/cli/`, `tests/cli/`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. FIX-TXN: Route project saves and analysis-model writes through the safe-write transaction

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Close the WP-CORE-02 remainder in SECOND_PASS_B.md: route ectt.prj project saves and ectt.ana.persist.write_analysis_model callers through OutputRoot.transaction, so a cancelled or failed write leaves the original files untouched (SDD-003 section 3). Do not change file formats or public names. Tests: injected failure mid-save leaves original byte-identical; cancellation leaves no partial file.
- Allowed paths: `src/ectt/prj/`, `tests/prj/`, `src/ectt/ana/`, `tests/ana/`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. CI-LINUX: Linux CI lane for the full gate

- Estimate 60k tokens, hard cap 78k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: D-03 says Windows first with Linux CI kept green. Edit only .github/workflows/tests.yml so the full gate block (pytest, ruff, mypy, plan_check, trace_check, and the Linux baseline test) runs on ubuntu-latest and windows-latest with pinned action versions and 'permissions: contents: read'. Do not edit traceability.yml. Verify the YAML parses and that every command in it works locally. Say in the ledger that CI itself could not be run.
- Allowed paths: `.github/workflows/tests.yml`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. WP-MIG-02
[WP-MIG-02] Ceedling project import  (board: CMP-MIG, phase P2, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-MIG-02 (Ceedling project import) for requirements TOOL-MIG-020.
- Requirements: TOOL-MIG-020
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ING-01, WP-MIG-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-02-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-MIG-02-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-MIG-02-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 5. WP-MIG-04
[WP-MIG-04] Commercial tool and CSV test data import  (board: CMP-MIG, phase P3, 6 person-weeks)

- Estimate 230k tokens, hard cap 299k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-MIG-04 (Commercial tool and CSV test data import) for requirements TOOL-MIG-030, TOOL-MIG-050.
- Requirements: TOOL-MIG-030, TOOL-MIG-050
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TCM-06. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-04-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-MIG-04-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-MIG-04-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 6. WP-MIG-05
[WP-MIG-05] Import fidelity reporting  (board: CMP-MIG, phase P3, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-MIG-05 (Import fidelity reporting) for requirements TOOL-MIG-040, TOOL-MIG-110.
- Requirements: TOOL-MIG-040, TOOL-MIG-110
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-MIG-04. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-05-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-MIG-05-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-MIG-05-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 7. WP-TRC-04
[WP-TRC-04] ReqIF export and external traceability tool interop  (board: CMP-TRC, phase P4, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TRC-04 (ReqIF export and external traceability tool interop) for requirements TOOL-TRC-070, TOOL-TRC-100.
- Requirements: TOOL-TRC-070, TOOL-TRC-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-TRC-03. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/verification/WP-TRC-04-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TRC-04-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TRC-04-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 8. WP-TRC-05
[WP-TRC-05] Source-element linking and requirement change detection  (board: CMP-TRC, phase P4, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TRC-05 (Source-element linking and requirement change detection) for requirements TOOL-TRC-080, TOOL-TRC-090.
- Requirements: TOOL-TRC-080, TOOL-TRC-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ANA-02, WP-TRC-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/verification/WP-TRC-05-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TRC-05-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TRC-05-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 9. WP-MIG-03
[WP-MIG-03] Interchange format documentation  (board: CMP-MIG, phase P2, 2 person-weeks)

- Estimate 100k tokens, hard cap 130k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-MIG-03 (Interchange format documentation) for requirements TOOL-MIG-100.
- Requirements: TOOL-MIG-100
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-REP-12, WP-TCM-06. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-03-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-MIG-03-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-MIG-03-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 10. WP-MIG-07
[WP-MIG-07] Migration assessment mode  (board: CMP-MIG, phase P4, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-MIG-07 (Migration assessment mode) for requirements TOOL-MIG-090.
- Requirements: TOOL-MIG-090
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-MIG-05. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-07-analysis.md`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-MIG-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-MIG-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 11. FIX-ANAGATE: Wire eligibility-gate reasons to the unsupported-construct inventory

- Estimate 90k tokens, hard cap 117k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: The PAR-140 inventory is now populated. Make the eligibility gate (src/ectt/ana/eligibility.py) report each unsupported construct from the inventory as a named reason instead of the generic 'unmodeled aspects' text. Do not touch PAR-080 (exposure; ADR-sensitive). Tests: one per construct kind, ordering deterministic, empty inventory unchanged.
- Allowed paths: `src/ectt/ana/`, `tests/ana/`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 12. TEST-MUT2: Mutation-style test strengthening for rep and trc

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. For src/ectt/rep and src/ectt/trc, hand-write mutants (flip a comparison, drop a branch, swap an ordering) in a temp copy, confirm the existing tests kill each, and add tests for any survivor. Report kill rate in docs/glm-night/overnight-20261120/mutation-rep-trc.md. No src/ edits.
- Allowed paths: `tests/rep/`, `tests/trc/`, `docs/glm-night/overnight-20261120/`, `docs/glm-night/overnight-20261120/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1735k tokens.
