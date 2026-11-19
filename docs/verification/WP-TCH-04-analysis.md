# Verification Analysis Note — WP-TCH-04 (Capability Declaration and Compiler Version Gating)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-04. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TCH-060 (M, P3, T) and TOOL-TCH-070 (M, P3, T), building on the WP-TCH-01
configuration format and the WP-TCH-02 built-ins.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TCH-060): a metric request is gated against the
  compiler configuration's declared coverage kinds: requesting a kind the
  configuration does not declare is refused with a named error naming the
  configuration and the unsupported kind; supported kinds pass.
- AC-2 (falsifiable, from TOOL-TCH-070): the compiler version is parsed from real
  compiler-version output text; a feature gate consults the documented
  requirement table (MC/DC requires GCC ≥ 14 or Clang ≥ 18): an insufficient version
  is refused with the feature and required version named; a sufficient version passes;
  an unknown feature is a named error; a non-raising verdict form exists for reporting.
- AC-3 (falsifiable): gating is deterministic and serialisable.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCH-060** | The tool shall declare, per compiler configuration, which coverage metrics are achievable, and shall refuse to request unsupported metrics. | `src/ectt/tch/gating.py` (`gate_metrics`, `MetricGate`, `UnsupportedMetricError`), declared kinds from the WP-TCH-01 config, re-exported by `src/ectt/tch/__init__.py` | **Guarantee:** the declared kinds live on the configuration (TOOL-TCH-01's `coverage.kinds`); `gate_metrics` grants exactly the requested kinds the configuration declares — in request order — and refuses any other with `UnsupportedMetricError` naming the configuration, the refused kind(s) and the declared set. Gates are frozen, deterministic data.<br><br>**Test evidence:** `tests/tch/test_gating.py` — `test_supported_metrics_pass_the_gate`, `test_unsupported_metric_refused_with_names`, `test_gating_errors_derive_from_tch_error`. |
| **TOOL-TCH-070** | The tool shall detect the compiler version and reject or warn when the version does not support a requested feature (e.g. MC/DC requiring GCC ≥ 14 or Clang ≥ 18). | `src/ectt/tch/gating.py` (`parse_compiler_version`, `check_version`, `VersionGate`, `FEATURE_VERSION_REQUIREMENTS`), `VersionRequirementError`/`UnknownFeatureError` | **Guarantee:** the version is parsed from real compiler-version output text (`gcc (GCC) 14.1.0` → (14, 1), clang 18.1.3, 13.2.1 …); the documented requirement table is exactly `{"mcdc": {"gcc": (14, 0), "clang": (18, 0)}}` — MC/DC passes on GCC ≥ 14.0 and Clang ≥ 18.0, is refused below with the required version named, an unknown feature or family raises `UnknownFeatureError`, and a non-raising `VersionGate` verdict form (message included) exists for reporting. No version text → named error.<br><br>**Not covered:** executing a real compiler to *obtain* the version text (the caller supplies it; process execution is build-executor work).<br><br>**Test evidence:** `tests/tch/test_gating.py` — `test_version_parsed_from_realistic_compiler_output`, `test_version_without_number_is_named_error`, `test_mcdc_requires_gcc_14`, `test_mcdc_requires_clang_18`, `test_unknown_feature_is_named_error`, `test_gate_verdicts_are_frozen_and_deterministic` (10 tests total, green in the WP-TCH-04 gate run: 746 passed, 4 skipped). |
