# WP-COV-08 — Unit-under-test versus harness coverage separation

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-160
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-COV-01 (implemented in this lane: `ectt.cov`), WP-ING-04
(implemented: `ectt.ing` test scope — the named set of units under test,
TOOL-ING-130)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first"** — separation
  operates over gcov-derived documents; Clang must not shape it.

## Acceptance criteria

Derived from the SRS text (SRS-001 §12 line 423: "The tool shall report coverage of
the unit under test separately from coverage of harness, stub, and framework code")
and the PLAN-001 §5.4 row (`WP-COV-08`; COV-160; dependencies COV-01 ING-04).
PLAN-001 §5.4 records **no package-specific acceptance criterion** for this package
(flagged for reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (COV-160 — separation).** `separate_coverage` partitions a coverage
   document's files into the roles `uut`, `harness`, `stub`, `framework` by
   explicit caller-supplied assignment (the UUT set comes from a test scope, the
   harness/stub sets from the harness generator, the framework set from the tool
   runtime). Per-role statement, branch and function totals are computed from that
   role's files only; the UUT figure is never polluted by harness execution.
2. **AC-2 (no guessing, fail-closed).** Roles are never inferred from path shapes,
   extensions or directory conventions: a file without an explicit assignment lands
   in `unclassified` and is surfaced there — never merged into a role, never
   dropped. An assignment naming an unknown role is a named error.
3. **AC-3 (conservation).** The per-role totals plus the unclassified files sum to
   the whole-document totals — no file is counted twice and none is lost
   (checked as an exact arithmetic identity over the same counters).
4. **AC-4 (determinism).** Roles render in fixed order (`uut`, `harness`, `stub`,
   `framework`), files sorted within a role; the result serialises canonically;
   no wall-clock; no network.
