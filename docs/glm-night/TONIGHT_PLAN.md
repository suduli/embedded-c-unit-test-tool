# Tonight's plan (2026-11-21)

Last night's work (both chats) is merged into local `main`. All checks pass: 3097 tests, ruff, mypy, plan_check, trace_check. Nothing is pushed.

## What to do
1. Open two GLM (ZAI) chats, Chat A and Chat B.
2. Paste into Chat A the whole file `docs/glm-night/overnight-20261121/LANE_A_queue.md`.
3. Paste into Chat B the whole file `docs/glm-night/overnight-20261121/LANE_B_queue.md`.
4. Sleep. Both stop by themselves at 05:30.

## What each chat does
- Chat A (7 tasks): connect the build step, harness generator, host profile and generation run to the pieces built earlier; nested expected values; extra tests.
- Chat B (9 tasks): analysis model update (function lines, global types, every unsupported spot), exact requirement links, safer saves, report marks, format reference doc, project save layout, ReqIF relations, extra tests.

## Why the list is shorter than before
Almost everything left on the board waits on your decisions. ADR-004 (coverage) alone holds about 30 tasks. Answer it and I can write a much bigger queue.

## Your own to-do list
- Read `SECOND_PASS_A.md` and `SECOND_PASS_B.md` in `docs/glm-night/overnight-20261120/`.
- Decide: ADR-003, ADR-004, ADR-005, ADR-007, SRS-Q2, SRS-Q9.
- Decide whether to keep the ReqIF schema file in the repo (see the second-pass list).
