| item | what is needed | why it needs a human | where |
|---|---|---|---|
| FIX-TXN | Make OutputRoot.transaction re-entrant (nested scopes join the outer one) so callers need no private-attribute check; ana.persist currently reads output_root._journal to join a caller's scope | src/ectt/core/fs.py is outside lane B's allowed paths | src/ectt/ana/persist.py write_analysis_model |
| FIX-TXN | Project saves cannot use OutputRoot.transaction (the project tree is source, OutputRoot refuses overlap and writes marker files); an equivalent Project.transaction was added in ectt.prj. Owner to confirm that is the intended reading of SDD-003 section 3 | design wording ambiguity | src/ectt/prj/project.py |
| WP-MIG-04 | Format-specific adapters for commercial tools own (non-tabular) export formats (TOOL-MIG-030 remainder) | needs each tool's documented export sample or spec, which is not in the repository | docs/verification/WP-MIG-04-analysis.md "Not covered" |
