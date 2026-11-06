# Sequential requirements and architecture document review

**Project:** Unit / Embedded C Unit Testing Tool  
**Review date:** 2026-10-15  
**Reviewed checkout:** `b5786e020c34ebaf182b48e72c730c461d03c679`  
**Disposition:** **Changes required before baselining this document set.**  
**Findings:** **32 open — 16 HIGH, 15 MEDIUM, 1 LOW.**  
**Snapshot recheck:** 2026-10-17; all 11 document hashes still match the reviewed versions.  
**Evidence:** [Document hashes and traceability output](/E:/projects/UDS_Simulator/Unit/docs/reviews/2026-10-15-document-review-evidence.json).  
**Scope:** The 11 documents below were read in the listed order, followed by cross-document reconciliation and targeted checks of supporting artifacts. Source documents were left unchanged. All findings below are **OPEN**.

Severity: **HIGH** = contradiction or omission that blocks a stated requirement, invalidates claimed traceability, or risks losing evidence/user work; **MEDIUM** = material ambiguity, inaccurate rationale, or incomplete contract; **LOW** = editorial/reference defect. Severity concerns the documentation baseline, not proof of an exploitable or deployed software defect. Related occurrences are cross-referenced rather than counted again.

## Review inventory

| Order | Document | Finding IDs |
|---|---|---|
| 1 | [SRS-001 requirements](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md) | DR-01–06 |
| 2 | [PLAN-001 work breakdown](/E:/projects/UDS_Simulator/Unit/PLAN-001-specification-analysis-and-work-breakdown.md) | DR-07–09 |
| 3 | [SDD-001 architecture](/E:/projects/UDS_Simulator/Unit/design/SDD-001-architecture.md) | DR-10; related DR-08 |
| 4 | [SDD-002 interfaces](/E:/projects/UDS_Simulator/Unit/design/SDD-002-interfaces.md) | DR-11–14 |
| 5 | [SDD-003 persistent data](/E:/projects/UDS_Simulator/Unit/design/SDD-003-data-model.md) | DR-15–18; related DR-13 |
| 6 | [SDD-004 traceability](/E:/projects/UDS_Simulator/Unit/design/SDD-004-traceability-architecture.md) | DR-19–20; related DR-01/07 |
| 7 | [SDD-005 external integration](/E:/projects/UDS_Simulator/Unit/design/SDD-005-external-integration.md) | DR-21–23; related DR-03 |
| 8 | [ADR-001 core decisions](/E:/projects/UDS_Simulator/Unit/ADR-001-architecture-decisions.md) | DR-24–26; related DR-10/21 |
| 9 | [ADR-002 storage format](/E:/projects/UDS_Simulator/Unit/ADR-002-project-data-format.md) | DR-27–28 |
| 10 | [ADR-006 fork or build](/E:/projects/UDS_Simulator/Unit/ADR-006-fork-or-build-fresh.md) | DR-29 |
| 11 | [ADR-008 structured AI decisions](/E:/projects/UDS_Simulator/Unit/ADR-008-ai-structured-decision-provider.md) | DR-30–32; related DR-07/11 |

## 1. SRS-001 — requirements

### DR-01 — **HIGH: Two different requirements share TOOL-PLG-080**

**Location:** [line 866](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:866) and line 868.

The first definition requires an AI-provider extension point (Must/P2/Analysis); the second requires graceful extension-load failure (Must/P3/Demonstration). References cannot identify which obligation is intended. The trace checker reports the duplicate and a verification mismatch at DSN-PLG-030.

**Correction:** Preserve both obligations with distinct permanent IDs; update AI references, design allocations, verification methods, work packages and generated artifacts together. There are **329 definition lines but 328 unique IDs** in the current SRS. Keeping both obligations after renumbering would produce 329 unique IDs; merely changing the register count to 328 would conceal the duplicate.

### DR-02 — **HIGH: Phase commitments depend on later or optional functionality**

**Location:** [TCD-010, line 280](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:280), HAR-010 at 218, UIX-030 at 532, COV-140/150 at 414–416.

P1 C-authored tests require a generated harness that is P2. The P2 complete GUI workflow includes test authoring, while its detailed authoring facilities are placed in P3. Mandatory P3 justification metadata depends on a Should/P4 justification feature. PLAN-001 already identifies related phase defects; the SRS still contains them.

**Correction:** Define a coherent minimum workflow for each phase, move prerequisites earlier or narrow the earlier commitment, and make COV-150 explicitly conditional if COV-140 remains optional. Recompute the schedule after those decisions.

### DR-03 — **HIGH: Required project license conflicts with repository license**

**Location:** [LIC-010, line 748](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:748); [LICENSE](/E:/projects/UDS_Simulator/Unit/LICENSE:1); [LICENSEES](/E:/projects/UDS_Simulator/Unit/LICENSEES:3).

LIC-010 requires a permissive license, while the repository declares AGPL-3.0. PLAN-001 F-16 and SDD-005 §3 already acknowledge the conflict; acknowledgment does not resolve the requirement.

**Correction:** Record the owner's licensing decision and reconcile the SRS, ADR-005 decision status, dependency policy and repository notices. This review identifies the inconsistency and does not change licensing.

### DR-04 — **MEDIUM: Absolute egress prohibition conflicts with opt-in remote AI**

**Location:** [UIX-350, line 608](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:608), AIF-030 at 630.

UIX-350 prohibits transmitting any user content to an external service. AIF-030 allows source, test data and metadata to leave after session-specific remote-provider authorization. Both cannot apply literally to the same GUI-triggered remote AI operation.

**Correction:** Separate the unconditional telemetry prohibition from explicitly authorized AI data transfer, name the governing policy, and test both unauthorized denial and authorized transfer through the central provider interface.

### DR-05 — **MEDIUM: Determinism has inconsistent scope**

**Location:** [NFR-060, line 716](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:716), REP-070/100 at 482–488.

“All tool outputs” must be deterministic for identical inputs, but reports contain execution timestamps and REP-100 expressly excludes timestamps. AI output, time-budgeted generation and newly assigned IDs also need a defined replay boundary.

**Correction:** Define canonical output determinism separately from new execution observations. Specify which timestamps, seeds, provider responses, identifiers and environment/toolchain versions count as replay inputs, and which output fields are excluded from byte comparisons.

### DR-06 — **MEDIUM: Quantitative acceptance criteria remain underspecified**

**Location:** [NFR-030, line 710](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:710), NFR-140/150 at 732–734.

The 30-second target uses undefined “typical developer hardware”; own-source coverage and memory limits only require a documented threshold/ceiling without choosing one. Teams can select incompatible acceptance conditions after implementation.

**Correction:** Baseline reference hardware, workload, cache state, measurement method, coverage metric/exclusions and numeric ceilings, or point to a controlled acceptance specification that supplies them.

## 2. PLAN-001 — specification analysis and work breakdown

### DR-07 — **HIGH: Complete allocation claims omit five AI requirements**

**Location:** [coverage claim, line 49](/E:/projects/UDS_Simulator/Unit/PLAN-001-specification-analysis-and-work-breakdown.md:49), §7 and Appendix A; [register](/E:/projects/UDS_Simulator/Unit/design/trace/design-elements.yaml).

The plan claims all 323 requirements are covered. Appendix A omits AIF-220, AIF-230, AIF-240, AIF-250 and AIF-260. The live checker finds those five unallocated, including two Must requirements. Its current unique-ID totals are 328 parsed, 326 in scope and 321 allocated, with the duplicate caveat in DR-01. SDD-004's “321/321” snapshot and the generated matrix/graph cannot establish current completeness.

**Correction:** Repair DR-01 first, allocate the five requirements and the distinct AI extension obligation, revise effort/phase estimates, then regenerate all dependent counts and views. Require the traceability check to pass before claiming full allocation.

### DR-08 — **MEDIUM: Planning and architecture decision status is stale**

**Location:** [PLAN line 4](/E:/projects/UDS_Simulator/Unit/PLAN-001-specification-analysis-and-work-breakdown.md:4), line 26, §§4.1/9; [SDD-001 line 35](/E:/projects/UDS_Simulator/Unit/design/SDD-001-architecture.md:35) and §8.

The plan describes ADR-001 as undecided and still treats accepted decisions/spikes as future gates. SDD-001 says none of ADR-001–007 is decided while its later material records accepted decisions; ADR-002 remains presented as unresolved. ADR-008's new provider scope has not propagated through the baseline.

**Correction:** Retain dated historical analysis as history, but refresh the current decision register, outstanding work and upstream versions. Link each accepted decision to its implemented, pending and superseded consequences rather than leaving contradictory current-state prose.

### DR-09 — **HIGH: Results-export obligation is assigned to the wrong work package**

**Location:** [line 765](/E:/projects/UDS_Simulator/Unit/PLAN-001-specification-analysis-and-work-breakdown.md:765), WP-REP-10 at 495; SRS MIG-060 at 808.

The plan says WP-REP-10 supplies the results half of MIG-060. WP-REP-10 actually delivers coverage interchange for MIG-080 in P4. MIG-060 requires reconstructable test-case and result exports in P2. A coverage exchange task does not cover the result-export obligation or its delivery date.

**Correction:** Assign a P2 result-export owner and format, include reconstruction/round-trip acceptance, and fix the dependency and allocation tables.

## 3. SDD-001 — architecture and component design

### DR-10 — **MEDIUM: Complete API lacks a documented route to higher-layer capabilities**

**Location:** [line 145](/E:/projects/UDS_Simulator/Unit/design/SDD-001-architecture.md:145), §4.4 at 233; SDD-002 §9.3.

The architecture says no L5 component depends on L6, while the API must expose the complete capability surface, including L6 AI and migration functions. The register gives CMP-API only a CMP-CORE dependency and does not describe the composition root or inverted operation ports that make this work. ADR-001's in-process/no-IPC rationale also needs reconciliation with the mandatory JSON transport.

**Correction:** Document registration/composition ownership, operation interfaces, call flow into AIF/MIG and how CLI/GUI use the mandated transport. In-process calls can coexist if their role and equivalence are explicit. This is a missing architectural explanation, not proof that dependency inversion is impossible. See DR-08 for stale status text.

## 4. SDD-002 — interface design

### DR-11 — **HIGH: AI-provider extension contract is missing**

**Location:** [S7, line 378](/E:/projects/UDS_Simulator/Unit/design/SDD-002-interfaces.md:378).

S7 lists four extension points and still interprets PLG-080 solely as load-failure handling. SRS AIF-230/250/260 and ADR-008 require a shared provider interface covering generation and structured validation. A declared architectural seam without request, response and capability contracts cannot deliver interchangeable providers.

**Correction:** Add the AI extension point with role capabilities, version negotiation, request/response schemas, provenance, error/timeout/cancellation behavior and local/remote authorization. Allocate it after DR-01 is resolved. Prove two different adapters work without caller changes.

### DR-12 — **HIGH: Coverage model does not define MC/DC independence evidence**

**Location:** [S4 model, line 245](/E:/projects/UDS_Simulator/Unit/design/SDD-002-interfaces.md:245), especially line 252.

Per-condition true/false flags and a generic decision status cannot distinguish ordinary outcome coverage from demonstrated independent effect. The contract does not define condition independence status, its derivation or supporting test-vector references. Reporting/merging can therefore discard the information required to substantiate MC/DC. Clang documents independent effect as the defining criterion. [Clang coverage documentation](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html#interpreting-reports).

**Correction:** Define per-condition MC/DC status and evidence provenance, merge semantics, unsupported/unmeasured states and summary denominators. Require fixtures with identical outcome flags but different independence results. This finding concerns the published model, not a measured failure in an implemented coverage engine.

### DR-13 — **MEDIUM: Schema-version acceptance rules conflict and are too broad**

**Location:** [versioning, line 58](/E:/projects/UDS_Simulator/Unit/design/SDD-002-interfaces.md:58); [SDD-003 reader rule, line 156](/E:/projects/UDS_Simulator/Unit/design/SDD-003-data-model.md:156).

SDD-002 accepts every newer minor version and permits added enum members; SDD-003 rejects versions above reader.max. Unknown result/review states are not equivalent to ignorable descriptive fields, and a writable reader could also discard unknown fields on save.

**Correction:** Publish one compatibility policy per seam. Define safe additive changes, unsupported enum behavior, preservation rules for writable documents and rejection/capability negotiation for semantics the reader cannot honor. Test older-reader/newer-writer combinations.

### DR-14 — **MEDIUM: IPC framing and cancellation are not specified**

**Location:** [transport and message shape, line 329](/E:/projects/UDS_Simulator/Unit/design/SDD-002-interfaces.md:329).

The document gives JSON objects over byte streams without choosing framing or defining size limits. Its “progress / cancellation” example only shows progress. It omits cancellation requests/acknowledgments, terminal-event ordering and completion/cancel races.

**Correction:** Specify framing, encoding, correlation rules, error envelope, message limits and a cancellation state machine. Add interoperability examples for partial reads, concurrent requests and a cancellation arriving as an operation completes.

## 5. SDD-003 — persistent data design

### DR-15 — **HIGH: Output-only write rule contradicts project editing**

**Location:** [two-tree rules, line 51](/E:/projects/UDS_Simulator/Unit/design/SDD-003-data-model.md:51) through line 57.

The project tree is explicitly written by tool operations, but the following rule confines every write to the output root. That would prohibit project creation, saving tests and storing justifications in the prescribed layout.

**Correction:** Define separate authorized project-state and generated-output write boundaries, while preserving read-only UUT sources. Specify transactional project updates and path/symlink handling for both boundaries.

### DR-16 — **HIGH: Project metadata prohibition excludes mandatory provenance**

**Location:** [determinism rules, line 133](/E:/projects/UDS_Simulator/Unit/design/SDD-003-data-model.md:133), line 142 and justifications layout at 79.

The whole project tree forbids timestamps and user names, and provenance is placed only in output/archive data. Yet authored justifications live in the project tree and COV-150 requires author/date; AI-origin and review information likewise require persistent provenance.

**Correction:** Distinguish volatile serialization metadata from meaningful authored audit fields. Preserve required author, review and creation facts in canonical project records; exclude only incidental save-time/host information from deterministic serialization.

### DR-17 — **HIGH: Disposable output can contain irreplaceable user code**

**Location:** [regeneration claim, line 50](/E:/projects/UDS_Simulator/Unit/design/SDD-003-data-model.md:50), generated harness/stubs at 88; SRS HAR-100 and STB-110/120.

Output is described as fully regenerable and always ignorable, but generated harnesses and stubs have user-editable regions that must survive regeneration. No canonical project-tree store is identified for those authored bodies. Deleting the allegedly disposable output could lose them.

**Correction:** Store user fragments in authored project state and generate from them, or explicitly classify affected files as non-disposable with preservation/conflict safeguards. Demonstrate delete-and-regenerate recovery using nontrivial user modifications.

### DR-18 — **HIGH: Archive layout does not establish the promised replay closure**

**Location:** [archive design, line 223](/E:/projects/UDS_Simulator/Unit/design/SDD-003-data-model.md:223).

The archive promises no outward references and discusses re-execution, but lists configuration, tests, report model and reports without a UUT source/header snapshot, user stub bodies or a complete toolchain/build-input closure. Recording a compiler name/version alone cannot recover those inputs after the original workspace disappears.

**Correction:** Separate report re-rendering from executable replay. Specify the source/build dependency snapshot and hashes, user-authored generated-code fragments, and how exact tool/release/toolchain artifacts remain available offline. Test reproduction with the original workspace unavailable.

## 6. SDD-004 — traceability architecture

### DR-19 — **MEDIUM: Code/test traceability is still described as pre-code future work**

**Location:** [line 256](/E:/projects/UDS_Simulator/Unit/design/SDD-004-traceability-architecture.md:256), also line 46.

The document says code links are inactive because there is no code, although source and tests now exist. The current trace checker validates requirements/design/register/diagrams, not the full declared source-implements and test-verifies graph. The intended activation gate has not been reconciled with the repository's development stage.

**Correction:** Update the current-state section and define the delivered-phase scope for activating source/test trace checks. Distinguish declarative design allocation, claimed source/test links and executed verification evidence. Do not label design coverage as implementation or test coverage. Current design-count claims are separately covered by DR-07.

### DR-20 — **MEDIUM: Dependency-edge table permits too much of L6**

**Location:** [line 93](/E:/projects/UDS_Simulator/Unit/design/SDD-004-traceability-architecture.md:93).

The table allows same/lower layers “plus L6,” whereas SDD-001 and the checker limit upward references to explicitly cross-cutting components, currently PLG and SEC. The shorthand appears to allow dependencies on AI, migration or packaging that the actual rule forbids.

**Correction:** State the cross_cutting exception precisely and use the same wording in prose, register documentation and diagram legends.

## 7. SDD-005 — external integration

### DR-21 — **HIGH: LibTooling rejection contradicts the accepted analyzer fallback**

**Location:** [line 390](/E:/projects/UDS_Simulator/Unit/design/SDD-005-external-integration.md:390), rejection table at 371; [ADR-001 line 134](/E:/projects/UDS_Simulator/Unit/ADR-001-architecture-decisions.md:134).

SDD-005 rejects LibTooling categorically on ABI grounds; accepted ADR-001 explicitly permits a focused C++ LibTooling analyzer emitting the same JSON model. An isolated, pinned executable has a different compatibility boundary from linking the main application to a changing C++ ABI.

**Correction:** Reconcile the policy with the accepted fallback. Define whether the rejected case is in-process linkage and document build/pinning/distribution obligations for the allowed executable, or formally supersede the fallback with evidence.

### DR-22 — **MEDIUM: Several dependency facts are incorrect**

**Location:** [GoogleTest, line 261](/E:/projects/UDS_Simulator/Unit/design/SDD-005-external-integration.md:261); [RTT, line 548](/E:/projects/UDS_Simulator/Unit/design/SDD-005-external-integration.md:548); [grcov, line 804](/E:/projects/UDS_Simulator/Unit/design/SDD-005-external-integration.md:804).

| Claim in document | Evidence-backed correction |
|---|---|
| GoogleTest 1.14 is last C++14; 1.15 raises floor to C++17 | The official 1.15 release still supports C++14. Recheck the exact chosen tag rather than using this boundary. [GoogleTest v1.15.0](https://github.com/google/googletest/releases/tag/v1.15.0). |
| grcov cannot read branch data | Its upstream instructions explicitly support branch coverage with --branch. This does not establish MC/DC support. [grcov README](https://github.com/mozilla/grcov). |
| SEGGER RTT target-source grant requires a SEGGER probe | The current official target-source license permits redistribution/modification and does not contain that restriction. This is distinct from J-Link software licensing. [RTT license](https://github.com/SEGGERMicro/RTT/blob/main/LICENSE.md). |

**Correction:** Pin the exact source/version/license reviewed, update all repeated claims including the “verified” appendix, and reassess the affected accept/reject rationale. Live upstream checks were made on 2026-10-15; they do not substitute for verifying the eventual shipped artifact.

### DR-23 — **MEDIUM: Dependency eligibility rules conflict with accepted packaging choices**

**Location:** [license-policy table, line 106](/E:/projects/UDS_Simulator/Unit/design/SDD-005-external-integration.md:106), interpreter exclusion at 885.

“Permissive only” for linked dependencies does not account for accepted PySide6/Qt licensing. The assertion that INS-030 and K-04/K-05 exclude every interpreter-based dependency also conflicts with the accepted bundled Python runtime approach: a user-installed interpreter and a bundled runtime are different deployment obligations.

**Correction:** Define admissibility by the actual artifact, license and distribution mechanism. Document exceptions/obligations for accepted dependencies and distinguish forbidden prerequisites from bundling cost. Additional “never bundle” policies should be identified as project decisions rather than inferred automatically from offline/non-admin installation requirements.

## 8. ADR-001 — core decisions

### DR-24 — **HIGH: Qualification content is committed to two different releases**

**Location:** [Tier 2, line 47](/E:/projects/UDS_Simulator/Unit/ADR-001-architecture-decisions.md:47), SRS-impact line 67.

Tier 2 puts tool-classification analysis in v1.1, while §1.6 retains QUA-010–060 in v1.0. QUA-010 is precisely the classification analysis. The accepted summary repeats the tier split without resolving the requirement-level conflict.

**Correction:** Publish a requirement-by-requirement release/phase mapping and amend the SRS and plan to match the accepted scope. Do not treat P4 and v1.1 as interchangeable without an explicit release definition.

### DR-25 — **HIGH: Suggested QScintilla choice is unresolved for the selected stack/policy**

**Location:** [GUI comparison, line 172](/E:/projects/UDS_Simulator/Unit/ADR-001-architecture-decisions.md:172).

The Qt option proposes QScintilla for source/coverage viewing, while the selected stack uses PySide6 and LIC-020 restricts strong-copyleft linkage. Riverbank documents QScintilla Python bindings based on PyQt and GPLv3/commercial licensing. The ADR provides neither a compatible binding plan nor a license decision. [QScintilla introduction](https://www.riverbankcomputing.com/software/qscintilla/intro).

**Correction:** Treat the editor widget as an unresolved dependency until a compatible, permitted option is selected and tested. If QScintilla is retained, document the exact binding and licensing arrangement; do not imply that selecting PySide6 settles it.

### DR-26 — **MEDIUM: Linker wrapping does not solve same-translation-unit call interception**

**Location:** [STB-090 rationale, line 94](/E:/projects/UDS_Simulator/Unit/ADR-001-architecture-decisions.md:94).

The feasibility table points to linker --wrap for call wrapping. GNU ld applies wrapping to undefined references; calls resolved within the same translation unit do not acquire the required interception simply by passing this flag. SDD-005 already recognizes this boundary. [GNU ld options](https://sourceware.org/binutils/docs/ld/Options.html).

**Correction:** Narrow the claim to external unresolved calls and define a separate strategy or unsupported case for same-unit/static/inlined calls. Verify the intended compiler/linker/optimization combinations before claiming STB-090 coverage.

## 9. ADR-002 — project data storage format

### DR-27 — **MEDIUM: Byte-identical no-op guarantee needs an input-domain qualification**

**Location:** [canonicalization rule, line 51](/E:/projects/UDS_Simulator/Unit/ADR-002-project-data-format.md:51).

The ADR requires canonical quoting/indentation and says semantically null load-save cycles are strictly byte-identical. Valid noncanonical input necessarily changes when canonicalized. The real RestrictedYamlAdapter reproduced this: `schema_version: "1.0"\nname: demo\n` became `"schema_version": "1.0"\n"name": "demo"\n`; parsed values stayed equal but bytes changed.

**Correction:** Guarantee byte stability after canonicalization, or preserve the original bytes when no semantic edit occurs. State which behavior the API promises and verify both canonical and valid noncanonical inputs. This is a reproduced adapter-level limit; a separate project-save optimization could still preserve bytes.

### DR-28 — **LOW: Invalid section reference and overly broad format summary**

**Location:** [line 5](/E:/projects/UDS_Simulator/Unit/ADR-002-project-data-format.md:5), line 43, summary at 107.

“SDD-001 §396” refers to a line number as if it were a section. The summary's “all ectt project artifacts” is also broader than the intended authored project documents: analysis/report exchange models and archive manifests remain JSON elsewhere.

**Correction:** Use the stable SDD-001 §8 decision-table reference/anchor and explicitly scope Restricted YAML to authored project-state documents, preserving the JSON seams.

## 10. ADR-006 — fork or build fresh

### DR-29 — **MEDIUM: Claimed fork savings are not all off the critical path**

**Location:** [line 307](/E:/projects/UDS_Simulator/Unit/ADR-006-fork-or-build-fresh.md:307), savings table at 281; [PLAN critical path, line 315](/E:/projects/UDS_Simulator/Unit/PLAN-001-specification-analysis-and-work-breakdown.md:315).

The ADR estimates about six weeks saved on ANA-01/02/03 and then calls all savings off the critical path. PLAN-001 explicitly places ANA-01 and ANA-02 on that path and calls this analysis/generation segment compressible.

**Correction:** Recompute schedule sensitivity with the actual dependency graph, separating effort savings from calendar savings and porting/rehosting prerequisites. The build-fresh conclusion may still hold, but this particular justification is unsupported as written.

## 11. ADR-008 — AI structured-decision provider

### DR-30 — **HIGH: Certification-evidence exclusion overstates the SRS**

**Location:** [line 172](/E:/projects/UDS_Simulator/Unit/ADR-008-ai-structured-decision-provider.md:172); [AIF-100](/E:/projects/UDS_Simulator/Unit/SRS-001-requirements.md:644).

The ADR says AIF-100 excludes every AI-generated or AI-adjudicated result. AIF-100 actually requires a configurable mode prohibiting AI-generated artifacts; it neither mandates universal exclusion nor explicitly covers adjudication. The stated assurance argument depends on a stronger rule than the requirement supplies.

**Correction:** Specify how generated, reviewed and adjudicated artifacts are classified, what the evidence mode excludes, and its default/enforcement. Amend the controlling requirement if universal exclusion is intended. Preserve original deterministic results and provenance separately from AI advice.

### DR-31 — **HIGH: Typed vendor output is treated as removing validation**

**Location:** [comparison, line 98](/E:/projects/UDS_Simulator/Unit/ADR-008-ai-structured-decision-provider.md:98), consequences at 156–157.

The ADR describes values that callers can branch on without a parse/validate step. Even a typed SDK response needs boundary validation of schema/version, ranges, expected choices, missing values, transport errors and provider capability. Vendor typing alone does not establish semantic validity for a test decision.

**Correction:** Require provider-adapter validation and a normalized validated result before control-flow use. Define abstention/error behavior, provenance and whether AI may influence acceptance. Test malformed, out-of-range, missing and unsupported responses independently of any vendor's documentation.

### DR-32 — **MEDIUM: Provider capabilities and substitution cost are overstated**

**Location:** [primitive claims, line 56](/E:/projects/UDS_Simulator/Unit/ADR-008-ai-structured-decision-provider.md:56), line 100 and substitution claim at 158–169.

The current TypeSafe introduction lists probabilities/confidence for Choice and Score, but Noul is described as a numeric value in [0,1]; that is not automatically a separate calibrated confidence signal. The ADR also describes substitution of an unknown provider type as changing configuration alone, although its own design requires an adapter. [TypeSafe introduction](https://docs.typesafe.ai/introduction).

**Correction:** Model confidence/probabilities as explicit optional capabilities with documented meaning. Distinguish selecting an already implemented adapter from implementing/evaluating a new one. Retain the ADR's existing caution that vendor claims have not been independently behaviorally verified.

## Evidence and verification

The read-only traceability command was run in the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe design\trace\trace_check.py --check-diagrams design\diagrams
```

**Result: exit 1, eight errors**:

1. Duplicate TOOL-PLG-080 at SRS line 868, first defined at 866.
2. Register declares 323 requirements; checker parsed 328 unique IDs.
3. DSN-PLG-030 declares verification D but its retained PLG-080 allocation requires A.
4. TOOL-AIF-220 unallocated.
5. TOOL-AIF-230 unallocated.
6. TOOL-AIF-240 unallocated.
7. TOOL-AIF-250 unallocated.
8. TOOL-AIF-260 unallocated.

The count includes one raw duplicate definition. The checker reports 326 non-Future unique IDs, 321 allocated, 239 design elements and 24 components. These figures do not prove all semantic allocations are correct.

Other checks:

- Work-package arithmetic: **183 packages, 622 person-weeks**; total agrees with the plan.
- Requirement comparison: the plan's appendix contains 323 IDs and omits the five AI IDs above.
- Relative Markdown file-target check across the 11 documents and design/README: **no missing local targets found**. Fragment anchors, plain-text section references and every external URL were not exhaustively validated.
- RestrictedYamlAdapter no-op example: equal parsed values, unequal serialized bytes, as described in DR-27.
- Targeted upstream checks: GoogleTest, grcov, SEGGER RTT, QScintilla, GNU ld, Clang coverage and TypeSafe documentation.
- Supporting review included the design register, generated matrix/graph, diagram specifications and traceability CI/checker. Diagram visual rendering and full application behavior were not tested.

This review establishes document inconsistencies and contract gaps. It does not certify implementation completeness or independently validate every external dependency, standard interpretation, historical spike or vendor claim. No application changes, commits or license changes were made.

## Suggested correction order

1. Repair requirement identity and allocation (DR-01/07/11), then regenerate trace artifacts.
2. Settle release phases, licensing and qualification scope (DR-02/03/09/24).
3. Resolve authored-data safety and replay rules (DR-15–18).
4. Complete coverage, schema, IPC and AI boundary contracts (DR-10–14/30–32).
5. Reconcile accepted decisions, dependency facts and rationale (remaining findings).
6. Rerun traceability and targeted contract checks; close findings with revised locations and evidence.

