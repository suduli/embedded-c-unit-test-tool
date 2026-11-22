<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Adding a compiler configuration

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Compiler knowledge is data, not code: a compiler configuration file
(`ectt.tch.config`) declares a compiler's invocation shape, flags, output
switches and coverage switches, and a registry (`CompilerConfigRegistry`)
holds the known compilers. GCC and Clang configurations ship built in
(`ectt.tch.builtin`); a cross-compilation roster is available
(`ectt.tch.cross`).

To add a compiler whose configuration is not built in, write a configuration
file conforming to the compiler-configuration schema (versioned,
`CONFIG_SCHEMA_VERSION`; see `docs/user/options/compiler-config.md` for the
fields) and register it with a `CompilerConfigRegistry`. Unknown fields and
unknown coverage kinds are refused - a mis-typed configuration fails closed.
Configurations for compilers ectt has never seen must be authored by you;
ectt will not guess flag semantics.

