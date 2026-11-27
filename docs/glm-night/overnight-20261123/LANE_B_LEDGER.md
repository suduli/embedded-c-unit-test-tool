# Lane B ledger — overnight 2026-11-23

Setup: worktree wt-night-23b branched from local main b9b1262 ("Merge
glm-night/20261123-a into main"). The queue text named b8ae29f as the branch
point; main had moved 22 commits further when this run started (lane A's
20261123 work plus the tracker merge are already in), so the queue was written
before lane A merged. Branched from current main as the setup block instructs.

Baseline gates at the actual branch point (each gate run and checked
separately):

- pytest: 3819 passed, 6 skipped, 1 xfailed, 1 warning — NOT the 3710 / 6 the
  queue states for b8ae29f. The +109 passed and the xfail are lane A's merged
  work, not lane B changes.
- ruff, mypy (198 files), plan_check (346 requirements / 344 allocations / 191
  packages), trace_check: all clean.

Pre-existing at the branch point, recorded here so lane B effects can be told
apart from them (lane B does not touch either one; both are outside this lane's
allowed paths):

- xfail(strict) `tests/core/test_properties_seeded.py::test_changed_excludes_missing_files`
  — lane A's recorded selfverify defect, fix queued in SECOND_PASS_A (A9).
- warning `PytestCollectionWarning` raised from `tests/cli/test_compose.py`
  (a `TestCase*` dataclass name that pytest tries to collect).

Assumptions taken (unattended run, conservative reading):
- B1: "a claim not supported by data is refused" is read as a caller-named claim: the
  caller lists the claims the report may make, and each is checked against the supplied
  data. Claims are opt-in; with none requested the report makes none and lists every
  known claim under `not_claimed`.
- B1: "no target execution unless the data says so" resolves to "never claimed", because
  no data the tool records can say so today (target run plans only; execution metadata
  is documented as never branched on; a host profile is not target evidence).
- B1: this run started on 2026-11-27 (afternoon), not on the queue's night; the 05:30
  stop rule is measured from the start of the run.

| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| B1 | DONE | (pending) | ~140k | ~140k | WP-REP-05 (TOOL-REP-060, TOOL-REP-140): ectt.rep.certification builds a certification verification report from result, coverage and trace data via narrow data-class imports only (MetricTotals, ThresholdResult, Justification, TraceabilityMatrix, HostProfile). Contents: tool version/build/dependency and schema versions/provenance digest; execution facts recorded verbatim (never interpreted) plus host profile; every test with status and definition digest; coverage per metric as raw counters beside the stated criteria with unmeasured / not-applicable / not-measured lists; justified exclusions as valid / invalidated / unverifiable (an unverifiable or invalidated justification is never counted); the traceability matrix; a scope statement naming units, tests, requirements and what is excluded (tests not executed, partial run, untraced tests, unverified requirements, metrics not measured). Missing data: each absent input named in missing_inputs, the section reads missing, an undeterminable list is None (never empty), absent criteria never read as met. Claims: opt-in and checked against the data; an unsupported claim is refused (claim_not_supported) before anything is written; target_executed and mcdc_measured are never supported and are always under not_claimed, so every known claim is either made or explicitly not claimed with a reason. Fail-closed: unknown_claim, unknown_metric (incl. mcdc passed in as a figure), criteria_metrics_mismatch, unknown_verdict. Byte-identical under input order; no clock read; creation timestamp not rendered. 44 tests. Analysis note: docs/verification/WP-REP-05-analysis.md. SECOND_PASS_B: TOOL-REP-140 says every report; only this report carries a scope statement. Gate: 3863 passed / 6 skipped / 1 xfailed (pre-existing) / 1 warning (pre-existing); ruff, mypy (199 files), plan_check, trace_check clean — each gate checked on its own. Real GCC output: not applicable to this item. |
| B2 | SECOND-PASS | — | ~35k | ~175k | WP-COV-06 (TOOL-COV-080/190): NO CODE WRITTEN. The item's premise does not hold in the repo: the analysis model's decision inventory at schema 1.5 is a single status record (`DecisionInventoryModel.status/detail`), and the assembler hard-codes `not_extracted` ("decision extraction is not implemented in this analyzer build"); the per-function `decisions[]` the published schema defines (id, line, conditions) has no field on `FunctionModel`, nothing writes it and the reader drops it. The dependency WP-COV-05 is not implemented. The recorded PLAN-001 §5.4 criterion needs a probed condition maximum recorded per backend: nothing records one (tch/gating.py holds a documentation-derived table, which TOOL-COV-190 forbids substituting), and no compiler is installed to probe with. Checked against the GCC manuals (14.4.0 and 15.2.0): the `-fcondition-coverage` entry documents no maximum, no limit-tuning option and no list of non-instrumentable expressions, and the gcov reference page has no not-instrumented marker. With no decisions to enumerate, every construct would be `no_data`; any implementation would rest on invented inputs. Details and what is needed in SECOND_PASS_B. Also relevant to the open SRS-Q2: the gcov manual states GCC's condition coverage is masking MC/DC. |
| B3 | DONE | (pending) | ~110k | ~285k | WP-COV-11 (TOOL-COV-170): ectt.cov.coupling analyze_coupling(model, document) -> CouplingReport; reads the analysis model, never changes it. Control coupling: every call in the model's call graph forms a caller-to-callee pair with its sites; exercised iff a site returned; not_exercised when every site has call data and none returned (call_site_not_reached / call_never_returned); otherwise not_determinable with a reason (callee_not_identified, file_not_in_coverage, call_line_not_in_coverage, no_call_data, ambiguous_call_site). Data coupling: per inventory global, recorded writers x readers; exercised iff both functions executed. Stated in the output itself (data_pairs_basis) that this is function-level, because the model records a global access by name without a line. A global with no recorded access is not_determinable (no_recorded_access). Nothing is guessed: a call through a pointer never gets a target; a call site matches a gcov call record only when its line holds exactly one of each (neither side names the callee); a file-scope static is keyed by unit and name, so same-named statics in two units are never coupled; a callee defined in two units is assigned to neither. Data only: no score, no verdict about any objective. Refused: unknown_call_via, unknown_call_classification, indirect_call_names_callee, unknown_global_access. A failed unit is listed as not analysed. Byte-identical under input order and path spelling. 29 tests, one driven by the real analyzer's output. Analysis note: docs/verification/WP-COV-11-analysis.md. Real GCC output NOT checked: call matching is by line, one-to-one, and GCC's line attribution for macro-expanded or same-line calls is unverified (such sites read not_determinable). Gate: 3892 passed / 6 skipped / 1 xfailed / 1 warning (both pre-existing); ruff, mypy (200 files), plan_check, trace_check clean, each gate checked on its own. FIX in a separate commit under B3: while exporting the coupling API, found that ectt.cov.__all__ declared eight justification names (Justification, annotate_coverage, ...) that the package never imported, so `from ectt.cov import Justification` raised ImportError on main. The names were added to __all__ by lane B's own 2026-11-21 WP-COV-09 commit without the import; no test noticed because tests import from ectt.cov.justification directly. Restored the import and added tests/cov/test_public_api.py (declared names are bound, nothing is declared twice, every module's public names are reachable); the guard was run against the unfixed package first and failed naming all eight. The same scan found unbound declared exports in three packages outside this lane (ana, ing, tcm) — recorded in SECOND_PASS_B, not touched. |
