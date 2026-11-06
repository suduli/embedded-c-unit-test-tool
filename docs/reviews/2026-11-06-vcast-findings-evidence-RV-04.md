# RV-04 — Coverage & MC/DC cross-review: vcast-findings vs ectt baseline

Reviewer: RV-04 (of six parallel cross-review agents). Date: 2026-11-06.
Scope: static findings only — no code inside `vcast-findings` was executed and no file outside the single output below was modified.

Inputs (vcast-findings side): `vcast-findings/deep-specifications/COVERAGE_AND_IO.md`, `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` (D4, D8, boundary 5), `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §5–§6, `vcast-findings/deep-20261027/cover_models.html.txt`, the five MC/DC documentation extracts under `vcast-findings/deep-specifications/text/`, and `vcast-findings/selected/IO/c_cover.h`.

Baseline (ectt side): `design/SDD-002-interfaces.md` (S3, S4, §3), `design/SDD-005-external-integration.md` (§5.5, §6.1–§6.3), `SRS-001-requirements.md` (TOOL-COV-*, TOOL-TCH-060/070, TOOL-TGT-050/090), `PLAN-001-specification-analysis-and-work-breakdown.md` (§5.5 COV work packages, §6.4, risk register).

---

### F-01 — MC/DC variant (masking vs unique-cause) is already data in ectt
**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/text/Use Masking MC DC.htm.txt` lines 5–8: masking MC/DC "as defined in the FAA CAST Position Paper-6" for DO-178B/C; "This option requires reinstrumentation after its value has changed"; `VCAST_VCAST_MASKING_MCDC True | False`, default False (unique cause otherwise).
- `vcast-findings/deep-20261027/cover_models.html.txt` lines 188–192 and 244–245: `masking_mcdcbool` is a per-file attribute of the instrumentation, alongside `max_mcdc_conditionsint` — the variant is recorded as instrumentation metadata, not a report-time choice.
- `vcast-findings/deep-specifications/COVERAGE_AND_IO.md` line 7: masking vs unique-cause "requires reinstrumentation after changes".

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 260–261 (S4): `"mcdc": { "form": "masking", "mechanism": "gcc -fcondition-coverage", "gap_to_unique_cause": "..." }` — the variant is a first-class data field with a declared gap field.
- `design/SDD-002-interfaces.md` lines 321–323 (§7.2): "`mcdc.form` is data. Every renderer is obliged to display it."
- `design/SDD-002-interfaces.md` lines 66–67 (§3): unknown MC/DC form enum values "fail closed; they are never coerced to a known value".
- `SRS-001-requirements.md` lines 398 (TOOL-COV-060: state form and mechanism in every report) and 404 (TOOL-COV-090: support unique-cause or document the precise gap); `PLAN-001-specification-analysis-and-work-breakdown.md` line 422 (`WP-COV-05` MC/DC measurement and form declaration) and line 427 (`WP-COV-10` unique-cause or documented gap).
- `design/SDD-005-external-integration.md` lines 468–470 (§5.5.1): both open-source backends implement masking, not unique-cause; TOOL-COV-060 is what states it.

**Assessment:** S4 declares exactly what the VectorCAST evidence shows must be data — and more: VectorCAST stores the variant per instrumented file; ectt additionally records `mechanism` and `gap_to_unique_cause` and fail-closes on unknown forms. VectorCAST's "reinstrumentation after change" rule corresponds to S4 §7.1 line 303–305's rule that merges are only valid with identical MC/DC form and build/instrumentation configuration. The one structural difference: VectorCAST *selects* the variant at instrumentation time (its own instrumenter); ectt *inherits* it from the compiler backend (both masking per SDD-005 §5.5.1) — so ectt has no user-facing variant switch to specify, only a declaration duty, which TOOL-COV-060 / WP-COV-05 discharge.

**Recommendation:** No change required. When `WP-COV-05` lands, ensure the declared `form` is derived from probed backend behavior (not assumed "masking" for every version) and that an unexpected backend form is a diagnostic, reusing the §3 fail-closed rule.

---

### F-02 — Covered rows vs satisfied pairs are separate quantities in both models
**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/text/Understanding MC DC Analysis.htm.txt` lines 5–7: the equivalence-pair matrix shows "both the static pair analysis and the pair coverage achieved"; "An asterisk next to a row number indicates that the row has been covered"; Pa/Pn summary lines reflect satisfied pairs. Lines 30–40 (the `a && b` example): 4 covered rows but "the pair coverage is 1 of 2 pairs satisfied" and "5/6 branch outcomes" — three distinct quantities (rows, branch outcomes, pairs).
- `vcast-findings/deep-20261027/cover_models.html.txt` lines 1825–1845 (MCDCDecision): the four MC/DC checks; independence pairs defined as two rows differing in one condition's value and the decision outcome, "or irrelevant due to masking"; "a condition is covered if and only if one or more of its independence pairs are covered". Lines 1912–1931 (MCDCPair with `row1`/`row2`/`matters`/`covered()`), 1942–1973 (MCDCRow), 1750–1777 (MCDCCondition `covered_pairs` / `get_covered_pair`). Lines 987–1004: separate metric families for `mcdc_branches`, `mcdc_pairs` (covered/uncovered/aggregate/annotations).
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` line 22 (D8): "distinct source/instrumented entities, branches, MC/DC conditions, decisions, pairs, rows, results and merge strategies."

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 280–291 (§7.1): per-condition `independence` (`demonstrated` / `not_demonstrated` / `unmeasured` / `unsupported`); "True/false flags record exercised outcomes only; neither two true flags nor decision outcome coverage proves independence"; `demonstrated` requires evidence including the witness pair.
- `design/SDD-002-interfaces.md` lines 306–308: "Never OR ordinary outcome flags into independence." Lines 293–301: summary counts separate inventory / measured / demonstrated / not_demonstrated / unmeasured / unsupported / justified.

**Assessment:** The core VectorCAST invariant — covered rows (outcome observations) and satisfied pairs (independence proofs) are different quantities, and only pairs prove condition coverage — is exactly S4's rule that outcome flags never OR into independence and that demonstration requires a witness pair under the declared form. S4 is stricter than VectorCAST's API surface: it demands traceable evidence (vectors or a digest-bound `backend_assertion`, lines 288–291) where VectorCAST exposes only the resulting pair/row objects. One modelling difference: VectorCAST publishes the full candidate pair matrix (rows as reportable entities, `MCDCRow`, `num_rows`, MCDC-coverage line 1880–1881); S4 records the verdict and witness pair per condition but not the row/truth-table inventory as data, so a report cannot reconstruct *why* a pair was candidate.

**Recommendation:** Keep S4 as is for v1; if assessor-facing pair matrices are later needed (VectorCAST's annotated-source + matrix view), add rows as optional evidence payload under §7.1 rather than a schema change to the verdict fields.

---

### F-03 — Merge contract vs VectorCAST's named merge strategies for source variants
**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-20261027/cover_models.html.txt` lines 896–906 and 1974–1984 (`CoverMergeStrategy` / `MergeStrategy`): when "combining results across different targets ... a line of source may be different in the translation unit than it is in the source file as written ... this happens when there is a macro on the line", five named strategies: `COUNT_UNIQUE_VARIANTS` (default), `COUNT_ALL_VARIANTS`, `COUNT_MACRO_VARIANTS`, `IGNORE_VARIANTS`, `FILTER_BY_VARIANT`.
- Same file lines 93–96, 178–179 (`has_variance`): per-Branch/per-object flag that the translation unit differs from original source due to preprocessing.
- `vcast-findings/deep-specifications/COVERAGE_AND_IO.md` line 7 and `text/Use Masking MC DC.htm.txt` line 6: option changes (masking) require reinstrumentation — i.e. merge validity is instrumentation-configuration-bound.

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 303–313 (§7.1): "Merge only records with identical source/expression identity, condition mapping, MC/DC form, backend semantics and build/instrumentation configuration ... Incompatible records remain separate with a diagnostic." Lines 306–310: cross-run witness pairing only with full compatible vectors; never OR outcome flags.
- `design/SDD-002-interfaces.md` lines 315–317: acceptance fixtures "must include ... incompatible merges".

**Assessment:** S4's identity-keyed merge with keep-separate-plus-diagnostic is a valid, conservative resolution of the same problem VectorCAST solves with five enumerated strategies (it most closely matches `FILTER_BY_VARIANT` plus separation). However, ectt's contract never names the *source-variant* case (macro-expanded lines, preprocessed divergence) as a merge input, even though SDD-005 §5.5.1 (lines 481–491) shows macro-heavy guard expressions are exactly where Clang drops MC/DC instrumentation — so variant-differing MC/DC records will occur in practice. There is no declared behavior for two records of the same condition whose expressions differ only by macro expansion beyond the generic "incompatible" diagnostic, and no per-object `has_variance` equivalent in S4.

**Recommendation:** In S4 §7.1 (or a DSN-COV decision), state explicitly that macro/preprocessing variant differences make MC/DC records merge-incompatible (never silently `IGNORE_VARIANTS`), and consider a `variant_digest` within the source/expression identity so the diagnostic can name the variant mismatch. Defer enumerated strategies to a later ADR if a real need appears.

---

### F-04 — Per-backend condition-count capacity: data exists but probing is not required
**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/text/Set Absolute Limit for MC DC subconditions to 31.htm.txt` lines 5–7: "For C++, the absolute maximum number of MC/DC sub-conditions supported is 52 by default. Setting this option reduces the maximum number to 31" (`VCAST_UNSIGNED_LONG_MCDC_STORAGE`).
- `vcast-findings/deep-specifications/text/Optimized MC DC Storage Threshold.htm.txt` lines 6–7: storage threshold range 0–8, default 8 — a documented, configurable capacity, "not universal limits inferred from individual constants" (`COVERAGE_AND_IO.md` line 9).
- `vcast-findings/deep-20261027/cover_models.html.txt` lines 190–192 and 593–595 (`max_mcdc_conditionsint` per file), lines 338–340 and 741–743 (`max_instrumented_mcdc_conditions` per instrumented file), lines 1860–1862 (`max_conditions_exceededbool` per MCDCDecision: "True if this decision has more conditions than specified as allowed").
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` line 22 (D8) and `COVERAGE_AND_IO.md` line 9: these are declared per-backend/per-instrumentation capabilities.

**ectt baseline evidence:**
- `design/SDD-005-external-integration.md` lines 478 (table row "Conditions per decision: 64 (64-bit mask) / default 6, tunable") and 484–491 (§5.5.1): "Clang's default limit is 6 conditions per decision ... simply *drop out* of MC/DC instrumentation. The limit is tunable via the `cc1` option `-fmcdc-max-conditions`. (*Unverified:* ...) treat the availability as needing confirmation against the pinned `clang -cc1 --help`, not prose. TOOL-COV-080 ... is the mechanism that makes that requirement non-optional."
- `design/SDD-005-external-integration.md` lines 730–741 (§6.3): capability probing is enumerated for exactly three cases — QEMU exit propagation, sanitizer/profile runtime, link seam — plus the generalisation of TOOL-TCH-060; MC/DC condition limits are not in the probed list.
- `SRS-001-requirements.md` lines 204 (TOOL-TCH-060: declare per compiler configuration which metrics are achievable, refuse unsupported), 402 (TOOL-COV-080: report expressions exceeding compiler condition-count limits), 206 (TOOL-TCH-070 version detection); `design/SDD-002-interfaces.md` lines 269–270 (S4 `unmeasured` with reason "condition count exceeds compiler limit").
- `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` line 180 states the requirement ectt lacks: "The product must declare its own tested maximums from the pinned backend; current online documentation is not a guarantee for every installed release."

**Assessment:** The detection-and-report duty (TOOL-COV-080 → S4 `unmeasured`) and the raw capacity facts (Clang 6 / GCC 64) are covered, and SDD-005 already distrusts prose for the `-fmcdc-max-conditions` availability. But no requirement or work package obliges the tool to *probe and record* the effective maximum condition count (and limit-option availability) per pinned backend as run evidence — §6.3's probe list stops at three unrelated capabilities, and neither SRS nor `WP-COV-06` (PLAN line 423) asks for a declared/recorded maximum. VectorCAST's evidence shows capacity is option-dependent (52 vs 31; threshold 0–8) and per-file recorded — a version floor alone cannot express it, which is precisely SDD-005 §6.3's own argument.

**Recommendation:** Add MC/DC condition-limit availability (e.g. `-fmcdc-max-conditions` presence and the effective maximum) to §6.3's probed-capability list and to `WP-COV-06`'s scope; record the probed maximum in the S4 `mcdc` block (e.g. `max_conditions_probed`) so `unmeasured` reasons can cite the actual backend limit rather than a documentation claim.

---

### F-05 — Threshold/limit boundary prose is self-contradictory; boundary fixtures are mandated nowhere
**Class:** risk

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/text/Optimized MC DC Storage Threshold.htm.txt`: line 5 says bit-array for sub-condition counts "fewer than this value" and tree for "greater than this value" (equality unassigned), while line 8 says bit-array for counts "equal to or smaller than this value" — the same official page contradicts itself on equality at the threshold. `vcast-findings/deep-specifications/COVERAGE_AND_IO.md` line 9: "its prose differs on equality at the threshold, so exact equality behavior needs a fixture."
- `text/Use Optimized MC DC Instrumentation.htm.txt` lines 5–10: storage format (bit-array vs balanced tree) changes semantics of the produced data; "the result data generated is not compatible with the standard instrumentation model."

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 315–317 (§7.1 fixtures list): equal-flags/different-independence, short-circuit/masking pairs, missing backend evidence, incompatible merges, zero/unsupported denominators — no backend-boundary fixture (condition exactly at the compiler's maximum, at/around any tunable limit).
- `PLAN-001-specification-analysis-and-work-breakdown.md` lines 636–661 (§6.4): differential testing against gcov/llvm-cov output and negative testing (COV-080 refusal) are specified, but no boundary/equality fixtures; line 285 (`WP-COV-05` exit criterion) covers per-condition reporting only; line 423 (`WP-COV-06`) is uninstrumentable-expression detection without boundary cases.
- Counter-evidence that ectt already distrusts prose: `design/SDD-005-external-integration.md` lines 486–489 — the `-fmcdc-max-conditions` availability must be checked "against the pinned `clang -cc1 --help`, not prose."

**Assessment:** The VectorCAST threshold page is concrete proof that vendor prose can disagree with itself on an off-by-one at a semantic boundary — the exact failure class ectt's own `-fmcdc-max-conditions` unverified-note worries about. ectt's fixture list and §6.4 validation strategy currently contain no at-the-boundary cases (condition count exactly equal to the backend maximum; limit option flipped between builds producing incompatible profile formats), so the ambiguity VectorCAST exhibits would go undetected by the planned validation even though TOOL-COV-080's refusal behavior "fails silently in the direction of an over-optimistic result" (PLAN line 657–661).

**Recommendation:** Add to §6.4 and the `WP-COV-05`/`WP-COV-06` exit criteria: (a) a decision with condition count exactly at the probed backend maximum and one at maximum+1; (b) a rebuild with a changed limit/threshold option whose records must merge-invalidate (ties into F-03/F-04); (c) assert the exceeded decision appears as `unmeasured` with the limit in its reason.

---

### F-06 — Overflow/truncated profile data: S3/S4 vocabulary exists but profile completeness is not modeled
**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/COVERAGE_AND_IO.md` line 11: "Lines 868–894 show a buffered ASCII sink that latches a full state and writes an exceeded marker" (in `../selected/IO/c_cover_io.c`) — i.e. a coverage artifact can exist on disk yet be provably incomplete. Line 19: "Treat overflow and missing profiles as incomplete evidence."
- `vcast-findings/selected/IO/c_cover.h` lines 29–39: `VCAST_USE_STATIC_MEMORY`, `VCAST_MAX_MCDC_STATEMENTS`, `VCAST_MAX_COVERED_SUBPROGRAMS` — bounded static pools whose exhaustion is an expected, signalable condition, not an error crash.
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` lines 63–67 (boundary 6): retain "coverage availability and artifact completeness independently."

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 222–236 (S3): `partial`, `not_executed`, and `infrastructure_faults` ("flash failure, no output, reset, watchdog — DSN-EXT-070"); lines 241–245 (§6.1): "A subset run cannot be presented as a full one"; "A rig that fails to flash must never read as failing software."
- `design/SDD-002-interfaces.md` lines 269–273 (S4): per-decision `unmeasured` with reason; digest-bound `justified`.
- `design/SDD-002-interfaces.md` lines 364–365 (S5): `advisories` including `partial_run`.

**Assessment:** S3's `infrastructure_faults` covers "no output" (absent artifact) and S4's `unmeasured` covers per-decision compiler refusal — but neither model has a place for the VectorCAST-evidenced intermediate case: a *present but truncated/overflowed* coverage artifact (buffer latched full, exceeded marker written, counters dropped). `partial` in S3 is about test subset, not artifact completeness. A reader of the current S3/S4 could attach a complete-looking S4 to a truncated profile and produce an overclaim — the exact direction PLAN line 657–661 warns every coverage defect fails in. This is a schema gap, not a contract conflict: S4's own merge rule ("Missing measurement stays visible in per-run provenance", lines 310–311) needs a run-level completeness fact to be visible about.

**Recommendation:** Add to S3's execution metadata (or S4's file block) an explicit coverage-artifact completeness field — e.g. `coverage_artifact: { complete: true | truncated | missing, markers: [...] }` — populated by the backend adapter from decoder diagnostics (gcov/llvm-cov warnings, marker records); define that `truncated` forces affected decisions toward `unmeasured` and emits an S5 advisory, mirroring DSN-CBT-030's "fields, not report options" pattern.

---

### F-07 — Target coverage runtime: separability holds; capacity/loss controls are declared nowhere yet
**Class:** risk

**vcast-findings evidence:**
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` lines 57–61 (boundary 5): D4 shows "no heap, custom file/serial I/O, memory placement, explicit flush/clear, and condition-vector storage"; "separate instrumentation, on-target collection, transport, decoding and reporting. A host-only MVP can reuse a compiler coverage runtime. An embedded target requires a validated target runtime and collector with **declared capacity and loss behavior**."
- `vcast-findings/selected/IO/c_cover.h` lines 13–66: `VCAST_USE_STDOUT`/`VCAST_USE_PUTCHAR`/`VCAST_CUSTOM_STD_OUTPUT`/`VCAST_CUSTOM_FILE_OUTPUT` (output sink selection), `VCAST_USE_STATIC_MEMORY` + `VCAST_MAX_MCDC_STATEMENTS` (no-heap capacity), `VCAST_ENABLE_DATA_CLEAR_API` (`VCAST_CLEAR_COVERAGE_DATA`), `VCAST_DUMP_CALLBACK` (`VCAST_DUMP_COVERAGE_DATA`), `VCAST_FLUSH_DATA`, `VCAST_ATTRIBUTE_CODE` (memory placement); lines 730–780: buffered vs realtime MC/DC instrumentation-point declarations with explicit `num_conditions` parameters.
- `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` line 194: "A target coverage runtime should support fixed memory, explicit initialization/flush, custom transport hooks and overflow/loss indicators."

**ectt baseline evidence:**
- `design/SDD-005-external-integration.md` lines 512–524 (§5.5.3): the bare-metal path is libgcov via `-fprofile-info-section` (GCC ≥ 11) + `__gcov_info_to_gcda()` (GCC ≥ 12), "serialise counters out over the same one-way channel it uses for results"; lines 500–510 (§5.5.2): decoding is the toolchain's own gcov reader; merging happens in ectt's normalised model "above the raw format."
- `design/SDD-002-interfaces.md` lines 252–255 (S4 producer `CMP-COV`, isolates "Coverage backend (ADR-004)" per seam register line 44); S3 lines 226–227 record execution domain (`where: target`).
- `SRS-001-requirements.md` lines 406 (TOOL-COV-100 bare-metal retrieval), 368 (TOOL-TGT-050 semihosting + UART), 376 (TOOL-TGT-090 fault discrimination); `PLAN-001-specification-analysis-and-work-breakdown.md` line 424 (`WP-COV-07` bare-metal coverage retrieval, P3, depends on COV-01 + EXT-03).

**Assessment:** ectt's decomposition already satisfies DEEP boundary 5's *separability* demand: instrumentation belongs to the compiler, collection to the libgcov/llvm profile runtime, transport to CMP-EXT (TOOL-TGT-050), decoding to CMP-COV adapters, and reporting to S4 — with §5.5.2 explicitly forbidding raw-format-level merging. The gap is deferred, not structural: TOOL-COV-100 requires retrieval but, unlike VectorCAST's shipped configuration surface (static-memory pools with declared maximums, clear/dump APIs, flush control, custom sinks, `num_conditions`-parameterised probes) and boundary 5's "declared capacity and loss behavior", no ectt requirement or WP yet obliges the future target path to declare per-build capacity (max MC/DC statements, max subprograms), loss/overflow indication, or clear/dump/flush hooks. Since `WP-COV-07` depends on `EXT-03`, this will surface at P3.

**Recommendation:** Before `WP-COV-07` starts, extend TOOL-COV-100 (or add a sibling requirement) to require the target coverage path to declare its memory capacity, and to surface overflow/loss as evidence per F-06; adopt PRODUCT_ARCHITECTURE §6 line 194's four properties (fixed memory, explicit init/flush, custom transport hooks, overflow/loss indicators) as the acceptance checklist.

---

### F-08 — Provider-named metrics / no relabeling of backend results
**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` lines 174–176 (§5): "The backend owns its compile/link flags, profile collection and decoding ... Their tool-specific results must remain distinguishable until a validated normalization establishes equivalence"; and (line 176) GCC `-fcondition-coverage` vs Clang `-fcoverage-mcdc` named separately.
- `vcast-findings/deep-20261027/cover_models.html.txt` lines 172–186 (`coverage_type` enum: STATEMENT, BRANCH, MCDC, ... distinct per instrumentation) and lines 1353–1377 (`CoverageStatus` incl. `PARTIAL`, `NOT_APPLICABLE`): metric identities stay tied to the producing instrumentation.

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 260–261 (S4): `mechanism` is recorded data (`"gcc -fcondition-coverage"`), so a metric's provider identity travels with it; lines 288–291 (`backend_assertion` evidence retains tool/version/command/record locator); lines 303–305 (merge requires identical "backend semantics").
- `design/SDD-005-external-integration.md` lines 474–477 (§5.5.1 table names each backend's flag and reader: `gcov --conditions` vs `llvm-cov --show-mcdc`) and lines 477–478 (both are masking — form alone does not collapse the two backends into one identity).

**Assessment:** PRODUCT_ARCHITECTURE's rule that LLVM/GCC results must stay distinguishable until a validated normalization exists is exactly S4's design: `mechanism` is mandatory data, merges are refused across differing backend semantics, and even authoritative backend independence bits are kept as digest-bound `backend_assertion` rather than being silently translated into ectt's witness-pair vocabulary. There is no ectt text that relabels provider metrics (e.g. presenting Clang region/line data as ectt "statement coverage"); TOOL-COV-010/020 are satisfied *through* the named backend with the mechanism disclosed per TOOL-COV-060.

**Recommendation:** None for the contract. One implementation caution for `WP-COV-01`: gcovr (ADAPTER-ONLY, floor 8.0/prefer 8.2, SDD-005 lines 460 and 709) may rename/aggregate conditions when adapting — the adapter must preserve the provider metric name into S4's `mechanism` rather than gcovr's.

---

### F-09 — Short-circuit preservation and evaluated/not-evaluated states are contractual in both
**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` line 178 (§5): "Store evaluated/not-evaluated condition states, decision outcomes and contributing test identities. Preserve short-circuit behavior; never evaluate an operand merely to collect a missing value."
- `vcast-findings/deep-specifications/COVERAGE_AND_IO.md` line 19: "preserve short-circuit behavior, and independently validate any claimed MC/DC variant against known cases."
- `vcast-findings/deep-specifications/text/Understanding MC DC Analysis.htm.txt` lines 12–16: the annotated view marks unevaluated outcomes as `( )` (e.g. `4 1.2 (T)( )` — b's false outcome never observed because `a` short-circuited).

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 283–287 (§7.1): evidence must include "condition evaluations (including short-circuit unevaluated values), decision outcomes, and the witness pair"; lines 315–316: acceptance fixtures must include "short-circuit/masking pairs".

**Assessment:** Both sides treat unevaluated-by-short-circuit as a first-class recorded state rather than a hole, forbid fabricating evaluations, and require fixtures exercising it. S4's evidence schema (evaluation records including unevaluated values) is the same information VectorCAST renders as `( )` markers in the annotated listing.

**Recommendation:** None. Carry the short-circuit fixture requirement through to `WP-COV-05`'s test plan explicitly (it is currently stated at S4 §7.1 but not repeated in the WP exit criterion, PLAN line 285).

---

### F-10 — VectorCAST evidence implies a concrete MC/DC fixture corpus that PLAN's COV WPs do not yet name
**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` line 180 (§5): "Validate nested expressions, repeated conditions, coupled conditions, side effects, macro expansions and provider exclusions. Expressions skipped due to backend limits remain visible as unsupported/excluded."
- `vcast-findings/deep-20261027/cover_models.html.txt` lines 199–236: VectorCAST records per-file instrumentation options for exactly these construct classes — `has_logical_operators_in_parameters`, `has_ternary_operator`, `has_nested_ternary_operator`, `has_constant_branch`, `cover_nested_conditional`, `cover_logical_operators_in_parameters`, `handle_ternary_operator` — i.e. construct handling is option- and instrumentation-dependent, and coverage results are only comparable within one instrumentation (lines 306–309: `get_coverable_objects` "Only returns these objects for the current instrumentation").
- `vcast-findings/deep-specifications/text/Understanding MC DC Analysis.htm.txt` lines 26–40: the worked `a && b` example is the minimal known-answer case (matrix, covered rows, satisfied pairs).
- `vcast-findings/deep-specifications/text/Use Masking MC DC.htm.txt` line 5 and `COVERAGE_AND_IO.md` line 19: variant claims must be validated "against known cases" (CAST-6 masking semantics).

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` lines 315–317: S4's fixture list covers independence semantics (equal flags/different independence, short-circuit/masking pairs, missing evidence, incompatible merges, zero denominators) but not expression-shape classes (nested, repeated/`a && a`, coupled `a && (b || a)`, side-effecting operands, macro-expanded operands, ternaries).
- `PLAN-001-specification-analysis-and-work-breakdown.md` lines 636–661 (§6.4): the coverage oracle is differential agreement with the backend's own report ("line for line") — necessary, but it inherits the backend's blind spots and would not catch a shared misinterpretation of masking semantics; `WP-COV-05` (line 422) and its exit criterion (line 285) and `WP-COV-06` (line 423) name no fixture corpus; `SRS-001-requirements.md` line 400 (TOOL-COV-070 per-condition detail) and line 404 (TOOL-COV-090 gap documentation) imply known-answer cases without mandating them.
- Supporting SRS obligation: `SRS-001-requirements.md` line 414–416 (TOOL-COV-140/150 justified-vs-covered) parallels VectorCAST's `CoverageStatus.ANNOTATED` (cover_models lines 1353–1377) — also needing a known-answer fixture once `WP-COV-09` starts, but that is out of RV-04's core scope.

**Assessment:** The construct classes VectorCAST explicitly instruments, flags, and documents (nested/repeated/coupled conditions, side effects, macro expansion, ternaries, constant branches) are precisely the cases where GCC and Clang MC/DC implementations have documented divergent or limit behavior (SDD-005 §5.5.1's Clang-6 trap). PLAN's otherwise-strong differential oracle cannot by itself establish that ectt interprets masking independence correctly — two agreeing readings of the same raw data can both be wrong; a known-answer corpus (VectorCAST's `a && b` matrix as the seed case) is the missing control. The current text nowhere commits the COV work packages to such a corpus.

**Recommendation:** Amend §6.4 (or `WP-COV-05`'s exit criterion) to require a known-answer MC/DC corpus: minimal `a && b` matrix reproduction; nested (`a && (b || c)`); repeated/coupled operands; side-effecting operand (must not be evaluated); macro-expanded condition; constant/`if(0)` decision; and a masking-vs-unique-cause divergent case documenting the expected difference per TOOL-COV-090. Each case asserts S4 statuses (`demonstrated` / `not_demonstrated` / `unmeasured`) plus the witness pair.

---

## Summary

- **Strongest confirmation:** S4's MC/DC contract already encodes the deepest VectorCAST lessons as data — variant/form (`mcdc.form` + `mechanism`, fail-closed), rows-vs-pairs separation (never OR outcomes into independence), short-circuit unevaluated states, digest-bound backend assertions, and provider-identifiable metrics (F-01, F-02, F-08, F-09 all aligned; 0 conflicts).
- **Decision-relevant #1 (F-04 + F-05):** ectt has the capacity *facts* (Clang default 6 / GCC 64) but no requirement to *probe and record* the effective per-backend condition maximum, and no boundary fixtures — while VectorCAST shows limits are option-dependent (52 vs 31; threshold 0–8) and its own documentation contradicts itself on threshold equality. Cheapest fix: add MC/DC limit availability to SDD-005 §6.3's probe list and boundary cases to §6.4 / WP-COV-05/06 exit criteria.
- **Decision-relevant #2 (F-06):** neither S3 nor S4 can currently represent a *present-but-truncated* coverage artifact (VectorCAST's latched buffer + exceeded marker); this is the remaining overclaim channel and needs an explicit coverage-artifact completeness field that propagates to `unmeasured` and an S5 advisory.
- **Decision-relevant #3 (F-10):** PLAN's differential-vs-backend oracle is good but self-blind; a known-answer MC/DC corpus (nested/repeated/coupled/side-effect/macro/constant cases, seeded by VectorCAST's `a && b` matrix) should be mandated in §6.4 before `WP-COV-05` starts.
- **Deferred, not broken (F-07):** ectt's instrumentation/collection/transport/decoding separation already matches DEEP boundary 5; the D4 runtime controls (no-heap capacity, clear/dump/flush, custom sinks, loss indicators) should be written into TOOL-COV-100/WP-COV-07 scope before P3 target work begins.
- **Minor contract note (F-03):** S4's identity-keyed merge is validly conservative but should explicitly name macro/source-variant divergence as merge-incompatible (VectorCAST's five named merge strategies exist for exactly that case).

**Counts by class:** aligned 4 (F-01, F-02, F-08, F-09) · conflict 0 · gap 4 (F-03, F-04, F-06, F-10) · risk 2 (F-05, F-07) · total 10.
