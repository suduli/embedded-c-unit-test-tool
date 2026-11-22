# Overnight GLM queue, lane B (generated; do not edit, regenerate)

You are an unattended executor on the ZAI harness. No human will answer. For any ambiguity, take the most conservative reading, write the assumption in the ledger, continue.

## Setup (once)
```
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-night-22b -b glm-night/20261122-b main
cd ../wt-night-22b
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
```
Baseline at the branch point (local `main` e5184df): 3558 passed, 6 skipped; ruff, mypy, plan_check, trace_check all clean. Create `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md` with header `| item | state | commit | est tokens | cumulative | notes |` if missing, and `docs/glm-night/overnight-20261122/SECOND_PASS_B.md` with header `| item | what is needed | why it needs a human | where |`.

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
`git add <only paths the item allows>`; `git commit -m "[GLM-NIGHT] <item>: <summary, 70 chars max>"` with body (what, how verified, files) ending `Co-Authored-By: GLM Agent <noreply@example.com>`. Never `git add -A`, never push, never amend, never force, never `--no-verify`. Work only on `glm-night/20261122-b`.

## Hard rules
1. Never decide an owner decision. No C compiler is installed on this machine: generated C is checked by parsing only. Open: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9, PR #4. Answered decisions are quoted verbatim inside the items that use them.
2. Do not edit `SRS-001-requirements.md`, ADR files, `LICENSE`, `LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/`, `spikes/`, `pyproject.toml`, `EXEC-PLAN-001-*`, `PLAN-001-*`, or the other lane's ledger. No item may edit `design/`.
3. Never copy code, strings or identifiers from `vcast-findings/` into `src/`.
4. No PR or issue writes, no board writes, no network from product code or tests, no new runtime dependencies, no secrets.
5. Never delete or weaken tests or gates. A real failure you cannot fix: `xfail(strict=True, reason=...)` plus a ledger note.
6. Each lane owns its `src/ectt/<pkg>/` and `tests/<pkg>/` for the packages named in its items. Never touch the other lane's packages.

## Blockers never stop the run
If an item needs a human (decision, review, hardware, missing input, unresolvable ambiguity): do not wait. Write NO code for the blocked part, append a row to `docs/glm-night/overnight-20261122/SECOND_PASS_B.md` (what is needed, why), mark the ledger row `SECOND-PASS` (or PARTIAL if an increment landed), `git restore` only your own uncommitted edits, and start the next item. Dependents become `SKIPPED (dep)`.

## Budget and clock
- Items are in priority order; estimates are rough. Keep a running cumulative estimate in the ledger (use the ZAI usage counter if available).
- Per-item hard cap is stated in each item (1.3 x estimate). At the cap or after 3 failed gate attempts: PARTIAL, commit what is green, move on.
- Stop starting new items when the ZAI usage counter shows your lane has used 1,450k tokens (if there is no counter, ignore this token limit) OR the local time reaches 05:30, whichever comes first. If you run out of items before then, stop and write the summary.
- Then finish the current item, write `docs/glm-night/overnight-20261122/LANE_B_SUMMARY.md` (counts per state, every PARTIAL/SKIPPED/SECOND-PASS with reason, shared-file changes needed, final gate output), commit it, stop.

## Queue
### 1. B2: Report views for re-execution results and thresholds

- Estimate 200k tokens, hard cap 260k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: In ectt.rep add report views for: a subset run (state that the suite was only partly run, from suite_view data), a run comparison with its coverage delta and removed tests, a minimized suite (kept versus redundant and the preserved union), the host profile label on results, and coverage threshold results including the new no_data state (shown as a failure). Import only the narrow data classes from ectt.cbt, ectt.ext and ectt.cov. Tests: each view, no_data shown as failed, output deterministic. Other lanes call these views, so keep the function names stable and list them in docs/verification/WP-REP-views-analysis.md.
- Allowed paths: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-views-analysis.md`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 2. B1: Make the coverage merge independent of input order

- Estimate 80k tokens, hard cap 104k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Review finding: in src/ectt/cov/merge.py, _merge_documents takes data_file from the first admitted run in INPUT order, so the same runs merged in another order give a different aggregate. Make the merged provenance field order-independent (for example the sorted list of all data files). Counts must not change. Tests: all permutations of three runs give byte-identical merged output; a single run is unchanged.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 3. B3: Coverage threshold configuration in the project store

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Let a project configure coverage thresholds (statements, branches) and the allow_not_applicable list, stored in the project data format as exact fractions, and loaded into ectt.cov.MetricThreshold. Do not change existing file formats: this is an optional new section, absent means no thresholds. Tests: round trip, a float is refused, an unknown metric is refused, absent section is no-op.
- Allowed paths: `src/ectt/prj/`, `tests/prj/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 4. B6: Coverage reader checks against more GCC cases

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Extend tests/cov with hand-written gcov JSON fixtures for cases real GCC produces: template and inline functions seen in several files, a file with only declarations, lines with unexecuted blocks, throw branches, version 1 and version 2 documents. Take key names from the GCC gcov documentation, not memory. Fix reader bugs these expose (src/ectt/cov only). Say in the ledger that real GCC output is still unchecked.
- Allowed paths: `src/ectt/cov/`, `tests/cov/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 5. B4: Draft the user documentation pages

- Estimate 220k tokens, hard cap 286k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: From the WP-CORE-07 documentation index (find it in src/ectt/core and docs/verification/WP-CORE-07-analysis.md) write the missing docs/user/ pages as DRAFTS. Mark each page DRAFT at the top. Describe only what exists in the code today (check each command or option exists); mark anything planned as 'not yet available'. Add a test that every page in the index exists and every command it names is real.
- Allowed paths: `docs/user/`, `src/ectt/core/`, `tests/core/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 6. B5: Draft SECURITY.md

- Estimate 60k tokens, hard cap 78k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: From the WP-SEC-05 policy (src/ectt/sec and its verification note) write a DRAFT security disclosure policy at docs/proposals/SECURITY-draft.md, ready for the owner to copy to the repository root. Do not create SECURITY.md at the root. Do not invent contact addresses: use the placeholder OWNER-CONTACT-REQUIRED.
- Allowed paths: `docs/proposals/SECURITY-draft.md`, `tests/sec/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 7. B7: Mutation-style tests for cov and rep

- Estimate 150k tokens, hard cap 195k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Hand-written mutants in a temp copy of src/ectt/cov and src/ectt/rep; confirm kills; add tests for survivors. Kill rate to docs/glm-night/overnight-20261122/mutation-cov-rep.md. No src/ edits.
- Allowed paths: `tests/cov/`, `tests/rep/`, `docs/glm-night/overnight-20261122/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

### 8. B8: Seeded property-style tests for cov thresholds and rep views

- Estimate 120k tokens, hard cap 156k, or 3 failed gate attempts, then PARTIAL and move on.
- Goal: Tests only. Fixed-seed random metric totals against thresholds (exact fractions, boundary values, no_data), and random run sets through the new rep views. No wall clock. No src/ edits.
- Allowed paths: `tests/cov/`, `tests/rep/`, `docs/glm-night/overnight-20261122/LANE_B_LEDGER.md`, `docs/glm-night/overnight-20261122/SECOND_PASS_B.md`. Anything else: do not edit; write the needed change in the second-pass file.
- Done when: tests pass (happy path plus at least two error cases), full gate green, one commit, one ledger row.

## End
Listed total 1100k tokens.
