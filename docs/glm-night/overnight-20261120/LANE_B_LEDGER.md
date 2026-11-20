| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| FIX-REP | DONE | 3e68e96 | 110k | 110k | executor: Claude; 1465 passed |
| FIX-TXN | DONE | 650e1df | 120k | 230k | executor: Claude; Project.transaction (journal+rollback+cancellation) and token on save_file/save; write_analysis_model runs in OutputRoot.transaction, joining a caller |
| CI-LINUX | DONE | d997eaf | 60k | 290k | executor: Claude; tests.yml now runs pytest, ruff, mypy, plan_check, trace_check on both OSes plus the explicit Linux baseline test on Linux; actions pinned to exact ta |
| WP-MIG-02 | DONE | a4ef3dd | 180k | 470k | executor: Claude; import_ceedling_project preserves project.yml verbatim and registers test functions by file/name/line/id/digest; unconverted constructs reported with  |
| WP-MIG-04 | PARTIAL | PENDING | 230k | 700k | executor: Claude; import_mapped_csv maps any tabular export (csv/tsv/pipe/semicolon) onto data-driven cases with per-row outcomes and unmapped-column report. TOOL-MIG-0 |
