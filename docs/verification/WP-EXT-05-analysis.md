# Verification Analysis Note — WP-EXT-05 (Hardware Inventory and Target Failure Classification)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-EXT-05. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TGT-080 (S, P3, D) and TOOL-TGT-090 (S, P3, T).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TGT-080): a declarative hardware inventory describes
  connected targets with exactly the documented fields — identifier, platform, probe
  type, serial device, flash timeout — as frozen records in a deterministic,
  serialisable inventory; duplicate identifiers and unknown probe types are named
  errors; a target is looked up by identifier.
- AC-2 (falsifiable, from TOOL-TGT-090): target execution failures — flash failure,
  no output, target reset, watchdog — are detected and classified from probe/simulator
  output text, distinguished from test failures: the classifier returns a target
  failure verdict only for target-level signatures; clean output and test-failure
  lines (PASS/FAIL) never classify as target failures; the verdict is deterministic
  and serialisable.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TGT-080** | The tool shall support a declarative hardware inventory describing connected targets: identifier, platform, probe type, serial device, and flash timeout. *(Method D)* | `src/ectt/ext/inventory.py` (`TargetDescriptor`, `HardwareInventory`, `UnknownTargetError`), probe types from WP-EXT-02's `PROBE_FAMILIES`, re-exported by `src/ectt/ext/__init__.py` | **Guarantee:** the inventory record carries exactly the five documented fields; duplicate identifiers, unknown probe types (checked against the documented probe families), blank fields and non-positive flash timeouts are named errors; a target is looked up by identifier; the inventory is frozen and serialises deterministically regardless of entry order — the demonstration is the two-target inventory exercised in tests.<br><br>**Test evidence:** `tests/ext/test_inventory.py` — `test_inventory_describes_connected_targets`, `test_duplicate_identifier_is_named_error`, `test_unknown_probe_type_is_named_error`, `test_blank_fields_and_bad_timeout_are_named_errors`, `test_lookup_unknown_id_is_named_error`, `test_inventory_is_frozen_and_deterministic`. |
| **TOOL-TGT-090** | The tool shall detect target execution failures — flash failure, no output, target reset, watchdog — and distinguish them from test failures. | `src/ectt/ext/inventory.py` (`classify_target_failure`, `TargetFailure`, `FAILURE_*` constants) | **Guarantee:** output text is classified against the documented target-level signatures — flash failure, target reset, watchdog, and the empty-stream `no_output` verdict — each returning a `TargetFailure` with kind and detail; a pure test-failure stream (`PASS`/`FAIL` lines) never classifies as a target failure (asserted negatively), which is the "distinguish them from test failures" clause; classification is deterministic and serialisable.<br><br>**Test evidence:** `tests/ext/test_inventory.py` — `test_flash_failure_classified`, `test_no_output_classified`, `test_target_reset_classified`, `test_watchdog_classified`, `test_test_failures_never_classify_as_target_failures`, `test_classification_is_deterministic` (12 tests total, green in the WP-EXT-05 gate run: 817 passed, 4 skipped). |
