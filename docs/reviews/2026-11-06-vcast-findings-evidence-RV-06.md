# RV-06 — vcast-findings gaps, risks & open decisions vs ectt baseline

- **Review agent:** RV-06 of six (gaps, risks & open decisions domain)
- **Date:** 2026-11-06
- **Subject:** `vcast-findings/` remaining-gap register, dispositioned design-review findings, review-process notes and declared unknowns
- **Baseline:** ectt accepted decisions and plans — `ADR-001-architecture-decisions.md`, `PLAN-001-specification-analysis-and-work-breakdown.md`, `docs/reviews/2026-10-15-document-review.md`, `design/SDD-002-interfaces.md`, `design/SDD-005-external-integration.md`, `SRS-001-requirements.md`
- **Method:** read-only cross-review. No script inside `vcast-findings/` was executed; no file outside this evidence document was modified. Every finding cites at least one path on each side. Verdicts use the tracker legend (`aligned` | `conflict` | `gap` | `risk`); the coverage table additionally uses reflected / partial / net-new.

Inputs read:

- `vcast-findings/deep-specifications/GAPS.md` (8 recovery gaps)
- `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (Codex 1–6, Claude F1–F6, dispositions, readiness boundary)
- `vcast-findings/deep-specifications/REVIEW_NOTES.md` (review-process corrections)
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` §"What remains unknown" (6 unknowns) and §"Design boundary"
- `vcast-findings/README.md` (scope note) and `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §8/§9/§12 (FRs, validation strategy, ownership decisions)

---

## 1. Disposition-coverage table

| # | vcast-findings item | Verdict | ectt citation | Applies to |
|---|---|---|---|---|
| G1 | GAPS: native parser/generator/instrumenter tracing | Reflected (principle); row itself investigation-only | `PLAN-001` §6.4 differential testing (l.636–640); `SDD-005` §6.1 floors (l.691–709); ADR-004 open (`PLAN-001` l.160) | Both (ectt residue = validate its *own* chosen backends) |
| G2 | GAPS: exact generated harness comparison | Partial — net-new check | `PLAN-001` WP-QUA-03 known-answer suite (l.529); QUA-030; §6.4 corpus (l.629–634) — no harness-vs-reference-test agreement check | ectt validation planning |
| G3 | GAPS: script compatibility corpus (malformed inputs) | Reflected | `PLAN-001` l.156 (ADR-002 "grammar, rejection and preservation tests"); §6.4 negative testing (l.657–661); WP-SEC-03 (l.537) | Both |
| G4 | GAPS: populated persistence inspection / migration | Reflected (residue); row investigation-only | `PLAN-001` WP-PRJ-03 schema migration w/ confirmation (l.326); DR-15–18 corrections (`design/SDD-003-data-model.md` l.8) | Both |
| G5 | GAPS: coverage format / MC/DC algorithm validation | Reflected | `design/SDD-002-interfaces.md` §7.1 acceptance fixtures (l.315–317); `PLAN-001` WP-COV-05 (l.422); R-4 (`ADR-001` l.297) | ectt validation planning |
| G6 | GAPS: UI workflow observation | Reflected (concern class); row investigation-only | `PLAN-001` L5 register (22 WP-GUI-*, l.462–483); P2 gate (l.675) | VectorCAST-investigation only |
| G7 | GAPS: compiler/target/performance measurement on exact config | Partial — known open baseline defect | DR-06 (`docs/reviews/2026-10-15-document-review.md` l.72–78); `PLAN-001` WP-CORE-05 / NFR-030/040/150 (l.320) | ectt validation planning |
| G8 | GAPS: requirements/qualification evidence | Reflected | `ADR-001` §1.3 tiers (l.44–50) + §1.6 QUA mapping (l.69–84); QUA-090 / WP-QUA-07 (`PLAN-001` l.533); R-10 (`ADR-001` l.303) | Both |
| C1 | Codex 1: compilation database lacks link plan | Partial | `SRS-001` ING-010..040 (l.122–128, compile only); HAR-120 / WP-GEN-05 link closure (`SRS-001` l.242; `PLAN-001` l.372) | ectt design/plan |
| C2 | Codex 2: fresh dependency resolution over caches | Partial | ING-100 staleness "re-ingest or warn" (`SRS-001` l.140, Should/P2); WP-ING-03 (l.345) — weaker than "unknown completeness forces rebuild" | ectt design/plan |
| C3 | Codex 3: executable/test-revision mismatch | Partial | HAR-090 generator header (l.236), HAR-110 interface staleness (l.240), CBT-010 (l.426), CBT-070 (l.438) — no artifact-binding check before each run | ectt design/plan |
| C4 | Codex 4: attempt-before-build; evaluation identity | Partial | QUA-060 / WP-CORE-04 provenance (`SRS-001` l.692; `PLAN-001` l.319); S3 `run_id` (`SDD-002` l.222–236) — no attempt-before-build-success contract | ectt design/plan |
| C5 | Codex 5: unknown coverage denominator | Reflected | `SDD-002` §7.1 denominators + zero-denominator N/A (l.293–301); §7.2 "unmeasured is not uncovered" (l.324–326); S1 decision inventory (l.146–151); COV-080 (`SRS-001` l.402) | ectt design (key check passed) |
| C6 | Codex 6: reproducibility definition | Reflected | SEC-030 "functionally identical" + SEC-040 pins/hashes (`SRS-001` l.772–774); WP-SEC-02 (l.536); §6.4 two-machine diff (l.642–645); P4 auditor gate (l.677) | ectt design (key check passed) |
| CL1 | Claude F1: embedded-to-host portability / HostProfile | Partial | TGT-070 / WP-EXT-04 parity (`SRS-001` l.372; `PLAN-001` l.403); SDD-005 §6.3 capability probing (l.730–741) — no first-class ABI-gap record | ectt design (low priority) |
| CL2 | Claude F2: inaccessible state observability gate | Reflected | PAR-080 (l.178) + HAR-030 optional static exposure (l.222); PAR-090 macro obscuring (l.180); WP-GEN-03 / WP-ANA-06 (`PLAN-001` l.370, l.341) | ectt design |
| CL3 | Claude F3: stub symbol/prototype evidence | Reflected | STB-030 type closure (l.252) + `SDD-002` S1 contract point "stub must compile standalone" (l.141); HAR-120/WP-GEN-05; DR-26 wrapping limits (`ADR-001` l.108); `SDD-005` §5.2.1 | ectt design |
| CL4 | Claude F4: crash profile absence | Partial | EXE-030 crash isolation (l.342); S3 `infrastructure_faults` (`SDD-002` l.244); S4 `unmeasured` (l.324–326) — no explicit crashed-run coverage admission rule | ectt design (minor) |
| CL5 | Claude F5: premature exit(0) / modal errors | Partial | EXE-030/040/060 (l.342–348); S3 `timeout` distinct outcome (`SDD-002` l.246); WP-EXH-02 (l.397) — no completion-marker vs exit-0 rule, no modal/no-dialog validation | ectt design/plan |
| CL6 | Claude F6: libclang vs LibTooling feasibility | Reflected | `ADR-001` §2.4/§2.5 (l.143–162); R-01/R-5 fallback (l.294, l.761); DR-21 correction (l.7) + `SDD-005` §6.2 item 3 (l.726–728); `SDD-002` S1 (l.95–101) | ectt design (key check passed) |
| U1 | Unknown: EDG/parser/instrumentation algorithms | Reflected as architecture stance; investigation-only | `SDD-005` §5.7 "engine never enters the evidence chain" (l.585–589); ADR-004 open (`PLAN-001` l.160) | VectorCAST-investigation primarily |
| U2 | Unknown: full C++ mocking/interception | Reflected as scope decision; investigation-only | `SDD-005` §1.2 (l.51); GoogleTest host-only P3 WP-GEN-10 (`PLAN-001` l.377) | VectorCAST-investigation only |
| U3 | Unknown: active SQL schemas / migrations / transactions | Reflected by different design; investigation-only | ADR-002 restricted YAML (l.112); `PLAN-001` WP-PRJ-01..03 (l.324–326) | VectorCAST-investigation only |
| U4 | Unknown: host/target timing, overhead, robustness under failures | Partial — known open defect | DR-06 (l.72–78); WP-CORE-05 (l.320); §6.4 target-in-the-loop (l.652–655); WP-EXT-06 footprint docs (l.405) | ectt validation planning |
| U5 | Unknown: runtime activation of optional packages | Reflected | WP-PLG-02 discovery/load-failure isolation (l.524); PLG-070/080; AIF-01 | VectorCAST-investigation primarily |
| U6 | Unknown: qualification/acceptance evidence for supplied build | Reflected (posture) | `ADR-001` §1.2–1.5 (l.40–65); R-10 (l.303); PRODUCT_ARCHITECTURE §9 qualification disclaimer (l.267) matches | Both (posture parity) |
| R1 | README scope note + extracted proprietary assets; PRODUCT_ARCHITECTURE §12 separate-repository rule | Net-new risk | `LICENSE` AGPL-3.0 vs LIC-010 (F-16, `PLAN-001` l.119–129; DR-03 l.48–54; `SDD-005` §3.2 l.137–161); R-8 (`PLAN-001` l.764); ADR-005 open (l.161) | Both — decision-relevant |
| R2 | REVIEW_NOTES process corrections | Reflected (process parity) | 2026-10-17 correction notes in `ADR-001` l.7, `ADR-002` l.112, `ADR-006` (header), `ADR-008` (header), `SDD-003` l.8, `PLAN-001` l.3 | Process note only |

DR correction coverage verified on the ectt side: ADR-001 note covers DR-24–26 (+DR-10/21), ADR-002 note covers DR-27/28, ADR-006 note covers DR-29, ADR-008 note covers DR-30–32, SDD-003 revision note covers DR-15–18 and DR-13, PLAN-001 v0.2 reconciliation refreshes DR-08's status staleness. Remaining uncorrected: DR-01–06 (SRS), DR-10–14 (SDD-001/002), DR-19/20 (SDD-004), DR-22/23 (SDD-005) — in particular **DR-03/F-16 (licence) remains open in every document that mentions it** (`ADR-001` l.7 "the project license remains unresolved"; `PLAN-001` l.161; `SDD-005` §3.2).

---

## 2. Findings

### F-01 — GAPS row 1: native parser/generator/instrumenter tracing
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Native parser, generator and instrumenter" (l.5) and closing note (l.14): "Ghidra, IDA and Kuna were not configured… Obtaining a decompiler alone will not establish runtime behavior… A bounded original prototype can proceed to a feasibility experiment."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` §6.4 "Differential testing against ground truth" (l.636–640): reported coverage must agree with the backend's own report line for line; `E:\projects\UDS_Simulator\Unit\design\SDD-005-external-integration.md` §6.1 binding floors for GCC/Clang coverage (l.695–699).
**Assessment:** The row is an investigation-of-VectorCAST concern (recover third-party native behavior). ectt needs no decompiler tracing; its analogue — proving its *chosen* parser/coverage backends behave as documented — is already planned (differential testing, ADR-004 backend decision, `WP-COV-01/05`). Both sides independently converge on the same moral: an unverified backend must not anchor claims.
**Recommendation:** No new ectt work. Keep the GAPS moral in mind when closing ADR-004: the backend decision must be followed by the §6.4 differential fixtures before coverage claims are enabled (`PLAN-001` l.160 gates ADR-004 before COV-01 integration).

### F-02 — GAPS row 2: compare generated harness against reference tests
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Exact generated harness and stub dispatch" (l.6); `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §9 (l.261): "Compare generated-harness results with manually written reference tests."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` WP-QUA-03 user-executable validation suite (l.529, QUA-030 "known-answer cases"), §6.4 reference corpus (l.629–634, parse-construct coverage) and golden-file testing (l.642–645, byte stability). No work package or test-design paragraph requires that a *generated harness executing hand-authored inputs* agrees with a *manually written reference test of the same case*.
**Assessment:** ectt validates harness determinism (golden files) and parse breadth (corpus), but the metamorphic check "generated pipeline result == reference-test result on the same inputs" — which the vcast design review added as a core validation strategy — is not in the plan. This is the cheapest strong oracle for harness-generation semantics (WP-GEN-01/02) and fits naturally inside WP-QUA-03's known-answer suite.
**Recommendation:** Extend WP-QUA-03 acceptance (or §6.4) with a small fixture set where each generated-harness run must match a hand-written Unity/cmocka reference test's outcome, including one failing case. Documentation-level change; no ADR needed.

### F-03 — GAPS row 3: malformed/repeated/range/escape input corpus
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Script compatibility and edge cases" (l.7): run malformed, repeated, range, escape and case-sensitive inputs.
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` l.156 (ADR-002 consequence: "implement grammar, rejection and preservation tests"); §6.4 "Negative testing — what the tool must refuse" (l.657–661); WP-SEC-03 configuration-is-data (l.537).
**Assessment:** The concern class (hostile/edge inputs to the tool's own input format) is already an accepted consequence of ADR-002 plus §6.4 negative testing; TCD-050/060 (comparison engine) and WP-TCM-05 ranged/robustness generation (l.383) cover value-range edges on the test-data side.
**Recommendation:** None new. When WP-QUA-03 fixtures are written, mirror the GAPS row's categories (malformed, repeated, range, escape, case-sensitivity) in the rejection tests so the corpus is systematic rather than ad hoc.

### F-04 — GAPS row 4: populated persistence inspection / migration assumptions
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Persistence and migration" (l.8): empty shipped `master.db`; "test ID and deletion assumptions" unproven.
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` WP-PRJ-03 "Schema migration with explicit confirmation" (l.326), WP-PRJ-02 diff-stable storage (l.325); `E:\projects\UDS_Simulator\Unit\design\SDD-003-data-model.md` l.8 revision note: draft corrections for DR-15–18 and DR-13 (authored-data preservation, replay closure).
**Assessment:** The row is investigation-specific (reverse-engineering a shipped SQLite schema). Its transferable residue — "identity and deletion assumptions need testing on populated data" — is already structurally provided for in ectt: migration confirmation, DR-17/DR-18 corrections demanding delete-and-regenerate recovery and replay closure. No ectt action derives from the VectorCAST database itself.
**Recommendation:** None. (RV-03 covers the schema-comparison side.)

### F-05 — GAPS row 5: coverage format and MC/DC algorithm validation
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Coverage format and MC/DC algorithm" (l.9): known expressions including short-circuit and threshold cases; validate decoder and pair semantics; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §9 (l.265): "independently reviewed truth-table fixtures and per-condition independence pairs."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\design\SDD-002-interfaces.md` §7.1 acceptance fixtures (l.315–317): "equal true/false outcome flags with different independence results, short-circuit/masking pairs, missing backend evidence, incompatible merges, and zero/unsupported denominators"; `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` WP-COV-05 (l.422) and R-4 masking-vs-unique-cause risk (`E:\projects\UDS_Simulator\Unit\ADR-001-architecture-decisions.md` l.297).
**Assessment:** ectt's seam contract already mandates exactly the fixture classes the vcast design review asks for, in more operational detail. This is the strongest alignment in the whole comparison and dates from the DR-12 correction.
**Recommendation:** None new; the only dependency is organizational — ADR-004 must close before WP-COV-01/05 can execute those fixtures (`PLAN-001` l.160).

### F-06 — GAPS row 6: UI/workflow observation of the incumbent
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "UI, workflows and integrations" (l.10): observe representative workflows on an authorized installation.
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` L5 register, 22 WP-GUI packages (l.462–483) and P2 gate (l.675): GUI authors data, executes, inspects results/coverage, launches reports.
**Assessment:** Investigation-internal. ectt does not need to observe VectorCAST's UI; its own UI workflow verification is fully allocated. Observation of the incumbent is at most competitive research, outside the baseline's scope.
**Recommendation:** No ectt action.

### F-07 — GAPS row 7: measure compiler/target/performance on the exact configuration
**Class:** risk
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Compiler, target and performance" (l.11): "Select an actual pilot and target, measure layout, runtime, memory and coverage behavior on the exact configuration"; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §8 (l.255): "Performance targets must be calibrated on the pilot. Initial engineering targets, not measurements."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\docs\reviews\2026-10-15-document-review.md` DR-06 (l.72–78): the 30-second target uses undefined "typical developer hardware"; own-source coverage and memory limits only require a documented threshold "without choosing one" — still open, no correction note addresses it; `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` WP-CORE-05 (l.320, NFR-030/040/150, P2).
**Assessment:** Both sides record the same truth — numbers written before a pilot exists are guesses — but ectt's DR-06 is an open baseline defect while the vcast proposal resolved it by explicitly labelling its targets uncalibrated. Until DR-06 is corrected, NFR-030/040/150 acceptance conditions can be chosen post hoc by the implementer, which weakens the P2 gate.
**Recommendation:** Correct DR-06 before WP-CORE-05 starts: name reference hardware, workload and measurement method, or explicitly reclassify the NFR targets as uncalibrated engineering targets to be pinned at P2 entry (the vcast §8 wording is a usable model).

### F-08 — GAPS row 8: requirements and qualification evidence
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/GAPS.md` row "Requirements and qualification" (l.12): "no qualification follows from this investigation"; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §9 (l.267): qualification "is a separate program… Supporting traceability or coverage does not confer qualification."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\ADR-001-architecture-decisions.md` §1.2–1.3 (l.40–50): "be qualifiable, not qualified"; Tier 1 in v1.0, Tier 2 in v1.1, Tier 3 not a shipped artifact; §1.6 QUA mapping (l.69–84); QUA-090 / WP-QUA-07 no-overclaim (`PLAN-001` l.533); R-10 (`ADR-001` l.303).
**Assessment:** The vcast proposal's qualification disclaimer and ectt's accepted tier model are the same position derived independently: qualification is a funded program, evidence discipline starts immediately, and overclaim is the liability. No conflict; ectt is if anything more operationally developed (QUA-010..100 mapped to phases).
**Recommendation:** None. Keep both statements consistent if any vcast-derived text is ever quoted in ectt public material.

### F-09 — Codex 1: compilation database lacks a link plan
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` decision table (l.16): "Codex 1: compilation database lacks link plan — Accepted. Explicit LinkPlan required; automatic build-system capture is later."; contract sketch `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §3 "HostProfile and LinkPlan" (l.112).
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` ING-010..040 (l.122–128): ingestion covers per-TU compile invocation only — no link description; HAR-120 (l.242) / `PLAN-001` WP-GEN-05 "Link closure and unresolved reference reporting" (l.372) resolves harness externals at generation time.
**Assessment:** Partial. ectt can discover missing link inputs only indirectly when the harness link fails (WP-GEN-05 reporting, WP-BLD-01). The vcast review's point is subtler: *which* real dependencies replace stubs is a decided input, not a discovered accident, and it must be captured as an explicit validated artifact before builds run. ectt's HAR-120 satisfies correctness (nothing unresolved silently) but not provenance (no record of the intended link closure to compare against when builds break).
**Recommendation:** Add to WP-GEN-05's acceptance an explicit, persisted link-closure record (stubbed vs linked-real per external, with source of the decision), even if the P1 ingestion path stays compile-database-only. No SRS change required; HAR-120 already demands the reporting half.

### F-10 — Codex 2: fresh dependency resolution over caches
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.17): "Fresh dependency resolution first; unknown completeness forces rebuild. No speculative dependency cache added."; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §9 (l.263): cache-invalidity fixtures must include "shadowing-header creation/deletion, `__has_include` changes and library replacement."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` ING-100 (l.140, Should/P2): "detect that the ingested project model is stale… and re-ingest **or warn**"; `PLAN-001` WP-ING-03 (l.345); §6.4 corpus (l.629–634) contains no header-shadowing / include-change fixture.
**Assessment:** Partial, and the direction of the residual is over-optimism: ectt's staleness rule permits *warning* and continuing on a possibly stale model, while the vcast disposition forces rebuild when completeness is unknown. A stale analysis model silently feeding harness generation is exactly the false-negative direction §6.4 says "fails silently in the direction of an over-optimistic result."
**Recommendation:** Two documentation-level hardenings: (a) elevate the ING-100 acceptance (WP-ING-03) to require re-ingestion when staleness cannot be bounded, with "warn-only" limited to explicitly declared schedule-only paths; (b) add shadowing-header and `__has_include` cases to the §6.4 reference corpus / WP-ING-03 fixtures. Consider the Should→Must promotion of ING-100 as an SRS decision.

### F-11 — Codex 3: executable/test-revision mismatch before every run
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.18): "Initial test data/assertions/stubs compile into harness; CompiledTestManifest checked before every run."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` HAR-090 (l.236, generated-code header carries tool version + source model), HAR-110 (l.240, interface-change staleness), CBT-010 (l.426, re-execute without regeneration), CBT-070 (l.438, test staleness on interface change); `E:\projects\UDS_Simulator\Unit\PLAN-001-specification-analysis-and-work-breakdown.md` WP-GEN-04 / WP-CBT-01 (l.371, l.414).
**Assessment:** Partial. ectt's staleness checks key on the *interface*, not on the binding between a compiled artifact and the test-data revision it was built from. Editing a test's data values (not the interface) can leave a previously built harness binary in place; nothing in SRS/SDD requires the runner to verify the artifact matches the current case revision before executing. The vcast disposition closes exactly this window.
**Recommendation:** Add a contract point to WP-EXH-01/WP-CBT-01 acceptance (and consider a `TOOL-CBT` or `TOOL-EXE` requirement): every run binds to a content-identified test-revision/build-artifact pair, and a mismatch is rejected (or forces rebuild) rather than executed. Fits the existing S3 `run_id` + provenance model in `design/SDD-002-interfaces.md` l.222–236.

### F-12 — Codex 4: run attempt exists before build; artifact optional until success
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.19): "RunAttempt exists before build; artifact optional until success; evaluation records retain exact evidence/policy."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` QUA-060 (l.692, reproduction info in every generated artifact, P4) and NFR-090 fail-safe termination (`PLAN-001` WP-CORE-02, l.317); `design/SDD-002-interfaces.md` S3 `run_id` (l.222–236). No ectt document states that a build *failure* produces a recorded, inspectable attempt with no artifact.
**Assessment:** Partial. ectt's provenance story starts from generated artifacts (QUA-060) and persisted result sets (S3); a failed build is an error path (NFR-090), not a first-class record. The vcast disposition makes the attempt the unit of history so build failures are auditable with the same identity discipline as runs. For a tool whose users debug compiler/integration problems, that history has real value and it is cheap to specify now.
**Recommendation:** Extend the WP-CORE-04 provenance record (or S3's contract points) with: attempt records are created at build start, persist on build failure with diagnostics, and reference the optional artifact only after success. Documentation-level; no new component.

### F-13 — Codex 5: unknown coverage denominator
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.20): "Valid mapped scope only; missing/unsupported scope separate and whole-project completeness withheld."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\design\SDD-002-interfaces.md` §7.1 (l.293–301): summaries report inventory / instrumentable / demonstrated / not_demonstrated / unmeasured / unsupported separately; primary percentage is demonstrated over *all in-scope inventory conditions*; the measured-only percentage "must label that denominator"; "A zero denominator is N/A"; §7.2 (l.324–326): "**`unmeasured` is not `uncovered`.** … Collapsing it into either of the other two is the most dangerous misreport the tool can make"; S1 decision inventory (l.146–151); `SRS-001-requirements.md` COV-080 (l.402).
**Assessment:** ectt already encodes the disposition, and goes further (labeled dual denominators, N/A rule, inventory-based primary denominator). The key check requested passes: SDD-002 S4 fully covers Codex 5.
**Recommendation:** None. Cite `SDD-002` §7.1 as the authoritative resolution if this disposition is ever reused.

### F-14 — Codex 6: reproducibility defined (recipe vs byte-identical)
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.21): "Recipe replayability separated from byte-identical builds; clean-directory comparisons required."; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §9 (l.263).
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` SEC-030 (l.772): reproducible build = "functionally identical artifacts" with a documented procedure — i.e., recipe replayability, deliberately not byte-identity; SEC-040 (l.774) pins + hashes; `PLAN-001` WP-SEC-02 (l.536), §6.4 golden-file "run twice, on two machines, and diff" (l.642–645) and P1 gate "byte-identical output across two runs" (l.674), P4 gate auditor-reproducible archive (l.677).
**Assessment:** ectt's split matches the disposition term for term: SEC-030 is the recipe claim, golden-file/P1 output determinism is the byte claim for *reports and project files*, and WP-PRJ-05 (l.328) verifies archive reproduction. The key check passes.
**Recommendation:** None. Minor: when WP-SEC-02 fixtures are defined, include a clean-directory build comparison (not just two runs on one machine) to mirror the vcast acceptance.

### F-15 — Claude F1: embedded-to-host portability recorded as data (HostProfile)
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.22): "HostProfile records transformations and ABI gaps; concrete architecture/ABI examples… are not adopted as universal facts. No target-equivalence claim."; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §3 (l.112).
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` TGT-070 (l.372, unmodified host/target execution) / `PLAN-001` WP-EXT-04 parity (l.403); `design/SDD-005-external-integration.md` §6.3 capability probing recorded "in the run evidence" (l.730–741); S3 `execution` metadata (`design/SDD-002-interfaces.md` l.226–227).
**Assessment:** Partial. ectt commits to host/target parity *behavior* but has no first-class record of *why* a host run differs from the target (ABI widths, struct layout, bit-field packing, native `long long` vs target types) — the information an assessor needs to judge whether host evidence transfers. SDD-005 §6.3 probes capabilities per toolchain, which is the right hook; the ABI-gap inventory itself is unowned. Low priority until P3, but cheap to reserve a home for now.
**Recommendation:** When WP-TCH-01 defines the compiler configuration format, reserve an optional host-vs-target divergences section (populated during WP-EXT-04 parity work and rendered in reports). No SRS change required; it is a TCH descriptor extension.

### F-16 — Claude F2: inaccessible state → observability gate, not automatic inclusion
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.23): "Accepted observability gate; deferred inclusion rewriting. Public API sequences may expose behavior; inaccessible direct state checks rejected. Pilot must fit rather than automatically adding UUT inclusion mode."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` PAR-080 (l.178, static functions made testable without modifying user source), HAR-030 (l.222, *optionally* expose statics), PAR-090 (l.180, macro-obscured interfaces recorded); `PLAN-001` WP-GEN-03 "Static exposure and integration-scope harness" (l.370) and WP-ANA-06 testability classification (l.341); `design/SDD-002-interfaces.md` S1 annotations "never omitted" (l.145).
**Assessment:** ectt's design already embodies the gate: exposure is opt-in (HAR-030), testability is classified and reported (PAR-080/090, WP-ANA-06), and unhandled constructs surface as annotations instead of silent failure. The vcast disposition's restraint (fit the pilot, don't auto-add inclusion modes) is the same conservative posture §6.4's "negative testing" paragraph institutionalizes.
**Recommendation:** None.

### F-17 — Claude F3: stub symbol/prototype evidence
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.24): "LinkPlan describes inputs/flags/runtime; symbol tables and link maps validate resolution but cannot alone recover the entire plan. Compile against shared declarations; reject unsupported bindings."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` STB-030 (l.252, per-stub standalone declarations) with the `design/SDD-002-interfaces.md` S1 contract point "stub must compile standalone (TOOL-STB-030)" (l.141); HAR-120 unresolved-reference reporting (l.242) / WP-GEN-05 (l.372); `E:\projects\UDS_Simulator\Unit\ADR-001-architecture-decisions.md` l.108 + DR-26 correction (l.7, l.111): wrapping validated only for external unresolved calls, per compiler/linker fixtures; `design/SDD-005-external-integration.md` §5.2.1 link seam is toolchain-specific (l.340) and §6.3 probes it per vendor (l.737).
**Assessment:** ectt's split — declarations from the analysis model, resolution proven at link time, unsupported constructs flagged (STB-130/WP-GEN-09, l.376) — is the same evidence strategy as the disposition, with the DR-26 correction already narrowing the wrapping claim exactly as Codex/Claude asked. The key check passes.
**Recommendation:** None.

### F-18 — Claude F4: crash profiles and profile-flush safety
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.25): "No promise of crash profiles. Exception-handler/profile flush safety was not validated, so it is not required in the MVP."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` EXE-030 (l.342, crash isolation); `design/SDD-002-interfaces.md` S3 `infrastructure_faults` (l.244–245) and S4 `unmeasured` (l.324–326); `PLAN-001` WP-COV-02 merge semantics (l.419).
**Assessment:** Partial. ectt correctly never promises coverage from a crashed run, and its `unmeasured` state keeps missing measurement visible. But no document states the admission *rule*: when a run crashes after partially flushing a profile, is that partial profile merged, quarantined, or discarded? Silence here lets an implementation do the optimistic thing (merge partial data) — the exact over-claim direction SDD-002 §7.2 forbids for denominators.
**Recommendation:** Add one contract sentence to WP-COV-02 acceptance: coverage artifacts from runs whose outcome is `error`/`timeout`/crash are retained but excluded from aggregate merges unless explicitly labeled per-run (consistent with §7.1's "Missing measurement stays visible in per-run provenance", l.311–312).

### F-19 — Claude F5: premature exit(0) and modal-error handling
**Class:** gap
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.26): "Finalized per-attempt result required; exit zero alone insufficient. Runtime-specific no-dialog settings and Job Object handling must be validated before selecting exact flags/APIs."; FR-06 (`vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` l.236) lists "premature exit(0)… modal-error… cases remain distinguishable where observable."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\SRS-001-requirements.md` EXE-030/040/060 (l.342–348: crash isolation, timeout, non-zero CI exit); `design/SDD-002-interfaces.md` S3 (l.246: "`timeout` is a distinct outcome from `fail`"); `PLAN-001` WP-EXH-02 (l.397).
**Assessment:** Partial. ectt distinguishes crash/timeout/fail, but nothing requires distinguishing *completed pass* from *process exit 0 before the harness finished* — a Windows-realistic failure mode for generated harnesses (runtime abort paths, modal DLL-load error boxes swallowed by CI). The vcast disposition's rule (completion marker required; exit zero alone insufficient) is the missing contract point, and its warning (no-dialog flags/Job Objects must be validated per runtime before selection) is a concrete fixture for WP-EXH-02 that ectt currently lacks.
**Recommendation:** Add to WP-EXH-02: (a) harnesses emit a completion record; a run whose process exits 0 without it is classified `error`, never `pass`; (b) an acceptance fixture proving modal-error suppression / child-process cleanup on real Windows (aligning with §6.4's target-in-the-loop realism, l.652–655).

### F-20 — Claude F6: libclang vs LibTooling feasibility
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` (l.27): "Feasibility option, not mandatory replacement… Keep backend boundary, investigate in M0, retain C++/LibTooling recommendation pending evidence."
**ectt baseline evidence:** `E:\projects\UDS_Simulator\Unit\ADR-001-architecture-decisions.md` §2.4 (l.143–152): Python/libclang now, JSON model "inviolable", focused C++ LibTooling executable only if CFG needed; §2.5 spike-01 held at 151k LOC (l.160–162); DR-21 correction note (l.7) reconciling the LibTooling rejection with `design/SDD-005-external-integration.md` §6.2 item 3 (l.726–728: in-process linkage rejected, pinned JSON-emitting executable allowed); `design/SDD-002-interfaces.md` S1 rule (l.95–101); R-01/R-5 (`ADR-001` l.294; `PLAN-001` l.761).
**Assessment:** The vcast disposition is structurally the ectt accepted position: keep the backend seam, treat LibTooling as a measured fallback, don't re-decide without evidence. ectt has already executed the feasibility spike (WP-SPIKE-01) that the vcast plan only schedules for its M0. The key check passes: seam S1 backend-independence is exactly the boundary Claude F6 asks to keep.
**Recommendation:** None for the decision. One watch item: the vcast disposition flags *packaging cost* of an LLVM-linked worker as unmeasured; ectt's WP-SPIKE-03 (l.308) packaged PySide6+libclang but never a C++ LibTooling binary. If R-5's fallback ("Bring the C++ LibTooling analyzer forward") is ever triggered, repeat the packaging spike for that artifact before committing.

### F-21 — Unknown 1: complete EDG/parser/instrumentation algorithms
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` l.95: "Complete EDG/parser behavior, source rewriting rules and instrumentation algorithms" unknown; l.102: prevents claiming a clone, not an original proposal.
**ectt baseline evidence:** `design/SDD-005-external-integration.md` §5.7 (l.585–589): "an external engine proposes input vectors; the tool then compiles and runs them with the *user's* compiler… The engine never enters the evidence chain"; §6.1 floors (l.695–699); `PLAN-001` l.160 (ADR-004 open before COV-01).
**Assessment:** VectorCAST-specific. ectt's architecture deliberately avoids owning parser/instrumenter algorithms (compiler-provided coverage, user's toolchain), so this unknown costs ectt nothing directly. The residue — an open coverage-backend decision whose semantics must then be fixture-validated — is already tracked as ADR-004 plus F-01/F-05 above.
**Recommendation:** No ectt action beyond closing ADR-004 before COV-01 integration.

### F-22 — Unknown 2: full C++ mocking/interception mechanics
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` l.96: full C++ mocking/interception mechanics and language-construct support unknown (D11, `selected/vunit/include/vunit/mock.h`, untraced).
**ectt baseline evidence:** `design/SDD-005-external-integration.md` §1.2 (l.51): "Google Test and equivalent" is the wrong frame; `PLAN-001` WP-GEN-10 GoogleTest host-only P3 (l.377); `ADR-006-fork-or-build-fresh.md` headline: UTBotCpp's C++ GoogleTest output violates TOOL-HAR-060.
**Assessment:** VectorCAST-specific. ectt's scope decision (C-first, C++ frameworks host-only and never the default) was made and accepted; deep C++ interception is out of scope by design, so the unknown maps to a documented boundary rather than a risk. If C++ support ever expands, WP-GEN-10's compatibility matrix is the vehicle — matching the vcast disposition's "each capability has its own compatibility matrix" (PRODUCT_ARCHITECTURE §11, M4 row, l.296).
**Recommendation:** None.

### F-23 — Unknown 3: complete SQL schemas, migration rules, transactions
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` l.97: active SQL schemas, migration rules and cross-database transactions unknown (empty shipped `master.db`).
**ectt baseline evidence:** `ADR-002-project-data-format.md` l.112 (restricted YAML, scoped to authored project state, JSON seams preserved); `PLAN-001` WP-PRJ-01..03 (l.324–326).
**Assessment:** VectorCAST-specific. ectt's persistence is its own restricted-YAML store with explicit schema migration; nothing depends on recovering VectorCAST's databases. The transferable caution (populate-then-test migration, F-04) is already allocated.
**Recommendation:** None.

### F-24 — Unknown 4: host/target timing, overhead, robustness under execution failures
**Class:** risk
**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` l.98: "Actual host/target timing, overhead, resource use and robustness under execution failures" unknown; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §8 (l.255): budgets only after measuring the selected corpus.
**ectt baseline evidence:** `docs/reviews/2026-10-15-document-review.md` DR-06 (l.72–78, open: quantitative criteria underspecified); `PLAN-001` WP-CORE-05 (l.320), §6.4 target-in-the-loop (l.652–655: "a simulator will not reproduce [flash failure, watchdog reset, semihosting] faithfully"), WP-EXT-06 footprint documentation (l.405).
**Assessment:** This is the one unknown that is fully applicable to ectt's own validation planning, and ectt already knows it (DR-06 open; §6.4 names the physical-board prerequisite for P3). The residual risk is sequencing: WP-CORE-05 starts at P2 while its acceptance numbers are unpinned, and P3's target work depends on hardware budgeting that §6.4 says must be planned ("hard prerequisite for P3").
**Recommendation:** Fold DR-06 resolution (F-07) and the P3 physical-board budget into the same calibration step; do not let WP-CORE-05 exit with post hoc chosen thresholds.

### F-25 — Unknown 5: runtime activation of optional packages/integrations
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` l.99: "Runtime activation of optional packages and integrations" unknown.
**ectt baseline evidence:** `PLAN-001` WP-PLG-02 "Extension discovery and load failure isolation" (l.524, PLG-070/080); WP-AIF-02 optionality/separability/default-off (l.492).
**Assessment:** Mostly VectorCAST-specific (licensing-dependent feature activation). ectt's analogue — optional components that load or fail safely behind extension points — is already specified. The GAPS/unknown moral that activation behavior must be *observed*, not assumed, is covered by PLG-080's load-failure obligation and ADR-008's "provider claims remain unverified until exercised" (`PLAN-001` l.158).
**Recommendation:** None.

### F-26 — Unknown 6: product-level qualification/acceptance evidence for the supplied build
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` l.100: "Product-level qualification/acceptance evidence for this exact supplied build" unknown; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §9 (l.267): "The analyzed product advertises safety-related workflows; its claims do not transfer to this new implementation."
**ectt baseline evidence:** `ADR-001-architecture-decisions.md` §1.1 (l.34–36): VectorCAST ships DO-178C/DO-330 packages, Cantata is SGS-TÜV certified — an open-source project "cannot match independent third-party certification"; §1.2 reframe (l.40–42); R-10 overclaim risk (l.303); QUA-090/WP-QUA-07 (`PLAN-001` l.533).
**Assessment:** VectorCAST-specific unknown, but its product consequence is the foundation of ectt's whole qualification posture: vendor certifications of incumbents transfer to nothing, so ectt sells "qualifiable" discipline (Tier 1/Tier 2) instead. The two documents agree; ectt's position is more developed.
**Recommendation:** None (adoption-competitive consequence already tracked as R-7, `PLAN-001` l.763).

### F-27 — Licence and evidence-segregation risk: F-16 unresolved while vcast-findings holds proprietary extracted assets in the AGPL repository
**Class:** risk
**vcast-findings evidence:** `vcast-findings/README.md` l.21: "`selected/`: 100 selected extracted files, **including binaries, source and shipped documentation**. These are investigation evidence, not new-product assets"; l.30: "Scope: static investigation… No VectorCAST target execution… is claimed"; `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` §Design boundary (l.106): "Extracted VectorCAST source, binaries and templates… are not proposed product dependencies or distributable assets"; `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §12 (l.307): "A new product repository should be separate from this REA investigation repository."
**ectt baseline evidence:** `PLAN-001` F-16 (l.119–129): LIC-010 (Must, P1) requires a permissive licence while `LICENSE`/`LICENSEES` are AGPL-3.0 — "the only finding that is already false in the repository"; `docs/reviews/2026-10-15-document-review.md` DR-03 (l.48–54, HIGH, open); `ADR-001` correction note (l.7): "the project license remains unresolved (LIC-010 versus repository AGPL-3.0), with no change to LICENSE"; `design/SDD-005-external-integration.md` §3.2 (l.137–161): ADR-005 "should be written before the dependency set is frozen"; `PLAN-001` R-8 (l.764) and WP-PKG-07 (l.520, P1, LIC-010 enforcement).
**Assessment:** Two compounding risks. (a) **Sequencing:** F-16/DR-03 remains a live blocker in every baseline document; the vcast investigation's own experience reinforces the cost asymmetry — the vcast team refused to run an unauthorized installation and scoped the whole investigation around what static evidence permits, showing how sharply legal boundaries constrain tooling work. Ectt's contributor base is still small, which is the cheapest moment to relicense (R-8 fallback: "relicense while the contributor set is still small"). (b) **Segregation:** the ectt repository now contains extracted proprietary VectorCAST binaries and source under `vcast-findings/` while declaring AGPL-3.0 and permissive-licence ambitions; the investigation's own design boundary demands the product repository be separate and the assets non-distributable. Nothing in the ectt baseline records a rule preventing vcast-findings content (schemas, recovered source, templates) from leaking into `src/` or the docs. Read-only discipline held during this review, but the repo-level exposure (e.g., a public GitHub remote — ADR-001 l.14 references a published documentation site) needs an owner decision.
**Recommendation:** (1) Resolve ADR-005/F-16 **before further implementation** — it is P1 (WP-PKG-07), it is the only finding already false in the repository, and every dependent decision (SDD-005 §4–§8 recommendations, SBOM, dependency admissibility) assumes LIC-010 wins. (2) Record an explicit no-import/provenance rule: no file, schema, template or symbol list under `vcast-findings/` may be copied, transcribed, or used as a product dependency or specification source; cite-only with the investigation's own boundary statement. (3) Obtain a legal posture on distributing a public repository containing extracted proprietary artifacts, or move `vcast-findings/` to a private location — an owner decision, flagged here because both source documents say the separation is mandatory.

### F-28 — REVIEW_NOTES corrections and process parity
**Class:** aligned
**vcast-findings evidence:** `vcast-findings/deep-specifications/REVIEW_NOTES.md` (l.5–9): reviewers read partially ("Claude explicitly reported partial reading and did not inspect coverage function bodies"); corrections to the raw Claude report ("SBF means stub by function; `VCAST is Done` is termination output"; "The reported 26-condition constant alone does not establish a product-wide limit"); "Inferred event-limit scope, parser risks and generated-code behavior remain unverified. The raw reports remain unchanged as historical records."; `vcast-findings/deep-20261027/REVIEW_DECISIONS.md` l.3: "The revised document has not received another independent review."
**ectt baseline evidence:** 2026-10-17 correction notes carry the identical epistemic pattern: `ADR-001` l.7, `ADR-002` l.112, `ADR-006` (header note), `ADR-008` (header note): "The 2026-09-19 acceptance is historical; these corrections do not assert new approval or implementation validation"; `design/SDD-003-data-model.md` l.8 (draft corrections for DR-15–18/DR-13); `PLAN-001` l.3 (v0.2 reconciled) and l.26 ("Decision acceptance does not establish implemented behavior").
**Assessment:** Investigation-internal, and materially reassuring rather than concerning: both sides refuse to let unverified reviewer inference become baseline fact, both preserve raw records unchanged, and both mark corrected documents as not independently re-reviewed. The vcast corrections themselves (terminology, a termination marker, a condition-count constant) have no ectt analogue — except one: ectt must resist importing any vcast-derived numeric claim (e.g., condition-count limits) as fact; the 26-condition incident is a worked example of why. On the ectt side, the DR correction notes address DR-08/10/13/15–18/21/24–32; DR-01–07, DR-09, DR-11, DR-12, DR-14, DR-19/20, DR-22/23 and above all DR-03 remain open without correction notes.
**Recommendation:** No action beyond the standing rule: if any vcast-findings number is ever cited in an ectt document, cite it as unverified static-analysis inference with the REVIEW_NOTES caveat attached.

---

## 3. Summary

- **Counts (28 findings):** aligned 17 · gap 8 · risk 3 · conflict 0. No vcast-findings disposition contradicts an accepted ectt decision; every gap is additive (an acceptance fixture, a contract point, or a reserved field), not architectural.
- **Strongest alignments:** Codex 5 (coverage denominator) is fully anticipated by `SDD-002` §7.1 with stricter detail; Codex 6 (reproducibility) maps onto SEC-030/040 + §6.4; Claude F6 (libclang/LibTooling) is the already-accepted ADR-001 §2.4 position, spike evidence included; the qualification posture (G8/U6) is the same "qualifiable, never qualified" stance derived independently on both sides.
- **Most decision-relevant — licence:** F-16/DR-03 (LIC-010 vs AGPL `LICENSE`) is still open in every document, and the repository now simultaneously hosts an AGPL-licensed product baseline and extracted proprietary VectorCAST binaries/source (`vcast-findings/selected/`) whose own design boundary demands a separate product repository. Resolve ADR-005 before more implementation; record the no-import rule; get a legal posture on the public-repo exposure.
- **Most valuable cheap gaps:** the vcast review's four run-integrity dispositions translate directly into ectt acceptance criteria — artifact-binding check before every run (F-11/C3), attempt-recorded-before-build (F-12/C4), completion-marker vs premature exit(0) plus modal/no-dialog validation (F-19/CL5), and a crashed-run coverage admission rule (F-18/CL4). All are one-contract-point changes to WP-EXH-01/02, WP-CBT-01 and WP-COV-02.
- **Planning gaps to schedule:** harness-vs-reference-test agreement inside WP-QUA-03 (F-02); DR-06 quantitative calibration before WP-CORE-05 exits (F-07/F-24); ING-100 staleness hardening plus shadowing-header/`__has_include` fixtures (F-10/C2); an explicit link-closure record in WP-GEN-05 (F-09/C1).
- **Process parity:** both sides use the same correction discipline (raw records preserved, corrections dated, no re-review claimed); vcast-finding numeric claims must stay quarantined as unverified inference if ever cited (F-28).
