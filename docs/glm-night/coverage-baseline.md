# TASK-004 — Coverage baseline (line coverage)

Measured with `pytest-cov` (dev extra) at commit `ea0a75f` (TASK-003 landed), before any
TASK-004 test was added:

```bash
.venv/Scripts/python -m pytest -q -p no:cacheprovider --cov=ectt.core --cov=ectt.prj --cov=ectt.ing --cov=ectt.ana --cov-report=term-missing
```

Line coverage is the org floor (`org.md`, Testing Posture: 80% line coverage). Branch coverage is not
measured. Coverage config adds no `omit` patterns and no `# pragma: no cover` exists in `src/`.

## Before (ea0a75f)

Totals per package are summed from the per-module statement counts reported by coverage.

| Package | Statements | Missed | Line coverage | Floor (80%) |
|---|---:|---:|---:|---|
| `ectt.core` | 412 | 80 | **80.6%** | met, marginal |
| `ectt.prj` | 618 | 79 | 87.2% | met |
| `ectt.ing` | 635 | 37 | 94.2% | met |
| `ectt.ana` | 1383 | 176 | 87.3% | not in scope (list only) |
| **All four** | 3048 | 372 | 88.0% | — |

Full suite before: 237 passed, 1 skipped.

## Per-module detail (before)

| Module | Stmts | Miss | Cover | Missing lines |
|---|---:|---:|---:|---|
| `core/determinism.py` | 179 | 26 | 85% | 60-62, 105, 111, 155-163, 207, 279, 283, 287, 289, 292, 347-356 |
| `core/fs.py` | 230 | 54 | 77% | 202-206, 230-231, 260, 268, 278-279, 296-300, 316, 328-339, 343-349, 353-366, 401, 410-411, 456-483 |
| `core/__init__.py` | 3 | 0 | 100% | — |
| `prj/project.py` | 159 | 25 | 84% | 81, 128, 162, 194-199, 203-208, 214, 270, 288, 307-308, 328-332 |
| `prj/yaml_adapter.py` | 256 | 45 | 82% | see run output |
| `prj/model.py` | 67 | 5 | 93% | 48, 91-93, 180 |
| `prj/paths.py` | 44 | 2 | 95% | 66, 120 |
| `prj/errors.py` | 86 | 2 | 98% | 64, 66 |
| `ing/compdb_adapter.py` | 297 | 21 | 93% | see run output |
| `ing/staleness.py` | 143 | 14 | 90% | see run output |
| `ing/model.py` | 101 | 2 | 98% | 55, 143 |

`ana` modules are listed for reference only; per the card they are gap-listed, not targeted.

## After (TASK-004 landing)

Tests added: `tests/core/test_fs_coverage.py` (19 tests) and `tests/core/test_determinism_coverage.py`
(20 tests). No `prj`, `ing` or `ana` tests were added: `prj` and `ing` already exceed 80%, and
`ana` is list-only by the card.

| Package | Statements | Missed | Line coverage | Before | Delta |
|---|---:|---:|---:|---:|---:|
| `ectt.core` | 412 | 14 | **96.6%** | 80.6% | +16.0 pts |
| `ectt.prj` | 618 | 79 | 87.2% | 87.2% | — |
| `ectt.ing` | 635 | 37 | 94.2% | 94.2% | — |
| `ectt.ana` | 1383 | 176 | 87.3% | 87.3% | — (list only) |
| **All four** | 3048 | 306 | 90.0% | 88.0% | +2.0 pts |

Suite after: **272 passed, 1 skipped** (was 237 passed, 1 skipped). Gates after: ruff exit 0,
`mypy src` 0 issues (25 files), `plan_check` exit 0, `trace_check` exit 0.

### Acceptance check

1. `ectt.core`, `ectt.prj`, `ectt.ing` ≥ 80% line coverage — **met** (96.6%, 87.2%, 94.2%).
2. Before/after per package — this file; `ana` gaps listed below.
3. No `assert True`, no `# pragma: no cover` added, no `omit` config — **met** (the test files
   assert concrete values, exception types and reason codes).
4. Full gate green — **met** (see above).

### Remaining uncovered lines in `ectt.core` (not targeted, reason recorded)

| Lines | Why not covered here |
|---|---|
| `determinism.py` 157-163 | `_stable_sort_key` branches for `Path`, `dict`/`set` and fallback types. Only reached by the set-ordering path; a direct sort-key test is a possible follow-up. |
| `determinism.py` 349-356 | POSIX re-exec (`os.execv`) branch. This machine is Windows; the POSIX branch is untested here and is a **platform gap**, not a Windows gap. |
| `fs.py` 278-279 | `OSError` while reading an existing file for the null-operation check. Needs an unreadable file, which is not reliably creatable on Windows without ACL changes. |

### `ectt.ana` gaps (list only, per the card)

Measured, not targeted. These need libclang fixtures to exercise:

| Module | Missing (before) |
|---|---:|
| `frontend.py` | 61 of 291 (79%) |
| `persist.py` | 26 of 187 (86%) |
| `types.py` | 43 of 258 (83%) |
| `interface.py` | 16 of 139 (88%) |
| `model.py` | 16 of 340 (95%) |
| `__init__.py` | 10 of 21 (52%) |
| `errors.py` | 4 of 109 (96%) |

Given the 80% floor applies to `core`, `prj` and `ing` only, `ana` is not a TASK-004 failure.
