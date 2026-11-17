# BACKLOG_GLM_NIGHT — unattended overnight backlog for the GLM agent (ECTT, the Embedded-C Unit Test Tool)

Repo: `E:\projects\UDS_Simulator\Unit` (GitHub `suduli/embedded-c-unit-test-tool`). Python package `ectt`, tests in `tests/`, specs in `SRS-001`, `PLAN-001`, `design/`.
Generated 2026-11-17. Budget ≈ 3,000,000 tokens. Core queue ≈ 2.85M. Reserve queue ≈ 1.25M (only when core is finished).

> Replaces an earlier version of this file that wrongly targeted the UDS-SIMULATION website repo.

---

## 1. What was found (discovery summary)

State at HEAD `71e9811` on branch `docs/pending-decisions` (21 commits ahead of local `main`; T-15…T-22 only exist on this branch):

- **Implemented:** WP-CORE-01, WP-PRJ-01, WP-ING-01, WP-ANA-01/02/04 (+ T-07…T-13, T-15…T-22 review tasks, mostly spec/gate work). Spikes 01–03 done.
- **Baseline tests (`.venv`):** 234 pass, 1 skipped, **3 FAIL** — all in `tests/ana/test_persist.py` (`test_real_extraction_assemble_write_read_roundtrip`, `test_schema_version_gate_newer_minor_accepted_and_unknown_fields_ignored`, `test_assemble_emits_1_1_with_not_extracted_inventory`). Cause visible: tests assert schema `1.0`, emitter now produces `1.2` (drift after T-09/T-10). System Python lacks `clang`; use `.venv`.
- **Design gates green:** `design/trace/plan_check.py` and `trace_check.py` pass (346 reqs, 191 packages).
- **CI gap:** only `.github/workflows/traceability.yml` exists. No pytest, lint, type-check or coverage in CI; no `ruff`/`mypy` configured (pyproject has only pytest + jsonschema in dev extras).
- **Pending WPs** (PLAN-001 §5.5, all "Planned"): P1 packages not yet built include WP-CORE-02/03, WP-ANA-03/07, WP-ING-07, TCH-01/02, GEN-01, BLD-01, EXH-01…03, COV-01…03, REP-01…03. Decision-free, bounded ones are queued below.
- **Blocked by owner decisions (do NOT decide them):** D-01 licence (T-01, ADR-005), D-02 identity model (T-04, unblocks T-14), D-03 platform order (T-05), D-04 NFR calibration (T-06). T-02 (no-import/provenance rule for `vcast-findings/`) is "Not Started" but cites ADR-005.
- **GitHub:** no open issues; open PRs #6 (GitHub Projects workflow, `codex/github-projects-workflow`) and #4 (ADR-008 allocation, `fix/aif-provider-traceability`); stale local branches exist.
- **Docs:** static HTML in `docs/` (index, components, doc-map, oss-integration, reviews trackers) — this repo's "docs site".

### Mapping of your requested areas to this repo

| Requested area | Applies here as |
|---|---|
| SEO improvement | N/A (no public website). Closest: docs HTML metadata/readability → TASK-018 |
| UI redesign | N/A in code (GUI is WP-GUI-*, not started, ADR-001 spike only). Static docs pages only → TASK-018 |
| MCP work | N/A (no MCP server in this repo) |
| Post marketing | N/A and blocked by D-01 (don't publicize before licence). README/dev guide only → TASK-019 |
| docs-site update | TASK-017 (trackers/verification), TASK-018 (docs HTML), TASK-019 (README) |
| Test "SID" test cases | N/A (UDS SIDs belong to the other repo). Equivalent here: missing/failing tests → TASK-001, 004, 005 and the per-WP tests |
| New planning | TASK-014 (decision memos), TASK-015, TASK-023 |
| GitHub backlog | TASK-021 (read-only audit of PRs/branches) |
| Other gaps | TASK-002, 003, 007, 008, 019, 020, 022 |

---

## 2. Token estimate

| Queue | Tasks | Est. tokens |
|---|---|---|
| Core | TASK-000 … TASK-024 | **2,850,000** (table §5) |
| Reserve | TASK-101 … TASK-108 | 1,250,000 |
| Stop rule | stop starting new tasks at ≈2.8M used; keep ≈150k for TASK-024 | |

Estimates are rough (±40%). Track a running total in the log.

---

## 3. Agent instructions (READ FIRST, FOLLOW EXACTLY)

You are an unattended executor. No human will answer. Ambiguity → choose the most conservative reading, record the assumption in the log, continue.

### 3.1 Branch and isolation

Do not work on `main` or on `docs/pending-decisions` directly. Use a sibling worktree based on the current tip of `docs/pending-decisions` (it contains T-15…T-22; `main` does not):

```bash
cd /e/projects/UDS_Simulator/Unit
git worktree add ../wt-unit-glm-night -b glm-night/20261117 docs/pending-decisions
cd ../wt-unit-glm-night
py -3.11 -m venv .venv          # or: python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```

All work happens in `E:\projects\UDS_Simulator\wt-unit-glm-night` on `glm-night/20261117`. Do NOT use the main checkout's `.venv` (an editable install there would import the wrong `src`). If `libclang` fails to install, mark clang-dependent tasks BLOCKED and continue with the rest.

### 3.2 Commit workflow

- One commit per task (extra commits allowed for big tasks). Stage only the paths you touched (`git add <paths>`, never `git add -A`).
- Message format, exactly: `[GLM-NIGHT] TASK-012: <imperative summary, ≤70 chars>`. Body: what, why, how verified (commands + result), `Files:`. End with `Co-Authored-By: GLM Agent <noreply@example.com>`.
- Non-task commits: `[GLM-NIGHT] LOG: …`. Morning filter: `git log --grep='\[GLM-NIGHT\]' --oneline`.
- Commit only when acceptance criteria pass and the **full gate** (§3.5) is green, apart from failures already in the baseline (§3.4).
- Never: force-push, `git reset --hard` on shared refs, rebase pushed work, `--no-verify`, amend earlier task commits.
- After each phase run `git push -u origin glm-night/20261117` (plain push, never to `main`). If push fails, continue and note it.

### 3.3 Safety rules (hard)

1. Never make an owner decision. D-01…D-04, ADR-003/004/005/007 stay **Open**. Do not edit ADR files, change a decision-register state, change LICENSE/LICENSEES, or flip any "Awaiting decision" status. Memos and proposals go in `docs/proposals/` as drafts.
2. Do not edit accepted requirements text in `SRS-001` or accepted ADRs. You may allocate work and update derived tables only through the repo's own tool: `python design/trace/plan_check.py --write` and only in tasks that say so.
3. Do not touch `aidlc/` state or audit files, `.claude/`, `.agents/`, `.agy-staff/`, `.zcode/`, `vcast-findings/` (read-only reference; see TASK-015 for the no-import rule), or `spikes/`.
4. Never copy code, schema, strings or identifiers out of `vcast-findings/` into `src/`. `src/` is a fresh build (ADR-006).
5. Do not open, comment on, merge or close PRs/issues; do not delete branches; do not publish or post anything; no network calls from product code or tests (also a requirement, TASK-007).
6. No secrets in code or logs. No new runtime dependencies. Dev-only deps (ruff, mypy, pytest-cov) may be added to `[project.optional-dependencies].dev` in TASK-003/004 only.
7. Never delete or weaken tests, thresholds or gates to get green. A real failing test you cannot fix → `xfail(strict=True, reason=...)` plus a log entry, not removal.
8. Never delete files unless the task names them. Leave the stray `NUL` file alone.
9. Commands expected to exceed 15 minutes, or needing interaction → kill, mark BLOCKED.
10. Determinism is a product requirement (WP-CORE-01): new code must not use wall-clock time, random values or unordered iteration in outputs; use `ectt.core.determinism` helpers.

### 3.4 Failure handling — never stop the run

Per task: implement → verify → commit. If it can't be completed:
- Cap effort at **1.5× the estimate**, then stop.
- `git restore` only the paths you edited for that task (leave the tree clean).
- Log it `BLOCKED` or `FAILED` with one paragraph (command, error excerpt, what you tried).
- Continue with the next task whose dependencies are not blocked. Dependents become `SKIPPED (dep)`.
- Baseline: TASK-000 records the failing tests. Anything failing identically in the baseline is not yours (TASK-001 fixes the three known ones).

### 3.5 Verification (the "full gate")

```bash
.venv/Scripts/python -m pytest -q -p no:cacheprovider
.venv/Scripts/python design/trace/plan_check.py
.venv/Scripts/python design/trace/trace_check.py
```
Run the narrow test file first, the full gate before every commit. Tasks that add code also add tests (org rule: tests are a first-class deliverable; each new module needs the happy path and at least two error/edge cases; no always-passing tests).

### 3.6 Logging

Maintain `docs/glm-night/GLM_NIGHT_LOG.md` (created in TASK-000). After each task append and commit with the task:
`| TASK-id | DONE/PARTIAL/BLOCKED/FAILED/SKIPPED | commit sha | tokens (est.) | cumulative | notes/assumptions/follow-ups |`
Also keep sections "Decisions & assumptions" and "Ideas not done". At cumulative ≥ 2.8M jump to TASK-024.

### 3.7 Order

Core in numeric order. After TASK-024 is committed, if budget remains run Reserve in order, then refresh TASK-024 (`[GLM-NIGHT] TASK-024: refresh report`).

---

## 4. Do-not-touch list

- Everything in §3.3 items 1–4.
- Open PRs #4 and #6 and their branches.
- GUI, MCP, packaging release work, anything needing a debug probe, simulator, hardware or network.
- WPs that depend on open ADRs: ATG-02/03 (ADR-003), COV-01 integration (ADR-004), PKG-01 integration (ADR-007), COV-05 acceptance (SRS §27 q2), EXH-04 (SRS §27 q9), T-14 (needs D-02).

---

## 5. Core queue

| ID | Title | Area | Est. | Depends |
|---|---|---|---|---|
| TASK-000 | Worktree, venv, baseline, log | setup | 30k | — |
| TASK-001 | Fix the 3 failing `test_persist` tests (schema 1.0 → 1.2 drift) | tests | 70k | 000 |
| TASK-002 | CI workflow: pytest + design gates, Linux & Windows | gaps | 50k | 001 |
| TASK-003 | Add ruff + mypy config and triage findings | gaps | 120k | 001 |
| TASK-004 | Coverage baseline and gap-filling tests (≥80% on core/prj/ing) | tests | 200k | 001 |
| TASK-005 | ADR-002 grammar: rejection and preservation test suite | tests | 150k | 001 |
| TASK-006 | WP-CORE-02 structured error model, fail-safe, cancellation | impl | 220k | 004 |
| TASK-007 | WP-CORE-03 platform baseline and offline guarantee | impl | 120k | 006 |
| TASK-008 | WP-ANA-03 call graph and scope classification | impl | 250k | 006 |
| TASK-009 | WP-ANA-07 partial-failure resilience | impl | 130k | 006 |
| TASK-010 | WP-ING-07 authored link plan ingestion and validation | impl | 170k | 006 |
| TASK-011 | WP-PRJ-04 dangling reference detection | impl | 100k | 006 |
| TASK-012 | WP-PRJ-03 schema migration with explicit confirmation | impl | 200k | 006 |
| TASK-013 | WP-CORE-04 provenance record and version identification | impl | 130k | 006 |
| TASK-014 | Decision memos D-01…D-04 (decision-ready drafts) | planning | 120k | 000 |
| TASK-015 | T-02 draft: no-import/provenance rule for `vcast-findings/` | planning | 70k | 014 |
| TASK-016 | Verification analysis notes for landed WPs | docs | 90k | 013 |
| TASK-017 | Refresh subsystem tracker (md + html) for what landed | docs | 100k | 016 |
| TASK-018 | Docs HTML pages: status, metadata, links, a11y basics | docs-site | 100k | 017 |
| TASK-019 | README and developer guide (setup, test, gates, layout) | docs | 60k | 002 |
| TASK-020 | Trace/ID consistency checker beyond `plan_check` | gaps | 100k | 000 |
| TASK-021 | Read-only audit: PRs #4/#6, stale branches, repo hygiene | GitHub | 70k | 000 |
| TASK-022 | Dependency and licence audit (report only) | gaps | 40k | 000 |
| TASK-023 | Next-phase plan from PLAN-001 critical path | planning | 100k | 017 |
| TASK-024 | Morning review pack | review | 150k | all |

Sum ≈ 2.85M (TASK-024 is run last regardless of numbering gaps).

### TASK-000 — Worktree, venv, baseline, log
- Do: §3.1 setup. Run the full gate, save to `docs/glm-night/baseline.md` (pass/fail/skip counts, every failing test id, `plan_check`/`trace_check` outputs, python/libclang versions). Create `docs/glm-night/GLM_NIGHT_LOG.md` with the table header and the two extra sections.
- Done when: both files exist, baseline lists exactly the 3 known failures (or states the difference), commit exists.

### TASK-001 — Fix the 3 failing `test_persist` tests
- Files: `tests/ana/test_persist.py`, possibly `src/ectt/ana/persist.py`. Read `docs/verification/WP-ANA-04-analysis.md`, schema files `1.0/1.1/1.2`, and the T-09/T-10 evidence in `docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md`.
- Decide per failure whether the test is stale (asserts `"1.0"` where the emitter intentionally emits the current version) or the code regressed. Fix tests to assert the current version via the module's own constant, not a new literal, and keep the compatibility-rule tests (older/newer minor, different major) meaningful. Do not change emitted schema semantics.
- Done when: the 3 tests pass, no other test changed status, full gate green, commit body explains each failure's root cause.

### TASK-002 — CI workflow
- Add `.github/workflows/tests.yml`: on push/PR, matrix `ubuntu-latest` + `windows-latest`, Python 3.11, `pip install -e ".[dev]"`, run pytest and both design gates; pinned action versions like `traceability.yml`; `permissions: contents: read`. Do not modify `traceability.yml`.
- Verify: YAML parses (`python -c "import yaml…"`); the exact commands in the file succeed locally.
- Done when: workflow file exists, commands verified locally, note in log that CI itself could not be run.

### TASK-003 — ruff + mypy
- Add `ruff` and `mypy` to dev extras; add `[tool.ruff]` (line-length consistent with existing code, select a conservative rule set: E, F, I, B, UP) and `[tool.mypy]` (python 3.11, `ignore_missing_imports` only for `clang`). Run both; fix mechanical findings (imports, unused names) in small commits; do NOT mass-reformat. Remaining findings → `docs/glm-night/lint-baseline.md` with counts per rule.
- Done when: ruff exits 0 or has a documented ignore list with reasons; mypy runs and its remaining errors (if any) are listed; full gate green; `git diff --stat` shows no sweeping reformat.

### TASK-004 — Coverage baseline and gap tests
- Add `pytest-cov` to dev extras. Measure per package (`ectt.core`, `ectt.prj`, `ectt.ing`, `ectt.ana`); write `docs/glm-night/coverage-baseline.md`. Add tests to bring `core`, `prj`, `ing` to ≥ 80% line coverage (org floor) — real behaviour tests with ≥ 2 error/edge cases per uncovered function; no `assert True`, no `# pragma: no cover` additions. `ana` gaps: list only (needs libclang fixtures).
- Done when: report shows before/after; ≥ 80% on the three packages; gate green.

### TASK-005 — ADR-002 grammar tests
- Read `ADR-002-project-data-format.md`, `src/ectt/prj/yaml_adapter.py`, existing `tests/prj/test_yaml_adapter.py`. Add a suite (`tests/prj/test_adr002_conformance.py`) covering the restricted-grammar rules the ADR names: each forbidden construct is rejected with a named error (anchors/aliases, tags, multi-document, implicit typing hazards such as `no`/`on`/`1e3`/octal-looking strings, duplicate keys, non-string keys — whichever the ADR lists), byte-stable round trip, key-order preservation, comment preservation if the ADR requires it. Derive the list from the ADR text; cite section numbers in test docstrings.
- If a conformance test exposes a genuine adapter bug: fix minimally if clearly within ADR-002; otherwise `xfail(strict=True)` + log.
- Done when: every grammar rule in the ADR maps to ≥ 1 test.

### TASK-006 — WP-CORE-02 structured error model
- Requirements: NFR-090, NFR-180 (`SRS-001`); exit criterion in PLAN-001; design in `design/SDD-001/002`. Create `src/ectt/core/errors.py`: a base `EcttError` with stable `code`, `category` (usage / input / environment / internal / cancelled), `reason`, `context` (deterministic dict), JSON-serialisable; a cancellation token (`threading.Event` based) and a fail-safe wrapper that guarantees no partial output is left in the confined output root (use `ectt.core.fs`). Make the existing `prj`, `ing`, `ana` error base classes inherit from it **without changing their public names, messages or `reason` values**.
- Tests: serialisation determinism, category mapping, cancellation mid-operation leaves no partial files, existing error tests still pass unchanged.
- Done when: gate green, all existing error classes derive from `EcttError`, `docs/verification/WP-CORE-02-analysis.md` drafted (format of the ANA-04 note).

### TASK-007 — WP-CORE-03 platform baseline and offline guarantee
- Requirements NFR-010, NFR-020, NFR-100. Do NOT resolve D-03 (platform order). Implement `src/ectt/core/platform.py`: detect OS/arch/Python/libclang version, compare against the declared baseline (read the NFR text; encode both Windows and Linux as supported-in-parallel without ranking them), return a structured report. Add an **offline guard test**: import every `ectt` module with `socket.socket.connect`/`urllib` patched to fail, and assert no import-time or run-time network use across the existing pipeline fixture (`tests/core/fixture_pipeline.py`).
- Done when: platform report test passes on this machine, offline guard test passes, note in log that Linux behaviour is untested here.

### TASK-008 — WP-ANA-03 call graph and scope classification (needs libclang)
- Requirement PAR-060. Read `src/ectt/ana/interface.py`, `model.py`, schema 1.2, SDD-002 §3 for the model contract. Add call-graph extraction (direct calls; indirect calls through function pointers recorded as "unresolved indirect", never guessed) and classification of each callee as in-unit / external / library / unresolved. This adds model fields → **minor schema bump 1.3 additive** with a new `analysis-model-1.3.schema.json`; the 1.2 reader rules must keep working (add tests). Update the version constant and the TASK-001 tests accordingly.
- Tests: fixtures in `tests/ana/` (small C sources, same style as `test_interface.py`): direct call, static function, recursion, function-pointer call, call to undeclared function, macro-wrapped call.
- Done when: schema validates, determinism test (two runs byte-identical), gate green, `docs/verification/WP-ANA-03-analysis.md` drafted.
- Blocked → mark BLOCKED if libclang unusable.

### TASK-009 — WP-ANA-07 partial-failure resilience
- Requirements PAR-130, PAR-140. A failure on one translation unit/function must not abort the run; the model records the failure with a named reason (use TASK-006's error model) and every other element is still produced. Add fixtures with a syntax error in one file among valid ones. Reader and eligibility gate (`eligibility.py`) must treat failed elements as unmeasurable with the recorded reason.
- Done when: tests show the valid parts extracted, failure inventory present and deterministic.

### TASK-010 — WP-ING-07 authored link plan ingestion and validation
- Requirement ING-200; T-12 landed the LinkPlan spec (SDD-002/003 amendments, `DSN-ING-120`). Implement `src/ectt/ing/linkplan.py` per that spec: parse the authored link plan from the project store, validate (missing objects, duplicates, unknown toolchain keys, absolute paths outside the project), report each violation with a named reason.
- Done when: spec clauses map to tests; invalid plans never partially load; gate green.

### TASK-011 — WP-PRJ-04 dangling reference detection
- Requirement PRJ-090 (1w). Implement detection of references in the project store that point at missing ids (read `design/SDD-003-data-model.md` for reference kinds), returning a deterministic sorted list; integrate with `ectt.prj.project` load as a report, not an exception, unless the spec says otherwise.
- Done when: tests for none/one/many/cyclic references pass.

### TASK-012 — WP-PRJ-03 schema migration with explicit confirmation
- Requirement PRJ-040. Implement migration framework: registry of migration steps between project schema versions, a plan/dry-run that lists changes, and an `apply` that requires an explicit confirmation token argument (no implicit migration on load; old version loads read-only or is refused per SDD). Writes are atomic and use the confined output helpers; a failed migration leaves the original untouched.
- Done when: v(n)→v(n+1) example migration with tests (dry-run, confirmed, unconfirmed refused, failure leaves original byte-identical).

### TASK-013 — WP-CORE-04 provenance record and version identification
- Requirements QUA-060, INS-110. Add `src/ectt/core/provenance.py`: a deterministic record (tool version from package metadata, schema versions, python/libclang versions, input digests via existing determinism helpers) with no wall-clock fields in the hashed portion. `ectt.__version__` exposure if missing.
- Done when: record is reproducible in two runs; tests cover the changed-input digest case.

### TASK-014 — Decision memos D-01…D-04
- Source: "Decision queue" section of `docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md`, ADR-005 context, SRS LIC-010…060, the T-04 memo.
- Write `docs/proposals/decision-memos-20261117.md` (and update nothing else): per decision — question, options a–d with exact files that would change, the precise patch text to apply for each option (as fenced diffs, unapplied), risks, what unblocks, and your recommendation labelled as a recommendation. For D-01 include a plain comparison of AGPL-3.0 / Apache-2.0 / MIT / proprietary against LIC-010 as written.
- Done when: four self-contained sections; nothing in the repo's decision state changed.

### TASK-015 — T-02 draft: vcast-findings no-import rule
- Write `docs/proposals/T-02-no-import-rule-draft.md`: draft requirement/ADR-addendum text, a proposed automated check design (a test that scans `src/` for byte-identical or near-identical copies of strings/identifiers listed in `vcast-findings/*-symbols.json`, `vcapplib-sql-strings.json`, `vcapplib-recovered-schema.sql`), and a **working prototype test** `tests/core/test_no_vcast_import.py` that passes today (and fails on a planted fixture in a temp dir). It must read vcast-findings only to build deny-lists in memory; do not copy any of its content into the repo.
- Done when: prototype test passes and is deterministic; proposal states it depends on D-01 and is not adopted.

### TASK-016 — Verification analysis notes
- Pattern: `docs/verification/WP-ANA-04-analysis.md`. Add notes for WP-CORE-01 and for every WP landed tonight (CORE-02/03/04, ANA-03/07, ING-07, PRJ-03/04) covering requirements verified by analysis (*A*): requirement id → implementation reference → argument → test evidence (real test names that exist; verify with `pytest --collect-only`).
- Done when: every referenced test id exists.

### TASK-017 — Refresh subsystem tracker
- Update `docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md` (WP statuses → **Complete** only for WPs whose acceptance/exit criterion in PLAN-001 §5.4/§5.5 is actually met; "Partial — <what's missing>" otherwise; update the "Implemented at HEAD" line) and the HTML tracker `2026-11-07-subsystem-task-tracker.html` the same way (look at how it is built; if generated by a script run that script, otherwise edit the same strings). Run `plan_check.py --write` only if the PLAN-001 derived tables need regeneration, then the full gate. Do not change T-xx / D-xx statuses.
- Done when: counts in header lines match the tables; gates green.

### TASK-018 — Docs HTML pages
- Files: `docs/index.html`, `components.html`, `doc-map.html`, `oss-integration.html` (and their `*.visual-check.*` fixtures only if a script regenerates them). Check: `<title>`, meta description, `lang`, heading order, `alt` on images, link targets resolve (relative links to files that exist), light/dark contrast of the CSS variables (compute WCAG ratios in a script; fix only tokens that fail AA with minimal change), no external network assets. Mind that `traceability.yml` triggers on changes to `docs/index.html` and `docs/components.html` — run the gates.
- Done when: `docs/glm-night/docs-html-audit.md` lists before/after; gates green.

### TASK-019 — README and developer guide
- Update `README.md`: what ECTT is (from SRS intro, no claims beyond what exists), current status table (implemented WPs vs planned), quick start (`venv`, `pip install -e ".[dev]"`, test, gates), repo layout, how to read PLAN/SRS/SDD, contribution status (**do not** state a licence choice; link to LICENSE as-is and mention it is under review only if the file already says so). Add `docs/DEVELOPING.md` with the workflow (tests, gates, determinism rules, error model, how verification notes work).
- Done when: every command in the docs was executed successfully in this worktree.

### TASK-020 — Trace/ID consistency checker
- Add `design/trace/id_check.py` (stdlib only, runs in the CI environment with just PyYAML): verify that every `WP-*`, `TOOL-*`, `DSN-*`, `T-NN`, `NR-NN`, `ADR-NNN` id referenced anywhere in `*.md`/`*.html`/`design/**` exists in its defining register; report dangling and duplicate ids; exit non-zero on dangling. Do not wire into CI in this task; list pre-existing findings in `docs/glm-night/id-check-baseline.md` and fix only trivial typos.
- Done when: script is deterministic and fast (< 20s) with tests in `tests/design/test_id_check.py`.

### TASK-021 — Read-only repo/PR audit
- Using `gh` read-only (`pr view`, `pr list`, `pr diff --stat`) and `git`: for PR #4 and #6 — what they change, conflicts with `docs/pending-decisions`, whether still wanted (e.g., is #4's allocation already in the 191-package register?), CI status. List local/remote branches: merged, stale, ahead/behind. Check tracked junk (`git ls-files` for `.venv`, `.pytest_cache`, `__pycache__`, large files > 1 MB). Write `docs/glm-night/repo-audit.md` with recommended actions as a checklist for the owner. Take no action.
- Done when: every branch and both PRs have a row and a recommendation.

### TASK-022 — Dependency and licence audit (report only)
- `pip list --outdated`, `pip-audit` if installable offline-safe else note, licences of `PyYAML`, `libclang`, `jsonschema`, dev tools (from package metadata) vs. SRS licensing requirements. Note the `libclang>=18.1,<19` pin rationale (see spikes/ADR-001). No file changes besides the report `docs/glm-night/dependency-audit.md`.
- Done when: table + recommendations; `pyproject.toml` untouched.

### TASK-023 — Next-phase plan from PLAN-001 critical path
- Using the tracker and register: write `docs/proposals/next-phase-plan-20261117.md`: the next 10 decision-free WPs ranked (critical path first: ANA-05/06, ING-02/03/04, TCH-01/02, GEN-01 …), for each: effort, prerequisites already satisfied, what ADR/decision it waits on, test strategy, and an "agent-ready? yes/no + why" column; list what is gated by D-01…D-04 and what each answer unlocks.
- Done when: every WP id exists in the register; nothing outside `docs/proposals/` changed.

### TASK-024 — Morning review pack
- Create `docs/glm-night/MORNING_REVIEW.md`: all tasks with status/commit/tokens, `git log --grep='\[GLM-NIGHT\]' --stat` summary, final full-gate output, test count before/after (234+3 → ?), coverage before/after, BLOCKED/FAILED with reasons, assumptions needing owner input, suggested review order (highest risk first: TASK-008, 012, 006, 001), and exact commands to review/merge/discard. Push the branch.
- Done when: each task id appears exactly once.

---

## 6. Reserve queue (after TASK-024; same rules)

| ID | Title | Est. | Notes |
|---|---|---|---|
| TASK-101 | WP-ING-02 alternative ingestion paths | 150k | no D-gates; follow `compdb_adapter.py` pattern |
| TASK-102 | WP-ING-03 ingestion diagnostics, persistence, staleness extension | 120k | builds on T-08 `staleness.py` |
| TASK-103 | WP-ANA-06 static function testability and macro resolution | 200k | needs libclang |
| TASK-104 | WP-PRJ-02 diff-stable sharded storage | 200k | |
| TASK-105 | WP-CORE-06 logging and diagnostic bundle | 130k | depends on TASK-006 |
| TASK-106 | WP-TCH-02 host compiler detection (GCC/Clang) — detection and version report only, no building | 150k | |
| TASK-107 | Mutation-style test strengthening for `ectt.core` and `ectt.prj` (hand-written mutants, kill-rate report) | 150k | tests only |
| TASK-108 | Property-based fuzz-style tests for the YAML adapter and schema reader using seeded `random` | 150k | deterministic seeds only |

---

## 7. Morning review commands

```bash
cd /e/projects/UDS_Simulator/wt-unit-glm-night
git log --grep='\[GLM-NIGHT\]' --oneline
git log --grep='TASK-008' --stat
cat docs/glm-night/MORNING_REVIEW.md
# accept:  open a PR glm-night/20261117 -> docs/pending-decisions (or main); do not auto-merge
# discard: git worktree remove ../wt-unit-glm-night && git branch -D glm-night/20261117
```
