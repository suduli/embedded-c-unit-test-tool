# Plan to run now (2026-11-22)

Everything from the last two nights is merged into local `main`. All checks pass: 3558 tests, ruff, mypy, plan_check, trace_check. The coverage threshold fix is in. Nothing is pushed.

## What to do
1. Open two GLM (ZAI) chats, Chat A and Chat B.
2. Paste into Chat A the whole file `docs/glm-night/overnight-20261122/LANE_A_queue.md`.
3. Paste into Chat B the whole file `docs/glm-night/overnight-20261122/LANE_B_queue.md`.
4. Both stop by themselves at 05:30, or earlier when their list is done.

## What each chat does
- Chat A (7 tasks): connect the finished pieces to the command line (generation run, impact, subset runs, comparison, minimization, host profile), reach file-level variables in generated harnesses, map source changes to coverage items, extra tests. The CLI items wait for Chat B's report views (item B2) and skip themselves if not ready.
- Chat B (8 tasks): report views for the new results first, then a fix so coverage merge does not depend on input order, coverage thresholds in project settings, more GCC coverage test cases, DRAFT user documentation pages, a DRAFT security policy, extra tests.

## Notes
- No C compiler here: generated C and coverage code are tested on hand-written samples only. Run it once on a machine with GCC.
- Still held: MC/DC (SRS-Q2), packaging (ADR-007), GUI, AI-provider work, CBMC test generation (CBMC not installed, design not written).

## Your to-do after
- Review the DRAFT pages and security policy before copying them into the repo.
- Update SDD-005, the tracker and the execution plan, which still say AGPL.
