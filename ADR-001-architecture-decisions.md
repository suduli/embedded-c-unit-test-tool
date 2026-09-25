# ADR-001 — Core Language, Front-End Technology, and Qualification Scope

**Document ID:** ADR-001
**Status:** **Accepted, 2026-09-19** — validation spikes (§4.2) complete, all three recommendations in §4 stand at high confidence, and ADR-006 (§5) — the one remaining condition — resolved as "build fresh," discharging it without overturning any recommendation here
**Relates to:** SRS-001 open questions 1, 4, 5

---

<!-- nav:start -->
**Related documents** — [SRS-001](SRS-001-requirements.md) · **ADR-001** *(you are here)* · [ADR-006](ADR-006-fork-or-build-fresh.md) · [SDD-001](design/SDD-001-architecture.md) · [SDD-002](design/SDD-002-interfaces.md) · [SDD-003](design/SDD-003-data-model.md) · [SDD-004](design/SDD-004-traceability-architecture.md) · [SDD-005](design/SDD-005-external-integration.md) · [Register](design/trace/design-elements.yaml) · [Design index](design/README.md)

Architecture diagrams: [specifications](design/diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 0. Why these three are one decision

They are not independent:

- **Language constrains GUI.** A Python core pairs naturally with Qt (in-process, no IPC). A Rust core pairs naturally with Tauri. A C++ core pairs with Qt but at high build cost. Choosing the GUI first and the language second usually produces an awkward IPC layer that exists only because the two halves were chosen separately.
- **Qualification scope constrains language.** If v1.0 must produce certification evidence, determinism, auditability, and long-term reproducibility of the toolchain itself become hard requirements — which disfavours a dynamic runtime with a large transitive dependency tree.
- **Qualification scope constrains what v1.0 *is*.** If qualification is deferred, v1.0's target user changes from "verification engineer producing ASIL-D evidence" to "embedded developer doing TDD," and the front-end priorities shift accordingly.

So: decide qualification scope first, because it defines the product. Then language. Then GUI.

---

## 1. Decision C — Qualification scope (decide this first)

### 1.1 The uncomfortable fact

**You cannot win on qualification cost.** QA Systems states its Cantata certification kits are free of charge, and Cantata is independently certified by SGS-TÜV SAAR up to the highest integrity levels with a TCL1 classification under ISO 26262. LDRA ships a Tool Qualification Support Pack. VectorCAST ships DO-178C/DO-330 packages.

An open-source project cannot match independent third-party certification without either substantial funding for a certification body engagement, or a foundation-level governance structure. Any roadmap that treats "get certified" as a v1.0 milestone is planning to fail.

### 1.2 The reframe that works

The goal is not **"be qualified."** It is **"be qualifiable."**

Under ISO 26262-8, a test tool typically lands at TCL2 or TCL3 (it can fail to detect errors), so *the user* must qualify it for *their* project — by validation, proof in use, or development according to a safety standard. A commercial vendor's kit is a head start on that work, not a substitute for it. An open-source tool that gives users everything they need to perform validation themselves occupies a legitimate and defensible position — and has one advantage no commercial tool can match: **the user can inspect the source and the entire development history.**

### 1.3 Three tiers of qualification work

| Tier | Content | Cost | Verdict |
|---|---|---|---|
| **1 — Discipline** | Unique release identification and archival; reproducible builds; documented known-error list per release; Tool Operational Requirements document; the tool's own validation test suite, user-executable | Low — this is just good engineering | **Do in v1.0.** Retrofitting it later is far more expensive than doing it from the start. |
| **2 — Documentation** | Tool classification analysis (TI/TD → TCL); mapping of tool capabilities to the verification objectives of each standard; qualification artifact templates for users | Moderate — weeks of specialist writing | **Do in v1.1**, once the feature set has stopped moving. |
| **3 — Certification** | Independent assessment; full validation evidence package; per-standard certification kits | High — funded engagement with a certification body | **Not a shipped artifact.** Revisit only if the project acquires institutional backing. |

### 1.4 Why Tier 3 in v1.0 is actively harmful

Qualification evidence is only meaningful for a **stable** tool. Every requirement change invalidates part of the evidence. Qualifying a v1.0 that will change substantially over the following year means paying for the work twice. This is the standard reason commercial vendors qualify on long release cycles.

### 1.5 What this means for the product

v1.0's primary user is **not** the ASIL-D verification engineer. It is:

- Embedded teams doing host-side TDD who currently have no tool
- Teams under MISRA/quality mandates without full certification obligations
- Safety teams using it as a **supplementary** tool alongside a qualified one — for exploratory testing, coverage gap-finding, and developer-level testing before formal verification
- Cost-sensitive projects at lower integrity levels (ASIL A/B, DAL C/D, IEC 62304 Class A/B) where self-qualification is proportionate

That is a large market and it does not require beating Cantata at certification.

### 1.6 SRS impact

- QUA-010 through QUA-060: keep in v1.0, re-phase to **P1/P2** where they are discipline rather than documentation. Reproducibility and version identification must be designed in from the first commit.
- QUA-070, QUA-080, QUA-100: re-phase to **P4 / v1.1**.
- QUA-090 (do not overclaim) becomes the most important requirement in the section, not a footnote.
- Add: a requirement that the project publish its own development process, CI results, and defect history publicly — this is the open-source substitute for a certification kit, and it is free.

---

## 2. Decision A — Core implementation language

### 2.1 The pivotal technical question

**Does the tool need access to the Clang control flow graph?**

This single question decides the language, and it deserves a direct answer before anything else:

- **libclang** — the stable C API, with official Python bindings — exposes the AST: function signatures, parameter and return types, user-defined types, global variable references, and enough information to build a call graph. It does **not** expose the CFG.
- **LibTooling** — the C++-only API — exposes the CFG, full AST matchers, and complete type information.

Now check what the SRS actually needs:

| Requirement | Needs CFG? | Notes |
|---|---|---|
| PAR-030/040/050/060 (signatures, types, globals, call graph) | **No** | libclang is sufficient |
| PAR-070 (control flow graph) | **Yes** | But: what consumes it? |
| PAR-120 (cyclomatic complexity) | No | `lizard` computes this without a CFG |
| COV-010–080 (all coverage incl. MC/DC) | **No** | gcov/llvm-cov instrument at compile time; the tool consumes their JSON output |
| ATG-020 (symbolic execution) | **No** | KLEE operates on LLVM bitcode and does its own analysis |
| STB-090 (call wrapping) | Probably not | Achievable via linker `--wrap`, as cmocka does |
| UIX-270 (graphical control flow view) | **Yes** | But this is a *(S, P3)* nice-to-have |

**Conclusion: the CFG is needed only for PAR-070 and the optional flow-graph view.** Coverage comes from the compiler. Test generation comes from KLEE. Complexity comes from lizard. The deep-analysis case for C++ is much weaker than it first appears.

This means **Python is viable**, and PAR-100 — which already mandates a JSON model as the sole interface between parsing and generation — was written to permit swapping in a C++ analyzer later without disturbing anything downstream.

### 2.2 Comparison

| | **Python** | **Rust** | **C++** |
|---|---|---|---|
| libclang access | Official bindings, AST only | `clang`/`clang-sys` crates, AST only | Full LibTooling incl. CFG |
| Ecosystem reuse | **Enormous** — gcovr, lizard, StrictDoc, pyOCD, Twister are all Python and importable as libraries | Must shell out to all of the above | Must shell out |
| Prior art to read | Zephyr Twister (the recommended architectural model) is Python | — | UTBotCpp is C++ |
| Contributor pool in embedded | **Largest** — west, Twister, pyOCD, build scripts are all Python; embedded engineers already write it | Smallest — few embedded C engineers write Rust | Moderate; but LLVM-linking expertise is rare |
| Distribution | **Weakest** — needs a runtime, or large PyInstaller bundles with slow startup and occasional AV false positives | **Strongest** — single static binary | Weak — must match a pinned LLVM version |
| Performance at 500 TUs | Adequate; parsing happens inside libclang (C++), so overhead is marshalling, parallelizable with multiprocessing | Excellent | Excellent |
| Determinism (NFR-060) | Achievable with care — dict/set iteration discipline required | Excellent by default | Good |
| Build complexity | Trivial | Low | **High** — linking LLVM is notoriously painful and version-pinned |
| Time to first working prototype | **Weeks** | Months | Months |

### 2.3 The distribution problem is the real Python objection

Everything else favours Python. The counter-argument is that UIX-040 requires the application to be installable by a user with no development environment beyond a C toolchain — and shipping a Python application to a conservative corporate embedded environment is genuinely harder than shipping one binary.

Mitigations, in order of preference: bundle with PyInstaller or Nuitka into a signed installer per platform; ship the container image (NFR/CIC-040) as the CI path; document a `pipx` install for developer users. None is as clean as a Rust binary, but all are proven — gcovr, Twister, and pyOCD all ship this way to exactly this audience.

#### 2.3.1 Validation update (`WP-SPIKE-03`, run after this analysis)

A PyInstaller bundle of PySide6 + libclang together built cleanly on the first attempt — libclang's ctypes-loaded shared library was collected via a plain `binaries=[...]` spec entry, no `Config.set_library_file()` fallback needed — producing a 194.2 MB onedir distribution with a ~162ms in-process cold start, and no administrative privileges implicated anywhere in the build or run path. This was measured on the development machine that built it, not a clean one, so it cannot speak to Defender/SmartScreen behaviour on a genuinely clean install — that remains a manual follow-up, not something an agentic run can close. Full results: [`spikes/spike-03-packaging/RESULTS.md`](spikes/spike-03-packaging/RESULTS.md).

**Verdict on R-03 (§6):** partially mitigated. The mechanical packaging risk — does PyInstaller even work with this exact dependency set — is resolved. The policy risk — does a locked-down corporate endpoint accept an unsigned bundle this size — is untested and needs a real clean-machine or VM run before that line of the risk register is marked closed.

### 2.4 Recommendation

**Python core, with a deliberate architectural seam for a future C++ analyzer.**

Concretely:
1. Build the parsing layer against libclang's Python bindings, emitting the JSON model required by PAR-100.
2. **Treat that JSON model as an inviolable interface.** Nothing downstream may call libclang directly.
3. If and when CFG access proves necessary (PAR-070, UIX-270), write one focused C++ LibTooling binary that emits the same JSON model, and swap it in. Nothing else changes.

This is UTBotCpp's client-server insight — isolate the toolchain-version-sensitive component — applied without inheriting its Ubuntu-resident server (Docker is merely how UTBotCpp makes that Ubuntu assumption portable to other hosts, not a separate requirement of its own — see [ADR-006](ADR-006-fork-or-build-fresh.md) §3.1).

**Choose Rust instead if** distribution to locked-down corporate environments is the single dominant constraint and you are willing to accept a much smaller contributor pool and reimplement what the Python ecosystem gives free.

**Choose C++ only if** you decide to fork UTBotCpp, in which case the decision is made for you.

### 2.5 Validation update (`WP-SPIKE-01`, run after this analysis)

§2.1's premise held under real load. Run against 151,558 lines of real, unmodified vendor embedded C (STM32F4 HAL driver + CMSIS device headers — 7.5× the 20,000-line floor this spike set for itself), libclang's AST alone extracted 1,810 functions, 506 types, 16 globals and 1,502 direct calls with **zero parse errors**. 32 of 1,534 call sites (2.1%) are function-pointer dispatches — IRQ/DMA-completion callback tables, a single well-understood pattern — that AST-only extraction cannot resolve to a concrete callee. Every one was recorded as an explicit, located, unresolved edge rather than silently dropped or misattributed, and none of them needed statement-level control-flow reasoning to explain: resolving them is a points-to/symbol-table problem, not a CFG one. Full results: [`spikes/spike-01-cfg-sufficiency/RESULTS.md`](spikes/spike-01-cfg-sufficiency/RESULTS.md).

**Verdict on R-01 (§6):** the risk does not materialize. The recommended path — libclang now, PAR-100's JSON seam held absolutely, a C++ analyzer only if a CFG-dependent requirement (PAR-070, UIX-270) is actually pursued — stands without the "contingent on §2.1 holding" qualifier §4 originally carried. The recommended next step is a scoped extension to `WP-ANA-03` for function-pointer resolution, not a reopening of this language question.

---

## 3. Decision B — Standalone GUI technology

### 3.1 The two widgets that decide this

Most of the UI is unremarkable. Two components are not, and they should drive the choice:

1. **UIX-110/120 — hierarchical tree with aggregated status.** Project → environment → unit → function → test case, each node showing rolled-up pass/fail counts, coverage percentage, and staleness. Must stay responsive at 10,000 test cases (NFR-050), which requires virtualized rendering and lazy expansion.
2. **UIX-150/160/170 — type-aware tabular test data editor.** Editable grid where struct and array parameters expand into a nested tree *within* the table, values are validated against their declared C type, and enums are presented by name. This is the hardest widget in the product and it is the one users will spend their day in — it is Tessy's Test Data Editor and VectorCAST's Test Editor.

Qt provides both nearly free (`QTreeView` + `QAbstractItemModel` handles nested-tree-in-table natively, with virtualization built in). Web technology requires assembling them from AG Grid or TanStack Table plus custom work.

### 3.2 Comparison

| | **Qt / PySide6** | **Tauri** | **Electron** | **Local server + browser** |
|---|---|---|---|---|
| Pairs with | Python, C++ | Rust | Any | Any |
| Tree + nested editable grid | **Native, virtualized, free** | Build on AG Grid/TanStack | Same as Tauri | Same as Tauri |
| Binary size | ~100–200 MB bundled | **~10 MB** | ~150 MB+ | Engine only |
| Rendering consistency | **Uniform** | Varies — WebView2 on Windows vs. WebKitGTK on Linux | **Uniform** (bundled Chromium) | Varies by user's browser |
| License | **LGPL** (PySide6) — dynamic linking required | MIT/Apache-2.0 | MIT | N/A |
| Native file dialogs, menus | Yes | Yes | Yes | **No** |
| Debugger integration (UIX-230) | Straightforward | Workable | Workable | **Awkward** |
| Code view with coverage overlay | QScintilla | Monaco | Monaco | Monaco |
| Offline / no-network (UIX-050, 350) | Trivially | Trivially | Trivially | Opens a localhost port |
| Front-end contributor pool | Moderate | **Large** (web devs) | **Large** | Large |
| Feels like a product to a conservative embedded engineer | **Yes** | Yes | Yes | **No** |

### 3.3 The localhost objection

"Serve a web UI on localhost" is the cheapest option and it is tempting, especially since it also delivers the deferred team dashboard (UIX-400) for free. Reject it as the *primary* interface for two reasons:

1. **It does not feel like a product.** "Run the tool, then open your browser to a port" is a developer-tool interaction. Your users are buying a replacement for a polished commercial desktop application.
2. **An open localhost port is a security-policy problem in exactly your target market.** Defence, aerospace, and automotive environments frequently run host-based firewalls and endpoint monitoring that flag or block listening sockets. This is a support burden you do not want on the critical path of every user's first experience.

Both objections disappear if the browser UI is an *additional* interface for team/CI viewing — which is precisely what UIX-400 already deferred it to.

### 3.4 The Qt licensing question, answered plainly

PySide6 is LGPL. LGPL permits use in a permissively-licensed application provided Qt is **dynamically linked** and the user retains the ability to replace the Qt libraries. This is compatible with LIC-010 and LIC-020 — but it must be handled deliberately:

- Dynamically link Qt; never statically link it
- Record Qt and PySide6 in the SBOM (LIC-030) with license text
- Verify that the chosen bundler (PyInstaller/Nuitka) preserves dynamic linking and library replaceability
- Note that **PyQt** is GPL/commercial and is **not** suitable — use PySide6, which is the Qt Company's own LGPL binding

This is a documentation obligation, not a blocker. But it is the one place where this recommendation carries genuine legal homework, and it should be reviewed by counsel before release rather than after.

### 3.5 Recommendation

**PySide6 (Qt) if the core is Python — which is the recommendation in §2.4.**

Rationale, in order of weight: the two hardest widgets come free and virtualized; in-process with a Python core eliminates an entire IPC layer and its failure modes; the result looks and behaves like the commercial tools your users already know; and Qt's multi-decade stability suits a tool whose users may need to reproduce a build a decade from now.

**Choose Tauri if** you choose Rust in §2, or if binary size and installation friction turn out to dominate user feedback.

**Choose Electron only if** front-end contributor availability becomes the binding constraint — it is the least defensible technically but has the largest talent pool and VS Code proves the model works for this exact class of tool.

### 3.6 Validation update (`WP-SPIKE-02`, run after this analysis)

§3.1's hardest widget was prototyped and held up. A 4-deep nested struct — reaching through a union, a function-pointer member, and a fixed array, all three siblings at one level so none could mask a bug in another — was fully editable via `QAbstractItemModel` plus per-kind `QStyledItemDelegate`s: enum and function-pointer fields render by name, never by raw value; an out-of-range edit is rejected without corrupting the displayed value; array elements are independently addressable. Cold start measured at 242ms. Two findings are worth folding directly into `WP-GUI-11`'s own design rather than rediscovering them mid-implementation: arrays materialize as an extra UI tree row beyond what the schema's type-depth count suggests, and range enforcement has to live in the model's `validate()`, not the widget's `QValidator` (which only blocks keystrokes that are unambiguously invalid, not ones merely out of range — `"999"` against a 0–255 field is treated as `Intermediate`, not `Invalid`). Full results: [`spikes/spike-02-nested-editor/RESULTS.md`](spikes/spike-02-nested-editor/RESULTS.md).

**Verdict on R-02 (§6):** substantially mitigated, not eliminated — this exercised one struct shape at a small scale, not the performance envelope at realistic data volumes (RESULTS.md says so explicitly), and undo/redo was out of scope. §3.5 holds for the editor's *shape*; `WP-GUI-11` still owns proving it at scale.

---

## 4. Recommended combined position

| Decision | Recommendation | Confidence |
|---|---|---|
| **Qualification scope** | Tier 1 (discipline) in v1.0; Tier 2 (documentation) in v1.1; Tier 3 (certification) not a shipped artifact. Target "qualifiable," not "qualified." | **High** — the cost argument against Cantata's free kit is decisive |
| **Core language** | Python, with PAR-100's JSON model held as an inviolable seam permitting a later C++ LibTooling analyzer | **High** — §2.1's CFG-sufficiency premise confirmed against 151k lines of real vendor code (`WP-SPIKE-01`, §2.5), and ADR-006 (accepted: build fresh, §5) confirms this is not overturned |
| **GUI** | PySide6 (Qt), standalone desktop, dynamically linked, LGPL documented in SBOM | **High** — the hardest widget (the nested type-aware editor) was prototyped and held up (`WP-SPIKE-02`, §3.6), and downstream of the now-accepted language decision |

### 4.1 What would change these recommendations

- **If you decide to fork UTBotCpp** → core becomes C++, GUI likely Qt, and the whole analysis reorders.
- **If the CFG turns out to be needed early** (e.g. you pursue unique-cause MC/DC via source transformation, per COV-090) → the C++ analyzer moves from "later" to "now," and a pure-C++ core becomes more attractive.
- **If a certification body engagement becomes fundable** → Tier 3 returns to the roadmap and language determinism/auditability arguments strengthen considerably.
- **If early users are dominated by locked-down corporate environments** → distribution friction outweighs ecosystem reuse, and Rust + Tauri becomes the better pairing.

### 4.2 Suggested validation before committing

All three spikes below (`WP-SPIKE-01/02/03`) have run. Each is summarized where it bears on the decision above (§2.5, §3.6, §2.3.1) and reported in full under [`spikes/`](spikes/); none is a formal ADR-006 evaluation (§5).

1. ~~**Spike the CFG question.**~~ **Done — held.** See §2.5. [`spikes/spike-01-cfg-sufficiency/RESULTS.md`](spikes/spike-01-cfg-sufficiency/RESULTS.md)
2. ~~**Spike the hard widget.**~~ **Done — held.** See §3.6. [`spikes/spike-02-nested-editor/RESULTS.md`](spikes/spike-02-nested-editor/RESULTS.md)
3. ~~**Spike distribution.**~~ **Done — mechanically sound; clean-machine AV/SmartScreen behaviour still untested.** See §2.3.1. [`spikes/spike-03-packaging/RESULTS.md`](spikes/spike-03-packaging/RESULTS.md)

Each spike was days, not weeks, and each directly tested the assumption its decision rests on — exactly as intended. They deliberately did not settle ADR-006 (§5), which needed a direct evaluation of UTBotCpp itself rather than a viability check on the from-scratch alternative — that evaluation has since been done and accepted.

---

## 5. Decisions this document does not make

ADR-001 deliberately covers three coupled decisions. The following remain open and should each receive their own ADR, because bundling decisions obscures which rationale supports which choice.

### ADR-002 — Project and test data format
**Question:** YAML, TOML, JSON, or a purpose-built DSL for project files, test scope definitions, and data-driven test cases.
**Why it matters:** PRJ-010 through PRJ-080 impose demanding constraints — human-readable, diff-stable, deterministic ordering, localized merge conflicts, explicit schema versioning. YAML satisfies readability but has well-known ambiguity hazards (implicit typing of values like `NO`, `on`, and version strings) that are actively dangerous when the content is C values and type names. TOML is unambiguous but awkward for the deeply nested structures required by UIX-160. JSON is unambiguous and machine-friendly but poor for hand editing and has no comment support, which conflicts with users annotating test rationale.
**Bearing on other decisions:** none significant — this can be decided independently and late, provided the model layer is format-agnostic from the start.

### ADR-003 — Symbolic execution engine
**Question:** Adopt KLEE, adopt CBMC, support both, or defer automatic test generation entirely.
**Why it matters:** SRS ATG-020 and ATG-030 are *(S/C, P3)*. KLEE's toolchain-version sensitivity is precisely the problem UTBotCpp solved with a client-server split; inheriting KLEE means inheriting that problem. CBMC has lighter integration cost but a different capability profile.
**Bearing on other decisions:** significant. If KLEE is adopted, the isolation strategy chosen in §2.4 must accommodate a second toolchain-pinned component, and the case for the client-server architecture strengthens.

### ADR-004 — Coverage backend strategy
**Question:** Whether to support the GCC and Clang coverage paths equally, or designate GCC as primary.
**Why it matters:** the two paths differ materially. GCC's `-fcondition-coverage` with `gcov --conditions --json-format` is consumable end to end today, and gcovr supports it. Clang's `-fcoverage-mcdc` is ignored by current gcovr, so supporting it means parsing llvm-cov output directly. Supporting both equally roughly doubles the coverage layer's surface.
**Bearing on other decisions:** moderate. It determines whether TCH-060 (declaring achievable metrics per compiler) is a small table or a substantial compatibility matrix.

### ADR-005 — License selection
**Question:** Apache-2.0 or MIT.
**Why it matters:** LIC-010 requires a permissive license but does not name one, and the difference is not cosmetic in this domain. **Apache-2.0 includes an express patent grant and a patent retaliation clause; MIT does not.** For a tool used in automotive, avionics, and medical device development — patent-dense industries where corporate legal review gates adoption — the explicit patent grant materially reduces the friction of that review. Apache-2.0 also aligns with LLVM, cmocka, and StrictDoc. MIT's advantage is brevity and Unity/CMock alignment.
**Recommendation, stated here because it is low-controversy:** Apache-2.0.
**Bearing on other decisions:** interacts with LIC-020 and the Qt/LGPL analysis in §3.4; Apache-2.0 and LGPL-dynamic-linking coexist without difficulty.

### ADR-006 — Fork UTBotCpp or build fresh
**Question:** whether to fork UnitTestBot/UTBotCpp as a foundation.
**Why it matters:** it is the closest existing open-source analog and it solves real problems — KLEE integration, stub synthesis with symbolic return values, automatic project configuration. But it is host-Linux-oriented, C++-implemented, and generates GoogleTest output — all three of which conflict with the recommendations in §2 and §3 and with SRS HAR-060.
**Bearing on other decisions:** decisive. A fork settles the language question as C++ and reopens the GUI and framework decisions. This should be resolved before ADR-001's recommendations are accepted, not after.
**Resolved — Accepted, 2026-09-19: build fresh, do not fork.** Recorded in full in [`ADR-006-fork-or-build-fresh.md`](ADR-006-fork-or-build-fresh.md), which is a direct evaluation of `UnitTestBot/UTBotCpp` against this specification (GitHub API, wiki, and repository, independently verified) — not the viability check the §4.2 spikes ran. Headline finding: UTBotCpp's Apache-2.0 license removes what usually kills a fork decision, but the fork collides with this specification on eight points — no target execution at all, line-coverage-only, an LLVM-14 pin four majors behind SDD-005's required floor on the API SDD-005 already rejects as unstable, an Ubuntu-resident server, C++ GoogleTest output that violates `TOOL-HAR-060`, a test-generation support matrix that excludes `void*`/variadics/external-state — exactly what embedded HAL code is made of — no standalone GUI, and a two-year-dormant upstream with no one to share the maintenance burden. Its one real asset, working KLEE-based test generation, serves `ATG-020`/`030`, which this specification files at *(S/C, P3)* — the lowest-priority band in the document. Four design ideas are harvested without forking (§5 of that document): the client-server split (already credited above), the `KLEE_MODE` symbolic-stub duality, `link_commands.json`'s link-closure insight, and the `c-syntax` support matrix as a ready-made risk list — all feeding `WP-GEN-05`/`06`/`07` and ADR-003. This discharges §4's outstanding condition without changing any recommendation in this document.

### ADR-007 — Distribution and packaging
**Question:** the concrete packaging mechanism per platform, given INS-010 through INS-050.
**Why it matters:** offline installation, side-by-side versions, no administrative privileges, and decade-scale archivability are demanding in combination. This is the primary risk attached to the Python recommendation in §2.4; the §4.2 distribution spike (`WP-SPIKE-03`, §2.3.1) has now run and cleared the mechanical question, so this ADR can proceed — it should focus on the per-platform signing/installer mechanism and the still-open clean-machine endpoint-security question rather than re-litigating whether PyInstaller works at all.

---

## 6. Risk register

| ID | Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|---|
| R-01 | libclang's AST-only API proves insufficient, forcing a C++ analyzer earlier than planned | Medium — schedule, not architecture, provided the PAR-100 seam is respected | **Low** (was Medium — `WP-SPIKE-01` ran clean at 7.5× the size floor, §2.5) | Hold the JSON model boundary absolutely; extend `WP-ANA-03` for function-pointer resolution rather than reopening the language question |
| R-02 | The type-aware nested test data editor proves substantially harder than estimated | **High** — it is the widget users live in; a poor one undermines the whole product | **Low** (was Medium — `WP-SPIKE-02` ran and held, §3.6) | Carry both `WP-SPIKE-02` findings (array row-depth, validator-vs-`validate()` split) directly into `WP-GUI-11`'s design; performance at realistic data volumes is still untested |
| R-03 | Python distribution to locked-down corporate environments proves unacceptable | High — excludes the target market | **Medium, narrowed to policy risk only** (was Medium overall — `WP-SPIKE-03` confirmed the packaging mechanics work, §2.3.1; clean-machine AV/SmartScreen behaviour is the untested remainder) | Run a real clean-machine or VM test for endpoint-security behaviour before closing this line; retain Rust as a fallback while the codebase is small |
| R-04 | MC/DC support proves inadequate for users' certification authorities (masking vs. unique-cause) | High — removes the safety-critical use case | Medium | Document the distinction prominently per COV-060; validate with a real assessor before committing to COV-090 |
| R-05 | Compiler and target support breadth becomes an unbounded maintenance burden | High — this is where commercial vendors have invested decades | High | Make TCH-040/PLG-020 genuinely sufficient so support is contributed rather than centrally maintained; resist bundling configurations the project cannot test |
| R-06 | Insufficient contributors; the project becomes one person's maintenance burden | **High** — the common failure mode for tools of this ambition | High | Choose the language for contributor availability; keep extension points low-friction; ship something useful at P1 rather than architecting toward a distant v1.0 |
| R-07 | Adoption fails because migration from incumbent tools is too costly for users | High | Medium | Treat Section 23 (MIG) as adoption-critical rather than convenience; validate import fidelity against a real commercial project early |
| R-08 | AI features attract attention but produce unreviewable artifacts that damage trust in safety contexts | Medium — reputational, and hard to reverse | Medium | AIF-010/070/080/090/100 are already defensive; resist relaxing them under feature pressure |
| R-09 | KLEE's toolchain version sensitivity destabilizes the build for all users | Medium | Medium-high | Isolate it as an optional component; never place it on the critical path of a default install |
| R-10 | Qualification expectations are set higher than the project can deliver, creating liability | **High** | Medium | QUA-090 forbids overclaiming; state the position from the first public communication, not after users have assumed otherwise |

---

## 7. Note on ADR granularity

This document bundles three decisions because they are genuinely coupled and could not be analysed independently. That is an exception. Subsequent decisions should each receive a separate ADR, in the conventional form — context, decision, status, consequences — so that the rationale for any single choice can be located, reviewed, and if necessary superseded without disturbing the others.
