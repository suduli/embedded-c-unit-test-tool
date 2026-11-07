# Subsystem requirements & tasks — full inventory (features, WPs, SRS requirements)

- **Date:** 2026-11-07 · **Supersedes:** the review-delta-only version of this file
- **Inventory source:** PLAN-001 §5.5 register (188 work packages · 638 person-weeks) and SRS-001 (337 unique requirement IDs: 335 allocated + 2 future; the former "323" prose is retired — see T-03 evidence), parsed at HEAD `b5786e0`
- **Review deltas:** 29 proposed requirements (NR-01..29) and 22 tasks (T-01..22) from the [vcast-findings review](2026-11-06-vcast-findings-review-tracker.md) (evidence files RV-01..06)
- **Status:** T-03 **landed 2026-11-07** — SRS-001 correction note applied (EXE-040, PLG-080/PLG-100, COV-150, AIF-260), design register extended (DSN-PLG-050, DSN-AIF-140/150), PLAN-001 derived tables regenerated; **both gates green** (plan_check exit 0: 329 requirements / 327 allocations / 188 packages; trace_check exit 0: 327/327 allocated). All other items remain proposals — landing them requires the change process and approval
- **Implemented at HEAD:** WP-CORE-01, WP-PRJ-01, WP-ING-01, WP-ANA-01, WP-ANA-02, WP-ANA-04 (+ spikes WP-SPIKE-01..03 recorded in ADR-001)
- **Companion:** [HTML tracker](2026-11-07-subsystem-task-tracker.html) (filterable) · [subsystem work map](diagrams/subsystem-workmap.html) · [§ Repository hosting](#9-repository-hosting-decision)

## L0 — Platform & Persistence

13 work packages · 38 person-weeks · 33 SRS requirements allocated · 2 implemented · 1 review-derived requirements · 1 review tasks

### CMP-CORE — 8 WPs · 23 pw · 22 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-CORE-01` | Determinism, source immutability and output confinement | P1 | 3w | NFR-060 NFR-070 NFR-080 PRJ-050 PRJ-080 | **Complete** |
| `WP-CORE-02` | Structured error model, fail-safe termination and cancellation | P1 | 3w | NFR-090 NFR-180 | Planned |
| `WP-CORE-03` | Platform baseline and offline guarantee | P1 | 2w | NFR-010 NFR-020 NFR-100 | Planned |
| `WP-CORE-04` | Provenance record and version identification | P2 | 2w | QUA-060 INS-110 | Planned |
| `WP-CORE-05` | Performance, scale and memory envelope | P2 | 4w | NFR-030 NFR-040 NFR-050 NFR-150 | Planned |
| `WP-CORE-06` | Logging and diagnostic bundle | P2 | 2w | NFR-130 NFR-160 | Planned |
| `WP-CORE-07` | User documentation and text externalisation | P2 | 4w | NFR-120 NFR-190 | Planned |
| `WP-CORE-08` | Self-verification of the tool's own source | P2 | 3w | NFR-140 NFR-170 | Planned |

### CMP-PRJ — 5 WPs · 15 pw · 11 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-PRJ-01` | Plain-text schema-versioned project store | P1 | 4w | PRJ-010 PRJ-020 PRJ-070 UIX-320 CIC-080 | **Complete** |
| `WP-PRJ-02` | Diff-stable sharded storage for concurrent edit | P2 | 3w | PRJ-030 PRJ-060 | Planned |
| `WP-PRJ-03` | Schema migration with explicit confirmation | P2 | 3w | PRJ-040 | Planned |
| `WP-PRJ-04` | Dangling reference detection | P3 | 1w | PRJ-090 | Planned |
| `WP-PRJ-05` | Archival export and reproduction verification | P4 | 4w | PRJ-100 PRJ-110 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-06 | NFR thresholds calibrated from measured baselines before WP-CORE-05 exits P2 | DR-06, NFR-030..150 | RV-06 F-07/F-24 | P2 |

### Review-derived tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-06 | DR-06 NFR calibration plan + fixtures; provisional NFRs marked | NR-06 | RV-06 F-07/F-24 | P2 | Not Started | — |

## L1 — Comprehension

23 work packages · 72 person-weeks · 51 SRS requirements allocated · 4 implemented · 8 review-derived requirements · 6 review tasks

### CMP-ING — 7 WPs · 21 pw · 22 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-ING-01` | Compilation database ingestion | P1 | 3w | ING-010 ING-020 ING-030 ING-040 | **Complete** |
| `WP-ING-02` | Alternative ingestion paths | P2 | 3w | ING-050 ING-060 ING-080 ING-210 | Planned |
| `WP-ING-03` | Ingestion diagnostics, persistence and staleness | P2 | 3w | ING-070 ING-090 ING-100 ING-220 | Planned |
| `WP-ING-04` | Test scope model and resolution | P2 | 5w | ING-120 ING-130 ING-140 ING-150 ING-190 | Planned |
| `WP-ING-05` | Scope conflict detection and external dependency reporting | P2 | 3w | ING-160 ING-170 ING-180 | Planned |
| `WP-ING-06` | Multi-toolchain ingestion | P3 | 2w | ING-110 | Planned |
| `WP-ING-07` | Authored link plan ingestion and validation | P2 | 2w | ING-200 | Planned |

### CMP-ANA — 9 WPs · 29 pw · 17 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-ANA-01` | C front-end binding and dialect support | P1 | 4w | PAR-010 PAR-020 | **Complete** |
| `WP-ANA-02` | Interface and type extraction | P1 | 5w | PAR-030 PAR-040 PAR-050 | **Complete** |
| `WP-ANA-03` | Call graph and scope classification | P2 | 3w | PAR-060 | Planned |
| `WP-ANA-04` | Analysis model persistence and schema versioning | P1 | 3w | PAR-100 PAR-110 | **Complete** |
| `WP-ANA-05` | Control flow graph capability | P2 | 6w | PAR-070 PAR-120 | Planned |
| `WP-ANA-06` | Static function testability and macro resolution | P2 | 4w | PAR-080 PAR-090 PAR-170 | Planned |
| `WP-ANA-07` | Partial-failure resilience | P2 | 2w | PAR-130 PAR-140 | Planned |
| `WP-ANA-08` | Analysis model decision inventory | P2 | 1w | PAR-150 | Planned |
| `WP-ANA-09` | Value ranges and dimension metadata in the analysis model | P2 | 1w | PAR-160 | Planned |

### CMP-TCH — 7 WPs · 22 pw · 12 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-TCH-01` | Declarative compiler configuration format | P1 | 3w | TCH-020 PLG-020 | Planned |
| `WP-TCH-02` | Host compiler support: GCC and Clang | P1 | 2w | TCH-010 | Planned |
| `WP-TCH-03` | Cross-toolchain support and shipped configurations | P3 | 5w | TCH-030 TCH-040 TCH-050 | Planned |
| `WP-TCH-04` | Capability declaration and compiler version gating | P3 | 3w | TCH-060 TCH-070 | Planned |
| `WP-TCH-05` | Multi-toolchain builds and reproducible containers | P3 | 3w | TCH-080 TCH-090 | Planned |
| `WP-TCH-06` | Proprietary compiler support | P3 | 4w | TCH-100 | Planned |
| `WP-TCH-07` | First-run environment verification | P2 | 2w | INS-080 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-07 | Ingested context captures response files (expanded), compiler/SDK/sysroot/target identity — landed 2026-11-07 as TOOL-ING-210/220 | TOOL-ING-210, TOOL-ING-220 | RV-02 F-01 | P1 |
| NR-08 | Explicit build identity/tag per ingested configuration set — landed 2026-11-07 (CompilationDatabase.build_tag) | TOOL-ING-220 | RV-03 F-05 | P1 |
| NR-09 | Stale ingest forces re-analysis; shadowing-header/__has_include invalidation — landed 2026-11-07 (fail-closed staleness.py, no warn path) | TOOL-ING-100 | RV-06 F-10 | P1 |
| NR-10 | S1 schema mandates the decision inventory — landed 2026-11-07 (schema 1.1 + reader gate, fail-closed status) | TOOL-PAR-150, DSN-ANA-110 | RV-02 F-03 | P1 |
| NR-11 | Unsupported constructs as first-class S1 inventory data — landed 2026-11-07 (per-unit required array, TOOL-PAR-140) | TOOL-PAR-140, DSN-ANA-100 | RV-05 F-08 | P1 |
| NR-12 | Ranges/dimensions first-class in the type model — landed 2026-11-07 (TOOL-PAR-160, schema 1.2, DSN-ANA-120) | TOOL-PAR-160, DSN-ANA-120 | RV-03 F-06 | P1 |
| NR-13 | Eligibility/observability gate: discovery does not imply eligibility | PAR-080/090, HAR-030 | RV-02 F-13 | P1 |
| NR-14 | Authored LinkPlan required before build; unresolved input blocks — landed 2026-11-07 as TOOL-ING-200 (WP-ING-07, DSN-ING-120) | TOOL-ING-200, DSN-ING-120 | RV-02 F-05 | P0 |

### Review-derived tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-07 | Extend ing: response-file expansion, build-context identity, build tags (TOOL-ING-210/220, DSN-ING-130/140) | NR-07, NR-08 | RV-02 F-01, RV-03 F-05 | P1 | **Complete** | — |
| T-08 | ING-100 fail-closed staleness: content fingerprints (compdb, sources, response files, include surface) + invalidation fixtures | NR-09 | RV-06 F-10 | P1 | **Complete** | — |
| T-09 | S1 schema 1.1: mandatory decision + unsupported inventories, reader gates fail closed | NR-10, NR-11 | RV-02 F-03, RV-05 F-08 | P1 | **Complete** | — |
| T-10 | Value ranges + array dimension metadata in ana model and schema 1.2 (round-trip + conformance tests) | NR-12 | RV-03 F-06 | P1 | **Complete** | — |
| T-11 | Eligibility/observability gate: assess_eligibility over the S1 model (channels, named reasons), consumed by CMP-ATG | NR-13 | RV-02 F-13 | P1 | **Complete** | — |
| T-12 | LinkPlan: TOOL-ING-200 + WP-ING-07 + DSN-ING-120 + SDD-002/SDD-003 amendments | NR-14 | RV-02 F-05 | P0 | **Complete** | — |

## L2 — Synthesis

23 work packages · 92 person-weeks · 54 SRS requirements allocated · 0 implemented · 2 review-derived requirements · 1 review tasks

### CMP-GEN — 11 WPs · 43 pw · 29 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-GEN-01` | Harness generation core | P1 | 5w | HAR-010 HAR-020 HAR-040 HAR-050 | Planned |
| `WP-GEN-02` | Framework back-ends: Unity and cmocka | P2 | 4w | HAR-060 HAR-070 PLG-030 | Planned |
| `WP-GEN-03` | Static exposure and integration-scope harness | P2 | 4w | HAR-030 HAR-080 | Planned |
| `WP-GEN-04` | Regeneration contract and conflict reporting | P2 | 5w | HAR-090 HAR-100 HAR-110 CBT-070 | Planned |
| `WP-GEN-05` | Link closure and unresolved reference reporting | P2 | 2w | HAR-120 | Planned |
| `WP-GEN-06` | Stub generation core | P2 | 4w | STB-010 STB-020 STB-030 | Planned |
| `WP-GEN-07` | Stub behaviour programming | P2 | 5w | STB-040 STB-050 STB-060 STB-070 | Planned |
| `WP-GEN-08` | Stub scope control and indirect-call stubbing | P2 | 4w | STB-080 STB-100 STB-140 | Planned |
| `WP-GEN-09` | Stub regeneration and unsupported-construct flagging | P2 | 4w | STB-110 STB-120 STB-130 | Planned |
| `WP-GEN-10` | GoogleTest back-end (host only) | P3 | 3w | HAR-065 | Planned |
| `WP-GEN-11` | Call wrapping of intra-unit calls | P3 | 3w | STB-090 | Planned |

### CMP-TCM — 7 WPs · 25 pw · 14 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-TCM-01` | Test cases authored in C | P1 | 2w | TCD-010 | Planned |
| `WP-TCM-02` | Data-driven test case model and on-disk format | P2 | 5w | TCD-020 TCD-030 TCD-040 TCD-140 | Planned |
| `WP-TCM-03` | Expected-value comparison engine | P2 | 4w | TCD-050 TCD-060 | Planned |
| `WP-TCM-04` | Suites, selective execution and test independence | P2 | 3w | TCD-080 TCD-090 | Planned |
| `WP-TCM-05` | Ranged and robustness input generation | P2 | 3w | TCD-070 TCD-130 | Planned |
| `WP-TCM-06` | Test case interchange import and export | P2 | 3w | TCD-100 | Planned |
| `WP-TCM-07` | Boundary, equivalence and classification-tree derivation | P3 | 5w | TCD-110 TCD-120 | Planned |

### CMP-ATG — 5 WPs · 24 pw · 11 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-ATG-01` | Validation port and generated-case lifecycle | P3 | 4w | ATG-040 ATG-050 ATG-070 ATG-080 | Planned |
| `WP-ATG-02` | Symbolic execution engine adapter | P3 | 8w | ATG-010 ATG-020 | Planned |
| `WP-ATG-03` | Bounded model checking engine | P3 | 5w | ATG-030 | Planned |
| `WP-ATG-04` | Targeted generation against uncovered constructs | P3 | 4w | ATG-090 | Planned |
| `WP-ATG-05` | Generation reporting, bounds and capability limits | P3 | 3w | ATG-060 ATG-100 ATG-110 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-15 | Compound/iterative tests explicitly deferred with a migration flag — landed 2026-11-07 (TOOL-MIG-110, DSN-MIG-090) | TOOL-MIG-110, DSN-MIG-090 | RV-03 F-03 | P1 |
| NR-16 | Test identity per NR-04 implemented in TCM (assigned ids + digest binding) | SDD-003 §6/§7 | RV-05 F-05 | P0 |

### Review-derived tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-13 | Compound-test defer decision + migration flag | NR-15 | RV-03 F-03 | P1 | Not Started | — |

## L3 — Realization

14 work packages · 51 person-weeks · 22 SRS requirements allocated · 0 implemented · 4 review-derived requirements · 2 review tasks

### CMP-BLD — 3 WPs · 9 pw · 3 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-BLD-01` | Host build orchestration and incremental rebuild | P1 | 4w | EXE-080 | Planned |
| `WP-BLD-02` | Sanitizer integration | P2 | 2w | EXE-090 | Planned |
| `WP-BLD-03` | Cross-compiled target build | P3 | 3w | TGT-010 | Planned |

### CMP-EXH — 4 WPs · 13 pw · 7 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-EXH-01` | Host execution and per-test result reporting | P1 | 4w | EXE-010 EXE-020 | Planned |
| `WP-EXH-02` | Crash isolation, timeout and process exit status | P1 | 3w | EXE-030 EXE-040 EXE-060 | Planned |
| `WP-EXH-03` | Parallel test execution | P1 | 2w | EXE-050 | Planned |
| `WP-EXH-04` | Debugger launch with entry breakpoint | P2 | 4w | EXE-070 | Planned |

### CMP-EXT — 7 WPs · 29 pw · 12 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-EXT-01` | Simulator execution: QEMU and Renode | P3 | 5w | TGT-020 | Planned |
| `WP-EXT-02` | Hardware execution and flashing via debug probe | P3 | 6w | TGT-030 TGT-040 | Planned |
| `WP-EXT-03` | Target result retrieval channels and protocol | P3 | 4w | TGT-050 TGT-060 | Planned |
| `WP-EXT-04` | Host and target test parity | P3 | 3w | TGT-070 | Planned |
| `WP-EXT-05` | Hardware inventory and target failure classification | P3 | 4w | TGT-080 TGT-090 | Planned |
| `WP-EXT-06` | Suite splitting and on-target footprint documentation | P3 | 4w | TGT-100 TGT-110 | Planned |
| `WP-EXT-07` | User-supplied target execution methods | P3 | 3w | TGT-120 PLG-040 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-17 | RunAttempt allocated before build; build failure is a first-class attempt record | S3, WP-CORE-04 | RV-06 F-12 | P1 |
| NR-18 | Pass requires finalized per-attempt result record; exit(0) alone is abnormal | S3, TOOL-EXE-030/060 | RV-06 F-19 | P1 |
| NR-19 | Exact artifact↔test-revision binding checked before every run | HAR-090/110, CBT-070 | RV-06 F-11 | P1 |
| NR-20 | HostProfile records target→host derivations and ABI gaps | TOOL-TGT-070 | RV-02 F-04 | P2 |

### Review-derived tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-14 | Run-integrity acceptance into WP-EXH-01/02 + WP-CBT-01 | NR-17..19 | RV-06 F-11/12/19 | P1 | Not Started | T-04 |
| T-15 | HostProfile/ABI-divergence record section | NR-20 | RV-02 F-04 | P2 | Not Started | — |

## L4 — Evidence

32 work packages · 115 person-weeks · 52 SRS requirements allocated · 0 implemented · 6 review-derived requirements · 5 review tasks

### CMP-COV — 11 WPs · 43 pw · 17 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-COV-01` | Statement and branch coverage from compiler backend | P1 | 4w | COV-010 COV-020 | Planned |
| `WP-COV-02` | Coverage merge and per-test attribution | P1 | 4w | COV-110 COV-120 | Planned |
| `WP-COV-03` | Coverage threshold enforcement | P1 | 1w | COV-130 | Planned |
| `WP-COV-04` | Function and function-call coverage | P3 | 2w | COV-030 COV-040 | Planned |
| `WP-COV-05` | MC/DC measurement and form declaration | P3 | 6w | COV-050 COV-060 COV-070 | Planned |
| `WP-COV-06` | Uninstrumentable expression detection | P3 | 3w | COV-080 | Planned |
| `WP-COV-07` | Bare-metal coverage retrieval | P3 | 5w | COV-100 | Planned |
| `WP-COV-08` | Unit-under-test versus harness coverage separation | P3 | 2w | COV-160 | Planned |
| `WP-COV-09` | Coverage-by-analysis justification with digest binding | P4 | 4w | COV-140 COV-150 | Planned |
| `WP-COV-10` | Unique-cause MC/DC support or documented gap | P4 | 6w | COV-090 | Planned |
| `WP-COV-11` | Control coupling and data coupling analysis | P4 | 6w | COV-170 | Planned |

### CMP-REP — 12 WPs · 41 pw · 18 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-REP-01` | Single intermediate report model | P1 | 4w | REP-090 REP-100 | Planned |
| `WP-REP-02` | Machine-readable outputs: JUnit and Cobertura/LCOV | P1 | 3w | REP-010 REP-020 | Planned |
| `WP-REP-03` | HTML report with annotated source | P1 | 4w | REP-030 REP-040 | Planned |
| `WP-REP-04` | MC/DC condition detail rendering | P3 | 3w | REP-050 | Planned |
| `WP-REP-05` | Certification verification report and scope statement | P4 | 5w | REP-060 REP-140 | Planned |
| `WP-REP-06` | Report provenance and format version stability | P4 | 3w | REP-070 REP-130 | Planned |
| `WP-REP-07` | Paginated PDF archival rendering | P4 | 4w | REP-080 | Planned |
| `WP-REP-08` | Cross-unit summary and coverage trend | P3 | 4w | REP-110 REP-120 | Planned |
| `WP-REP-09` | Report generation from archived result data | P4 | 3w | REP-150 | Planned |
| `WP-REP-10` | Coverage interchange import and export | P4 | 3w | MIG-080 | Planned |
| `WP-REP-11` | Report format extension point | P3 | 2w | PLG-050 | Planned |
| `WP-REP-12` | Reconstructable open result export with test-case coordination | P2 | 3w | MIG-060 | Planned |

### CMP-TRC — 5 WPs · 18 pw · 10 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-TRC-01` | Requirement association and bidirectional matrix | P4 | 4w | TRC-010 TRC-020 TRC-030 | Planned |
| `WP-TRC-02` | Unlinked requirement and unlinked test reporting | P4 | 2w | TRC-040 | Planned |
| `WP-TRC-03` | Requirement import from ReqIF, CSV and plain text | P4 | 4w | TRC-050 TRC-060 | Planned |
| `WP-TRC-04` | ReqIF export and external traceability tool interop | P4 | 4w | TRC-070 TRC-100 | Planned |
| `WP-TRC-05` | Source-element linking and requirement change detection | P4 | 4w | TRC-080 TRC-090 | Planned |

### CMP-CBT — 4 WPs · 13 pw · 7 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-CBT-01` | Suite re-execution without regeneration | P2 | 2w | CBT-010 | Planned |
| `WP-CBT-02` | Change impact analysis and subset execution | P3 | 5w | CBT-020 CBT-030 CBT-040 | Planned |
| `WP-CBT-03` | Run comparison and coverage delta | P3 | 3w | CBT-050 CBT-060 | Planned |
| `WP-CBT-04` | Test suite minimization | P3 | 3w | CBT-080 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-21 | Coverage completeness state complete|truncated|missing; truncated → unmeasured + advisory | S3/S4, S5 | RV-04 F-06 | P1 |
| NR-22 | MC/DC condition-limit probing per backend + boundary fixtures | SDD-005 §6.3/§6.4 | RV-04 F-04/F-05 | P1 |
| NR-23 | Known-answer MC/DC corpus mandated before WP-COV-05 | PLAN §6.4 | RV-04 F-10 | P1 |
| NR-24 | Macro/source-variant divergence merge-incompatible | S4 merge rules | RV-04 F-03 | P1 |
| NR-25 | Crashed-run coverage quarantined unless validated | WP-COV-02 | RV-06 F-18 | P1 |
| NR-26 | Per-requirement verdicts deduplicated, worst outcome, labeled denominators | SDD-002 §8 | RV-03 F-08 | P1 |

### Review-derived tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-16 | Coverage completeness state in S3/S4 + S5 advisory (+NR-27 surfacing) | NR-21, NR-27 | RV-04 F-06 | P1 | Not Started | — |
| T-17 | MC/DC limit probing + boundary fixtures + macro-variant merge rule | NR-22, NR-24 | RV-04 F-03..05 | P1 | Not Started | — |
| T-18 | Known-answer MC/DC corpus mandate | NR-23 | RV-04 F-10 | P1 | Not Started | — |
| T-19 | Verdict dedup + labeled denominators + 2/1 anomaly fixture | NR-26 | RV-03 F-08 | P1 | Not Started | — |
| T-20 | Crashed-run coverage admission rule | NR-25 | RV-06 F-18 | P1 | Not Started | — |

## L5 — Interfaces

30 work packages · 106 person-weeks · 45 SRS requirements allocated · 0 implemented · 1 review-derived requirements · 0 review tasks

### CMP-API — 3 WPs · 9 pw · 5 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-API-01` | Engine API protocol, operation catalogue and versioning | P1 | 4w | UIX-010 UIX-020 PLG-060 | Planned |
| `WP-API-02` | Local-only transport with no network listener | P2 | 2w | UIX-050 | Planned |
| `WP-API-03` | CLI and GUI round-trip equivalence | P2 | 3w | UIX-330 | Planned |

### CMP-CLI — 5 WPs · 12 pw · 7 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-CLI-01` | Non-interactive CLI generated from the operation catalogue | P1 | 3w | CIC-010 CIC-020 | Planned |
| `WP-CLI-02` | Stable documented exit codes | P1 | 1w | CIC-030 | Planned |
| `WP-CLI-03` | Container execution | P1 | 2w | CIC-040 | Planned |
| `WP-CLI-04` | Reference CI pipelines and artifact caching | P2 | 3w | CIC-050 CIC-070 | Planned |
| `WP-CLI-05` | CI sharding and report merge | P3 | 3w | CIC-060 | Planned |

### CMP-GUI — 22 WPs · 85 pw · 33 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-GUI-01` | Application shell, installability and platform support | P2 | 6w | UIX-030 UIX-040 UIX-340 UIX-350 | Planned |
| `WP-GUI-02` | Project and environment management workflow | P2 | 5w | UIX-060 UIX-070 UIX-100 | Planned |
| `WP-GUI-03` | Integration scope creation and dependency preview | P2 | 3w | UIX-080 | Planned |
| `WP-GUI-04` | Build progress and navigable compiler diagnostics | P2 | 3w | UIX-090 | Planned |
| `WP-GUI-05` | Navigation tree, status aggregation, filter and search | P2 | 5w | UIX-110 UIX-120 UIX-130 UIX-140 | Planned |
| `WP-GUI-06` | Execution control and per-test result presentation | P2 | 4w | UIX-210 UIX-220 | Planned |
| `WP-GUI-07` | Console pane reproducing engine commands | P2 | 2w | UIX-240 | Planned |
| `WP-GUI-08` | Coverage summary, annotation and basic HTML report launch | P2 | 4w | UIX-250 UIX-280 | Planned |
| `WP-GUI-09` | Actionable error messaging | P2 | 2w | UIX-360 | Planned |
| `WP-GUI-10` | Tabular data-driven test case editor | P2 | 5w | UIX-150 | Planned |
| `WP-GUI-11` | Nested type-aware value editor | P2 | 8w | UIX-160 UIX-170 | Planned |
| `WP-GUI-12` | Stub configuration view | P3 | 4w | UIX-180 | Planned |
| `WP-GUI-13` | Ranged and boundary input authoring | P3 | 3w | UIX-190 | Planned |
| `WP-GUI-14` | C source test editor with syntax highlighting | P3 | 3w | UIX-200 | Planned |
| `WP-GUI-15` | Debugger launch from the application | P3 | 4w | UIX-230 | Planned |
| `WP-GUI-16` | MC/DC per-condition detail view | P3 | 3w | UIX-260 | Planned |
| `WP-GUI-17` | Graphical control flow view with coverage overlay | P3 | 5w | UIX-270 | Planned |
| `WP-GUI-18` | Non-blocking interface during long operations | P3 | 4w | UIX-370 | Planned |
| `WP-GUI-19` | Coverage-by-analysis justification capture | P4 | 3w | UIX-290 | Planned |
| `WP-GUI-20` | In-application report generation and viewing | P4 | 3w | UIX-300 | Planned |
| `WP-GUI-21` | Traceability matrix view with navigation | P4 | 3w | UIX-310 | Planned |
| `WP-GUI-22` | Keyboard-driven workflow | P4 | 3w | UIX-380 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-27 | CLI/GUI surface completeness states and verdict provenance without relabeling | TOOL-UIX-010..390 | RV-04 F-06 | P2 |

## L6 — Assurance & Ecosystem

53 work packages · 164 person-weeks · 78 SRS requirements allocated · 0 implemented · 2 review-derived requirements · 2 review tasks

### CMP-AIF — 16 WPs · 51 pw · 26 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-AIF-01` | Provider abstraction and local model runtime | P3 | 5w | AIF-020 AIF-050 | Planned |
| `WP-AIF-02` | Optionality, separability and default-off | P3 | 2w | AIF-010 | Planned |
| `WP-AIF-03` | Data egress control and pre-use disclosure | P3 | 3w | AIF-030 AIF-040 | Planned |
| `WP-AIF-04` | Generated artifact validation and rejection recording | P3 | 4w | AIF-070 AIF-210 | Planned |
| `WP-AIF-05` | Append-only AI provenance, replay constraints and review state | P3 | 5w | AIF-080 AIF-090 AIF-160 AIF-180 AIF-190 | Planned |
| `WP-AIF-06` | Time and token bounds on AI operations | P3 | 2w | AIF-150 | Planned |
| `WP-AIF-07` | Local model integrity and hardware requirements | P3 | 3w | AIF-170 AIF-200 | Planned |
| `WP-AIF-08` | AI-assisted test case generation | P3 | 4w | AIF-060 | Planned |
| `WP-AIF-09` | AI-assisted stub body generation | P3 | 3w | AIF-110 | Planned |
| `WP-AIF-10` | AI-assisted test failure explanation | P3 | 3w | AIF-120 | Planned |
| `WP-AIF-11` | AI-assisted naming and documentation | P3 | 2w | AIF-140 | Planned |
| `WP-AIF-12` | Certification evidence review and exclusion mode | P4 | 2w | AIF-100 | Planned |
| `WP-AIF-13` | AI-proposed requirement-to-test links | P4 | 3w | AIF-130 | Planned |
| `WP-AIF-14` | Typed decision evaluation, validation and provider role separation | P3 | 4w | AIF-220 AIF-230 | Planned |
| `WP-AIF-15` | Local/enterprise substitution and all-role extension conformance | P3 | 4w | AIF-250 AIF-260 | Planned |
| `WP-AIF-16` | Configurable remote structured-decision default profile | P4 | 2w | AIF-240 | Planned |

### CMP-MIG — 7 WPs · 26 pw · 9 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-MIG-01` | Execution of existing Unity and cmocka suites | P2 | 4w | MIG-010 | Planned |
| `WP-MIG-02` | Ceedling project import | P2 | 4w | MIG-020 | Planned |
| `WP-MIG-03` | Interchange format documentation | P2 | 2w | MIG-100 | Planned |
| `WP-MIG-04` | Commercial tool and CSV test data import | P3 | 6w | MIG-030 MIG-050 | Planned |
| `WP-MIG-05` | Import fidelity reporting | P3 | 3w | MIG-040 MIG-110 | Planned |
| `WP-MIG-06` | Coexistence with another tool on one project | P3 | 3w | MIG-070 | Planned |
| `WP-MIG-07` | Migration assessment mode | P4 | 4w | MIG-090 | Planned |

### CMP-PKG — 9 WPs · 25 pw · 18 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-PKG-01` | Offline, non-admin, runtime-free installation | P2 | 6w | INS-010 INS-020 INS-030 | Planned |
| `WP-PKG-02` | Self-contained archivable release identity | P2 | 3w | INS-040 QUA-050 | Planned |
| `WP-PKG-03` | Side-by-side versions and confirmed upgrade | P2 | 4w | INS-050 INS-060 | Planned |
| `WP-PKG-04` | Documented uninstallation | P2 | 1w | INS-070 | Planned |
| `WP-PKG-05` | Versioned CI container image | P2 | 2w | INS-090 | Planned |
| `WP-PKG-06` | Shared read-only multi-user installation | P3 | 3w | INS-100 | Planned |
| `WP-PKG-07` | License policy, process isolation and automated enforcement | P1 | 3w | LIC-010 LIC-020 LIC-030 LIC-040 LIC-050 LIC-060 | Planned |
| `WP-PKG-08` | Separable restrictively-licensed optional components | P3 | 2w | LIC-070 | Planned |
| `WP-PKG-09` | Installation without administrative privileges | P2 | 1w | NFR-110 | Planned |

### CMP-PLG — 4 WPs · 12 pw · 5 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-PLG-01` | Extension point definition and versioning | P1 | 3w | PLG-010 | Planned |
| `WP-PLG-02` | Extension discovery and load failure isolation | P3 | 3w | PLG-070 PLG-080 | Planned |
| `WP-PLG-03` | Built-ins implemented through public extension points | P3 | 3w | PLG-090 | Planned |
| `WP-PLG-04` | AI provider extension protocol, registration and capability negotiation | P2 | 3w | PLG-100 | Planned |

### CMP-QUA — 8 WPs · 26 pw · 8 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-QUA-01` | Tool classification analysis and confidence level | P4 | 3w | QUA-010 | Planned |
| `WP-QUA-02` | Tool operational requirements specification | P2 | 4w | QUA-020 | Planned |
| `WP-QUA-03` | User-executable validation suite | P2 | 6w | QUA-030 | Planned |
| `WP-QUA-04` | Known error list maintained per release | P2 | 2w | QUA-040 | Planned |
| `WP-QUA-05` | Development process and change control documentation | P4 | 3w | QUA-070 | Planned |
| `WP-QUA-06` | Standards objective mapping | P4 | 4w | QUA-080 | Planned |
| `WP-QUA-07` | Explicit statement of what is and is not qualified | P2 | 1w | QUA-090 | Planned |
| `WP-QUA-08` | Templates for user tool qualification artifacts | P4 | 3w | QUA-100 | Planned |

### CMP-SEC — 9 WPs · 24 pw · 12 requirements allocated
| WP | Capability delivered | Phase | Effort | Requirements | Status |
|---|---|:--:|--:|---|---|
| `WP-SEC-01` | Release signing and Software Bill of Materials | P2 | 3w | SEC-010 SEC-020 | Planned |
| `WP-SEC-02` | Reproducible build and pinned dependency integrity | P2 | 4w | SEC-030 SEC-040 | Planned |
| `WP-SEC-03` | Untrusted-project warning and configuration-is-data | P2 | 3w | SEC-050 SEC-070 | Planned |
| `WP-SEC-04` | Log and diagnostic content control | P2 | 2w | SEC-120 | Planned |
| `WP-SEC-05` | Security disclosure process and supported-version policy | P2 | 1w | SEC-080 | Planned |
| `WP-SEC-06` | Restricted execution context for harnesses | P3 | 4w | SEC-060 | Planned |
| `WP-SEC-07` | Target-supplied data treated as untrusted | P3 | 2w | SEC-090 | Planned |
| `WP-SEC-08` | Credential storage via platform secure storage | P3 | 3w | SEC-110 | Planned |
| `WP-SEC-09` | Dependency vulnerability scanning in CI | P3 | 2w | SEC-100 | Planned |

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-28 | Generated-harness results agree with independently written reference tests | WP-QUA-03 | RV-06 F-02 | P2 |
| NR-29 | Packaging gated on clean-machine endpoint acceptance (ADR-007) | WP-PKG-07 | RV-01 F-17 | P2 |

### Review-derived tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-21 | Harness-vs-reference agreement check in WP-QUA-03 | NR-28 | RV-06 F-02 | P2 | Not Started | — |
| T-22 | Clean-machine endpoint gate in WP-PKG (ADR-007) | NR-29 | RV-01 F-17 | P2 | Not Started | — |

## Governance & cross-cutting decisions (gates everything)

### Review-derived requirements

| ID | Requirement (proposed) | Baseline | Source | Priority |
|---|---|---|---|:--:|
| NR-01 | Licence posture resolved: LIC-010 satisfied (ADR-005) before further implementation | LIC-010, F-16 | RV-06 F-27 | P0 |
| NR-02 | No-import rule: no VectorCAST-extracted asset enters ectt source/distribution | ADR-005 consequence | RV-06 F-27 | P0 |
| NR-03 | Timeout is a distinct outcome, never a failure (amends TOOL-EXE-040) | TOOL-EXE-040 | RV-02 F-11 | P0 |
| NR-04 | One identity model decided: stable ids + digests vs revision entities | SDD-003 §6/§7 | RV-05 F-05 | P0 |
| NR-05 | Platform order decided (Windows-first pilot vs Linux-first NFR-010) | NFR-010/020 | RV-05 F-06 | P1 |

### Tasks

| ID | Task | Lands | Source | Priority | Status | Blocked by |
|---|---|---|---|:--:|---|---|
| T-01 | Convene ADR-005 licence decision; update LICENSE/LIC-010; re-run gates | NR-01 | RV-06 F-27 | P0 | Not Started | — |
| T-02 | Write the no-import/provenance rule for vcast-findings assets | NR-02 | RV-06 F-27 | P0 | Not Started | — |
| T-03 | SRS change: TOOL-EXE-040 timeout distinct from fail + gate repair (PLG-080/100, COV-150, AIF allocations) | NR-03 | RV-02 F-11 | P0 | **Complete** | — |
| T-04 | Decide and record the identity model (SDD-003 §6/§7) — memo prepared, decision pending | NR-04 | RV-05 F-05 | P0 | Not Started | — |
| T-05 | Decide and record platform order | NR-05 | RV-05 F-06 | P1 | Not Started | — |

### T-03 evidence (landed 2026-11-07)

- **SRS-001 correction note 2026-11-07:** TOOL-EXE-040 timeout is a distinct outcome — never a failure (RV-02 F-11, aligning with SDD-002 §6.1); the AI-provider extension point is renumbered TOOL-PLG-080 → **TOOL-PLG-100** per ADR-008's 2026-10-17 note (TOOL-PLG-080 retains load-failure handling); TOOL-COV-150 → P4 per the recorded F-05 resolution; TOOL-AIF-260's cross-ref corrected to TOOL-PLG-100.
- **Design register:** DSN-PLG-050 (AI provider extension point), DSN-AIF-140 (structured-decision validation role) and DSN-AIF-150 (default provider is configuration) added; `requirement_count: 329`.
- **PLAN-001:** derived tables regenerated via `plan_check.py --write`; the stale "323 requirements" prose is gone after regeneration.
- **Both gates green:** `plan_check.py` exit 0 — 329 requirements, 327 unique primary allocations, 188 packages, 638 person-weeks, 52-week lower bound; `trace_check.py` exit 0 — 327/327 requirements allocated, 0 unallocated, 242 design elements, 24 components.
- **Discovered and fixed en route:** three pre-existing plan_check failures (duplicate TOOL-PLG-080 identifier, unallocated TOOL-PLG-100, WP-COV-09 deadline) and five unallocated AIF requirements — the 2026-10-17 corrections pass had updated ADR-008/SDD-002 but never re-run the gates. The canonical SRS requirement count is 329.

### T-04 decision memo (prepared 2026-11-07 — decision pending)

**Recommendation: keep stable ids + content digests (SDD-003 §6/§7) as the identity model; do not adopt separate revision entities.**

- RV-05 F-05 found the proposal's TestRevision/EnvironmentRevision model incompatible with ectt's accepted stable-id + digest staleness; a content digest in the result record reconciles the two.
- The proposal's own CompiledTestManifest semantics (executable ↔ test-content binding checked before every run) reduce to digest binding — no separate revision registry is required.
- SDD-002's fail-closed versioning already treats edited state as new content; digest binding preserves historical results without revision bookkeeping.
- On approval: record in an SDD-003 §6/§7 amendment plus one sentence in SDD-002 S2/S3; WP-TCM-02 then implements digest binding (unblocks T-14).

### T-12 evidence (landed 2026-11-07 — L1 Comprehension)

- **SRS-001:** TOOL-ING-200 (M, P2, T) — explicit authored per-scope link plan required before any harness build; ordered inputs with resolved identities, linker/runtime identity, effective link command; unresolvable input blocks the build with a diagnostic; the compilation database alone does not define the link.
- **PLAN-001:** WP-ING-07 (CMP-ING, P2, 2w) added; derived tables regenerated.
- **Design register:** DSN-ING-120 (authored link plan validation, fails closed; authored intent vs DSN-GEN-090's computed closure) satisfies TOOL-ING-200.
- **SDD-002 §2:** authored-inputs note (scopes, link plans, justifications cross seams as versioned project files). **SDD-003:** `link-plans/` added to the authored project tree.
- **Gates:** plan_check exit 0 — 330 requirements, 328 allocations, 189 packages, 640 person-weeks; trace_check exit 0 — 328/328 allocated, 243 elements.

### T-07 evidence (landed 2026-11-07 — L1 Comprehension)

- **SRS-001:** TOOL-ING-210 (response-file expansion: @file resolved against the entry working directory, depth-bounded recursion, raw invocation preserved, named diagnostics for missing/unreadable/oversized files) and TOOL-ING-220 (build-context identity: compiler path, target triple, sysroot; explicit build tag per ingested set).
- **PLAN-001:** ING-210 → WP-ING-02, ING-220 → WP-ING-03.
- **Design register:** DSN-ING-130 and DSN-ING-140 added; requirement_count 332.
- **Code:** src/ectt/ing — expand_response_files() with size/depth bounds, ResponseFileError with named reasons, CompilerInvocation.raw_arguments/target_triple/sysroot, TranslationUnit.response_files, CompilationDatabase.build_tag.
- **Tests:** 10 new tests; tests/ing+core+prj: 129 passed, 1 skipped (pre-existing); tests/ana requires libclang (environmental).
- **Gates:** plan_check exit 0 — 332 requirements, 330 allocations, 189 packages, 640 person-weeks; trace_check exit 0 — 330/330 allocated, 245 elements.

### T-08 evidence (landed 2026-11-07 — L1 Comprehension)

- **SRS-001:** TOOL-ING-100 reworded fail-closed — a stale ingested model forces re-ingestion before downstream use; warning-only consumption is no longer an available behavior; staleness is content-based (source, response file, configuration, include surface incl. shadowing and __has_include changes).
- **Design register:** DSN-ING-060 restated; unknown include-surface completeness forces rebuild.
- **Code:** src/ectt/ing/staleness.py (capture_staleness_inputs / check_staleness / assert_fresh; StalenessError with reasons and changed paths; include-surface bounded at 20000 headers, unknown → stale).
- **Fixtures:** tests/ing/test_staleness.py — 10 fixtures incl. shadowing create/revert, __has_include change, identical-mtime content change, missing source, unknown surface.
- **Tests:** tests/ing+core+prj: 138 passed, 1 skipped.
- **Gates:** plan_check exit 0 (332 requirements); trace_check exit 0 (330/330 allocated).

### T-09 evidence (landed 2026-11-07 — L1 Comprehension)

- **SRS-001:** TOOL-PAR-140 (per-unit machine-checkable unsupported-construct inventory, emitted even when empty) and TOOL-PAR-150 (explicit decision inventory whose completeness is data — not_extracted/partial/complete; cannot be omitted from a schema-valid model; unknown status fails closed) added; allocated to WP-ANA-07 and new WP-ANA-08.
- **Design register:** DSN-ANA-100 and DSN-ANA-110 added; requirement_count 334.
- **Schema:** analysis-model-1.1.schema.json published — decision_inventory required at model level, unsupported_constructs required per unit; the 1.0 schema remains published for historical documents.
- **Code:** model.py (UnsupportedConstructModel, DecisionInventoryModel, AnalysisUnit.unsupported_constructs, AnalysisModel.decision_inventory, schema 1.1); persist.py (assembler emits 1.1 with an explicit not_extracted inventory; reader enforces minor-gated presence and fail-closed status; historical 1.0 documents still read).
- **Verification:** smoke exercise (assemble → write → read → 3 negative gates → 1.0 compat) passed; tests/ing+core+prj 138 passed, 1 skipped; the ana test files carrying the new CI gate tests require libclang (environmental) — they run in CI.
- **Gates:** plan_check exit 0 — 334 requirements, 332 allocations, 190 packages, 641 person-weeks; trace_check exit 0 — 332/332 allocated, 245 elements.

### T-10 evidence (landed 2026-11-07 — L1 Comprehension)

- **SRS-001:** TOOL-PAR-160 (S, P2, T) — optional value-range constraints on parameters, struct/union fields, and type definitions, plus optional array dimension metadata, as first-class model data that bounded generation consumes as model input; round-tripped losslessly; absence explicitly optional.
- **PLAN-001:** WP-ANA-09 (CMP-ANA, P2, 1w) added; derived tables regenerated.
- **Design register:** DSN-ANA-120 added; requirement_count 335.
- **Schema:** analysis-model-1.2.schema.json published — optional value_range/dimensions (additive-optional minor bump; 1.0/1.1 remain published).
- **Code:** model.py — RangeModel, DimensionModel, ParameterModel.value_range, StructMemberModel.value_range, TypeModel.value_range + TypeModel.dimensions (nested element chains remain the primary shape encoding; the analyzer never manufactures ranges from C source — authored data, TCM/ATG scope).
- **Tests:** 5 new (round-trips, absent-key omission, jsonschema conformance vs 1.2) — 146 passed, 1 skipped.
- **Gates:** plan_check exit 0 — 335 requirements, 333 allocations, 190 packages, 641 person-weeks; trace_check exit 0 — 333/333 allocated, 245 elements.

### T-11 evidence (landed 2026-11-07 — L1 Comprehension)

- **SRS-001:** TOOL-PAR-170 (S, P2, T) — eligibility and observability gate over the analysis model; per-function observable channels (parameters, return value, global accesses) and machine-readable ineligibility reasons (static without opt-in exposure; no observable channel); discovery does not imply eligibility; requested-but-inaccessible state reported as gate reasons. Allocated to WP-ANA-06.
- **Design register:** DSN-ANA-130 added; requirement_count 336.
- **Code:** src/ectt/ana/eligibility.py — assess_eligibility(units, expose_static, void_type_refs) → EligibilityRecord (ref-normalized void detection; caller-supplied void set keeps type-graph naming decoupled). Records are S1-adjacent derived data consumed by CMP-ATG, deterministic and libclang-free.
- **Tests:** 8 new in tests/ana/test_eligibility.py — 154 passed, 1 skipped.
- **Gates:** plan_check exit 0 — 336 requirements, 334 allocations, 190 packages, 642 person-weeks; trace_check exit 0 — 334/334 allocated, 246 elements.

### T-13 evidence (landed 2026-11-07 — L6 Migration)

- **SRS-001:** TOOL-MIG-110 (S, P3, T) — legacy material containing compound or iterative test structures (slots, slot iterations, per-slot histories) is reported explicitly as deferred with its location; flattening, dropping and silent emulation are non-behaviors; the deferred set is machine-checkable so migration scope is auditable. The defer decision is recorded in the requirement text (RV-03 F-03).
- **PLAN-001:** MIG-110 allocated to WP-MIG-05 (Import fidelity reporting, P3); derived tables regenerated.
- **Design register:** DSN-MIG-090 (Deferred-structure reporting) added; requirement_count 337.
- **Gates:** plan_check exit 0 — 337 requirements, 335 allocations, 191 packages, 642 person-weeks; trace_check exit 0 — 335/335 allocated, 246 elements.

## Validation spikes (complete — ADR-001)

| WP | Capability | Effort | Status |
|---|---|--:|---|
| `WP-SPIKE-01` | CFG sufficiency spike: python-clang against real embedded code | 1w | Complete |
| `WP-SPIKE-02` | Nested type-aware test data editor spike in PySide6 | 2w | Complete |
| `WP-SPIKE-03` | PyInstaller distribution spike onto clean Windows | 1w | Complete |

## Repository hosting decision

**Already provisioned and live:** https://github.com/suduli/embedded-c-unit-test-tool — public, AGPL-3.0, remote `origin` verified live at `b5786e0`; docs tooling already emits this URL. Expected Pages: https://suduli.github.io/embedded-c-unit-test-tool/

| Option | Free tier (2026-11) | CI | Fit |
|---|---|---|---|
| **GitHub (current)** | Unlimited public repos; Actions free for public repos; Pages free | Actions | **Recommended — provisioned + tool-integrated** |
| GitLab.com | Unlimited public repos; 400 compute min/mo | GitLab CI | Viable mirror; tight CI quota |
| Codeberg | Non-profit Forgejo; Pages; Woodpecker beta (onboarding) | Woodpecker | Best non-profit option post-licence-decision |
| Self-host Forgejo | Free software, own hardware | Own runners | Org control; ops burden |

Recommendation: stay on GitHub; enforce branch protection on `main` + the traceability CI gate; resolve NR-01 (licence) before soliciting contributors; optionally mirror to Codeberg afterwards. Sources: refine.dev/blog/github-alternatives · european-alternatives.eu · live `git ls-remote` verification.

## Artifact links

| Artifact | Purpose |
|---|---|
| `2026-11-07-subsystem-requirements-and-tasks.md` | This register (authoritative) |
| `2026-11-07-subsystem-task-tracker.html` | HTML tracker (filterable: subsystem × status × phase) |
| `diagrams/subsystem-workmap.archify.json` + `.html` | Subsystem architecture diagram |
| `2026-11-06-vcast-findings-review-tracker.md` + RV-01..06 evidence | The review this register derives from |
