# DRAFT MEMO — Should the ECTT GUI (and optionally the core) move from Python + PySide6 to Rust (+ Tauri or another Rust GUI)?

**Status: DRAFT — decision-ready input only. NOT ADOPTED. This memo changes no decision state.**
ADR-001 remains **Accepted** (Python + PySide6); ADR-003/004/005/007 remain **Open** (EXEC-PLAN-001-unified-execution-plan.md §1 item 1, §6.1 "Other open gates"). Per EXEC-PLAN-001 §5.6 item 4, decision memos and drafts are allowed under `docs/proposals/` when labelled draft/recommendation and not adopted — this document is exactly that. The decision itself belongs to the owner.
**Date:** 2026-11-17. **Author:** unattended executor run (`proposals/rust-gui-eval` worktree), per the task brief; every claim cites file + section; external or unmeasured claims are marked **unverified**.

---

## 0. The question

Should the GUI — and optionally the core — move from **Python + PySide6** to **Rust**, with Tauri (or another Rust-native GUI toolkit) as the front end?

Four options are evaluated:

| Option | Core | GUI |
|---|---|---|
| **A** | Python | PySide6 (current accepted position) |
| **B** | Rust | Tauri (web view) |
| **C** | Python | Rust/Tauri shell as a thin client over the S6 engine JSON API |
| **D** | Rust | Qt via Rust bindings |

This memo does not decide between them. It consolidates what the repository's own evidence says, identifies what is unmeasured, and ends with a clearly-labelled recommendation plus the triggers that would change it.

---

## 1. Constraints taken from the requirements

The requirements — not preferences — define what any stack must satisfy. Cited from SRS-001-requirements.md; attributes shown as *(priority, phase, verification)* per its §2.2 convention.

| Requirement | What it constrains | Bearing on a stack move | Source |
|---|---|---|---|
| TOOL-UIX-010 *(M, P1, A)* | Core is a CLI engine; GUIs are clients with **no capability unavailable from it** | Any Rust GUI must remain a pure front end; no capability may migrate into the GUI | SRS-001 §17.1 |
| TOOL-UIX-020 *(M, P2, A)* | Documented, **versioned JSON interface over stdio or local socket** for front ends | A Tauri shell is just another client of this seam; the seam is language-agnostic | SRS-001 §17.1; SDD-002 §9 |
| TOOL-UIX-030 *(M, P2, D)* | Standalone graphical application, complete workflow, no editor/IDE/third-party host app | Tauri is a desktop shell and is listed as a candidate technology in ADR-001 §3.2; that it fully satisfies UIX-030 is plausible but **unverified** — no repo document asserts it | SRS-001 §17.1; ADR-001 §3.2 |
| TOOL-UIX-040 *(M, P2, I)* | Installable/runnable by a user with **no development environment beyond a C toolchain** | The distribution story of every option is judged against this | SRS-001 §17.1 |
| TOOL-UIX-050 *(M, P2, T)*; TOOL-NFR-100 *(M, P2, I)*; TOOL-UIX-350 *(M, P2, I)* | Local engine; **no network access**; no telemetry | Any web-view stack must load zero remote content (CDN, fonts, update checks); must be verified, not assumed | SRS-001 §17.1, §20, §17.7 |
| TOOL-UIX-110/120 *(M, P2, T)* + TOOL-NFR-050 *(M, P2, A)* | Hierarchical tree with aggregated status; **10,000 test cases** scale | Qt gives native virtualized views "nearly free" (ADR-001 §3.1); a web stack must assemble this from AG Grid/TanStack + custom work (ADR-001 §3.2) — an evidence gap today | SRS-001 §17.3, §20; ADR-001 §3.1–3.2 |
| TOOL-UIX-150/160/170 *(M, P3, T)* | Tabular editor; structured/array parameters expand as a tree; **type-aware validation, enums by name** | The hardest widget; spike-02 evidence is Qt-specific and does not transfer (§4 below) | SRS-001 §17.4 |
| TOOL-UIX-320 *(M, P1, I)* | All state in plain-text, version-controllable files; **GUI never the sole source of state** | For a web-view GUI: webview-local storage (localStorage, IndexedDB) must not hold project state — a design constraint option C must carry | SRS-001 §17.7 |
| TOOL-UIX-330 *(M, P2, T)* | GUI-created projects fully usable from the CLI and reverse | Falls out of the S6 design (`cli_equivalent` on every response), in **all** options | SRS-001 §17.7; SDD-002 §9.3 |
| TOOL-UIX-340 *(M, P2, T)* | Linux x86-64 **and** Windows x86-64 | Qt renders uniformly; Tauri "varies — WebView2 on Windows vs WebKitGTK on Linux" (ADR-001 §3.2) | SRS-001 §17.7; ADR-001 §3.2 |
| TOOL-UIX-370 *(S, P3, T)*; TOOL-NFR-180 *(M, P2, T)* | Responsive UI during long ops; interruptible, valid state | Progress and cancellation are **protocol-level** in S6 — preserved in all options | SRS-001 §17.7, §20; SDD-002 §9.2–9.3 |
| TOOL-NFR-110 *(S, P2, I)*; TOOL-INS-020 *(M, P2, D)* | Installation without administrative privileges | Both stacks must demonstrate it; PyInstaller side is evidenced (spike-03), Tauri side is not | SRS-001 §20, §24 |
| TOOL-INS-010 *(M, P2, D)*; TOOL-INS-030 *(M, P2, D)* | Fully offline install; **no language runtime, package manager or compiler beyond the existing C toolchain** | Option A's PyInstaller bundle satisfies this mechanically; options B/D satisfy it for the core; **option C still ships the Python engine**, so the runtime-free claim rests on the engine bundle in every option | SRS-001 §24 |
| TOOL-INS-040 *(M, P2, I)*; TOOL-INS-050 *(M, P2, T)* | Self-contained archivable artifact reinstalled **years later**; side-by-side versions | The Qt bundle is a plain folder of DLLs (spike-03); a Tauri install depends on the host's WebView2 system component — a long-term archivability dependency that is **unverified** | SRS-001 §24; spike-03 RESULTS.md §Admin-privilege check |
| TOOL-SEC-010/020/030/040 *(M, P2)*; TOOL-LIC-030/060 *(M/S, P1/P2)* | Signed artifacts; SBOM with hashes; reproducible builds; pinned deps; automated license check | ADR-001 §0: qualification scope "disfavours a dynamic runtime with a large transitive dependency tree" — the in-repo argument that points at a compiled core long-term; neither stack has demonstrated SEC-030 reproducibility — **unverified** both ways | SRS-001 §22, §21; ADR-001 §0 |
| TOOL-LIC-010 *(M, P1, I)*; TOOL-LIC-020 *(M, P1, I)*; TOOL-LIC-050 *(M, P2, I)* | Permissive license for the tool's source; strong copyleft only as separate processes; no components whose license prohibits commercial use | PySide6 is **LGPL** — dynamic-linking, replaceability and SBOM obligations apply (ADR-001 §3.4); Tauri is MIT/Apache-2.0 (ADR-001 §3.2); the grid components a web editor needs (AG Grid) have commercial tiers — **unverified, must be checked before any option-C commitment** | SRS-001 §21; ADR-001 §3.4, §3.2 |
| TOOL-PAR-100 *(M, P2, T)*; TOOL-PAR-110 *(S, P2, A)* | JSON analysis model is the **sole input** to downstream stages; schema-versioned | The seam that makes a core-language swap survivable downstream (PLAN-001 §4.3 row 1) | SRS-001 §4; PLAN-001 §4.3 |
| TOOL-PAR-070 *(S, P2, T)*; TOOL-UIX-270 *(S, P3, T)* | CFG; graphical CFG view | The only CFG consumers (ADR-001 §2.1); they drive the isolated-analyzer path in every option, not the GUI language | SRS-001 §4, §17.6; ADR-001 §2.1 |

---

## 2. The two seams that decide whether any move is survivable

1. **TOOL-PAR-100's JSON analysis model** (SRS-001 §4; ADR-001 §2.4: "Treat that JSON model as an inviolable interface"). PLAN-001 §4.3 row 1 makes this the reason a core-language reversal is *recoverable* at all: "The `TOOL-PAR-100` JSON model seam is what makes this survivable: downstream L2–L5 packages consume the model, not the analyzer. **Hold that seam absolutely.**"
2. **S6, the engine API** (SDD-002 §9). JSON over stdio or a filesystem-permissioned local socket, length-prefixed frames of 1–8,388,608 bytes, `session.hello` version negotiation, protocol-level progress and cancellation, and `cli_equivalent` on every operational response (SDD-002 §9.1–9.3). Its contract points state: "Front-ends hold no capability. The API surface is the complete capability surface" (SDD-002 §9.3). SDD-001 §8 records the consequence in one line: "A technology change is a rewrite of L5 only."

Together these mean: **the GUI language is a fully isolated variable** (it can change with zero engine rework), and **the core language is an L1-local variable** (it can change without touching L2–L5, at the cost of re-implementing the analyzer-side packages). That is what makes options C and B structurally different in blast radius — not preference.

---

## 3. Options

### Option A — stay Python + PySide6 (the accepted position)

**What changes:** nothing. WP-GUI-01..22 and WP-PKG-01 proceed as planned (PLAN-001 §5.5). ADR-001 §3.5 ("PySide6 (Qt) if the core is Python — which is the recommendation in §2.4") and §4 stand. ADR-007 remains open for the per-platform installer/signing mechanism only (ADR-001 §5, ADR-007 entry).

**WPs invalidated/rebuilt:** none, by definition.

**Nested editor (WP-GUI-11, 8 person-weeks — the single largest WP in the plan, PLAN-001 §4.4):** direct path. WP-GUI-11 inherits two spike-02 findings ready-made: (1) "4-deep" is a schema-type count, not a tree-row count — arrays materialize an extra row, so the spike's path crosses **5** rows (spike-02 RESULTS.md §Two findings); (2) the widget-level `QIntValidator` is a soft guard and range enforcement must live in the model's `validate()`, not the validator (same section). Residuals, honestly scoped by the spike itself: performance at realistic data volumes, undo/redo, and persistence-format integration are untested (spike-02 RESULTS.md §What this does not prove). Risk R-02 is Low after the spike (ADR-001 §6) with a documented fallback: "Ship a flat editor for scalars and a raw C fallback for aggregates" (PLAN-001 §8, R-3).

**libclang path:** python-clang official bindings, AST-only — proven at scale: spike-01 extracted 1,810 functions / 506 types / 1,502 calls from 151,558 lines of real vendor embedded C with zero parse errors; R-01 is Low (ADR-001 §2.5). CFG needs (PAR-070, UIX-270 only, ADR-001 §2.1) are served by a focused isolated C++ LibTooling executable emitting the same JSON model (ADR-001 §2.4).

**Distribution / install (INS-010/020, NFR-110):** the only option with **measured** packaging evidence: PyInstaller onedir bundle of PySide6 + libclang builds cleanly, 194.2 MB, in-process cold start ≈151–172 ms (mean ≈162 ms), built and run non-elevated, libclang collected via a plain `binaries=[...]` entry (spike-03 RESULTS.md §Measurements, §Admin-privilege check; ADR-001 §2.3.1). The verdict is explicitly **"PASS (local build)", not a clean-machine PASS**: Defender/SmartScreen behaviour on a genuinely clean machine is the untested remainder (spike-03 RESULTS.md §Honest limits; ADR-001 §2.3.1; R-03, ADR-001 §6) — and it is now formalized as the release gate "TOOL-INS-120 / clean-machine endpoint acceptance", which no release may ship without (ADR-001 §5, ADR-007 entry, recorded 2026-11-17; PLAN-001 §5.5 WP-PKG-01 exit criterion). Secondary open item: the source/coverage editor widget (UIX-200, WP-GUI-14) is **unselected** — QScintilla's PyQt/GPL-commercial licensing does not automatically carry to PySide6 (ADR-001 §3.4).

**Contributor pool:** "Largest — few embedded C engineers write Rust" is the table's own phrasing for Python's embedded pool (ADR-001 §2.2); R-06 ("insufficient contributors", likelihood High) is mitigated precisely by this choice ("Choose the language for contributor availability", ADR-001 §6).

**Risks:** R-03 policy risk (Medium, "narrowed to policy risk only", ADR-001 §6); LGPL SBOM/replaceability work before release (ADR-001 §3.4); reproducible-build evidence for a Python transitive dependency tree is unverified (TOOL-SEC-030; ADR-001 §0 names the "large transitive dependency tree" as the qualification-facing weakness of a dynamic runtime).

**Reversibility:** the seams preserve both exits. A later GUI move is "an L5 rewrite and nothing else moves" (PLAN-001 §4.3 row 2); a later core move is absorbed by the PAR-100 seam (§4.3 row 1). Staying costs nothing *now*; its price is only that the GUI WPs eventually get built in Qt, at which point the GUI-move option acquires the same sunk cost every option has.

### Option B — Rust core + Tauri

**What changes:** a full re-implementation of the core in Rust and a full GUI rebuild on web technology inside a Tauri shell.

**WPs invalidated/rebuilt (PLAN-001 §4.3):** two rows apply.
- Row 1 (core language → C++ or Rust): invalidates `WP-ANA-01/02/03/05/06`, `WP-CORE-03`, `WP-PKG-01` — **30 person-weeks sunk**; recoverable downstream only because of the PAR-100 seam. Of the named set, `WP-ANA-01` (4w) and `WP-ANA-02` (5w) are already Implemented (EXEC-PLAN-001 §7.5; effort figures PLAN-001 §5.3) — that work is stranded.
- Row 2 (GUI → non-Qt): all 22 `WP-GUI-*` are rebuilt — **85 person-weeks** of planned work spent in the new stack instead (none of it is sunk today; all 22 GUI WPs are Planned, EXEC-PLAN-001 §2).
- **ASSUMPTION (recorded, conservative):** §4.3's row 1 does not name the other landed Python packages (`WP-CORE-01` 3w, `WP-PRJ-01` 4w, `WP-ING-01` 3w, `WP-ANA-04` 3w — efforts per PLAN-001 §5.3). §4.3's recoverable column speaks only of L2–L5 consuming the model. A full core rewrite re-implements these as well; their contracts (determinism, plain-text store, ingestion, schema versioning) survive, their Python code does not. Treat the 30 pw as a floor, not the total.

**Nested editor path (WP-GUI-11):** the spike-02 PASS does **not** transfer. It validated `QAbstractItemModel` + per-kind `QStyledItemDelegate`s — Qt idioms (spike-02 RESULTS.md; ADR-001 §3.6). A Tauri GUI rebuilds the editor on "AG Grid or TanStack Table plus custom work" (ADR-001 §3.2). PLAN-001 §4.4 is explicit about the rule that governs this: "reopening an affected decision requires refreshed evidence." The two hard-won findings (array row-depth; validate()-enforces-not-the-validator) are Qt-idiom statements; their web equivalents must be re-derived. R-02 returns to roughly its pre-spike level — **judgement, not measurement**.

**libclang path:** `clang`/`clang-sys` crates, AST-only (ADR-001 §2.2), plus the same isolated-analyzer option for CFG. The decisive loss is ecosystem reuse: "gcovr, lizard, StrictDoc, pyOCD, Twister are all Python and importable as libraries" in Python; in Rust/C++ "every one becomes a subprocess" (ADR-001 §2.2 ecosystem row; ADR-006 §4.2 "Ecosystem reuse — inverted").

**Distribution / install (INS-010/020, NFR-110):** Rust's distribution row is "Strongest — single static binary" (ADR-001 §2.2) and Tauri's bundle is "~10 MB" (ADR-001 §3.2 — the repo's own planning figure, **not a local measurement**). But note what actually ships: the engine still carries libclang (≈80.1 MB of spike-03's 194.2 MB bundle, spike-03 RESULTS.md §libclang shared-library collection outcome) plus whatever ecosystem tools become subprocesses; and the clean-machine endpoint acceptance gate (TOOL-INS-120; ADR-001 §5 ADR-007 entry) applies to whatever artifact ships, in every option. WebView2 presence/version on the target host is a new system-level dependency bearing on INS-040 archivability — **unverified**.

**Contributor pool:** core pool is the smallest of the three languages ("few embedded C engineers write Rust", ADR-001 §2.2); the front-end pool is large (web developers, ADR-001 §3.2). Option B trades core contributors for GUI contributors — in direct tension with the R-06 mitigation (ADR-001 §6).

**Risks:** R-06 (core contributors, High likelihood); R-02 reopened for the editor; time-to-first-prototype "Months" vs Python "Weeks" (ADR-001 §2.2); reimplementation of what the Python ecosystem gives free (the explicit caveat ADR-001 §2.4 attaches to choosing Rust); UIX-340 rendering variance (ADR-001 §3.2); SEC-030 reproducibility unverified for a cargo dependency tree.

**Reversibility:** the PAR-100 seam keeps L2–L5 intact through the rewrite (PLAN-001 §4.3 row 1), but the sunk 30 pw grows every week the Python core lands more WPs. This option is cheapest exactly now — and most expensive after P2.

### Option C — Python core + Rust/Tauri GUI over the S6 JSON API

**What changes:** the GUI only. The engine stays Python; a Tauri shell becomes another front-end client speaking S6 over stdio/local socket (TOOL-UIX-010/020; SDD-002 §9). This is **not** the "localhost server + browser" model ADR-001 §3.3 rejected: S6 offers no TCP transport by design — "an open localhost port is a host-firewall and endpoint-monitoring problem in precisely the defence, aerospace, and automotive environments this tool targets" (SDD-002 §9.1; DSN-API-030). The deferred browser UI (TOOL-UIX-400, F) "gets its own transport and its own security analysis rather than widening S6" (SDD-002 §9.1) — option C does not build it.

**WPs invalidated/rebuilt (PLAN-001 §4.3 row 2 only):** all 22 `WP-GUI-*` are rebuilt on the new stack — 85 pw of *planned* (not sunk) effort, and the row's recovery verdict is "Fully. `CMP-GUI` holds no capability of its own; its data contract is the test case model. A technology change is an L5 rewrite and nothing else moves." Engine-side WPs, including everything already Implemented (9 packages, EXEC-PLAN-001 §2), are untouched. **ASSUMPTION (recorded):** WP-PKG-01's scope grows, because the release must package a second, separate artifact (Tauri shell) alongside the engine bundle — §4.3 does not address this; conservative reading is added PKG effort, not invalidation.

**Nested editor path (WP-GUI-11):** same evidence gap as B — no transferred spike, refreshed evidence required (PLAN-001 §4.4) — plus one option-C-specific question: where does per-keystroke type validation live? Either re-implemented in the front end (duplicating C-type knowledge outside the engine) or done via S6 operations (a round trip per edit; frames up to 8 MiB are transport-legal, SDD-002 §9.2, but **interactive per-edit latency over S6 is unmeasured** — no repo document measures it). TOOL-UIX-170 demands type-aware validation; TOOL-UIX-320 forbids the GUI from being the sole source of state, so the webview must not persist project state locally. Both are exactly what the PoC in poc-plan.md is scoped to measure.

**libclang path:** unchanged from A — python-clang with spike-01's evidence intact (ADR-001 §2.5). This is C's structural advantage over B/D: zero core risk, zero ecosystem loss, and every landed package keeps working.

**Distribution / install (INS-010/020, NFR-110):** the engine still ships as the PyInstaller bundle (194.2 MB measured, spike-03), of which libclang is ~80 MB and Qt DLLs are the rest (spike-03 §Measurements) — option C shrinks only the GUI share, not the engine's; the runtime-free install claim (INS-030) continues to rest on the engine bundle, unchanged. The Tauri shell adds ~10 MB (ADR-001 §3.2 figure, unmeasured locally). Whether the two artifacts merge into one installer is precisely the open ADR-007 question (ADR-001 §5; EXEC-PLAN-001 §6.1). The clean-machine endpoint acceptance gate applies to the combined shipping artifact.

**Contributor pool:** engine Python (largest embedded pool, ADR-001 §2.2) + GUI web developers (large pool, ADR-001 §3.2) — the best split among the moving options, and each pool works in its own language.

**Risks:** R-02 reopened for the web editor (as B); unmeasured S6 per-edit latency; grid-component licensing (AG Grid commercial tiers — **unverified**, must be checked against TOOL-LIC-050 before any commitment); WebView2/WebKitGTK rendering variance against UIX-340 (ADR-001 §3.2); two-artifact packaging complexity.

**Reversibility:** this is the cheapest decision point that will ever exist for a GUI-stack move — **zero GUI sunk cost today** (all 22 GUI WPs Planned, EXEC-PLAN-001 §2). A failed PoC costs ≤3 person-days (poc-plan.md) and A is restored with nothing lost; an adopted move still leaves the engine swap absorbed by PAR-100 later (§4.3 row 1). Conversely, once WP-GUI-01 starts landing Qt code, option C's cost curve begins.

### Option D — Rust core + Qt bindings (e.g., CXX-Qt)

**What changes:** the core rewrites (as B) *and* the GUI is re-hosted from PySide6 to Qt-through-Rust-bindings. The toolkit stays Qt; the language changes everywhere.

**WPs invalidated/rebuilt:** row 1 of PLAN-001 §4.3 applies in full (30 pw; `WP-ANA-01/02` landed and stranded) — plus the same conservative assumption about the other landed Python packages as option B. Row 2 ("GUI → non-Qt") does **not** literally apply, since the toolkit is still Qt; but every one of the 22 `WP-GUI-*` implementations is rewritten in a different language against different bindings. The "fully recoverable, L5 rewrite only" reasoning of row 2 must be re-derived for a same-toolkit-different-language rewrite — **judgement, marked as such**.

**Nested editor path (WP-GUI-11):** spike-02's *findings* transfer conceptually (same Qt widget classes, same validate()-enforces principle) but none of the *code* transfers; no Rust-Qt spike exists anywhere in the repo. The CXX-Qt binding project's maturity is **unverified** — no repository document evaluates it, and this memo does not attempt to.

**libclang path:** `clang`/`clang-sys` AST-only (ADR-001 §2.2), with the same ecosystem inversion as B (ADR-006 §4.2).

**Distribution / install:** a static Rust core plus Qt libraries to bundle; the LGPL dynamic-linking, replaceability and SBOM obligations of §3.4 persist unchanged; no packaging evidence exists for Rust+Qt — **unverified**.

**Contributor pool:** plausibly the smallest of all options — the intersection of embedded-Rust and Rust-Qt expertise is narrower than either alone — **unverified inference, marked as such**.

**Risks:** all of B's core risks, plus binding immaturity, plus the highest evidence deficit of the four options (zero spikes speak to it).

**Reversibility:** as B — PAR-100 absorbs the downstream; the sunk cost grows with every landed Python WP.

---

## 4. Decision table

Every cell cites repo evidence or is marked unverified/judgement. "pw" = person-weeks (PLAN-001's unit).

| Criterion | A — PySide6 | B — Rust core + Tauri | C — Python core + Tauri GUI | D — Rust core + Qt bindings |
|---|---|---|---|---|
| Nested-editor (WP-GUI-11) evidence | **PASS, measured** — spike-02 checklist 5/5, 242.3 ms cold start, two design findings carried (spike-02 RESULTS.md; ADR-001 §3.6) | None — refreshed evidence required (PLAN-001 §4.4); PoC planned (poc-plan.md) | None today; same PoC supplies it | None; findings transfer only conceptually |
| Packaging evidence (INS-010/020, NFR-110) | **Measured** — 194.2 MB onedir, ≈162 ms in-process cold start, non-elevated; clean-machine endpoint test still open (spike-03 §Honest limits) | None local; "~10 MB" is ADR-001 §3.2's planning figure — unverified | Engine side = A's evidence; shell side unverified | None — unverified |
| libclang / ecosystem | Official python-clang; spike-01 held at 151,558 LOC (ADR-001 §2.5) | clang-sys; ecosystem reuse inverted — libraries become subprocesses (ADR-001 §2.2; ADR-006 §4.2) | **Unchanged from A** | clang-sys; inverted as B |
| Engine WPs invalidated (PLAN-001 §4.3 row 1) | 0 | 7 WPs, 30 pw sunk (ANA-01/02 already landed) | 0 | 7 WPs, 30 pw sunk (ANA-01/02 landed) |
| GUI WPs rebuilt (§4.3 row 2) | 0 | 22 WPs, 85 pw (planned, not sunk) | 22 WPs, 85 pw (planned, not sunk) | 22 WPs re-implemented in a new language — row 2 not literally applicable (judgement) |
| Sunk effort at risk **today** | 0 (A is the baseline) | ≥30 pw, plus 13 pw landed-but-unnamed Python WPs under the conservative assumption of §3-B | 0 | ≥30 pw + same assumption |
| Contributor pool | Largest embedded pool (ADR-001 §2.2); R-06-aligned (§6) | Smallest core pool / large GUI pool (§2.2, §3.2) | Largest core pool / large GUI pool | Plausibly smallest overall (unverified inference) |
| Platform consistency (UIX-340) | Uniform (ADR-001 §3.2) | WebView2 vs WebKitGTK variance (§3.2) | Same variance, GUI only | Uniform (Qt) |
| Licence interactions | LGPL dynamic-linking obligations; QScintilla unselected (§3.4) | MIT/Apache (§3.2); grid licence must be checked (unverified) | LGPL engine-side unchanged + grid licence unverified | LGPL obligations persist (§3.4) |
| Reversibility from today | Both seams preserve future exits (§4.3) | PAR-100 preserves downstream only; core cost grows weekly | Cheapest window ever for a GUI move; engine exit preserved | As B |
| Fits the accepted ADR-001 §4 position | Yes (it *is* the position) | Only under the §4.1 trigger ("early users dominated by locked-down corporate environments") | Partially — §3.5 names Tauri as the pairing "if you choose Rust in §2, or if binary size and installation friction turn out to dominate user feedback"; the latter is still an open empirical question (R-03) | Not addressed by any repo analysis |

---

## 5. What evidence would change the answer

Ordered roughly by how cheaply each can be obtained. Sources are repo documents; none of these are speculations.

1. **The clean-machine endpoint test fails for the PyInstaller bundle.** The one remaining R-03 line: "Run a real clean-machine or VM test for endpoint-security behaviour before closing this line" (ADR-001 §6) — now the TOOL-INS-120 release gate (ADR-001 §5 ADR-007 entry). A failure here is exactly ADR-001 §4.1's trigger: "If early users are dominated by locked-down corporate environments → distribution friction outweighs ecosystem reuse, and Rust + Tauri becomes the better pairing."
2. **A Tauri PoC passes the spike-02 criterion** (the checklist, plus measured install size, cold start, no-admin install, and per-edit latency). That converts the two live unknowns of option C into measurements. Failing the criterion settles the question for A at near-zero cost. See poc-plan.md.
3. **Grid-component licence terms.** If the web grid/editor components needed for UIX-150/160/170 carry licence terms that fail TOOL-LIC-050 (no components whose licence prohibits commercial use), option C's editor path changes materially. **Unverified today** — must be checked before any commitment.
4. **WebView2/WebKitGTK evidence against UIX-340.** Rendering consistency and offline behaviour of the two web engines on the two mandated platforms is currently unmeasured (ADR-001 §3.2 notes the variance; nobody has tested it here).
5. **Qualification pressure rises.** ADR-001 §0's argument — determinism, auditability, and reproducibility of the toolchain "disfavour a dynamic runtime with a large transitive dependency tree" — strengthens for a compiled core if Tier-2/Tier-3 qualification work (ADR-001 §1.3) is pulled forward. Note this argues for *a* compiled core; ADR-001 §4.1's corresponding bullet names the **C++** analyzer, not Rust, as the case that gets pulled forward when CFG needs arrive early.
6. **CFG needs arrive early** (PAR-070 or UIX-270 pursued, e.g. unique-cause MC/DC via source transformation per COV-090). Per ADR-001 §4.1 this moves the C++ analyzer from "later" to "now" — it does not by itself argue for Rust, and option C is unaffected (the analyzer swap crosses PAR-100 either way).
7. **A maintainer-pool reality check.** If actual contributor engagement lands mostly web-side, the R-06 calculus shifts toward larger front-end pools (ADR-001 §6 mitigation; §3.2 pool rows) — evidence that does not exist yet.

---

## 6. RECOMMENDATION (a recommendation only — not a decision, not adopted)

**Recommend option A (stay Python + PySide6) for the core without qualification, and option A for the GUI by default — while authorizing one time-boxed, ≤3-person-day option-C PoC (poc-plan.md) before WP-GUI-01 begins.**

Reasoning, each step traceable to cited evidence:

1. **The core stays Python on today's evidence.** Spike-01 held at 7.5× its size floor with zero parse errors (ADR-001 §2.5); the ecosystem-reuse and contributor-pool arguments (ADR-001 §2.2) dominate; R-06's mitigation is contributor availability (ADR-001 §6); and the PAR-100 seam already preserves the future Rust/C++ swap at lower cost than a premature rewrite (PLAN-001 §4.3 row 1). Nothing in this memo's evidence disturbs ADR-001 §2.4.
2. **The GUI stays Qt *by default* because its evidence is the only measured evidence.** Spike-02's PASS is Qt-specific, and PLAN-001 §4.4's rule is that reopening requires refreshed evidence. WP-GUI-11 (8 pw, the largest package, the named schedule driver — PLAN-001 §4.4, §8 R-3) starts from two carried findings on this stack and from nothing on any other.
3. **But the PoC should be run now, because this is the zero-sunk-cost window.** All 22 GUI WPs are Planned; none is Implemented (EXEC-PLAN-001 §2). §4.3 row 2 says a GUI technology change is fully recoverable — but only while "an L5 rewrite" is the *entirety* of the lost work. Three person-days converts the option-C unknowns (web nested editor at the spike-02 bar; Tauri install metrics) into data, at a moment when a negative result discards nothing. This mirrors ADR-001 §6's own R-03 mitigation posture: "retain Rust as a fallback while the codebase is small."
4. **The core does *not* move to Rust as part of any of this.** Option B/D's 30 pw floor (plus the conservative 13 pw assumption recorded in §3-B), ecosystem inversion, smallest core contributor pool, and "Months vs Weeks" prototype time (ADR-001 §2.2) are all costs paid with no offsetting measured benefit in the repo evidence.
5. **The genuine open trigger is R-03's remaining policy risk.** If the TOOL-INS-120 clean-machine endpoint test fails for the PyInstaller artifact, §4.1's locked-down-environment trigger fires, and the PoC already done becomes the decision evidence for the GUI half of a move. That is the only path by which this memo's answer changes — and it is an evidence path, not a decision made here.

This recommendation does **not** reopen or amend ADR-001, does not change any decision state, and is not adopted. If the owner accepts it, the natural instruments are: authorize the PoC (poc-plan.md), and let the PoC's result plus the TOOL-INS-120 clean-machine run feed whatever ADR the owner chooses to write — per ADR-001 §7, a GUI-technology reversal "should receive their own ADR."

---

## 7. ESCALATE

Recorded per the task brief ("If you hit anything that needs an owner choice, write 'ESCALATE: <question> — options' in memo.md and continue") and EXEC-PLAN-001 §5.6:

1. **ESCALATE: authorize and provision the ≤3-person-day Tauri PoC?** — options: (a) authorize poc-plan.md as written; (b) authorize with the S6-IPC-latency variant dropped (pure front-end PoC only); (c) do not run it, stay on option A without further evidence. Blocked-by in practice: this machine has **no MSVC linker / Windows SDK** (§8) and a network fetch for crates/npm packages would be needed — both are environment decisions, and the hard rules for this run prohibit network fetches and toolchain installs.
2. **ESCALATE: D-01 / ADR-005 licence posture (already pending, not new).** It interacts with every option: PySide6's LGPL obligations and the SBOM work they add (ADR-001 §3.4) bear on option A; grid-component licensing bears on option C; LIC-010 must be reconciled with the repository licence regardless (EXEC-PLAN-001 §6.1 D-01; PLAN-001 §8 R-8). This memo takes no position.
3. **ESCALATE: ADR-007 remains open in every option** — the per-platform installer/signing mechanism and the clean-machine acceptance evidence are owner-gated (ADR-001 §5 ADR-007 entry; EXEC-PLAN-001 §6.1 "Other open gates"). A stack move does not close it; it only changes what the ADR must evaluate.
4. **ESCALATE: Linux-side evidence is gated on D-03 (platform order).** UIX-340 requires Linux + Windows, but which platform leads is a pending owner decision (EXEC-PLAN-001 §6.1 D-03; D-03 "Watch: WP-GUI-01"). The PoC plan therefore treats the Linux/WebKitGTK leg as optional and does not rank platforms.

---

## 8. PoC execution status — BLOCKED (toolchain)

The task brief permits an optional `poc/` build "only if the Rust toolchain and npm are already installed and need no network." Findings from the probes run for this memo (2026-11-17, this machine):

**BLOCKED: MSVC C++ build toolchain (link.exe + Windows SDK import libraries).** Detail, so the next run does not re-derive it:

- Present: `cargo 1.92.0` / `rustc 1.92.0` (stable-x86_64-pc-windows-msvc) at `C:\Users\sudul\.cargo\bin`; `node v24.22.1`, `npm 11.19.1`, `pnpm`; Tauri crates cached in the cargo registry (`tauri-2.9.5`, `tauri-build-2.5.3`, `tauri-codegen-2.5.2`, `tauri-macros-2.5.2`, `tauri-plugin-2.5.2`, plus serde/serde_json) — evidence of a prior Tauri setup on this machine.
- Missing: `link.exe` with the MSVC libraries. `C:\Program Files\Microsoft Visual Studio\2022` exists but is an **empty directory**; `vswhere.exe` reports **no installed VS products**; no Windows Kits SDK directory; **no `kernel32.lib` anywhere** under Program Files. A trivial `fn main(){}` binary fails: `error: linking with 'link.exe' failed` → "you may need to install Visual Studio build tools with the 'C++ build tools' workload". `-C link-self-contained=yes` is unsupported on the `x86_64-pc-windows-msvc` target; no GNU toolchain is installed (`rustup toolchain list` shows only stable-msvc). `tauri-cli` is not installed.
- Therefore no Rust binary — and no Tauri PoC — can be linked on this machine, and the "need no network" condition cannot be met either (crates/npm fetches would be required for the remaining closure). Per the task brief ("If a toolchain is missing, write 'BLOCKED: <tool>' in memo.md and stop this step"), **the PoC build was not started**; no network fetch was attempted (hard rule); poc-plan.md documents the procedure for a provisioned machine.

---

## 9. Assumptions recorded (conservative readings, per the task brief)

1. **"need no network"** was read as *the PoC build must require no network*; since crates/npm closure would need fetching (and linking is blocked regardless), the optional PoC was skipped rather than attempted.
2. **PLAN-001 §4.3's 30 pw is treated as a floor** for options B/D: the table names `WP-ANA-01/02/03/05/06`, `WP-CORE-03`, `WP-PKG-01`; the four other landed Python packages (`WP-CORE-01/PRJ-01/ING-01/ANA-04`, 13 pw combined, efforts per PLAN-001 §5.3) are conservatively assumed to need re-implementation in a full core move. §4.3 itself does not say this — recorded as an assumption, not a citation.
3. **ADR-001 §3.2's "~10 MB" Tauri figure** is the repo's own planning number, not a local measurement; the memo never treats it as measured.
4. **CXX-Qt maturity, AG Grid/TanStack licence terms, WebView2 archivability (INS-040) behaviour, and Tauri's satisfaction of UIX-030** are all marked unverified; none is asserted from repo evidence, and no external sources were fetched for this memo.
5. **WP-PKG-01 scope growth** under option C (second artifact to package) is an assumption, not a documented consequence.
6. R-02's post-reopen level for options B/C ("roughly its pre-spike level") is **judgement**, not measurement.

---

## 10. Sources

Every claim above cites one of:

- `ADR-001-architecture-decisions.md` §0, §1.3, §2.1, §2.2, §2.3.1, §2.4, §2.5, §3.1, §3.2, §3.3, §3.4, §3.5, §3.6, §4, §4.1, §5 (ADR-007 entry), §6 (R-01..R-10), §7
- `ADR-006-fork-or-build-fresh.md` §4.2, §7, §9.1
- `SRS-001-requirements.md` §4 (PAR-100/110/070), §17.1–17.8 (UIX-010..400), §20 (NFR-050/060/100/110/180), §21 (LIC-010..070), §22 (SEC-010..040), §24 (INS-010..050)
- `PLAN-001-specification-analysis-and-work-breakdown.md` §4.3 (reversal impact), §4.4 (spike criteria; WP-GUI-11 schedule-driver statement), §5.3 (critical path; landed-WP efforts), §5.5 (WP-GUI-01..22, WP-PKG-01 register), §8 (R-3, R-8)
- `design/SDD-001-architecture.md` §4.4, §8, §9
- `design/SDD-002-interfaces.md` §3, §9 (S6 transport, framing, cancellation, contract points)
- `spikes/spike-02-nested-editor/RESULTS.md` (checklist, findings, latency, limits), `spikes/spike-02-nested-editor/struct_def.md`
- `spikes/spike-03-packaging/RESULTS.md` (measurements, admin check, deviations, honest limits)
- `EXEC-PLAN-001-unified-execution-plan.md` §1, §2 (state snapshot: 9 implemented WPs; all GUI WPs Planned), §5.4–5.6 (gates, branches, escalation incl. §5.6 item 4 permitting this memo), §6.1 (D-01..D-04; open ADRs)
- Toolchain probes executed for this memo (§8) — machine-local, reproducible by re-running the listed commands.

*End of memo. Draft — not adopted.*
