# WP-REP-10 — Coverage interchange import and export

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-MIG-080
Design elements: DSN-REP-* / DSN-MIG-* per PLAN-001 §3
Dependencies: WP-COV-02 (implemented in this lane: `ectt.cov` merge), WP-REP-01
(implemented: `ectt.rep`)
Decisions applied as written (not re-decided): none recorded for this package.

## Acceptance criteria

Derived from the SRS text (SRS-001 line 844: "The tool shall import and export
coverage data in standard interchange formats, permitting aggregation with coverage
produced by other tools") and the PLAN-001 §5.4 row (`WP-REP-10` — Coverage
interchange import and export; MIG-080; dependencies COV-02 REP-01). PLAN-001 §5.4
records **no package-specific acceptance criterion** for this package (flagged for
reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (export — LCOV).** `export_lcov` renders a gcov-derived coverage document
   as an LCOV tracefile: `TN`/`SF` per file, `FN`/`FNDA`/`FNF`/`FNH` per function,
   `BRDA`/`BRF`/`BRH` per branch (`taken` is `-` for a branch of a never-executed
   line, matching the LCOV convention), `DA`/`LF`/`LH` per line, `end_of_record`
   per file. Deterministic (sorted, no wall-clock).
2. **AC-2 (export — Cobertura).** `export_cobertura` renders the document as
   Cobertura XML with per-line `<line number hits branch>` elements; branch-bearing
   lines carry `branch="true"` and a `condition-coverage` attribute computed from
   the model's condition outcomes; `timestamp="0"` (wall-clock excluded).
3. **AC-3 (import — LCOV).** `import_lcov` parses a tracefile into the
   `ectt.cov` model: `DA` line counts, `BRDA` taken counts (`-` → 0), `FN`/`FNDA`
   function records, `LF`/`LH`/`BRF`/`BRH`/`FNF`/`FNH` cross-checked against the
   parsed detail records (a mismatch is a named error — no silent repair).
4. **AC-4 (import — Cobertura, statement-level).** `import_cobertura` parses the
   per-line `hits` into statement coverage. Cobertura's aggregate
   `condition-coverage` does not carry per-branch taken counts, so branch records
   are not invented: a document imported from Cobertura carries statement counts
   only (recorded in the document as data, never guessed into branch figures).
5. **AC-5 (aggregation).** Imported documents aggregate with `ectt.cov.merge`
   (they are ordinary `GcovDocument` values carrying the producing tool's recorded
   version string, so documents of the same provenance merge; the merge's
   provenance-equality rule applies unchanged). Round trips hold: export → import
   reproduces the exported counts (LCOV fully; Cobertura at statement level).
6. **AC-6 (fail-closed).** Malformed XML, an unknown LCOV record tag, a
   non-integer or negative count, an `SF` without `end_of_record`, or a summary
   mismatch is a named error.
