<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: Untrusted-project trust record

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

The trust record (`ectt.sec.trust.UntrustedProjectTracker`) is a
plain-data file you can inspect: one decision per project root, bound to the
project's content digest (`content_digest`, with an exclusion path for the
record itself).

- `decision(project_root)` returns the current `TrustDecision` (a project
  never seen before requires the warning);
- `mark_opened(project_root)` records the explicit opt-in.

`TrustDecision.requires_warning` and `warning_text(decision)` drive any UI.
The record never contains source content, only digests and decisions. A
project whose content changed after the opt-in is a new decision, not a
silent continuation.

