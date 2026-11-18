# WP-QUA-01 — Analysis: tool classification analysis and confidence level

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-QUA-01.
The requirement text (TOOL-QUA-010, method *I*) yields the deliverable definition:

> The tool shall be accompanied by a Tool Classification analysis addressing ISO 26262-8 **Tool
> Impact** and **Tool error Detection**, yielding a **Tool Confidence Level**.

- **AC-1:** a Tool Classification analysis document exists, addressing Tool Impact and Tool error
  Detection per ISO 26262-8 and recording the resulting Tool Confidence Level.
- **AC-2 (ADR-sensitive):** the TI/TD determinations and the resulting TCL are certification
  judgments — the classification decision this package exists to produce. They are **not derivable
  from repository facts alone**: they require the owner's qualification context (safety scope of
  the tool's outputs, integration into the user's safety lifecycle). Deciding them in an
  unattended run would answer an ADR-sensitive question, which is out of scope by rule.

## Decision-free part assessed

The mechanical scaffolding is already in place from WP-QUA-02 (same run):
`src/ectt/qua/operational_requirements.py` records the intended-use/classification line as `OPEN`
with the WP-QUA-01 reference, and `src/ectt/qua/qualification_scope.py` enforces the no-claim
guard. What remains — and what blocks this package — is the substantive TI/TD/TCL analysis, which
is a human judgment over the tool's role in the user's safety argument, not a code increment.

## Result

**BLOCKED** — the deliverable's substance is the classification decision (ADR-sensitive). No code
was written for the blocked part; no classification option was chosen. Owner actions to unblock:
answer the tool-classification question in the ADR/decision register (with TI per ISO 26262-8
§5.4.2, TD per §5.4.5, TCL per §5.4.7), after which the analysis document can be authored against
the existing `ectt.qua` artifacts and the OPEN markers in WP-QUA-02's renderer can be filled.
