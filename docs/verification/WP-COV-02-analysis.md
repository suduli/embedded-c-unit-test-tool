# WP-COV-02 — Coverage merge and per-test attribution

Status: in progress (overnight lane B, 2026-11-21)
Requirements: TOOL-COV-110, TOOL-COV-120, TOOL-COV-180 (queue scope); the recorded
PLAN-001 §5.4 acceptance criterion for this package adds the TOOL-COV-220
quarantine semantics, which the merge implements as its admission rule.
Design elements: DSN-COV-* per PLAN-001 §3 (CMP-COV)
Dependencies: WP-COV-01 (implemented in this lane: `ectt.cov` gcov reader + model)
Decisions applied as written (not re-decided):
- **ADR-004 coverage backend (owner answer, 2026-11-21): "GCC first"** — merging
  operates on gcov-derived documents from WP-COV-01; Clang must not shape it.
- **No C compiler on this machine:** merge semantics are validated against
  hand-written fixtures from the documented gcov format. **Real GCC output has not
  been checked.**

## Recorded acceptance criterion (PLAN-001 §5.4, quoted)

> `WP-COV-02` — A profile flushed by a run that then crashes is retained but excluded
> from the aggregate until explicitly admitted per run; the aggregate figure never
> includes quarantined data, and per-run provenance still shows it.

(Quoted verbatim from PLAN-001 §5.4 line 250; it is the TOOL-COV-220 semantics bound
to this package's merge.)

## Acceptance criteria

Derived from the SRS texts (SRS-001 §12 lines 417, 418, 425, 428), the PLAN-001 §5.4
row and the recorded criterion above. PLAN-001 §5.4 records no *further* package-
specific acceptance criteria for WP-COV-02 beyond the quoted quarantine criterion
(flagged for reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (COV-110 — merge).** Coverage documents from multiple test executions
   merge into one result set: per file, per line — counts sum, `unexecuted_block`
   ORs over contributing runs; per line, branches merge positionally with counts
   summed and `fallthrough`/`throw` required to agree (a mismatch is a named
   error); per line, condition outcomes merge conservatively — a term index is
   not-covered-true/false in the merge iff it is not-covered in *every*
   contributing run, and the merged `covered` is recomputed from the merged
   not-covered sets. A line with conditions in some contributing runs and none in
   others is refused (named error) — an unrecorded outcome may not be assumed
   covered. Files union by path, lines union by number.
2. **AC-2 (COV-120 — per-test attribution).** Every run keeps its own coverage
   record under its test id; per-test statement/branch totals are computed from
   that record alone. Duplicate test ids are refused with a named error.
3. **AC-3 (COV-180 — completeness state travels).** Every run's artifact carries a
   recorded completeness state — `complete`, `truncated`, or `missing` — surfaced
   through the merge exactly as recorded, never relabelled. A `truncated` or
   `missing` artifact forces every construct it would have measured out of the
   aggregate (its counts contribute nothing) and its advisory text travels with
   the result for the report. A `truncated` record may retain its partial
   document in per-run provenance; a `missing` record carries no document.
4. **AC-4 (recorded §5.4 criterion — quarantine).** A run whose recorded outcome
   is `error` or `timeout` is retained in per-run provenance but excluded from
   the aggregate unless a recorded per-run admission decision explicitly admits
   it. In the S3 result vocabulary (ectt.exh: `pass | fail | error | timeout |
   not_run`) a harness crash surfaces as outcome `error`; there is no separate
   `crash` outcome to invent. A recorded admission decision can also *deny* a run
   whose outcome would otherwise be admitted. The aggregate figure never includes
   quarantined or denied data.
5. **AC-5 (fail-closed merge inputs).** Unknown completeness states, unknown
   outcome values (outside the S3 set), duplicate test ids, a `complete` run
   without a document, branch-count or condition-count mismatches for the same
   line across runs, and condition-presence inconsistencies are named errors —
   never silently resolved.
6. **AC-6 (determinism).** The merged document dumps to canonical JSON bytes with
   `schema_version` first; no wall-clock; no network.

## Requirement → implementation → tests

| Requirement | Implementation | Tests (tests/cov/) |
|---|---|---|
| TOOL-COV-110 | `ectt.cov.merge.merge_run_coverage` — union/sum/intersection rules over gcov documents | `test_merge_sums_line_counts_across_runs`, `test_merge_unions_lines_across_files`, `test_merge_or_unexecuted_block`, `test_branch_flag_disagreement_is_refused`, `test_condition_outcomes_merge_conservatively`, `test_condition_presence_mismatch_is_refused` |
| TOOL-COV-120 | `ectt.cov.merge.coverage_for_test` over retained per-run records | `test_per_test_coverage_is_attributed`, `test_duplicate_test_ids_are_refused` |
| TOOL-COV-180 | `RunCoverage.completeness` + advisory carry, exclusion from aggregate | `test_truncated_artifact_is_excluded_with_advisory`, `test_missing_artifact_is_excluded_with_advisory`, `test_completeness_state_travels_unrelabeled` |
| §5.4 quarantine criterion | default quarantine for `error`/`timeout` outcomes + recorded `RunAdmission` decisions | `test_error_outcome_is_quarantined_by_default`, `test_timeout_outcome_is_quarantined_by_default`, `test_explicit_admission_admits_quarantined_run`, `test_explicit_denial_excludes_run`, `test_quarantined_run_stays_in_provenance` |
| AC-5 | named errors | `test_unknown_completeness_is_refused`, `test_unknown_outcome_is_refused`, `test_complete_run_without_document_is_refused`, `test_branch_count_mismatch_is_refused`, `test_condition_count_mismatch_is_refused` |
| AC-6 | canonical dump | `test_merged_dump_is_canonical_and_byte_identical` |

## Uncovered (out of WP-COV-02 scope)

- TOOL-COV-200 (macro/preprocessing-variant merge-incompatibility) — named in the
  PLAN-001 §5.4 requirements column but not in this work item's requirement list;
  it needs source-identity metadata the gcov format does not carry and is left to
  a follow-up work item (flagged in the lane ledger, not implemented here).
- Advisory rendering in human reports — WP-REP-* scope; the advisory travels as data.
- Real GCC output verification (no C compiler; ADR-004) — needs a GCC run; recorded
  in the lane ledger and second-pass file.
