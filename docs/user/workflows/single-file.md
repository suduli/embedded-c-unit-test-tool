<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Single-file testing without a build system

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

The fastest path from one C file to a testable unit is the single-file
ingestion (`ectt.ing.single_file.ingest_single_source`): give it a path to a
C source file and it builds the ingestion model without any build system,
compilation database, or project store.

Constraints enforced by the code:

- the file must exist and be readable (`SingleSourceReadError` otherwise);
- the file must be a C source (`NotCSourceError` otherwise - headers and
  other languages are refused, not guessed).

After ingestion, the usual pipeline applies: analysis (`ectt.ana`), harness
generation (`ectt.gen`), and host execution (`ectt.exh`) - each documented on
its own page. A single `ectt test path/to/file.c`-style command is
**not yet available**; the CLI currently exposes only `operation.cancel` (see
`ectt --list-commands`).

