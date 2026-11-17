# GLM Night — Baseline Record

**Recorded:** 2026-11-18, during `TASK-000` (EXEC-PLAN-001 §7.1).
**Worktree:** `E:\projects\UDS_Simulator\wt-unit-glm-night`, branch `glm-night/20261117`, cut from `docs/pending-decisions` tip `26ff2d7` (10 commits ahead of `origin/main`, not pushed — EXEC-PLAN-001 §5.5).
**Venv:** dedicated `.venv` in the worktree (§5.1 rule: never reuse the main checkout's `.venv`); `python -m venv` with Python 3.13.2 (`py -3.11` unavailable on this machine — 3.13 is the only installed interpreter; §5.1's `python -m venv` fallback used).
**Install:** `.venv/Scripts/python -m pip install -e ".[dev]"` — succeeded; resolved `PyYAML 6.0.3, libclang 18.1.1, pytest 9.2.0, jsonschema 4.26.0` + editable `ectt 0.1.0`.

## Test suite baseline

Command: `.venv/Scripts/python -m pytest -q -p no:cacheprovider`

**Result: 3 failed, 234 passed, 1 skipped** — exactly the documented baseline (EXEC-PLAN-001 §2, §5.4). The 3 failures, and only these:

1. `tests/ana/test_persist.py::test_real_extraction_assemble_write_read_roundtrip`
2. `tests/ana/test_persist.py::test_schema_version_gate_newer_minor_accepted_and_unknown_fields_ignored`
3. `tests/ana/test_persist.py::test_assemble_emits_1_1_with_not_extracted_inventory`

Visible failure mode (all three): `AssertionError: assert '1.2' == '1.1'` at `tests/ana/test_persist.py:630` — the tests assert schema version `1.1` literals while the module's current-version constant has moved to `1.2` (the schema 1.0 → 1.2 drift named in the TASK-001 card). These are the *only* permitted red tests; anything else red after TASK-000 is attributable to the current task.

## Design gates baseline

| Gate | Result |
|---|---|
| `design/trace/plan_check.py` | exit 0 — 346 requirements; 344 unique primary allocations; 191 packages; 642 person-weeks; 52-week lower bound |
| `design/trace/trace_check.py` | exit 0 — 344/344 in-scope requirements allocated; 259 design elements |
| `design/trace/unified_plan_sync.py --check` | exit 0 — EXEC-PLAN-001 MD and tracker HTML in sync (246 tasks) |

## Decision state baseline (unchanged by TASK-000)

D-01 (licence), D-02 (identity model), D-03 (platform order), D-04 (NFR calibration) — all pending user decision; ADR-003, ADR-004, ADR-005, ADR-007, SRS §27 q2/q9 — open. Nothing in this baseline touches them (EXEC-PLAN-001 §1 item 1, §6.1).

## Toolchain notes for later tasks

- Network + PyPI available on this machine (pip install succeeded).
- Rust: cargo/rustc 1.92 present but **no MSVC linker/Windows SDK** (see `docs/proposals/rust-gui-eval/memo.md` §8) — irrelevant to the Python queue; recorded here so nobody re-probes.
- Push remains owner-approved only (§5.5.4) — the worktree branch carries the 10 unpushed `docs/pending-decisions` commits underneath it.
