| WP | state | commit | tests | notes |
|---|---|---|---|---|
| WP-PLG-01 | DONE | e6e0a41 | 412 passed, 4 skipped | TOOL-PLG-010: 4 builtin extension-point descriptors, open registry, error hierarchy; all gates green |
| WP-TCH-01 | DONE | a33fc18 | 444 passed, 4 skipped | TOOL-PLG-020 + TOOL-TCH-020: YAML schema v1, loader/validator/registry, 23 tests; gates green (1 ruff-fix round) |
| WP-TCH-02 | DONE | 9065a0b | 452 passed, 4 skipped | TOOL-TCH-010: gcc/clang built-ins via public loader+registry, no-override discipline, 8 tests; gates green (1 gate retry) |
| WP-GEN-01 | PARTIAL | 5068522 | 466 passed, 4 skipped | HAR-010/020/050 covered; HAR-040 partial: model lacks global types -> file-static access + extern emission remain; gates green (1 gate retry) |
| WP-TCM-01 | DONE | b5cb1d7 | 479 passed, 4 skipped | TOOL-TCD-010: C-source case registration with harness-include verification, 13 tests; gates green (2 gate retries: ruff fixes) |
| WP-BLD-01 | DONE | eba9d83 | 490 passed, 4 skipped | TOOL-EXE-080: digest-based incremental planner, exactly-affected rebuilds, 11 tests; gates green (1 gate retry: ruff) |
| WP-SEC-05 | DONE | 582c080 | 498 passed, 4 skipped | TOOL-SEC-080 (method I): policy prose in analysis note + machine-readable ectt.sec.policy; OWNER-REVIEW draft, SECURITY.md promotion needed; gates green (1 gate retry) |
| WP-BLD-02 | DONE | dacf04b | 509 passed, 4 skipped | TOOL-EXE-090: opt-in ASan/UBSan flags+env, output classifier; execution capture is EXH-01; gates green (2 gate retries) |
| WP-SEC-04 | DONE | 0809946 | 520 passed, 4 skipped | TOOL-SEC-120: location-only diagnostics, verbatim-source guard (substring), exact bundle manifest; gates green (1 gate retry) |
| WP-CORE-06 | DONE | 0cd11c6 | 533 passed, 4 skipped | TOOL-NFR-130/160: Verbosity logger, SEC-04 guard at record time, manifest-linked bundle; gates green (1 gate retry) |
| WP-TCH-07 | DONE | 88ca73c | 547 passed, 4 skipped | TOOL-INS-080: injectable env verification (toolchain presence, feature availability), clear sorted report, first-run marker; gates green (1 gate retry) |
| WP-ING-02 | PARTIAL | e60cd94 | 554 passed, 4 skipped | ING-060 done; ING-210 claimed (pre-existing green tests); ING-050 documented; ING-080 IDE importers remain open; gates green (1 gate retry) |
| WP-ING-03 | DONE | 6456992 | 569 passed, 4 skipped | ING-070/090 implemented; ING-100/220 claimed with pre-existing green evidence + fresh demo; gates green (1 gate retry) |
| WP-PLG-04 | DONE | 3ccf23c | 581 passed, 4 skipped | TOOL-PLG-100 (board AC): ai_providers point via public surface, capability/version negotiation, rejection-before-loading proven; gates green (1 gate retry) |
| WP-SEC-03 | DONE | 490bd8c | 598 passed, 4 skipped | TOOL-SEC-050/070: persisted trust record + warning text, data-only config boundary; gates green (1 gate retry) |
| WP-CORE-07 | PARTIAL | fbf995e | 612 passed, 4 skipped | NFR-190 catalog done; NFR-120 index done but docs/user/ pages are owner shared-file change; gates green (2 gate retries) |
| WP-GEN-02 | DONE | 045dd87 | 622 passed, 4 skipped | HAR-060/070 PLG-030: descriptor-driven back-ends, unity+cmocka built-ins, C++-free render scan; 4 open ADR questions recorded (default framework, cmocka-stub binding, template distribution, engine); gates green (1 gate retry) |
| WP-GEN-04 | DONE | 069e463 | 631 passed, 4 skipped | Board AC met: byte-for-byte region preservation, conflict reports write nothing (verified); HAR-090/100/110 + CBT-070 covered; gates green (1 gate retry) |
