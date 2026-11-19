# Verification Analysis Note — WP-TCH-03 (Cross-Toolchain Support and Shipped Configurations)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-TCH-03. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-TCH-030 (M, P3, T), TOOL-TCH-040 (S, P3, T), TOOL-TCH-050 (S, P3, I),
building on the WP-TCH-01 format and WP-TCH-02 host built-ins.

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-TCH-050): the tool ships compiler configurations for
  the full minimum roster — GCC (host), Clang (host), arm-none-eabi-gcc,
  riscv64-unknown-elf-gcc, avr-gcc, SDCC — all built through the same schema-version-1
  validation as user files, with GNU-family cross configs carrying their target
  triple in the invocation; the roster is deterministic and retrievable by name.
- AC-2 (falsifiable, from TOOL-TCH-040): an additional cross compiler is supported by
  authoring a configuration file through the WP-TCH-01 public path — demonstrated
  with a user cross config loaded and registered with no tool source change.
- AC-3 (falsifiable, from TOOL-TCH-030): the GNU embedded toolchain support is
  expressed as the shipped arm-none-eabi-gcc and riscv64-unknown-elf-gcc
  configurations with correct executable names and triples; duplicate registration is
  refused like any user config.

**Honest limits (why this lands as PARTIAL):** TOOL-TCH-030 requires verification
*against* `arm-none-eabi-gcc` and a RISC-V GNU toolchain — executing real
cross-compilers is outside this environment; the shipped configurations and their
mechanism are verified here, and the execution verification is recorded as pending a
runtime-evidence run. The SDCC coverage flag in the shipped config is provisional
(owner-review draft, like the WP-SEC-05 policy) — the config is declarative data and
owner-correctable without code changes.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-TCH-050** | The tool shall ship compiler configurations for at minimum: GCC (host), Clang (host), arm-none-eabi-gcc, riscv64-unknown-elf-gcc, avr-gcc, and SDCC. *(Method I)* | `src/ectt/tch/cross.py` (`shipped_cross_configs`, `shipped_roster`, `register_cross_builtins`, `ensure_roster_complete`, `SHIPPED_CONFIG_NAMES`), plus the WP-TCH-02 host built-ins; re-exported by `src/ectt/tch/__init__.py` | **Guarantee (inspection):** the shipped roster is exactly the six SRS-minimum configurations — GCC and Clang from the host built-ins, the four cross configs from this module — all built through the same schema-version-1 validation as user files (a structural mistake would raise the identical named errors at import); GNU cross configs carry `.elf` output conventions; `ensure_roster_complete` refuses a registry missing any roster entry. Deterministic roster order.<br><br>**Owner-review draft:** the SDCC coverage flag (`--debug`, provisional) is flagged for owner correction; the config is declarative data, correctable without tool source changes.<br><br>**Test evidence:** `tests/tch/test_cross.py` — `test_shipped_roster_covers_the_srs_minimum`, `test_cross_configs_pass_the_user_validation_path`, `test_roster_completeness_enforced`. |
| **TOOL-TCH-040** | The tool shall support additional cross-compilers via user-authored compiler configuration files without requiring changes to the tool's source code. | WP-TCH-01 loader/registry (`load_compiler_config`, `CompilerConfigRegistry`) exercised with a cross config | **Guarantee:** demonstrated end-to-end in tests: a user-authored YAML for a fictional `xtensa-esp32-elf-gcc` cross compiler loads, validates and registers through the public path — zero tool source changes, exactly the TOOL-PLG-020 discipline applied to cross compilers.<br><br>**Test evidence:** `tests/tch/test_cross.py` — `test_additional_cross_compiler_via_config_file_only`. |
| **TOOL-TCH-030** | The tool shall support cross-compilation using GNU-style embedded toolchains, verified against at minimum `arm-none-eabi-gcc` and a RISC-V GNU toolchain. | `src/ectt/tch/cross.py` (arm-none-eabi-gcc and riscv64-unknown-elf-gcc configurations), plus the WP-TCH-01 invocation contract | **Guarantee (partial):** the GNU embedded toolchain support is expressed as the shipped configurations for `arm-none-eabi-gcc` and `riscv64-unknown-elf-gcc` with correct executable names, GNU family, `.elf` output conventions and per-config coverage declarations; duplicate registration is refused like any user config.<br><br>**This is why WP-TCH-03 lands as PARTIAL:** TOOL-TCH-030 requires verification *against* the real toolchains; executing `arm-none-eabi-gcc` and a RISC-V GNU toolchain is outside this environment and is recorded as pending a runtime-evidence run. No claim of executed cross-compilation is made here.<br><br>**Test evidence:** `tests/tch/test_cross.py` — `test_cross_configs_carry_triples_and_invocations`, `test_duplicate_cross_registration_refused`. |

## Standing summary

WP-TCH-03 is recorded as **PARTIAL** in the ledger: TOOL-TCH-050 and TOOL-TCH-040 are
covered with test evidence; TOOL-TCH-030's shipped configurations are in place but its
against-real-toolchains verification is pending a runtime-evidence run.
