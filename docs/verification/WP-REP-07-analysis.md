# WP-REP-07 — Paginated PDF archival rendering

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-REP-080
Design elements: DSN-REP-* per PLAN-001 §3 (CMP-REP)
Dependencies: WP-REP-03 (implemented in this lane), WP-REP-01 (implemented)
Decisions applied as written (not re-decided): none recorded for this package.
Constraint honoured: **no new runtime dependencies** (queue hard rule 4) — the PDF
writer is hand-written against the PDF 1.4 specification structure (catalog, pages,
page, base-14 Helvetica font, uncompressed content streams, xref, trailer), with no
third-party PDF library.

## Acceptance criteria

Derived from the SRS text (SRS-001 line 514: "The tool shall produce reports in a
paginated, archivable format (PDF) for records retention") and the PLAN-001 §5.4
row (`WP-REP-07` — Paginated PDF archival rendering; REP-080; dependency REP-03).
PLAN-001 §5.4 records **no package-specific acceptance criterion** for this package
(flagged for reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (REP-080 — paginated PDF).** `render_pdf` produces a structurally valid
   PDF 1.4 document (parseable header, catalog, page tree, font, content streams,
   xref table with correct offsets, trailer) whose content streams contain the
   run id, every test id and status, every coverage unit and figure, and the
   provenance facts — flowing across Letter-size pages with fixed margins; a long
   run spans multiple pages (e.g. 120 tests → more than two pages).
2. **AC-2 (archival determinism).** Output is byte-identical for identical
   inputs; no document-creation timestamp is emitted (no Info dictionary, no
   wall-clock); no network; no third-party dependency.
3. **AC-3 (pagination and safety).** Every page carries a `Page N of M` footer;
   text is truncated at a fixed character budget (never silently overflowing the
   page); PDF string specials (`\`, `(`, `)`) are escaped; characters outside
   WinAnsi/Latin-1 are substituted deterministically (`?`), never dropped
   silently.
4. **AC-4 (no disagreement).** The text drawn in the PDF is derived from the same
   model accessors as every other renderer (`test_statuses()`,
   `coverage_figures()`, `provenance_facts()`) — statuses and figures parsed back
   out of the content streams agree with the model.
