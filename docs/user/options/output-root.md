<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Confined output root

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Everything ectt generates is written through an
`ectt.core.fs.OutputRoot`: a designated output directory that enforces path
confinement (absolute paths, drive letters, `..` escapes and
symlink/junction escapes are refused), refuses to take over an existing
non-empty directory without the marker file, and writes atomically
(temporary file in the same directory + atomic replace).

Writes are transactional: `OutputRoot.transaction` scopes a group of writes;
on failure or cancellation everything the scope wrote is undone (created
files removed, directories retracted, overwritten files restored
byte-for-byte). Nested scopes join the outermost scope - writes become
durable only when the outermost scope exits cleanly.

An output root may not contain, equal, or live inside any declared source
root (`RootOverlapError`).

