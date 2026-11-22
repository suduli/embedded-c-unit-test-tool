<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Building with sanitizers and incremental rebuild

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Build planning lives in `ectt.bld`. The incremental planner
(`ectt.bld.plan`) records one build record per artifact and decides per
artifact whether a rebuild is needed: reasons include no previous record,
changed source, changed configuration, or changed flags - anything else is
left untouched (no gratuitous rebuilds).

Sanitizers: `ectt.bld.sanitize.SanitizerSettings` accepts the known modes
address and undefined (`KNOWN_SANITIZER_MODES`); unknown modes are refused.
`sanitizer_compile_flags` returns the compile switches and
`sanitizer_runtime_env` the runtime environment for the chosen modes.
Thread sanitizer and other modes are **not yet available**.

Executing the planned build through a compiler is the harness-build path
(`ectt.bld.harness_build`) - it requires a working toolchain; ectt never
pretends a build happened.

