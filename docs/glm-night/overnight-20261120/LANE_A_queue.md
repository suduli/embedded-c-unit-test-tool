# Overnight GLM queue, lane A (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-a -b glm-night/20261120-a main
cd ../wt-night-a
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` f044ef1): 1457 passed, 5 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261120/SECOND_PASS_A.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261120-a`.

## Hard rules
1. Never decide an owner decision. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261120/SECOND_PASS_A.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. Last night the estimates ran high, so expect to finish the whole list. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261120/LANE_A_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. WP-CBT-01
[WP-CBT-01] Suite re-execution without regeneration  (board: CMP-CBT, phase P2, 2 person-weeks)

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-CBT-01 (Suite re-execution without regeneration) for requirements TOOL-CBT-010.
- Requirements: TOOL-CBT-010
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests". Also satisfy the run-integrity acceptance of T-14 (EXEC-PLAN-001 section 7.4, card T-14). It was waiting on D-02, which is now answered.
- Allowed paths: `src/ectt/cbt/`, `tests/cbt/`, `docs/verification/WP-CBT-01-analysis.md`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-CBT-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-CBT-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 2. WP-ATG-01
[WP-ATG-01] Validation port and generated-case lifecycle  (board: CMP-ATG, phase P3, 4 person-weeks)

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-ATG-01 (Validation port and generated-case lifecycle) for requirements TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080.
- Requirements: TOOL-ATG-040, TOOL-ATG-050, TOOL-ATG-070, TOOL-ATG-080
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/atg/`, `tests/atg/`, `docs/verification/WP-ATG-01-analysis.md`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-ATG-01-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-ATG-01-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 3. WP-TCM-07
[WP-TCM-07] Boundary, equivalence and classification-tree derivation  (board: CMP-TCM, phase P3, 5 person-weeks)

- Estimate 205k tokens, hard cap 266k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-TCM-07 (Boundary, equivalence and classification-tree derivation) for requirements TOOL-TCD-110, TOOL-TCD-120.
- Requirements: TOOL-TCD-110, TOOL-TCD-120
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ANA-02, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-07-analysis.md`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-TCM-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-TCM-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 4. WP-GEN-07
[WP-GEN-07] Stub behaviour programming  (board: CMP-GEN, phase P2, 5 person-weeks)

- Estimate 205k tokens, hard cap 266k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-GEN-07 (Stub behaviour programming) for requirements TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070.
- Requirements: TOOL-STB-040, TOOL-STB-050, TOOL-STB-060, TOOL-STB-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-GEN-06, WP-TCM-02. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Decision text (do NOT re-decide; implement it as written): D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests".
- Allowed paths: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-07-analysis.md`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-GEN-07-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-GEN-07-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 5. FIX-GENPROTO: Harness emits the run-result stream and resets state in the setup hook

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: From SECOND_PASS_A.md: make generated harnesses emit the RESULT/FAILURE stream protocol defined in docs/verification/WP-EXH-01-analysis.md, and reset harness state in the setup hook (DSN-TCM-060). Tests: generated harness output parses with the WP-EXH-01 normaliser; state from one test never leaks into the next.
- Allowed paths: `src/ectt/gen/`, `tests/gen/`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. FIX-TCMNEST: Nested struct, array and union expectations in test case files

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: From SECOND_PASS_A.md: extend the WP-TCM-02 model and the .tests restricted-YAML form so expected values for struct, array and union can be authored, and make the WP-TCM-03 comparison engine consume them. Keep existing flat files valid and byte-stable. Tests: round trip, nested mismatch reported with a path, unknown member refused.
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. WP-ATG-05
[WP-ATG-05] Generation reporting, bounds and capability limits  (board: CMP-ATG, phase P3, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-ATG-05 (Generation reporting, bounds and capability limits) for requirements TOOL-ATG-060, TOOL-ATG-100, TOOL-ATG-110.
- Requirements: TOOL-ATG-060, TOOL-ATG-100, TOOL-ATG-110
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-ATG-01. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/atg/`, `tests/atg/`, `docs/verification/WP-ATG-05-analysis.md`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-ATG-05-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-ATG-05-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 8. WP-EXT-04
[WP-EXT-04] Host and target test parity  (board: CMP-EXT, phase P3, 3 person-weeks)

- Estimate 155k tokens, hard cap 201k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement WP-EXT-04 (Host and target test parity) for requirements TOOL-TGT-070.
- Requirements: TOOL-TGT-070
- Acceptance criteria (board): **No package-specific acceptance criterion is recorded in PLAN-001 §5.4 for this package yet — flagged for reconciliation.** Write falsifiable, reviewable criteria before moving this item to Ready.
- Dependencies: WP-EXH-01, WP-EXT-03. Items already implemented are in the repo; items earlier in this queue must be DONE or PARTIAL in your ledger first.
- Allowed paths: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-04-analysis.md`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else (design/, SRS, ADRs, tracker, pyproject, other packages): do not edit; write the needed change in the second-pass file.

Steps:
1. RECON: derive falsifiable acceptance criteria from the PLAN-001 section 5.4 row and the SRS text; write them under `## Acceptance criteria` in `docs/verification/WP-EXT-04-analysis.md` before code. If they cannot be derived without inventing scope, SKIPPED with reason `no derivable AC`.
2. Implement the smallest increment that meets the criteria with tests: happy path plus at least two error/edge cases; deterministic output; no network; no wall-clock in outputs.
3. Write or update `docs/verification/WP-EXT-04-analysis.md` (requirement -> implementation -> real test names). Mark anything uncovered as not covered.
4. Run the gate block. Commit with the commit block. Append one ledger row. Next item.

### 9. TEST-PROP-TCM: Seeded property-style tests for tcm and exh

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Deterministic seeded random inputs for the CSV interchange round trip, range expansion and suite selection expressions (tcm), and result-record normalisation (exh). Fixed seeds, no wall clock. No src/ edits.
- Allowed paths: `tests/tcm/`, `tests/exh/`, `docs/glm-night/overnight-20261120/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261120/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1510k tokens.
