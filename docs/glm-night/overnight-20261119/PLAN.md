# Overnight plan 2026-11-19 (generated)

Base: local `main` 353b9b4 (970 passed, 4 skipped; ruff, mypy, plan_check, trace_check clean). Branch `glm-night/20261119-plan` holds these files; lanes branch from it.
Window: now to 06:00; stop starting items at 05:30. Token pool 3.0M: 1.45M stop per lane, about 0.1M reserve.
Estimates are rough (+/-40%). Rows marked tail run only if the lane is under 1.45M when it reaches them.

## Lane A

| # | Item | Est k | Cap k | Cumulative k | Cross-lane | Zone |
|---|---|---|---|---|---|---|
| 1 | N00 Apply D-02 to SDD-003 s6/s7 | 60 | 78 | 60 |  | core |
| 2 | WP-TCM-02 Data-driven test case model and on-disk format | 205 | 266 | 265 |  | core |
| 3 | WP-EXH-01 Host execution and per-test result reporting | 180 | 234 | 445 |  | core |
| 4 | WP-EXH-02 Crash isolation, timeout and process exit status | 155 | 201 | 600 |  | core |
| 5 | WP-TCM-03 Expected-value comparison engine | 180 | 234 | 780 |  | core |
| 6 | WP-TCM-04 Suites, selective execution and test independence | 155 | 201 | 935 |  | core |
| 7 | WP-EXH-03 Parallel test execution | 130 | 169 | 1065 |  | core |
| 8 | WP-TCM-05 Ranged and robustness input generation | 155 | 201 | 1220 |  | core |
| 9 | WP-TCM-06 Test case interchange import and export | 155 | 201 | 1375 |  | core |
| 10 | WP-CBT-01 Suite re-execution without regeneration | 130 | 169 | 1505 |  | core |
| 11 | WP-TCM-07 Boundary, equivalence and classification-tree derivation | 205 | 266 | 1710 |  | tail |
| 12 | WP-GEN-07 Stub behaviour programming | 205 | 266 | 1915 |  | tail |
| 13 | WP-ATG-01 Validation port and generated-case lifecycle | 180 | 234 | 2095 |  | tail |

## Lane B

| # | Item | Est k | Cap k | Cumulative k | Cross-lane | Zone |
|---|---|---|---|---|---|---|
| 1 | WP-CORE-03 Platform baseline and offline guarantee | 130 | 169 | 130 |  | core |
| 2 | WP-CORE-02 Structured error model, fail-safe termination and cancellation | 90 | 117 | 220 |  | core |
| 3 | WP-ANA-07 Partial-failure resilience | 90 | 117 | 310 |  | core |
| 4 | WP-ANA-06 Static function testability and macro resolution | 150 | 195 | 460 |  | core |
| 5 | TASK-107 Mutation-style test strengthening | 150 | 195 | 610 |  | core |
| 6 | WP-REP-01 Single intermediate report model | 180 | 234 | 790 | WP-EXH-01 | core |
| 7 | WP-REP-11 Report format extension point | 130 | 169 | 920 |  | core |
| 8 | WP-REP-06 Report provenance and format version stability | 155 | 201 | 1075 |  | core |
| 9 | WP-REP-08 Cross-unit summary and coverage trend | 180 | 234 | 1255 |  | core |
| 10 | WP-PLG-03 Built-ins implemented through public extension points | 155 | 201 | 1410 |  | core |
| 11 | WP-CORE-04 Provenance record and version identification | 60 | 78 | 1470 |  | core |
| 12 | WP-PRJ-05 Archival export and reproduction verification | 180 | 234 | 1650 |  | tail |
| 13 | WP-REP-09 Report generation from archived result data | 155 | 201 | 1805 |  | tail |
| 14 | WP-CLI-05 CI sharding and report merge | 155 | 201 | 1960 |  | tail |
| 15 | WP-TRC-01 Requirement association and bidirectional matrix | 180 | 234 | 2140 | WP-TCM-02 | tail |
| 16 | WP-TRC-02 Unlinked requirement and unlinked test reporting | 130 | 169 | 2270 |  | tail |
| 17 | TASK-108 Seeded property tests | 150 | 195 | 2420 |  | tail |
| 18 | WP-REP-12 Reconstructable open result export with test-case coordination | 155 | 201 | 2575 | WP-TCM-06 | tail |
| 19 | WP-MIG-01 Execution of existing Unity and cmocka suites | 180 | 234 | 2755 | WP-EXH-01 | tail |
| 20 | WP-TRC-03 Requirement import from ReqIF, CSV and plain text | 180 | 234 | 2935 |  | tail |

