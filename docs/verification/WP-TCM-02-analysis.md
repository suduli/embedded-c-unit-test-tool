# WP-TCM-02 — Data-driven test case model and on-disk format

Status: in progress (overnight lane A, 2026-11-19)
Requirements: TOOL-TCD-020, TOOL-TCD-030, TOOL-TCD-040, TOOL-TCD-140
Design elements: DSN-TCM-020 (model + format), DSN-TCM-110 (stable identity)
Dependencies: WP-ANA-04 (implemented: `ectt.ana`), WP-PRJ-01 (implemented: `ectt.prj`)
Decisions applied as written (not re-decided):
- **D-02, option (a)** (owner answer 2026-11-19): "Stable ids plus content digests" — test and result identities are stable ids bound to content digests; separate revision entities are not adopted; digest binding is the staleness mechanism. (SDD-003 §6/§7 amendment, commit 15719e4.)
- **ADR-002 (Accepted)**: restricted YAML is the surface syntax for authored project-state documents; surface syntax confined to one adapter. SRS §27 q6 asked for the concrete format; ADR-002 answers it for authored project state, so no new decision is taken tonight.

## Acceptance criteria

Derived from the SRS texts (SRS-001 lines 298–302, 322), DSN-TCM-020/DSN-TCM-110 statements, SDD-002 §5 (S2 model sketch), SDD-003 §2.1 (`.tests` grouped per unit), §5 (schema versioning), §6/§7 (identity + digest binding as amended for D-02), and ADR-002. PLAN-001 §5.4 records no package-specific criterion for CMP-TCM (flagged for reconciliation) — these are the derived, reviewable criteria:

1. **AC-1 (TCD-020, TCD-040 — the model is data).** A data-driven test case can be authored entirely as data carrying every field TOOL-TCD-040 names: input parameter values, initial values of accessed globals, expected return value, expected final values of globals, expected output parameter values, and stub behaviour and expectations. Loading a well-formed `.tests` file yields case records exposing exactly these fields plus identity and origin.
2. **AC-2 (TCD-040 — completeness is enforced).** A case missing any of the TOOL-TCD-040 sections (inputs, expected, stubs), an empty identifier, or an unknown origin is rejected at load with a named error carrying the file path — not silently defaulted.
3. **AC-3 (TCD-030 — plain-text diffable format).** The on-disk format is restricted YAML text per ADR-002: UTF-8, LF endings, every scalar double-quoted, deterministic key order with `schema_version` first. Round-trip is idempotent: `dump(parse(dump(parse(text)))) == dump(parse(text))`. Anchors, aliases, explicit tags, merge keys, duplicate keys, and multi-document streams are rejected (adapter-enforced).
4. **AC-4 (TCD-140 — stable unique identity).** Each case carries an identifier assigned at creation that survives a values-only edit: load → change a field → save → load yields the same id with different content. The store rejects a duplicate identifier within one file with a named error. Identifiers are never derived from content.
5. **AC-5 (D-02 — digest binding).** Each case record exposes a content digest computed deterministically (SHA-256 over the canonical JSON encoding of the case content, excluding the id and the digest itself). Editing any content field changes the digest while the id stays; two cases with identical content have identical digests; the digest is process-independent (no `PYTHONHASHSEED` dependence) and insertion-order-independent.
6. **AC-6 (determinism — no wall-clock, no network).** Serialization output contains no timestamps and no wall-clock values; two dumps of the same model are byte-identical; the implementation performs no network I/O.
7. **AC-7 (schema versioning).** A `.tests` document without `schema_version`, with a non-integer version, or with a version above the supported maximum is rejected with the corresponding named error from the shared version-dispatch machinery (SDD-003 §5).

## Edge and error cases covered

- duplicate case id in one file (AC-4)
- missing required section: `inputs` / `expected` / `stubs` absent (AC-2)
- empty identifier (AC-2)
- unknown origin author (AC-2)
- missing/invalid/unsupported `schema_version` (AC-7)
- restricted-YAML hazards: alias, duplicate key (AC-3, adapter-level)

## Requirement → implementation → tests

| Requirement | Implementation | Tests (tests/tcm/test_datacases.py) |
|---|---|---|
| TOOL-TCD-020 | `ectt.tcm.datacases` — `DataDrivenTestCase` + section models; every TOOL-TCD-040 field carried as data | `test_full_model_round_trip_carries_every_field` |
| TOOL-TCD-030 | restricted YAML `.tests` files via `ectt.prj.yaml_adapter.RestrictedYamlAdapter`; idempotent canonical dump; comment-preserving atomic save | `test_dump_is_quoted_schema_first_deterministic_text`, `test_round_trip_is_idempotent`, `test_two_dumps_of_same_model_are_byte_identical_and_carry_no_timestamps`, `test_yaml_hazards_are_rejected_at_text_level`, `test_save_is_noop_when_identical_and_guards_comments`, `test_scalar_unknown_key_is_preserved_through_round_trip` |
| TOOL-TCD-040 | required `inputs`/`expected`/`stubs` sections with per-section key validation | `test_missing_required_section_is_rejected`, `test_unknown_structured_key_is_refused_not_dropped`, `test_full_model_round_trip_carries_every_field` |
| TOOL-TCD-140 | id assigned at creation, never derived; duplicates rejected per file; id survives values-only edits | `test_identifier_survives_value_edit`, `test_duplicate_identifier_within_one_file_is_rejected`, `test_value_edit_changes_digest_and_id_stays` |
| TOOL-TCD-140 (uniqueness), DSN-TCM-110 | `parse_test_cases_document` duplicate check | `test_duplicate_identifier_within_one_file_is_rejected` |
| D-02 option (a) digest binding | `compute_case_digest` + `DataDrivenTestCase.content_payload` (canonical JSON, id/digest excluded); `stale` flag; write refuses digest-less records | `test_digest_is_order_and_process_independent`, `test_recorded_digest_binding_flags_stale_never_current`, `test_value_edit_changes_digest_and_id_stays`, `test_dump_refuses_to_write_a_case_without_recorded_digest` |
| SDD-003 §5 versioning | shared `dispatch_schema_version` against `TEST_CASES_KIND` | `test_missing_schema_version_is_rejected`, `test_unsupported_schema_version_is_rejected`, `test_invalid_schema_version_is_rejected` |
| file-level behaviors | load/save round trip; named read error; structural malformation | `test_load_and_save_round_trip_on_disk`, `test_unreadable_file_raises_named_error`, `test_structural_malformation_is_rejected` |

Uncovered: none — all derived acceptance criteria AC-1..AC-7 have at least one named test.

## Second-pass items

- PLAN-001 §5.4 has no package-specific acceptance criterion for WP-TCM-02; the derived criteria above should be reviewed by the owner and the reconciled text written into the plan (owner edit; PLAN-001 is out of lane scope tonight).
- SRS §27 q6 ("choose the concrete format before implementation") is answered for authored project state by ADR-002 (restricted YAML); the SRS question text may be closed by the owner.
