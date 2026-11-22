# WP-COV-09 — Coverage-by-analysis justification with digest binding

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-140, TOOL-COV-150
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-COV-01 (implemented in this lane: `ectt.cov`), WP-PRJ-01
(implemented: `ectt.prj`; justification records are data and do not require
project integration in this increment — storage in a project file is a
consumer concern, flagged below)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first"** —
  annotation evaluates over gcov-derived documents; Clang must not shape it.

## Recorded acceptance criterion (PLAN-001 §5.4, quoted)

> `WP-COV-09` — Editing a source line under an accepted justification invalidates
> that justification, and the next report shows the construct as uncovered rather
> than justified

(Quoted verbatim from PLAN-001 §5.4 line 251. Done requires reviewed acceptance
evidence against this criterion.)

## Acceptance criteria

Derived from the SRS texts (SRS-001 §12 lines 420–421), the PLAN-001 §5.4 row
(`WP-COV-09` — Coverage-by-analysis justification with digest binding; COV-140
COV-150; dependencies COV-01 PRJ-01) and the recorded criterion above:

1. **AC-1 (COV-140 — justified rather than covered).** A user-supplied
   justification for code that cannot be covered by test is recorded against a
   construct (a source line range in a file). Annotation of a coverage document
   reports, per instrumented line: a line not covered by test inside a region
   whose justification is *valid* reports `justified` (never silently counted as
   covered); a line covered by test reports `covered` regardless of
   justifications; an uncovered line with no valid justification reports
   `uncovered`.
2. **AC-2 (recorded criterion — digest binding and invalidation).** Every
   justification binds to the digest of its associated source at acceptance
   time. When the source changes — the current digest no longer matches the
   recorded one — the justification evaluates `invalidated`, and annotation
   shows the constructs it covered as `uncovered` rather than `justified`, with
   the invalidation surfaced as an advisory carrying the justification id.
   Binding granularity is deliberately the whole source file (conservative:
   editing any line of the file invalidates; a stale justification is never
   shown as valid).
3. **AC-3 (COV-150 — author, date, rationale, invalidation).** A justification
   record carries author, date, and rationale; all three are mandatory and
   validated (non-empty author and rationale, ISO `YYYY-MM-DD` date). The date
   is authored acceptance data, not a wall-clock read.
4. **AC-4 (fail-closed).** A malformed line range (`start < 1` or `end < start`),
   a non-64-hex digest, an empty author/rationale, or a malformed date is
   refused with a named error. Annotation with a digest missing for a justified
   file is a named error — an unverifiable justification never evaluates valid.
5. **AC-5 (determinism).** Annotation output serialises canonically (files
   sorted, lines sorted, statuses fixed vocabulary `covered`/`uncovered`/
   `partial`/`justified`); no wall-clock; no network.
