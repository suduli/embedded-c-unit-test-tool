# LANE A ledger — overnight 2026-11-21

Branch `glm-night/20261121-a`, branched from local `main` 26e4330 (plan header referenced a690b3f; main had moved — branched from current main HEAD as the setup block literally specifies `main`; queue file regenerated at 26e4330).

Baseline at branch point: full suite 3097 passed, 6 skipped per plan (not re-run; gates run per item).

Stop clock: lane stops starting new items at local 05:30 Nov 22 (first occurrence; run started 17:56 Nov 21). No ZAI usage counter available in this harness — token budget cap ignored per plan instruction.

| item | state | commit | est tokens | cumulative | notes |
|------|-------|--------|-----------|------------|-------|
| A1 | DONE | PENDING | 180k | 180k | executor: GLM (ZAI). ectt.bld.harness_build: build_harness_suite gates the build on the authored link plan (refusal stops the build with the plan's named reasons; the build port is never invoked), invokes a caller-supplied build port (no C compiler here), records the built suite and stores it in the SDD-003 layout at <output-root>/<env>/build/<scope>.suite-record.json (default output root build/ectt). ectt.cbt: reexecute_isolated + reexecute_parallel dispatch through ectt.exh run_isolated/run_parallel behind one shared integrity gate (record digest, binary digest, NR-19 stale check); reexecute_suite refactored onto the same gate, behavior unchanged. D-02 implemented as quoted by the owner: stable ids plus content digests. Verified by full gate (3121 passed, 6 skipped; ruff/mypy/plan_check/trace_check clean); tests/bld/test_harness_build.py (14 tests) + tests/cbt/test_reexecute_runners.py (10 tests) cover the four required cases (valid plan build, refused plan stops the build, re-execution reuses the record, changed source invalidates it) plus error cases. No second-pass row: nothing owner-blocking surfaced. |
