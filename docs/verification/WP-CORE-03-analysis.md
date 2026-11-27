# Verification Analysis Note — WP-CORE-03 (Platform Baseline and Offline Guarantee)

Analysis evidence for requirements verified under WP-CORE-03. Status: **implemented**
(evidence-backed by the tests named below).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4
for this package. The falsifiable criteria below are derived from the PLAN-001 §5.4 row
(`WP-CORE-03`, CMP-CORE, P1, 2w, TOOL-NFR-010/020/100, no dependencies) and the SRS texts,
and are implemented as written. They are recorded here rather than in PLAN-001 — register
edits are owner territory (reconciliation noted in SECOND_PASS_B).

## Acceptance criteria (derived, falsifiable)

- **AC-1 (TOOL-NFR-010, verification method T — boundary value analysis):** on a Linux x86-64
  host, `ectt.core.platform.current_platform()` returns `Platform.LINUX` and
  `executable_suffix()` returns `""`, and the full unit-test suite passes. Standing evidence
  is the Linux CI lane per decision D-03 ("Windows first, Linux CI kept green"); the in-repo
  hook is `test_linux_x86_64_baseline`, which executes on Linux and skips elsewhere with an
  explicit reason.
- **AC-2 (TOOL-NFR-020, T — equivalence partitioning):** on Windows, `current_platform()`
  returns `Platform.WINDOWS` and `executable_suffix()` returns `".exe"`, and the full suite
  passes on Windows (this run). Platform detection partitions over the equivalence classes
  {win32-family}, {linux-family}, {darwin-family}, {other}, each covered by boundary-value
  tests. macOS shares the POSIX code path (`executable_suffix(Platform.MACOS) == ""`); macOS
  runner evidence is deferred by D-03 and tracked in SECOND_PASS_B.
- **AC-3 (TOOL-NFR-100, I — inspection checklist, machine-supported):** a source-tree audit
  (`find_network_imports`, an AST import scan against the explicit `NETWORK_MODULES`
  deny-list) over every module in `src/ectt` reports zero network-capable imports. The audit
  is itself a unit test (`test_repository_source_is_offline`) that fails if any banned import
  appears, and its output is deterministic and sorted so it serves directly as the inspection
  checklist artefact.
- **AC-4 (platform report):** `platform_report()` returns a deterministic, canonical-JSON
  serialisable mapping of host facts (platform, machine, executable suffix, validated flag)
  with no wall-clock and no network dependency; two consecutive calls are equal.

Decision D-03 (owner answer, 2026-11-19, memo option (a)): "Windows first, Linux CI kept
green" — implemented as written: `VALIDATED_PLATFORMS == {WINDOWS, LINUX}`, asserted by
`test_validated_platforms_follow_decision_d03`. macOS is recognised, shares the POSIX path,
and is reported `validated: false` until runner evidence exists.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-NFR-010** | The tool shall run on Linux x86-64. | `src/ectt/core/platform.py` (`detect_platform`, `current_platform`, `executable_suffix`, `platform_report`) | **Mechanism:** platform handling is centralised in one pure module. `detect_platform` maps the `sys.platform` family values to a canonical `Platform` enum; Linux is a first-class value, `executable_suffix` returns `""` on the POSIX branch shared by Linux and macOS, and `platform_report` exposes the host facts (platform, machine, executable suffix, validated flag) the tool actually relies on. There is no Windows-only primitive on the tested core surface: path handling in `core` is `pathlib`-based and line-ending normalisation is LF-canonical (`canonical_text`).<br><br>**Evidence:** boundary value analysis over `sys.platform` values — `test_detect_platform_boundary_values` (win32, linux, linux2, darwin, cygwin, freebsd13, empty string); `test_linux_x86_64_baseline` (executes on the Linux CI lane, skips elsewhere with an explicit reason); `test_executable_suffix_partitions_by_platform_family`; `test_current_platform_matches_running_interpreter`. The full suite (970 passed, 4 skipped at baseline) is the standing Linux-CI-green check per D-03.<br><br>**Not covered here:** an actual Linux runner invocation in this lane — the lane executes on Windows; the Linux CI lane is the owner's standing evidence per D-03. |
| **TOOL-NFR-020** | The tool shall run on Windows and macOS. | `src/ectt/core/platform.py` (`Platform`, `VALIDATED_PLATFORMS`, `executable_suffix`), `src/ectt/core/determinism.py` (`neutralize_hash_seed` win32/POSIX branches) | **Mechanism:** Windows is the first-class platform (D-03): `Platform.WINDOWS`, `".exe"` suffix, and the existing re-exec path in `neutralize_hash_seed` already branches win32 vs POSIX. macOS resolves to `Platform.MACOS` and shares the exact POSIX code path of Linux (`executable_suffix(Platform.MACOS) == ""`), so no platform-specific work is outstanding in the mechanism itself.<br><br>**Evidence:** equivalence partitioning — `test_windows_baseline` (executes on this Windows run), `test_detect_platform_boundary_values`, `test_executable_suffix_partitions_by_platform_family`, `test_macos_recognised_but_not_yet_validated`, plus the existing `tests/core/test_determinism.py` re-exec branch tests.<br><br>**Not covered here:** an actual macOS runner invocation. D-03 orders Windows first and Linux CI green; macOS validation is deferred, recorded in SECOND_PASS_B, and visibly reported by `platform_report()["validated"] = false` rather than hidden. |
| **TOOL-NFR-100** | The tool shall not require network access for any non-AI functionality. | `src/ectt/core/platform.py` (`NETWORK_MODULES`, `find_network_imports`, `assert_offline`, `OfflineViolationError`) | **Mechanism:** the offline guarantee is machine-checked, not asserted by prose. `find_network_imports` parses every `*.py` file under a source root with `ast` and reports imports whose top-level module is in the explicit `NETWORK_MODULES` deny-list (stdlib network stacks: socket, ssl, urllib, http, ftplib, telnetlib, smtplib, poplib, imaplib, nntplib, xmlrpc; third-party clients: requests, httpx, aiohttp, urllib3, websockets, websocket, grpc, pycurl). Files that cannot be parsed are reported as `<syntax-error>` hits so the scan cannot be silently blinded. Cache directories are skipped. Output is a sorted, deterministic tuple. `assert_offline` turns a non-empty scan into `OfflineViolationError` (category `core`, reason `network_import`).<br><br>**Evidence:** `test_repository_source_is_offline` scans the whole product source (`src/ectt`) and passes with zero hits — this is the inspection checklist for NFR-100 and fails on any future network import. Fixture evidence: `test_find_network_imports_detects_banned_modules`, `test_find_network_imports_clean_tree_has_no_hits`, `test_find_network_imports_output_is_sorted_and_deterministic`, `test_find_network_imports_flags_unparsable_file`, `test_find_network_imports_skips_caches`, `test_assert_offline_raises_on_violation`, `test_banned_module_list_covers_essentials`.<br><br>**Scope limit:** the scan sees `import`/`from ... import` statements; dynamic string-based imports (`importlib.import_module("socket")`) are out of scope and noted as a residual risk in the checklist. `pytest` itself is test infrastructure, not product functionality. |

## Design notes

- **Why a pure detection function.** `detect_platform` takes the platform string as an
  argument (defaulting to `sys.platform`), so every equivalence class is testable on any host
  without monkeypatching globals; the two skipif tests then anchor the classes that can be
  verified for real (Windows here, Linux on CI).
- **Why `VALIDATED_PLATFORMS` is data, not a gate.** The platform order decision (D-03) is
  about *evidence priority*, not about refusing hosts. The module reports `validated: false`
  for macOS instead of raising, so nothing weakens TOOL-NFR-020 and the gap stays visible.
- **Why the offline audit lives in core and is a test.** TOOL-NFR-100 is verified by
  inspection; a deterministic, sorted scan result is the artefact an inspector can review,
  and encoding it as a test makes the checklist self-enforcing.
- **Error classes.** `PlatformError` and `OfflineViolationError` derive from `CoreError`
  (category `core`), so no new error category is introduced and the WP-CORE-02 exit-code
  mapping keeps working unchanged.
- **SECOND_PASS rows.** (1) macOS runner evidence for TOOL-NFR-020 — hardware/CI, owner
  territory. (2) PLAN-001 §5.4 has no package-specific acceptance criterion for CMP-CORE —
  owner reconciliation of the derived criteria above. (3) Linux CI lane wiring (`*.yml` under
  `.github/`) is outside this item's allowed paths — maintained by the owner per D-03.

## Requirement split, 2026-11-27

The owner chose Windows only for the first release. TOOL-NFR-020 (M, P1) now covers Windows; macOS is the new TOOL-NFR-200 (S, P2). The macOS runner-evidence gap recorded above now applies to TOOL-NFR-200.
