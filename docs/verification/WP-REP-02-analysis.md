# WP-REP-02 — Machine-readable outputs: JUnit and Cobertura/LCOV

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-REP-010, TOOL-REP-020
Design elements: DSN-REP-* per PLAN-001 §3 (CMP-REP)
Dependencies: WP-COV-02 (implemented in this lane: `ectt.cov`), WP-REP-01
(implemented: `ectt.rep` single intermediate model + text/JSON renderers)
Decisions applied as written (not re-decided): none recorded for this package.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 500–502) and the PLAN-001 §5.4 row
(`WP-REP-02` — Machine-readable outputs: JUnit and Cobertura/LCOV; REP-010 REP-020;
dependencies REP-01 COV-02). PLAN-001 §5.4 records **no package-specific acceptance
criterion** for this package (flagged for reconciliation) — these are the derived,
reviewable criteria:

1. **AC-1 (REP-010 — JUnit XML).** `render_junit` over the report model produces a
   well-formed JUnit XML document: one `testsuite` per model carrying the run id and
   the count attributes (`tests`, `failures`, `errors`, `skipped`) derived from the
   model's status vocabulary (`pass`, `fail`, `error`, `timeout`, `not_run`), one
   `testcase` per test; `fail` renders a `failure` element, `error`/`timeout`
   render an `error` element (typed), `not_run` renders `skipped`, `pass` renders a
   bare `testcase`. Attribute and text content is XML-escaped deterministically;
   the digest of the executed definition travels on the testcase.
2. **AC-2 (REP-020 — Cobertura XML).** `render_cobertura` over the report model
   produces a well-formed Cobertura XML document with one class per coverage unit,
   aggregate `lines-valid`/`lines-covered` totals and per-class `line-rate`
   computed from the model's raw counters by a documented deterministic policy
   (exact rational, round-half-even to 6 decimal places, trailing zeros stripped).
   The `timestamp` attribute is fixed to `"0"`: rendered output excludes wall-clock
   time (the strictest reading of TOOL-REP-100, matching WP-REP-01's renderer
   convention).
3. **AC-3 (single-model discipline, REP-090/100).** Both renderers consume only the
   model's `test_statuses()`, `coverage_figures()` and identity accessors — no
   renderer computes a status or a figure from anything else; re-rendering a
   model is byte-identical; `generated_at` never appears in the output; statuses
   and figures parsed back out of the XML agree with the model (no disagreement).
4. **AC-4 (edge cases).** An empty run renders an empty testsuite and an empty
   package without error; a 0/0 coverage unit renders `line-rate="0"` with
   `lines-valid="0"` (no division by zero); XML special characters in ids are
   escaped, never interpolated raw.

Out of scope, recorded: **LCOV** per-line tracefile output. TOOL-REP-020 reads
"Cobertura XML **and/or** LCOV"; the report model carries aggregate counters only
(raw `covered`/`total` per unit) and deliberately no per-line records, so an LCOV
tracefile (which requires per-line `DA:` records) cannot be produced honestly from
the model. Per-line coverage lands with the annotated-source work (WP-REP-03),
which must introduce per-line data; LCOV is flagged there and in the lane ledger.
