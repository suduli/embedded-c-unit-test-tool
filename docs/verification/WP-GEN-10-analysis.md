# Verification Analysis Note — WP-GEN-10 (GoogleTest Back-End, Host Only)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-GEN-10. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-HAR-065 (C, P3, T) — *The tool shall provide an optional GoogleTest
back-end for host-only execution, for interoperability with existing GoogleTest
suites and tooling. This back-end shall not be required for any documented workflow.*
It extends the WP-GEN-02 back-end surface.

## Acceptance criteria

- AC-1 (falsifiable, from "optional" and "not required"): the GoogleTest back-end
  exists as a declarative descriptor registered only on explicit request — it is
  absent from the default built-in registration, which remains exactly Unity and
  cmocka (so no documented workflow requires it).
- AC-2 (falsifiable, from "host-only"): the descriptor declares itself host-only,
  and rendering through it produces GoogleTest-style output (the gtest header, TEST
  macros, an explicit host-only note in the banner).
- AC-3 (falsifiable): the GoogleTest render is exempt from the WP-GEN-02 C++-free
  scan by descriptor data (`cpp_allowed=True` — GoogleTest output is C++), and the
  C++-free discipline still holds for every other back-end (a C++ construct in a
  non-GoogleTest render is still the named error).
- AC-4 (falsifiable): registering the GoogleTest back-end twice is refused; the
  descriptor is frozen and listing stays deterministic.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-HAR-065** | The tool shall provide an optional GoogleTest back-end for host-only execution, for interoperability with existing GoogleTest suites and tooling. This back-end shall not be required for any documented workflow. | `src/ectt/gen/backends.py` (`register_gtest_backend`, `GTEST_BACKEND_ID`, `FrameworkBackend.cpp_allowed`/`host_only` descriptor fields), re-exported by `src/ectt/gen/__init__.py` | **Guarantee:** the GoogleTest back-end exists as a declarative descriptor (`googletest`, header `gtest/gtest.h`, `host_only=True`, `cpp_allowed=True`) registered only on explicit request — the default built-in registration remains exactly Unity and cmocka, so no documented workflow requires it. Rendering through it produces GoogleTest-style host-only output (gtest header include, namespace, host-only banner note) and is exempt from the WP-GEN-02 C++-free scan by descriptor data; every other back-end still enforces the scan (asserted with a C++-containing non-gtest back-end raising `CppConstructInOutputError`). Double registration is refused; the flags ride the declarative descriptor path.<br><br>**Not covered:** running the produced GoogleTest suite (host execution is WP-EXH-01); linking GoogleTest itself is the build step's dependency concern.<br><br>**Test evidence:** `tests/gen/test_gtest.py` — `test_gtest_is_not_among_the_builtins`, `test_gtest_registers_on_explicit_request`, `test_gtest_render_produces_google_test_style_output`, `test_gtest_render_is_exempt_from_cpp_free_scan`, `test_cpp_free_scan_still_applies_to_other_backends`, `test_gtest_double_registration_refused`, `test_descriptor_declares_host_only_through_the_data_path` (7 tests, green in the WP-GEN-10 gate run: 724 passed, 4 skipped). |
