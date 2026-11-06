# RV-03 — Data model & persistence cross-review of vcast-findings against ectt baseline

Reviewer: RV-03 (data model & persistence). Date: 2026-11-06.
Subject: `vcast-findings/` (static reverse-engineering evidence of VectorCAST 2026 SP4 persistence).
Baseline: `design/SDD-002-interfaces.md`, `design/SDD-003-data-model.md`, `ADR-002-project-data-format.md`, `design/SDD-004-traceability-architecture.md`, `SRS-001-requirements.md`, `PLAN-001-specification-analysis-and-work-breakdown.md`, and implemented `src/ectt/prj`, `src/ectt/ing`, `src/ectt/ana`.

Method: read-only comparison. Every finding cites at least one vcast-findings path and at least one ectt baseline path. No script inside vcast-findings was executed; no spec/design/src file was modified.

---

### F-01 — Expected-vs-actual separation is preserved by the S2/S3 seam

**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/master-schema.sql` keeps authored specification and observed results in separate tables: `test_data` (lines 344–354: `kind`, `testcase_id`, `data_object_id`, `value`, `action`, `usercode_tag` — the specified inputs/expected, bound to the test case) vs `actuals` (lines 31–54: `test_datum_id`, `event_id`, `testhistory_id`, `is_result`, `value`, `usercode_value`, `"match"`, `match_string`, `unused` — observed per-event values with match flags, bound to run histories, not to the case). The `actuals.test_datum_id` FK makes row-level expected↔observed correspondence explicit.
- `testcases` carries the existence flags `input_exists`, `expected_exists`, `results_exist` (master-schema.sql lines 401–403), again distinguishing authored content from execution artifacts.
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` D7: "Separate objects for types, parameters, globals, expected/actual data, test cases, history, slots and results"; D6 confirms the Data API exposes these as distinct model objects.

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` §5 (S2 Test Case Model): authored `inputs` and `expected` blocks (`"expected": { "return": 4095, "globals": {...}, "comparison": {...} }`, lines 174–181) live in the project tree; §6 (S3 Result Set) carries generated `results[].failures[]` with `"expected": "4095", "actual": "0"` plus `duration_ms`, `run_id` — produced by runners, never authored.
- `design/SDD-003-data-model.md` §2 two-trees table: authored state (scopes, environments, test cases) is version-controlled; derived state (results) is gitignored output.
- `SRS-001-requirements.md` TOOL-TCD-040 (authored expected values) vs TOOL-EXE-020 (per-test report "with failures identifying the assertion, expected value, actual value, and source location").

**Assessment:** The separation the incumbent enforces at the table level (authored `test_data` vs run-bound `actuals`) is preserved in ectt at the seam level: S2 is the authored expectation surface, S3 is the generated observation surface, and SDD-003 §2 forbids results from entering the project tree. TOOL-ATG-080 (generated expected values marked unreviewed) additionally keeps ATG-authored expectations distinguishable, matching the incumbent's `origin`-style discipline.

**Recommendation:** None required for the separation itself. See F-04 for the granularity nuance (per-datum match flags vs failure-only actuals).

---

### F-02 — Authored/observed conflation in the incumbent's `testcases` table is designed out in ectt

**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/master-schema.sql` lines 380–442: the `testcases` table mixes authored definition columns (`name`, `tolerance`, `requirement_keys`, `variant_logic`, `csv_options`) with live execution state on the same row: `status`, `testcase_status`, `execution_status`, `failure_reasons`, `start_time`/`end_time` (TIMESTAMP), `input_exists/expected_exists/results_exist`, and `history_id` FK into `test_histories`. A single table row is simultaneously the authored case and its latest-run outcome; run identity is a mutable FK (`history_id`) on the authored record.
- `vcast-findings/deep-specifications/SPECIFICATION_RECOVERY.md` §"Storage relationships…" cautions that the schema's declared relations and lifecycle semantics (e.g., the `deleted_testcase` trigger cascading into `test_histories`, master-schema.sql lines 503–509) cannot be fully interpreted statically — the conflation makes lifecycle invariants hard to recover even for the vendor's own users.

**ectt baseline evidence:**
- `design/SDD-003-data-model.md` §4: "No incidental save timestamps, host names, or serializer user names… Execution timestamps and host observations live in results/output and archives (REP-070)" — authored records are byte-stable and never mutated by a run.
- `design/SDD-002-interfaces.md` §6 (S3): results are a separate versioned document keyed by `run_id` with `order_seed`; run comparison keys on the immutable test id (S2 §5.1 "Identity is assigned, not derived").
- Implemented `src/ectt/prj/project.py` `save_file` (lines 228–332) enforces atomic, byte-identical-no-op writes to the project tree; `src/ectt/ana/persist.py` `write_analysis_model`/`compute_model_digest` (lines 244–262, 413–423) keep derived models digest-addressed in the output tree.

**Assessment:** The incumbent's evidence shows the failure mode of storing run state on the authored record (unstaleable mixed state, mutation of "authored" rows by execution, cascade-delete triggers to keep it consistent). ectt's two-trees rule plus assigned ids structurally prevent this: an execution can never rewrite a test case, and comparing runs is a join on ids rather than reading mutable columns. This is a confirmation that the SDD-003 §2/§4 discipline targets a real, observed industry failure mode.

**Recommendation:** Keep the discipline explicit in SDD-003 when results storage (S3 persistence, currently only specified via S5/archives) is designed: results must reference test ids, never embed or update case rows.

---

### F-03 — Compound tests, slots and iterations have no equivalent in S2, SRS-001 or PLAN-001

**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/master-schema.sql`: `slots` (lines 313–324: `parent_id` FK to `testcases`, `testcase_id` FK to member case, `iteration_count`, `delay`), `slot_histories` (lines 296–311: `testhistory_id`, `slot_id`, `num_iterations`, `kind`), and `events` (lines 93–128: `iteration_index`, `range_iteration_index`, `is_new_slot`, `is_new_iteration`, `is_new_range_iteration`); `testcases.for_compound_only` (line 406) marks cases that only exist as compound members.
- `vcast-findings/deep-specifications/SPECIFICATION_RECOVERY.md` §"Harness lifecycle": "The table driver nests slot iterations and range iterations, with user initialization before the generated UUT switch… Stub counters have conditional range/compound reset and an unconditional slot-end reset."
- `vcast-findings/deep-specifications/master-tables.json` (`table: "slots"` line 1305, `table: "slot_histories"` line 1227) confirm these are first-class persisted structures, not report-time constructs.

**ectt baseline evidence:**
- `SRS-001-requirements.md`: a grep for `compound|iteration|slot` returns zero hits — no requirement covers compound parent/member cases or per-slot run structures. TOOL-TCD-070 ("ranged inputs, generating one executed test per value in the range") is the nearest concept, and it materializes iterations as independent executed test cases rather than as nested slots inside one run.
- `design/SDD-002-interfaces.md` §5 (S2): the model has `kind: data | c_source`, `inputs`, `expected`, `stubs` — no parent/member composition, no sequence-of-slots construct; §6 (S3) results are flat per-test records with no event stream, iteration index, or slot history.
- `PLAN-001-specification-analysis-and-work-breakdown.md`: `WP-TCM-05` "Ranged and robustness input generation" (TCD-070, TCD-130) and `WP-TCM-03` "Expected-value comparison engine" exist, but no WP covers compound/iterative test structures; `WP-EXH-01/02` (host execution, crash isolation) have no per-slot result concept either.

**Assessment:** This is a real capability gap relative to the incumbent's data model, though a deliberate one: DEEP_ANALYSIS.md §"3. Harness lifecycle and test authoring are separate" recommends starting with "conventional coded tests plus a small typed data-case format", and ectt's flattening strategy (one executed test per range value, independent results) achieves iteration semantics with simpler result identity — every iteration gets its own S3 record instead of a nested slot-history tree. What is lost: ordered multi-step scenarios (call sequence with per-step expected values, inter-step state, delays between steps — `slots.delay`) and stateful stub sequences spanning slots (`stubs.hal_read.mode: sequence` in S2 hints at sequences, but there is no ordered multi-call scenario structure with per-call expectations in one logical test).

**Recommendation:** Do not close silently. Either (a) add a deferred requirement/WP for compound test cases (parent case + ordered member cases, each member an ordinary S2 case, results linked by parent run id — the flattening-friendly design), or (b) record in SDD-002 §5 that ordered multi-step scenarios are out of scope for v1 and must be authored as C-source tests (`kind: c_source`), so the limitation is visible to users migrating from VectorCAST (TOOL-MIG-030/090 migration-fidelity reporting should flag compound tests as a fidelity loss).

---

### F-04 — Per-datum observed values with match flags are coarser in S3 (failure-only actuals)

**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/master-schema.sql` `actuals` (lines 31–54): one row per observed datum per event, with `"match"` BOOLEAN, `match_string`, `is_result`, `unused`, and `usercode_value` — i.e., the incumbent persists the full observed-value matrix for passing tests too, aligned row-by-row with authored `test_data` via `actuals.test_datum_id`. `test_summaries` (lines 367–378) then aggregates (`expected_fail/expected_total`, `control_flow_fail/total`).
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` D7: "results" and "history" are separate model objects; observed data is retained per event, not only per failure.

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` §6 (S3): `results[].failures[]` records `expected`/`actual` only inside failure entries; a passing test carries only `outcome`, `duration_ms`, and no observed values. S5 embeds S3 as-is.
- `SRS-001-requirements.md` TOOL-EXE-020 mandates expected/actual in *failure* reports only; TOOL-UIX-220 likewise ("for each failure").

**Assessment:** ectt's S3 satisfies every stated requirement but loses two capabilities the incumbent's schema supports: (1) post-hoc review of observed values for passing tests (auditors asking "what did the UUT actually return on the passing run?" cannot answer from S3); (2) tolerance-adjacent diagnostics (near-miss values, `match_string`-style detail) without re-running. Since results are the gitignored output tree (SDD-003 §2), persisting full observed values costs nothing in diff stability.

**Recommendation:** When S3 persistence is specified (currently S3 exists only as an interchange shape in SDD-002 §6), add an optional per-assertion observed-values block (expected, actual, comparison verdict) to each result record — the `actuals` table is the evidence that a certification-grade incumbent keeps this data for every datum, not just failures. Keep it optional-with-default so the common report stays small; TOOL-REP-12 (WP-REP-12) export already plans "expected/actual values" in results interchange, so align the two.

---

### F-05 — Build-capture DB captures observability ectt's compdb model defers; classify gaps for WP-ING

**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/vcapplib-recovered-schema.sql`: `FILES` (line 11: `FILEID`, `FILENAME`, `FILEPATH`, six date/time components, `ETIME`), `COMMANDS` (line 14: `CMD`, `CMDLINE`, `PWD`, `OUTPUT` — captured command output), `COMPILATION` (line 17: `TAG`, `FILEID`, `CMDID`), `BUILDS` (line 8: `TAG`, `PATH`, `MACHINE`, `USERNAME`, `DAY…SECONDS`), plus `VCINSTRUMENTSTATUS`/`VCQUICKPARSESTATUS`/`VCCODEGENSTATUS` (lines 38–44: per-FILEID+TAG status), `VCMETRICS` (line 29: SLOC, COMPLEXITY, BRANCHES, MCDC_PAIRS per function), `COMMENT_DENSITY`, `VCCHANGEDFILES` (line 53), `VCINSTFILEENABLER`/`VCPARSEFILEENABLER`/`VCCODEGENFILEENABLER` (lines 56–62).
- `vcast-findings/VCAPPLIB.md` §"Database model recovered from the DLL": observed query joins at offsets `0x21b690` (FILES.FILEID↔COMPILATION.FILEID, COMPILATION.CMDID↔COMMANDS.CMDID) and `0x21cff0` (tags, command lines, working directories via CMDID); `vcast-findings/vcapplib-sql-strings.json` lines 272–312 show tag-scoped queries (`… INNER JOIN COMPILATION b … AND b.TAG=%Q`).
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` D13 / §"1. Build context is part of the analysis input": "Preserve the original command even when an adapter derives a separate analysis command."

**ectt baseline evidence:**
- `src/ectt/ing/model.py`: `TranslationUnit` (lines 46–70) captures `source_path`, `working_directory`, `include_paths`, `preprocessor_definitions`, `compiler_invocation` (executable, full `arguments`, `residual_flags`), `language_standard`, `output_file`; `CompilationDatabase` (lines 125–169) supports multiple TUs per source path (`filter_by_source`, lines 151–154), so multi-configuration files are representable.
- `design/SDD-003-data-model.md` §9: cache keyed on "compilation database entry, source digests, flags, front-end version" (TOOL-ING-090/100, TOOL-CIC-070); §4 forbids incidental timestamps/host names in *authored* records (output-tree models are exempt via provenance, `src/ectt/ana/model.py` `ProvenanceModel` lines 481–507 records `generated_at`, `front_end`, input digests).
- `PLAN-001…` `WP-ING-01` (ING-010..040), `WP-ING-03` "Ingestion diagnostics, persistence and staleness" (ING-070/090/100), `WP-ING-06` "Multi-toolchain ingestion" (ING-110).

**Assessment — what vcshell.db captures that ectt's compdb model does not, classified for WP-ING:**

| vcshell.db concept | In ectt ing model? | WP-ING relevance |
|---|---|---|
| Working directory (`PWD`) | Yes (`working_directory`) | — |
| Output artifact (`OUTPUT`), full cmdline | Yes (`output_file`, `arguments`, `residual_flags`) | — |
| Multiple configs per file | Yes (`filter_by_source`; SDD-002 §4 provenance digests) | — |
| Build tag grouping compilations (`COMPILATION.TAG`, tag-scoped joins) | No — TUs are a flat tuple; no persisted build/run identity on the ingested set | WP-ING-03 (staleness): selecting "which compilations belong to build X" currently requires recomputing digests; a build-tag/scope identity on the ingested database would make incremental rebuild selection and CI restore (TOOL-CIC-070) query-shaped rather than recompute-shaped |
| Capture metadata (`BUILDS`: machine, user, date/time) | No — deliberately excluded from authored records (SDD-003 §4); could live in output-tree provenance like `ProvenanceModel.generated_at` | Low priority: S3 `execution` metadata + S5 provenance already cover run-level host identity; duplicating it in ing adds nondeterminism risk |
| Per-file instrumentation/quick-parse/codegen status (VC*STATUS) | No — generation/instrumentation status is not an ing concern | Not WP-ING: belongs to CMP-GEN/CMP-COV generated-artifact staleness (TOOL-HAR-110 digest pattern already covers "generated artifact stale"); do not pull into ing |
| Code metrics per function (VCMETRICS) | Partially — `ana` emits `complexity` per function (SDD-002 §4.1); SLOC/comment density/branches are absent | WP-ING-05 / ANA boundary; metrics are analysis-model output, not ingestion — defer to a report-model decision, not ing |
| Changed-file tracking (VCCHANGEDFILES) | No — derived by digest comparison against cache (SDD-003 §9) | WP-ING-03: digest-based staleness is the ectt answer; a persisted changed-file list would be a cache, not a model — correctly omitted |

**Recommendation:** The one gap worth a design note is build identity on the ingested set: give `CompilationDatabase` (or its persisted form) an explicit identity digest + optional tag label so tag-scoped selection like the incumbent's `… AND b.TAG=%Q` queries is a field lookup. Machine/user/time should stay out of ing (SDD-003 §4 determinism rule is correct; the incumbent stores it because vcshell.db is a single-writer local DB, not a versioned artifact). Instrumentation/codegen status and metrics should be rejected for WP-ING scope — they are downstream artifacts with their own staleness contracts.

---

### F-06 — Type registry: closure and conflict detection survive; ranges/dimensions are not first-class

**Class:** gap

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/master-schema.sql`: `types` (lines 444–467: `kind`, `is_pointer`, `element_id`, `secondary_id`, `range_id`, `typemark`), `fields` (lines 144–157: `name`, `type_id`, `parent_type_id`, `range_id`, `is_bitfield`), `enums` (lines 71–78: `name`, `value`, `type_id`), `ranges` (lines 287–294: `min`, `mid`, `max`, `size` — all VARCHAR, i.e. text-preserved values), `dimensions` (lines 56–69: `low`, `high`, `min`, `max`, `offset`, `range_id`, `index_type_id` — first-class array-dimension records), `inheritances` (lines 234–242). The `range_id` FK appears on `types`, `fields`, `parameters` (line 271/280), and `globals` (line 230): every data anchor can carry a range constraint.
- `vcast-findings/deep-specifications/master-tables.json` `table: "dimensions"` (line 121) and `table: "ranges"` (line 1181) confirm these as independent per-row records.
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` D7 lists types as their own model objects.

**ectt baseline evidence:**
- `src/ectt/ana/model.py` `TypeModel` (lines 333–411): kinds struct/union/enum/typedef/function_pointer/builtin/pointer/array; `StructMemberModel.bit_width` ≙ `fields.is_bitfield`; `EnumeratorModel` ≙ `enums`; `element_type`+`size` ≙ a slice of `dimensions`; `parameters` carry `type` refs ≙ `parameters.type_id`. No `range` field exists anywhere in the model; array `size` is a single int with no per-dimension index-type or offset.
- `src/ectt/ana/types.py` `TypeGraphBuilder` (lines 67–531): transitive closure over pointers/arrays/typedef/struct/union/enum — the structural registry survives.
- `src/ectt/ana/persist.py` (lines 171–205): model-wide type merge with `TypeDefinitionConflictError` on differing canonical definitions, and `TypeClosureError` on dangling `ref:type.*` — a stronger integrity contract than the incumbent's declared-but-unenforced FKs.
- `design/SDD-002-interfaces.md` §4.1 shape: `"types": { "type.adc_channel_t": { "kind": "enum", "enumerators": [...] } }` — same registry concept, nested map instead of tables.

**Assessment:** What survives: the structural type registry (kinds, members/fields with bitfields, enumerators, pointer/array/typedef/function-pointer closure), plus conflict detection the incumbent lacks. What is absent: (1) `ranges` — min/mid/max/size as first-class data attached to types, fields, parameters and globals. ectt keeps comparison tolerance in the S2 case (`comparison: {tolerance}`) and generates range tests at authoring time (TOOL-TCD-070), but the analysis model cannot state "this parameter's domain is [0, 4095]" — which ATG boundary generation (WP-TCM-07, WP-ATG-02) will need as an input, and which the incumbent stores textually (VARCHAR `min`/`max` — notably the same quote-values-as-text philosophy as ADR-002). (2) `dimensions` — multi-dimensional array metadata (per-dimension low/high, index type, offset); ectt models multi-dim arrays as nested single-size arrays, losing index-type and offset. (3) `inheritances` — no C equivalent; correctly absent for an embedded-C tool.

**Recommendation:** Add an optional `range` facet to `ParameterModel`/`StructMemberModel` (or a top-level `ranges` map with digest-stable ids, referenced like `ref:type.*`) in the S1/ana schema before WP-ATG work starts; ranges recovered from source (e.g., clamped checks, enum bounds) are exactly the input bounded generation needs, and the incumbent's evidence shows they belong to the model, not to individual test cases. Dimensions metadata is lower priority (fixed-size C arrays suffice for v1); record as a known limitation for multi-dimensional array editing (it interacts with WP-SPIKE-02's "fixed array editable at every level").

---

### F-07 — Persistence-technology contrast is a deliberate trade-off, correctly decided

**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/VCAPPLIB.md`: the DLL "imports 18 SQLite functions"; 27 `CREATE TABLE` strings recovered; the build DB is a local single-writer SQLite file (`vcshell.db`); `vcast-findings/deep-specifications/SPECIFICATION_RECOVERY.md` component map: "master-schema.sql records the schema of a shipped SQLite file… Schema declarations do not establish live data, foreign-key enforcement" — i.e., relational integrity is declared in DDL but its enforcement and lifecycle are opaque, and the recovery itself was hard precisely because state lives in an opaque binary container.
- `vcast-findings/deep-specifications/master-schema.sql` lines 488–509: cross-table lifecycle is maintained by hand-written `AFTER DELETE` triggers rather than declared constraints.

**ectt baseline evidence:**
- `ADR-002-project-data-format.md` §2: restricted YAML, one serialisation adapter, deterministic emission; §1 rationale (diffable, reviewable, decade-scale lifetimes). `design/SDD-003-data-model.md` §3: one-file-per-thing granularity chosen specifically so concurrent edits produce localized conflicts — the direct opposite of a whole-project database file, which forces whole-file conflict at any granularity.
- Queryability is not given up blindly: SDD-002 §8 persists the S5 report model ("a report regenerates from archived data with no re-execution"), and SDD-003 §9 provides the content-addressed cache for incremental lookups; `src/ectt/ana/persist.py` `read_analysis_model` (lines 265–386) gives validated programmatic access to models without a DB engine.

**Assessment:** The incumbent's SQLite choice optimizes single-user queryability and transactional writes; its costs show up in the recovered evidence: undeclared-enforcement FKs, trigger-encoded cascade invariants, no localized VCS merge story (a `.db` is unmergeable), and long-term interpretability risk (a 26-table schema whose live semantics cannot be recovered statically years later — exactly the failure SDD-003 §5 fail-closed versioning exists to prevent). ectt's YAML tree pays with query latency and multi-file transactionality (SDD-003 §2 journals multi-file updates) but keeps every record diffable, versioned, and self-describing with `schema_version`. For a decades-horizon safety tool the trade is right; the evidence strengthens rather than challenges ADR-002.

**Recommendation:** No change. One forward note: when result volumes grow, ectt should reach for many-small-files plus the S5 projection (or an explicit disposable index in `cache/`), never an authored-state database — SDD-003 §9's "always discardable" rule is the boundary.

---

### F-08 — Requirement-verdict aggregation anomaly is not yet guarded in S5/TOOL-TRC

**Class:** risk

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/SPECIFICATION_RECOVERY.md` §"Storage relationships and requirement interpretation": "each association is resolved by test, function and unit name; the first match is used… one requirement may appear multiple times or in both lists… two passing associations for one assigned requirement can yield a numerator of two and denominator of one before formatting."
- `vcast-findings/deep-specifications/master-schema.sql` line 397: `testcases.requirement_keys TEXT` — requirement association is a denormalized text blob on the case, with no association table, no unique constraint, and no requirement entity in the shipped unit-test DB at all; duplication is structurally invited.
- `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` D9: requirement identifiers, repositories and synchronization metadata link into result models; §"7. Requirements and reporting are projections over evidence": "The design should have one result model usable by CLI, UI, reports and requirements integrations."

**ectt baseline evidence:**
- `design/SDD-002-interfaces.md` §8 (S5): `"traceability": { "matrix": [...], "unlinked_requirements": [...], "unlinked_tests": [...] }` — the matrix rows exist but **no rule specifies per-requirement verdict aggregation** (dedup of multiple links, whether one requirement's status is min over linked tests, how unreviewed/ATG-origin tests count). S4.1 shows the project knows how to write denominator discipline ("must label that denominator. A zero denominator is N/A") — but only for MC/DC conditions, not requirement coverage.
- `SRS-001-requirements.md`: TOOL-TRC-020 (bidirectional matrix), TOOL-TRC-030 ("report the pass/fail status of each linked test case" — per-test, not per-requirement), TOOL-TRC-040 (unlinked detection), TOOL-REP-110 (cross-unit aggregation). No requirement defines a per-requirement verdict, so the anomaly class (numerator > denominator, double-counted associations) is unspecified rather than prevented.
- Partial protection exists: `design/SDD-003-data-model.md` §7 binds requirement links to "digest of requirement text at last review" (TOOL-TRC-090, "link marked needing re-review"), which prevents stale-claim carry-forward but not count duplication; SDD-002 §2 requirement ids come "from the requirements source" (imported, TOOL-TRC-050/060), so association is by id, not by first-name-match as in the incumbent's example.

**Assessment:** ectt avoids the *cause* of the incumbent's anomaly (name-based first-match resolution; untyped denormalized key lists) by using imported requirement ids and digest-bound links. But the *effect* — a report counting two associations for one requirement as 2/1 — is exactly the kind of error SDD-002 §8's `advisories`/disclosure philosophy should make structurally impossible, and today nothing in SRS-001/SDD-002/SDD-004 defines the aggregation semantics. SDD-004 covers the project's own SRS→design traceability, not user-requirement verdicts, so it does not help. A renderer or future requirement-coverage feature could independently invent a numerator/denominator and inherit the incumbent's bug.

**Recommendation:** Add one normative sentence to SDD-002 §8 (and a TOOL-TRC requirement at next SRS revision): requirement-level figures must be computed by deduplicating association rows to unique (requirement id, test id) pairs, the per-requirement verdict is the worst linked-test outcome (with unreviewed-origin tests counted as unverified, per TOOL-ATG-080), every percentage names its denominator, and a requirement linked to zero executed tests is unverified — never inferred from coverage. Add an acceptance fixture reproducing the incumbent's 2-associations/1-requirement scenario.

---

### F-09 — Recovered-schema cautions (triggers, id duality, name uniqueness) are covered by fail-closed versioning and digest-bound identity

**Class:** aligned

**vcast-findings evidence:**
- `vcast-findings/deep-specifications/SPECIFICATION_RECOVERY.md` §"Storage relationships…": three explicit cautions — (1) "The SQL deletion triggers use several ID comparisons whose intended external invariants are unknown" (triggers at master-schema.sql lines 488–509 cascade deletions across `actuals`/`events`/`outputfiles`/`slot_histories`/`test_data` via raw id equality); (2) "The two `data_object_id` fields have different declared types and no declared relation" (`test_data.data_object_id INTEGER` line 348 vs `actuals.data_object_id TEXT` line 34); (3) "Names, nullable fields and identifiers must not be assumed unique or interchangeable" (e.g., nullable `testcases.name VARCHAR` with a non-unique index, master-schema.sql lines 25, 387).

**ectt baseline evidence:**
- Against (1) silent cascade semantics: `design/SDD-003-data-model.md` §7 digest-bound records — a change *invalidates* (state becomes `expired`/`stale`/`needing re-review`) instead of deleting dependents; §8 archives are explicit, self-contained, digest-verified records; `src/ectt/prj/project.py` writes are atomic per file with no cross-file cascade at all. There is no destructive cascade anywhere in the implemented tree.
- Against (2) ambiguous dual-typed identity: SDD-003 §6 identity table (test ids assigned with random suffix, TOOL-TCD-140; requirement ids from the source; every reference stored relative and resolved by a validation pass, TOOL-PRJ-090), plus implemented referential enforcement — `src/ectt/ana/persist.py` `TypeClosureError` rejects any dangling `ref:type.*` (lines 192–205, 366–383) and `TypeDefinitionConflictError` rejects conflicting duplicate definitions (lines 171–190). ectt's cross-references are typed (digest, `ref:type.*`, project-relative path) and validated, never two same-named columns of different types.
- Against (3) name-as-identity: SDD-003 §10 risk table ("Test case ids collide after a merge → sufficient random suffix, plus a duplicate-id check in project validation"); SDD-002 §3 fail-closed rule ("Unknown semantic enum values… fail closed; they are never coerced"); implemented `src/ectt/prj/model.py` `dispatch_schema_version` (lines 103–157) refuses absent/unsupported versions instead of guessing — the direct guard against "assumed" identity.
- `design/SDD-002-interfaces.md` §9.2: duplicate JSON keys are rejected in the engine protocol, mirroring ADR-002 §3's duplicate-key rejection — the parser-level analogue of the incumbent's silent column-overwrite hazard.

**Assessment:** All three recovered cautions correspond to failure modes ectt has already designed against, with implemented evidence for referential closure (persist.py) and identity assignment (prj). The residual exposure is procedural rather than structural: future ectt records (S3 results, requirement links) must keep referencing assigned ids and digests, not human names — the moment a feature resolves a test by name (as the incumbent's requirements example resolves by test/function/unit name), the anomaly class of F-08 returns.

**Recommendation:** Encode the lesson as a review rule rather than new mechanisms: no ectt record may establish identity or association by human-readable name alone; names are display data. Add this sentence to SDD-003 §6 and a fixture that renames a test case and proves its results/requirement links still resolve by id.

---

## Summary

- **Counts:** aligned 4 (F-01, F-02, F-07, F-09) · gap 4 (F-03, F-04, F-05, F-06) · conflict 0 · risk 1 (F-08). Total 9.
- **Expected/actual and authored/observed separation (Q1) is faithfully preserved**: the incumbent's `test_data` vs `actuals`/`test_histories` split maps onto ectt's S2 (authored `inputs`/`expected`) and S3 (generated results) seam plus the SDD-003 two-trees rule; the incumbent's own conflation of run state onto `testcases` rows validates that discipline.
- **Most decision-relevant — compound/slot/iteration structures (Q2) are a genuine, unrecorded gap**: VectorCAST persists slots, slot histories and per-event iteration indices as first-class data; SRS-001 has zero requirements for them and PLAN-001 no WP. Decide explicitly: defer with a migration-fidelity flag (TOOL-MIG-090) or add a flattening-friendly compound-case WP; silence will surface as a migration surprise.
- **Most decision-relevant — per-requirement verdict aggregation (Q5/F-08) is unspecified and is the one true risk**: the recovered anomaly (two passing associations → numerator 2/denominator 1) arises from denormalized name-based association; ectt avoids the cause (imported ids, digest-bound links) but SDD-002 S5 defines no aggregation semantics, so a future renderer could reinvent the bug. One normative sentence + one fixture closes it.
- **Build capture (Q3) and type registry (Q4) gaps are scoped and modest**: ectt's `ing` model already captures working directory, output, full argv and multi-config files; the only WP-ING-worthy addition is an explicit build identity/tag on the ingested set. The `ana` type graph matches the incumbent's registry structurally (with stronger conflict detection); the real omission is first-class ranges/dimensions — recommend adding range facets to the S1 schema before WP-ATG starts.
- **Persistence technology (Q5/Q6): ADR-002's restricted-YAML one-file-per-thing decision is reinforced, not challenged**, by the recovered evidence — the incumbent's trigger-maintained, opaque SQLite state is precisely the failure mode (undeclared invariants, unmergeable, unrecoverable semantics) that SDD-003's fail-closed versioning, digest-bound records, and assigned-id identity already guard against.
