# Overnight GLM queue, lane A (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-27a -b glm-night/20261127-a main
cd ../wt-night-27a
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` c1fd70e): 4026 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261127/LANE_A_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261127/SECOND_PASS_A.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261127-a`.

## Hard rules
1. Never decide an owner decision. Owner answers (2026-11-27), quoted: MC/DC is 'Masking + document gap'; a GCC older than 14 is 'Say not available' (run the other coverage, show MC/DC as unmeasured with the reason, and a configured MC/DC minimum fails); 'GCC only' (no Clang MC/DC). Compiler: 'Docker gcc:14'. A real GCC 14.4.0 is available ONLY as the local Docker image `gcc:14`: `MSYS_NO_PATHCONV=1 docker run --rm --network none -v <absolute temp dir>:/w gcc:14 sh -c '...'`. Never pull images, never install a compiler, never mount anything but a temp directory holding copies. If Docker is not running, say so in the ledger and work from the committed fixtures. The test suite must not need Docker: commit captured output as fixtures, with the commands used. Open: ADR-007, SRS-Q9, the ADR-005 record location, PR #4. Before using `xfail`, run the test without it and confirm it fails for the stated reason. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261127/SECOND_PASS_A.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261127/LANE_A_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. A1: Decision and condition extraction in the analysis model (schema 1.6)

- Estimate 220k tokens, hard cap 286k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: The model's decision inventory is hard-coded 'not_extracted'. Extract every boolean decision with its conditions in source order (file, line, column, expression text, owning function, macro-expansion flag) into decisions[], set status complete or partial honestly, bump the schema to 1.6 with a new schema file, and update every consumer that pins the version (search for 1.5; ectt.mig has a FormatSpec). Check on real source that GCC's condition order matches yours using Docker, on tests/cov/fixtures/gcc14/mcdc.c. Tests: a&&b, nested, repeated operand, macro condition, constant, ternary, loop conditions, older 1.5 documents still read. Write the analysis note to docs/verification/WP-ANA-08-decisions-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/ana/`, `src/ectt/mig/`, `tests/ana/`, `tests/mig/`, `docs/verification/WP-ANA-08-decisions-analysis.md`, `docs/glm-night/overnight-20261127/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. A2: MC/DC capability, version gate and build flags

- Estimate 170k tokens, hard cap 221k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.tch declare condition coverage as available for GCC 14 or newer only, with the probed maximum of 64 conditions recorded as run evidence (TOOL-COV-190: probed, not taken from documentation; give a probe function with an injected runner, and capture the real probe with Docker as a fixture). In ectt.bld add -fcondition-coverage to compile flags and --conditions to gcov only when MC/DC is requested and available. Older GCC: build the other coverage and return a named 'mcdc_not_available' reason. Tests: GCC 13 vs 14, flags present and absent, probe result recorded, probe failure is 'unknown', never a guessed number.
- Allowed paths: `src/ectt/tch/`, `src/ectt/bld/`, `tests/tch/`, `tests/bld/`, `docs/glm-night/overnight-20261127/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. A3: Compile the generated harnesses and stubs with a real compiler

- Estimate 220k tokens, hard cap 286k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Generated C has only ever been parsed. Generate harnesses and stubs for a few representative units (scalars, structs, arrays, file statics, function pointers, GoogleTest excluded), compile, link and run them with Docker gcc:14 using -Wall -Wextra -Werror, and fix the generator bugs this exposes. Add golden-text tests for each fix and record the compile commands and results in the analysis note. Unity or cmocka sources that are not in the repository must not be downloaded: use a minimal local stand-in header for compile checks and say so. Write the analysis note to docs/verification/WP-GEN-compile-check-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-compile-check-analysis.md`, `docs/glm-night/overnight-20261127/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. A4: Export bindings left over from earlier runs

- Estimate 70k tokens, hard cap 91k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: docs/glm-night/overnight-20261123/SECOND_PASS_B.md lists missing public exports in ectt.ana, ectt.ing and ectt.tcm. Add them and a public-surface guard test per package. No behaviour change.
- Allowed paths: `src/ectt/ing/`, `src/ectt/tcm/`, `src/ectt/ana/`, `tests/ing/`, `tests/tcm/`, `tests/ana/`, `docs/glm-night/overnight-20261127/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. A5: Mutation and seeded tests for decision extraction and the MC/DC gate

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Hand-written mutants in a temp copy of the new ana, tch and bld code; add tests for survivors; seeded random boolean expressions: extracted condition count and order match the generator. Report to docs/glm-night/overnight-20261127/mutation-ana-tch-bld.md. No src/ edits.
- Allowed paths: `tests/ana/`, `tests/tch/`, `tests/bld/`, `docs/glm-night/overnight-20261127/`, `docs/glm-night/overnight-20261127/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261127/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 820k tokens.
