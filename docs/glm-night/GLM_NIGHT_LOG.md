# GLM Night Log

Running execution log for the overnight backlog (EXEC-PLAN-001 §5.8: one row per task; `sha` = landing commit; tokens in thousands, estimates where no meter is available; cumulative = running sum of the tokens column).

Branch: `glm-night/20261117` (worktree `../wt-unit-glm-night`, off `docs/pending-decisions` tip). Push pending owner approval (§5.5.4).

| TASK-id | DONE/PARTIAL/BLOCKED/FAILED/SKIPPED | sha | tokens | cumulative | notes |
|---|---|---|---|---|---|
| TASK-000 | DONE | e58eac4 | 30 (est) | 30 | Worktree + venv (py3.13, editable install OK) + baseline: 234 passed / 3 failed / 1 skipped (the 3 documented test_persist failures), plan_check 346/344/191, trace_check 344/344, sync --check OK; baseline.md written; no decision state touched |
| TASK-001 | DONE | (backfill at next tracker commit) | 70 (est) | 100 | 3 test_persist failures fixed: SCHEMA_VERSION_CURRENT constant exposed in persist.py (assemble() uses it), tests assert the constant; newer-minor 1.5 fixture upgraded with the >= 1.1 mandatory inventories (TOOL-PAR-140/150); emit-version test renamed without the version literal. Suite 237 passed / 0 failed / 1 skipped; gates green |
