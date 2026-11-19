# Verification Analysis Note — WP-TCH-06 (Proprietary Compiler Support)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-06. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-TCH-100 (C, P3, T) — *The tool shall support proprietary compilers
(Keil armcc/armclang, IAR, TASKING, Green Hills) through the compiler configuration
mechanism where their invocation is externally scriptable.*

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TCH-100 and "where their invocation is externally
  scriptable"): a proprietary compiler family roster (armcc, armclang, iar, tasking,
  greenhills) is documented with per-family external-scriptability notes; a
  proprietary compiler is supported by authoring a schema-version-1 configuration
  file through the public WP-TCH-01 path — demonstrated end-to-end with a Keil
  armclang config, no tool source change.
- AC-2 (falsifiable): the family roster is machine-readable, frozen and
  deterministic; a config whose `family` is outside the documented proprietary set
  still loads (the format is open), but the roster records which families are
  documented as externally scriptable.

**Honest limits (why this lands as PARTIAL):** actual execution of proprietary
compilers (licensed toolchains) is outside this environment; the mechanism and roster
are verified here, execution verification is pending a runtime-evidence run with a
licensed toolchain.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCH-100** | The tool shall support proprietary compilers (Keil armcc/armclang, IAR, TASKING, Green Hills) through the compiler configuration mechanism where their invocation is externally scriptable. | `src/ectt/tch/proprietary.py` (`proprietary_families`, `ProprietaryFamily`, `PROPRIETARY_FAMILIES`), support mechanism = WP-TCH-01 public config path; re-exported by `src/ectt/tch/__init__.py` | **Guarantee:** the proprietary family roster documents all five SRS families (armcc, armclang, iar, tasking, greenhills) with their drivers and external-scriptability notes, frozen and deterministic; support is by authoring a schema-version-1 configuration through the public path — demonstrated end-to-end for Keil armclang (file → load → registry → lookup, `.axf` conventions, `--coverage` line) and IAR iccarm (text path), with zero tool source changes. The format stays open: an unknown family name still loads as data.<br><br>**This is why WP-TCH-06 lands as PARTIAL:** executing licensed proprietary toolchains is outside this environment; mechanism and roster are verified here, against-real-compiler verification is pending a runtime-evidence run.<br><br>**Test evidence:** `tests/tch/test_proprietary.py` — `test_proprietary_roster_covers_the_srs_families`, `test_every_roster_family_documents_scriptability`, `test_keil_armclang_config_loads_end_to_end`, `test_iar_config_loads_through_the_public_text_path`, `test_roster_is_frozen_and_deterministic`, `test_proprietary_error_derives_from_tch_error` (6 tests, green in the WP-TCH-06 gate run: 773 passed, 4 skipped). |

## Standing summary

WP-TCH-06 is recorded as **PARTIAL** in the ledger: the roster and the public-config
support mechanism are covered with test evidence; against-real-proprietary-compiler
verification is pending a runtime-evidence run with licensed toolchains.
