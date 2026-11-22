<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Ingesting via build interception (Bear)

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Build interception - running the project's build under a tool that records
every compiler invocation - is **not yet available**: there is no Bear (or
equivalent) integration in the code today, and this page will not guess at
one.

What exists now is the compile-database route
(`docs/user/workflows/compile-database.md`): produce a
`compile_commands.json` by any means (your build system's export option, or
Bear itself if you have it installed), then ingest it with
`ectt.ing.compdb_adapter.load_compdb`. ectt reads the database; it never
runs your build for ingestion purposes.

When interception lands, this page will describe the real interface and this
notice will be removed.

