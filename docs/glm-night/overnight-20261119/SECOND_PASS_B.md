# Lane B second-pass — overnight 2026-11-19

Items (or parts of items) that need a human. No code was written for the blocked part of each row.

| item | what is needed | why it needs a human | where |
|------|----------------|----------------------|-------|
| WP-CORE-03 | macOS runner evidence for TOOL-NFR-020 (suite green on a macOS machine or CI runner) | No macOS hardware/runner is reachable from this lane; D-03 orders Windows first, Linux CI green | docs/verification/WP-CORE-03-analysis.md "Not covered" (NFR-020) |
| WP-CORE-03 | Record the derived CMP-CORE acceptance criteria into PLAN-001 §5.4 (owner reconciliation) | PLAN-001 §5.4 is owner territory; board flags "no package-specific acceptance criterion" | docs/verification/WP-CORE-03-analysis.md §Acceptance criteria |
| WP-CORE-03 | Linux CI lane wiring (.github/ workflow running the gate block incl. test_linux_x86_64_baseline) | .github/ is outside this item's allowed paths; D-03 makes Linux CI the standing NFR-010 evidence | docs/verification/WP-CORE-03-analysis.md AC-1 |
| WP-CORE-02 | Route prj project saves through OutputRoot.transaction (SDD-003 §3 "cancellation rolls back uncommitted state") | src/ectt/prj is outside WP-CORE-02's allowed paths; close with the WP-PRJ items (lane B owns prj) | docs/verification/WP-CORE-02-analysis.md TOOL-NFR-180 "Not covered here" |
| WP-CORE-02 | Route ana.persist callers (write_analysis_model users) through OutputRoot.transaction | src/ectt/ana is outside WP-CORE-02's allowed paths; close with the WP-ANA items (lane B owns ana) | docs/verification/WP-CORE-02-analysis.md TOOL-NFR-180 "Not covered here" |
| WP-CORE-02 | Optional dedicated interruption exit code (table extension beyond {0,1,2,10,11}) | The WP-CLI-02 table is a stable contract frozen by an existing test; a new code needs an owner release-note entry | docs/verification/WP-CORE-02-analysis.md design note "Exit codes: adopt, do not extend" |
| WP-ANA-07 | Implement the multi-file analysis run driver owning the per-unit PER_UNIT_FAILURES isolation loop | Explicitly out of scope for this item by the queue instruction ("do not add a multi-file driver"); needs a work-package decision on driver shape (CLI command vs API) | docs/verification/WP-ANA-07-analysis.md "Not yet covered" |
| WP-ANA-07 | Wire eligibility-gate reasons to the now-populated unsupported-construct inventory | TOOL-PAR-170 gate wiring is WP-ANA-06 territory (PAR-080 exposure is ADR-sensitive); the gate's unmodeled-aspects list is now backed by model facts | docs/verification/WP-ANA-07-analysis.md "Not yet covered" |
| WP-ANA-06 | Implement TOOL-PAR-080's static-exposure mechanism (testability without source modification) with WP-GEN-03 | The exposure mechanism is ADR-sensitive (ADR-001 §2/ADR-003 territory) and ADR-003 is an open owner decision — no code may be written for it | docs/verification/WP-ANA-06-analysis.md TOOL-PAR-080 row |
| WP-ANA-06 | Owner-reconcilable option: embed macro-resolution records in the S1 analysis model (additive schema minor bump) vs the current derived-data shape | The SDD-002 S1 shape is register territory; both options are recorded, none decided | docs/verification/WP-ANA-06-analysis.md "Gaps / not covered" |

