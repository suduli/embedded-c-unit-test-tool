# Chat 1 run summary (2026-11-19)

Queue: `docs/glm-night/chat1-queue.md` (41 items) on branch `glm-night/chat1`,
worktree `wt-chat1`, base `glm-night/20261117` (e2708f1). Final head: ade583d + the
summary commit. **All five gates green at end of run: 827 passed / 4 skipped, ruff
clean, mypy clean (88 source files), plan_check PASS (346 reqs / 344 alloc / 191 pkgs
/ 642 pw), trace_check OK.** Baseline at setup was 399/4/0-fails; every gate run
after every item exited 0 (no pre-existing failures to record). Zero pushes, zero
shared-file edits, zero chat-2 contacts.

## Counts per state

| State | Count |
|---|---|
| DONE | 32 |
| PARTIAL | 9 |
| SKIPPED | 0 |
| BLOCKED | 0 |

DONE: WP-PLG-01, WP-TCH-01, WP-TCH-02, WP-TCM-01, WP-BLD-01, WP-SEC-05, WP-BLD-02,
WP-SEC-04, WP-CORE-06, WP-TCH-07, WP-ING-03, WP-PLG-04, WP-SEC-03, WP-GEN-02,
WP-GEN-04, WP-ING-04, WP-ING-05, WP-GEN-03, WP-GEN-06, WP-GEN-05, WP-GEN-08,
WP-GEN-09, WP-ING-06, WP-SEC-07, WP-GEN-10, WP-GEN-11, WP-PLG-02, WP-TCH-04,
WP-EXT-03, WP-EXT-07, WP-EXT-05, WP-EXT-06.

## PARTIAL items and reasons

| WP | Requirement(s) left open | Reason |
|---|---|---|
| WP-GEN-01 | TOOL-HAR-040 (file-static variable access; type-resolved `extern` emission) | The analysis model records accessed globals by name+access only — no type reference, no global-definition list — so `extern` emission would be invented and file-static access needs a design decision. HAR-010/020/050 are covered. |
| WP-ING-02 | TOOL-ING-080 (Keil uVision / IAR EW / Eclipse imports) | Three format-specific XML importers exceed the smallest derivable increment; no criterion invented, no stub importer faked. ING-060 done, ING-210 claimed (pre-existing green evidence), ING-050 documented as demonstration path. |
| WP-CORE-07 | TOOL-NFR-120 (the user-facing pages themselves) | The externalisation mechanism (TOOL-NFR-190) and the complete machine-readable doc index are done and tested; the 15 `docs/user/` pages are outside this run's allowed paths — owner shared-file change (below). |
| WP-TCH-03 | TOOL-TCH-030 (verification **against** `arm-none-eabi-gcc` and a RISC-V GNU toolchain) | Executing real cross toolchains is outside this environment. The 6-config shipped roster (TOOL-TCH-050) and add-by-file support (TOOL-TCH-040) are done. SDCC coverage flag is an owner-review draft. |
| WP-BLD-03 | TOOL-TGT-010 (executing the composed cross builds) | Same environment limit as WP-TCH-03: command composition, metric gating and staleness carry-over are verified; execution pending runtime evidence. |
| WP-TCH-05 | TOOL-TCH-090 (building/validating the actual container images) | The deterministic container specification generation is done (digest-pinned, no invented digests); image builds run in CI — pending runtime evidence. TCH-080 fully done. |
| WP-TCH-06 | TOOL-TCH-100 (verification against licensed proprietary compilers) | The 5-family roster and the public-config support path (armclang, IAR demonstrated) are done; licensed toolchains unavailable here. |
| WP-EXT-01 | TOOL-TGT-020 (verification **against** QEMU and Renode) | Simulator run plans (both families) and the SEC-07 output boundary are verified; real simulator execution pending runtime evidence. |
| WP-EXT-02 | TOOL-TGT-030/040 (execution against physical hardware) | Probe descriptors and flash/run command composition for OpenOCD/pyOCD/J-Link are verified; real-hardware execution pending runtime evidence. |

No SKIPPED and no BLOCKED items: every queue item had derivable acceptance criteria,
and the ADR-sensitive item (WP-GEN-02) was handled by implementing only the
decision-free part.

## ADR questions recorded (not decided) — from WP-GEN-02's ledger row

1. Default framework selection policy (Unity vs cmocka when a project declares none).
2. cmocka mock-record integration binding to the WP-GEN-06 stub contract.
3. Third-party template/back-end distribution format (overlaps WP-PLG-02 discovery).
4. Template engine choice (stdlib substitution shipped; descriptor absorbs a change).

## Owner-review drafts created tonight (bind only when the owner accepts)

- WP-SEC-05: the disclosure process and supported-version policy (machine-readable in
  `ectt.sec.policy`, prose in the analysis note).
- WP-TCH-03: the SDCC coverage flag in the shipped config.
- WP-TCH-06: the proprietary-family scriptability notes.
- WP-EXT-06: the on-target overhead numbers (marked analytical, pending measurement).

## Shared-file changes needed from the owner in the morning

1. **`SECURITY.md`** (new, repo root): promote the WP-SEC-05 policy prose from
   `docs/verification/WP-SEC-05-analysis.md` §The policy and link it from the README.
   Root-level files were outside this run's allowed paths.
2. **`docs/user/` pages** (15 new files per the WP-CORE-07 index, which is both in
   `docs/verification/WP-CORE-07-analysis.md` §The index and machine-readable in
   `ectt.core.docindex`): installation (1), workflows (9), options (5). After
   creating each page, flip its index entry status `pending-page-not-created` →
   `shipped` in `src/ectt/core/docindex.py` (my allowed path, but the pages are not).
3. **Runtime-evidence runs** (not file edits, but morning follow-ups recorded in the
   ledger): real cross-toolchains (WP-TCH-03/BLD-03), licensed proprietary compilers
   (WP-TCH-06), QEMU/Renode execution (WP-EXT-01), physical probes (WP-EXT-02),
   container image builds (WP-TCH-05). Also replace WP-EXT-06's analytical overhead
   numbers with measured values after those runs.
4. **Morning merge owns** `design/trace/*` and the unified plan: I regenerated
   nothing and edited neither SRS-001 nor PLAN-001, so plan_check/trace_check need no
   reconciliation from my side.

## Ledger

`docs/glm-night/CHAT1_LEDGER.md` has one row per item (41 rows), state, commit hash,
test counts and notes. Commits follow the `[GLM-NIGHT-CHAT1] <WP>: <summary>`
convention with the required co-author trailer; the ledger itself was committed with
its item where changed and carries the remainder in the summary commit.
