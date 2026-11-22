# WP-REP-03 — HTML report with annotated source

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-REP-030, TOOL-REP-040
Design elements: DSN-REP-* per PLAN-001 §3 (CMP-REP)
Dependencies: WP-COV-01 (implemented in this lane: `ectt.cov`), WP-REP-01
(implemented: `ectt.rep`), WP-COV-09 (implemented in this lane: per-line
annotation with justification statuses)
Decisions applied as written (not re-decided): none recorded for this package.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 504–506) and the PLAN-001 §5.4 row
(`WP-REP-03` — HTML report with annotated source; REP-030 REP-040; dependencies
COV-01 REP-01). PLAN-001 §5.4 records **no package-specific acceptance criterion**
for this package (flagged for reconciliation) — these are the derived, reviewable
criteria:

1. **AC-1 (REP-030 — combined report).** `render_html` produces a single
   human-readable HTML document combining: the run summary (run id, partial flag,
   status counts, provenance facts), the test table (one row per test with its S3
   status) and the coverage summary (per-unit counters) — all read only from the
   model's `test_statuses()`/`coverage_figures()`/`provenance_facts()` accessors,
   the same sources as every other renderer (REP-090 discipline).
2. **AC-2 (REP-040 — annotated source).** For every file that has both per-line
   annotation (from `ectt.cov.justification.annotate_coverage`) and available
   source text, the report renders the source with per-line coverage status:
   class-marked `covered`, `partial`, `uncovered`, `justified` lines; a
   `justified` line visibly carries its owning justification id; instrumented
   lines and non-instrumented lines are visually distinct. Line numbers are
   rendered for every source line.
3. **AC-3 (no guessing, nothing dropped).** An annotated file whose source text is
   not supplied is listed under a "source not available" section — surfaced, never
   silently omitted; statuses and figures parsed back out of the HTML agree with
   the model and the annotation (no disagreement).
4. **AC-4 (determinism and escaping).** Re-rendering is byte-identical;
   `generated_at` never appears; all dynamic text (ids, source lines) is
   HTML-escaped, never interpolated raw; no wall-clock; no network; no external
   assets (the page is self-contained).
