# GLM Night Log

Running execution log for the overnight backlog (EXEC-PLAN-001 §5.8: one row per task; `sha` = landing commit; tokens in thousands, estimates where no meter is available; cumulative = running sum of the tokens column).

Branch: `glm-night/20261117` (worktree `../wt-unit-glm-night`, off `docs/pending-decisions` tip). Push pending owner approval (§5.5.4).

| TASK-id | DONE/PARTIAL/BLOCKED/FAILED/SKIPPED | sha | tokens | cumulative | notes |
|---|---|---|---|---|---|
| TASK-000 | DONE | e58eac4 | 30 (est) | 30 | Worktree + venv (py3.13, editable install OK) + baseline: 234 passed / 3 failed / 1 skipped (the 3 documented test_persist failures), plan_check 346/344/191, trace_check 344/344, sync --check OK; baseline.md written; no decision state touched |
| TASK-001 | DONE | aaf88a1 | 70 (est) | 100 | 3 test_persist failures fixed: SCHEMA_VERSION_CURRENT constant exposed in persist.py (assemble() uses it), tests assert the constant; newer-minor 1.5 fixture upgraded with the >= 1.1 mandatory inventories (TOOL-PAR-140/150); emit-version test renamed without the version literal. Suite 237 passed / 0 failed / 1 skipped; gates green |
| TASK-002 | DONE | 35487c4 | 50 (est) | 150 | .github/workflows/tests.yml: pytest + plan_check + trace_check on ubuntu-latest & windows-latest, py3.11, @v4/@v5 pins, contents: read; YAML parses; exact commands verified locally (237/1, gates exit 0); CI not executed - branch unpushed, first run on owner push/PR |
| TASK-003 | DONE | ea0a75f | 120 (est) | 270 | ruff 0.17.5 + mypy 2.4.1 config in pyproject; ruff exit 0 (118 -> 0: 65 auto + 39 hand incl. 3 real F821 missing imports), mypy exit 0 (11 -> 0), suite 237/1 unchanged; triage + per-rule counts in lint-baseline.md; no sweeping reformat |
| TASK-004 | DONE | (backfill at next tracker commit) | 110 (est) | 380 | pytest-cov 7.1.0 added to dev extras (not in addopts). Line coverage before: core 80.6%, prj 87.2%, ing 94.2%, ana 87.3% (list only). After: core 96.6% (+16 pts, 39 new behaviour tests in tests/core/test_fs_coverage.py and test_determinism_coverage.py), prj/ing unchanged (already above floor). Platform gap: determinism POSIX execv branch untested on Windows. Suite 272 passed / 1 skipped; ruff 0, mypy src 0, plan_check 0, trace_check 0; baseline in docs/glm-night/coverage-baseline.md |
