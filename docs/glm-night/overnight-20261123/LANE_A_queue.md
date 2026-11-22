# Overnight GLM queue, lane A (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-23a -b glm-night/20261123-a main
cd ../wt-night-23a
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` b8ae29f): 3710 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261123/SECOND_PASS_A.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261123-a`.

## Hard rules
1. Never decide an owner decision. No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261123/SECOND_PASS_A.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261123/LANE_A_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. A1: WP-QUA-03: user-executable validation suite

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.qua add a validation suite a user can run on their own machine to check the tool works: a list of self-checks (each with an id, what it proves, how long it takes), a runner that executes them with fake or bundled inputs only (no network, no compiler needed), and a result record with pass, fail or not-run with a named reason. A check that needs a missing tool is not-run, never pass. Tests: all pass, one fails, one not-run, result record byte-stable. Write the analysis note to docs/verification/WP-QUA-03-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-03-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. A2: WP-QUA-04: known error list per release

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.qua add a known-error list model: entries with id, summary, affected versions, workaround, status (open, fixed in X), loaded from a plain-text data file, validated (duplicate ids, a fixed-in version not after the introduced version, missing workaround for an open entry are refused with named reasons), and a query that returns what applies to a given release. Tests for each refusal and the query. Write the analysis note to docs/verification/WP-QUA-04-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-04-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. A3: WP-SEC-01: Software Bill of Materials generation

- Estimate 180k tokens, hard cap 234k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.sec add SBOM generation: read the installed Python package metadata (name, version, licence, hashes where recorded) of the tool and its dependencies and write a CycloneDX 1.5 JSON document, sorted and byte-stable (no timestamps unless injected). Release signing needs keys the owner holds: do NOT implement signing; add a named 'signing_not_configured' result and record it as a second-pass row. Take field names from the CycloneDX 1.5 specification, not memory, and say in the ledger which source you used. Tests: stable output, missing licence reported as unknown, sort order. Write the analysis note to docs/verification/WP-SEC-01-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-01-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. A4: WP-SEC-02: pinned dependency integrity check

- Estimate 140k tokens, hard cap 182k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.sec add a checker that compares the installed packages with a pinned lock file (name, exact version, hash) and reports each difference by name: missing, extra, wrong version, wrong hash, unpinned. Read only; it never installs anything. Do not edit pyproject.toml. Tests: clean match, each difference kind, malformed lock file refused. Write the analysis note to docs/verification/WP-SEC-02-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-02-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. A5: WP-SEC-06: restricted execution context for harnesses

- Estimate 170k tokens, hard cap 221k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.exh add a restricted run context for starting a generated harness: confined working directory, scrubbed environment (only an allow-list passes), no inherited handles, a wall-clock limit and an output size limit, all recorded in the result. There is no C compiler, debugger or simulator on this machine: test by parsing, golden text and fake callables only, and say so in the ledger. Test with a fake process starter that records what it was given. Tests: environment scrub, directory confinement refuses a path escape, limits recorded, a refused context starts nothing. Write the analysis note to docs/verification/WP-SEC-06-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/exh/`, `tests/exh/`, `docs/verification/WP-SEC-06-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. A6: WP-EXH-04: debugger launch with entry breakpoint

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.exh build the debugger command line for a built test harness: gdb first, with a breakpoint at the test function entry, the working directory and arguments as the normal run uses. Only build and return the command (argv list) and the refusal reasons (debugger not named, no symbols recorded, harness not built); starting the debugger is behind an injected starter. There is no C compiler, debugger or simulator on this machine: test by parsing, golden text and fake callables only, and say so in the ledger. Tests: argv golden text, each refusal, quoting of paths with spaces. Write the analysis note to docs/verification/WP-EXH-04-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/exh/`, `tests/exh/`, `docs/verification/WP-EXH-04-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. A7: WP-CORE-08: self-verification of the tool's own source

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.core add a self-verification check: a manifest of the SHA-256 of every file in the installed ectt package, a function that writes it and one that verifies the installed tree against it, naming each changed, missing and unexpected file. Ignore __pycache__. Do not commit a manifest generated from this tree as a fixed file; tests build their own temp trees. Tests: clean, changed, missing, extra, manifest tampered. Write the analysis note to docs/verification/WP-CORE-08-analysis.md in the same style as the existing notes there.
- Allowed paths: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-08-analysis.md`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 8. A8: Mutation-style tests for qua, sec and exh

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Hand-written mutants in a temp copy of src/ectt/qua, src/ectt/sec and src/ectt/exh (include the new modules from items A1 to A6); confirm existing tests kill each; add tests for survivors. Kill rate to docs/glm-night/overnight-20261123/mutation-qua-sec-exh.md. Reuse docs/glm-night/overnight-20261122/mutation_runner.py as a starting point (copy it, do not edit the original). No src/ edits.
- Allowed paths: `tests/qua/`, `tests/sec/`, `tests/exh/`, `docs/glm-night/overnight-20261123/`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 9. A9: Seeded property-style tests for qua, sec and core

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random inputs: known-error list validation order independence, SBOM output stable under input order, lock-file checker symmetry, self-verification manifest round trip. No wall clock. No src/ edits.
- Allowed paths: `tests/qua/`, `tests/sec/`, `tests/core/`, `docs/glm-night/overnight-20261123/LANE_A_LEDGER.md`, `docs/glm-night/overnight-20261123/SECOND_PASS_A.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1330k tokens.
