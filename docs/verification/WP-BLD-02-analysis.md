# Verification Analysis Note — WP-BLD-02 (Sanitizer Integration)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-BLD-02. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-EXE-090 (S, P2, T) — *The tool shall detect and report memory errors
during host execution via sanitizer integration, without such detection being
mandatory* — built on the WP-BLD-01 build surface.

## Acceptance criteria

- AC-1 (falsifiable, from "without such detection being mandatory"): sanitizer
  integration is opt-in — the default settings request no sanitizer, produce an empty
  flag set, and no sanitizer environment; a build/run performed without enabling
  sanitizers behaves exactly as before this package existed.
- AC-2 (falsifiable): enabling the `address` and/or `undefined` sanitizer modes
  produces the documented GNU-style compile-and-link flag set — one merged
  `-fsanitize=` flag when both are requested — plus the documented runtime-options
  environment; requesting an unknown mode is a named error; the flag mapping is
  deterministic.
- AC-3 (falsifiable, from "detect and report memory errors during host execution"):
  the run-output classifier recognises AddressSanitizer and UndefinedBehaviorSanitizer
  diagnostic markers in captured process output and returns a structured finding
  (sanitizer kind and summary line); output without such markers yields no finding;
  a finding is reported independently of the test verdict (a run can pass tests and
  still carry a sanitizer finding).
- AC-4 (falsifiable): settings, flag sets and findings serialise deterministically
  and are frozen.

Scope notes: this increment ships the sanitizer *configuration and detection-report*
surface inside the build package. Executing the built binary and capturing its output
is the host execution work (WP-EXH-01 and later); the classifier here is the
reporting half that consumes captured output. Sanitizer availability per compiler is
a compiler-capability concern (WP-TCH-04 owns per-config metric/feature declaration);
the flag mapping here is documented for GNU-style compilers and nothing else.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-EXE-090** | The tool shall detect and report memory errors during host execution via sanitizer integration, without such detection being mandatory. | `src/ectt/bld/sanitize.py` (`SanitizerSettings`, `sanitizer_compile_flags`, `sanitizer_runtime_env`, `SanitizerFinding`, `classify_run_output`), `InvalidSanitizerModeError` in `src/ectt/bld/errors.py`, re-exported by `src/ectt/bld/__init__.py` | **Guarantee (opt-in):** `SanitizerSettings()` defaults to no modes — empty flag set, empty runtime environment, and `classify_run_output` is inert without them; nothing in the build surface turns a sanitizer on by itself. Requesting `address`/`undefined` produces the documented GNU-style flags (one merged `-fsanitize=address,undefined` when both are requested) and the `ASAN_OPTIONS` runtime environment with `halt_on_error` recorded; an unknown mode raises `InvalidSanitizerModeError` naming the offender.<br><br>**Guarantee (detect and report):** `classify_run_output` recognises AddressSanitizer/LeakSanitizer/ThreadSanitizer `ERROR:` blocks and UBSan `runtime error:` lines in captured run output and returns ordered, structured findings (canonical kind + diagnostic line), independent of the test verdict — a run whose tests all pass still carries its sanitizer findings, which is what "detect and report memory errors during host execution" requires of the reporting half.<br><br>**Not covered:** running the built binary and capturing its output (WP-EXH-01 execution surface consumes this module); per-compiler sanitizer availability gating (WP-TCH-04); LeakSanitizer/ThreadSanitizer as *settings* modes (only `address` and `undefined` are settings kinds; their diagnostics are still classified).<br><br>**Test evidence:** `tests/bld/test_sanitize.py` — `test_default_settings_enable_nothing`, `test_address_mode_produces_documented_flags`, `test_combined_modes_produce_one_merged_flag`, `test_halt_on_error_false_is_recorded_in_env`, `test_unknown_mode_is_named_error`, `test_settings_and_flags_are_deterministic`, `test_asan_output_yields_structured_finding`, `test_ubsan_output_yields_structured_finding`, `test_plain_output_yields_no_findings`, `test_finding_does_not_depend_on_test_verdict`, `test_finding_order_follows_output_order` (11 tests, green in the WP-BLD-02 gate run: 509 passed, 4 skipped). |
