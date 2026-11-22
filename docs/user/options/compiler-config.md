<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Compiler configuration file fields (invocation, flags, output, coverage)

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

A compiler configuration (`ectt.tch.config`) declares:

- **invocation** (`InvocationSpec`): how the compiler executable is invoked;
- **output** (`OutputSpec`): where object files and coverage artifacts land;
- **flags**: the switches for includes, defines, warnings, coverage;
- **coverage** (`KNOWN_COVERAGE_KINDS`): which coverage kinds the compiler
  can produce, gated against the toolchain's measured support
  (`ectt.tch.gating`).

The schema is versioned (`CONFIG_SCHEMA_VERSION`); loading refuses unknown
schema versions and unknown fields. Built-in GCC and Clang configurations
live in `ectt.tch.builtin`; a cross-compiler roster in `ectt.tch.cross` and
`ectt.tch.multibuild` plans multi-toolchain builds.

