# Overnight GLM queue, lane A (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-21a -b glm-night/20261121-a main
cd ../wt-night-21a
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` c559087): 3097 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261121/SECOND_PASS_A.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261121-a`.

## Hard rules
1. Never decide an owner decision. No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261121/SECOND_PASS_A.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261121/LANE_A_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. A1: Wire the build step: record compiled suites and load link plans

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Two integrations in src/ectt/bld: (1) call ectt.cbt record_compiled_suite from the build step and store the record in the project layout (SDD-003), and let reexecute_suite be used by the run_parallel/run_isolated callers in ectt.exh; (2) call ectt.ing.linkplan.load_link_plan from the harness-build step so a refused plan stops the build with its named reason. Stable ids plus content digests apply: D-02 Identity model (owner answer, 2026-11-19, memo option (a)): "Stable ids plus content digests". Tests: build with valid plan, refused plan stops build, re-execution without regeneration reuses the record, changed source invalidates it.
- Allowed paths: `src/ectt/bld/`, `tests/bld/`, `src/ectt/cbt/`, `tests/cbt/`, `src/ectt/ing/`, `tests/ing/`, `src/ectt/exh/`, `tests/exh/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. A2: Harness generator: stub setup and expectations, result stream, state reset

- Estimate 200k tokens, hard cap 260k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: From the second-pass lists of 11-20: wire render_stub_setup and render_stub_expectations into the harness generator and the result stream; make the framework back-end templates emit ectt_begin_test, ectt_end_test and ectt_fail; register ectt_stub_reset_all as a state reset. There is no C compiler on this machine, so verify by parsing the generated C (a C front end such as libclang) and by string-level golden tests; say so in the ledger. Tests: generated C parses without errors, output is byte-identical across two runs, a template with no stubs is unchanged.
- Allowed paths: `src/ectt/gen/`, `tests/gen/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. A3: Nested expected values: inputs, globals and struct return

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Extend nested path keys to inputs.globals (initial nested values) and to a struct return value (expected.return is a single string today). Keep older files valid and byte-stable. Tests: round trip, nested mismatch reported with its path, unknown member refused, old flat file unchanged.
- Allowed paths: `src/ectt/tcm/`, `tests/tcm/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. A4: Host profile and parity wiring

- Estimate 160k tokens, hard cap 208k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Implement TOOL-TGT-130: a versioned host profile recording the target-to-host derivation and ABI differences, with unmeasured differences explicitly 'unknown'; label every host-executed result with its profile; wire check_parity into run preparation; allow two result sets (host and target) to be passed to compare_outcomes. Do not run anything on hardware. Tests: profile is deterministic, unknown stays unknown, label present on results, parity check blocks a run with a named reason.
- Allowed paths: `src/ectt/ext/`, `tests/ext/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. A5: Generation run: connect the validation port and report marks

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Bind the generation run (ectt.atg) to a validation port that builds through ectt.bld and runs through ectt.exh using fakes in tests (no C compiler is available), so CoverageDelta.newly_covered is populated when the port reports coverage. Tests only use the fake port; say so in the ledger. Do not edit ectt.rep: list the renderer change needed in the second-pass file.
- Allowed paths: `src/ectt/atg/`, `tests/atg/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. A6: Mutation-style tests for gen, cbt and exh

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. For src/ectt/gen, src/ectt/cbt and src/ectt/exh, hand-write mutants (flip a comparison, drop a branch, swap an order) in a temp copy, confirm existing tests kill each, add tests for survivors. Write the kill rate to docs/glm-night/overnight-20261121/mutation-gen-cbt-exh.md. No src/ edits.
- Allowed paths: `tests/gen/`, `tests/cbt/`, `tests/exh/`, `docs/glm-night/overnight-20261121/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. A7: Seeded property-style tests for gen and atg

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random inputs for harness rendering (identifiers, escaping, long names), stub value rendering (no injection into generated C) and generation-run limits. No wall clock. No src/ edits.
- Allowed paths: `tests/gen/`, `tests/atg/`, `docs/glm-night/overnight-20261121/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1100k tokens.
