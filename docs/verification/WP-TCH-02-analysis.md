# Verification Analysis Note — WP-TCH-02 (Host Compiler Support: GCC and Clang)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-02. The
acceptance criteria below are derived from the SRS-001 requirement owned by this work
package: TOOL-TCH-010 (M, P1, T) — *The tool shall support GCC and Clang as host
compilers* — supported by the WP-TCH-01 format (TOOL-PLG-020, TOOL-TCH-020).

## Acceptance criteria

- AC-1 (falsifiable): the tool ships two built-in compiler configurations, one for
  GCC and one for Clang as host compilers; when registered, both are retrievable by
  name from the WP-TCH-01 registry, and each specifies an executable, debug flags,
  at least two named optimization levels, output conventions, and at least one
  supported coverage kind with its flags.
- AC-2 (falsifiable): the built-in configurations are produced through the same
  schema-version-1 validation as user-authored configuration files (no separate or
  privileged code path), so a structural mistake in a built-in would fail the same
  named errors.
- AC-3 (falsifiable): registration of the built-ins obeys the same registry
  discipline as user configurations: a second registration of the same name is
  rejected with `DuplicateCompilerConfigError`, including when a user-authored
  configuration claimed the name first.
- AC-4 (falsifiable): the built-in configuration set is deterministic — every call
  yields the same names, families, executables and declared coverage-kind sets, in a
  deterministic order.

Scope note: cross toolchains and the shipped configuration roster
(`arm-none-eabi-gcc`, RISC-V, `avr-gcc`, SDCC) belong to WP-TCH-03 (TOOL-TCH-030,
TOOL-TCH-040, TOOL-TCH-050) and are not claimed here. Coverage-kind capability
gating and compiler-version gating belong to WP-TCH-04. The built-in host configs
declare the `--coverage` line/branch kinds only; declaring MC/DC unconditionally
would contradict TOOL-TCH-070's version gating (MC/DC requires GCC ≥ 14 / Clang ≥ 18)
and is deliberately left to the gating work package.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCH-010** | The tool shall support GCC and Clang as host compilers. | `src/ectt/tch/builtin.py` (`built_in_host_configs`, `register_host_builtins`, `GCC_HOST_CONFIG_NAME`, `CLANG_HOST_CONFIG_NAME`), built on `src/ectt/tch/config.py` (`load_compiler_config_text`, `CompilerConfigRegistry`), re-exported by `src/ectt/tch/__init__.py` | **Guarantee:** the tool ships two built-in host compiler configurations, `gcc` (executable `gcc`) and `clang` (executable `clang`), each specifying debug flags, three named optimization levels (none/size/speed), output conventions (`.o` object suffix), and the coverage kinds the `--coverage` mechanism delivers on both compilers (line, branch) with per-kind flags. `register_host_builtins` puts them into any `CompilerConfigRegistry` through the public `register` API, after which both are retrievable by name.<br><br>**Analysis argument (no privileged path):** the built-ins are embedded schema-version-1 YAML documents passed through the same `load_compiler_config_text` validator a user file reaches via `load_compiler_config`; a structural error in a built-in document raises the identical named errors at import time. Registration reuses `CompilerConfigRegistry.register`, so a user configuration that claimed the name `gcc` first blocks the built-in with `DuplicateCompilerConfigError` — the tool never silently overwrites a user's config.<br><br>**Not covered:** cross toolchains and the shipped configuration roster (WP-TCH-03, TOOL-TCH-030/040/050); coverage-metric and version gating such as MC/DC on GCC ≥ 14 (WP-TCH-04, TOOL-TCH-060/070); driving an actual compiler binary (host build orchestration is WP-BLD-01, TOOL-EXE-080). This package's support claim is the declarative configuration + registry surface those packages consume.<br><br>**Test evidence:** `tests/tch/test_host.py` — `test_two_builtin_host_configs_are_shipped`, `test_gcc_host_config_specifies_every_format_aspect`, `test_clang_host_config_specifies_every_format_aspect`, `test_builtins_are_produced_by_the_public_loader`, `test_builtins_register_and_lookup_by_name`, `test_lookup_before_registration_is_unknown`, `test_builtins_never_overwrite_user_configs`, `test_builtin_set_is_deterministic` (8 tests, green in the WP-TCH-02 gate run: 452 passed, 4 skipped). |
