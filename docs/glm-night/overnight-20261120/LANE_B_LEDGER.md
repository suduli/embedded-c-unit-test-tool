| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| FIX-REP | DONE | 3e68e96 | 110k | 110k | executor: Claude; 1465 passed |
| FIX-TXN | DONE | 650e1df | 120k | 230k | executor: Claude; Project.transaction (journal+rollback+cancellation) and token on save_file/save; write_analysis_model runs in OutputRoot.transaction, joining a caller |
| CI-LINUX | DONE | d997eaf | 60k | 290k | executor: Claude; tests.yml now runs pytest, ruff, mypy, plan_check, trace_check on both OSes plus the explicit Linux baseline test on Linux; actions pinned to exact ta |
| WP-MIG-02 | DONE | a4ef3dd | 180k | 470k | executor: Claude; import_ceedling_project preserves project.yml verbatim and registers test functions by file/name/line/id/digest; unconverted constructs reported with  |
| WP-MIG-04 | PARTIAL | f3d5cb9 | 230k | 700k | executor: Claude; import_mapped_csv maps any tabular export (csv/tsv/pipe/semicolon) onto data-driven cases with per-row outcomes and unmapped-column report. TOOL-MIG-0 |
| WP-MIG-05 | DONE | 76da821 | 155k | 855k | executor: Claude; build_*_fidelity_report for CSV and Ceedling imports; converted/lossy/not_converted per artifact; deferred slot structures listed with location in a m |
| WP-TRC-04 | PARTIAL | d83e54b | 180k | 1035k | executor: Claude; export_reqif writes ReqIF 1.2 (requirements, tests, relations, specification) that import_reqif reads back exactly. Fixed importer to read the standar |
| WP-TRC-05 | DONE | dd71a54 | 180k | 1215k | executor: Claude; SourceLink/resolve_source_links (function or line range, persisted as function anchors, unresolved reasons) and review baselines + detect_changes (cha |
| WP-MIG-03 | DONE | c41e295 | 100k | 1315k | executor: Claude; INTERCHANGE_FORMATS registry + check_format_documentation (versions vs code, examples vs readers, schemas) + render_format_reference. Found and fixed: |
| WP-MIG-07 | DONE | 38ff925 | 180k | 1495k | executor: Claude; assess_ceedling_project / assess_mapped_csv dry-run the import adapters and report outcome (ready/needs_manual_work/not_assessable), fidelity counts w |
| FIX-ANAGATE | DONE | PENDING | 90k | 1585k | executor: Claude; assess_eligibility adds unsupported_construct:<kind> reasons (sorted by kind) to the function that owns the recorded first occurrence; find_unattribut |
