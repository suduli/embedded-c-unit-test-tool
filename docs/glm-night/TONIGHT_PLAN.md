# Plan to run now (2026-11-27 queues: MC/DC)

Local `main` is the starting point (c1fd70e). All checks pass: 4026 tests, ruff, mypy, plan_check, trace_check. Nothing is pushed.

## What to do
1. Start Docker Desktop and leave it running.
2. Open two GLM (ZAI) chats, Chat A and Chat B.
3. Paste into Chat A the whole file `docs/glm-night/overnight-20261127/LANE_A_queue.md`.
4. Paste into Chat B the whole file `docs/glm-night/overnight-20261127/LANE_B_queue.md`.
5. Both stop by themselves at 05:30, or earlier when their list is done.

## What each chat does
- Chat A (5 tasks): list every decision and condition in the analyzed code, MC/DC compiler flags and version check, compile the generated test code with a real compiler for the first time, small leftovers, extra tests.
- Chat B (7 tasks): MC/DC results, worked examples with hand-computed answers, real coverage checks, MC/DC minimums, code the compiler cannot measure (waits for Chat A's first task), report detail and a DRAFT page on what MC/DC does and does not show, extra tests.

## Notes
- GCC 14.4.0 is installed only as a Docker image (`gcc:14`, about 2.2 GB). Nothing was installed into Windows.
- Still held: GUI, AI-provider work, CBMC test generation, packaging (ADR-007).

## Your to-do after
- Read the security draft and the guide pages in `docs/user/`.
