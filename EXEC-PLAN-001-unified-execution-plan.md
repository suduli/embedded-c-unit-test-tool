# EXEC-PLAN-001 — Unified execution plan

**Purpose:** one ordered, agent-ready plan that merges the three plan layers of this repository — the **PLAN-001** work breakdown (191 work packages), the **vcast-findings** review track (`T-01`…`T-22`) and the **BACKLOG_GLM_NIGHT** overnight queue (`TASK-000`…`TASK-024`, reserve `TASK-101`…`TASK-108`) — into a single task model with full traceability. An agent that has never seen this repository should be able to pick up the next task from this file alone.

**Companion tracker (live view):** [`EXEC-PLAN-001-tracker.html`](EXEC-PLAN-001-tracker.html) — open it directly in a browser. Its embedded JSON block is the **single source of truth**; the data-driven sections of this document (between `GENERATED` markers) are regenerated from it with `python design/trace/unified_plan_sync.py`. Hand-written sections (§1, §3.1–3.2, §4.1, §4.4, §5) are edited by hand.

**Sources (not modified by this plan):** [`PLAN-001`](PLAN-001-specification-analysis-and-work-breakdown.md) · [`SRS-001`](SRS-001-requirements.md) · [`BACKLOG_GLM_NIGHT.md`](BACKLOG_GLM_NIGHT.md) · [subsystem tracker](docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md) · [vcast-findings review](docs/reviews/2026-11-06-vcast-findings-review-tracker.md) · [`design/trace/design-elements.yaml`](design/trace/design-elements.yaml) · ADR-001/002/006/008.

**Decisions D-01…D-04 are pending user decisions. This plan does not resolve them and no agent may.**

---

## 1. Read this first

1. **Do not decide anything that belongs to the owner.** D-01 licence, D-02 identity model, D-03 platform order, D-04 NFR calibration — and the open ADR-003/004/005/007 and SRS §27 q2/q9 — stay open. If your task needs one of them, stop and escalate (§5.6).
2. **Pick tasks only from the ready queue (§4.2), lowest `seq` first, only when every dependency is done.** Work packages (`WP-…`) that are scheduled into the queue are delivered *by* their `TASK-…`; you start the TASK, not the WP.
3. **Every commit passes the full gate** (§5.4). The baseline has exactly three known failing tests (fixed by `TASK-001`); anything else red is yours.
4. **Never touch**: `main`, `docs/pending-decisions` (work in a worktree off its tip), accepted ADR/SRS text, `LICENSE`/`LICENSEES`, `aidlc/`, `.claude/`, `vcast-findings/` content, `spikes/`, open PRs #4/#6.
5. **Push nothing without owner approval** (this overrides BACKLOG §3.2 — see §5.5).
6. **Update the tracker JSON, then re-run the sync script, in the same commit as the work** (§5.9).

---

## 2. State of the project at the as-of date

<!-- BEGIN GENERATED: snapshot -->
**As of 2026-11-18** · HEAD `35487c4` on `glm-night/20261117` (14 commits ahead of `origin/main`, **not pushed**).

| Source plan | Implemented | Landed | In Progress | Planned | Blocked | Total |
|---|---|---|---|---|---|---|
| PLAN-001 | 9 | · | · | 173 | 9 | 191 |
| vcast-findings | · | 16 | · | · | 6 | 22 |
| BACKLOG | · | · | · | 24 | 1 | 25 |
| BACKLOG-RESERVE | · | · | · | 8 | · | 8 |
| **Total** | 9 | 16 | · | 205 | 16 | 246 |

- **Requirements:** 346 in SRS-001; 344 allocated to a work package; 2 Future (not allocated); 259 design elements. Allocated requirements by owning-WP status: Implemented 21, Planned 299, Blocked 24.
- **Work packages:** 191 · 642 person-weeks.
- **Review track (vcast-findings):** 16 of 22 landed. Not landed: `T-01` (Blocked), `T-02` (Blocked), `T-04` (Blocked), `T-14` (Blocked), `T-05` (Blocked), `T-06` (Blocked).
- **Gates at HEAD:** plan_check — exit 0 — 346 requirements; 344 unique primary allocations; 191 packages; 642 person-weeks; 52-week lower bound. trace_check — exit 0 — 344/344 in-scope requirements allocated; 259 design elements.
- **Tests at HEAD:** 237 passed, 0 failed, 1 skipped. Failing:  (fixed by `TASK-001`).
- **Overnight backlog budget:** core queue sums to 2,940k tokens (its header says 2,850k); reserve 1,250k.
- **Startable right now:** `TASK-000` (dependencies met, not blocked).

**Notes and discrepancies found while consolidating:**

1. Review-task progress is 16 of 22 landed (T-03, T-07…T-13, T-15…T-22); a summary saying 20 of 22 is wrong. T-01, T-04, T-05, T-06 are 'Awaiting decision' (D-01…D-04), T-02 is Not Started (ADR-005), T-14 is Not Started (needs T-04). Source: docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md.
2. The BACKLOG core-queue estimates sum to 2,940k tokens, not the 2,850k stated in its header; reserve sums to 1,250k.
3. TASK-007 (WP-CORE-03) is marked Blocked: its order-neutral encoding of Windows/Linux is effectively answer (c) of D-03, which only the owner may give.
4. ADR-003, ADR-004, ADR-007 and SRS §27 q2/q9 are open but are not in the D-01…D-04 queue; they gate WP-ATG-02/03, WP-COV-01 (critical path), WP-PKG-01, WP-COV-05 and WP-EXH-04.
5. design/trace/requirement-matrix.csv and trace-graph.json list 323 requirements (stale generated artefacts); the live counts (346) come from SRS-001 and plan_check.
6. BACKLOG §3.2 tells agents to push glm-night/20261117; that branch is cut from the unpushed docs/pending-decisions, so a push would publish those 10 commits. This plan makes the push owner-approved.
<!-- END GENERATED: snapshot -->

---

## 3. The single task model

### 3.1 ID namespaces — original IDs are kept exactly as written; nothing is renumbered

| Namespace | Source plan | Meaning | Example |
|---|---|---|---|
| `WP-<AREA>-NN` | PLAN-001 §5.5 | A work package — a cohesive capability that owns SRS requirements (191 of them, incl. 3 spikes). | `WP-CORE-02` |
| `T-NN` | vcast-findings | A review-derived task (22). Mostly specification / design-register / gate work, landed through the design gates. | `T-09` |
| `TASK-NNN` | BACKLOG_GLM_NIGHT | An overnight execution task. `TASK-000…024` is the core queue, `TASK-101…108` the reserve queue. | `TASK-006` |
| `D-NN` | decision queue | A pending user decision (D-01…D-04). | `D-01` |
| `ADR-00N`, `SRS-Q2/Q9` | ADRs / SRS §27 | Other open or accepted architecture decisions and SRS open questions. `SRS-Q2` = §27 q2, `SRS-Q9` = §27 q9. | `ADR-004` |
| `TOOL-<CAT>-NNN` | SRS-001 | An SRS requirement (346). | `TOOL-ING-200` |
| `DSN-<COMP>-NNN` | design register | A design element satisfying requirements. | `DSN-ING-120` |
| `PR#n` / `PRn-x` | GitHub | An open pull request / one of its remaining owner steps. | `PR#6`, `PR6-a` |

**Overlaps.** A `TASK-` is the *execution unit* for a `WP-` (for example `TASK-006` delivers `WP-CORE-02`); a `T-` often is the *specification* half of a `WP-` (for example `T-12` specified `WP-ING-07`, whose code is `TASK-010`). Both IDs stay; they cross-reference each other (§3.4). A WP is marked **Implemented** only when its own PLAN-001 exit criterion is met — landing a related `T-` or finishing its `TASK-` is evidence, not proof.

### 3.2 Status and lane vocabulary

| Status | Used for | Meaning |
|---|---|---|
| **Implemented** | `WP-…` | The package's code and exit evidence exist and are verified. |
| **Landed** | `T-…`, `TASK-…` | The task is done and its acceptance criteria and gates passed. |
| **In Progress** | any | An agent has claimed the task and is working on it (set it when you start; at most one per agent). |
| **Planned** | any | Not started, not decision-blocked. Whether it can start is a separate question (see lane and dependencies). |
| **Blocked** | any | Cannot proceed or be accepted without an open decision (`blockedBy` is non-empty). **Escalate; never decide.** A *technical* failure (tool missing, libclang unusable) is **not** this status — see §5.3. |

| Lane | Meaning |
|---|---|
| `done` | Implemented / Landed. |
| `queue` | Core overnight backlog (`TASK-000…024`), ordered by `seq`. |
| `reserve` | `TASK-101…108` — only after `TASK-024` is committed. |
| `scheduled` | A planned `WP-` that a queued/reserve `TASK-` delivers; follow the TASK. |
| `blocked` | Decision-blocked. |
| `backlog` | A planned `WP-` not yet scheduled into any queue. |

### 3.3 Fields carried by every task

<!-- BEGIN GENERATED: fields -->
| Field | Meaning |
|---|---|
| `id` | Original ID, exactly as written in its source plan (WP-…, T-NN, TASK-NNN). Never renumber. |
| `title` | Short title from the source plan. |
| `source` | PLAN-001 \| vcast-findings \| BACKLOG \| BACKLOG-RESERVE. |
| `area` | Component area for WPs (CORE, ANA, ING, …), REVIEW for T-xx, backlog area for TASK-xxx. |
| `status` | Implemented (WP code done) \| Landed (T-xx / TASK-xxx done) \| In Progress \| Planned \| Blocked. |
| `lane` | done \| queue (core backlog) \| reserve \| scheduled (WP delivered by a queued TASK) \| blocked \| backlog (planned WP). Update with status. |
| `seq` | Position in the single execution order. Lower first. Stable; do not renumber. |
| `deps` | Hard prerequisites (task ids). A task is startable only when all are Implemented/Landed. |
| `softDeps` | Schedule-only (~) and port-mediated (^) WP edges from PLAN-001; not start gates. |
| `blockedBy` | Open decisions/ADRs/SRS questions that block the task (D-01…D-04, ADR-00x, SRS-Qx). Non-empty ⇒ status Blocked ⇒ escalate, never decide. |
| `watch` | Soft gates: the task can start but a decision may change it. |
| `reqs` | Linked SRS requirements (TOOL-…). |
| `wps` | PLAN-001 work packages this task delivers or touches. |
| `related` | Cross-references (overlapping tasks, NR ids, review sources, DSN elements). |
| `adrs` | Linked ADRs / open questions. |
| `prs` | Linked pull requests (PR#n). |
| `branch` | Branch the work lives on / will land on. |
| `files` | Files or directories likely touched (planning aid, not a limit for landed items). |
| `acceptance` | Concrete, falsifiable acceptance criteria. |
| `verify` | Verification commands. G-FULL = the three gate commands; G-GATES = the two design gates. |
| `verifyState` | pass \| failing \| pending — state of the verification evidence at as-of date. |
| `commit` | Landing commit (short sha) for done items. |
| `est` | Effort: person-weeks for WPs, thousand tokens for TASK-xxx. |
| `notes` | Free text: assumptions, partial progress, escalations. |
<!-- END GENERATED: fields -->

### 3.4 Overlap map — which tasks touch the same work

<!-- BEGIN GENERATED: overlap -->
| Task | Source | Work packages touched | Related tasks / decisions | SRS requirements |
|---|---|---|---|---|
| `T-03` | vcast-findings | `WP-AIF-15`, `WP-COV-09`, `WP-EXH-02`, `WP-PLG-02`, `WP-PLG-04` | — | `TOOL-AIF-260`, `TOOL-COV-150`, `TOOL-EXE-040`, `TOOL-PLG-080`, `TOOL-PLG-100` |
| `T-12` | vcast-findings | `WP-ING-07` | — | `TOOL-ING-200` |
| `T-07` | vcast-findings | `WP-ING-02`, `WP-ING-03` | — | `TOOL-ING-210`, `TOOL-ING-220` |
| `T-08` | vcast-findings | `WP-ING-03` | — | `TOOL-ING-100` |
| `T-09` | vcast-findings | `WP-ANA-07`, `WP-ANA-08` | — | `TOOL-PAR-140`, `TOOL-PAR-150` |
| `T-10` | vcast-findings | `WP-ANA-09` | — | `TOOL-PAR-160` |
| `T-11` | vcast-findings | `WP-ANA-06` | — | `TOOL-PAR-170` |
| `T-13` | vcast-findings | `WP-MIG-05` | — | `TOOL-MIG-110` |
| `T-16` | vcast-findings | `WP-COV-02` | — | `TOOL-COV-180` |
| `T-17` | vcast-findings | `WP-COV-02`, `WP-COV-05`, `WP-COV-06` | — | `TOOL-COV-190`, `TOOL-COV-200` |
| `T-18` | vcast-findings | `WP-COV-05`, `WP-COV-10` | — | `TOOL-COV-090`, `TOOL-COV-210` |
| `T-19` | vcast-findings | `WP-ATG-01`, `WP-TRC-01` | — | `TOOL-ATG-080`, `TOOL-TRC-110` |
| `T-20` | vcast-findings | `WP-COV-02` | — | `TOOL-COV-220` |
| `T-21` | vcast-findings | `WP-GEN-01`, `WP-QUA-03` | — | `TOOL-QUA-110` |
| `T-22` | vcast-findings | `WP-PKG-01`, `WP-PKG-07` | — | `TOOL-INS-120` |
| `T-15` | vcast-findings | `WP-EXT-04` | — | `TOOL-TGT-070`, `TOOL-TGT-130` |
| `TASK-000` | BACKLOG | — | `WP-ANA-04` | — |
| `TASK-001` | BACKLOG | `WP-ANA-04` | `T-09`, `T-10` | `TOOL-PAR-100`, `TOOL-PAR-110` |
| `TASK-002` | BACKLOG | — | `WP-CORE-08` | — |
| `TASK-004` | BACKLOG | — | `WP-CORE-08` | — |
| `TASK-005` | BACKLOG | `WP-PRJ-01` | — | `TOOL-PRJ-010`, `TOOL-PRJ-020`, `TOOL-PRJ-070` |
| `TASK-006` | BACKLOG | `WP-CORE-02` | — | `TOOL-NFR-090`, `TOOL-NFR-180` |
| `TASK-008` | BACKLOG | `WP-ANA-03` | `TASK-001` | `TOOL-PAR-060` |
| `TASK-009` | BACKLOG | `WP-ANA-07` | `T-09`, `T-11` | `TOOL-PAR-130`, `TOOL-PAR-140` |
| `TASK-010` | BACKLOG | `WP-ING-07` | `T-12` | `TOOL-ING-200` |
| `TASK-011` | BACKLOG | `WP-PRJ-04` | — | `TOOL-PRJ-090` |
| `TASK-012` | BACKLOG | `WP-PRJ-03` | — | `TOOL-PRJ-040` |
| `TASK-013` | BACKLOG | `WP-CORE-04` | — | `TOOL-QUA-060`, `TOOL-INS-110` |
| `TASK-014` | BACKLOG | — | `T-01`, `T-04`, `T-05`, `T-06` | — |
| `TASK-015` | BACKLOG | — | `T-02` | — |
| `TASK-016` | BACKLOG | — | `WP-CORE-01` | — |
| `TASK-017` | BACKLOG | — | `WP-ANA-08`, `WP-ANA-09` | — |
| `TASK-101` | BACKLOG-RESERVE | `WP-ING-02` | — | `TOOL-ING-050`, `TOOL-ING-060`, `TOOL-ING-080`, `TOOL-ING-210` |
| `TASK-102` | BACKLOG-RESERVE | `WP-ING-03` | — | `TOOL-ING-070`, `TOOL-ING-090`, `TOOL-ING-100`, `TOOL-ING-220` |
| `TASK-103` | BACKLOG-RESERVE | `WP-ANA-06` | — | `TOOL-PAR-080`, `TOOL-PAR-090`, `TOOL-PAR-170` |
| `TASK-104` | BACKLOG-RESERVE | `WP-PRJ-02` | — | `TOOL-PRJ-030`, `TOOL-PRJ-060` |
| `TASK-105` | BACKLOG-RESERVE | `WP-CORE-06` | — | `TOOL-NFR-130`, `TOOL-NFR-160` |
| `TASK-106` | BACKLOG-RESERVE | `WP-TCH-02` | — | `TOOL-TCH-010` |
| `T-01` | vcast-findings | `WP-PKG-07` | — | `TOOL-LIC-010` |
| `T-05` | vcast-findings | `WP-CORE-03` | — | `TOOL-NFR-010`, `TOOL-NFR-020` |
| `T-06` | vcast-findings | `WP-CORE-05` | — | `TOOL-NFR-030`, `TOOL-NFR-040`, `TOOL-NFR-050`, `TOOL-NFR-150` |
| `TASK-007` | BACKLOG | `WP-CORE-03` | `T-05` | `TOOL-NFR-010`, `TOOL-NFR-020`, `TOOL-NFR-100` |
<!-- END GENERATED: overlap -->

---

## 4. Execution order

### 4.1 Order of work

The list is a single sequence by `seq`; the stretches are:

1. **History (done)** — spikes, six implemented WPs, sixteen landed review tasks (§4.6).
2. **Foundation, `TASK-000` → `TASK-001`** — create the worktree/venv, record the baseline, then fix the three failing `test_persist` tests (schema `1.0` → `1.2` drift after T-09/T-10). Nothing else starts before the suite is green.
3. **CI and tooling, `TASK-002` → `TASK-003`** — a pytest + design-gate workflow, then ruff + mypy. (Today only `traceability.yml` exists; there is no test, lint or type check in CI.)
4. **Quality baseline, `TASK-004`, `TASK-005`** — coverage ≥ 80% on `core`/`prj`/`ing`; the ADR-002 grammar rejection/preservation suite.
5. **Implementation, `TASK-006` → `TASK-013`** — `TASK-006` (error model) first, because 008–013 build on it. `TASK-007` (platform baseline) is **held out as Blocked on D-03**.
6. **Planning and documentation, `TASK-014` → `TASK-023`** — decision memos (drafts only), the T-02 draft, verification notes, tracker refresh, docs, README, ID checker, read-only repo and dependency audits, next-phase plan.
7. **`TASK-024`** — morning review pack, always last of the core queue.
8. **Reserve, `TASK-101` → `TASK-108`**, then refresh `TASK-024`.
9. **Decision-blocked work (§4.3)** waits for the owner. **Unscheduled WPs (§4.5)** wait for scheduling (`TASK-023` ranks the next ten).

Core queue follows BACKLOG numeric order; the stop rule is "stop starting new tasks at ≈ 2.8M tokens used; keep ≈ 150k for `TASK-024`".

### 4.2 Ready queue (decision-free; ordered)

A task is **startable** only when its status is Planned, it has no `blockedBy`, and every dependency is Implemented/Landed. `TASK-016` lists only `TASK-013` as its dependency but documents WPs delivered by `TASK-006…013`; treat those as effective prerequisites.

<!-- BEGIN GENERATED: queue -->
| Seq | ID | Title | Delivers WP | Est. | Depends on | Status | Startable now |
|---|---|---|---|---|---|---|---|
| 26 | `TASK-000` | Worktree, venv, baseline, log | — | 30k tokens | — | Planned | yes |
| 27 | `TASK-001` | Fix the 3 failing `test_persist` tests (schema 1.0 → 1.2 drift) | `WP-ANA-04` | 70k tokens | `TASK-000` | Planned | after deps |
| 28 | `TASK-002` | CI workflow: pytest + design gates, Linux & Windows | — | 50k tokens | `TASK-001` | Planned | after deps |
| 29 | `TASK-003` | Add ruff + mypy config and triage findings | — | 120k tokens | `TASK-001` | Planned | after deps |
| 30 | `TASK-004` | Coverage baseline and gap-filling tests (≥80% on core/prj/ing) | — | 200k tokens | `TASK-001` | Planned | after deps |
| 31 | `TASK-005` | ADR-002 grammar: rejection and preservation test suite | `WP-PRJ-01` | 150k tokens | `TASK-001` | Planned | after deps |
| 32 | `TASK-006` | WP-CORE-02 structured error model, fail-safe, cancellation | `WP-CORE-02` | 220k tokens | `TASK-004` | Planned | after deps |
| 34 | `TASK-008` | WP-ANA-03 call graph and scope classification | `WP-ANA-03` | 250k tokens | `TASK-006` | Planned | after deps |
| 36 | `TASK-009` | WP-ANA-07 partial-failure resilience | `WP-ANA-07` | 130k tokens | `TASK-006` | Planned | after deps |
| 38 | `TASK-010` | WP-ING-07 authored link plan ingestion and validation | `WP-ING-07` | 170k tokens | `TASK-006` | Planned | after deps |
| 40 | `TASK-011` | WP-PRJ-04 dangling reference detection | `WP-PRJ-04` | 100k tokens | `TASK-006` | Planned | after deps |
| 42 | `TASK-012` | WP-PRJ-03 schema migration with explicit confirmation | `WP-PRJ-03` | 200k tokens | `TASK-006` | Planned | after deps |
| 44 | `TASK-013` | WP-CORE-04 provenance record and version identification | `WP-CORE-04` | 130k tokens | `TASK-006` | Planned | after deps |
| 46 | `TASK-014` | Decision memos D-01…D-04 (decision-ready drafts) | — | 120k tokens | `TASK-000` | Planned | after deps |
| 47 | `TASK-015` | T-02 draft: no-import/provenance rule for `vcast-findings/` | — | 70k tokens | `TASK-014` | Planned | after deps |
| 48 | `TASK-016` | Verification analysis notes for landed WPs | — | 90k tokens | `TASK-013` | Planned | after deps |
| 49 | `TASK-017` | Refresh subsystem tracker (md + html) for what landed | — | 100k tokens | `TASK-016` | Planned | after deps |
| 50 | `TASK-018` | Docs HTML pages: status, metadata, links, a11y basics | — | 100k tokens | `TASK-017` | Planned | after deps |
| 51 | `TASK-019` | README and developer guide (setup, test, gates, layout) | — | 60k tokens | `TASK-002` | Planned | after deps |
| 52 | `TASK-020` | Trace/ID consistency checker beyond `plan_check` | — | 100k tokens | `TASK-000` | Planned | after deps |
| 53 | `TASK-021` | Read-only audit: PRs #4/#6, stale branches, repo hygiene | — | 70k tokens | `TASK-000` | Planned | after deps |
| 54 | `TASK-022` | Dependency and licence audit (report only) | — | 40k tokens | `TASK-000` | Planned | after deps |
| 55 | `TASK-023` | Next-phase plan from PLAN-001 critical path | — | 100k tokens | `TASK-017` | Planned | after deps |
| 56 | `TASK-024` | Morning review pack | — | 150k tokens | `TASK-000`, `TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005`, `TASK-006`, `TASK-008`, `TASK-009`, `TASK-010`, `TASK-011`, `TASK-012`, `TASK-013`, `TASK-014`, `TASK-015`, `TASK-016`, `TASK-017`, `TASK-018`, `TASK-019`, `TASK-020`, `TASK-021`, `TASK-022`, `TASK-023` | Planned | after deps |
| 57 | `TASK-101` | WP-ING-02 alternative ingestion paths | `WP-ING-02` | 150k tokens | `TASK-024` | Planned | after deps |
| 59 | `TASK-102` | WP-ING-03 ingestion diagnostics, persistence, staleness extension | `WP-ING-03` | 120k tokens | `TASK-024` | Planned | after deps |
| 61 | `TASK-103` | WP-ANA-06 static function testability and macro resolution | `WP-ANA-06` | 200k tokens | `TASK-024` | Planned | after deps |
| 63 | `TASK-104` | WP-PRJ-02 diff-stable sharded storage | `WP-PRJ-02` | 200k tokens | `TASK-024` | Planned | after deps |
| 65 | `TASK-105` | WP-CORE-06 logging and diagnostic bundle | `WP-CORE-06` | 130k tokens | `TASK-006`, `TASK-024` | Planned | after deps |
| 67 | `TASK-106` | WP-TCH-02 host compiler detection (GCC/Clang) — detection and version report only, no building | `WP-TCH-02` | 150k tokens | `TASK-024` | Planned | after deps |
| 69 | `TASK-107` | Mutation-style test strengthening for `ectt.core` and `ectt.prj` (hand-written mutants, kill-rate report) | — | 150k tokens | `TASK-024` | Planned | after deps |
| 70 | `TASK-108` | Property-based fuzz-style tests for the YAML adapter and schema reader using seeded `random` | — | 150k tokens | `TASK-024` | Planned | after deps |
<!-- END GENERATED: queue -->

### 4.3 Blocked tasks — waiting on D-01…D-04 and open ADRs / SRS questions

Everything here needs an owner answer. "Downstream tasks held" counts tasks that depend, directly or transitively, on the blocked one. Note the critical-path consequence: `WP-COV-01` is gated by **ADR-004**, which is *not* in the D-01…D-04 queue.

<!-- BEGIN GENERATED: blocked -->
| Seq | ID | Title | Blocked by | Downstream tasks held | Why / note |
|---|---|---|---|---|---|
| 71 | `T-01` | Convene ADR-005 licence decision; update LICENSE/LIC-010; re-run gates | `D-01` | 0 | Source status in tracker: Awaiting decision |
| 72 | `T-02` | Write the no-import/provenance rule for vcast-findings assets | `D-01` | 0 | Source status is 'Not Started'. Blocked: its consequence anchor is ADR-005 (D-01). TASK-015 prepares a draft only. |
| 73 | `T-04` | Decide and record the identity model (SDD-003 §6/§7) — memo prepared, decision pending | `D-02` | 1 | Source status in tracker: Awaiting decision |
| 74 | `T-14` | Run-integrity acceptance into WP-EXH-01/02 + WP-CBT-01 | `D-02` | 0 | Source status is 'Not Started', blocked by T-04 (itself awaiting D-02 identity model). |
| 75 | `T-05` | Decide and record platform order | `D-03` | 0 | Source status in tracker: Awaiting decision |
| 76 | `T-06` | DR-06 NFR calibration plan + fixtures; provisional NFRs marked | `D-04` | 0 | Source status in tracker: Awaiting decision |
| 77 | `TASK-007` | WP-CORE-03 platform baseline and offline guarantee | `D-03` | 0 | The backlog queues this while listing D-03 as an owner decision. Encoding Windows and Linux as co-equal is itself answer (c) 'both in parallel', and the decision queue lists WP-CORE-03 as gated by D-03. Conservative reading applie… |
| 78 | `WP-CORE-03` | Platform baseline and offline guarantee | `D-03` | 28 | the platform baseline is the platform order (D-03: Windows-first / Linux-first / parallel); NFR-010/020 wording is pending. |
| 79 | `WP-PKG-07` | License policy, process isolation and automated enforcement | `D-01` | 1 | LIC-010..060 licence policy cannot be implemented until the licence posture (D-01 / ADR-005) is decided. |
| 80 | `WP-COV-01` | Statement and branch coverage from compiler backend | `ADR-004` | 26 | coverage backend strategy is open (ADR-004); integration waits on it — critical-path package. |
| 81 | `WP-PKG-01` | Offline, non-admin, runtime-free installation | `ADR-007` | 11 | distribution/installer choice is open (ADR-007); integration waits on it. |
| 82 | `WP-EXH-04` | Debugger launch with entry breakpoint | `SRS-Q9` | 1 | debugger front-end is an open SRS question (§27 q9); P2 integration waits on it. |
| 83 | `WP-PKG-08` | Separable restrictively-licensed optional components | `D-01` | 0 | separable restrictively-licensed components follow WP-PKG-07 and the licence decision. |
| 84 | `WP-ATG-02` | Symbolic execution engine adapter | `ADR-003` | 1 | symbolic-execution engine choice is open (ADR-003); P3 integration waits on it. |
| 85 | `WP-ATG-03` | Bounded model checking engine | `ADR-003` | 0 | bounded-model-checking engine choice is open (ADR-003). |
| 86 | `WP-COV-05` | MC/DC measurement and form declaration | `SRS-Q2` | 4 | MC/DC form is an open SRS question (§27 q2); P3 acceptance waits on it. |
<!-- END GENERATED: blocked -->

### 4.4 Open pull requests — what they gate

No task in any of the three source plans is *blocked* by PR #4 or PR #6. They matter in three ways:

- **PR #6** (GitHub Projects workflow, `codex/github-projects-workflow`, mergeable) changes `pyproject.toml` (`[tool.pytest]` `pythonpath`) — an adjacent-section edit that `TASK-003`/`TASK-004` (dev extras) can merge with trivially. Its remaining steps are owner actions (secret, flag flip, view grouping, merge) — §6.
- **PR #4** (ADR-008 allocation, `fix/aif-provider-traceability`) is **CONFLICTING**. Much of its content overlaps work already on `docs/pending-decisions` via `T-03`. `TASK-021` produces the read-only overlap audit; the keep/close decision is the owner's.
- **Agents must not open, comment on, merge or close any PR** (BACKLOG §3.3 rule 5). Merging `docs/pending-decisions` into `main` is an owner action that will have to reconcile PR #4.

### 4.5 Planned work packages not yet scheduled

<!-- BEGIN GENERATED: backlog -->
160 PLAN-001 work packages are Planned but not yet scheduled into the overnight queue (by start phase: P1 17, P2 57, P3 60, P4 26). Their full entries are in §8. They become startable only when a human or `TASK-023` schedules them.

Of these, **14** already have every hard dependency satisfied (candidates for `TASK-023`'s ranking):

| WP | Title | Phase | Eff. | Hard deps | Gate / ADR |
|---|---|---|---|---|---|
| `WP-GEN-01` | Harness generation core | P1 | 5w | `WP-ANA-04` | — |
| `WP-CORE-07` | User documentation and text externalisation | P2 | 4w | — | — |
| `WP-SEC-05` | Security disclosure process and supported-version policy | P2 | 1w | — | — |
| `WP-SEC-04` | Log and diagnostic content control | P2 | 2w | `WP-CORE-01` | — |
| `WP-SEC-03` | Untrusted-project warning and configuration-is-data | P2 | 3w | `WP-PRJ-01` | — |
| `WP-ING-04` | Test scope model and resolution | P2 | 5w | `WP-ING-01` | — |
| `WP-ANA-05` | Control flow graph capability | P2 | 6w | `WP-ANA-01`, `WP-SPIKE-01` | `ADR-001` |
| `WP-ANA-08` | Analysis model decision inventory | P2 | 1w | `WP-ANA-04` | — |
| `WP-ANA-09` | Value ranges and dimension metadata in the analysis model | P2 | 1w | `WP-ANA-04` | — |
| `WP-TCM-02` | Data-driven test case model and on-disk format | P2 | 5w | `WP-PRJ-01`, `WP-ANA-04` | `ADR-001` |
| `WP-CORE-05` | Performance, scale and memory envelope | P2 | 4w | — | `ADR-001` |
| `WP-CORE-08` | Self-verification of the tool's own source | P2 | 3w | — | `ADR-001` |
| `WP-MIG-06` | Coexistence with another tool on one project | P3 | 3w | `WP-CORE-01`, `WP-PRJ-01` | — |
| `WP-QUA-05` | Development process and change control documentation | P4 | 3w | — | — |
<!-- END GENERATED: backlog -->

### 4.6 Done

<!-- BEGIN GENERATED: done -->
| Seq | ID | Title | Status | Commit | Branch | Verification |
|---|---|---|---|---|---|---|
| 1 | `WP-SPIKE-01` | CFG sufficiency spike: python-clang against real embedded code | Implemented | `6af7d84` | main (landed) | pass |
| 2 | `WP-SPIKE-02` | Nested type-aware test data editor spike in PySide6 | Implemented | `6af7d84` | main (landed) | pass |
| 3 | `WP-SPIKE-03` | PyInstaller distribution spike onto clean Windows | Implemented | `6af7d84` | main (landed) | pass |
| 4 | `WP-CORE-01` | Determinism, source immutability and output confinement | Implemented | `51bde0b` | main (landed) | pass |
| 5 | `WP-PRJ-01` | Plain-text schema-versioned project store | Implemented | `d9557dd` | main (landed) | pass |
| 6 | `WP-ING-01` | Compilation database ingestion | Implemented | `c80ef9f` | main (landed) | pass |
| 7 | `WP-ANA-01` | C front-end binding and dialect support | Implemented | `ae10ce2` | main (landed) | pass |
| 8 | `WP-ANA-02` | Interface and type extraction | Implemented | `ae10ce2` | main (landed) | pass |
| 9 | `WP-ANA-04` | Analysis model persistence and schema versioning | Implemented | `b5786e0` | main (landed) | failing |
| 10 | `T-03` | SRS change: TOOL-EXE-040 timeout distinct from fail + gate repair (PLG-080/100, COV-150, AIF allocations) | Landed | `3e60d10` | main (via PR#7) | pass |
| 11 | `T-12` | LinkPlan: TOOL-ING-200 + WP-ING-07 + DSN-ING-120 + SDD-002/SDD-003 amendments | Landed | `3e60d10` | main (via PR#7) | pass |
| 12 | `T-07` | Extend ing: response-file expansion, build-context identity, build tags (TOOL-ING-210/220, DSN-ING-130/140) | Landed | `6a299d4` | main (via PR#7) | pass |
| 13 | `T-08` | ING-100 fail-closed staleness: content fingerprints (compdb, sources, response files, include surface) + invalidation fixtures | Landed | `6f7b740` | main (via PR#7) | pass |
| 14 | `T-09` | S1 schema 1.1: mandatory decision + unsupported inventories, reader gates fail closed | Landed | `83bf22a` | main (via PR#7) | pass |
| 15 | `T-10` | Value ranges + array dimension metadata in ana model and schema 1.2 (round-trip + conformance tests) | Landed | `b7adfad` | main (via PR#7) | pass |
| 16 | `T-11` | Eligibility/observability gate: assess_eligibility over the S1 model (channels, named reasons), consumed by CMP-ATG | Landed | `96c4b23` | main (via PR#7) | pass |
| 17 | `T-13` | Compound-test defer decision + migration flag | Landed | `1ad783b` | main (via PR#7) | pass |
| 18 | `T-16` | Coverage completeness state: TOOL-COV-180 + SDD-002 §6.1/§7.2/§8 amendments + DSN-COV-110 | Landed | `ca77dbd` | main (via PR#7) | pass |
| 19 | `T-17` | MC/DC limit probing + boundary fixtures + macro-variant merge rule | Landed | `c6339e3` | docs/pending-decisions (unpushed) | pass |
| 20 | `T-18` | Known-answer MC/DC corpus mandate | Landed | `966b21e` | docs/pending-decisions (unpushed) | pass |
| 21 | `T-19` | Verdict dedup + labeled denominators + 2/1 anomaly fixture | Landed | `afa4339` | docs/pending-decisions (unpushed) | pass |
| 22 | `T-20` | Crashed-run coverage admission rule | Landed | `93171a2` | docs/pending-decisions (unpushed) | pass |
| 23 | `T-21` | Harness-vs-reference agreement check in WP-QUA-03 | Landed | `0ae84c1` | docs/pending-decisions (unpushed) | pass |
| 24 | `T-22` | Clean-machine endpoint gate in WP-PKG (ADR-007) | Landed | `f167005` | docs/pending-decisions (unpushed) | pass |
| 25 | `T-15` | HostProfile/ABI-divergence record section | Landed | `a412112` | docs/pending-decisions (unpushed) | pass |
<!-- END GENERATED: done -->

---

## 5. Agent handoff rules

You are an executor. Ambiguity → choose the most conservative reading, record the assumption in the task's `notes` (and in `docs/glm-night/GLM_NIGHT_LOG.md` once `TASK-000` has created it), and continue. These rules restate and, where marked **override**, tighten `BACKLOG_GLM_NIGHT.md` §3.

### 5.1 Setup (once)

```bash
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-unit-glm-night -b glm-night/20261117 docs/pending-decisions
cd ../wt-unit-glm-night
py -3.11 -m venv .venv          # or: python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```

Work only in `E:\projects\UDS_Simulator\wt-unit-glm-night` on `glm-night/20261117`. Never use the main checkout's `.venv` (an editable install there imports the wrong `src`). The system Python lacks `clang`; use `.venv`. If `libclang` fails to install, mark clang-dependent tasks (TASK-008, TASK-103) failed-technical (§5.3) and continue.

### 5.2 Pick the next task

1. Read the JSON block in `EXEC-PLAN-001-tracker.html` (or §4.2). Ensure `git status` is clean.
2. Candidates = tasks with `status = "Planned"`, `lane = "queue"`, empty `blockedBy`, and **all** `deps` Implemented/Landed. Pick the **lowest `seq`**.
3. If the queue has no candidate: the reserve lane (`TASK-101…`) becomes eligible **only after `TASK-024` is Landed**. If nothing is eligible, write the final report and stop.
   **`TASK-024` exception:** it is the one task exempt from dependency gating. Its listed dependencies exclude the owner-blocked `TASK-007`, and it must also run when other core tasks ended as technical failures (§5.3) or `SKIPPED (dep)` — start it once every other core task is Landed or has such a log entry, or when the token budget reaches ≈ 2.8M.
4. Never pick a `Blocked` task, a `lane = backlog` WP, or a `lane = scheduled` WP directly. Never skip ahead because a task looks easy.
5. Re-check dependencies against the JSON, not memory: a dependency that failed or was skipped makes its dependents `SKIPPED (dep)` — leave them Planned with a note.

### 5.3 Update status

| When | Edit in the tracker JSON | Notes |
|---|---|---|
| You start | `status: "In Progress"` | Add start note to `notes`. |
| Task landed (acceptance met, full gate green) | TASK/T: `status: "Landed"`, `lane: "done"`, `commit: "<sha>"`, `verifyState: "pass"` | Same commit as the work. |
| Task delivers a WP | WP: `status: "Implemented"`, `lane: "done"`, `commit`, `verifyState` — **only if the WP's PLAN-001 exit criterion is actually met**; else leave Planned and write `notes: "partial: <what remains>"` | WPs never flip on a TASK alone. |
| Technical failure (libclang, timeout > 15 min, unfixable red test) | keep `status: "Planned"`; `notes: "FAILED|BLOCKED (technical): <command, error excerpt, what you tried>"` | Per BACKLOG §3.4 (cap effort at 1.5× estimate, restore only your own paths). Do **not** use `Blocked` — that status means an owner decision. |
| Owner answers a decision | Only the owner (or a session quoting the owner's answer verbatim) sets `decisions[].state` to `Decided: <answer>`, clears `blockedBy` on the unblocked tasks, and sets them to `Planned` | Agents never infer an answer. |

Then run `python design/trace/unified_plan_sync.py` (§5.9). If you re-ran the gates, also update `meta.asOf`, `meta.head`, `meta.tests` and `meta.gates`.

### 5.4 Gates (run before every commit)

**G-FULL** — the full gate:

```bash
.venv/Scripts/python -m pytest -q -p no:cacheprovider
.venv/Scripts/python design/trace/plan_check.py
.venv/Scripts/python design/trace/trace_check.py
```

**G-GATES** = the last two commands. Run the narrow test file first, G-FULL before every commit.

| Gate | What it enforces | Expected today |
|---|---|---|
| `plan_check.py` | SRS ↔ PLAN-001 §5.5 allocation (one primary owner per non-Future requirement), dependency closure, no cycles, derived tables not drifted. `--write` regenerates derived tables — run it **only** in a task that says so. | exit 0 — 346 requirements, 344 allocations, 191 packages, 642 person-weeks, 52-week bound |
| `trace_check.py` | SRS ↔ design register allocation, graph well-formedness. | exit 0 — 344/344 allocated, 259 design elements |
| `pytest` | Behaviour tests. | **before `TASK-001`: 234 passed, 3 failed, 1 skipped** (the 3 `test_persist` failures are the *only* permitted red); **after: all green** |

Rules: never delete or weaken tests, thresholds or gates to get green (a real unfixable failure → `xfail(strict=True, reason=…)` plus a log entry); no new runtime dependencies (dev-only deps only in `TASK-003/004`); new code is deterministic (no wall-clock, randomness, unordered iteration in outputs — use `ectt.core.determinism`); each new module gets the happy path plus at least two error/edge cases.

### 5.5 Branches and the unpushed `docs/pending-decisions`

| Fact | Consequence |
|---|---|
| `docs/pending-decisions` is **10 commits ahead of `origin/main` and has never been pushed** (no remote branch). It holds `T-15`, `T-17…T-22`, the decision-queue commit and the backlog. | It is the only copy of that work. |
| Sixteen review tasks: `T-03`, `T-07…T-13`, `T-16` reached `main` via **PR #7**; `T-15`, `T-17…T-22` exist **only** on `docs/pending-decisions`. | Always base on its tip, never on local `main`. |
| **Local `main` is stale** relative to `origin/main` (PR #7 merged on the remote). | Never base work on local `main`; compare against `origin/main` (`git fetch` is allowed — it is read-only). |

Rules:

1. **Never** work directly on `docs/pending-decisions` or `main`. Use the worktree branch `glm-night/20261117` cut from the `docs/pending-decisions` tip (§5.1).
2. **Never** rebase, amend, force-push, reset or delete `docs/pending-decisions` (or any pushed branch). One commit per task; stage only the paths you touched (`git add <paths>`, never `git add -A`); never `--no-verify`.
3. Commit message exactly: `[GLM-NIGHT] TASK-012: <imperative summary, ≤70 chars>` with a body (what, why, how verified, `Files:`). For `T-`/`WP-` work use that task's ID.
4. **Override of BACKLOG §3.2 — do not push.** `glm-night/20261117` contains the 10 unpushed commits; pushing it would publish them to the public repo while D-01 (licence) is open. Commit locally, record `push pending owner approval` in the log, and let the owner push (or authorise a push explicitly).
5. Merging anything into `main` is an owner action via PR. PR #4 is CONFLICTING and PR #6 is a separate owner decision (§4.4).

### 5.6 Stop and escalate — never decide

Stop work on the task, leave it as is, and escalate when **any** of these is true:

- the task (or a task it depends on) has a non-empty `blockedBy` (D-01…D-04, ADR-003/004/005/007, SRS-Q2/Q9);
- doing the task would *require choosing* a licence, an identity model, a platform order, an NFR calibration, a coverage backend, a symbolic-execution engine, a distribution format, an MC/DC form or a debugger front-end — even implicitly (for example an implementation that ranks Windows vs Linux, or edits `LICENSE`);
- the task needs to edit accepted ADR text, `SRS-001` requirement text, `LICENSE`/`LICENSEES`, a decision-register state, or any file on the do-not-touch list;
- it needs credentials, a secret, network access from product code, hardware, or a PR/issue/branch action.

How to escalate:

1. Do **not** implement a "provisional" workaround that bakes in a choice.
2. In the tracker JSON set `notes` to `ESCALATE: <the question> — options: <a/b/c> — blocked: <ids>`; keep (or set) `status: "Blocked"` with the right `blockedBy` only when an owner decision is the cause.
3. Pick the next startable task (§5.2) and continue. At the end of the run list every escalation in `docs/glm-night/MORNING_REVIEW.md` (`TASK-024`) and in your final report.
4. Decision memos and drafts (`TASK-014`, `TASK-015`) are allowed: they live under `docs/proposals/`, are labelled draft/recommendation, change no decision state, and must say they are not adopted.

**Two deliberate deviations from the backlog, made so no agent decides for the owner:** (a) `TASK-007` / `WP-CORE-03` is **Blocked on D-03** — the backlog's "encode Windows and Linux in parallel without ranking them" is itself answer (c) of D-03; the owner must answer D-03 or explicitly approve that encoding first. (b) Pushing is owner-approved (§5.5.4).

### 5.7 Hard safety rules (from BACKLOG §3.3, unchanged)

1. Never make an owner decision; do not edit ADR files, decision states, `LICENSE`/`LICENSEES`, or flip "Awaiting decision" statuses.
2. Do not edit accepted `SRS-001` text; derived tables only via `plan_check.py --write`, only in tasks that say so.
3. Do not touch `aidlc/` state/audit files, `.claude/`, `.agents/`, `.agy-staff/`, `.zcode/`, `vcast-findings/` (read-only reference), or `spikes/`.
4. Never copy code, schema, strings or identifiers out of `vcast-findings/` into `src/`.
5. No network calls from product code or tests; no secrets; no publishing or posting.
6. Never delete files unless the task names them (leave the stray `NUL` file alone). Commands expected to exceed 15 minutes or needing interaction → kill, mark technically failed (§5.3).

### 5.8 Definition of done (per task)

All acceptance criteria in its card are met and demonstrable by its verification commands; G-FULL is green apart from the documented baseline; the commit exists with the `[GLM-NIGHT]` format; the tracker JSON and this document are updated and in sync (§5.9); `docs/glm-night/GLM_NIGHT_LOG.md` has the row (`| TASK-id | DONE/PARTIAL/BLOCKED/FAILED/SKIPPED | sha | tokens | cumulative | notes |`).

### 5.9 Keeping the tracker and this plan in sync

```bash
python design/trace/unified_plan_sync.py          # regenerate the generated sections
python design/trace/unified_plan_sync.py --check  # exit 1 if stale (run before committing)
```

The script needs only the Python standard library. Never hand-edit text between `GENERATED` markers; edit the JSON block in the tracker (one task per line) and re-run it. Hand-written sections may be edited freely.

---

## 6. Decisions and open pull requests

### 6.1 Pending user decisions and open gates

<!-- BEGIN GENERATED: decisions -->
### D-01 · Licence posture — **Pending user decision**

**Question:** Which licence does the project ship under? The repo is public showing AGPL-3.0 but SRS LIC-010 requires a permissive licence — one of the two must move.

| Option | Choice | Consequence |
|---|---|---|
| a | Keep AGPL-3.0 | Amend LIC-010 to require AGPL-3.0; no relicense churn; strong copyleft deters commercial/embedding use. |
| b | Apache-2.0 | Satisfies LIC-010 as written; permissive + explicit patent grant; requires repo licence change. |
| c | MIT | Simplest permissive option satisfying LIC-010; no patent grant. |
| d | Proprietary / closed | Repo goes private, AGPL dropped, LIC-010 becomes proprietary; loses public visibility. |

- **Priority:** P0 · **References:** `T-01`, `NR-01`, `ADR-005`, `LIC-010`
- **Gates:** publicising the repo / contributor solicitation; WP-PKG-07 (LIC-010..060); T-02 no-import rule (ADR-005 anchor)
- **Unblocks:** `T-01`, `T-02`, `WP-PKG-07`, `WP-PKG-08` · **Watch:** `TASK-015`, `TASK-019`, `TASK-022`
- **Answer:** _awaiting decision — agents must not answer._

### D-02 · Identity model — **Pending user decision**

**Question:** Stable ids + content digests vs revision entities? The T-04 memo recommends stable ids + digests (a recommendation, not a decision).

| Option | Choice | Consequence |
|---|---|---|
| a | Stable ids + digests (memo recommendation) | SDD-003 §6/§7 amendment + one sentence in SDD-002 S2/S3; WP-TCM-02 implements digest binding; unblocks T-14. |
| b | Revision entities | Heavier model and schema churn; conflicts with the accepted stable-id + digest staleness model (RV-05 F-05). |
| c | Defer | T-14 stays blocked; revisit after T-17..T-22. |

- **Priority:** P0 · **References:** `T-04`, `NR-04`, `SDD-003 §6/§7`
- **Gates:** T-04 → T-14 (run-integrity acceptance in WP-EXH-01/02, WP-CBT-01); WP-TCM-02 digest binding
- **Unblocks:** `T-04`, `T-14` · **Watch:** `WP-TCM-02`
- **Answer:** _awaiting decision — agents must not answer._

### D-03 · Platform order — **Pending user decision**

**Question:** Windows pilot first or Linux-first (NFR-010/020)?

| Option | Choice | Consequence |
|---|---|---|
| a | Windows pilot first | Matches the current dev platform; WP-SPIKE-03 already done; Linux CI kept green in parallel as a compat check. |
| b | Linux-first | Matches typical embedded toolchains/CI; Windows compatibility tracked as secondary. |
| c | Both in parallel | Equal co-pilots from day one; highest setup and test-matrix cost. |

- **Priority:** P1 · **References:** `T-05`, `NR-05`, `NFR-010`, `NFR-020`
- **Gates:** NFR-010/020 wording; WP-CORE-03 (platform baseline); WP-GUI-01 platform-support planning
- **Unblocks:** `T-05`, `TASK-007`, `WP-CORE-03` · **Watch:** `WP-GUI-01`
- **Answer:** _awaiting decision — agents must not answer._

### D-04 · DR-06 NFR calibration — **Pending user decision**

**Question:** How should DR-06 NFR calibration be handled before pilot data exists?

| Option | Choice | Consequence |
|---|---|---|
| a | Defer to post-pilot | Provisional NFRs stay marked; calibrate before WP-CORE-05 exits P2 (already mandated by NR-06). |
| b | Calibrate now | Set provisional targets from current analysis runs; revisit post-pilot. |
| c | Drop DR-06 | Remove the requirement if no longer meaningful. |

- **Priority:** P2 · **References:** `T-06`, `NR-06`, `DR-06`
- **Gates:** T-06; WP-CORE-05 NFR thresholds
- **Unblocks:** `T-06` · **Watch:** `WP-CORE-05`
- **Answer:** _awaiting decision — agents must not answer._

### Other open gates (not in the D-01…D-04 queue)

| ID | Title | State | Gates |
|---|---|---|---|
| `ADR-001` | Language, GUI, qualification tiers | Accepted 2026-09-19 | — |
| `ADR-002` | Project data format (restricted YAML) | Accepted 2026-09-26 | — |
| `ADR-003` | Symbolic execution | Open — not in the D-queue | `WP-ATG-02`, `WP-ATG-03` |
| `ADR-004` | Coverage backend strategy | Open — not in the D-queue | `WP-COV-01` |
| `ADR-005` | Licence selection | Open (same question as D-01) | `T-01`, `T-02`, `WP-PKG-07`, `WP-PKG-08` |
| `ADR-006` | Fork or build fresh | Accepted 2026-09-19 (build fresh) | — |
| `ADR-007` | Distribution / installer | Open — not in the D-queue | `WP-PKG-01` |
| `ADR-008` | AI structured-decision provider | Accepted 2026-09-19 | — |
| `SRS-Q2` | SRS §27 q2 — MC/DC form | Open — not in the D-queue | `WP-COV-05` |
| `SRS-Q9` | SRS §27 q9 — debugger front-end | Open — not in the D-queue | `WP-EXH-04` |
<!-- END GENERATED: decisions -->

### 6.2 Open pull requests

<!-- BEGIN GENERATED: prs -->
### PR#6 · Add GitHub Projects workflow for the ECTT — Delivery board

- **State:** OPEN · **Mergeable:** MERGEABLE · `codex/github-projects-workflow` → `main` · https://github.com/suduli/embedded-c-unit-test-tool/pull/6
- **Checks:** Importer tests (no credentials): SUCCESS; Synchronize project: SKIPPED (flag off)
- **What it does:** Importer tools/github_projects.py, project-sync.yml, issue/PR templates, docs/projects/README.md, 70 offline tests. Sync is disabled by default (ECTT_PROJECTS_SYNC_ENABLED unset). Touches pyproject.toml ([tool.pytest] pythonpath adds tools).
- **Related tasks:** `TASK-002`, `TASK-003`, `TASK-021` · **Tasks it blocks:** none in the source plans
- **Note:** No task in the three source plans is blocked by this PR. Agents must not open, comment on, merge or close it (BACKLOG §3.3 rule 5).
- **Remaining steps:**
  - [ ] `PR6-a` Create the ECTT_PROJECTS_TOKEN repository secret (owner action; never by an agent)
  - [ ] `PR6-b` Flip the sync flag (ECTT_PROJECTS_SYNC_ENABLED) once the baseline is approved
  - [ ] `PR6-c` Configure view grouping on the ECTT — Delivery project
  - [ ] `PR6-d` Merge PR #6 (owner action)

### PR#4 · Allocate the ADR-008 AI-provider requirements and restore the trace gate

- **State:** OPEN · **Mergeable:** CONFLICTING · `fix/aif-provider-traceability` → `main` · https://github.com/suduli/embedded-c-unit-test-tool/pull/4
- **Checks:** Requirement allocation: SUCCESS
- **What it does:** Renumbers the extension point to TOOL-PLG-100, allocates AIF-220..260, adds DSN-AIF-140/150/160 and DSN-PLG-050, WP-AIF-14. Much of this overlaps work already on docs/pending-decisions via T-03 (3e60d10: DSN-PLG-050, DSN-AIF-140/150 present; WP-AIF-14 present; DSN-AIF-160 absent — AIF-260 is allocated through another element). Overlap is an observation for TASK-021, not a verdict.
- **Related tasks:** `WP-AIF-14`, `WP-PLG-04`, `T-03`, `TASK-021` · **Tasks it blocks:** none in the source plans
- **Note:** Mergeable state is CONFLICTING. These steps are derived from reading the PR; they are proposals, not recorded owner decisions.
- **Remaining steps:**
  - [ ] `PR4-a` Owner decides whether PR #4 is still wanted (TASK-021 produces the overlap audit; read-only)
  - [ ] `PR4-b` If wanted: rebase/resolve conflicts against current main and re-run both gates (owner or an explicitly authorised session)
  - [ ] `PR4-c` Merge, or close as superseded (owner action)
<!-- END GENERATED: prs -->

---

# 7. Task cards

Full per-task detail for everything an agent may pick up, escalate, or has completed as a work package. The same data, filterable, is in the tracker. Fields are explained in §3.3.

<!-- BEGIN GENERATED: cards -->
## 7.1 Ready queue — core overnight backlog (BACKLOG TASK-000 … TASK-024)

### TASK-000 — Worktree, venv, baseline, log

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 26 · **Source:** BACKLOG · **Area:** setup · **Est.:** 30k tokens
- **Dependencies:** —
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `WP-ANA-04`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)` · **Commit:** `e58eac4`
- **Files likely touched:** `docs/glm-night/baseline.md`, `docs/glm-night/GLM_NIGHT_LOG.md`, `../wt-unit-glm-night (worktree) + .venv`
- **Acceptance criteria:**
  1. docs/glm-night/baseline.md and GLM_NIGHT_LOG.md exist
  2. baseline lists exactly the 3 known failures: tests/ana/test_persist.py::test_real_extraction_assemble_write_read_roundtrip, ::test_schema_version_gate_newer_minor_accepted_and_unknown_fields_ignored, ::test_assemble_emits_1_1_with_not_extracted_inventory (or states the difference)
  3. baseline counts recorded: 234 passed / 3 failed / 1 skipped, plan_check 346/344/191, trace_check 344/344
  4. commit exists
- **Verification** (pass):
  - `git worktree list | grep wt-unit-glm-night`
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider (expect 3 failed, 234 passed, 1 skipped)`
  - full gate **G-FULL** (see §5.4)
- **Notes:** Landed 2026-11-18: worktree glm-night/20261117 created from 26ff2d7; dedicated .venv (py3.13) + editable install OK; baseline 234 passed / 3 failed / 1 skipped (exactly the 3 documented test_persist failures), plan_check 346/344/191 exit 0, trace_check 344/344 exit 0, sync --check OK; baseline.md + GLM_NIGHT_LOG.md written. Landing sha backfilled at the next tracker-touching commit: a landing commit cannot contain its own sha (precedent: 26ff2d7 backfilled the T-15/T-17..T-22 shas).

### TASK-001 — Fix the 3 failing `test_persist` tests (schema 1.0 → 1.2 drift)

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 27 · **Source:** BACKLOG · **Area:** tests · **Est.:** 70k tokens
- **Dependencies:** `TASK-000`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-100`, `TOOL-PAR-110`
- **Work packages:** `WP-ANA-04` · **Related:** `T-09`, `T-10`
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)` · **Commit:** `aaf88a1`
- **Files likely touched:** `tests/ana/test_persist.py`, `src/ectt/ana/persist.py (only if a real regression is found)`
- **Acceptance criteria:**
  1. the 3 named test_persist tests pass (assert the module's own current-version constant, not a new literal)
  2. compatibility-rule tests (older/newer minor, different major) stay meaningful
  3. no other test changes status; suite ends 237 passed / 0 failed / 1 skipped
  4. commit body explains each failure's root cause
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/test_persist.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** Landed 2026-11-18. Root causes: (1) test_real_extraction_assemble_write_read_roundtrip pinned the assembler's emitted version with '1.0' literals (3 sites) - written at WP-ANA-04 when 1.0 was current; the emitted version existed only as an inline literal in persist.py, so the 1.1 (T-09) and 1.2 (T-10) schema bumps stranded it. (2) test_schema_version_gate_newer_minor_accepted_and_unknown_fields_ignored fed a 1.5 fixture lacking the inventories mandatory at >= 1.1 (TOOL-PAR-140/150, introduced by T-09), so the reader rejected it with missing_decision_inventory; fixture upgraded to a valid modern document, gate-rule intent (newer minor accepted, unknown fields ignored) preserved. (3) test_assemble_emits_1_1_with_not_extracted_inventory pinned the emitted version '1.1' (T-09 era); the 1.2 bump (T-10) moved assemble() to 1.2. Fix: exposed SCHEMA_VERSION_CURRENT in persist.py (assemble() now uses it; exported in __all__), tests assert the constant instead of literals; renamed test 3 to test_assemble_emits_current_version_with_not_extracted_inventory so the name no longer carries a version literal. Suite 237 passed / 0 failed / 1 skipped (criterion met); older/newer-minor and different-major gate rules untouched and still meaningful. Landing sha backfilled at the next tracker-touching commit.

### TASK-002 — CI workflow: pytest + design gates, Linux & Windows

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 28 · **Source:** BACKLOG · **Area:** gaps · **Est.:** 50k tokens
- **Dependencies:** `TASK-001`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `WP-CORE-08`, `PR#6`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)` · **Commit:** `35487c4`
- **Files likely touched:** `.github/workflows/tests.yml (new; traceability.yml untouched)`
- **Acceptance criteria:**
  1. workflow runs pytest + both design gates on ubuntu-latest and windows-latest, Python 3.11, pinned actions, permissions: contents: read
  2. YAML parses; the exact commands in it succeed locally
  3. log notes that CI itself could not be run
- **Verification** (pass):
  - `.venv/Scripts/python -c "import yaml;yaml.safe_load(open('.github/workflows/tests.yml'))"`
  - full gate **G-FULL** (see §5.4)
- **Notes:** Landed 2026-11-18: .github/workflows/tests.yml added - matrix ubuntu-latest/windows-latest, Python 3.11, actions/checkout@v4 + actions/setup-python@v5 (same major-tag pins as the existing traceability.yml house convention; full-commit-SHA pinning not applied), permissions: contents: read, workflow_dispatch included; runs the three G-FULL commands (pytest -q -p no:cacheprovider; python design/trace/plan_check.py; python design/trace/trace_check.py). YAML parses locally; each of the exact commands succeeds locally on Windows (237 passed / 1 skipped, both gates exit 0). CI itself could not be run: the branch is unpushed (push is owner-approved per EXEC-PLAN-001 5.5.4), so the workflow has never executed on GitHub runners - first run happens when the owner pushes or opens a PR. traceability.yml untouched; PR#6's project-sync.yml is a different file. Landing sha backfilled at the next tracker-touching commit.

### TASK-003 — Add ruff + mypy config and triage findings

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 29 · **Source:** BACKLOG · **Area:** gaps · **Est.:** 120k tokens
- **Dependencies:** `TASK-001`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `PR#6`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `pyproject.toml ([project.optional-dependencies].dev, [tool.ruff], [tool.mypy])`, `src/ (mechanical fixes only)`, `docs/glm-night/lint-baseline.md`
- **Acceptance criteria:**
  1. ruff exits 0 or has a documented ignore list with reasons
  2. mypy runs; remaining errors listed in lint-baseline.md with counts per rule
  3. no sweeping reformat in git diff --stat
  4. full gate green
- **Verification** (pass):
  - `.venv/Scripts/python -m ruff check .`
  - `.venv/Scripts/python -m mypy src`
  - full gate **G-FULL** (see §5.4)
- **Notes:** PR#6 edits pyproject.toml ([tool.pytest] pythonpath) — adjacent-section edit, expect an easy merge. Landed 2026-11-18. ruff 0.17.5 + mypy 2.4.1 + types-PyYAML added to dev extras (dev-only deps allowed in TASK-003/004). Config in pyproject: [tool.ruff] scoped to owned paths (spikes/vcast-findings/aidlc/design/docs/assets excluded - do-not-touch or out-of-scope), explicit select (E4/E7/E9,F,B,I,UP,SIM,C4,RUF,PERF,PIE,FURB,PLW,BLE), reasoned ignores (RUF022 semantic __all__ grouping; F401 in __init__ re-exports; BLE001 in tests); [tool.mypy] python_version 3.11. Result: ruff check . exit 0 (baseline 118 in scope: 65 auto-fixes + 39 hand fixes incl. 3 real F821 missing imports shared with mypy; noqa'd 1 PLW0603 singleton + 2 deliberate BLE001 fallbacks with reasons); mypy src exit 0 (baseline 11 -> 0; 2 yaml Event attr-defined errors surfaced only after stubs installed, fixed with commented inline ignores). Suite 237 passed / 1 skipped unchanged. Full triage with per-rule counts + excluded-path findings recorded in docs/glm-night/lint-baseline.md. No sweeping reformat (34 files, +167/-152). Landing sha backfilled at the next tracker-touching commit.

### TASK-004 — Coverage baseline and gap-filling tests (≥80% on core/prj/ing)

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 30 · **Source:** BACKLOG · **Area:** tests · **Est.:** 200k tokens
- **Dependencies:** `TASK-001`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `WP-CORE-08`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `pyproject.toml (pytest-cov in dev extras)`, `tests/core/`, `tests/prj/`, `tests/ing/`, `docs/glm-night/coverage-baseline.md`
- **Acceptance criteria:**
  1. line coverage ≥ 80% on ectt.core, ectt.prj and ectt.ing
  2. coverage-baseline.md shows before/after per package; ana gaps listed only
  3. no assert-True tests, no new pragma: no cover
  4. full gate green
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider --cov=ectt.core --cov=ectt.prj --cov=ectt.ing --cov-report=term-missing`
  - full gate **G-FULL** (see §5.4)

### TASK-005 — ADR-002 grammar: rejection and preservation test suite

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 31 · **Source:** BACKLOG · **Area:** tests · **Est.:** 150k tokens
- **Dependencies:** `TASK-001`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PRJ-010`, `TOOL-PRJ-020`, `TOOL-PRJ-070`
- **Work packages:** `WP-PRJ-01` · **Related:** —
- **ADRs:** `ADR-002` · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `tests/prj/test_adr002_conformance.py (new)`, `src/ectt/prj/yaml_adapter.py (only a minimal in-ADR fix)`
- **Acceptance criteria:**
  1. every restricted-grammar rule named in ADR-002 maps to ≥ 1 test (docstrings cite ADR section numbers)
  2. forbidden constructs rejected with named errors; byte-stable round trip; key order preserved
  3. genuine adapter bugs: minimal fix or xfail(strict=True) + log
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/test_adr002_conformance.py`
  - full gate **G-FULL** (see §5.4)

### TASK-006 — WP-CORE-02 structured error model, fail-safe, cancellation

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 32 · **Source:** BACKLOG · **Area:** impl · **Est.:** 220k tokens
- **Dependencies:** `TASK-004`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-NFR-090`, `TOOL-NFR-180`
- **Work packages:** `WP-CORE-02` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/core/errors.py (new)`, `src/ectt/prj/errors.py`, `src/ectt/ing/errors.py`, `src/ectt/ana/errors.py`, `tests/core/test_errors.py (new)`, `docs/verification/WP-CORE-02-analysis.md`
- **Acceptance criteria:**
  1. EcttError base with stable code/category/reason/context, JSON-serialisable and deterministic
  2. cancellation token + fail-safe wrapper leaves no partial output in the confined root
  3. existing prj/ing/ana error classes derive from EcttError with unchanged public names, messages and reason values
  4. existing error tests pass unchanged; gate green; WP-CORE-02 analysis note drafted
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/test_errors.py tests/prj tests/ing tests/ana`
  - full gate **G-FULL** (see §5.4)

### TASK-008 — WP-ANA-03 call graph and scope classification

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 34 · **Source:** BACKLOG · **Area:** impl · **Est.:** 250k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-060`
- **Work packages:** `WP-ANA-03` · **Related:** `TASK-001`
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/ana/ (new call-graph module, model.py, persist.py)`, `src/ectt/ana/schema/analysis-model-1.3.schema.json (new)`, `tests/ana/test_callgraph.py (new)`, `tests/ana/test_persist.py (version constant)`, `docs/verification/WP-ANA-03-analysis.md`
- **Acceptance criteria:**
  1. additive minor schema bump 1.3 validates; 1.2 reader rules still work (tests)
  2. indirect calls recorded as unresolved, never guessed; callees classified in-unit/external/library/unresolved
  3. fixtures: direct, static, recursion, function-pointer, undeclared, macro-wrapped
  4. two runs byte-identical; gate green; analysis note drafted
  5. BLOCKED if libclang unusable
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`
  - full gate **G-FULL** (see §5.4)

### TASK-009 — WP-ANA-07 partial-failure resilience

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 36 · **Source:** BACKLOG · **Area:** impl · **Est.:** 130k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-130`, `TOOL-PAR-140`
- **Work packages:** `WP-ANA-07` · **Related:** `T-09`, `T-11`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/ana/persist.py`, `src/ectt/ana/eligibility.py`, `src/ectt/ana/frontend.py`, `tests/ana/ (partial-failure fixtures)`
- **Acceptance criteria:**
  1. a failure in one translation unit/function does not abort the run; the model records a named reason
  2. valid parts extracted, failure inventory present and deterministic
  3. eligibility gate treats failed elements as unmeasurable with the recorded reason
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`
  - full gate **G-FULL** (see §5.4)

### TASK-010 — WP-ING-07 authored link plan ingestion and validation

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 38 · **Source:** BACKLOG · **Area:** impl · **Est.:** 170k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-ING-200`
- **Work packages:** `WP-ING-07` · **Related:** `T-12`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/ing/linkplan.py (new)`, `tests/ing/test_linkplan.py (new)`
- **Acceptance criteria:**
  1. spec clauses (DSN-ING-120) map to tests
  2. invalid plans never partially load; violations carry named reasons (missing objects, duplicates, unknown toolchain keys, absolute paths outside project)
  3. gate green
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/test_linkplan.py`
  - full gate **G-FULL** (see §5.4)

### TASK-011 — WP-PRJ-04 dangling reference detection

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 40 · **Source:** BACKLOG · **Area:** impl · **Est.:** 100k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PRJ-090`
- **Work packages:** `WP-PRJ-04` · **Related:** —
- **ADRs:** `ADR-002` · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/prj/ (reference-check module, project.py integration)`, `tests/prj/ (dangling reference tests)`
- **Acceptance criteria:**
  1. deterministic sorted list of dangling references reported on load (report, not exception, unless SDD says otherwise)
  2. tests for none / one / many / cyclic references pass
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/`
  - full gate **G-FULL** (see §5.4)

### TASK-012 — WP-PRJ-03 schema migration with explicit confirmation

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 42 · **Source:** BACKLOG · **Area:** impl · **Est.:** 200k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PRJ-040`
- **Work packages:** `WP-PRJ-03` · **Related:** —
- **ADRs:** `ADR-002` · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/prj/ (migration framework)`, `tests/prj/ (migration tests)`
- **Acceptance criteria:**
  1. registry of migration steps; plan/dry-run lists changes; apply requires an explicit confirmation token
  2. no implicit migration on load
  3. atomic writes via confined output helpers; failed migration leaves the original byte-identical
  4. tests: dry-run, confirmed, unconfirmed refused, failure leaves original unchanged
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/`
  - full gate **G-FULL** (see §5.4)

### TASK-013 — WP-CORE-04 provenance record and version identification

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 44 · **Source:** BACKLOG · **Area:** impl · **Est.:** 130k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-QUA-060`, `TOOL-INS-110`
- **Work packages:** `WP-CORE-04` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/core/provenance.py (new)`, `src/ectt/__init__.py (__version__)`, `tests/core/ (provenance tests)`
- **Acceptance criteria:**
  1. provenance record reproducible in two runs; no wall-clock fields in the hashed portion
  2. tests cover the changed-input digest case
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`
  - full gate **G-FULL** (see §5.4)

### TASK-014 — Decision memos D-01…D-04 (decision-ready drafts)

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 46 · **Source:** BACKLOG · **Area:** planning · **Est.:** 120k tokens
- **Dependencies:** `TASK-000`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `D-01`, `D-02`, `D-03`, `D-04`, `T-01`, `T-04`, `T-05`, `T-06`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/proposals/decision-memos-20261117.md (new; nothing else changes)`
- **Acceptance criteria:**
  1. four self-contained sections (D-01..D-04): question, options a–d with exact files, unapplied fenced-diff patch text, risks, what unblocks, recommendation labelled as such
  2. no decision state changed anywhere in the repo
- **Verification** (pending):
  - `git diff --stat (only docs/proposals/ changed)`
  - full gate **G-FULL** (see §5.4)

### TASK-015 — T-02 draft: no-import/provenance rule for `vcast-findings/`

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 47 · **Source:** BACKLOG · **Area:** planning · **Est.:** 70k tokens
- **Dependencies:** `TASK-014`
- **Blocking decision / gate:** — · watch `D-01`
- **SRS requirements:** —
- **Work packages:** — · **Related:** `T-02`, `D-01`, `ADR-005`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/proposals/T-02-no-import-rule-draft.md (new)`, `tests/core/test_no_vcast_import.py (new prototype)`
- **Acceptance criteria:**
  1. prototype test passes today and fails on a planted fixture in a temp dir
  2. reads vcast-findings/ only to build in-memory deny-lists; nothing copied into the repo
  3. proposal states it depends on D-01 and is NOT adopted
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/test_no_vcast_import.py`
  - full gate **G-FULL** (see §5.4)

### TASK-016 — Verification analysis notes for landed WPs

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 48 · **Source:** BACKLOG · **Area:** docs · **Est.:** 90k tokens
- **Dependencies:** `TASK-013`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `WP-CORE-01`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/verification/WP-CORE-01-analysis.md`, `docs/verification/WP-<landed>-analysis.md (CORE-02/04, ANA-03/07, ING-07, PRJ-03/04; CORE-03 only if unblocked)`
- **Acceptance criteria:**
  1. every referenced test id exists (check with pytest --collect-only)
  2. format follows docs/verification/WP-ANA-04-analysis.md
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest --collect-only -q -p no:cacheprovider`
  - full gate **G-FULL** (see §5.4)
- **Notes:** Declared dependency is TASK-013 only, but the note set covers WP-CORE-02/04, ANA-03/07, ING-07, PRJ-03/04 — treat TASK-006…TASK-013 (except a blocked TASK-007) as effective prerequisites.

### TASK-017 — Refresh subsystem tracker (md + html) for what landed

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 49 · **Source:** BACKLOG · **Area:** docs · **Est.:** 100k tokens
- **Dependencies:** `TASK-016`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `WP-ANA-08`, `WP-ANA-09`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md`, `docs/reviews/2026-11-07-subsystem-task-tracker.html`, `EXEC-PLAN-001-tracker.html (status sync; see handoff rules)`
- **Acceptance criteria:**
  1. WP statuses → Complete only where the PLAN-001 §5.4/§5.5 exit criterion is actually met; header counts match tables
  2. T-xx / D-xx statuses unchanged
  3. plan_check --write only if derived tables need it; gates green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-018 — Docs HTML pages: status, metadata, links, a11y basics

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 50 · **Source:** BACKLOG · **Area:** docs-site · **Est.:** 100k tokens
- **Dependencies:** `TASK-017`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/index.html`, `docs/components.html`, `docs/doc-map.html`, `docs/oss-integration.html`, `docs/glm-night/docs-html-audit.md`
- **Acceptance criteria:**
  1. title/meta description/lang/heading order/alt/link targets/contrast (AA) audited with before/after in docs-html-audit.md
  2. no external network assets
  3. traceability gate still green (workflow triggers on docs/index.html and docs/components.html)
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-019 — README and developer guide (setup, test, gates, layout)

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 51 · **Source:** BACKLOG · **Area:** docs · **Est.:** 60k tokens
- **Dependencies:** `TASK-002`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `D-01`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `README.md`, `docs/DEVELOPING.md (new)`
- **Acceptance criteria:**
  1. every command in the docs was executed successfully in the worktree
  2. no licence choice stated (link LICENSE as-is)
  3. status table = implemented vs planned WPs
- **Verification** (pending):
  - `run each documented command`
  - full gate **G-FULL** (see §5.4)

### TASK-020 — Trace/ID consistency checker beyond `plan_check`

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 52 · **Source:** BACKLOG · **Area:** gaps · **Est.:** 100k tokens
- **Dependencies:** `TASK-000`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `design/trace/id_check.py (new)`, `tests/design/test_id_check.py (new)`, `docs/glm-night/id-check-baseline.md`
- **Acceptance criteria:**
  1. reports dangling and duplicate WP-/TOOL-/DSN-/T-NN/NR-NN/ADR-NNN ids; non-zero exit on dangling
  2. deterministic and < 20 s
  3. pre-existing findings listed in id-check-baseline.md; not wired into CI
- **Verification** (pending):
  - `.venv/Scripts/python design/trace/id_check.py`
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/design/test_id_check.py`
  - full gate **G-FULL** (see §5.4)

### TASK-021 — Read-only audit: PRs #4/#6, stale branches, repo hygiene

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 53 · **Source:** BACKLOG · **Area:** GitHub · **Est.:** 70k tokens
- **Dependencies:** `TASK-000`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** `PR#4`, `PR#6`
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/glm-night/repo-audit.md (new; report only)`
- **Acceptance criteria:**
  1. every local/remote branch and both PRs have a row and a recommendation
  2. no action taken (no PR/issue/branch changes)
- **Verification** (pending):
  - `gh pr view 4 / gh pr view 6 (read-only)`
  - `git branch -a -vv`

### TASK-022 — Dependency and licence audit (report only)

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 54 · **Source:** BACKLOG · **Area:** gaps · **Est.:** 40k tokens
- **Dependencies:** `TASK-000`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** `D-01`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/glm-night/dependency-audit.md (new; report only)`
- **Acceptance criteria:**
  1. table of dependency licences vs SRS licensing requirements + recommendations
  2. pyproject.toml untouched
- **Verification** (pending):
  - `git diff --stat (only the report)`

### TASK-023 — Next-phase plan from PLAN-001 critical path

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 55 · **Source:** BACKLOG · **Area:** planning · **Est.:** 100k tokens
- **Dependencies:** `TASK-017`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/proposals/next-phase-plan-20261117.md (new)`
- **Acceptance criteria:**
  1. next 10 decision-free WPs ranked with effort, prerequisites, gating decision, test strategy, agent-ready yes/no
  2. every WP id exists in the register; nothing outside docs/proposals/ changed
- **Verification** (pending):
  - `.venv/Scripts/python design/trace/id_check.py (if TASK-020 landed)`
  - full gate **G-FULL** (see §5.4)

### TASK-024 — Morning review pack

- **Status:** Planned · **Lane:** Ready queue · **Seq:** 56 · **Source:** BACKLOG · **Area:** review · **Est.:** 150k tokens
- **Dependencies:** `TASK-000`, `TASK-001`, `TASK-002`, `TASK-003`, `TASK-004`, `TASK-005`, `TASK-006`, `TASK-008`, `TASK-009`, `TASK-010`, `TASK-011`, `TASK-012`, `TASK-013`, `TASK-014`, `TASK-015`, `TASK-016`, `TASK-017`, `TASK-018`, `TASK-019`, `TASK-020`, `TASK-021`, `TASK-022`, `TASK-023`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `docs/glm-night/MORNING_REVIEW.md (new)`
- **Acceptance criteria:**
  1. each task id appears exactly once with status/commit/tokens
  2. final full-gate output and test count before/after (234+3 → ?)
  3. BLOCKED/FAILED reasons, assumptions needing owner input, review order, review/merge/discard commands
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)
- **Notes:** Runs last of the core queue regardless of numbering; stop starting new tasks at ≈2.8M tokens used and keep ≈150k for it. Dependencies exclude TASK-007 (owner-blocked on D-03). It is exempt from dependency gating on any core task whose log entry is FAILED/BLOCKED/SKIPPED (technical): run it once every other core task is Landed or has such an entry.

## 7.2 Reserve queue (TASK-101 … TASK-108; only after TASK-024)

### TASK-101 — WP-ING-02 alternative ingestion paths

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 57 · **Source:** BACKLOG-RESERVE · **Area:** reserve-ING · **Est.:** 150k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-ING-050`, `TOOL-ING-060`, `TOOL-ING-080`, `TOOL-ING-210`
- **Work packages:** `WP-ING-02` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/ing/`, `tests/ing/`
- **Acceptance criteria:**
  1. WP-ING-02 alternative ingestion paths — follow compdb_adapter.py pattern; no D-gates
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-102 — WP-ING-03 ingestion diagnostics, persistence, staleness extension

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 59 · **Source:** BACKLOG-RESERVE · **Area:** reserve-ING · **Est.:** 120k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-ING-070`, `TOOL-ING-090`, `TOOL-ING-100`, `TOOL-ING-220`
- **Work packages:** `WP-ING-03` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/ing/`, `tests/ing/`
- **Acceptance criteria:**
  1. WP-ING-03 ingestion diagnostics, persistence, staleness extension — builds on T-08 staleness.py
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-103 — WP-ANA-06 static function testability and macro resolution

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 61 · **Source:** BACKLOG-RESERVE · **Area:** reserve-ANA · **Est.:** 200k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-080`, `TOOL-PAR-090`, `TOOL-PAR-170`
- **Work packages:** `WP-ANA-06` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/ana/`, `tests/ana/`
- **Acceptance criteria:**
  1. WP-ANA-06 static function testability and macro resolution — needs libclang; PAR-170 already landed via T-11
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-104 — WP-PRJ-02 diff-stable sharded storage

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 63 · **Source:** BACKLOG-RESERVE · **Area:** reserve-PRJ · **Est.:** 200k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PRJ-030`, `TOOL-PRJ-060`
- **Work packages:** `WP-PRJ-02` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/prj/`, `tests/prj/`
- **Acceptance criteria:**
  1. WP-PRJ-02 diff-stable sharded storage — diff-stable sharded storage (ADR-002 grammar)
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-105 — WP-CORE-06 logging and diagnostic bundle

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 65 · **Source:** BACKLOG-RESERVE · **Area:** reserve-CORE · **Est.:** 130k tokens
- **Dependencies:** `TASK-006`, `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-NFR-130`, `TOOL-NFR-160`
- **Work packages:** `WP-CORE-06` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/core/`, `tests/core/`
- **Acceptance criteria:**
  1. WP-CORE-06 logging and diagnostic bundle — depends on TASK-006
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-106 — WP-TCH-02 host compiler detection (GCC/Clang) — detection and version report only, no building

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 67 · **Source:** BACKLOG-RESERVE · **Area:** reserve-TCH · **Est.:** 150k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-TCH-010`
- **Work packages:** `WP-TCH-02` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/tch/`, `tests/tch/`
- **Acceptance criteria:**
  1. WP-TCH-02 host compiler detection (GCC/Clang) — detection and version report only, no building — detection and version report only — no building
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-107 — Mutation-style test strengthening for `ectt.core` and `ectt.prj` (hand-written mutants, kill-rate report)

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 69 · **Source:** BACKLOG-RESERVE · **Area:** reserve-tests · **Est.:** 150k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `tests/core/`, `tests/prj/`
- **Acceptance criteria:**
  1. Mutation-style test strengthening for `ectt.core` and `ectt.prj` (hand-written mutants, kill-rate report) — tests only; hand-written mutants, kill-rate report
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

### TASK-108 — Property-based fuzz-style tests for the YAML adapter and schema reader using seeded `random`

- **Status:** Planned · **Lane:** Reserve queue · **Seq:** 70 · **Source:** BACKLOG-RESERVE · **Area:** reserve-tests · **Est.:** 150k tokens
- **Dependencies:** `TASK-024`
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** — · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `tests/core/`, `tests/prj/`, `tests/ana/ (schema reader)`
- **Acceptance criteria:**
  1. Property-based fuzz-style tests for the YAML adapter and schema reader using seeded `random` — deterministic seeds only
  2. same rules as the core queue; only after TASK-024 is committed
  3. full gate green
- **Verification** (pending):
  - full gate **G-FULL** (see §5.4)

## 7.3 Blocked backlog task

### TASK-007 — WP-CORE-03 platform baseline and offline guarantee

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 77 · **Source:** BACKLOG · **Area:** impl · **Est.:** 120k tokens
- **Dependencies:** `TASK-006`
- **Blocking decision / gate:** `D-03`
- **SRS requirements:** `TOOL-NFR-010`, `TOOL-NFR-020`, `TOOL-NFR-100`
- **Work packages:** `WP-CORE-03` · **Related:** `T-05`, `D-03`
- **ADRs:** — · **PRs:** —
- **Branch:** `glm-night/20261117 (worktree ../wt-unit-glm-night, off docs/pending-decisions tip)`
- **Files likely touched:** `src/ectt/core/platform.py (new)`, `tests/core/test_platform.py`, `tests/core/test_offline_guard.py`
- **Acceptance criteria:**
  1. platform report test passes on this machine
  2. offline-guard test passes (no import/run-time network use across tests/core/fixture_pipeline.py)
  3. log notes Linux behaviour untested
  4. NOT STARTABLE until the owner answers D-03 or explicitly approves the order-neutral encoding (see notes)
- **Verification** (pending):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/test_platform.py tests/core/test_offline_guard.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** The backlog queues this while listing D-03 as an owner decision. Encoding Windows and Linux as co-equal is itself answer (c) 'both in parallel', and the decision queue lists WP-CORE-03 as gated by D-03. Conservative reading applied: Blocked until the owner answers D-03 or explicitly approves the order-neutral encoding. TASK-016 must skip CORE-03 while this is blocked.

## 7.4 vcast-findings tasks not yet landed (T-01, T-02, T-04, T-05, T-06, T-14)

### T-01 — Convene ADR-005 licence decision; update LICENSE/LIC-010; re-run gates

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 71 · **Source:** vcast-findings · **Area:** REVIEW · **Priority:** P0
- **Dependencies:** —
- **Blocking decision / gate:** `D-01`
- **SRS requirements:** `TOOL-LIC-010`
- **Work packages:** `WP-PKG-07` · **Related:** `NR-01`, `RV-06 F-27`
- **ADRs:** `ADR-005` · **PRs:** —
- **Branch:** `n/a — decision first`
- **Files likely touched:** `LICENSE`, `SRS-001-requirements.md (LIC-010)`, `ADR-001-architecture-decisions.md (ADR-005 record)`, `design/trace/design-elements.yaml`
- **Acceptance criteria:**
  1. ADR-005 recorded with the owner's chosen option
  2. LICENSE and LIC-010 are consistent with each other
  3. plan_check and trace_check green after the change
- **Verification** (pending):
  - design gates **G-GATES** (plan_check + trace_check)
- **Notes:** Source status in tracker: Awaiting decision

### T-02 — Write the no-import/provenance rule for vcast-findings assets

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 72 · **Source:** vcast-findings · **Area:** REVIEW · **Priority:** P0
- **Dependencies:** —
- **Blocking decision / gate:** `D-01`
- **SRS requirements:** —
- **Work packages:** — · **Related:** `NR-02`, `RV-06 F-27`
- **ADRs:** `ADR-005` · **PRs:** —
- **Branch:** `n/a — decision first`
- **Files likely touched:** `docs/ (provenance rule) or SRS-001 addendum`, `ADR-005 consequence text`
- **Acceptance criteria:**
  1. No-import/provenance rule written and anchored to ADR-005
  2. TASK-015 draft + prototype test reviewed by the owner (not adopted before D-01)
- **Verification** (pending):
  - design gates **G-GATES** (plan_check + trace_check)
- **Notes:** Source status is 'Not Started'. Blocked: its consequence anchor is ADR-005 (D-01). TASK-015 prepares a draft only.

### T-04 — Decide and record the identity model (SDD-003 §6/§7) — memo prepared, decision pending

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 73 · **Source:** vcast-findings · **Area:** REVIEW · **Priority:** P0
- **Dependencies:** —
- **Blocking decision / gate:** `D-02`
- **SRS requirements:** —
- **Work packages:** — · **Related:** `NR-04`, `RV-05 F-05`
- **ADRs:** — · **PRs:** —
- **Branch:** `n/a — decision first`
- **Files likely touched:** `design/SDD-003-data-model.md §6/§7`, `design/SDD-002-interfaces.md (S2/S3 sentence)`
- **Acceptance criteria:**
  1. SDD-003 §6/§7 amended with the chosen identity model
  2. one sentence added to SDD-002 S2/S3
  3. gates green; T-14 unblocked
- **Verification** (pending):
  - design gates **G-GATES** (plan_check + trace_check)
- **Notes:** Source status in tracker: Awaiting decision

### T-14 — Run-integrity acceptance into WP-EXH-01/02 + WP-CBT-01

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 74 · **Source:** vcast-findings · **Area:** REVIEW · **Priority:** P1
- **Dependencies:** `T-04`
- **Blocking decision / gate:** `D-02`
- **SRS requirements:** —
- **Work packages:** — · **Related:** `NR-17..19`, `RV-06 F-11/12/19`
- **ADRs:** — · **PRs:** —
- **Branch:** `n/a — decision first`
- **Files likely touched:** `PLAN-001 §5.4 (WP-EXH-01/02, WP-CBT-01 exit criteria)`, `SRS-001-requirements.md (NR-17..19 wording)`, `design/trace/design-elements.yaml`
- **Acceptance criteria:**
  1. Run-integrity acceptance written into WP-EXH-01/02 and WP-CBT-01 exit criteria
  2. NR-17..19 wording agreed
  3. gates green
- **Verification** (pending):
  - design gates **G-GATES** (plan_check + trace_check)
- **Notes:** Source status is 'Not Started', blocked by T-04 (itself awaiting D-02 identity model).

### T-05 — Decide and record platform order

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 75 · **Source:** vcast-findings · **Area:** REVIEW · **Priority:** P1
- **Dependencies:** —
- **Blocking decision / gate:** `D-03`
- **SRS requirements:** `TOOL-NFR-010`, `TOOL-NFR-020`
- **Work packages:** `WP-CORE-03` · **Related:** `NR-05`, `RV-05 F-06`
- **ADRs:** — · **PRs:** —
- **Branch:** `n/a — decision first`
- **Files likely touched:** `SRS-001-requirements.md (NFR-010/020 wording note)`
- **Acceptance criteria:**
  1. Platform order recorded
  2. NFR-010/020 wording note landed
  3. gates green
- **Verification** (pending):
  - design gates **G-GATES** (plan_check + trace_check)
- **Notes:** Source status in tracker: Awaiting decision

### T-06 — DR-06 NFR calibration plan + fixtures; provisional NFRs marked

- **Status:** Blocked · **Lane:** Blocked · **Seq:** 76 · **Source:** vcast-findings · **Area:** REVIEW · **Priority:** P2
- **Dependencies:** —
- **Blocking decision / gate:** `D-04`
- **SRS requirements:** `TOOL-NFR-030`, `TOOL-NFR-040`, `TOOL-NFR-050`, `TOOL-NFR-150`
- **Work packages:** `WP-CORE-05` · **Related:** `NR-06`, `RV-06 F-07/F-24`
- **ADRs:** — · **PRs:** —
- **Branch:** `n/a — decision first`
- **Files likely touched:** `SRS-001-requirements.md (DR-06 / NFR-030..150 provisional marks)`, `PLAN-001 §6.4 calibration fixtures`
- **Acceptance criteria:**
  1. NR-06 disposition recorded on T-06 per the chosen option (defer / calibrate now / drop)
  2. provisional NFRs marked consistently
- **Verification** (pending):
  - design gates **G-GATES** (plan_check + trace_check)
- **Notes:** Source status in tracker: Awaiting decision

## 7.5 Implemented work packages (PLAN-001)

### WP-SPIKE-01 — CFG sufficiency spike: python-clang against real embedded code

- **Status:** Implemented · **Lane:** Done · **Seq:** 1 · **Source:** PLAN-001 · **Area:** SPIKE · **Est.:** 1w · **Phase:** P0
- **Dependencies:** —
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** `WP-SPIKE-01` · **Related:** —
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `6af7d84`
- **Files likely touched:** `spikes/spike-01-cfg-sufficiency/RESULTS.md`, `spikes/spike-01-cfg-sufficiency/tests/test_extract.py`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (; techniques: n/a) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider spikes/spike-01-cfg-sufficiency/tests/test_extract.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** recorded complete in ADR-001

### WP-SPIKE-02 — Nested type-aware test data editor spike in PySide6

- **Status:** Implemented · **Lane:** Done · **Seq:** 2 · **Source:** PLAN-001 · **Area:** SPIKE · **Est.:** 2w · **Phase:** P0
- **Dependencies:** —
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** `WP-SPIKE-02` · **Related:** —
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `6af7d84`
- **Files likely touched:** `spikes/spike-02-nested-editor/RESULTS.md`, `spikes/spike-02-nested-editor/tests/test_model.py`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (; techniques: n/a) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider spikes/spike-02-nested-editor/tests/test_model.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** recorded complete in ADR-001

### WP-SPIKE-03 — PyInstaller distribution spike onto clean Windows

- **Status:** Implemented · **Lane:** Done · **Seq:** 3 · **Source:** PLAN-001 · **Area:** SPIKE · **Est.:** 1w · **Phase:** P0
- **Dependencies:** —
- **Blocking decision / gate:** —
- **SRS requirements:** —
- **Work packages:** `WP-SPIKE-03` · **Related:** —
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `6af7d84`
- **Files likely touched:** `spikes/spike-03-packaging/RESULTS.md`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (; techniques: n/a) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - full gate **G-FULL** (see §5.4)
- **Notes:** recorded complete in ADR-001

### WP-CORE-01 — Determinism, source immutability and output confinement

- **Status:** Implemented · **Lane:** Done · **Seq:** 4 · **Source:** PLAN-001 · **Area:** CORE · **Est.:** 3w · **Phase:** P1
- **Dependencies:** —
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-NFR-060`, `TOOL-NFR-070`, `TOOL-NFR-080`, `TOOL-PRJ-050`, `TOOL-PRJ-080`
- **Work packages:** `WP-CORE-01` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `51bde0b`
- **Files likely touched:** `src/ectt/core/`, `tests/core/test_determinism.py`, `tests/core/test_fs.py`, `tests/core/test_pipeline_reproducibility.py`
- **Acceptance criteria:**
  1. PLAN-001 §5.4 exit criterion: Two runs from identical inputs on different machines produce byte-identical generated artifacts; a write attempted outside the configured output root fails and is reported; no user source file's mtime or content changes across a full run
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/test_determinism.py tests/core/test_fs.py tests/core/test_pipeline_reproducibility.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** 45 tests green

### WP-PRJ-01 — Plain-text schema-versioned project store

- **Status:** Implemented · **Lane:** Done · **Seq:** 5 · **Source:** PLAN-001 · **Area:** PRJ · **Est.:** 4w · **Phase:** P1
- **Dependencies:** `WP-CORE-01`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PRJ-010`, `TOOL-PRJ-020`, `TOOL-PRJ-070`, `TOOL-UIX-320`, `TOOL-CIC-080`
- **Work packages:** `WP-PRJ-01` · **Related:** —
- **ADRs:** `ADR-001`, `ADR-002` · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `d9557dd`
- **Files likely touched:** `src/ectt/prj/`, `tests/prj/test_paths.py`, `tests/prj/test_project.py`, `tests/prj/test_schema_dispatch.py`, `tests/prj/test_yaml_adapter.py`, `docs/verification/WP-PRJ-01-inspection.md`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (I×5; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/test_paths.py tests/prj/test_project.py tests/prj/test_schema_dispatch.py tests/prj/test_yaml_adapter.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** 35 tests green + inspection record

### WP-ING-01 — Compilation database ingestion

- **Status:** Implemented · **Lane:** Done · **Seq:** 6 · **Source:** PLAN-001 · **Area:** ING · **Est.:** 3w · **Phase:** P1
- **Dependencies:** `WP-PRJ-01`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-ING-010`, `TOOL-ING-020`, `TOOL-ING-030`, `TOOL-ING-040`
- **Work packages:** `WP-ING-01` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `c80ef9f`
- **Files likely touched:** `src/ectt/ing/`, `tests/ing/test_cmake.py`, `tests/ing/test_compdb_adapter.py`, `tests/ing/test_model.py`, `docs/verification/WP-ING-01-inspection.md`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (D×1, T×3; techniques: EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/test_cmake.py tests/ing/test_compdb_adapter.py tests/ing/test_model.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** 50 tests green + inspection record

### WP-ANA-01 — C front-end binding and dialect support

- **Status:** Implemented · **Lane:** Done · **Seq:** 7 · **Source:** PLAN-001 · **Area:** ANA · **Est.:** 4w · **Phase:** P1
- **Dependencies:** `WP-ING-01`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-010`, `TOOL-PAR-020`
- **Work packages:** `WP-ANA-01` · **Related:** —
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `ae10ce2`
- **Files likely touched:** `src/ectt/ana/`, `tests/ana/test_frontend.py`, `tests/ana/test_dialects.py`, `tests/ana/test_errors.py`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, PAIRWISE) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/test_frontend.py tests/ana/test_dialects.py tests/ana/test_errors.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** 26 tests green (libclang required)

### WP-ANA-02 — Interface and type extraction

- **Status:** Implemented · **Lane:** Done · **Seq:** 8 · **Source:** PLAN-001 · **Area:** ANA · **Est.:** 5w · **Phase:** P1
- **Dependencies:** `WP-ANA-01`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-030`, `TOOL-PAR-040`, `TOOL-PAR-050`
- **Work packages:** `WP-ANA-02` · **Related:** —
- **ADRs:** `ADR-001` · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `ae10ce2`
- **Files likely touched:** `src/ectt/ana/`, `tests/ana/test_interface.py`, `tests/ana/test_types.py`
- **Acceptance criteria:**
  1. Every owned requirement is verified by its Appendix A method (T×3; techniques: EQUIVALENCE PARTITIONING, PAIRWISE) and the exit evidence is recorded; full gate green.
- **Verification** (pass):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/test_interface.py tests/ana/test_types.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** 16 tests green (libclang required)

### WP-ANA-04 — Analysis model persistence and schema versioning

- **Status:** Implemented · **Lane:** Done · **Seq:** 9 · **Source:** PLAN-001 · **Area:** ANA · **Est.:** 3w · **Phase:** P1
- **Dependencies:** `WP-ANA-02`
- **Blocking decision / gate:** —
- **SRS requirements:** `TOOL-PAR-100`, `TOOL-PAR-110`
- **Work packages:** `WP-ANA-04` · **Related:** —
- **ADRs:** — · **PRs:** —
- **Branch:** `main (landed)` · **Commit:** `b5786e0`
- **Files likely touched:** `src/ectt/ana/`, `tests/ana/test_persist.py`, `tests/ana/test_schema_conformance.py`, `tests/ana/test_model.py`, `docs/verification/WP-ANA-04-analysis.md`
- **Acceptance criteria:**
  1. PLAN-001 §5.4 exit criterion: A model emitted by the analyzer validates against its published schema, carries a schema version, and is rejected with a named reason by a consumer pinned to an incompatible version
- **Verification** (failing):
  - `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/test_persist.py tests/ana/test_schema_conformance.py tests/ana/test_model.py`
  - full gate **G-FULL** (see §5.4)
- **Notes:** 3 of 30 tests in test_persist.py fail at HEAD (stale '1.0' assertions after T-09/T-10); fixed by TASK-001

## 7.6 Landed vcast-findings tasks (compact)

| ID | Title | Commit | Branch | SRS requirements | WPs |
|---|---|---|---|---|---|
| `T-03` | SRS change: TOOL-EXE-040 timeout distinct from fail + gate repair (PLG-080/100, COV-150, AIF allocations) | `3e60d10` | main (via PR#7) | `TOOL-AIF-260`, `TOOL-COV-150`, `TOOL-EXE-040`, `TOOL-PLG-080`, `TOOL-PLG-100` | `WP-AIF-15`, `WP-COV-09`, `WP-EXH-02`, `WP-PLG-02`, `WP-PLG-04` |
| `T-12` | LinkPlan: TOOL-ING-200 + WP-ING-07 + DSN-ING-120 + SDD-002/SDD-003 amendments | `3e60d10` | main (via PR#7) | `TOOL-ING-200` | `WP-ING-07` |
| `T-07` | Extend ing: response-file expansion, build-context identity, build tags (TOOL-ING-210/220, DSN-ING-130/140) | `6a299d4` | main (via PR#7) | `TOOL-ING-210`, `TOOL-ING-220` | `WP-ING-02`, `WP-ING-03` |
| `T-08` | ING-100 fail-closed staleness: content fingerprints (compdb, sources, response files, include surface) + invalidation fixtures | `6f7b740` | main (via PR#7) | `TOOL-ING-100` | `WP-ING-03` |
| `T-09` | S1 schema 1.1: mandatory decision + unsupported inventories, reader gates fail closed | `83bf22a` | main (via PR#7) | `TOOL-PAR-140`, `TOOL-PAR-150` | `WP-ANA-07`, `WP-ANA-08` |
| `T-10` | Value ranges + array dimension metadata in ana model and schema 1.2 (round-trip + conformance tests) | `b7adfad` | main (via PR#7) | `TOOL-PAR-160` | `WP-ANA-09` |
| `T-11` | Eligibility/observability gate: assess_eligibility over the S1 model (channels, named reasons), consumed by CMP-ATG | `96c4b23` | main (via PR#7) | `TOOL-PAR-170` | `WP-ANA-06` |
| `T-13` | Compound-test defer decision + migration flag | `1ad783b` | main (via PR#7) | `TOOL-MIG-110` | `WP-MIG-05` |
| `T-16` | Coverage completeness state: TOOL-COV-180 + SDD-002 §6.1/§7.2/§8 amendments + DSN-COV-110 | `ca77dbd` | main (via PR#7) | `TOOL-COV-180` | `WP-COV-02` |
| `T-17` | MC/DC limit probing + boundary fixtures + macro-variant merge rule | `c6339e3` | docs/pending-decisions (unpushed) | `TOOL-COV-190`, `TOOL-COV-200` | `WP-COV-02`, `WP-COV-05`, `WP-COV-06` |
| `T-18` | Known-answer MC/DC corpus mandate | `966b21e` | docs/pending-decisions (unpushed) | `TOOL-COV-090`, `TOOL-COV-210` | `WP-COV-05`, `WP-COV-10` |
| `T-19` | Verdict dedup + labeled denominators + 2/1 anomaly fixture | `afa4339` | docs/pending-decisions (unpushed) | `TOOL-ATG-080`, `TOOL-TRC-110` | `WP-ATG-01`, `WP-TRC-01` |
| `T-20` | Crashed-run coverage admission rule | `93171a2` | docs/pending-decisions (unpushed) | `TOOL-COV-220` | `WP-COV-02` |
| `T-21` | Harness-vs-reference agreement check in WP-QUA-03 | `0ae84c1` | docs/pending-decisions (unpushed) | `TOOL-QUA-110` | `WP-GEN-01`, `WP-QUA-03` |
| `T-22` | Clean-machine endpoint gate in WP-PKG (ADR-007) | `f167005` | docs/pending-decisions (unpushed) | `TOOL-INS-120` | `WP-PKG-01`, `WP-PKG-07` |
| `T-15` | HostProfile/ABI-divergence record section | `a412112` | docs/pending-decisions (unpushed) | `TOOL-TGT-070`, `TOOL-TGT-130` | `WP-EXT-04` |
<!-- END GENERATED: cards -->

---

# 8. Work-package register (PLAN-001, not yet Implemented)

Every PLAN-001 work package that is not Implemented, in execution order, with all task fields in compact form. `Accept:` is the PLAN-001 §5.4 exit criterion where one is written, otherwise "every owned requirement is verified by its Appendix A method". Packages scheduled into the overnight queue point at their delivering `TASK-`.

<!-- BEGIN GENERATED: register -->
#### WP-CORE-02 — Structured error model, fail-safe termination and cancellation

- Planned · P1 · 3w · seq 33 · Scheduled via TASK · hard deps met: yes
- deps `WP-CORE-01` · no decision block · delivered by `TASK-006` · ADR — · PR —
- Reqs: `TOOL-NFR-090`, `TOOL-NFR-180`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL

#### WP-ANA-03 — Call graph and scope classification

- Planned · P2 · 3w · seq 35 · Scheduled via TASK · hard deps met: yes
- deps `WP-ANA-02` · no decision block · delivered by `TASK-008` · ADR `ADR-001` · PR —
- Reqs: `TOOL-PAR-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ana/`, `tests/ana/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`; G-FULL

#### WP-ANA-07 — Partial-failure resilience

- Planned · P2 · 2w · seq 37 · Scheduled via TASK · hard deps met: no
- deps `WP-ANA-01`, `WP-CORE-02` · no decision block · delivered by `TASK-009` · ADR — · PR —
- Reqs: `TOOL-PAR-130`, `TOOL-PAR-140`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green. Partial progress: PAR-140 (unsupported-construct inventory) landed via T-09; PAR-130 (partial-failure resilience) remains.
- Files: `src/ectt/ana/`, `tests/ana/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`; G-FULL
- Notes: PAR-140 (unsupported-construct inventory) landed via T-09; PAR-130 (partial-failure resilience) remains.

#### WP-ING-07 — Authored link plan ingestion and validation

- Planned · P2 · 2w · seq 39 · Scheduled via TASK · hard deps met: yes
- deps `WP-ING-01` · no decision block · delivered by `TASK-010` · ADR — · PR —
- Reqs: `TOOL-ING-200`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green. Partial progress: Spec, DSN-ING-120 and SDD amendments landed via T-12; the code (src/ectt/ing/linkplan.py) is TASK-010.
- Files: `src/ectt/ing/`, `tests/ing/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/`; G-FULL
- Notes: Spec, DSN-ING-120 and SDD amendments landed via T-12; the code (src/ectt/ing/linkplan.py) is TASK-010.

#### WP-PRJ-04 — Dangling reference detection

- Planned · P3 · 1w · seq 41 · Scheduled via TASK · hard deps met: yes
- deps `WP-PRJ-01` · no decision block · delivered by `TASK-011` · ADR `ADR-002` · PR —
- Reqs: `TOOL-PRJ-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/prj/`, `tests/prj/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/`; G-FULL

#### WP-PRJ-03 — Schema migration with explicit confirmation

- Planned · P2 · 3w · seq 43 · Scheduled via TASK · hard deps met: yes
- deps `WP-PRJ-01` · no decision block · delivered by `TASK-012` · ADR `ADR-002` · PR —
- Reqs: `TOOL-PRJ-040`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/prj/`, `tests/prj/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/`; G-FULL

#### WP-CORE-04 — Provenance record and version identification

- Planned · P2 · 2w · seq 45 · Scheduled via TASK · hard deps met: yes
- deps `WP-CORE-01` · no decision block · delivered by `TASK-013` · ADR — · PR —
- Reqs: `TOOL-QUA-060`, `TOOL-INS-110`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL

#### WP-ING-02 — Alternative ingestion paths

- Planned · P2 · 3w · seq 58 · Scheduled via TASK · hard deps met: yes
- deps `WP-ING-01` · no decision block · delivered by `TASK-101` · ADR — · PR —
- Reqs: `TOOL-ING-050`, `TOOL-ING-060`, `TOOL-ING-080`, `TOOL-ING-210`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×3; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green. Partial progress: ING-210 (response-file expansion) landed via T-07; ING-050/060/080 remain.
- Files: `src/ectt/ing/`, `tests/ing/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/`; G-FULL
- Notes: ING-210 (response-file expansion) landed via T-07; ING-050/060/080 remain.

#### WP-ING-03 — Ingestion diagnostics, persistence and staleness

- Planned · P2 · 3w · seq 60 · Scheduled via TASK · hard deps met: yes
- deps `WP-ING-01` · no decision block · delivered by `TASK-102` · ADR — · PR —
- Reqs: `TOOL-ING-070`, `TOOL-ING-090`, `TOOL-ING-100`, `TOOL-ING-220`
- Accept: Every owned requirement is verified by its Appendix A method (T×4; techniques: EQUIVALENCE PARTITIONING, STATE TRANSITION) and the exit evidence is recorded; full gate green. Partial progress: ING-220 (build tag) landed via T-07 and ING-100 fail-closed staleness via T-08 (src/ectt/ing/staleness.py); diagnostics/persistence remain.
- Files: `src/ectt/ing/`, `tests/ing/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/`; G-FULL
- Notes: ING-220 (build tag) landed via T-07 and ING-100 fail-closed staleness via T-08 (src/ectt/ing/staleness.py); diagnostics/persistence remain.

#### WP-ANA-06 — Static function testability and macro resolution

- Planned · P2 · 4w · seq 62 · Scheduled via TASK · hard deps met: yes
- deps `WP-ANA-02` · no decision block · delivered by `TASK-103` · ADR `ADR-001` · PR —
- Reqs: `TOOL-PAR-080`, `TOOL-PAR-090`, `TOOL-PAR-170`
- Accept: Every owned requirement is verified by its Appendix A method (T×3; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green. Partial progress: PAR-170 (eligibility/observability gate) already landed via T-11 (src/ectt/ana/eligibility.py); PAR-080/090 (static testability, macro resolution) remain.
- Files: `src/ectt/ana/`, `tests/ana/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`; G-FULL
- Notes: PAR-170 (eligibility/observability gate) already landed via T-11 (src/ectt/ana/eligibility.py); PAR-080/090 (static testability, macro resolution) remain.

#### WP-PRJ-02 — Diff-stable sharded storage for concurrent edit

- Planned · P2 · 3w · seq 64 · Scheduled via TASK · hard deps met: yes
- deps `WP-PRJ-01` · no decision block · delivered by `TASK-104` · ADR `ADR-002` · PR —
- Reqs: `TOOL-PRJ-030`, `TOOL-PRJ-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/prj/`, `tests/prj/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/`; G-FULL

#### WP-CORE-06 — Logging and diagnostic bundle

- Planned · P2 · 2w · seq 66 · Scheduled via TASK · hard deps met: no
- deps `WP-CORE-02`, `WP-SEC-04` · no decision block · delivered by `TASK-105` · ADR — · PR —
- Reqs: `TOOL-NFR-130`, `TOOL-NFR-160`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL

#### WP-TCH-02 — Host compiler support: GCC and Clang

- Planned · P1 · 2w · seq 68 · Scheduled via TASK · hard deps met: no
- deps `WP-TCH-01` · no decision block · delivered by `TASK-106` · ADR — · PR —
- Reqs: `TOOL-TCH-010`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-CORE-03 — Platform baseline and offline guarantee

- Blocked · P1 · 2w · seq 78 · Blocked · hard deps met: yes
- deps — · blocked by `D-03` · delivered by `TASK-007` · ADR `ADR-001` · PR —
- Reqs: `TOOL-NFR-010`, `TOOL-NFR-020`, `TOOL-NFR-100`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-03-analysis.md` · Branch: `glm-night/20261117`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL
- Notes: the platform baseline is the platform order (D-03: Windows-first / Linux-first / parallel); NFR-010/020 wording is pending.

#### WP-PKG-07 — License policy, process isolation and automated enforcement

- Blocked · P1 · 3w · seq 79 · Blocked · hard deps met: yes
- deps — · blocked by `D-01` · ADR `ADR-005`, `ADR-001` · PR —
- Reqs: `TOOL-LIC-010`, `TOOL-LIC-020`, `TOOL-LIC-030`, `TOOL-LIC-040`, `TOOL-LIC-050`, `TOOL-LIC-060`
- Accept: Every owned requirement is verified by its Appendix A method (I×6; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/`, `docs/verification/WP-PKG-07-analysis.md` · Branch: `feat/wp-pkg-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL
- Notes: LIC-010..060 licence policy cannot be implemented until the licence posture (D-01 / ADR-005) is decided.

#### WP-COV-01 — Statement and branch coverage from compiler backend

- Blocked · P1 · 4w · seq 80 · Blocked · hard deps met: no
- deps `WP-EXH-01`, `WP-TCH-02` · blocked by `ADR-004` · ADR `ADR-004`, `ADR-001` · PR —
- Reqs: `TOOL-COV-010`, `TOOL-COV-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL
- Notes: coverage backend strategy is open (ADR-004); integration waits on it — critical-path package.

#### WP-PKG-01 — Offline, non-admin, runtime-free installation

- Blocked · P2 · 6w · seq 81 · Blocked · hard deps met: no
- deps `WP-SPIKE-03`, `WP-CORE-03` · blocked by `ADR-007` · ADR `ADR-007`, `ADR-001` · PR —
- Reqs: `TOOL-INS-010`, `TOOL-INS-020`, `TOOL-INS-030`, `TOOL-INS-120`
- Accept: PLAN-001 §5.4 exit criterion: The release package installs and runs on a clean machine with no development toolchain under default endpoint-security policy, without administrative privileges and without network access; the endpoint-security interactions are recorded per release
- Files: `src/ectt/pkg/`, `tests/pkg/` · Branch: `feat/wp-pkg-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL
- Notes: distribution/installer choice is open (ADR-007); integration waits on it.

#### WP-EXH-04 — Debugger launch with entry breakpoint

- Blocked · P2 · 4w · seq 82 · Blocked · hard deps met: no
- deps `WP-EXH-01` · blocked by `SRS-Q9` · ADR `SRS-Q9`, `ADR-001` · PR —
- Reqs: `TOOL-EXE-070`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/exh/`, `tests/exh/` · Branch: `feat/wp-exh-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/exh/`; G-FULL
- Notes: debugger front-end is an open SRS question (§27 q9); P2 integration waits on it.

#### WP-PKG-08 — Separable restrictively-licensed optional components

- Blocked · P3 · 2w · seq 83 · Blocked · hard deps met: no
- deps `WP-PKG-07` · blocked by `D-01` · ADR `ADR-005`, `ADR-001` · PR —
- Reqs: `TOOL-LIC-070`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/`, `docs/verification/WP-PKG-08-analysis.md` · Branch: `feat/wp-pkg-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL
- Notes: separable restrictively-licensed components follow WP-PKG-07 and the licence decision.

#### WP-ATG-02 — Symbolic execution engine adapter

- Blocked · P3 · 8w · seq 84 · Blocked · hard deps met: no
- deps `WP-ATG-01`, `WP-ANA-05` · blocked by `ADR-003` · ADR `ADR-003`, `ADR-001` · PR —
- Reqs: `TOOL-ATG-010`, `TOOL-ATG-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/atg/`, `tests/atg/` · Branch: `feat/wp-atg-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/atg/`; G-FULL
- Notes: symbolic-execution engine choice is open (ADR-003); P3 integration waits on it.

#### WP-ATG-03 — Bounded model checking engine

- Blocked · P3 · 5w · seq 85 · Blocked · hard deps met: no
- deps `WP-ATG-01` · blocked by `ADR-003` · ADR `ADR-003`, `ADR-001` · PR —
- Reqs: `TOOL-ATG-030`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/atg/`, `tests/atg/` · Branch: `feat/wp-atg-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/atg/`; G-FULL
- Notes: bounded-model-checking engine choice is open (ADR-003).

#### WP-COV-05 — MC/DC measurement and form declaration

- Blocked · P3 · 6w · seq 86 · Blocked · hard deps met: no
- deps `WP-COV-01`, `WP-TCH-04` · blocked by `SRS-Q2` · ADR `SRS-Q2`, `ADR-001` · PR —
- Reqs: `TOOL-COV-050`, `TOOL-COV-060`, `TOOL-COV-070`, `TOOL-COV-210`
- Accept: PLAN-001 §5.4 exit criterion: For a decision with N conditions, the report names which conditions were unexercised true and unexercised false, and every report states the MC/DC form obtained and the compiler mechanism that produced it; the fixture set includes a decision at exactly the probed backend condition maximum and one at maximum+1, and the exceeded decision reads unmeasured with the recorded limit in its reason; the known-answer MC/DC corpus (COV-210) passes with hand-computed statuses and witness pairs
- Files: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-05-analysis.md` · Branch: `feat/wp-cov-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL
- Notes: MC/DC form is an open SRS question (§27 q2); P3 acceptance waits on it.

#### WP-API-01 — Engine API protocol, operation catalogue and versioning

- Planned · P1 · 4w · seq 87 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-UIX-010`, `TOOL-UIX-020`, `TOOL-PLG-060`
- Accept: Every owned requirement is verified by its Appendix A method (A×2, I×1; techniques: ANALYSIS ARGUMENT, INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/api/`, `tests/api/`, `docs/verification/WP-API-01-analysis.md` · Branch: `feat/wp-api-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/api/`; G-FULL

#### WP-PLG-01 — Extension point definition and versioning

- Planned · P1 · 3w · seq 88 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-PLG-010`
- Accept: Every owned requirement is verified by its Appendix A method (A×1; techniques: ANALYSIS ARGUMENT) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-01-analysis.md` · Branch: `feat/wp-plg-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/plg/`; G-FULL

#### WP-TCH-01 — Declarative compiler configuration format

- Planned · P1 · 3w · seq 89 · Backlog (planned WP) · hard deps met: no
- deps `WP-PLG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCH-020`, `TOOL-PLG-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/` · Branch: `feat/wp-tch-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-CLI-01 — Non-interactive CLI generated from the operation catalogue

- Planned · P1 · 3w · seq 90 · Backlog (planned WP) · hard deps met: no
- deps `WP-API-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-CIC-010`, `TOOL-CIC-020`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cli/`, `tests/cli/` · Branch: `feat/wp-cli-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cli/`; G-FULL

#### WP-CLI-02 — Stable documented exit codes

- Planned · P1 · 1w · seq 91 · Backlog (planned WP) · hard deps met: no
- deps `WP-CLI-01`, `WP-CORE-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-CIC-030`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cli/`, `tests/cli/` · Branch: `feat/wp-cli-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cli/`; G-FULL

#### WP-CLI-03 — Container execution

- Planned · P1 · 2w · seq 92 · Backlog (planned WP) · hard deps met: no
- deps `WP-CLI-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-CIC-040`
- Accept: Every owned requirement is verified by its Appendix A method (D×1; techniques: SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cli/`, `tests/cli/` · Branch: `feat/wp-cli-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cli/`; G-FULL

#### WP-GEN-01 — Harness generation core

- Planned · P1 · 5w · seq 93 · Backlog (planned WP) · hard deps met: yes
- deps `WP-ANA-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-HAR-010`, `TOOL-HAR-020`, `TOOL-HAR-040`, `TOOL-HAR-050`
- Accept: Every owned requirement is verified by its Appendix A method (T×4; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-BLD-01 — Host build orchestration and incremental rebuild

- Planned · P1 · 4w · seq 94 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCH-02`, `WP-GEN-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-EXE-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/bld/`, `tests/bld/` · Branch: `feat/wp-bld-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/bld/`; G-FULL

#### WP-TCM-01 — Test cases authored in C

- Planned · P1 · 2w · seq 95 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCD-010`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/` · Branch: `feat/wp-tcm-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-EXH-01 — Host execution and per-test result reporting

- Planned · P1 · 4w · seq 96 · Backlog (planned WP) · hard deps met: no
- deps `WP-BLD-01`, `WP-TCM-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-EXE-010`, `TOOL-EXE-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/exh/`, `tests/exh/` · Branch: `feat/wp-exh-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/exh/`; G-FULL

#### WP-EXH-02 — Crash isolation, timeout and process exit status

- Planned · P1 · 3w · seq 97 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXH-01`, `WP-CORE-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-EXE-030`, `TOOL-EXE-040`, `TOOL-EXE-060`
- Accept: PLAN-001 §5.4 exit criterion: A test case that segfaults, one that hangs past the timeout, and one that calls `abort()` are each reported as a failure with the remaining cases still executed
- Files: `src/ectt/exh/`, `tests/exh/` · Branch: `feat/wp-exh-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/exh/`; G-FULL

#### WP-REP-01 — Single intermediate report model

- Planned · P1 · 4w · seq 98 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-01`, `WP-EXH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-090`, `TOOL-REP-100`
- Accept: PLAN-001 §5.4 exit criterion: Two different renderers over one persisted report model cannot disagree on any test's status or any coverage figure; re-running the renderer produces byte-identical output excluding timestamps
- Files: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-01-analysis.md` · Branch: `feat/wp-rep-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-EXH-03 — Parallel test execution

- Planned · P1 · 2w · seq 99 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXH-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-EXE-050`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/exh/`, `tests/exh/` · Branch: `feat/wp-exh-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/exh/`; G-FULL

#### WP-COV-02 — Coverage merge and per-test attribution

- Planned · P1 · 4w · seq 100 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-110`, `TOOL-COV-120`, `TOOL-COV-180`, `TOOL-COV-200`, `TOOL-COV-220`
- Accept: PLAN-001 §5.4 exit criterion: A profile flushed by a run that then crashes is retained but excluded from the aggregate until explicitly admitted per run; the aggregate figure never includes quarantined data, and per-run provenance still shows it
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-REP-03 — HTML report with annotated source

- Planned · P1 · 4w · seq 101 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-COV-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-030`, `TOOL-REP-040`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-COV-03 — Coverage threshold enforcement

- Planned · P1 · 1w · seq 102 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-130`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-REP-02 — Machine-readable outputs: JUnit and Cobertura/LCOV

- Planned · P1 · 3w · seq 103 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-COV-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-010`, `TOOL-REP-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-CORE-07 — User documentation and text externalisation

- Planned · P2 · 4w · seq 104 · Backlog (planned WP) · hard deps met: yes
- deps — · no decision block · ADR — · PR —
- Reqs: `TOOL-NFR-120`, `TOOL-NFR-190`
- Accept: Every owned requirement is verified by its Appendix A method (I×2; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-07-analysis.md` · Branch: `feat/wp-core-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL

#### WP-SEC-05 — Security disclosure process and supported-version policy

- Planned · P2 · 1w · seq 105 · Backlog (planned WP) · hard deps met: yes
- deps — · no decision block · ADR — · PR —
- Reqs: `TOOL-SEC-080`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-05-analysis.md` · Branch: `feat/wp-sec-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-SEC-04 — Log and diagnostic content control

- Planned · P2 · 2w · seq 106 · Backlog (planned WP) · hard deps met: yes
- deps `WP-CORE-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-SEC-120`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/` · Branch: `feat/wp-sec-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-QUA-02 — Tool operational requirements specification

- Planned · P2 · 4w · seq 107 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-04` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-QUA-020`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-02-analysis.md` · Branch: `feat/wp-qua-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-QUA-07 — Explicit statement of what is and is not qualified

- Planned · P2 · 1w · seq 108 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-04` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-QUA-090`
- Accept: PLAN-001 §5.4 exit criterion: Documentation states, in one place, what qualification evidence is provided and what remains the user's responsibility, and no other document claims more
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-07-analysis.md` · Branch: `feat/wp-qua-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-SEC-03 — Untrusted-project warning and configuration-is-data

- Planned · P2 · 3w · seq 109 · Backlog (planned WP) · hard deps met: yes
- deps `WP-PRJ-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-SEC-050`, `TOOL-SEC-070`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/` · Branch: `feat/wp-sec-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-PKG-02 — Self-contained archivable release identity

- Planned · P2 · 3w · seq 110 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-01`, `WP-CORE-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-INS-040`, `TOOL-QUA-050`
- Accept: Every owned requirement is verified by its Appendix A method (I×2; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/`, `docs/verification/WP-PKG-02-analysis.md` · Branch: `feat/wp-pkg-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL

#### WP-PKG-04 — Documented uninstallation

- Planned · P2 · 1w · seq 111 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-INS-070`
- Accept: Every owned requirement is verified by its Appendix A method (D×1; techniques: SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/` · Branch: `feat/wp-pkg-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL

#### WP-PKG-09 — Installation without administrative privileges

- Planned · P2 · 1w · seq 112 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-NFR-110`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/`, `docs/verification/WP-PKG-09-analysis.md` · Branch: `feat/wp-pkg-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL

#### WP-PLG-04 — AI provider extension protocol, registration and capability negotiation

- Planned · P2 · 3w · seq 113 · Backlog (planned WP) · hard deps met: no
- deps `WP-PLG-01` · no decision block · ADR `ADR-008` · PR `PR#4`
- Reqs: `TOOL-PLG-100`
- Accept: PLAN-001 §5.4 exit criterion: A third-party provider registers via the public extension API, negotiates capabilities and version compatibility, and an incompatible provider is rejected without loading it into a feature
- Files: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-04-analysis.md` · Branch: `feat/wp-plg-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/plg/`; G-FULL

#### WP-API-02 — Local-only transport with no network listener

- Planned · P2 · 2w · seq 114 · Backlog (planned WP) · hard deps met: no
- deps `WP-API-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-UIX-050`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/api/`, `tests/api/` · Branch: `feat/wp-api-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/api/`; G-FULL

#### WP-GUI-01 — Application shell, installability and platform support

- Planned · P2 · 6w · seq 115 · Backlog (planned WP) · hard deps met: no
- deps `WP-API-01`, `WP-SPIKE-03` · no decision block · watch `D-03` · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-030`, `TOOL-UIX-040`, `TOOL-UIX-340`, `TOOL-UIX-350`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, I×2, T×1; techniques: INSPECTION CHECKLIST, PAIRWISE, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/`, `docs/verification/WP-GUI-01-analysis.md` · Branch: `feat/wp-gui-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-ING-04 — Test scope model and resolution

- Planned · P2 · 5w · seq 116 · Backlog (planned WP) · hard deps met: yes
- deps `WP-ING-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-ING-120`, `TOOL-ING-130`, `TOOL-ING-140`, `TOOL-ING-150`, `TOOL-ING-190`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×4; techniques: EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ing/`, `tests/ing/`, `docs/verification/WP-ING-04-analysis.md` · Branch: `feat/wp-ing-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/`; G-FULL

#### WP-PKG-03 — Side-by-side versions and confirmed upgrade

- Planned · P2 · 4w · seq 117 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-01`, `WP-PRJ-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-INS-050`, `TOOL-INS-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/` · Branch: `feat/wp-pkg-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL

#### WP-QUA-04 — Known error list maintained per release

- Planned · P2 · 2w · seq 118 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-QUA-040`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-04-analysis.md` · Branch: `feat/wp-qua-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-SEC-01 — Release signing and Software Bill of Materials

- Planned · P2 · 3w · seq 119 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-SEC-010`, `TOOL-SEC-020`
- Accept: Every owned requirement is verified by its Appendix A method (I×2; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-01-analysis.md` · Branch: `feat/wp-sec-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-API-03 — CLI and GUI round-trip equivalence

- Planned · P2 · 3w · seq 120 · Backlog (planned WP) · hard deps met: no
- deps `WP-API-01`, `WP-CLI-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-UIX-330`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/api/`, `tests/api/` · Branch: `feat/wp-api-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/api/`; G-FULL

#### WP-ANA-05 — Control flow graph capability

- Planned · P2 · 6w · seq 121 · Backlog (planned WP) · hard deps met: yes
- deps `WP-ANA-01`, `WP-SPIKE-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-PAR-070`, `TOOL-PAR-120`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ana/`, `tests/ana/` · Branch: `feat/wp-ana-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`; G-FULL

#### WP-SEC-02 — Reproducible build and pinned dependency integrity

- Planned · P2 · 4w · seq 122 · Backlog (planned WP) · hard deps met: no
- deps `WP-SEC-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-SEC-030`, `TOOL-SEC-040`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, I×1; techniques: INSPECTION CHECKLIST, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-02-analysis.md` · Branch: `feat/wp-sec-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-TCH-07 — First-run environment verification

- Planned · P2 · 2w · seq 123 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCH-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-INS-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/` · Branch: `feat/wp-tch-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-CLI-04 — Reference CI pipelines and artifact caching

- Planned · P2 · 3w · seq 124 · Backlog (planned WP) · hard deps met: no
- deps `WP-CLI-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-CIC-050`, `TOOL-CIC-070`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cli/`, `tests/cli/` · Branch: `feat/wp-cli-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cli/`; G-FULL

#### WP-PKG-05 — Versioned CI container image

- Planned · P2 · 2w · seq 125 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-01`, `WP-CLI-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-INS-090`
- Accept: Every owned requirement is verified by its Appendix A method (D×1; techniques: SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/` · Branch: `feat/wp-pkg-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL

#### WP-GUI-02 — Project and environment management workflow

- Planned · P2 · 5w · seq 126 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-01`, `WP-PRJ-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-060`, `TOOL-UIX-070`, `TOOL-UIX-100`
- Accept: Every owned requirement is verified by its Appendix A method (T×3; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GUI-07 — Console pane reproducing engine commands

- Planned · P2 · 2w · seq 127 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-01`, `WP-API-03` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-240`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GUI-09 — Actionable error messaging

- Planned · P2 · 2w · seq 128 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-01`, `WP-CORE-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-360`
- Accept: Every owned requirement is verified by its Appendix A method (D×1; techniques: SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GUI-05 — Navigation tree, status aggregation, filter and search

- Planned · P2 · 5w · seq 129 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-110`, `TOOL-UIX-120`, `TOOL-UIX-130`, `TOOL-UIX-140`
- Accept: Every owned requirement is verified by its Appendix A method (T×4; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-ANA-08 — Analysis model decision inventory

- Planned · P2 · 1w · seq 130 · Backlog (planned WP) · hard deps met: yes
- deps `WP-ANA-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-PAR-150`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green. Partial progress: Model, schema 1.1 and reader gates for the decision inventory landed via T-09 (PAR-150); status stays Planned until the WP exit criterion is verified (candidate for TASK-016/017).
- Files: `src/ectt/ana/`, `tests/ana/` · Branch: `feat/wp-ana-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`; G-FULL
- Notes: Model, schema 1.1 and reader gates for the decision inventory landed via T-09 (PAR-150); status stays Planned until the WP exit criterion is verified (candidate for TASK-016/017).

#### WP-ANA-09 — Value ranges and dimension metadata in the analysis model

- Planned · P2 · 1w · seq 131 · Backlog (planned WP) · hard deps met: yes
- deps `WP-ANA-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-PAR-160`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green. Partial progress: Value ranges/dimensions in model + schema 1.2 landed via T-10 (PAR-160); status stays Planned until the WP exit criterion is verified (candidate for TASK-016/017).
- Files: `src/ectt/ana/`, `tests/ana/` · Branch: `feat/wp-ana-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ana/`; G-FULL
- Notes: Value ranges/dimensions in model + schema 1.2 landed via T-10 (PAR-160); status stays Planned until the WP exit criterion is verified (candidate for TASK-016/017).

#### WP-ING-05 — Scope conflict detection and external dependency reporting

- Planned · P2 · 3w · seq 132 · Backlog (planned WP) · hard deps met: no
- deps `WP-ING-04`, `WP-ANA-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-ING-160`, `TOOL-ING-170`, `TOOL-ING-180`
- Accept: Every owned requirement is verified by its Appendix A method (T×3; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ing/`, `tests/ing/` · Branch: `feat/wp-ing-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/`; G-FULL

#### WP-TCM-02 — Data-driven test case model and on-disk format

- Planned · P2 · 5w · seq 133 · Backlog (planned WP) · hard deps met: yes
- deps `WP-PRJ-01`, `WP-ANA-04` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-TCD-020`, `TOOL-TCD-030`, `TOOL-TCD-040`, `TOOL-TCD-140`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×3; techniques: EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-02-analysis.md` · Branch: `feat/wp-tcm-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-GEN-06 — Stub generation core

- Planned · P2 · 4w · seq 134 · Backlog (planned WP) · hard deps met: no
- deps `WP-ANA-04`, `WP-ING-05` · no decision block · ADR — · PR —
- Reqs: `TOOL-STB-010`, `TOOL-STB-020`, `TOOL-STB-030`
- Accept: Every owned requirement is verified by its Appendix A method (T×3; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GUI-03 — Integration scope creation and dependency preview

- Planned · P2 · 3w · seq 135 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-02`, `WP-ING-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-CORE-05 — Performance, scale and memory envelope

- Planned · P2 · 4w · seq 136 · Backlog (planned WP) · hard deps met: yes
- deps — · schedule/port `~WP-ANA-04`, `~WP-GEN-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-NFR-030`, `TOOL-NFR-040`, `TOOL-NFR-050`, `TOOL-NFR-150`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, D×3; techniques: ANALYSIS ARGUMENT, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-05-analysis.md` · Branch: `feat/wp-core-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL

#### WP-GEN-02 — Framework back-ends: Unity and cmocka

- Planned · P2 · 4w · seq 137 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-01`, `WP-PLG-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-HAR-060`, `TOOL-HAR-070`, `TOOL-PLG-030`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, T×2; techniques: ANALYSIS ARGUMENT, EQUIVALENCE PARTITIONING, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-02-analysis.md` · Branch: `feat/wp-gen-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GEN-03 — Static exposure and integration-scope harness

- Planned · P2 · 4w · seq 138 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-01`, `WP-ING-04`, `WP-ANA-06` · no decision block · ADR — · PR —
- Reqs: `TOOL-HAR-030`, `TOOL-HAR-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GEN-04 — Regeneration contract and conflict reporting

- Planned · P2 · 5w · seq 139 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-HAR-090`, `TOOL-HAR-100`, `TOOL-HAR-110`, `TOOL-CBT-070`
- Accept: PLAN-001 §5.4 exit criterion: Regenerating a harness whose user region is still valid preserves it byte-for-byte; regenerating one whose UUT signature changed incompatibly reports a conflict and writes nothing
- Files: `src/ectt/gen/`, `tests/gen/`, `docs/verification/WP-GEN-04-analysis.md` · Branch: `feat/wp-gen-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GUI-10 — Tabular data-driven test case editor

- Planned · P2 · 5w · seq 140 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-05`, `WP-TCM-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-150`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-10 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-TCM-03 — Expected-value comparison engine

- Planned · P2 · 4w · seq 141 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCD-050`, `TOOL-TCD-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: BOUNDARY VALUE ANALYSIS, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/` · Branch: `feat/wp-tcm-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-TCM-04 — Suites, selective execution and test independence

- Planned · P2 · 3w · seq 142 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCD-080`, `TOOL-TCD-090`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, T×1; techniques: ANALYSIS ARGUMENT, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/`, `docs/verification/WP-TCM-04-analysis.md` · Branch: `feat/wp-tcm-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-TCM-05 — Ranged and robustness input generation

- Planned · P2 · 3w · seq 143 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCD-070`, `TOOL-TCD-130`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/` · Branch: `feat/wp-tcm-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-TCM-06 — Test case interchange import and export

- Planned · P2 · 3w · seq 144 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCD-100`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/` · Branch: `feat/wp-tcm-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-GEN-07 — Stub behaviour programming

- Planned · P2 · 5w · seq 145 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-06`, `WP-TCM-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-STB-040`, `TOOL-STB-050`, `TOOL-STB-060`, `TOOL-STB-070`
- Accept: Every owned requirement is verified by its Appendix A method (T×4; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GEN-08 — Stub scope control and indirect-call stubbing

- Planned · P2 · 4w · seq 146 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-06`, `WP-ANA-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-STB-080`, `TOOL-STB-100`, `TOOL-STB-140`
- Accept: Every owned requirement is verified by its Appendix A method (T×3; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-BLD-02 — Sanitizer integration

- Planned · P2 · 2w · seq 147 · Backlog (planned WP) · hard deps met: no
- deps `WP-BLD-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-EXE-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/bld/`, `tests/bld/` · Branch: `feat/wp-bld-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/bld/`; G-FULL

#### WP-GEN-05 — Link closure and unresolved reference reporting

- Planned · P2 · 2w · seq 148 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-06`, `WP-ANA-03` · schedule/port `~WP-BLD-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-HAR-120`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GUI-04 — Build progress and navigable compiler diagnostics

- Planned · P2 · 3w · seq 149 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-02`, `WP-BLD-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GEN-09 — Stub regeneration and unsupported-construct flagging

- Planned · P2 · 4w · seq 150 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-04`, `WP-GEN-06` · no decision block · ADR — · PR —
- Reqs: `TOOL-STB-110`, `TOOL-STB-120`, `TOOL-STB-130`
- Accept: Every owned requirement is verified by its Appendix A method (T×3; techniques: BOUNDARY VALUE ANALYSIS, DECISION TABLE, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-GUI-11 — Nested type-aware value editor

- Planned · P2 · 8w · seq 151 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-10`, `WP-SPIKE-02`, `WP-ANA-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-160`, `TOOL-UIX-170`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-11 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-CBT-01 — Suite re-execution without regeneration

- Planned · P2 · 2w · seq 152 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXH-01`, `WP-TCM-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-CBT-010`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cbt/`, `tests/cbt/` · Branch: `feat/wp-cbt-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cbt/`; G-FULL

#### WP-GUI-06 — Execution control and per-test result presentation

- Planned · P2 · 4w · seq 153 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-05`, `WP-EXH-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-210`, `TOOL-UIX-220`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-MIG-01 — Execution of existing Unity and cmocka suites

- Planned · P2 · 4w · seq 154 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-02`, `WP-EXH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-010`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/` · Branch: `feat/wp-mig-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-CORE-08 — Self-verification of the tool's own source

- Planned · P2 · 3w · seq 155 · Backlog (planned WP) · hard deps met: yes
- deps — · schedule/port `~WP-EXH-01`, `~WP-COV-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-NFR-140`, `TOOL-NFR-170`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, D×1; techniques: ANALYSIS ARGUMENT, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/core/`, `tests/core/`, `docs/verification/WP-CORE-08-analysis.md` · Branch: `feat/wp-core-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/core/`; G-FULL

#### WP-MIG-02 — Ceedling project import

- Planned · P2 · 4w · seq 156 · Backlog (planned WP) · hard deps met: no
- deps `WP-MIG-01`, `WP-ING-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/` · Branch: `feat/wp-mig-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-REP-12 — Reconstructable open result export with test-case coordination

- Planned · P2 · 3w · seq 157 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-TCM-06` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-060`
- Accept: PLAN-001 §5.4 exit criterion: Export passing, failing, crashed, timed-out and partial-run cases plus result identities, expected/actual values, diagnostics and provenance; an independent reader reconstructs the test cases from TCM-06 and complete results without a private project database. Publish the versioned JSON interchange schema, examples and explicit loss/error handling; coverage export remains REP-10/P4
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-12 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-MIG-03 — Interchange format documentation

- Planned · P2 · 2w · seq 158 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-06`, `WP-REP-12` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-100`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/`, `docs/verification/WP-MIG-03-analysis.md` · Branch: `feat/wp-mig-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-QUA-03 — User-executable validation suite

- Planned · P2 · 6w · seq 159 · Backlog (planned WP) · hard deps met: no
- deps `WP-QUA-02`, `WP-CORE-08` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-QUA-030`, `TOOL-QUA-110`
- Accept: PLAN-001 §5.4 exit criterion: For each harness-agreement fixture, the generated-harness outcome equals the hand-written reference-test outcome on the same inputs — including one failing case and one stubbed-dependency case; any disagreement is reported as a harness-generation defect
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-03-analysis.md` · Branch: `feat/wp-qua-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-GUI-08 — Coverage summary, annotation and basic HTML report launch

- Planned · P2 · 4w · seq 160 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-05`, `WP-COV-02`, `WP-REP-03` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-250`, `TOOL-UIX-280`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-AIF-01 — Provider abstraction and local model runtime

- Planned · P3 · 5w · seq 161 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-03` · no decision block · ADR `ADR-008` · PR `PR#4`
- Reqs: `TOOL-AIF-020`, `TOOL-AIF-050`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, T×1; techniques: ANALYSIS ARGUMENT, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/`, `docs/verification/WP-AIF-01-analysis.md` · Branch: `feat/wp-aif-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-SEC-08 — Credential storage via platform secure storage

- Planned · P3 · 3w · seq 162 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-03` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-SEC-110`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/` · Branch: `feat/wp-sec-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-SEC-07 — Target-supplied data treated as untrusted

- Planned · P3 · 2w · seq 163 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-SEC-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/` · Branch: `feat/wp-sec-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-AIF-02 — Optionality, separability and default-off

- Planned · P3 · 2w · seq 164 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-010`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-AIF-03 — Data egress control and pre-use disclosure

- Planned · P3 · 3w · seq 165 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-SEC-08` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-030`, `TOOL-AIF-040`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: DECISION TABLE, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-AIF-05 — Append-only AI provenance, replay constraints and review state

- Planned · P3 · 5w · seq 166 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-CORE-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-080`, `TOOL-AIF-090`, `TOOL-AIF-160`, `TOOL-AIF-180`, `TOOL-AIF-190`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, I×2, T×2; techniques: ANALYSIS ARGUMENT, EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/`, `docs/verification/WP-AIF-05-analysis.md` · Branch: `feat/wp-aif-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-AIF-06 — Time and token bounds on AI operations

- Planned · P3 · 2w · seq 167 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-150`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-MIG-06 — Coexistence with another tool on one project

- Planned · P3 · 3w · seq 168 · Backlog (planned WP) · hard deps met: yes
- deps `WP-CORE-01`, `WP-PRJ-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-070`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/` · Branch: `feat/wp-mig-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-PKG-06 — Shared read-only multi-user installation

- Planned · P3 · 3w · seq 169 · Backlog (planned WP) · hard deps met: no
- deps `WP-PKG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-INS-100`
- Accept: Every owned requirement is verified by its Appendix A method (D×1; techniques: SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/pkg/`, `tests/pkg/` · Branch: `feat/wp-pkg-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/pkg/`; G-FULL

#### WP-PLG-02 — Extension discovery and load failure isolation

- Planned · P3 · 3w · seq 170 · Backlog (planned WP) · hard deps met: no
- deps `WP-PLG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-PLG-070`, `TOOL-PLG-080`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/plg/`, `tests/plg/` · Branch: `feat/wp-plg-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/plg/`; G-FULL

#### WP-ING-06 — Multi-toolchain ingestion

- Planned · P3 · 2w · seq 171 · Backlog (planned WP) · hard deps met: no
- deps `WP-ING-01`, `WP-TCH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-ING-110`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ing/`, `tests/ing/` · Branch: `feat/wp-ing-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ing/`; G-FULL

#### WP-TCH-03 — Cross-toolchain support and shipped configurations

- Planned · P3 · 5w · seq 172 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCH-030`, `TOOL-TCH-040`, `TOOL-TCH-050`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/`, `docs/verification/WP-TCH-03-analysis.md` · Branch: `feat/wp-tch-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-TCH-04 — Capability declaration and compiler version gating

- Planned · P3 · 3w · seq 173 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCH-060`, `TOOL-TCH-070`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/` · Branch: `feat/wp-tch-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-AIF-07 — Local model integrity and hardware requirements

- Planned · P3 · 3w · seq 174 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-SEC-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-170`, `TOOL-AIF-200`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×1; techniques: EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/`, `docs/verification/WP-AIF-07-analysis.md` · Branch: `feat/wp-aif-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-SEC-09 — Dependency vulnerability scanning in CI

- Planned · P3 · 2w · seq 175 · Backlog (planned WP) · hard deps met: no
- deps `WP-SEC-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-SEC-100`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/`, `docs/verification/WP-SEC-09-analysis.md` · Branch: `feat/wp-sec-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-GUI-18 — Non-blocking interface during long operations

- Planned · P3 · 4w · seq 176 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-01`, `WP-CORE-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-370`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-18 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-TCH-06 — Proprietary compiler support

- Planned · P3 · 4w · seq 177 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCH-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCH-100`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/` · Branch: `feat/wp-tch-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-TCM-07 — Boundary, equivalence and classification-tree derivation

- Planned · P3 · 5w · seq 178 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02`, `WP-ANA-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCD-110`, `TOOL-TCD-120`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tcm/`, `tests/tcm/` · Branch: `feat/wp-tcm-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tcm/`; G-FULL

#### WP-MIG-04 — Commercial tool and CSV test data import

- Planned · P3 · 6w · seq 179 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-06` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-030`, `TOOL-MIG-050`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/` · Branch: `feat/wp-mig-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-BLD-03 — Cross-compiled target build

- Planned · P3 · 3w · seq 180 · Backlog (planned WP) · hard deps met: no
- deps `WP-BLD-01`, `WP-TCH-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-010`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/bld/`, `tests/bld/` · Branch: `feat/wp-bld-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/bld/`; G-FULL

#### WP-GEN-10 — GoogleTest back-end (host only)

- Planned · P3 · 3w · seq 181 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-HAR-065`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-10 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-TCH-05 — Multi-toolchain builds and reproducible containers

- Planned · P3 · 3w · seq 182 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCH-03` · schedule/port `~WP-BLD-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TCH-080`, `TOOL-TCH-090`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: PAIRWISE, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/tch/`, `tests/tch/` · Branch: `feat/wp-tch-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/tch/`; G-FULL

#### WP-GUI-13 — Ranged and boundary input authoring

- Planned · P3 · 3w · seq 183 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-10`, `WP-TCM-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-190`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-13 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GUI-14 — C source test editor with syntax highlighting

- Planned · P3 · 3w · seq 184 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-10`, `WP-TCM-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-200`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-14 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GEN-11 — Call wrapping of intra-unit calls

- Planned · P3 · 3w · seq 185 · Backlog (planned WP) · hard deps met: no
- deps `WP-GEN-08`, `WP-ANA-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-STB-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gen/`, `tests/gen/` · Branch: `feat/wp-gen-11 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gen/`; G-FULL

#### WP-EXT-01 — Simulator execution: QEMU and Renode

- Planned · P3 · 5w · seq 186 · Backlog (planned WP) · hard deps met: no
- deps `WP-BLD-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-020`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ext/`, `tests/ext/` · Branch: `feat/wp-ext-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-EXT-02 — Hardware execution and flashing via debug probe

- Planned · P3 · 6w · seq 187 · Backlog (planned WP) · hard deps met: no
- deps `WP-BLD-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-030`, `TOOL-TGT-040`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ext/`, `tests/ext/` · Branch: `feat/wp-ext-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-GUI-12 — Stub configuration view

- Planned · P3 · 4w · seq 188 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-10`, `WP-GEN-07` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-180`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-12 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-AIF-10 — AI-assisted test failure explanation

- Planned · P3 · 3w · seq 189 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-EXH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-120`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-10 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-ATG-01 — Validation port and generated-case lifecycle

- Planned · P3 · 4w · seq 190 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02` · schedule/port `^WP-EXH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-ATG-040`, `TOOL-ATG-050`, `TOOL-ATG-070`, `TOOL-ATG-080`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×3; techniques: DECISION TABLE, EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/atg/`, `tests/atg/`, `docs/verification/WP-ATG-01-analysis.md` · Branch: `feat/wp-atg-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/atg/`; G-FULL

#### WP-MIG-05 — Import fidelity reporting

- Planned · P3 · 3w · seq 191 · Backlog (planned WP) · hard deps met: no
- deps `WP-MIG-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-040`, `TOOL-MIG-110`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/` · Branch: `feat/wp-mig-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-SEC-06 — Restricted execution context for harnesses

- Planned · P3 · 4w · seq 192 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXH-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-SEC-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/sec/`, `tests/sec/` · Branch: `feat/wp-sec-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/sec/`; G-FULL

#### WP-AIF-04 — Generated artifact validation and rejection recording

- Planned · P3 · 4w · seq 193 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-ATG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-070`, `TOOL-AIF-210`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-ATG-05 — Generation reporting, bounds and capability limits

- Planned · P3 · 3w · seq 194 · Backlog (planned WP) · hard deps met: no
- deps `WP-ATG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-ATG-060`, `TOOL-ATG-100`, `TOOL-ATG-110`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/atg/`, `tests/atg/` · Branch: `feat/wp-atg-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/atg/`; G-FULL

#### WP-COV-04 — Function and function-call coverage

- Planned · P3 · 2w · seq 195 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-030`, `TOOL-COV-040`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-COV-08 — Unit-under-test versus harness coverage separation

- Planned · P3 · 2w · seq 196 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-01`, `WP-ING-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-160`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-EXT-03 — Target result retrieval channels and protocol

- Planned · P3 · 4w · seq 197 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXT-01`, `WP-SEC-07` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-050`, `TOOL-TGT-060`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, T×1; techniques: ANALYSIS ARGUMENT, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-03-analysis.md` · Branch: `feat/wp-ext-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-GUI-15 — Debugger launch from the application

- Planned · P3 · 4w · seq 198 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-06`, `WP-EXH-04` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-230`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-15 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-REP-08 — Cross-unit summary and coverage trend

- Planned · P3 · 4w · seq 199 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-110`, `TOOL-REP-120`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-REP-11 — Report format extension point

- Planned · P3 · 2w · seq 200 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-PLG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-PLG-050`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-11 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-EXT-05 — Hardware inventory and target failure classification

- Planned · P3 · 4w · seq 201 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXT-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-080`, `TOOL-TGT-090`
- Accept: Every owned requirement is verified by its Appendix A method (D×1, T×1; techniques: DECISION TABLE, SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ext/`, `tests/ext/` · Branch: `feat/wp-ext-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-EXT-06 — Suite splitting and on-target footprint documentation

- Planned · P3 · 4w · seq 202 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXT-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-100`, `TOOL-TGT-110`
- Accept: Every owned requirement is verified by its Appendix A method (A×1, T×1; techniques: ANALYSIS ARGUMENT, BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ext/`, `tests/ext/`, `docs/verification/WP-EXT-06-analysis.md` · Branch: `feat/wp-ext-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-EXT-07 — User-supplied target execution methods

- Planned · P3 · 3w · seq 203 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXT-02`, `WP-PLG-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-120`, `TOOL-PLG-040`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/ext/`, `tests/ext/` · Branch: `feat/wp-ext-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-PLG-03 — Built-ins implemented through public extension points

- Planned · P3 · 3w · seq 204 · Backlog (planned WP) · hard deps met: no
- deps `WP-PLG-01` · schedule/port `~WP-TCH-01`, `~WP-GEN-02`, `~WP-REP-11` · no decision block · ADR — · PR —
- Reqs: `TOOL-PLG-090`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/plg/`, `tests/plg/`, `docs/verification/WP-PLG-03-analysis.md` · Branch: `feat/wp-plg-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/plg/`; G-FULL

#### WP-AIF-08 — AI-assisted test case generation

- Planned · P3 · 4w · seq 205 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-04`, `WP-COV-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-AIF-09 — AI-assisted stub body generation

- Planned · P3 · 3w · seq 206 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-04`, `WP-GEN-06` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-110`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-AIF-11 — AI-assisted naming and documentation

- Planned · P3 · 2w · seq 207 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-140`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-11 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-AIF-14 — Typed decision evaluation, validation and provider role separation

- Planned · P3 · 4w · seq 208 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-PLG-04`, `WP-AIF-04` · no decision block · ADR `ADR-008` · PR `PR#4`
- Reqs: `TOOL-AIF-220`, `TOOL-AIF-230`
- Accept: PLAN-001 §5.4 exit criterion: Valid typed decisions pass schema/domain validation; invalid, unsupported, failed and timed-out provider responses produce recorded rejection and no altered measured result
- Files: `src/ectt/aif/`, `tests/aif/`, `docs/verification/WP-AIF-14-analysis.md` · Branch: `feat/wp-aif-14 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-CBT-02 — Change impact analysis and subset execution

- Planned · P3 · 5w · seq 209 · Backlog (planned WP) · hard deps met: no
- deps `WP-CBT-01`, `WP-COV-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-CBT-020`, `TOOL-CBT-030`, `TOOL-CBT-040`
- Accept: Every owned requirement is verified by its Appendix A method (I×1, T×2; techniques: BOUNDARY VALUE ANALYSIS, EQUIVALENCE PARTITIONING, INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cbt/`, `tests/cbt/`, `docs/verification/WP-CBT-02-analysis.md` · Branch: `feat/wp-cbt-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cbt/`; G-FULL

#### WP-CBT-03 — Run comparison and coverage delta

- Planned · P3 · 3w · seq 210 · Backlog (planned WP) · hard deps met: no
- deps `WP-CBT-01`, `WP-COV-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-CBT-050`, `TOOL-CBT-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cbt/`, `tests/cbt/` · Branch: `feat/wp-cbt-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cbt/`; G-FULL

#### WP-CLI-05 — CI sharding and report merge

- Planned · P3 · 3w · seq 211 · Backlog (planned WP) · hard deps met: no
- deps `WP-CLI-04`, `WP-REP-08` · no decision block · ADR — · PR —
- Reqs: `TOOL-CIC-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cli/`, `tests/cli/` · Branch: `feat/wp-cli-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cli/`; G-FULL

#### WP-COV-07 — Bare-metal coverage retrieval

- Planned · P3 · 5w · seq 212 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-01`, `WP-EXT-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-100`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-EXT-04 — Host and target test parity

- Planned · P3 · 3w · seq 213 · Backlog (planned WP) · hard deps met: no
- deps `WP-EXT-03`, `WP-EXH-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TGT-070`, `TOOL-TGT-130`
- Accept: PLAN-001 §5.4 exit criterion: A host-executed result carries a versioned host profile naming the target→host derivation and its known ABI differences, with unmeasured differences shown as unknown; host success is never displayed as target behavior
- Files: `src/ectt/ext/`, `tests/ext/` · Branch: `feat/wp-ext-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/ext/`; G-FULL

#### WP-COV-06 — Uninstrumentable expression detection

- Planned · P3 · 3w · seq 214 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-05` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-080`, `TOOL-COV-190`
- Accept: PLAN-001 §5.4 exit criterion: The probed effective condition maximum and limit-option availability are recorded per pinned backend as run evidence, and a decision exceeding the recorded maximum is unmeasured with that limit in its reason
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-REP-04 — MC/DC condition detail rendering

- Planned · P3 · 3w · seq 215 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-03`, `WP-COV-05` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-050`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-AIF-15 — Local/enterprise substitution and all-role extension conformance

- Planned · P3 · 4w · seq 216 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-14`, `WP-PLG-04` · no decision block · ADR `ADR-008` · PR —
- Reqs: `TOOL-AIF-250`, `TOOL-AIF-260`
- Accept: PLAN-001 §5.4 exit criterion: Exercise remote and local/self-hosted adapters through the same extension contract for each role; deny unsupported capabilities explicitly and verify no calling feature imports a vendor SDK
- Files: `src/ectt/aif/`, `tests/aif/`, `docs/verification/WP-AIF-15-analysis.md` · Branch: `feat/wp-aif-15 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-ATG-04 — Targeted generation against uncovered constructs

- Planned · P3 · 4w · seq 217 · Backlog (planned WP) · hard deps met: no
- deps `WP-ATG-02` · schedule/port `^WP-COV-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-ATG-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/atg/`, `tests/atg/` · Branch: `feat/wp-atg-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/atg/`; G-FULL

#### WP-GUI-16 — MC/DC per-condition detail view

- Planned · P3 · 3w · seq 218 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-08`, `WP-COV-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-260`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-16 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-GUI-17 — Graphical control flow view with coverage overlay

- Planned · P3 · 5w · seq 219 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-08`, `WP-ANA-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-270`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-17 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-CBT-04 — Test suite minimization

- Planned · P3 · 3w · seq 220 · Backlog (planned WP) · hard deps met: no
- deps `WP-CBT-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-CBT-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cbt/`, `tests/cbt/` · Branch: `feat/wp-cbt-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cbt/`; G-FULL

#### WP-QUA-05 — Development process and change control documentation

- Planned · P4 · 3w · seq 221 · Backlog (planned WP) · hard deps met: yes
- deps — · no decision block · ADR — · PR —
- Reqs: `TOOL-QUA-070`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-05-analysis.md` · Branch: `feat/wp-qua-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-QUA-01 — Tool classification analysis and confidence level

- Planned · P4 · 3w · seq 222 · Backlog (planned WP) · hard deps met: no
- deps `WP-CORE-04` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-QUA-010`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-01-analysis.md` · Branch: `feat/wp-qua-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-QUA-06 — Standards objective mapping

- Planned · P4 · 4w · seq 223 · Backlog (planned WP) · hard deps met: no
- deps `WP-QUA-02` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-QUA-080`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-06-analysis.md` · Branch: `feat/wp-qua-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-QUA-08 — Templates for user tool qualification artifacts

- Planned · P4 · 3w · seq 224 · Backlog (planned WP) · hard deps met: no
- deps `WP-QUA-06` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-QUA-100`
- Accept: Every owned requirement is verified by its Appendix A method (I×1; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/qua/`, `tests/qua/`, `docs/verification/WP-QUA-08-analysis.md` · Branch: `feat/wp-qua-08 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/qua/`; G-FULL

#### WP-GUI-22 — Keyboard-driven workflow

- Planned · P4 · 3w · seq 225 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-380`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-22 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-COV-09 — Coverage-by-analysis justification with digest binding

- Planned · P4 · 4w · seq 226 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-01`, `WP-PRJ-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-COV-140`, `TOOL-COV-150`
- Accept: PLAN-001 §5.4 exit criterion: Editing a source line under an accepted justification invalidates that justification, and the next report shows the construct as uncovered rather than justified
- Files: `src/ectt/cov/`, `tests/cov/`, `docs/verification/WP-COV-09-analysis.md` · Branch: `feat/wp-cov-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-COV-11 — Control coupling and data coupling analysis

- Planned · P4 · 6w · seq 227 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-01`, `WP-ANA-03`, `WP-ING-04` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-COV-170`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-11 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-MIG-07 — Migration assessment mode

- Planned · P4 · 4w · seq 228 · Backlog (planned WP) · hard deps met: no
- deps `WP-MIG-05` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/mig/`, `tests/mig/` · Branch: `feat/wp-mig-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/mig/`; G-FULL

#### WP-REP-06 — Report provenance and format version stability

- Planned · P4 · 3w · seq 229 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-CORE-04` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-070`, `TOOL-REP-130`
- Accept: Every owned requirement is verified by its Appendix A method (I×2; techniques: INSPECTION CHECKLIST) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/`, `docs/verification/WP-REP-06-analysis.md` · Branch: `feat/wp-rep-06 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-TRC-01 — Requirement association and bidirectional matrix

- Planned · P4 · 4w · seq 230 · Backlog (planned WP) · hard deps met: no
- deps `WP-TCM-02`, `WP-REP-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TRC-010`, `TOOL-TRC-020`, `TOOL-TRC-030`, `TOOL-TRC-110`
- Accept: PLAN-001 §5.4 exit criterion: A requirement linked by two association rows to the same test aggregates to one counted pair and one worst-outcome verdict — never a 2/1 numerator-over-denominator — and a requirement linked to no executed test is reported unverified
- Files: `src/ectt/trc/`, `tests/trc/` · Branch: `feat/wp-trc-01 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/trc/`; G-FULL

#### WP-PRJ-05 — Archival export and reproduction verification

- Planned · P4 · 4w · seq 231 · Backlog (planned WP) · hard deps met: no
- deps `WP-PRJ-01`, `WP-CORE-04` · schedule/port `~WP-REP-06` · no decision block · ADR `ADR-002` · PR —
- Reqs: `TOOL-PRJ-100`, `TOOL-PRJ-110`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/prj/`, `tests/prj/` · Branch: `feat/wp-prj-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/prj/`; G-FULL

#### WP-AIF-13 — AI-proposed requirement-to-test links

- Planned · P4 · 3w · seq 232 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-01`, `WP-TRC-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-AIF-130`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-13 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-GUI-21 — Traceability matrix view with navigation

- Planned · P4 · 3w · seq 233 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-05`, `WP-TRC-01` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-310`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-21 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-REP-05 — Certification verification report and scope statement

- Planned · P4 · 5w · seq 234 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-TRC-01`, `WP-COV-09` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-REP-060`, `TOOL-REP-140`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-REP-07 — Paginated PDF archival rendering

- Planned · P4 · 4w · seq 235 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-07 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-REP-10 — Coverage interchange import and export

- Planned · P4 · 3w · seq 236 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-COV-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-MIG-080`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-10 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-TRC-02 — Unlinked requirement and unlinked test reporting

- Planned · P4 · 2w · seq 237 · Backlog (planned WP) · hard deps met: no
- deps `WP-TRC-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TRC-040`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/trc/`, `tests/trc/` · Branch: `feat/wp-trc-02 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/trc/`; G-FULL

#### WP-TRC-03 — Requirement import from ReqIF, CSV and plain text

- Planned · P4 · 4w · seq 238 · Backlog (planned WP) · hard deps met: no
- deps `WP-TRC-01` · no decision block · ADR — · PR —
- Reqs: `TOOL-TRC-050`, `TOOL-TRC-060`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/trc/`, `tests/trc/` · Branch: `feat/wp-trc-03 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/trc/`; G-FULL

#### WP-TRC-05 — Source-element linking and requirement change detection

- Planned · P4 · 4w · seq 239 · Backlog (planned WP) · hard deps met: no
- deps `WP-TRC-01`, `WP-ANA-02` · no decision block · ADR — · PR —
- Reqs: `TOOL-TRC-080`, `TOOL-TRC-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: EQUIVALENCE PARTITIONING, STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/trc/`, `tests/trc/` · Branch: `feat/wp-trc-05 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/trc/`; G-FULL

#### WP-COV-10 — Unique-cause MC/DC support or documented gap

- Planned · P4 · 6w · seq 240 · Backlog (planned WP) · hard deps met: no
- deps `WP-COV-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-COV-090`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/cov/`, `tests/cov/` · Branch: `feat/wp-cov-10 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/cov/`; G-FULL

#### WP-REP-09 — Report generation from archived result data

- Planned · P4 · 3w · seq 241 · Backlog (planned WP) · hard deps met: no
- deps `WP-REP-01`, `WP-PRJ-05` · no decision block · ADR — · PR —
- Reqs: `TOOL-REP-150`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: STATE TRANSITION) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/rep/`, `tests/rep/` · Branch: `feat/wp-rep-09 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/rep/`; G-FULL

#### WP-AIF-16 — Configurable remote structured-decision default profile

- Planned · P4 · 2w · seq 242 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-14`, `WP-AIF-03` · no decision block · ADR `ADR-008` · PR —
- Reqs: `TOOL-AIF-240`
- Accept: Every owned requirement is verified by its Appendix A method (D×1; techniques: SCENARIO (demonstration)) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-16 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-GUI-19 — Coverage-by-analysis justification capture

- Planned · P4 · 3w · seq 243 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-08`, `WP-COV-09` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-290`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: EQUIVALENCE PARTITIONING) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-19 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL

#### WP-TRC-04 — ReqIF export and external traceability tool interop

- Planned · P4 · 4w · seq 244 · Backlog (planned WP) · hard deps met: no
- deps `WP-TRC-03` · no decision block · ADR — · PR —
- Reqs: `TOOL-TRC-070`, `TOOL-TRC-100`
- Accept: Every owned requirement is verified by its Appendix A method (T×2; techniques: DECISION TABLE, PAIRWISE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/trc/`, `tests/trc/` · Branch: `feat/wp-trc-04 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/trc/`; G-FULL

#### WP-AIF-12 — Certification evidence review and exclusion mode

- Planned · P4 · 2w · seq 245 · Backlog (planned WP) · hard deps met: no
- deps `WP-AIF-05`, `WP-REP-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-AIF-100`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: DECISION TABLE) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/aif/`, `tests/aif/` · Branch: `feat/wp-aif-12 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/aif/`; G-FULL

#### WP-GUI-20 — In-application report generation and viewing

- Planned · P4 · 3w · seq 246 · Backlog (planned WP) · hard deps met: no
- deps `WP-GUI-08`, `WP-REP-05` · no decision block · ADR `ADR-001` · PR —
- Reqs: `TOOL-UIX-300`
- Accept: Every owned requirement is verified by its Appendix A method (T×1; techniques: BOUNDARY VALUE ANALYSIS) and the exit evidence is recorded; full gate green.
- Files: `src/ectt/gui/`, `tests/gui/` · Branch: `feat/wp-gui-20 (new branch; base origin/main once docs/pending-decisions is merged — not scheduled yet)`
- Verify: `.venv/Scripts/python -m pytest -q -p no:cacheprovider tests/gui/`; G-FULL
<!-- END GENERATED: register -->

---

## Appendix A — Traceability chain

`SRS requirement (TOOL-…)` → `design element (DSN-…)` → `work package (WP-…)` → `tasks (T-xx / TASK-xxx)` → `ADR / decision / PR` → `tests and verification`.

- Requirement → WP: PLAN-001 Appendix A (one primary owner per non-Future requirement).
- Requirement → DSN: `design/trace/design-elements.yaml` (`satisfies`).
- WP → tasks: the `wps` field of each `T-`/`TASK-` task, plus the `scheduledVia` pointer on the WP.
- ADR / decision / PR: the `adrs`, `blockedBy`, `watch` and `prs` fields.
- Tests: for Implemented WPs the `files` list names the test files and verification records; for planned work the `verify` field names the commands that will produce the evidence. In the tracker, open **Traceability → any requirement** to walk the chain with clickable IDs.

## Appendix B — How this plan was built

Parsed on 2026-11-17 from PLAN-001 §5.4/§5.5/Appendix A, SRS-001 requirement lines, `design-elements.yaml`, the subsystem tracker's review-task tables and evidence sections, and `BACKLOG_GLM_NIGHT.md` §5/§6; commit and branch facts from `git`, PR facts from read-only `gh pr view`; gate and test results from running them at HEAD. `design/trace/requirement-matrix.csv` and `trace-graph.json` were not used for counts — they still list 323 requirements and are stale generated artefacts.
