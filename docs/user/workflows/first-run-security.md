<!--
SPDX-License-Identifier: Apache-2.0
-->

# DRAFT: First run, environment verification and untrusted-project warning

> **Status: DRAFT** - authored by the documentation draft wave (WP-CORE-07).
> This page describes only what exists in the code today; anything planned is
> marked **not yet available**. The final wording is the owner's decision.

Before anything runs, ectt verifies the environment it was told to use
(`ectt.tch.environment`) - toolchain presence and versions are checked, and
a mismatch fails the run rather than being papered over. Coverage metric
gating (`ectt.tch.gating`) additionally checks that the pinned toolchain
actually supports the requested coverage metrics.

Untrusted projects: `ectt.sec.trust.UntrustedProjectTracker` keeps a trust
record (a decision per project root, bound to the project's content digest).
The first decision on an unseen project requires an explicit opt-in
(`mark_opened`); until then the tracker reports a decision that requires a
warning (`TrustDecision.requires_warning`, with ready-made `warning_text`).
Source content is never echoed into diagnostics
(`ectt.sec` diagnostic content control).

Destructive operations on untrusted data stay refused; the tracker is data
you can inspect.

