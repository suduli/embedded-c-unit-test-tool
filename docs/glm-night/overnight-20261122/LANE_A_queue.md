# Overnight GLM queue, lane A (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-22a -b glm-night/20261122-a main
cd ../wt-night-22a
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` e5184df): 3558 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261122/SECOND_PASS_A.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261122-a`.

## Hard rules
1. Never decide an owner decision. No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261122/SECOND_PASS_A.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261122/LANE_A_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. A1: Production composition point for the generation run

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Create src/ectt/cli/compose.py: one function that binds ectt.atg BoundValidationPort's build and execute delegates to ectt.bld.build_harness_suite and ectt.cbt.reexecute_isolated (atg must not import them itself: layer rule DSN-ATG-110). Tests with fake build and execute callables: binding order, a build refusal stops the run with its named reason, a refused link plan stops the run. No real compiler is used.
- Allowed paths: `src/ectt/cli/`, `tests/cli/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. A2: Harness generation: reach file-static data and emit externs

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Finish the WP-GEN-01 remainder (HAR-040). The analysis model (schema 1.5) now records global variable types and initial-value presence. Use it so the generated harness can read and set file-static variables and emits extern declarations where the variable is visible. Read the model only; do not edit ectt.ana. There is no C compiler on this machine: check generated C by parsing and golden text only, and say so in the ledger. Tests: golden C text for scalar, struct and array globals; a global whose type is not recorded is reported as not reachable with a named reason, never guessed.
- Allowed paths: `src/ectt/gen/`, `tests/gen/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. A3: Map a source diff to the construct identities coverage data uses

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.cbt, add a function that takes a source change (old and new file digests plus changed line ranges) and returns the affected construct identities that ectt.cov data uses, so change impact can pick the right subset. Use the function extents recorded in analysis model 1.5. Tests: change inside one function, change between functions, whole-file change, model without extents (falls back to whole file with a named note).
- Allowed paths: `src/ectt/cbt/`, `tests/cbt/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. A4: CLI commands for impact, subset run, comparison and minimization

- Estimate 200k tokens, hard cap 260k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Add four commands to the catalogue-generated CLI (ectt.cli): affected set and subset run (ectt.cbt.impact, reexecute_subset), compare two runs and their coverage (compare_runs, compare_coverage), and minimize a suite (minimize_suite). Each prints through the report views from lane B item B2 and uses the stable exit codes. Tests: each command happy path, a missing input gives the usage exit code, JSON output is byte-stable.
- CROSS-LANE DEPENDENCY on item `B2` (lane B, worktree `../wt-night-22b`). Before starting: look at `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md` there for a B2 row that is DONE. If so: `git merge --no-edit glm-night/20261122-b`, run the full gate; if red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: skip it now, retry once after the last item, then record `SKIPPED (dep)` in the ledger and the second-pass file.
- Allowed paths: `src/ectt/cli/`, `tests/cli/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. A5: Host profile label and parity-gated run preparation in the CLI

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Wire the host profile (ectt.ext) into the CLI run preparation: check_parity runs first and a failure stops the run with its named reason; every host-executed result is labelled with its profile. Hardware is not available, so no target run. Tests: parity failure blocks, unknown ABI differences show as unknown, label on every result.
- CROSS-LANE DEPENDENCY on item `B2` (lane B, worktree `../wt-night-22b`). Before starting: look at `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md` there for a B2 row that is DONE. If so: `git merge --no-edit glm-night/20261122-b`, run the full gate; if red, `git revert -m 1 HEAD` and treat as not satisfied. If not satisfied: skip it now, retry once after the last item, then record `SKIPPED (dep)` in the ledger and the second-pass file.
- Allowed paths: `src/ectt/cli/`, `tests/cli/`, `src/ectt/ext/`, `tests/ext/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. A6: Mutation-style tests for cli, atg and ext

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Hand-written mutants (flip a comparison, drop a branch, swap an order) in a temp copy of src/ectt/cli, src/ectt/atg and src/ectt/ext; confirm existing tests kill each; add tests for survivors. Kill rate to docs/glm-night/overnight-20261122/mutation-cli-atg-ext.md. No src/ edits.
- Allowed paths: `tests/cli/`, `tests/atg/`, `tests/ext/`, `docs/glm-night/overnight-20261122/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. A7: Seeded property-style tests for bld, cbt and gen

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random inputs: build planning order independence, re-execution record round trip, impact sets under random changes, generated C identifier and escape safety. No wall clock. No src/ edits.
- Allowed paths: `tests/bld/`, `tests/cbt/`, `tests/gen/`, `docs/glm-night/overnight-20261122/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1060k tokens.
