# Verification Analysis Note — WP-CORE-04 (Provenance Record and Version Identification)

Analysis evidence for requirements verified under WP-CORE-04. Status: **implemented for the
facilities and every artifact whose producer is inside this item's allowed paths**
(`src/ectt/core`, `src/ectt/rep`); other artifact families are listed below with their
producer and status — per the item instruction, producers outside the allowed paths are
skipped and recorded, not edited.

Re-verified 2026-11-19 (night run, lane B, worktree `wt-night-b`): the record/report facility
evidence from chat 2 (2026-11-18) stands unchanged; this pass closes the in-scope part of the
"embed in every artifact" remainder via WP-REP-06 (format 1.1) and adds the reproduction check
the prior pass named as missing.

## Embedding matrix (TOOL-QUA-060, artifact by artifact)

| Artifact | Producer | Provenance embedded | Status |
|---|---|---|---|
| Report model (format 1.1) | `ectt.rep` | Yes — full core `ProvenanceRecord` (tool version, build id, interpreter, schema versions, result-set digest, execution timestamp) plus execution facts; digest verified on load; tampering refused | **Done** (WP-REP-06, this branch) |
| Analysis model (S1, schema 1.4) | `ectt.ana` | Yes — its own `ProvenanceModel` (tool version, front-end, generated_at, per-input digests); shape predates the core facility and covers the reproduction facts | **Done by an equivalent record** (unifying onto the core facility is an owner-optional schema change; outside this item's paths) |
| Result set (S3) | `ectt.exh` | No provenance block of its own; its digest *is* recorded in every report built from it (`provenance.input_digests["result_set"]`) | **Skipped — producer outside this item's allowed paths** (SECOND_PASS: add a provenance block or accept digest-reference discipline) |
| Test-case files (restricted YAML) | `ectt.tcm` | Per-file digest binding exists (D-02 staleness); no tool-provenance block | **Skipped — producer outside this item's allowed paths** (SECOND_PASS) |
| Project store shards | `ectt.prj` | No provenance block | **Skipped — producer outside this item's allowed paths** (SECOND_PASS) |

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-QUA-060** | The tool shall record, in every artifact it generates, sufficient information to reproduce that artifact. | `src/ectt/core/provenance.py` (`build_provenance`, `ProvenanceRecord`), `src/ectt/rep/model.py` (format 1.1 embedding, digest verification), `tests/core/test_provenance.py`, `tests/rep/test_reproduction.py` | **Guarantee (sufficient facts):** the record holds the tool version, build identifier, interpreter version, caller-supplied dependency versions, schema versions and input digests. The digest is SHA-256 over the canonical encoding of the hashed portion; `generated_at` is carried beside the digest and excluded from it, so two clocks give the same digest.<br><br>**Guarantee (embedded, report artifact — closed this pass):** every report model of format 1.1 embeds the record (`build_provenance` with schema versions `report_model`/`result_set` and the result-set digest), and `load_report_model` recomputes the embedded digest and refuses mismatches — the provenance cannot be silently rewritten. The report id binds the whole body including the provenance.<br><br>**Guarantee (reproduction check — closed this pass):** the replay test the prior pass named as missing now exists: identical inputs rebuilt in the same environment produce byte-identical report dumps with identical embedded provenance digests; any changed input fact changes both (`tests/rep/test_reproduction.py`).<br><br>**Test evidence:** `tests/core/test_provenance.py` — `test_record_carries_tool_interpreter_dependency_schema_and_input_facts`, `test_digest_is_stable_for_identical_facts`, `test_digest_changes_with_any_hashed_fact`, `test_timestamp_is_recorded_but_never_hashed`, `test_no_clock_means_no_timestamp_field`, `test_canonical_json_is_byte_identical_across_runs`, `test_dependency_and_input_maps_are_sorted_regardless_of_insertion_order`. `tests/rep/test_reproduction.py` — `test_identical_inputs_reproduce_identical_reports`, `test_changed_input_changes_the_artifact_and_its_provenance`. `tests/rep/test_model.py` — `test_model_carries_execution_and_provenance`, `test_load_refuses_tampered_provenance`. |
| **TOOL-INS-110** | The tool shall report its version, build identifier, and the versions of its principal dependencies on request. | `src/ectt/core/provenance.py` (`version_report`, `tool_version`, `BUILD_ID_ENV`), `tests/core/test_provenance.py` | **Guarantee (version from the installation):** `tool_version()` reads the installed distribution's metadata. When the package is not installed it reports `unknown`, not the source-tree constant `__version__`, because an unprovable version is not reported as fact.<br><br>**Guarantee (build identifier from the build):** the identifier comes from the `ECTT_BUILD_ID` environment variable, read at call time; when the build did not record one it reports `unset`. The tool does not invent a build identity from git or the clock.<br><br>**Guarantee (dependencies on request):** `version_report` answers with the tool, version, build, interpreter and the dependency versions the caller passes. The report artifact (format 1.1) surfaces the tool version through `provenance_facts()` in both renderers.<br><br>**Test evidence:** `test_build_id_comes_from_the_environment_when_recorded`, `test_tool_version_is_not_faked_when_the_package_is_not_installed`, `test_version_report_answers_on_request_with_dependencies`; `tests/rep/test_renderers.py::test_renderers_cannot_disagree[*]` (provenance clause). |

## Not yet covered

- **Result set, test-case files, project shards carry no provenance block.** Their producers
  are in the branch but outside this item's allowed paths; listed in the embedding matrix
  above and recorded in SECOND_PASS. The report already records the result-set digest.
- **Build identifier is not set by any build.** Nothing in the repository sets
  `ECTT_BUILD_ID`. Until a build does, every record reports `unset` (honest, but weak
  evidence of which build made an artifact) — release-engineering follow-up.
- **Dependency versions are the caller's job.** The report passes none today; the analysis
  layer records libclang via its own `front_end` fact. Wiring library versions into the core
  record belongs to each producer (allowed-path limit).
- **Unifying ana's `ProvenanceModel` onto the core facility** is an additive schema change
  per artifact — owner-optional reconciliation, not decided here.

## Design notes

- **Why the timestamp is outside the hash.** A timestamp in the hash would make two identical
  productions produce different digests, so a digest could never prove a match. Keeping it
  beside the digest keeps the timestamp available without weakening the proof.
- **Why no source-tree version fallback.** The source constant is what the tree says, not
  what is installed. Reporting it as the installed version would make a stale checkout look
  current.
- **Why the embedded record is digest-verified on load.** A provenance block a reader will
  not verify is decoration; verification makes tampering visible instead of silent.

## Lane B re-verification (2026-11-19, worktree wt-night-b)

The facility tests remain green (full gate block green: pytest, ruff, mypy, plan_check,
trace_check). The in-scope embedding remainder is closed: the report artifact (the only
artifact producer inside this item's allowed paths) embeds and digest-verifies the core
provenance record since WP-REP-06 (f21c2fc), and the reproduction check exists. Out-of-scope
artifact families are listed in the matrix and SECOND_PASS rather than edited here.
