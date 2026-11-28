# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-27b -b glm-night/20261127-b main
cd ../wt-night-27b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` 3be82a9): 4064 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261127/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261127/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261127-b`.

## Hard rules
1. Never decide an owner decision. Owner answers (2026-11-27), quoted: MC/DC is 'Masking + document gap'; a GCC older than 14 is 'Say not available' (run the other coverage, show MC/DC as unmeasured with the reason, and a configured MC/DC minimum fails); 'GCC only' (no Clang MC/DC). Compiler: 'Docker gcc:14'. A real GCC 14.4.0 is available ONLY as the local Docker image `gcc:14`: `MSYS_NO_PATHCONV=1 docker run --rm --network none -v <absolute temp dir>:/w gcc:14 sh -c '...'`. Never pull images, never install a compiler, never mount anything but a temp directory holding copies. If Docker is not running, say so in the ledger and work from the committed fixtures. The test suite must not need Docker: commit captured output as fixtures, with the commands used. Already on main, build on it and do not rebuild: analysis model schema 1.6 `AnalysisUnit.decisions` (ectt.ana, each condition has `constant` and `negated`); `ectt.tch.plan_mcdc` and `probe_condition_limit`; `ectt.cov.measure_mcdc` returning `McdcResult` (decisions, unmeasured with reasons). Read docs/verification/WP-COV-05-analysis.md first. Open: ADR-007, SRS-Q9, the ADR-005 record location, PR #4. Before using `xfail`, run the test without it and confirm it fails for the stated reason. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261127/SECOND_PASS_B.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261127/LANE_B_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. B2: WP-COV-05: finish the known-answer MC/DC corpus

- Estimate 160k tokens, hard cap 208k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: TOOL-COV-210: a corpus of small C cases with HAND-COMPUTED expected results (a&&b independence matrix, nested, repeated and coupled operands, side-effecting operand not evaluated, macro condition, constant decision, a masking versus unique-cause divergent case with the difference written down). Write the expected values before running; then capture real gcov output with Docker and compare through `measure_mcdc`. A disagreement is a finding: explain it, never edit the expectation just to match. Also run the cases at -O2 and report any difference in condition direction or record placement (only -O0 has been checked). Real output samples are in tests/cov/fixtures/gcc14/ (see its README): in a condition record `count` is two outcomes per condition; 64 conditions are measured, 65 give no records. `seen_true` / `seen_false` mean the condition was SHOWN TO DECIDE the outcome with that value; False never means it never had that value; None means the direction is unknown. GCC reports conditions under `!` inverted (already undone in ectt.cov).
- Allowed paths: `tests/cov/`, `docs/glm-night/overnight-20261127/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. B6: End-to-end coverage check on real GCC output

- Estimate 160k tokens, hard cap 208k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: With Docker, build several small programs with coverage, run them one or more times, and check the reader, merge, metrics and thresholds against hand-counted statement and branch results (headers included from two files, templates not needed, a crashed run excluded). Commit the captured output as fixtures; fix bugs in ectt.cov. Also fix the three report observations in the 11-23 SECOND_PASS_B only if they are in ectt.rep.
- Allowed paths: `src/ectt/cov/`, `src/ectt/rep/`, `tests/cov/`, `tests/rep/`, `docs/glm-night/overnight-20261127/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. B4: MC/DC thresholds and project configuration

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Add an 'mcdc' metric to coverage thresholds and the project thresholds section. A configured MC/DC minimum FAILS when MC/DC is unavailable or unmeasured, unless the project explicitly allows not-applicable. Existing files without it keep working.
- Allowed paths: `src/ectt/cov/`, `src/ectt/prj/`, `tests/cov/`, `tests/prj/`, `docs/glm-night/overnight-20261127/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. B5: WP-REP-04 and WP-COV-10: MC/DC report detail and the documented gap

- Estimate 220k tokens, hard cap 286k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.rep render per-decision condition detail from `McdcResult` in the HTML report (TOOL-REP-050); never word a False as 'was never true' (say 'not shown'), show None as 'unknown'; state form and mechanism in every report that carries coverage (TOOL-COV-060). Write docs/user/mcdc.md (DRAFT) stating precisely how masking MC/DC differs from unique-cause, with the corpus case that shows it (TOOL-COV-090). Do not claim any certification authority accepts masking MC/DC: that is unchecked. Update the certification report's not-claimed list so MC/DC is claimed only when measured data is present, and never unique-cause. Real output samples are in tests/cov/fixtures/gcc14/ (see its README): in a condition record `count` is two outcomes per condition; 64 conditions are measured, 65 give no records. `seen_true` / `seen_false` mean the condition was SHOWN TO DECIDE the outcome with that value; False never means it never had that value; None means the direction is unknown. GCC reports conditions under `!` inverted (already undone in ectt.cov). Write the analysis note to docs/verification/WP-REP-04-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/user/`, `docs/verification/WP-REP-04-analysis.md`, `docs/glm-night/overnight-20261127/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. B7: Mutation and seeded tests for the MC/DC code

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Hand-written mutants in a temp copy of the new cov and rep code; add tests for survivors; seeded random condition records: merge is order independent and never raises covered above count. Report to docs/glm-night/overnight-20261127/mutation-mcdc.md. No src/ edits.
- Allowed paths: `tests/cov/`, `tests/rep/`, `docs/glm-night/overnight-20261127/`, `docs/glm-night/overnight-20261127/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 790k tokens.
