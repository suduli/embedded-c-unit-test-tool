| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| WP-CBT-01 | DONE | bdb4afc | 130k | 130k | executor: Claude; ectt.cbt: CompiledSuiteRecord (executable digest + bindings, digest-bound JSON), reexecute_suite (refuses changed/missing binary, stale tests not exec |
| WP-ATG-01 | DONE | ea2da2d | 180k | 310k | executor: Claude; ectt.atg: TestValidationPort (inverted dependency), validate_candidates gate (build+run before presenting, discards counted), emission as ordinary Dat |
| WP-TCM-07 | DONE | cb96fe4 | 205k | 515k | executor: Claude; ectt.tcm.derivation: boundary_values (BVA, robust mode), equivalence_classes, domains_from_parameters (authored ranges only), derive_vectors (one_at_a |
| WP-GEN-07 | DONE | fa024d4 | 205k | 720k | executor: Claude; ectt.gen.stubctl: per-stub control block + journal + shared order log, public C API, header, per-case setup/expectation rendering from StubSpec, value |
| FIX-GENPROTO | DONE | 63da3b4 | 180k | 900k | executor: Claude; New ectt.gen.protocol C runtime placed in every generated harness: RESULT/FAILURE lines with whitespace-safe tokens and line>=1 over an overridable tr |
| FIX-TCMNEST | DONE | a932d36 | 150k | 1050k | executor: Claude; Nested expected values are authored as path keys (g.header.len, g.payload[1], u.as_int) in the unchanged flat form, so existing flat files are valid a |
| WP-ATG-05 | DONE | 13b4907 | 155k | 1205k | executor: Claude; ectt.atg.run: run_generation under time/memory/case limits (graceful, returns what was generated, report names the limit; configured memory limit alwa |
