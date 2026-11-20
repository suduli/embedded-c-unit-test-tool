# Tonight's plan (2026-11-20)

Last night: 29 tasks finished in two lanes and merged into local `main` (commit f044ef1). All checks pass: 1457 tests, ruff, mypy, plan_check, trace_check. Nothing is pushed.

## What to do
1. Open two GLM (ZAI) chats, Chat A and Chat B.
2. Paste into Chat A the whole file `docs/glm-night/overnight-20261120/LANE_A_queue.md`.
3. Paste into Chat B the whole file `docs/glm-night/overnight-20261120/LANE_B_queue.md`.
4. Sleep. Both stop by themselves at 05:30.

## What each chat does
- Chat A (9 tasks): finish the 4 tasks left from last night (suite re-run, generated-case lifecycle, test derivation, stub behaviour), then fix the gaps lane A noted (harness result output, nested expected values), two more packages, and extra tests.
- Chat B (12 tasks): fix report merge loading, make saves safe against cancellation, add the Linux CI job, then migration import tools (Ceedling, CSV, fidelity, assessment), traceability export and linking, and extra tests.

## Tasks left out, and why
See `docs/glm-night/overnight-20261120/DEFERRED.md` (101 items). Main reasons: waiting on your open decisions (49), GUI work that needs a person to look at it (16), AI-provider work held by PR #4 (13), needs real hardware or toolchains (7), needs an owner decision (8), partial with a rest that cannot run unattended (8).

## Your own to-do list (GLM cannot do these)
- Read `SECOND_PASS_A.md` and `SECOND_PASS_B.md` in `docs/glm-night/overnight-20261119/`: mostly document edits (PLAN-001 acceptance criteria, SRS wording) only you may approve.
- Decide: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9. These hold about 49 tasks.
- Apply D-01 (licence), D-03 and D-04 wording to the official files when ready.
