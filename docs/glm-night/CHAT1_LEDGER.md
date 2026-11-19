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
| WP-ING-04 | DONE | a86fbb2 | 644 passed, 4 skipped | ING-120/130/140/150/190: named scopes, 4 membership modes, intra/external classification, JSON persistence; gates green (2 gate retries) |
| WP-ING-05 | DONE | 8a67b1d | 653 passed, 4 skipped | ING-160/170/180: 3 conflict kinds, multi-scope membership, complete stub list; gates green (2 gate retries) |
| WP-GEN-03 | DONE | 04ec302 | 660 passed, 4 skipped | HAR-030/080: optional statics via UUT-source include + markers, integration harness marks only external stubs; gates green (1 gate retry) |
| WP-GEN-06 | DONE | 385e9f2 | 671 passed, 4 skipped | STB-010/020/030: per-external stubs, identical signatures, collected type decls, stub marker; gates green (1 gate retry) |
| WP-GEN-05 | DONE | 6d27fab | 678 passed, 4 skipped | TOOL-HAR-120: stub/user-linkage resolution, enforced closure with named unresolved list; gates green (1 gate retry) |
| WP-GEN-08 | DONE | 5c03890 | 690 passed, 4 skipped | STB-080/100/140: exclusion precedence, stdlib-only-on-request (19-name vocabulary), pointer targets with access paths; gates green first try |
| WP-GEN-09 | DONE | cd472b5 | 700 passed, 4 skipped | STB-110/120/130: delimited stub bodies, preserve-where-permitted resync with reports, greppable unsupported markers; gates green (1 gate retry) |
| WP-ING-06 | DONE | 6724244 | 708 passed, 4 skipped | TOOL-ING-110: per-toolchain databases, verbatim flags, distinct same-source configs, build tags; gates green (1 gate retry) |
| WP-SEC-07 | DONE | 5505736 | 717 passed, 4 skipped | TOOL-SEC-090: frozen untrusted payload wrapper (no exec surface), data-only parsing, code-like content retained as data; gates green (1 gate retry) |
| WP-GEN-10 | DONE | 0daabb5 | 724 passed, 4 skipped | TOOL-HAR-065: gtest descriptor opt-in, host-only flag, cpp_allowed scan exemption, builtins unchanged; gates green (2 gate retries) |
| WP-GEN-11 | DONE | 111f825 | 731 passed, 4 skipped | TOOL-STB-090: internal-callee-validated wrap plans, generated #define seam (no user source changes); gates green (1 gate retry) |
| WP-PLG-02 | DONE | 99221eb | 737 passed, 4 skipped | TOOL-PLG-070/080: dir discovery w/o reinstall, 4 failure kinds, isolation proven with 4 failing + 2 good extensions; trust-gate obligation recorded; gates green (2 gate retries) |
| WP-TCH-04 | DONE | 96bf512 | 746 passed, 4 skipped | TOOL-TCH-060/070: declared-kind metric gate, version parse from real output, mcdc gcc>=14/clang>=18 table; gates green (1 gate retry) |
| WP-TCH-03 | PARTIAL | d120d53 | 752 passed, 4 skipped | TCH-050/040 done (6-config roster, user cross config); TCH-030 configs shipped but against-real-toolchain execution pending runtime evidence; SDCC flag owner-review; gates green first try |
| WP-BLD-03 | PARTIAL | 6c29113 | 759 passed, 4 skipped | TGT-010: exact cross command composition + metric gate + staleness carryover; real-toolchain execution pending runtime evidence; gates green (1 gate retry) |
| WP-TCH-05 | PARTIAL | 714d97f | 767 passed, 4 skipped | TCH-080 done (isolated per-toolchain dirs, one invocation); TCH-090 spec generation done, actual image build pending CI runtime evidence; fixed bld/tch circular import via lazy import; gates green (2 gate retries) |
| WP-TCH-06 | PARTIAL | f4f35cc | 773 passed, 4 skipped | TCH-100: 5-family roster with scriptability notes, armclang+IAR configs through public path; licensed-toolchain execution pending runtime evidence; gates green first try |
| WP-EXT-01 | PARTIAL | be928a4 | 783 passed, 4 skipped | TGT-020: qemu/renode descriptors, exact command composition, SEC-07 output boundary; real simulator execution pending runtime evidence; gates green first try |
| WP-EXT-03 | DONE | f0cdb17 | 790 passed, 4 skipped | TGT-050/060: semihosting+UART descriptors, one-way pure-text protocol parse (no bidirectional channel in API); gates green first try |
| WP-EXT-02 | PARTIAL | afe5f7a | 797 passed, 4 skipped | TGT-030/040: 3-family probe descriptors, flash+run command composition; real-hardware execution pending runtime evidence; gates green (1 gate retry) |
