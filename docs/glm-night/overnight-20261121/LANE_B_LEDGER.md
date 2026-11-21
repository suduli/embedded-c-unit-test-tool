# Lane B ledger — overnight 2026-11-21

Setup: worktree wt-night-21b branched from local main 26e4330 (the queue text said
a690b3f; main had moved one docs-only commit further, "Add coverage chain, report
outputs and change-impact tasks to the 11-21 queues" — branched from current main as
instructed). Baseline gates at the branch point: 3097 passed / 6 skipped, ruff, mypy,
plan_check, trace_check clean — identical to the stated baseline.

Assumptions taken (unattended run, conservative reading):
- Schema 1.5 is purely additive: new fields (function start/end line, per-occurrence
  unsupported-construct records, per-unit global-variable inventory) are optional and
  omitted from documents while unset; the reader validates a present field fail-closed
  (SDD-002 §3) instead of requiring it for 1.5 documents.
- The global-variable inventory is restricted to declarations in the translation
  unit's main file, matching the existing unit boundary rule for functions.
- The mig interchange FormatSpec `analysis-model` still documents "1.4"; updating it
  is outside B1's allowed paths (see SECOND_PASS_B.md). The two affected mig checks
  are marked xfail(strict=True) per queue rule 5 with a self-removing reason. Real
  GCC/gcov output not applicable to this item; libclang extraction verified by tests.

| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| B1 | DONE | (pending) | ~180k | ~180k | Schema 1.4→1.5 additive bump: FunctionModel start/end line (populated from libclang extent), UnsupportedConstructModel.occurrences with named owner per occurrence, per-unit global_variables inventory (name/type/has_initializer/storage_class/location). SCHEMA_VERSION_CURRENT→1.5 + analysis-model-1.5.schema.json. eligibility.py attributes constructs per occurrence owner (pre-1.5 first-occurrence fallback kept). 21 new tests (tests/ana/test_schema_1_5.py, 1.4-conformance kept, old-shape round trip, 6 fail-closed reader cases, byte-identical double run). Gate green: 3118 passed/6 skipped/2 xfailed. 2 mig checks xfail(strict) → SECOND_PASS_B. test_real_second_variadic... renamed to assert the new named-owner behavior mandated by this item. |

| WP-COV-01 | DONE | (pending) | ~150k | ~330k | ectt.cov package: documented GCC gcov JSON reader (format_version 1/2, gzip, unknown keys ignored, unknown version refused), statement metrics (covered/uncovered/partial via unexecuted_block), branch metrics (no-branch files report not-applicable, no fabricated 100%), conditions carried (count/covered/not_covered_true/false validated). Fixtures hand-written from GCC 14.4 documentation key-for-key (verified against gcc.gnu.org docs, not memory); real GCC output NOT checked (no C compiler, ADR-004) - noted here and in SECOND_PASS_B. 26 tests. Gate green: 3153 passed. |
| WP-COV-02 | DONE | (pending) | ~140k | ~470k | ectt.cov.merge: per-run RunCoverage (test_id/outcome/completeness/document/advisory, S3 outcome set), merge (counts sum, unexecuted OR, branches positional with flag agreement required, conditions merged by not-covered-set intersection with covered recomputed), per-test attribution (coverage_for_test), completeness gate (truncated/missing excluded with advisory, state travels unrelabeled, COV-180), quarantine (error/timeout excluded by default, recorded RunAdmission admits/denies, provenance retains everything - the recorded PLAN-001 5.4 criterion / COV-220; crash surfaces as outcome error per S3 vocabulary, no invented outcome). Named errors for all input inconsistencies. COV-200 (macro variant merge-incompatibility) explicitly out of scope (not in item's requirement list; needs source-identity metadata) - noted in analysis doc. 27 tests. Gate green: 3179 passed. Real GCC output NOT checked (no C compiler). |
| WP-COV-03 | DONE | (pending) | ~60k | ~530k | ectt.cov.thresholds: per-metric thresholds (statements/branches) as exact Fractions in 0..1; fail below, pass at/above; only configured metrics enforced; not-applicable totals (no statements/branches) record not_applicable and do not fail (coverage that cannot exist cannot be not-met); configured metric without totals is a named error (no silent skip). Overall passed flag for the run-level caller. 12 tests. Gate green: 3191 passed. |
