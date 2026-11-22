<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Logging verbosity levels

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

`ectt.core.logging.Verbosity` is a four-level scale: `QUIET` (0),
`NORMAL` (1), `VERBOSE` (2), `DEBUG` (3). An `EcttLogger` carries the
verbosity and emits `LogRecord`s; the diagnostic bundle
(`build_diagnostic_bundle`) includes records up to the requested level.

There is no global mutable verbosity: a component logs through the logger it
was given. The diagnostic content guard (`ectt.sec`) applies at every level -
source content stays out of diagnostics regardless of verbosity.

