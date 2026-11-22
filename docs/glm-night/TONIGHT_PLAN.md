# Plan to run now (2026-11-23 queues)

Last night's work is merged into local `main` (b8ae29f). All checks pass: 3710 tests, ruff, mypy, plan_check, trace_check. Nothing is pushed.

## What to do
1. Open two GLM (ZAI) chats, Chat A and Chat B.
2. Paste into Chat A the whole file `docs/glm-night/overnight-20261123/LANE_A_queue.md`.
3. Paste into Chat B the whole file `docs/glm-night/overnight-20261123/LANE_B_queue.md`.
4. Both stop by themselves at 05:30, or earlier when their list is done.

## What each chat does
- Chat A (9 tasks): a validation suite you can run yourself, a known-error list, a software bill of materials, a dependency check, a safer way to start test programs, debugger launch command, a check that the tool's own files are unchanged, extra tests.
- Chat B (7 tasks): a certification report with a clear "what this does not claim" statement, detection of code the coverage tool cannot measure, control and data coupling analysis, safety tests for report files, import/export round trips, extra tests.
- The two chats touch different folders, so they do not wait for each other.

## Notes
- Last night both chats finished in under an hour, so these lists are longer. The backlog is now thin: most of what is left is held on your decisions or needs a compiler or GUI.
- Release signing is not built (needs your keys); the chat records it as a to-do for you.
- Still held: MC/DC (SRS-Q2), packaging (ADR-007), GUI, AI-provider work, CBMC test generation.

## Your to-do after
- Review the DRAFT pages and security policy from last night before copying them into the repo.
- Update SDD-005, the tracker and the execution plan, which still say AGPL.
