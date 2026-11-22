<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Ingesting a compilation database

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Projects that already build with a compile_commands.json can be ingested
without changing the build: `ectt.ing.compdb_adapter` loads the database
(`load_compdb`), parses it (`parse_compdb`), turns each entry's command line
into arguments (`parse_command_to_arguments`, with response-file expansion via
`expand_response_files`), and extracts the compiler flags
(`extract_compiler_flags`) the analyzer and generator need.

The adapter reads the database from disk or from an already-parsed mapping;
entries that name no compilable source are reported, not silently skipped.
Ingesting through build interception (running your build under a watcher that
records the commands) is **not yet available** - produce a
compile_commands.json with your build system's own support (for CMake:
`CMAKE_EXPORT_COMPILE_COMMANDS=ON`) and use this page's route instead.

