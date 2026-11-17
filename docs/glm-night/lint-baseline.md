# GLM Night — Lint Baseline (TASK-003)

**Recorded:** 2026-11-18. **Tools:** ruff 0.17.5, mypy 2.4.1, types-PyYAML 6.0.12.20261113 (all added to `[project.optional-dependencies].dev` — dev-only deps, per EXEC-PLAN-001 §5.4).

## Configuration (pyproject.toml)

- `[tool.ruff]`: `target-version = "py311"`; `extend-exclude` = spikes, vcast-findings, aidlc, design, docs, assets — read-only/do-not-touch surfaces (EXEC-PLAN-001 §1 item 4, §5.7 item 3) and paths whose Python this task does not own.
- `[tool.ruff.lint]`: explicit `select` (E4/E7/E9, F, B, I, UP, SIM, C4, RUF, PERF, PIE, FURB, PLW, BLE) so the checked surface is pinned against tool-default drift; E501 deliberately not selected (no uniform line budget exists). Ignored rules and per-file ignores carry reasons inline in the config.
- `[tool.mypy]`: `python_version = "3.11"`; cache kept inside `.venv`.

## Baseline → result

| Check | Before | After |
|---|---|---|
| `ruff check .` | 118 violations in scope (65 auto-fixable) | **exit 0** |
| `mypy src` | 11 errors in 6 files | **0 errors (25 files)** |
| `pytest -q` | 237 passed / 1 skipped | **237 passed / 1 skipped (no status change)** |

## Violations fixed (by rule, in-scope)

| Rule | Count | How |
|---|---|---|
| F401 unused-import | 33 | `**/__init__.py` per-file ignore (re-export surface documented by each module's `__all__`); remaining unused imports auto-fixed (incl. `io` after the fs.py annotation fix) |
| I001 unsorted-imports | 5 | auto-fix |
| UP017 datetime.timezone.utc → datetime.UTC | 14 | auto-fix |
| FURB110/188, RUF019, SIM114, SIM300 | 6 | auto-fix |
| F821 undefined name (`Any` errors.py, `Sequence` types.py + interface.py) | 3 | **real defects** — missing imports; the same names mypy flagged [name-defined] |
| PLW1510 subprocess-run-without-check | 6 | explicit `check=False` added where the return code is handled/asserted below (documents intent, keeps the rule active) |
| mypy staleness.py tuple/list mismatch | 4 | accumulator lists kept mutable; deduped tuples moved into new locals (`unique_reasons`, `unique_changed_paths`) |
| mypy fs.py IOBase vs IO[Any] | 1 | return annotation widened to `IO[Any]` (pathlib `.open()` result; text or binary per mode) |
| mypy yaml Event.anchor/tag (surfaced after installing types-PyYAML) | 2 | inline `# type: ignore[attr-defined]` with comment — accesses guarded by `getattr()` above; the stub package does not model these attributes on the base `Event` type |
| mypy clang.cindex untyped | (in the 11) | inline `# type: ignore[import-untyped]` — the library ships no py.typed (house style previously used on the same import, lost in an import-sort) |
| BLE001 blind except (src) | 2 | `# noqa: BLE001` with reason — deliberate fallback paths (unvalidatable/unnormalizable path returned raw) |
| PLW0603 global-statement | 1 | `# noqa: PLW0603` with reason — deliberate lazy module-level singleton (`_DEFAULT_FRONTEND`); registry refactor is not mechanical |
| SIM102/103/105/108/109/118/211, PERF401/402/102, PIE810, RUF005, RUF059, F601, F841, B007 | 23 | hand-applied mechanical rewrites (ternaries, `in`-tuples, comprehensions/extend, `contextlib.suppress`, unused-name removal, `keys()` drop); each verified behavior-neutral by the unchanged suite |

F601 note: `tests/ana/test_model.py` fixture dict carried `"unsupported_constructs"` twice (identical value; second silently won) — duplicate removed.

## Documented ignores (config, with reasons in pyproject.toml)

- `RUF022` (unsorted `__all__`) — 19 sites; semantic grouping kept over isort-style order.
- `F401` in `**/__init__.py` — intentional re-export surface.
- `BLE001` in `tests/**` — tests deliberately exercise broad failure paths.

## Known findings on excluded paths (out of this task's scope; left for their owning tasks)

- `design/trace/unified_plan_sync.py:273` B023 (lambda over loop variable — benign today because the lambda is consumed within the same iteration) and `design/trace/trace_check.py:452` F841 (unused `work`) — design/trace tooling.
- `spikes/spike-02-nested-editor/model.py:193` B008 (`QModelIndex()` default arg) and assorted ISC004/FURB167/C408 in spikes/ and design/ — do-not-touch surfaces (EXEC-PLAN-001 §1 item 4).

## No sweeping reformat

`git diff --stat`: 34 files, +167/−152 — import ordering, targeted rewrites, and the additions above only; no whole-file reformats.
