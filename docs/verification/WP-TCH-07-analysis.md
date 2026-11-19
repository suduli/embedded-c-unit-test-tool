# Verification Analysis Note — WP-TCH-07 (First-Run Environment Verification)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-07. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-INS-080 (M, P2, T) — *On first run the tool shall verify its environment
— toolchain presence, versions, and feature availability — and report clearly what is
missing or unsupported* — built on the WP-TCH-01/02 compiler configuration surface.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-INS-080): `verify_environment` checks every declared
  requirement — toolchain presence (executable resolution) and feature availability
  (declared feature availability) — and produces a frozen report with a distinct
  status per requirement: `ok`, `missing`, or `unsupported`.
- AC-2 (falsifiable): the report renders one clear line per requirement naming the
  requirement's target and its status, so a reader can see exactly what is missing or
  unsupported; the lines are deterministic and sorted.
- AC-3 (falsifiable): executable resolution is injectable (tests run without a real
  toolchain) and defaults to a PATH lookup; an unresolvable executable yields
  `missing` naming the executable and the compiler configuration that needs it; a
  feature required but not declared available yields `unsupported`.
- AC-4 (falsifiable): first-run detection via a marker file — a missing (or
  unreadable) marker means a first run is needed; a present marker means it is not.
- AC-5 (falsifiable): reports serialise deterministically and are byte-identical
  across repeated verification with identical inputs.

Scope notes: version *detection* (running `--version` and parsing) is a process-
execution concern (WP-TCH-04 owns compiler version gating, TOOL-TCH-070); this
increment covers presence, declared feature availability, and clear reporting, and
accepts declared minimum-version facts for reporting without executing a compiler.
Real compiler invocation is not claimed here.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-INS-080** | On first run the tool shall verify its environment — toolchain presence, versions, and feature availability — and report clearly what is missing or unsupported. | `src/ectt/tch/environment.py` (`EnvironmentRequirement`, `verify_environment`, `EnvironmentReport`, `EnvironmentCheckResult`, `first_run_needed`), re-exported by `src/ectt/tch/__init__.py` | **Guarantee:** `verify_environment` checks toolchain presence (executable resolution, injectable for tests, defaulting to PATH lookup) and feature availability (against a declared availability mapping); every requirement gets a distinct status — `ok`, `missing`, or `unsupported` — with a detail line naming the executable/feature and the reason. `render()` emits one clear line per requirement in deterministic (kind, target) order; `missing_or_unsupported()` selects exactly the non-ok results. Declared version facts are reported when supplied (never obtained by executing a compiler here — that belongs to WP-TCH-04). `first_run_needed` implements the "on first run" trigger via a marker file (missing or unreadable → first run needed).<br><br>**Honest limits:** version *detection* by compiler execution is WP-TCH-04's gating concern; feature availability comes from a declared mapping, not from probing binaries.<br><br>**Test evidence:** `tests/tch/test_environment.py` — `test_missing_executable_is_reported_missing`, `test_resolved_executable_is_reported_ok`, `test_undeclared_feature_is_reported_unsupported`, `test_declared_unavailable_feature_is_reported_unsupported`, `test_available_feature_is_reported_ok`, `test_mixed_report_names_what_is_missing_or_unsupported`, `test_report_is_sorted_and_deterministic`, `test_missing_or_unsupported_selects_non_ok`, `test_declared_version_is_reported`, `test_unknown_requirement_kind_is_rejected`, `test_blank_target_is_rejected`, `test_first_run_needed_for_missing_marker`, `test_first_run_not_needed_for_present_marker`, `test_report_type_is_frozen` (14 tests, green in the WP-TCH-07 gate run: 547 passed, 4 skipped). |
