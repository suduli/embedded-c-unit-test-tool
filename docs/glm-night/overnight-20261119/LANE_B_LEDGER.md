# Lane B ledger — overnight 2026-11-19

Branch: `glm-night/20261119-b` (worktree `wt-night-b`), branch point `glm-night/20261119-plan` 46fa7e2.
Baseline at branch point (local main 353b9b4): 970 passed, 4 skipped; ruff, mypy, plan_check (346 reqs / 344 alloc), trace_check all clean. Re-verified in this worktree before item 1.

| item | state | commit | est tokens | cumulative | notes |
|------|-------|--------|-----------:|-----------:|-------|
| WP-CORE-03 | DONE | e7d6994 | 75k | 75k | ectt.core.platform: detection/suffix/report + AST offline audit (NFR-100 machine-checked); D-03 as written; 30 new tests; AC derived RECON-first (board has none for CMP-CORE). Est is actual (below 130k plan est) |
| WP-CORE-02 | DONE | a73a129 | 85k | 160k | chat-2 remainder closed: CATEGORY_EXIT_CODES + total exit_code_for_category + run() EcttError mapping; fixture pipeline routed through OutputRoot.transaction(token); 24 new tests. Product-op routing (prj saves, ana persist) → SECOND_PASS |
| WP-ANA-07 | DONE | 1d1e089 | 75k | 235k | PAR-140 inventory populated from extraction: variadic_function + variable_length_array_parameter, sorted/deterministic/round-trips through 1.4 reader; 9 new tests. Multi-file driver out of scope by instruction → SECOND_PASS |
| WP-ANA-06 | DONE (PAR-090 scope) | 0d10f95 | 85k | 320k | macros.py: resolve_interface_macros (object_like/function_like/unresolved, token-extent adjacency), derived data per eligibility precedent; PAR-080 untouched per instruction → SECOND_PASS (ADR-003 territory) |
| TASK-107 | DONE | 613588f | 90k | 410k | 19 hand-written single-fault mutants (core: canonical_text/float_repr/stable_id; prj: dangling refs/ShardStore), all killed, kill-rate report 100%; tests only, no src changes |
| WP-REP-01 | DONE | babdb69 | 95k | 505k | rep package: ReportModel (D-02 ids+digests, digest verified on load) + text/JSON renderers over shared accessors; board AC verified by cross-renderer agreement battery incl. persisted round-trip; lane A merged (c5d1c9c: EXH-01 98fe972 + TCM-02 ffacfce), post-merge gate green |

