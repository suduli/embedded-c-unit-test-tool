# Verification Analysis Note — WP-BLD-01 (Host Build Orchestration and Incremental Rebuild)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-BLD-01. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-EXE-080 (S, P1, T) — *The tool shall support incremental rebuild,
recompiling only artifacts affected by a change*.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-EXE-080): with no prior build record, the incremental
  planner schedules every requested artifact for compilation (reason `no_record`) —
  the first build builds everything.
- AC-2 (falsifiable): an artifact whose recorded inputs — source digest, compiler
  configuration name, and flag tuple — are unchanged since its record is planned as
  up to date and is not scheduled for recompilation.
- AC-3 (falsifiable): changing exactly one input dimension — the source digest, or
  the compiler configuration, or the flags — schedules exactly the affected artifact
  for recompilation and leaves the others up to date; no unaffected artifact is ever
  scheduled ("only artifacts affected by a change").
- AC-4 (falsifiable): every decision records its reason(s); a decision can carry
  several reasons (a source and its flags changed together); planning output is
  ordered deterministically by output path; two artifacts claiming the same output
  path are rejected with a named error.
- AC-5 (falsifiable): planning is a pure function of the requested specs and the
  prior records — identical inputs yield identical decisions with identical reasons,
  and the decision set serialises to a deterministic mapping.

Scope notes: this increment ships the incremental *planning* core — the decision of
what to recompile and why — which is the falsifiable core of TOOL-EXE-080. Invoking a
real compiler binary, parallel execution and rebuild timings belong to later build
work (the host build executor consumes this planner with the WP-TCH-02 compiler
configurations). Staleness is content-based (digests), matching the tool's
determinism requirements (TOOL-NFR-060) and the TOOL-ING-100 staleness philosophy;
mtimes are deliberately not consulted.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-EXE-080** | The tool shall support incremental rebuild, recompiling only artifacts affected by a change. | `src/ectt/bld/plan.py` (`ArtifactSpec`, `BuildRecord`, `RebuildDecision`, `IncrementalPlanner`), `src/ectt/bld/errors.py` (`DuplicateArtifactError`, `InvalidArtifactSpecError`), re-exported by `src/ectt/bld/__init__.py` | **Guarantee:** the planner compares each requested artifact against its previous-build record on three content dimensions — source digest, compiler configuration name, flag tuple — and schedules recompilation exactly when one differs (or no record exists). A build where nothing changed schedules nothing; changing one dimension of one artifact leaves every other artifact up to date. Reasons are recorded per decision (`no_record`, `source_changed`, `config_changed`, `flags_changed`) and accumulate; ordering is by output path; duplicate output paths and malformed specs are refused with named errors.<br><br>**Analysis argument:** "recompiling only artifacts affected by a change" is falsified by producing a plan that schedules an unaffected artifact, or fails to schedule an affected one. The plan is a pure function of (specs, records) — staleness is content-based via digests, so mtimes, filesystem races and non-determinism cannot enter the decision — and `RebuildDecision.to_dict()` is deterministic, which lets a later executor consume the plan verbatim.<br><br>**Not covered:** invoking the compiler binary, link orchestration, parallel execution and rebuild timing measurement (the build executor that consumes this planner is later build work); response-file and dependency-file (`-MMD`) staleness inputs are ingestion/build-executor surfaces.<br><br>**Test evidence:** `tests/bld/test_plan.py` — `test_first_build_schedules_everything`, `test_unchanged_inputs_are_up_to_date`, `test_only_source_changed_artifact_recompiles`, `test_only_flags_changed_artifact_recompiles`, `test_only_config_changed_artifact_recompiles`, `test_multiple_changes_accumulate_reasons`, `test_planning_output_is_deterministically_ordered`, `test_duplicate_output_path_rejected`, `test_blank_fields_rejected`, `test_plan_is_a_pure_function`, `test_recorded_builds_make_followup_plan_up_to_date` (11 tests, green in the WP-BLD-01 gate run: 490 passed, 4 skipped). |
