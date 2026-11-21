# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-b -b glm-night/20261121-b main
cd ../wt-night-b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` b393f0d): 3097 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261121/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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

### 2. B2: Exact range links for requirements using function extent

- Estimate 110k tokens, hard cap 143k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: After B1: make source-element links in ectt.trc resolve range links exactly using the new function extent, and keep approximate behaviour only for models without it. Tests: exact hit, boundary lines, model without extent still works.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. B3: Re-entrant safe-write transaction

- Estimate 100k tokens, hard cap 130k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Make OutputRoot.transaction in src/ectt/core/fs.py re-entrant (nested scopes join the outer one), then remove the private-attribute check in src/ectt/ana/persist.py that reads output_root._journal. Keep public names and error messages. Tests: nested commit, nested failure rolls back everything, cancellation inside nested scope.
- Allowed paths: `src/ectt/core/`, `tests/core/`, `src/ectt/ana/persist.py`, `tests/ana/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. B4: Report renderers show machine-generated and unreviewed marks

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Call report_marks and format_mark (from ectt.atg) in the ectt.rep renderers so reports show machine-generated and unreviewed marks. Import only the narrow function; do not make rep depend on the rest of atg. Tests: marked case shows mark, unmarked case unchanged, ordering deterministic.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. B5: Publish the interchange format reference

- Estimate 70k tokens, hard cap 91k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Write the output of render_format_reference() to docs/reference/interchange-format.md (generated by a small script in the same folder, with a test that the file matches the generator), and fix docs/verification/WP-MIG-01-analysis.md for the cmocka OK spelling. Allowed to create docs/reference/ only.
- Allowed paths: `src/ectt/mig/`, `tests/mig/`, `docs/reference/`, `docs/verification/WP-MIG-01-analysis.md`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. B6: Project.save integration of the sharded store

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Finish WP-PRJ-02: make Project.save able to write the sharded layout from ectt.prj.shards while the single-file manifest stays the default. Choose layout by an explicit argument only; no automatic switch. Tests: both layouts round-trip, unchanged save is byte-stable, interrupted save leaves the original.
- Allowed paths: `src/ectt/prj/`, `tests/prj/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. B7: Re-import SPEC-RELATIONS from ReqIF as associations

- Estimate 100k tokens, hard cap 130k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.trc, make import_reqif read SPEC-RELATIONS back as requirement-to-test associations, so export then import is lossless. Tests: round trip, dangling relation refused with a named reason, duplicate relation merged once.
- Allowed paths: `src/ectt/trc/`, `tests/trc/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 8. B8: Mutation-style tests for core, prj and mig

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. For src/ectt/core, src/ectt/prj and src/ectt/mig, hand-written mutants in a temp copy, confirm kills, add tests for survivors; kill rate in docs/glm-night/overnight-20261121/mutation-core-prj-mig.md. No src/ edits.
- Allowed paths: `tests/core/`, `tests/prj/`, `tests/mig/`, `docs/glm-night/overnight-20261121/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 9. B9: Seeded property-style tests for trc and rep

- Estimate 130k tokens, hard cap 169k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random inputs for the traceability matrix, ReqIF export and import round trip, and report merge. No wall clock. No src/ edits.
- Allowed paths: `tests/trc/`, `tests/rep/`, `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261121/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1130k tokens.
