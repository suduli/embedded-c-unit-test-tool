# DRAFT — Tauri Proof-of-Concept Plan (≤ 3 person-days), scoped to the WP-SPIKE-02 pass criterion

**Status: DRAFT — a plan only. Nothing has been built; nothing is adopted; no decision state changes.**
Companion to [memo.md](memo.md). It exists so that, if the owner authorizes the PoC (memo.md §7, ESCALATE item 1), the execution is time-boxed, its evidence maps 1:1 to the existing spike-02 baseline, and its result feeds the GUI-stack question without re-opening anything by itself.

**Current execution status on the 2026-11-17 machine: BLOCKED — MSVC C++ build toolchain (link.exe + Windows SDK import libraries) is missing; cargo/rustc/npm are present; tauri crates are partially cached; a build would also require crates.io/npm network fetches.** Detail and probe transcript: memo.md §8. This plan is written for the first machine/run that has the toolchain provisioned and network fetches authorized.

---

## 1. Why this PoC and why this scope

- The only measured evidence for the hardest widget (WP-GUI-11, 8 pw — the largest package and the named schedule driver, PLAN-001 §4.4) is spike-02's PySide6 PASS: 4-deep nested struct with union, function-pointer member and fixed array, editable at every level, type-validated, enums by name, 242.3 ms cold start (spikes/spike-02-nested-editor/RESULTS.md; ADR-001 §3.6).
- PLAN-001 §4.4 sets the rule: "reopening an affected decision requires refreshed evidence." A Tauri PoC against **the same struct definition and the same checklist** produces exactly that evidence for options B/C of memo.md — and nothing else, deliberately.
- Out of scope on purpose: the engine, S6 server implementation beyond a shim, coverage views, reports, undo/redo beyond a smoke check, performance at realistic data volumes, Linux/WebKitGTK (gated on D-03, EXEC-PLAN-001 §6.1 — see §6 below). This PoC does **not** satisfy WP-GUI-11's exit criterion; it only refreshes spike-level evidence.

## 2. The struct under test — verbatim reuse

Use `spikes/spike-02-nested-editor/struct_def.md` **unchanged** (read-only; spikes/ must not be modified): `Config_t → Device_t → Channel_t → Actuator_t → Pixel_t(union)`, with `Mode_t` enum, `void (*on_event)(int)` function pointer, `int32_t samples[4]` fixed array, `actuators[2]`, all three special members as siblings at one level (struct_def.md §nesting path explanation). The type model is transcribed into the PoC's static JSON — no parsing, no engine.

## 3. Preconditions (toolchain gate — verify before starting, ~15 min)

| # | Check | Command | Blocker if absent |
|---|---|---|---|
| P1 | Rust toolchain | `cargo --version`, `rustc -vV` | install rustup (owner-approved) |
| P2 | **MSVC linker + Windows SDK** | trivial `cargo build` of `fn main(){}` succeeds | install VS C++ build tools + Windows SDK (owner-approved) — **this is what is missing today** |
| P3 | Node/npm | `node --version`, `npm --version` | install Node LTS |
| P4 | Tauri CLI | `cargo tauri --version` or `npx @tauri-apps/cli --version` | install (fetch authorized) |
| P5 | Crates/npm closure | `cargo fetch` and `npm install` succeed | authorize network fetches; record versions/hashes for the report (SEC-040 practice, TOOL-SEC-040) |

If any check fails, stop and record `BLOCKED: <tool>` in the PoC results file — exactly as this memo's own run did (memo.md §8).

## 4. Day-by-day plan (3 person-days, hard stop)

### Day 1 — skeleton + static type model (1.0 d)
1. Scaffold a minimal **Tauri v2** app: static HTML/CSS/JS front end, **no bundler**, `withGlobalTauri: true` so no npm runtime packages are required for the shell (verify this actually works — it is an assumption to test, marked unverified in memo.md §9.4).
2. Transcribe `struct_def.md` into a static JSON type model (the spike-02 equivalent of `FieldSpec`): enum with named constants, union with two variants, function-pointer member, fixed array, nested structs to depth 4.
3. Render the tree: expandable nested rows for struct/union/array members. Pick the grid/tree component (virtualized list at minimum); if AG Grid or TanStack Table is chosen, **record exact package name + version + licence text** in the results file (feeds memo.md §5 item 3, TOOL-LIC-050 check).
4. Wire an exit hook: window opens, tree renders, no network requests made (verify: zero non-file origins in devtools network log — TOOL-UIX-050/UIX-350 constraint).

### Day 2 — editor behaviors, mapped 1:1 to the spike-02 checklist (1.0 d)
Reproduce the five checklist items of spike-02 RESULTS.md against the web tree, as automated checks (the spike used pytest-qt driving real widgets; the PoC equivalent is a headless/automation driver over the real DOM — e.g. Playwright or Tauri's WebDriver, whichever is cheapest to set up within the day):
1. **Depth:** expanding to the union reaches `device → channel → actuators[0] → pixel` — the spike's finding applies here too: a human crosses **5** tree rows, not 4 (spike-02 RESULTS.md §Two findings; arrays materialize an extra row). Assert the row count.
2. **Enum by name:** `mode` presents `MODE_IDLE / MODE_ACTIVE / MODE_FAULT` by name, never a raw integer.
3. **Range rejection:** typing `999` into `pixel.channel.r` (0–255) and confirming does **not** commit; the displayed value stays. Implement and test the web equivalent of the spike's finding — widget-level input filtering is a soft guard; the model layer's validation is the enforcement point.
4. **Function pointer by name:** `on_event` presents candidate handler names, not a raw address.
5. **Array independence:** `samples` expands into 4 independently editable integer rows.
Type validation (UIX-170's constraint) runs against the static type model in the front end for this PoC; note explicitly in the results that this duplicates type knowledge outside the engine — the option-C design tension memo.md §3-C identifies.

### Day 3 — measurements + verdict (1.0 d, including reporting)

**Measurements to record** (each against the spike-02/spike-03 reference numbers; the PoC reports numbers, it does not invent pass bars where none exist):

| Measurement | Method | Reference from repo evidence |
|---|---|---|
| Cold start to interactive | timestamp from process launch to tree rendered & first expand answered | spike-02: 242.3 ms (PySide6, unfrozen); spike-03: ≈151–172 ms in-process frozen |
| Per-edit latency | median + p95 over ≥100 typed edits (commit → re-render), and, **if the optional S6 variant of §5 is built**, the same edit through an S6-shaped round trip | none measured anywhere — this is the first number of its kind (memo.md §3-C marks S6 per-edit latency unmeasured) |
| Install size | onedir folder size; and installer size if an NSIS/MSI bundle is produced | spike-03: 194.2 MB onedir (PySide6+libclang); ADR-001 §3.2's "~10 MB" Tauri figure is a planning claim, not a measurement |
| No-admin install & run | repeat the spike-03 method: build/run non-elevated, no registry write, confirm via `[Security.Principal.WindowsPrincipal]` check (spike-03 RESULTS.md §Admin-privilege check) | spike-03: PASS (local build), non-elevated |
| Offline run | run with network disabled; assert zero external requests | required by TOOL-UIX-050/NFR-100/UIX-350 |
| Memory after full expand | process working set after expanding all rows | not measured for spike-02 — record, don't gate |
| Component licence | grid/tree package name, version, licence identifier | TOOL-LIC-050 input; AG Grid commercial tiers flagged unverified in memo.md |

**Pass/fail criteria** (proposed here as the PoC's own bars; they are planning judgements, not requirements — the owner may adjust):
- **PASS requires:** all five checklist items of §Day 2 pass under the automated driver; no-admin install and run holds; zero network at runtime; cold start ≤ **500 ms** (≈2× the spike-02 Qt reference — a deliberately generous bar so that the editor's *behaviour*, not framework overhead, decides); per-edit p95 ≤ **50 ms**.
- **FAIL if** any checklist item cannot be made to pass within the day-2 box, or the web grid cannot render the 5-row-deep path with per-level editing without a custom reimplementation whose effort visibly exceeds the remaining budget (record as `PARTIAL: <what>`).
- Either way the result file states: **"This PoC refreshes spike-level evidence only; it does not satisfy WP-GUI-11's exit criterion and does not reopen any ADR by itself."** (PLAN-001 §4.4's refreshed-evidence rule cuts both ways.)

**Reporting:** write results to `docs/proposals/rust-gui-eval/poc/RESULTS.md` in the same worktree-branch pattern as this memo (draft, not adopted, every number reproducible, deviations listed the way spike-03 RESULTS.md does). Do not touch `spikes/`, `docs/reviews/`, ADR/SRS/PLAN text, or the tracker.

## 5. Optional stretch (only if Days 1–2 finish early): minimal S6-shaped round trip

Add a Python **shim** (not the engine) that speaks S6's framing — 4-byte big-endian length prefix + one JSON object, `session.hello` bootstrap, one `model.validate` operation — over stdio per SDD-002 §9.2, and route Day 2's type-validation edits through it. This produces the option-C-specific number (per-edit latency across the process boundary) that memo.md §3-C flags as the decisive unmeasured quantity. The shim is PoC-local code under `poc/`, is not wired into `src/`, and adds no runtime dependency to the repo. Skip this stretch without hesitation if Day 1 or 2 slips — the checklist evidence stands alone.

## 6. Platform note (D-03 interaction)

TOOL-UIX-340 mandates Linux x86-64 and Windows x86-64, but platform order is a pending owner decision (EXEC-PLAN-001 §6.1 D-03, which also gates WP-GUI-01 planning). This PoC therefore targets **Windows only** (WebView2), matching the spike-02/03 baseline machine; the Linux/WebKitGTK leg is listed as future evidence, not part of the 3-day box, and no platform ranking is implied by this plan.

## 7. Rules the PoC run must honor (from the governing docs, restated)

- Work in a worktree branch, never on `docs/pending-decisions`/`main`; one commit; stage only `docs/proposals/rust-gui-eval/poc/` paths (EXEC-PLAN-001 §5.5 rules, adapted to this memo's branch `proposals/rust-gui-eval`).
- Never edit `spikes/`, `ADR-*`, `SRS-001`, `PLAN-001`, `design/`, `LICENSE`, tracker JSON (EXEC-PLAN-001 §1 item 4; §5.7).
- No network calls from repo code at runtime; build-time fetches are environment provisioning, recorded with versions/hashes in the results (this plan; TOOL-SEC-040 practice).
- No new runtime dependencies in the repo: PoC dependencies live in `poc/` manifests only, and `poc/` ships with its own `.gitignore` for `target/`, `node_modules/`, `dist/`.
- Label everything DRAFT/not-adopted; change no decision state; escalate rather than decide (EXEC-PLAN-001 §5.6).
- Before committing: `.venv/Scripts/python design/trace/plan_check.py`, `.venv/Scripts/python design/trace/trace_check.py` — both must stay green (this memo's run verified them at exit 0 before its own commit).

---

*End of plan. Draft — not adopted; execution requires owner authorization (memo.md §7, ESCALATE item 1).*
