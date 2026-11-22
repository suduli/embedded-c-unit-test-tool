<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Sanitizer modes and runtime options

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

`ectt.bld.sanitize.SanitizerSettings` configures sanitizer instrumentation.
The known modes today are address and undefined (`KNOWN_SANITIZER_MODES`);
any other mode is refused (`unknown_sanitizer_mode`), and a settings object
with no mode is refused as well - an empty sanitizer configuration is a
mistake, not a default.

- `sanitizer_compile_flags(settings)` - the compile switches for the chosen
  modes;
- `sanitizer_runtime_env(settings)` - the runtime environment (halt-on-error
  and log path) for the executed harness.

The sanitizer build classifier tags build output so a sanitizer report is
recognised as a run failure, not as a passing run with noise. Other sanitizer
families are **not yet available**.

