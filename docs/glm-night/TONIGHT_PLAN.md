# Tonight's plan (2026-11-19)

Branch: `glm-night/20261117` (pushed to origin, head after this commit).
Board: GitHub project 5, "ECTT — Delivery". Status was synced from the chat ledgers on 2026-11-19.

## Where things stand

- 76 queued items ran in the two GLM chats: 51 DONE, 24 PARTIAL, 1 BLOCKED (WP-QUA-01). Both chats are merged locally into this branch, and the trunk gates pass (970 passed, 4 skipped).
- 115 items are held. Each one waits on an owner decision (see below). No agent can run them tonight.
- Nothing merges to `main` tonight. The branch stays a review branch until the owner approves.

### Board status applied from the ledgers (66 items changed)

| Ledger state | Board status | Meaning |
|---|---|---|
| DONE (51) | Review | Code is on `glm-night/20261117`, awaiting owner review and merge. Not Done, because it is not on `main`. |
| PARTIAL (24) | Verification | Local evidence is in; the runtime or manual step is still open. |
| BLOCKED (1) | Backlog | WP-QUA-01 needs an ADR decision. |
| Held (115) | unchanged | Backlog or Needs reconciliation, as before. |

## 1. Owner decisions (highest value tonight)

Answering these releases most of the held work. The agent must not answer them.

| Decision | Releases (held items, approx.) |
|---|---|
| D-02 identity model | 69 via WP-EXH-01, 43 via WP-TCM-02, 4 via WP-CBT-01 |
| ADR-004 coverage (not in the queue; critical path) | 30 via WP-COV-01 |
| D-03 platform order | 29 via WP-CORE-03, 22 via WP-GUI-01 |
| ADR-007 packaging (not in the queue) | 12 via WP-PKG-01 |
| D-01 licence posture | 2 via WP-PKG-07, 1 via WP-PKG-08 |
| ADR-003 (not in the queue) | 2 via WP-ATG-02, 1 via WP-ATG-03 |
| SRS-Q2 / SRS-Q9 | 5 via WP-COV-05, 2 via WP-EXH-04 |
| D-04 NFR calibration | 1 via WP-CORE-05 |

Also decide whether the chat branches `glm-night/chat1` and `glm-night/chat2` are deleted after the merge. They are local only.

## 2. Runtime evidence runs (PARTIAL items, need a machine)

These need the real toolchain or hardware. Schedule them when the machine is free.

- WP-SPIKE-03: clean-VM endpoint-security step (manual, owner).
- WP-TCH-03, WP-BLD-03, WP-TCH-06, WP-EXT-01, WP-EXT-02, WP-TCH-05: real-toolchain and hardware runs.
- WP-CORE-02 and WP-CORE-07 are PARTIAL in the ledgers. Their open items are listed in their ledger rows.

## 3. Owner write-ups (no code needed)

- `SECURITY.md`, from the WP-SEC-05 policy.
- The 15 `docs/user/` pages in the WP-CORE-07 index.
- Review the drafts: security policy, SDCC flag, proprietary notes, overhead numbers.
- Four open ADR questions from WP-GEN-02 (recorded in `CHAT1_LEDGER.md`, undecided).

## 4. Bookkeeping that remains

- Reconcile the tracker's WP rows from the two ledgers. Not done yet, because the tracker is owner-edited.
- Decide `aheadOfOriginMain` in the tracker meta. The base is ambiguous: 146 against `origin/main`, 157 against local `main`.
- Chat 2 follow-ups: acceptance criteria into PLAN-001 §5.4 and the board, schema 1.5 bump for `complexity`, SDD-003 link-plan amendment, WP-QUA-01 classification (ADR-sensitive).

## Order for the morning

1. Answer section 1 (owner).
2. Approve or reject the merge of `glm-night/20261117` into `main`.
3. Run section 2 on a machine with the toolchain.
4. Next overnight run: the held items whose blockers are now answered.
