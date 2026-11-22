# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-23b -b glm-night/20261123-b main
cd ../wt-night-23b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` b8ae29f): 3710 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261123/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261123-b`.

## Hard rules
1. Never decide an owner decision. No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261123/SECOND_PASS_B.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261123/LANE_B_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. B1: WP-REP-05: certification verification report and scope statement

- Estimate 200k tokens, hard cap 260k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.rep add a certification verification report built from existing result, coverage and trace data: the tool version, the unit and scope, what was run, coverage achieved against the stated criteria, which items are unmeasured or not applicable, and an explicit scope statement of what the report does NOT claim (no MC/DC, no target execution unless the data says so). Missing data is stated as missing, never filled. Import only narrow data classes from other packages. Tests: complete data, each missing input named, byte-stable output, a claim not supported by data is refused. Write the analysis note to docs/verification/WP-REP-05-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-05-analysis.md`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. B2: WP-COV-06: uninstrumentable expression detection

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.cov add detection of expressions the compiler coverage backend cannot instrument (for example constant conditions, short-circuit forms folded away, macro expanded conditions), working from the analysis model's decision inventory (schema 1.5) and the gcov data. Result: a list of construct identities with a named reason each. A construct with no coverage data and no reason is 'no_data', not 'uninstrumentable'. Read the model only; do not edit ectt.ana. Write the analysis note to docs/verification/WP-COV-06-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-06-analysis.md`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. B3: WP-COV-11: control coupling and data coupling analysis

- Estimate 200k tokens, hard cap 260k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.cov add control coupling (which function calls were exercised by the tests, from the call graph in the analysis model and function-call coverage) and data coupling (which global variables are written by one function and read by another, from the global inventory in schema 1.5, and whether tests exercised both sides). Report per pair: exercised, not exercised, or not determinable with the reason. Do not claim a standard's objective is met; report data only. Tests: simple chain, unexercised call, global with no recorded access (not determinable), byte-stable output. Write the analysis note to docs/verification/WP-COV-11-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-11-analysis.md`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. B4: Report output robustness: HTML escaping and size limits

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Review ectt.rep HTML and XML outputs (HTML report, JUnit, Cobertura, LCOV): test that hostile text in test names, source lines and messages (markup, quotes, control characters, very long lines, non-UTF-8 bytes) is escaped or refused with a named reason and never breaks the document structure. Fix bugs found in src/ectt/rep only. Tests: one per output format per hostile input class.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. B5: Interchange round-trip checks for coverage and results

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: For the REP-10 and REP-02 formats, test export then import gives the same data, and that imports of hand-written files in the styles real tools produce (take structure from the public format descriptions, name the source in the ledger) are read correctly or refused with a named reason. Fix bugs in src/ectt/rep only. Say in the ledger that files from real tools are still unchecked.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. B6: Mutation-style tests for trc, mig and prj

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Hand-written mutants in a temp copy of src/ectt/trc, src/ectt/mig and src/ectt/prj; confirm kills; add tests for survivors. Kill rate to docs/glm-night/overnight-20261123/mutation-trc-mig-prj.md. Reuse docs/glm-night/overnight-20261122/mutation_runner.py as a starting point (copy it). No src/ edits.
- Allowed paths: `tests/trc/`, `tests/mig/`, `tests/prj/`, `docs/glm-night/overnight-20261123/`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. B7: Seeded property-style tests for cov coupling, rep report and trc

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random inputs: coupling analysis order independence, certification report stable under input order, trace matrix symmetry (requirement to test and test to requirement agree). No wall clock. No src/ edits. Run after items B1 and B3 exist.
- Allowed paths: `tests/cov/`, `tests/rep/`, `tests/trc/`, `docs/glm-night/overnight-20261123/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1160k tokens.
