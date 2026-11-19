# Verification Analysis Note — WP-REP-01 (Single Intermediate Report Model)

Analysis evidence for requirements verified under WP-REP-01. Status: **implemented**
(evidence-backed). Acceptance criterion from PLAN-001 §5.4 (recorded for this package, unlike
most): "Two different renderers over one persisted report model cannot disagree on any test's
status or any coverage figure; re-running the renderer produces byte-identical output
excluding timestamps."

## Acceptance evidence against the recorded criterion

- **One persisted model.** `ReportModel` (`src/ectt/rep/model.py`) is the single documented
  intermediate data model. It persists to byte-deterministic canonical JSON
  (`dump_report_model`, `schema_version` first key) and loads back validated
  (`load_report_model`), refusing unknown schema versions and any document whose stored
  report id does not match the id recomputed from its content (D-02 "stable ids plus content
  digests" — tampering with a status is refused with `digest_mismatch`).
- **Two renderers, one derivation source.** `render_text` (`ectt.rep.render`) and
  `render_json` both consume only the model's `test_statuses()` and `coverage_figures()`
  accessors; neither computes a status or a figure from any other input, so disagreement is
  structurally impossible (TOOL-REP-090's analysis argument).
- **Disagreement check (criterion clause 1).** `tests/rep/test_renderers.py::
  test_renderers_cannot_disagree` runs both renderers over the persisted round-trip of a
  battery of models (mixed statuses incl. fail/error/timeout/not_run, empty run, partial run,
  zero-coverage unit, single-test run) and asserts the status map and the coverage map parsed
  out of each renderer equal each other and the model, for every model in the battery.
- **Byte-identical re-rendering (criterion clause 2).** `test_rendering_is_byte_identical`
  re-runs both renderers and the dumper over the persisted model and asserts byte equality;
  `test_renderers_exclude_timestamps` asserts `generated_at` never appears in rendered output
  (timestamps are excluded outright, the strictest reading of "excluding timestamps").
  Determinism machinery: model content digests via `stable_id` over canonical JSON, renders
  through `canonical_text`/`canonical_json`.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-REP-090** | All report formats shall be generated from a single documented intermediate data model, so custom report formats can be added without re-running tests. | `src/ectt/rep/model.py` (`ReportModel`, `TestEntry`, `CoverageEntry`, `build_report_model`, `report_model_to_dict`, `dump_report_model`, `load_report_model`), `src/ectt/rep/render.py` (`render_text`, `render_json`), `src/ectt/rep/errors.py` (`ReportModelError`, category `report`) | **Guarantee (single model):** the model is a frozen dataclass document with schema version 1.0, built from one run's `ResultSet` (WP-EXH-01) plus optional coverage entries. Every executed test carries the content digest of the definition it ran (D-02); not-executed tests enter as `not_run`. Validation refuses duplicate tests/units, executed entries without digests, inconsistent coverage counters (`covered > total`), ids containing whitespace (the text render format stays unambiguous), and conflicting result/not-executed state.<br><br>**Guarantee (custom formats without re-running):** a new format is a new function over `test_statuses()`/`coverage_figures()` — the model already exists and is persisted; no test executes to produce it. The two shipped renderers demonstrate the pattern.<br><br>**Test evidence:** `tests/rep/test_model.py` — `test_build_aggregates_statuses_sorted`, `test_build_refuses_duplicate_result`, `test_build_refuses_result_and_not_executed_conflict`, `test_build_refuses_duplicate_coverage`, `test_coverage_entry_validation`, `test_test_entry_validation`, `test_ids_reject_whitespace`, `test_report_id_stable_and_discriminating`, `test_dump_is_byte_deterministic`, `test_roundtrip_preserves_model`, `test_load_accepts_bytes_and_mapping`, `test_load_refuses_tampered_status`, `test_load_refuses_unknown_schema_version`, `test_load_refuses_missing_field`, `test_load_refuses_duplicate_test_entry`. |
| **TOOL-REP-100** | Report generation shall be deterministic: identical inputs shall produce byte-identical reports, excluding timestamps. | `src/ectt/rep/model.py` (`_make_model` id over canonical content, `dump_report_model` via `canonical_json`), `src/ectt/rep/render.py` (both renderers over sorted accessors, `canonical_text`/`canonical_json`) | **Guarantee (byte determinism):** every byte of the dump and of both renderings is a pure function of model content: sets are absent, iteration is over sorted keys, floats do not appear in rendered output, and `canonical_text` normalises line endings. Timestamps enter the model only through the injected `Clock` and are excluded from rendered output entirely, so even differing clocks render identically.<br><br>**Test evidence:** `tests/rep/test_renderers.py` — `test_renderers_cannot_disagree` (per-model battery), `test_rendering_is_byte_identical`, `test_renderers_exclude_timestamps`, `test_text_summary_counts_statuses_deterministically`, `test_zero_total_coverage_renders_without_division` (0/0 renders as counters, no ratio policy), `test_renderers_are_pure_functions_of_content`; plus `tests/rep/test_model.py::test_dump_is_byte_deterministic`, `test_report_id_stable_and_discriminating`. |

## Design notes

- **Why statuses reuse the S3 vocabulary unchanged.** The model aggregates the execution
  host's normalized outcomes (`pass`, `fail`, `error`, `timeout`, `not_run`) verbatim; a
  report is not the place to invent a second status language.
- **Why ratios are not modeled.** The model carries raw counters (`covered`, `total`); a
  percentage is a display policy (rounding, denominator choice) that would give two renderers
  something to disagree about. Coverage export itself remains REP-10 (WP-REP-06, P4).
- **Why the report id covers `generated_at`.** Identical inputs include the clock value; the
  id is a content digest of the whole body (D-02). Renderers exclude the timestamp, so
  rendered bytes stay identical regardless.
- **Scope:** the model is fed by `ResultSet` (WP-EXH-01). Cross-run aggregation, coverage
  trends, and archival reproduction follow in WP-REP-08 / WP-REP-09 / WP-PRJ-05; the report
  format extension point is WP-REP-11 (TOOL-PLG-050).
- **SECOND_PASS rows.** (1) `CATEGORY_EXIT_CODES` in `ectt.cli.exit_codes` gains `"report"`
  when CLI paths are next in scope (WP-CLI-05); the total-by-fallback mapping already covers
  the new category fail-safe. (2) Board asks for *reviewed* acceptance evidence — owner
  review of this note is required to move WP-REP-01 past Done-with-evidence.
