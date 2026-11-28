# Plan to run now (2026-11-27 queues, rewritten 2026-11-28 after the core MC/DC merge)

Local `main` is the starting point. All checks pass: 4064 tests, ruff, mypy, plan_check, trace_check. Nothing is pushed.

## What to do
1. Start Docker Desktop and leave it running (the `gcc:14` image must stay installed).
2. Open two GLM (ZAI) chats, Chat A and Chat B.
3. Paste into Chat A the whole file `docs/glm-night/overnight-20261127/LANE_A_queue.md`.
4. Paste into Chat B the whole file `docs/glm-night/overnight-20261127/LANE_B_queue.md`.
5. Both stop by themselves at 05:30, or earlier when their list is done.

## What each chat does
- Chat A (4 tasks): make MC/DC usable from the build and command line, compile the generated test code with a real compiler for the first time, small leftovers, extra tests.
- Chat B (5 tasks): more worked MC/DC examples, real coverage checks, MC/DC minimums, report detail and a DRAFT page on what MC/DC does and does not show, extra tests.

## Already done (not in these queues)
- Listing decisions and conditions, the GCC version gate and 64-condition limit, MC/DC results and uncoverable-decision reasons.

## Your to-do after
- Read the security draft and the guide pages in `docs/user/`.
