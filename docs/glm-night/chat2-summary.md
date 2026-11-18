# Chat 2 overnight summary (2026-11-18)

Run: worktree `E:\projects\UDS_Simulator\wt-chat2`, branch `glm-night/chat2`, baseline
`glm-night/20261117` (e2708f1). All 35 queue items processed in order, then this summary.
**Nothing was pushed; no board/issue writes; no ADR or D-01..D-04 answered; shared files untouched.**

Final gate state: **532 passed / 4 skipped** (baseline 399/4; the 4 skips are the pre-existing
symlink-privilege environment skips), ruff clean, mypy clean (54 source files), plan_check OK
(346 requirements / 344 allocations / 191 packages — unchanged by design, regen owned by the
morning merge), trace_check OK.

## Counts per state

| State | Count |
|---|---:|
| DONE | 19 |
| PARTIAL | 15 |
| BLOCKED | 1 |
| SKIPPED | 0 |
| **Total** | **35** |

DONE: WP-SPIKE-01, WP-SPIKE-02, WP-CORE-01, WP-API-01, WP-CLI-01, WP-CLI-02, WP-PRJ-01,
WP-ING-01, WP-ANA-01, WP-ANA-02, WP-ANA-03, WP-ANA-04, WP-ANA-08, WP-ANA-09, WP-API-02,
WP-PRJ-03, WP-PRJ-04, WP-MIG-06, WP-QUA-05.

## PARTIAL / BLOCKED items and reasons

| WP | State | Reason |
|---|---|---|
| WP-SPIKE-03 | PARTIAL | Packaging spike verified as recorded `PASS (local build)` (194.2 MB, ~162 ms cold start, non-admin); the §4.4 criterion's clean-Windows-VM endpoint-security check needs a physical clean machine + human observation — not closable unattended. Owner: run the manual clean-VM step. |
| WP-CORE-02 | PARTIAL | Error model, transaction, cancellation all verified (16 tests). Open: CLI exit-code wiring (now exists as WP-CLI-02's table — adoption by callers remains), no long-running operation routes through `OutputRoot.transaction` yet. |
| WP-CLI-03 | PARTIAL | Container **execution** contract pinned by subprocess demos (stripped env, no TTY, exit-code fidelity, clean stdout). Open: the actual container image — that is WP-PKG-05 (INS-090) by register split; a docker demonstration was not run here. |
| WP-ANA-07 | PARTIAL | PAR-130 (partial-failure isolation) fully evidenced (15 tests). Open: PAR-140's unsupported-construct inventory is carried and schema-gated but never populated by extraction (always `[]`); the multi-file analysis driver that would own the isolation loop does not exist yet. |
| WP-CORE-04 | PARTIAL | Provenance facility verified (10 tests, deterministic digest, no wall-clock in hash). Open: TOOL-QUA-060's "in every generated artifact" — embedding lands with the producing packages. |
| WP-QUA-07 | PARTIAL | Qualification-scope statement implemented per §5.4 criterion (single place, evidence-cited, overclaim guard, 7 tests). Open: the classification line stays `OPEN` — deciding it is WP-QUA-01/owner. |
| WP-ING-07 | PARTIAL | Link-plan loader complete and fail-closed (24 tests). Open: wire `load_link_plan` into a harness-build step (build step doesn't exist yet), SDD-003 amendment for the proposed field schema, toolchain-adapter verification of linker/runtime identities. |
| WP-API-03 | PARTIAL | Engine leg of TOOL-UIX-330 implemented + tested (cli_equivalent on responses, one-catalogue identity, reachability, 7 tests). Open: the GUI leg — no GUI exists (CMP-GUI unimplemented by design); dependency state, not a defect. |
| WP-CLI-04 | PARTIAL | Reference pipelines (GitHub Actions + GitLab CI, valid YAML) + machine-readable cacheable-artifact contract (6 tests). Open: live-pipeline demonstration (method D needs real CI) and the versioned container image (WP-PKG-05). |
| WP-PRJ-02 | PARTIAL | Diff-stable sharded store implemented (11 tests: one-file-per-concern, byte-stable unchanged rewrites, name confinement). Open: `Project.save` integration (single-file manifest remains default until a format decision requires the split); TOOL-PRJ-030 evidence cited, not re-implemented. |
| WP-ANA-06 | PARTIAL | PAR-170 eligibility gate fully evidenced (10 tests). Open: PAR-080's exposure mechanism (testability without source modification — ADR-sensitive, belongs with WP-GEN-03) and PAR-090 entirely (no macro resolution exists; no tests). |
| WP-QUA-02 | PARTIAL | Operational-requirements spec artifact with the three required sections, SRS-cited environment facts, evidence-cited limitations (6 tests). Open: intended-use wording — classification-dependent (WP-QUA-01), recorded OPEN. |
| WP-ANA-05 | PARTIAL | Decision-free increment landed: DSN-ANA-040 capability/degrade record + AST-based cyclomatic complexity per function exposed as optional in-memory `FunctionModel.complexity` (8 tests vs real libclang). Open: the CFG construction itself — that is the open ADR-001 §2.4 mechanism decision; persisted-schema exposure of complexity (schema bump) deferred to the owning merge. |
| WP-QUA-06 | PARTIAL | Fail-closed mapping structure for the five named standards (clause+evidence-sourced rows, satisfaction claims refused, 6 tests). Open: the populated mapping — classification/qualification-context dependent; default is honestly empty. |
| WP-QUA-08 | PARTIAL | Four placeholder-only qualification templates (plan, classification record, known-error list, test report; 6 tests). Open: classification-dependent prefill (WP-QUA-01). |
| WP-QUA-01 | BLOCKED | The deliverable *is* the ISO 26262-8 TI/TD/TCL classification judgment — an ADR-sensitive decision an unattended run must never make. No code written for the blocked part. Owner: answer the classification decision; the `ectt.qua` artifacts (QUA-02/06/07/08) are ready to fill. |

## New code landed (BUILD-lane items)

- `src/ectt/api/` — catalogue, protocol (hello negotiation, envelope validation, session IDs),
  transport (SDD-002 §9.2 framing, stdio pump, no-socket guard), roundtrip contract.
- `src/ectt/cli/` — catalogue-generated parser, dispatcher, stable exit-code table
  (0/1/2/10/11), container-execution demo tests, CI reference templates + artifact-cache
  contract.
- `src/ectt/qua/` — qualification-scope statement, operational-requirements spec, process
  documentation, standards-objective mapping structure, qualification templates.
- `src/ectt/mig/` — coexistence scan + byte-level non-interference snapshots.
- `src/ectt/prj/shards.py` — diff-stable sharded store.
- `src/ectt/ana/cfg.py` + optional `FunctionModel.complexity`.
- Tests: +133 over baseline (399 → 532).

## Shared-file changes needed from the owner (morning merge)

1. **Board / PLAN-001 §5.4 reconciliation:** proposed falsifiable acceptance criteria for the
   RECON-flagged packages are recorded in each `docs/verification/WP-*-analysis.md` under
   "Acceptance criteria" (derived from SRS texts + recorded design, never invented). Owner should
   review and, if accepted, record them on the board / in §5.4 — I did not write the board or
   PLAN-001.
2. **Spike verification status:** the three spikes' historical-claim status is now verified with
   evidence chains (`WP-SPIKE-01/02/03-analysis.md`); the board's "unverified" notes and the
   reconciliation flags can be updated by the owner (WP-SPIKE-03 keeps an explicit open item:
   clean-VM endpoint-security check).
3. **Tracker / unified plan / GLM_NIGHT_LOG / parallel-plan:** merge this ledger
   (`docs/glm-night/CHAT2_LEDGER.md`, 35 rows) with chat 1's, then regenerate the tracker and
   unified plan (`design/trace/*` untouched here by rule — plan_check still passes on the
   unchanged baseline: 346/344/191).
4. **Analysis-model schema bump (1.4 → 1.5):** `FunctionModel.complexity` is in-memory only;
   persisting it needs an additive minor schema bump — owning-merge work.
5. **SDD-003 amendment:** link-plan field schema (WP-ING-07's proposal) needs recording before
   anyone authors plans against it.
6. **Decision queue:** WP-QUA-01 (tool classification TI/TD/TCL) is the one new BLOCKED item;
   answering it unblocks QUA-01/02/06/07/08 prefill. D-01..D-04 untouched, as instructed.

## Process disclosures (honesty notes)

- One accidental `--amend` at WP-SPIKE-01 (violation of the no-amend rule); content unchanged,
  corrected sha recorded in a dedicated commit (042e03a). No further amends.
- WP-CLI-04's first commit landed with one red test (trailing-slash assertion); fixed immediately
  in the next commit (2e1b7b3) before any gate was claimed green. Final state green.
- WP-ANA-05's main commit included a mypy error that slipped past a piped gate command; fixed in
  the follow-up commit (7cbfb14); final gates all exit 0.
- PySide6 + pytest-qt were installed into `wt-chat2/.venv` only (venv is untracked) to re-run the
  spike-02 suite live; no repo/packaging change.
- Every item's commit-sha chain is in `docs/glm-night/CHAT2_LEDGER.md`; two commits per item
  (content + ledger row) by design, since amends are forbidden.
