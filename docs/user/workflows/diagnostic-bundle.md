<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Producing a diagnostic bundle for a defect report

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

When something goes wrong, `ectt.core.logging.build_diagnostic_bundle`
produces a diagnostic bundle: the log records at the requested verbosity
(`ectt.core.logging.Verbosity`: QUIET, NORMAL, VERBOSE, DEBUG) plus the
bundle entries configured in `ectt.sec` - and the entries that must be
excluded (`BUNDLE_EXCLUSIONS`) are excluded, so source content does not leak
into the bundle.

The bundle is plain text, deterministic apart from the facts it reports, and
is what a defect report should attach. Verbosity is a per-logger setting on
`ectt.core.logging.EcttLogger`.

