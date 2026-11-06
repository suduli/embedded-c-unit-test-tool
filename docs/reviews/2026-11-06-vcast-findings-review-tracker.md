# vcast-findings ↔ ectt architecture review — task tracker

- **Date:** 2026-11-06 (created) · **Last updated:** 2026-11-07 (all six review tasks complete)
- **Subject reviewed:** `vcast-findings/` (VectorCAST 2026 SP4 static investigation, consolidated 2026-10-27; 225 files)
- **Baseline compared against:** ectt accepted architecture and work products — ADR-001/002/006/008, SDD-001..005, SRS-001, PLAN-001 (§5.5 register), and implemented `src/ectt` (WP-CORE-01, WP-PRJ-01, WP-ING-01, WP-ANA-01/02/04) at branch `feat/wp-prj-01`, HEAD `b5786e0`.
- **Method:** six parallel review agents (RV-01..RV-06), one per review domain. Each agent is read-only on `vcast-findings/`, `src/`, and all baseline docs; each writes exactly one evidence file under `docs/reviews/`.
- **Status legend:** `Not Started` → `In Progress` → `Complete` / `Blocked`.
- **Companion HTML tracker:** [`2026-11-06-vcast-findings-review-tracker.html`](2026-11-06-vcast-findings-review-tracker.html) (self-contained; same data and statuses).

---

## 1. Objective

The `vcast-findings/` investigation produced evidence registers (D1–D13, E1–E7), recovered persistence schemas, a proposed product architecture (FR-01..FR-12, phases M0–M5), prototype requirements (P01–P15), coverage/MC-DC findings, and a gap register. This review reconciles that material against ectt's accepted architecture and current implementation state, and classifies every finding as one of:

| Class | Meaning |
|---|---|
| `aligned` | vcast-findings confirms or independently supports an existing ectt decision/design element. |
| `conflict` | vcast-findings recommends something that contradicts an accepted ADR/SDD decision — needs a user decision, not a silent change. |
| `gap` | vcast-findings introduces a concept ectt's design or plan does not cover (candidate new ADR/WP). |
| `risk` | Evidence-backed caution that affects planning, scope claims, or verification strategy. |

The review produces **recommendations only**. No ADR/SDD/PLAN/SRS or source changes are made by this effort; follow-up edits require separate approval.

## 2. Task register

| ID | Review task | Evidence inputs (vcast-findings) | ectt baseline | Status | Evidence output | Findings summary |
|---|---|---|---|---|---|---|
| RV-01 | Stack & architecture comparison: proposed implementation stack (§2), alternatives (§2), support contract (§1), prerequisites (§10), phased delivery (§11) vs accepted language/GUI/storage/qualifications decisions | `deep-20261027/PRODUCT_ARCHITECTURE.md` (§1, §2, §10, §11, §12), `ARCHITECTURE.md`, `VCAPPLIB.md`, `deep-20261027/DEEP_ANALYSIS.md` | ADR-001 (Python core, PySide6 GUI, libclang front-end, JSON analysis-model seam), ADR-006 (build fresh), SDD-001 (24-component layering), SDD-005 (OSS catalogue, licence rule), PLAN-001 | **Complete** | [evidence-RV-01.md](2026-11-06-vcast-findings-evidence-RV-01.md) | 17 findings (5 conflict / 10 aligned / 1 gap / 1 risk). Proposal defaults conflict with accepted ADRs: React/TS web UI vs PySide6 + DSN-API-030, SQLite store vs ADR-002 YAML, GoogleTest foundation vs TOOL-HAR-060, C++ worker default (seam already accommodates swap), C++17 in first release. Incumbent's VcAppLib 81-export boundary, 7-mechanism pipeline and stub limits independently validate SDD-001/SDD-002. LinkPlan concept triple-validated. |
| RV-02 | Seams & contracts reconciliation: recovered subsystem boundaries 1–7 and core contracts (BuildContext, AnalysisSnapshot, HostProfile, LinkPlan, EnvironmentSpec, BuildArtifact, TestSpec, RunRecord, CoverageSnapshot) vs the seam register | `deep-20261027/DEEP_ANALYSIS.md` (D1–D13, boundaries 1–7, logical workflow), `deep-20261027/PRODUCT_ARCHITECTURE.md` (§3–§6), `deep-specifications/SPECIFICATION_RECOVERY.md` | SDD-002 (S1–S7 seams, versioning rule), SDD-004 (traceability meta-model), `src/ectt/ana` (S1 implementation), `src/ectt/ing` (compdb) | **Complete** | [evidence-RV-02.md](2026-11-06-vcast-findings-evidence-RV-02.md) | 15 findings (5 aligned / 8 gap / 1 conflict / 1 risk). AnalysisSnapshot↔S1, TestSpec↔S2, RunRecord↔S3 core, CoverageSnapshot↔S4 semantics match. Gaps: LinkPlan, HostProfile, CompiledTestManifest pre-run gate, RunAttempt identity, eligibility/observability gate. **Conflict verified:** SRS-001 TOOL-EXE-040 (timeout→fail) contradicts SDD-002 "timeout is a distinct outcome". Risk: schema-valid S1 docs can omit the decision inventory. |
| RV-03 | Data model & persistence review: recovered unit-test schema, build-capture schema, expected/actual + slots/histories structures vs the two-tree data model and restricted YAML store | `deep-specifications/master-schema.sql`, `deep-specifications/master-tables.json`, `vcapplib-recovered-schema.sql`, `vcapplib-sql-strings.json`, `VCAPPLIB.md`, `deep-specifications/SPECIFICATION_RECOVERY.md` (storage relationships, harness lifecycle) | SDD-003 (project tree vs output tree), ADR-002 (RestrictedYamlAdapter), `src/ectt/prj`, `src/ectt/ing/model.py`, `src/ectt/ana/model.py` + `persist.py` | **Complete** | [evidence-RV-03.md](2026-11-06-vcast-findings-evidence-RV-03.md) | 9 findings (4 aligned / 4 gap / 1 risk). ADR-002/SDD-003 two-tree design reinforced by recovered SQLite evidence. Gaps: compound/slots tests unrecorded, per-datum actuals missing for passing runs, build tags on ingested sets, first-class ranges/dimensions in type model. Risk: requirement-verdict aggregation anomaly (numerator 2 / denominator 1) unguarded in S5. |
| RV-04 | Coverage & MC/DC review: MC/DC variant semantics (masking vs unique-cause), optimized instrumentation storage/thresholds/limits, coverage I/O sinks and overflow behavior vs the coverage model and backend floors | `deep-specifications/COVERAGE_AND_IO.md`, `deep-20261027/DEEP_ANALYSIS.md` D4, `deep-20261027/PRODUCT_ARCHITECTURE.md` (§5), `deep-20261027/cover_models.html.txt`, `deep-specifications/text/Understanding MC DC Analysis.htm.txt` and sibling MC/DC text aids, `selected/IO/c_cover.h` | SDD-002 S4 (Coverage Model: MC/DC `form` as data, `unmeasured` ≠ `uncovered`, justified digests, independence pairs), SDD-005 §6.1 (GCC 14.1 `-fcondition-coverage`, Clang/LLVM 18.1 `-fcoverage-mcdc`), PLAN-001 COV WPs | **Complete** | [evidence-RV-04.md](2026-11-06-vcast-findings-evidence-RV-04.md) | 10 findings (4 aligned / 4 gap / 2 risk). S4 already holds MC/DC variant as data, rows-vs-pairs separation and provider-named metrics. Gaps: no `truncated` coverage-artifact state, MC/DC condition-limit probing absent from §6.3, no known-answer MC/DC corpus, macro-variant merge incompatibility unnamed. Risk: VectorCAST's own threshold doc self-contradicts on equality — backend-boundary fixtures needed. |
| RV-05 | Requirements & work-package mapping: P01–P15 and FR-01..FR-12 classified against SRS-001 requirements and the PLAN-001 register (covered by implemented WP / designed but unimplemented / absent) | `deep-specifications/PROTOTYPE_REQUIREMENTS.md` (P01–P15), `deep-20261027/PRODUCT_ARCHITECTURE.md` (§8 FR-01..FR-12, §9 validation strategy) | SRS-001 (`TOOL-*` requirements), PLAN-001 §5.5 register + §5.3 critical path, `docs/verification/` notes | **Complete** | [evidence-RV-05.md](2026-11-06-vcast-findings-evidence-RV-05.md) | 27 items classified: 3 fully covered by implemented WPs (P01, P03 discovery, FR-01 context half), 19 designed-but-unimplemented, 4 absent from SRS/PLAN (P02 LinkPlan, P06 stub-resolution proof, P09 exit(0)-gate, P15 validated pilot WP). Conflicts: test-revision model vs ectt stable-ids+digests; Windows-first pilot vs Linux-first SRS. |
| RV-06 | Gaps, risks & open decisions: 8 recovery gaps, 12 dispositioned review findings (Codex 1–6, Claude F1–F6), review-correctness notes vs open ADRs and the DR register | `deep-specifications/GAPS.md`, `deep-20261027/REVIEW_DECISIONS.md`, `deep-specifications/REVIEW_NOTES.md`, `deep-20261027/DEEP_ANALYSIS.md` ("What remains unknown") | Open ADR-003/004/005/007 topics, PLAN-001 §3.2 (F-16 `LIC-010` blocker), `docs/reviews/2026-10-15-document-review.md` (DR-01..32), ADR-001 risk register | **Complete** | [evidence-RV-06.md](2026-11-06-vcast-findings-evidence-RV-06.md) | 28 findings (17 aligned / 8 gap / 3 risk). Codex-5 (denominator), Codex-6 (reproducibility split) and Claude-F6 (libclang vs LibTooling) dispositions fully anticipated by SDD-002/ADR-001. Highest-value imports: run-integrity gaps (attempt-before-build, exit(0)-completion-marker, crashed-run coverage admission, artifact↔test-revision binding). Risk: licence blocker unresolved while repo hosts extracted proprietary assets. |

## 3. Evidence map — vcast-findings identifiers

Reusable identifiers found in the investigation, with their authoritative file locations. Agents cite these rather than re-describing sources.

| ID range | Meaning | Authoritative file |
|---|---|---|
| E1–E7 | Static architecture evidence (installer metadata, inventory, extraction integrity, PE imports, automation source, release notes, source identities) | `vcast-findings/ARCHITECTURE.md` §"Evidence and coverage" |
| D1–D13 | Deep-analysis evidence register (export/import inspections, harness S3.c, c_cover.h, Clang.py adapter, Data API/model docs, vunit headers, stub docs, VcAppLib) | `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` §"Evidence register" |
| Boundaries 1–7 | Recovered subsystem boundaries (build context, environment recipe, harness lifecycle, stubbing boundary, target coverage runtime, independent result identities, requirements-as-projections) | `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` §"Recovered subsystem boundaries" |
| FR-01..FR-12 | Proposed release requirements with acceptance evidence | `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §8 |
| P01–P15 | Proposed prototype requirements with acceptance checks | `vcast-findings/deep-specifications/PROTOTYPE_REQUIREMENTS.md` |
| Codex 1–6, Claude F1–F6 | Dispositioned findings from the 2026-10-27 independent reviews | `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` |
| Gaps (8 rows) | Remaining recovery gaps and next evidence needed | `vcast-findings/deep-specifications/GAPS.md` |
| Build-capture schema (27 tables) | VcAppLib `vcshell.db` recovered DDL (FILES/COMMANDS/COMPILATION/BUILDS/VCMETRICS/...) | `vcast-findings/vcapplib-recovered-schema.sql`, `VCAPPLIB.md` §"Database model recovered from the DLL" |
| Unit-test schema (26 tables) | Shipped `master.db` schema (types, functions, testcases, test_data, slots, slot_histories, events, actuals, requirements, ...) — all empty in the shipped copy | `vcast-findings/deep-specifications/master-schema.sql`, `master-tables.json` |

## 4. ectt baseline register (comparison targets)

| Artifact | Path | Status in repo |
|---|---|---|
| ADR-001 core decisions | `ADR-001-architecture-decisions.md` | Accepted 2026-09-19; corrected 2026-10-17 |
| ADR-002 project data format | `ADR-002-project-data-format.md` | Accepted 2026-09-26 |
| ADR-006 fork-or-build-fresh | `ADR-006-fork-or-build-fresh.md` | Accepted 2026-09-19 |
| ADR-008 AI decision provider | `ADR-008-ai-structured-decision-provider.md` | Accepted 2026-09-19 |
| SDD-001 architecture | `design/SDD-001-architecture.md` | 24 components, layer rule |
| SDD-002 interfaces | `design/SDD-002-interfaces.md` | Seams S1–S7 + TestValidationPort |
| SDD-003 data model | `design/SDD-003-data-model.md` | Two trees (authored vs output) |
| SDD-004 traceability | `design/SDD-004-traceability-architecture.md` | Trace meta-model + checker |
| SDD-005 external integration | `design/SDD-005-external-integration.md` | OSS catalogue + §6.1 floors |
| SRS-001 | `SRS-001-requirements.md` | 323 requirements, `TOOL-*` IDs |
| PLAN-001 | `PLAN-001-specification-analysis-and-work-breakdown.md` | Draft v0.2 (2026-10-17); 183 WPs |
| Implementation | `src/ectt/` (core, prj, ing, ana) | WP-CORE-01, PRJ-01, ING-01, ANA-01/02/04 committed |

## 5. Findings synthesis

**Total: 91 findings — 42 aligned · 32 gap · 7 conflict · 9 risk**, plus RV-05's 27-item requirement classification (3 covered by implemented WPs, 19 designed-but-unimplemented, 4 absent from SRS/PLAN). Every finding is cited on both sides in the per-task evidence files.

### A. What vcast-findings confirms

1. **SDD-001 decomposition validated by the incumbent's own static evidence.** VcAppLib is one shared 81-export boundary consumed identically by GUI, clicast and manage (RV-01 F-07); the seven recovered mechanisms map onto ectt's component families (F-11); the incumbent ships separate AI executables, corroborating CMP-AIF's quarantined design (F-16); its host-populated 10-slot callback bridge corroborates ectt's inverted composition-bound ports (F-09).
2. **Seam semantics independently converged.** TestSpec ≡ S2 (assigned ids, origin, requirement links); RunRecord ≡ S3 core (timeout distinct, `partial`/`not_executed` fields, `infrastructure_faults` channel, `order_seed`); CoverageSnapshot ≡ S4 (unmeasured ≠ uncovered, MC/DC form as data, rows-vs-pairs, provider-named metrics, short-circuit unevaluated states); AnalysisSnapshot ≡ S1 (failed TUs visible, no invented denominators) — RV-02 F-02/08/09/12, RV-04 F-01/02/08/09, RV-06 F-13/14/16/17.
3. **ADR-002/SDD-003 plain-text two-tree model is reinforced, not challenged, by the recovered SQLite evidence** (trigger-maintained FKs, unmergeable opaque DB, nullable/dual-typed identity cautions — all designed out by digest-bound records and fail-closed dispatch) — RV-03 F-02/07/09.
4. **Implemented WPs hold up:** WP-ING-01 covers P01 including distinct configurations (RV-05 F-09); WP-PRJ-01 already satisfies the storage half of FR-10/P14 (F-10); WP-ANA implements the same parser/build-compiler separation the shipped Clang.py adapter shows (RV-02 F-14).
5. **The LinkPlan concept is triple-validated** (UTBotCpp's `link_commands.json` harvest, VcAppLib's FILES/COMMANDS/COMPILATION schema, and the proposal's LinkPlan) — RV-01 F-12.

### B. Conflicts needing user decisions

| # | Topic | Proposal position | ectt accepted position | Ref |
|---|---|---|---|---|
| B1 | UI stack | React/TS local web UI + authenticated loopback API | PySide6/Qt; DSN-API-030 no TCP listener; browser UI rejected on security-policy/product-feel grounds | RV-01 F-02 |
| B2 | Evidence store | SQLite metadata + content-addressed blob store | ADR-002 restricted YAML + SDD-003 two trees | RV-01 F-03 |
| B3 | Host harness foundation | GoogleTest | TOOL-HAR-060 Unity/cmocka mandatory, HAR-065 GoogleTest optional host-only (the incumbent's own harness wires GoogleTest as optional too) | RV-01 F-04 |
| B4 | **Internal SRS contradiction (verified during this review)** | "timeout never a pass/fail" | SRS-001 TOOL-EXE-040 "report timed-out tests as failures" vs SDD-002 "`timeout` is a distinct outcome from `fail`" — SRS change request needed before WP-EXH acceptance | RV-02 F-11 |
| B5 | Identity model | TestRevision/EnvironmentRevision entities | ectt stable-id + digest staleness (SDD-003 §6/§7) — incompatible identity models; reconcile before WP-TCM-02 | RV-05 F-05 |
| B6 | Platform order | Windows-first validated toolchain + real pilot | SRS-001 is Linux-first (NFR-010 Must vs NFR-020 Should) | RV-05 F-06 |

B1–B3 are defaults-only conflicts already absorbed by the PAR-100 seam and the SDD-005 back-end catalogue — no ADR change is implied unless the user wants the proposal's defaults. B4–B6 need doc changes regardless of the proposal.

### C. Missing concepts (candidates for new requirements/WPs)

- **Identity chain — the largest structural blind spot:** LinkPlan manifest; CompiledTestManifest pre-run gate (reject mismatched exe↔test binding); RunAttempt allocated before build; EnvironmentRevision digest binding result → recipe → artifact → test revision. Allocate before WP-BLD-01/WP-EXH-01 acceptance — identity formats are the classic retrofit-too-late case. (RV-02 F-01/04/05/06/07/10/15; RV-05 F-01/03/04; RV-06 F-09/11/12)
- **Run-integrity four-pack (cheap, highest-value imports):** attempt-before-build record; exit(0)-without-finalized-record ≠ pass; crashed-run coverage admission rule; artifact↔test-revision pre-run binding. One-contract-point additions to WP-EXH-01/02, WP-CBT-01, WP-COV-02. (RV-06 F-11/12/18/19)
- **HostProfile / ABI-divergence record** for any target→host derivation; TOOL-TGT-070's "unmodified host/target" needs it to avoid an equivalence overclaim. (RV-02 F-04; RV-06 F-15)
- **Function-eligibility/observability gate** ("discovery must not imply eligibility"; no arbitrary static reads; report inaccessible state) — S1-adjacent data feeding CMP-ATG. (RV-02 F-13)
- **Coverage:** add a `truncated` state (complete|truncated|missing) for present-but-latched coverage artifacts; probe MC/DC condition limits in SDD-005 §6.3; mandate a known-answer MC/DC corpus before WP-COV-05; name macro/source-variant divergence as merge-incompatible. (RV-04 F-03/04/06/10)
- **Data model:** first-class ranges/dimensions in the ana type model (needed by bounded generation before WP-ATG); compound/slots test structures (explicit defer-with-migration-flag decision); per-datum actuals for passing runs; a per-requirement verdict dedup/denominator rule in SDD-002 §8. (RV-03 F-03/04/05/06/08)
- **Implementation lag behind published contracts:** response-file expansion + compiler-version/SDK/target identity in `ing`; make the decision inventory mandatory in the S1 schema so schema-valid documents cannot silently omit it. (RV-02 F-01/03)
- **Validation:** harness-vs-reference-test agreement check missing from WP-QUA-03. (RV-06 F-02)

### D. Recommended order of follow-up (all are doc/plan changes requiring your approval — none were made)

1. **Resolve ADR-005 (licence)** before further implementation: F-16/LIC-010 is still open, the repo LICENSE is AGPL-3.0, and `vcast-findings/` now hosts extracted proprietary VectorCAST assets — record the no-import rule and get a posture on public-repo exposure. Cheapest while the contributor set is small. (RV-06 F-27)
2. **SRS change request for TOOL-EXE-040** (timeout classification) and settle the revision-vs-stable-id identity model before WP-TCM-02. (RV-02 F-11; RV-05 F-05)
3. **Add the identity-chain contracts** (LinkPlan, CompiledTestManifest, RunAttempt, EnvironmentRevision digests) to SDD-002/SDD-003 with new SRS requirements before WP-BLD-01/WP-EXH-01. (RV-02 F-15; RV-05 F-01)
4. **Fold the run-integrity four-pack** and crashed-run coverage admission into WP-EXH-01/02, WP-CBT-01 and WP-COV-02 acceptance criteria. (RV-06 F-11/12/18/19)
5. **MC/DC capability probes, boundary-at-the-limit fixtures and a known-answer corpus** into SDD-005 §6.3/§6.4 and WP-COV-05/06 — vendor prose (including VectorCAST's own threshold page) demonstrably disagrees with itself off-by-one, and the failure direction is overclaim. (RV-04 F-04/05/10)
6. **Smaller guards:** per-requirement verdict/denominator rule in SDD-002 §8; harness-vs-reference check in WP-QUA-03; ranges/dimensions in the S1 schema before WP-ATG. (RV-03 F-08/F-06; RV-06 F-02)
7. **Hold ADR-001 UI/storage decisions**; the proposal's alternatives do not displace them. ADR-007's clean-machine endpoint test is the shared prerequisite for any packaging/UI-stack decision. (RV-01 F-02/03/17)

## 6. Review artifacts

| File | Purpose |
|---|---|
| `2026-11-06-vcast-findings-review-tracker.md` | This tracker (authoritative) |
| `2026-11-06-vcast-findings-review-tracker.html` | Standalone HTML rendering of the same data |
| `2026-11-06-vcast-findings-evidence-RV-01.md` … `RV-06.md` | Per-task evidence files written by the review agents |
| [`2026-11-07-subsystem-requirements-and-tasks.md`](2026-11-07-subsystem-requirements-and-tasks.md) + [`.html` tracker](2026-11-07-subsystem-task-tracker.html) | Follow-up (2026-11-07): full subsystem inventory (185 WPs · 634 pw · 328 SRS IDs) with the review-derived NR/T items folded in per subsystem |
| [`diagrams/proposed-architecture.archify.json`](diagrams/proposed-architecture.archify.json) + [`.html`](diagrams/proposed-architecture.html) | Archify architecture diagram of the proposal's §2 stack (12 nodes; delivered 2026-11-07, showcase validation 9/9 pass, SHA-256 `c9ea1c31…` for the artifact, `d136536b…` for the frozen specification). Topology: CLI/UI→API→application workflows→supervisor→(analysis→generate→build→execute→coverage)→evidence store→reports |

`vcast-findings/` was treated as read-only evidence for this review; helper scripts inside it (`extract_members.py`, `inspect_pe.py`) were not executed.
