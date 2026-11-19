# Verification Analysis Note — WP-SEC-03 (Untrusted-Project Warning and Configuration-Is-Data)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-SEC-03. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-SEC-050 (M, P2, D) — *The tool shall warn before executing user-supplied
code — including test cases, stub bodies, and build scripts — from a project the user
has not previously opened* — and TOOL-SEC-070 (M, P2, T) — *The tool shall not execute
code embedded in project configuration files. Configuration shall be data, not
script.*

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-SEC-050): a trust decision for a project root is
  derivable from a persisted, user-controlled trust record: a project the user has
  previously opened is `known`; a project not in the record is `untrusted`; and an
  untrusted decision renders a warning naming the project and the kinds of
  user-supplied code about to run (test cases, stub bodies, build scripts).
- AC-2 (falsifiable): marking a project opened persists it to the trust record;
  the record file is deterministic, sorted JSON (version-controllable text); a
  missing record file behaves as "nothing trusted"; the same project is never
  duplicated in the record.
- AC-3 (falsifiable, from TOOL-SEC-070): configuration reaching the tool passes a
  data-only validation: every value in a configuration document must be one of the
  data types (mapping, list, string, integer, float, boolean, None); any other
  value — a callable, a module, an arbitrary object — is rejected with a named error
  before the configuration is used, so embedded code cannot reach execution.
- AC-4 (falsifiable): the data-only validator recurses through mappings and lists
  and reports the offending key path; a fully data document passes and is returned
  unchanged.

Scope notes: the trust decision is the *gate surface* the command layer calls before
executing user code; rendering the warning interactively (prompt/CLI flow) is the
command layer's UX. TOOL-SEC-070 is enforced by type discipline plus the restricted
YAML loader already in the project store (no tags/anchors/code); the validator here
is the boundary check that runs regardless of where the mapping came from. Method D
for TOOL-SEC-050 (demonstration): the demonstration is the decision + warning-text
evidence below; a live CLI demonstration is a runtime-evidence run.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-SEC-050** | The tool shall warn before executing user-supplied code — including test cases, stub bodies, and build scripts — from a project the user has not previously opened. *(Method D)* | `src/ectt/sec/trust.py` (`UntrustedProjectTracker`, `TrustDecision`, `warning_text`, `TrustRecordError`), re-exported by `src/ectt/sec/__init__.py` | **Guarantee:** the decision surface distinguishes known from untrusted projects from a persisted, user-controlled trust record: an unopened project yields `requires_warning=True` and `warning_text` names the project and all three user-code kinds (test cases, stub bodies, build scripts); a previously opened project yields no warning requirement. Marking opened is idempotent and persists to deterministic, sorted JSON (byte-identical records regardless of marking order); a missing record behaves as nothing trusted; malformed or wrongly shaped records are named errors (`TrustRecordError`).<br><br>**Demonstration argument (method D):** the demonstrated sequence is: consult `tracker.decision(root)` before executing any user code → untrusted → render `warning_text(decision)` → on confirmation `tracker.mark_opened(root)` → subsequent runs are known. The interactive prompt is the command layer's UX; the decision and warning content demonstrated here are the gate's falsifiable core.<br><br>**Test evidence:** `tests/sec/test_trust.py` — `test_unknown_project_is_untrusted`, `test_missing_record_behaves_as_nothing_trusted`, `test_mark_opened_persists_and_project_becomes_known`, `test_mark_opened_is_idempotent`, `test_record_is_deterministic_sorted_json`, `test_warning_text_names_project_and_code_kinds`, `test_known_project_produces_no_warning_requirement`, `test_malformed_record_is_named_error`, `test_wrongly_shaped_record_is_named_error`. |
| **TOOL-SEC-070** | The tool shall not execute code embedded in project configuration files. Configuration shall be data, not script. | `src/ectt/sec/configuration_data.py` (`validate_configuration_is_data`, `ConfigurationIsNotDataError`), re-exported by `src/ectt/sec/__init__.py`; complements the restricted YAML loader in the project store | **Guarantee:** every configuration document passes the data-only boundary check before use: mappings and lists are recursed (string-keyed only), and any value that is not a data type — a callable, module, or arbitrary object — is refused with `ConfigurationIsNotDataError` naming the offending key path, before the configuration can reach execution. A fully data document passes unchanged; booleans are data (not callable-trap false positives).<br><br>**Analysis argument:** with the restricted YAML loader (no tags, anchors, code) and this type boundary, a configuration cannot carry executable content into the tool; the boundary runs regardless of where the mapping came from, so a config composed programmatically cannot smuggle a callable either.<br><br>**Test evidence:** `tests/sec/test_configuration_data.py` — `test_data_only_document_passes_unchanged`, `test_nested_lists_and_mappings_recursed`, `test_callable_value_is_rejected_with_key_path`, `test_arbitrary_object_value_is_rejected`, `test_module_value_is_rejected`, `test_non_string_key_is_rejected`, `test_error_derives_from_security_base`, `test_bool_is_data_not_callable_trap`. |
