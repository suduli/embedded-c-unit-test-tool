# RV-01 — Stack & architecture comparison: vcast-findings evidence vs ectt baseline

**Reviewer:** RV-01 (stack & architecture), cross-review 2026-11-06.
**vcast-findings inputs:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` (§1, §2, §10, §11, §12), `vcast-findings/ARCHITECTURE.md`, `vcast-findings/VCAPPLIB.md`, `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` (intro, "What this pass establishes", recovered boundaries).
**ectt baseline:** `ADR-001-architecture-decisions.md`, `ADR-002-project-data-format.md`, `ADR-006-fork-or-build-fresh.md`, `design/SDD-001-architecture.md`, `design/SDD-003-data-model.md`, `design/SDD-005-external-integration.md`, `PLAN-001-specification-analysis-and-work-breakdown.md` §5.5, `pyproject.toml` / `src/ectt` layout.

Status note: `PRODUCT_ARCHITECTURE.md` is an original product-design proposal produced *by* the VectorCAST investigation; it is not an ectt document. Where it disagrees with accepted ectt ADRs/SDDs, that disagreement is recorded here as a finding, not as an error on either side. Line numbers refer to the files as read on 2026-11-06.

---

### F-01 — Analysis front-end default: C++ LibTooling worker vs in-process libclang (the seam already accommodates the swap)

**Class:** conflict

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §2 stack table, "Source analysis" row (line 74): "C++ worker using Clang LibTooling/AST APIs … Pin the worker to its LLVM release"; mermaid diagram line 51 (`SUP --> AST[C++ Clang analysis worker]`); line 84: "The choice of full C++ AST access is deliberate; simpler libclang interfaces may be enough for browsing but can constrain a future transformation engine"; line 86 (M0 escape hatch): "If building LibTooling creates disproportionate setup cost, evaluate libclang against the exact discovery/type/call-reference contract before selecting it as a smaller first backend."

**ectt baseline evidence:** `ADR-001-architecture-decisions.md` §2.4 (lines 143–156): Python core, libclang Python bindings, "Treat that JSON model as an inviolable interface," and item 3 authorizes exactly "a focused, isolated C++ LibTooling executable emitting the same versioned JSON model … Pin its LLVM build … verify model-equivalent fixtures before substitution (SDD-005 §5.3)". `design/SDD-005-external-integration.md` §5.3 (lines 374–394): "LibTooling in-process linkage is rejected on compatibility, not capability. … That fallback may bundle a mutually compatible, pinned LLVM/LibTooling build and emit the same versioned PAR-100 JSON model." `ADR-001` §2.5 (`WP-SPIKE-01`): libclang's AST alone extracted 1,810 functions / 1,502 direct calls from 151,558 LOC with zero parse errors. `pyproject.toml` line 13 pins `libclang>=18.1,<19`.

**Assessment:** The disagreement is over the *default*, not the architecture. ectt defaults to in-process libclang and escalates to a C++ LibTooling executable only if a CFG consumer (PAR-070/UIX-270) is actually pursued; the proposal defaults to the LibTooling worker from M0 and offers libclang as the fallback. The proposal's worker — pinned LLVM release, LLVM objects kept inside the worker, versioned JSON over stdin/stdout (§2 line 81) — is shape-for-shape the component ADR-001 §2.4 item 3 and SDD-005 §5.3 "ALLOW isolated fallback" already describe, so ADR-001's seam language fully accommodates the swap: per SDD-001 §8 (line 394), "A C++ analyzer emitting the same JSON replaces `CMP-ANA` with no downstream change." What the proposal underweights is the cost ectt already priced: ADR-006 §4.2 puts a LibTooling port at 8–15 person-weeks with **Low** confidence because LibTooling has no stable API (SDD-005 §6.2 item 3), while ectt's own spike evidence shows libclang met the PAR-030–060 extraction contract at 7.5× the size floor without needing a CFG. SDD-005 §5.3's substitution conditions (model-equivalent fixtures, recorded hashes/build flags, offline binaries, never loading against arbitrary user LLVM) would apply to the proposal's worker verbatim.

**Recommendation:** Treat this as a validated-at-M0 choice, not an ADR conflict to litigate now: ectt's recorded path (libclang first, `WP-ANA-03` extension for function-pointer resolution) is cheaper and spike-supported; if a transformation engine or CFG consumer becomes a requirement, the LibTooling worker drops into `CMP-ANA` under the existing seam without touching SDD-001's L2–L5. Any such swap must inherit SDD-005 §5.3's isolation and fixture-equivalence conditions.

---

### F-02 — Primary UI: React/TypeScript loopback web app vs PySide6 desktop with no TCP listener

**Class:** conflict

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §1 (line 7): "Build a compiler-aware test automation engine with a CLI first, then a local web interface"; §2 diagram line 46: `UI[React and TypeScript local UI] --> API[Authenticated loopback API]`; §2 stack table line 80: "React/TypeScript with source viewer and tables | Suits the user's web stack"; §8 quality requirements (line 251): "A loopback API bound to an explicit local interface with a per-session secret and origin validation."

**ectt baseline evidence:** `ADR-001-architecture-decisions.md` §3.3 (lines 195–200) rejects localhost/browser as the *primary* interface for two stated reasons: (1) "It does not feel like a product" to the conservative embedded engineer; (2) "An open localhost port is a security-policy problem in exactly your target market" — defence/aerospace/automotive firewall and endpoint-monitoring regimes. `ADR-001` §3.5 (line 210): "PySide6 (Qt) if the core is Python." `design/SDD-001-architecture.md` §4.4 (lines 234–237): "`CMP-API` … a versioned JSON protocol over stdio or a filesystem-permissioned local socket. **No TCP listener is offered** (DSN-API-030)." Incumbent evidence: `vcast-findings/ARCHITECTURE.md` line 63 — `vcastqt.exe` is a native Qt 5 desktop GUI (importing Qt5Widgets/Gui/Core plus WebEngineWidgets for an embedded web view).

**Assessment:** A genuine, decision-relevant conflict. The proposal's mitigations (loopback-only bind, per-session secret, origin validation) answer the naive-security objection but not ADR-001's two stated grounds: a listening socket remains a support-burden trigger in exactly the markets ectt targets, and the product-feel objection is untouched. The incumbent's own evidence cuts toward ectt here: VectorCAST ships a native Qt desktop GUI as its primary interface (with a web view embedded *inside* the native shell — a hybrid neither document proposes). Note the boundary difference: ectt's DSN-API-030 rule governs the *engine* API (stdio/filesystem socket only), while the proposal's loopback API is an application-layer front-end over a stdin/stdout engine — so the conflict is confined to the L5 front-end, which SDD-001 §8 (line 395) explicitly says is absorbable ("A technology change is a rewrite of L5 only") but at the cost of re-running ADR-001 §3's analysis, and PLAN-001 line 175 prices a non-Qt GUI at all 22 `WP-GUI-*` packages / 85 person-weeks.

**Recommendation:** Keep the accepted PySide6 decision for ectt. If a browser surface is ever wanted, follow ADR-001 §3.3's own carve-out (browser UI as an *additional* team/CI viewing interface, per UIX-400) rather than as the primary interface, and reuse the proposal's concrete mitigations (loopback bind, per-session secret, origin validation) in that secondary role.

---

### F-03 — System of record: SQLite metadata store + content-addressed blobs vs restricted-YAML plain-text project store + two trees

**Class:** conflict

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §2 stack table lines 78–79: "Metadata | SQLite owned by one application writer"; "Large evidence | Content-addressed files on local disk"; §7 (lines 219–223): "One application process owns SQLite writes and schema migration … The compiler/build metadata, test specification, run evidence and report projections are separate concepts even if they initially share one database." Incumbent corroboration: `vcast-findings/VCAPPLIB.md` line 9 (VcAppLib imports 18 SQLite functions) and lines 60–72 (27 recovered `CREATE TABLE` strings for `vcshell.db`: FILES/COMMANDS/COMPILATION/BUILDS); `vcast-findings/ARCHITECTURE.md` line 42–44 (all three PEs import sqlite3.dll).

**ectt baseline evidence:** `design/SDD-001-architecture.md` §2 driver table (line 51): "All state is plain text under version control | TOOL-PRJ-010, TOOL-UIX-320 | No application database. The project store is the system of record"; §3 (lines 109–111): "The project store, not the tool, is the system of record … the requirement that makes decade-scale evidence retention possible." `ADR-002-project-data-format.md` (lines 40–43, accepted 2026-09-26): restricted YAML for authored project state — all scalars quoted, implicit typing off — with the rationale that implicit typing corrupts C values (register masks, float literals) silently. `design/SDD-003-data-model.md` §2 (lines 46–58): the two-tree model — version-controlled project tree (authored state) vs gitignored output tree (derived state).

**Assessment:** A real conflict on where *authored* state lives: the proposal puts test specifications in SQLite; ectt's SRS-driven rule (TOOL-PRJ-010) forbids an application database for the system of record, and ADR-002's restricted-YAML rationale (C values vs YAML implicit typing; diff-stable, decade-survivable plain text) is exactly the requirement the proposal's schema does not address. The incumbent evidence actually shows VectorCAST using SQLite for *build capture* (vcshell.db) and documented DataAPI environments "backed by SQLite plus other sources" (DEEP_ANALYSIS.md, row D6) — i.e., the proposal mirrors the incumbent, and ectt diverged deliberately. Partial alignment worth recording: the proposal's content-addressed immutable blob store (SHA-256, refcounted reclamation, §7 line 221) is conceptually ectt's output tree (derived, deletable, archived-when-evidence, SDD-003 §2), and its versioned requirement IDs + content digests (§7 line 219) match SDD-003 §2.1's `requirements/imported.reqs` + digests. The difference is medium, not concept — but the medium is what TOOL-PRJ-010/030/050 regulate.

**Recommendation:** Hold the accepted ADR-002/SDD-003 position for ectt (plain-text authored store; YAML restricted; derived state in the output tree). If run-history volume ever justifies indexed storage, confine it to the *output* tree as a rebuildable projection over plain-text evidence — never as the system of record — which would preserve TOOL-PRJ-010 while capturing most of the proposal's queryability benefit.

---

### F-04 — Harness foundation: GoogleTest as host harness vs Unity/cmocka mandatory with GoogleTest optional host-only

**Class:** conflict

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §2 stack table line 76: "Host harness | Original generated C/C++ wrappers plus GoogleTest | Reuse assertion/reporting foundations while owning environment generation and stubbing rules"; §4 (line 160): "Compile production C as C; the host test runner can be C++ with an `extern \"C\"` boundary"; line 170: "GoogleTest supplies a useful host test foundation, but gMock does not directly mock arbitrary free functions. The environment/stub generator remains a substantive component." Incumbent evidence: `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` evidence register row D3 (`selected/HARNESS_FILES/S3.c`, lines 16–112) — VectorCAST's own harness has *optional* GoogleTest initialization, i.e., the incumbent also treats GoogleTest as an add-on, not a foundation.

**ectt baseline evidence:** `design/SDD-005-external-integration.md` §5.1 (lines 219–221, quoting SRS-001): `TOOL-HAR-060` (M, P2) — Unity and cmocka mandatory, "Neither back-end shall introduce a C++ compilation or runtime dependency"; `TOOL-HAR-065` (C, P3) — "optional GoogleTest back-end for host-only execution … shall not be required for any documented workflow." §5.1.1 (lines 242–253): three mechanisms why GoogleTest cannot be the default — HAR-060 forbids C++; a C++ TU breaks `#include \"foo.c\"` static-function testing (TOOL-HAR-030); it can never run on target (TOOL-TGT-070). `PLAN-001-specification-analysis-and-work-breakdown.md` §5.5 (line 377): `WP-GEN-10` "GoogleTest back-end (host only)", P3, 3w, behind GEN-02. `ADR-006-fork-or-build-fresh.md` §3 collision #6 (line 229) rejects exactly this shape for UTBotCpp.

**Assessment:** Conflict on the default. The proposal's host-only first release makes GoogleTest-costless today (no target path yet), and its own §4 correctly identifies that gMock cannot mock free C functions — conceding ectt's fourth point in SDD-005 §5.1.1. But the moment ectt's requirements apply, GoogleTest-as-foundation violates TOOL-HAR-060's mandatory C back-ends, forfeits TOOL-HAR-030 static exposure (the `#include \"foo.c\"` technique fails in a C++ TU), and can never satisfy TOOL-TGT-070's run-unmodified-on-target rule — the same collision #6 that helped sink the UTBotCpp fork. Notably, the incumbent's own shipped harness (D3) wires GoogleTest as an optional initializer, corroborating SDD-005's optional placement and arguing against the proposal's foundation choice even on the proposal's own evidence base.

**Recommendation:** Keep Unity/cmocka as the mandatory generated back-ends and GoogleTest as the optional host-only back-end (`WP-GEN-10`, HAR-065) exactly as recorded. The proposal's useful nugget — "the environment/stub generator remains a substantive component" — is already ectt's position (CMP-GEN owns stub generation per SDD-005 §5.2; CMock demoted to CMP-MIG), so nothing structural needs to move.

---

### F-05 — One pinned LLVM/Clang host configuration vs "capability probing beats version pinning"

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §1 support contract (line 21): "One pinned LLVM/Clang host configuration using the Windows SDK/MSVC CRT; validate driver/linker/profile runtime together"; §2 line 74 ("Pin the worker to its LLVM release"); §5 (line 180): "The product must declare its own tested maximums from the pinned backend; current online documentation is not a guarantee for every installed release"; §10 (line 274): "One pinned LLVM/Clang release with matching coverage tools/runtime."

**ectt baseline evidence:** `design/SDD-005-external-integration.md` §6.3 (lines 730–741): "Capability probing beats version pinning" — scoped to three cases that resist version constraints entirely (QEMU exit-code behaviour per machine model, sanitizer/profile runtime availability per cross-target, link-seam mechanism per toolchain vendor), generalizing TOOL-TCH-060. The same document *pins its own shipped components* in §6.1 (lines 691–709): GCC 14.1 / Clang 18.1 MC/DC floors, libclang LLVM 18.1 ("Set by the MC/DC floor, to avoid shipping two LLVM trees in one air-gapped archive"), pinned Unity 2.6.0+/cmocka 1.1.7+/GoogleTest tag.

**Assessment:** Complementary, not conflicting — the two rules govern different objects. The proposal's pin is a *product support contract*: what the vendor ships, validates and declares maximums for. SDD-005 §6.3 is a *runtime architecture rule* for capabilities of software the tool does not ship (the user's compilers, simulators, sanitizers, linkers), where a version number is the wrong shape of requirement. ectt already pins what it bundles and probes what the user brings — the same split the proposal makes, expressed in different words. Both sides even agree on the failure mode: the proposal's "declare tested maximums from the pinned backend" is TOOL-TCH-060's refuse-what-the-toolchain-cannot-do, and its LLVM-coverage tool alignment requirement (§5, lines 174–182) matches SDD-005 §5.5.2's gcov version-lock discipline.

**Recommendation:** No change. Record the pairing explicitly in CMP-TCH's design vocabulary: pin the shipped analysis/coverage stack (libclang 18.1 floor, matching llvm-cov/llvm-profdata), probe user-toolchain capabilities at runtime and record them in run evidence (DSN-TCH-040/TOOL-TCH-060, SDD-005 §6.3). The proposal's support-contract table is a good format template for ectt's own documented support boundary.

---

### F-06 — Packaging: private bundled Python runtime vs PyInstaller spike evidence

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §2 stack table line 75: "Python with typed models and explicit workflow states … Package a private runtime for users; do not depend on arbitrary global Python installations"; §10 (line 275): "Pinned Python and Node toolchains for development; packaged Python and prebuilt UI assets for users"; §8 (line 253): "Signed/versioned distributable packages, dependency inventory and controlled upgrades with tested schema migration" (mechanism undelegated).

**ectt baseline evidence:** `ADR-001-architecture-decisions.md` §2.3 (line 135): bundle with PyInstaller/Nuitka into a signed installer per platform; §2.3.1 (`WP-SPIKE-03`, line 139): PyInstaller bundle of PySide6 + libclang built cleanly — 194.2 MB onedir, ~162 ms cold start, no administrative privileges; §6 R-03 (line 296): mechanical packaging risk resolved, clean-machine AV/SmartScreen policy risk still untested. `design/SDD-005-external-integration.md` §3 (line 114): "INS-030 and K-04/K-05 prohibit requiring a user-installed interpreter … they do not prohibit a bundled, offline runtime." ADR-007 (packaging) remains open by design (`SDD-001` §8 table).

**Assessment:** Aligned on the substance: both ship a private, offline Python runtime and both refuse dependence on a global interpreter — the proposal independently converged on the conclusion ADR-001 §2.3.1 validated mechanically. Two deltas: (a) the proposal adds a Node *development* toolchain and prebuilt UI *runtime* assets because of its React UI (F-02) — a supply-chain surface ectt does not carry; (b) neither side has closed the same residual risk (unsigned/large-bundle acceptance on locked-down clean machines), which ADR-001 R-03 already tracks and the proposal's "signed/versioned distributable packages" line acknowledges without a mechanism. Incumbent corroboration: VectorCAST itself ships an embedded Python 3.11 runtime (`vcast-findings/ARCHITECTURE.md` line 66), demonstrating the bundled-runtime pattern is the industry norm in this exact market.

**Recommendation:** No change to ectt's path; close ADR-007 with the per-platform signing mechanism and the clean-machine endpoint-security test that both documents identify as the open item. If the React UI were ever adopted (F-02), its prebuilt-assets pipeline must enter TOOL-LIC-030's SBOM discipline.

---

### F-07 — VcAppLib's single shared boundary with an identical 11-function import set independently supports ectt's one-API-boundary rule

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/VCAPPLIB.md` line 9: "The GUI (`vcastqt.exe`), `clicast.exe` and `manage.exe` import the same **11 functions** from this DLL"; interface surface table (lines 15–26): 81 exports in families `VcApp*` (7), `VcDb*` (45), `VcShell*` (7), `VcUtil*` (17), plus single-export internal entry points (`VcCodeGen*`, `VcInst*`, `VcQikParse*`, `VcTypeInfoDb*`); client table (lines 33–41): specialized entry points reuse the same library (`vcdb.exe` +`VcDbInternalMain`, `vcshell.exe` 2 imports, `vcutil.exe` 20). `vcast-findings/ARCHITECTURE.md` line 12: "the inspected GUI and two CLI executables directly import the same application libraries and runtime dependencies."

**ectt baseline evidence:** `design/SDD-001-architecture.md` §4.4 (lines 231–243): "`CMP-API` is the single boundary every front-end crosses … The CLI is generated from the same operation catalogue the API publishes (DSN-CLI-010) … Every API response carries the equivalent CLI invocation (DSN-API-040)"; §4 layering rule (line 164): "L5 … Front-ends. Hold no capability of their own."

**Assessment:** The incumbent's static evidence corroborates ectt's structural bet with unusual directness: one shared application-services library, three front-ends (GUI + two CLIs) consuming an identical narrow import set, and per-verb specialized entry points over the same library — functionally the same shape as ectt's CMP-API boundary with CLI verbs generated from one operation catalogue and front-ends holding no capability. The 11-function common set is even a working example of the "small surface" discipline DSN-API-020's versioned protocol aims at. The parallel has limits the evidence itself states: VcAppLib is a build-database/command API (VcDb*/VcShell*), not the whole engine, and import identity does not prove behavioural identity (`VCAPPLIB.md` line 42 warns the CLIs "must not be described as trivial wrappers").

**Recommendation:** Cite this as market validation in SDD-002/SDD-001 review discussions: the "front-ends are thin clients over one versioned boundary" rule is how the category leader actually ships. No design change.

---

### F-08 — VectorCAST component inventory families map onto SDD-001's component split at coarser granularity

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/ARCHITECTURE.md` component inventory (lines 61–74): Desktop interface (Qt GUI) · Command and project interfaces (clicast/manage) · Shared native services · Embedded scripting (python311 + Boost.Python; cabinet ships PySide2) · Build capture and compilation data (vcshell/vcdb; release notes document vcshell.db and compile_commands.json support) · Parsing and generation (edgfe, vccodegen, HARNESS_FILES) · Coverage and test orchestration (clicover, vcinst, vcqik) · Persistence and reports (SQLite; DataAPI 76 entries, ReportBuilder 319) · Requirements integration (rgw, 366 entries) · Test generation / LLM tooling (atg.exe, reqs2tests.exe, llm2check.exe; OpenAI/Anthropic/LiteLLM entries) · Compiler and target support (MinGW, GNAT, vunit) · Licensing (FlexLM). `vcast-findings/VCAPPLIB.md` lines 17–26 add `VcUtil*` "parsing/instrumentation/code-generation controls" and the `VcTypeInfoDb*` type-information entry point.

**ectt baseline evidence:** `design/SDD-001-architecture.md` §5 register (lines 266–291): 24 components in 7 layers — CMP-GUI, CMP-CLI/CMP-API, CMP-ING, CMP-ANA/CMP-TCH, CMP-GEN/CMP-TCM, CMP-BLD/CMP-EXH/CMP-EXT, CMP-COV, CMP-TRC, CMP-REP, CMP-AIF, plus L6 assurance/ecosystem.

**Assessment:** Every VectorCAST family has a natural ectt home: Desktop→CMP-GUI; command interfaces→CMP-CLI/CMP-API; build capture→CMP-ING; parsing/generation→CMP-ANA/CMP-GEN; coverage/orchestration→CMP-COV/CMP-BLD/CMP-EXH; reports→CMP-REP; requirements integration→CMP-TRC; test-gen/LLM→CMP-ATG/CMP-AIF; compiler/target→CMP-TCH/CMP-EXT. That is independent reverse-engineering support for the split: the incumbent needed the same functional seams (its `VcUtil*` export family even internal-partitions parse/instrument/codegen job control, matching ectt's CMP-BLD job orchestration). Two corroborating ironies: the incumbent embeds Python and ships PySide2 (line 66) — i.e., the market leader also chose Python + Qt for its application layer, the combination ADR-001 selects; and its GUI embeds a web view inside the native shell rather than being web-first (relevant to F-02). The mapping is coarser than 1:1: roughly 12 inventory families vs 24 ectt components, because ectt splits assurance/ecosystem concerns (L6) and holds components to requirement-allocation granularity the inventory does not resolve (its own column says "Functional subdivisions suggested by names need export/decompilation evidence").

**Recommendation:** Use this mapping as an external sanity check in SDD-001's next revision: it supports the claim that the 24-component split tracks real domain seams rather than internal aesthetics. No structural change.

---

### F-09 — Host-populated callback bridge is independent corroboration for ectt's inverted, composition-bound ports

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/VCAPPLIB.md` "Callback bridge: implementation ownership" (lines 85–108): `libvcdb_cutilsforada.dll` exports `libvcdb_AdaToCFunctionTable`; each main executable "calls it through an import thunk and writes ten addresses from that same executable into the returned table. The main executable therefore supplies the callback bodies"; each wrapper "loads one pointer, tests it for null and jumps through it when non-null."

**ectt baseline evidence:** `design/SDD-001-architecture.md` §4.3 (lines 215–218): "`CMP-ATG` … does not depend upward; it declares a `TestValidationPort` bound at composition time (DSN-ATG-110)." `PLAN-001-specification-analysis-and-work-breakdown.md` §5.5 (lines 363, 366): `WP-ATG-01`/`WP-ATG-04` carry port-mediated `^EXH-01` / `^COV-01` inverted dependencies.

**Assessment:** The incumbent's bridge is the same dependency pattern ectt formalizes as port-mediated inverted dependencies: the lower library owns the seam (null-checked dispatch table) and the upper host fills the implementations at startup. The evidence confirms table population and dispatch, not runtime execution (`VCAPPLIB.md` line 108), so the corroboration is structural, not behavioural — but structurally it demonstrates that "library defines the slot, host binds the implementation" survives in a shipping industrial tool at scale (three executables, ten slots). Ectt's variant adds what the bridge lacks: composition-time binding with a stub port so the layer graph stays acyclic and testable (DSN-ATG-110), rather than a mutable global table.

**Recommendation:** None needed; keep as corroborating evidence for the port pattern's industrial credibility.

---

### F-10 — Stub/link-seam limits stated identically on both sides

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §4 (line 164): validate at link that replacement symbols resolve to the generated stub; reject archive-member substitutions where ownership cannot be established; LTO disabled for the first validated stub path; (line 168): "This technique does not cover same-TU calls, internal linkage, inlining or arbitrary C++ methods. … Do not implement C/C++ semantics using regular-expression rewriting."

**ectt baseline evidence:** `design/SDD-005-external-integration.md` §5.2.1 (lines 346–364): link-seam strategy is a per-toolchain capability; "no link seam can intercept a call made within the same translation unit that defines the callee, and `static` functions are unreachable by any of these mechanisms. LTO makes this worse. Where the tool cannot honestly stub, it must say so." `ADR-001-architecture-decisions.md` §2.1 STB-090 row (line 108): GNU ld `--wrap` "does not intercept same-translation-unit/static/inlined calls"; §6 R-risk framing and ADR-006 §3 collision framing agree.

**Assessment:** Independent convergence on the technically correct boundary: both restrict first-release stubbing to externally linked functions replaced at the link seam, both demand link-level proof of replacement (the proposal via retained linker-map/symbol evidence; ectt via `WP-GEN-05` link-closure reporting, HAR-120), and both name LTO as the invalidator. The proposal's object-exclusion-first stub mode ("omits its original implementation object from the test link", line 162) is literally SDD-005 §5.2.1's table row "exclude the real `.o` from the test link — the preferred fallback, and often the better default." This is the strongest alignment in the set because it is a *limitation* — the kind both documents could have gotten wrong under product pressure, and did not.

**Recommendation:** No change. Optionally, when CMP-GEN's stub scope control (`WP-GEN-08`, STB-080/100/140) is designed, reuse the proposal's phrasing for the explicit-unsupported diagnostic ("same-TU calls, internal linkage, inlining" enumerated per construct), which matches TOOL-STB-120's flagging requirement.

---

### F-11 — The recovered end-to-end pipeline confirms ectt's component decomposition and its "integration is the product" thesis

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` "What this pass establishes" (lines 5–9): "The important product is an integrated testing pipeline. The inspected distribution contains distinct mechanisms for reconstructing compiler context, configuring a test environment, generating a harness, choosing real dependencies versus stubs, executing tests, collecting coverage, and querying linked results. A replacement needs agreement between those mechanisms. A test editor, compiler launcher and coverage dashboard alone would leave the hardest integration work unresolved." Recovered subsystem boundaries 1–7 and the logical workflow (lines 80–89): source/build commands → compiler context/typed model → environment/dependency policy → harness/stubs → compile/link → execution → assertions + coverage → versioned evidence store → reports/requirement links. `vcast-findings/ARCHITECTURE.md` line 82: the AutomationController route "captured build metadata → vcdb queries → project/environment setup → coverage instrumentation → generated environment scripts → compiler/test execution → results and reporting."

**ectt baseline evidence:** `design/SDD-001-architecture.md` §6 principal flows (lines 301–352): environment creation (ING → ANA → GEN → BLD) and execution/evidence (BLD → EXH/EXT → COV/REP, with TRC and CBT feeding one persisted report model); §1 (lines 20–22): every SRS requirement allocates to a design element.

**Assessment:** The investigation's central conclusion — the product *is* the integration of these seven mechanisms — is the same decomposition SDD-001 encodes, and each recovered boundary lands on a named ectt component: (1) build context in analysis input → CMP-ING; (2) environment as reproducible recipe → environment files + CMP-BLD; (3) harness lifecycle vs authoring separation → CMP-GEN/CMP-TCM; (4) explicit stub boundary → CMP-GEN + SDD-005 §5.2.1; (5) target coverage runtime as a separate component → CMP-EXT/CMP-COV; (6) independent identities for results and coverage → SDD-001 §7's "nothing overclaimed" row (DSN-COV-040/080); (7) requirements as projections with stale-detection → CMP-TRC. The proposal independently reached a seven-mechanism pipeline from incumbent evidence where ectt reached 24 components from requirements; the overlap is near-total, which is mutual validation. The residual difference is granularity and the L6 assurance band (F-13).

**Recommendation:** Use DEEP_ANALYSIS's boundary list as a checklist when reviewing SDD-001 for missing seams; it currently surfaces none. The "integration is the hardest part" warning also supports PLAN-001's weighting of the ING/ANA/GEN chain on the critical path.

---

### F-12 — Explicit link plan alongside compile_commands.json is validated by incumbent evidence on both sides

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` boundary 1 ("Build context is part of the analysis input", D5/D13) and `PRODUCT_ARCHITECTURE.md` §3 HostProfile and LinkPlan (line 116): "each EnvironmentRevision also requires a validated LinkPlan. The initial explicit manifest names selected objects, ordered libraries/archives, search paths, resolved library identities … `compile_commands.json` alone is insufficient. An unresolved input blocks building rather than being guessed." Database corroboration: `vcast-findings/VCAPPLIB.md` lines 60–72 — `FILES`/`COMMANDS`/`COMPILATION` tables with observed FILEID/CMDID join queries.

**ectt baseline evidence:** `ADR-006-fork-or-build-fresh.md` §5 item 3 (lines 326–329): harvest `link_commands.json` — "a compilation database alone cannot determine link closure … input to `WP-GEN-05` and `CMP-ING`; belongs in SDD-002's ingestion contract." `design/SDD-001-architecture.md` §4.2 (CMP-ING, DSN-ING-090 scope/dependency classification); `PLAN-001` §5.5 (line 372): `WP-GEN-05` "Link closure and unresolved reference reporting", 2w.

**Assessment:** Three independent sources converge: UTBotCpp's invented `link_commands.json` (harvested by ADR-006), the incumbent's own capture schema (COMPILATION associating build tags with FILEID and CMDID, recovered from VcAppLib's embedded SQL), and the proposal's LinkPlan contract. ectt's recorded decision already contains the right piece; the proposal adds one refinement worth noting — its FR-01 acceptance evidence (§8, line 231) explicitly includes "missing link inputs and HostProfile changes," i.e., a *validated* link manifest with host/target derivation records, which is slightly ahead of `WP-GEN-05`'s 2-week "report unresolved references" scope.

**Recommendation:** When `WP-GEN-05`/CMP-ING's link model is designed, carry the proposal's HostProfile/LinkPlan distinction (target build context vs derived host test link, with recorded transformations) into the ingestion contract — it matches ectt's host/target duality (DSN-EXH-010/DSN-EXT-060) and costs little to adopt at design time.

---

### F-13 — Components without counterparts in the other system

**Class:** gap

**vcast-findings evidence:** `vcast-findings/ARCHITECTURE.md` inventory (lines 61–74) contains no family for qualification-evidence production, security/integrity services, migration/interoperability, or a user extension framework; the closest items are data-driven configuration trees ("DATA, HARNESS_FILES, Compilers", line 68/73), metrics tables (VCMETRICS/COMMENT_DENSITY, `VCAPPLIB.md` line 67), and the licensing family (line 74: flexlm/lmgrd.exe, VLAL 9.3) which is commercial licence *enforcement*, not qualification. Conversely, VectorCAST fields ectt has nothing for: FlexLM licensing (line 74), Ada support (cutilsforada libraries, GNAT, lines 65/73), embedded WebEngine in the GUI (line 63), embedded Python scripting + Boost.Python (line 66), and the AutomationController quick-start Python app (line 22/E5, workflow at line 78).

**ectt baseline evidence:** `design/SDD-001-architecture.md` §5 register (lines 286–291): CMP-QUA (8 elements), CMP-SEC (11), CMP-MIG (8), CMP-PLG (4) — an entire L6 "Assurance & Ecosystem" layer; §4.5 (lines 246–256): CMP-AIF quarantine and DSN-PLG-040's requirement that the tool's own compiler configs/framework back-ends/report formats go through the extension points.

**Assessment:** The gaps cut both ways and each is a *position*, not an omission. Ectt's QUA/SEC/MIG/PLG have no VectorCAST analogue in the inspected evidence because they are open-source-project concerns the commercial product solves organizationally (qualification kits, vendor support, closed development) or commercially (FlexLM); SDD-001's L6 exists precisely because an OSS tool must ship those functions as software. VectorCAST's licensing, Ada, WebEngine, embedded interpreter and quick-start app have no ectt counterpart by deliberate scope (embedded C only; no browser UI per ADR-001 §3.3; CLI/GUI per SDD-001 L5; extension via CMP-PLG rather than an embedded interpreter). One partial overlap worth naming: the incumbent's per-file per-tag status tables (VCINSTRUMENTSTATUS/VCQUICKPARSESTATUS/VCCODEGENSTATUS, `VCAPPLIB.md` line 69) and "changed files" definitions (line 70) gesture toward ectt's CMP-CBT change-impact/regression territory without resolving it.

**Recommendation:** No action for ectt's component set — the asymmetric gaps confirm the two products solve different halves of the problem. When writing ADR-005/licence documentation, remember the incumbent's answer to the funding question is FlexLM + VLAL, which ADR-001 §1.1 already rules out for this project; and treat "no qualification family in the incumbent's installer inventory" as a reminder that CMP-QUA is ectt's differentiator, not table stakes.

---

### F-14 — Language scope: proposal admits C++17 in the first release; ectt v1.0 is C-only

**Class:** conflict

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §1 support contract (line 20): "Language | C99/C11; C++17 free functions and simple aggregates" in the first release; §1 eligibility (line 35): "For M2, admit simple C structs and C++17 free functions using public, trivial standard-layout aggregates."

**ectt baseline evidence:** `design/SDD-005-external-integration.md` §8 (line 788): "TOOL-HAR-060 forbids it [C++] in the mandatory back-ends, and v1.0 excludes C++ support outright." `design/SDD-001-architecture.md` §1.1 framing ("the architecture of the tool specified by SRS-001" — an embedded-**C** unit-test tool); `ADR-001` §3.1 targets the same C-idiom widgets.

**Assessment:** A scope divergence with architectural consequences, not just a roadmap difference: admitting C++17 free functions pulls a C++ runtime into the harness, which is exactly what TOOL-HAR-060's no-C++ rule exists to prevent for the mandatory back-ends, and it breaks the `#include \"foo.c\"` static-exposure technique (SDD-005 §5.1.1 item 2). The proposal contains its own contradiction here: §2 line 76 makes GoogleTest (C++) the host harness foundation while §4's own limits (line 168) exclude "arbitrary C++ methods" — i.e., it accepts C++-runtime cost without gaining C++ *member* testing, the main thing C++ support is for. Ectt's C-only v1.0 with Unity/cmocka keeps the harness a C TU, which is what makes static exposure, link seams, and target portability all work with one mechanism.

**Recommendation:** Keep ectt's C-only v1.0 scope. If C++ support is ever prioritized, it should arrive as a separately validated capability expansion with its own harness back-end and eligibility matrix (as both the proposal's §1 "Later qualification of support" column and SDD-005's ADAPTER-ONLY pattern suggest), not by relaxing HAR-060.

---

### F-15 — Evidence-overclaim defences match requirement-for-requirement

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md`: §3 AnalysisSnapshot (line 108): "Failed or unsupported TUs remain in the declared scope … Their number of coverable entities is unknown until a valid mapping exists; do not invent a denominator"; §3 CoverageSnapshot (line 150): "Never label a measured-subset percentage as complete project coverage. Distinguish mapped zero hits from missing profiles"; line 148: "LLVM region/line coverage must not be relabeled as statement coverage"; §3 TestSpec (line 132): "Boundary-value and AI-generated suggestions remain unreviewed until accepted"; §8 FR-11 (line 241): "Declare compiler/language/coverage/target capabilities. Unsupported requests fail with a concrete reason." Evidence base: `DEEP_ANALYSIS.md` row D8 (coverage models distinguishing conditions/decisions/pairs) and boundary 6 ("Coverage cannot stand in for a correctness oracle").

**ectt baseline evidence:** `design/SDD-001-architecture.md` §7 last row (lines 371–378): six independent elements for one purpose — "making the difference between *verified*, *unverified*, and *asserted-but-unreviewed* impossible to lose" — listing DSN-COV-040 (detect expressions the compiler declined to instrument), DSN-COV-080 (digest-bound coverage justifications), DSN-CBT-030, DSN-ATG-080, DSN-AIF-110, DSN-QUA-070; §4.2 (line 200–202): DSN-TCH-040 refuses a metric the toolchain cannot produce (K-03).

**Assessment:** Near-verbatim alignment on the failure mode both documents call the worst available: silent optimistic reporting. The proposal's "do not invent a denominator" and "mapped zero vs missing profile" distinctions are operational statements of DSN-COV-040/TOOL-COV-080; its provider-semantic labeling ("LLVM region/line must not be relabeled") is TOOL-COV-060's form-statement rule applied to metric naming; its "AI-generated suggestions remain unreviewed until accepted" is DSN-ATG-080/DSN-AIF-110. The incumbent evidence (D6–D8's separated expected/actual, history, and coverage models) supplied the raw observation both designs encode. This convergence from opposite starting points (requirement-first vs reverse-engineering-first) is strong evidence the rule set is domain-forced rather than taste.

**Recommendation:** No change. When CMP-COV report rendering is specified, borrow the proposal's crisp phrasings ("measured, excluded, unsupported and missing scope separately"; "coverage labeled separately from exercised production code") as acceptance-test wording for TOOL-COV-080 — they are tighter than most requirement prose.

---

### F-16 — AI/LLM surface: incumbent ships separate AI executables; ectt quarantines CMP-AIF; proposal keeps AI off the core path

**Class:** aligned

**vcast-findings evidence:** `vcast-findings/ARCHITECTURE.md` line 72: "atg.exe, code2reqs.exe, reqs2tests.exe, llm2check.exe; atg/autoreq and OpenAI/Anthropic/LiteLLM package entries", with the explicit limit "Bundled SDKs do not establish network use, enabled features, endpoints or credentials." `vcast-findings/deep-20261027/DEEP_ANALYSIS.md` "What remains unknown": "Runtime activation of optional packages and integrations." `PRODUCT_ARCHITECTURE.md` §8 (line 252): "No network or AI dependency for the core analyze/build/test/report workflow"; line 282: a language model as "optional later suggestion service; its output must pass the same deterministic build/test checks and human oracle review."

**ectt baseline evidence:** `design/SDD-001-architecture.md` §4.5 (lines 247–251): "`CMP-AIF` is structurally quarantined … it is the only component carrying an outbound network capability (DSN-CORE-090), it is separable, and with it absent everything else is unaffected. Its provenance record … is immutable and travels into every report (DSN-AIF-110)"; §5 register (line 291): CMP-AIF 13 elements, 21 requirements.

**Assessment:** Three-way convergence on AI as a separable, non-core capability. The incumbent ships AI/LLM tooling as distinct executables (llm2check.exe, reqs2tests.exe) separate from the GUI/CLI cores — process-level separation consistent with ectt's quarantine instinct, though the bundled SDK entries prove bundling, not architecture. Ectt's design is stricter than either: CMP-AIF is the only network-capable component and its provenance is mandatory in reports. The proposal's rule ("no network or AI dependency for the core workflow"; AI output must pass deterministic checks + human review) matches DSN-CORE-090's offline core and ADR-001 R-08's defensiveness almost clause for clause. Note the market signal: the presence of llm2check.exe in a 2026 safety-tooling release corroborates that CMP-AIF (21 requirements) is a real product surface, not gold-plating.

**Recommendation:** No change. Keep CMP-AIF optional and quarantined; the incumbent evidence supports its existence in the catalogue, and ectt's DSN-AIF-110 provenance rule remains the differentiator for safety contexts (R-08).

---

### F-17 — Shared residual distribution risk: clean-machine endpoint acceptance and multi-runtime supply chains

**Class:** risk

**vcast-findings evidence:** `vcast-findings/deep-20261027/PRODUCT_ARCHITECTURE.md` §10 (line 275): "packaged Python and prebuilt UI assets for users" — adding a Node toolchain and prebuilt web assets to the shipped surface; §8 (line 253): "Signed/versioned distributable packages, dependency inventory and controlled upgrades" — mechanism unspecified; §11 (line 292, M0): development-library availability and costs established as a gate. §12 (line 307): "A new product repository should be separate from this REA investigation repository."

**ectt baseline evidence:** `ADR-001-architecture-decisions.md` §2.3.1 / §6 R-03 (lines 139–141, 296): PyInstaller mechanics proven (194.2 MB, 162 ms cold start, no admin), but "clean-machine AV/SmartScreen behaviour … remains a manual follow-up"; `design/SDD-005-external-integration.md` §5.9 (line 643): PyInstaller GPL-2.0-or-later WITH exception, ADOPT-OPTIONAL build-time; §5.9's SBOM/signing rows (cosign, CycloneDX/SPDX, in-toto) are adopted precisely for this; ADR-007 remains open (`SDD-001` §8, line 401).

**Assessment:** Both stacks carry the same two unresolved tails: (1) will a large unsigned-but-signed-later bundle (194 MB for ectt; the proposal's adds prebuilt UI assets on top) pass locked-down corporate endpoints — untested on a clean machine on both sides, and it is the *target market's* defining constraint; (2) the proposal's React/Node layer adds a second package ecosystem (npm supply chain) that ectt's single-language stack avoids, widening the TOOL-LIC-030 SBOM surface if F-02 were ever adopted. The incumbent demonstrates the payoff of solving it (one InstallShield distribution, embedded runtimes, licensing daemon — `ARCHITECTURE.md` lines 12–14, 66, 74) but also its cost (FlexLM, a licensing family ectt will never have).

**Recommendation:** Close ADR-007 with the clean-machine/VM endpoint-security test as its exit criterion (both documents converge on this being the gating unknown), and hold the signing + SBOM pipeline from SDD-005 §5.9 as the mechanism. Reject any UI-technology change (F-02) that would add a second runtime ecosystem without a corresponding product win.

---

## Summary

- **The proposal and ectt agree on the hard parts.** The six friction points resolve into two genuine architecture conflicts on defaults only (F-01 LibTooling-vs-libclang default, F-04 GoogleTest default) that ectt's accepted seams and back-end catalogue already absorb or reject cleanly; the LLVM pin (F-05) and Python packaging (F-06) are complementary/aligned once "pin what you ship, probe what the user brings" is applied.
- **Two conflicts are product-identity decisions, not technical ones:** the React/loopback web UI (F-02) and the SQLite system-of-record (F-03) both contradict accepted ADRs for reasons the proposal does not answer (market security policy + product feel; TOOL-PRJ-010 plain-text evidence longevity). ADR-001 §3.3 and ADR-002/SDD-003 should stand.
- **The VectorCAST evidence independently validates ectt's architecture:** the VcAppLib 81-export boundary with an identical 11-function GUI/CLI import set (F-07) is field proof of the one-API-boundary/thin-front-end rule; the inventory families map onto all major SDD-001 components (F-08); the host-populated callback bridge (F-09) and the recovered seven-mechanism pipeline (F-11) corroborate ectt's port pattern and component seams; and the link-plan requirement (F-12) confirms the ADR-006 `link_commands.json` harvest.
- **The asymmetries are deliberate positions:** ectt's L6 (QUA/SEC/MIG/PLG) has no incumbent analogue because an OSS tool must ship what a vendor solves organizationally (F-13) — and CMP-QUA is a differentiator, while the incumbent's FlexLM/Ada/WebEngine/embedded-Python families are out of ectt's scope by decision, not omission.
- **Overclaim defences converged independently** (F-15): "do not invent a denominator," provider-labeled metrics, unreviewed-AI flags on both sides — strong evidence the TOOL-COV/ATG/AIF honesty requirements are domain-forced.
- **One shared risk to close:** clean-machine endpoint acceptance of the bundled runtime is untested on both sides and gates ADR-007 (F-17); the proposal's Node/UI asset chain would widen that surface if the web UI were adopted.

**Findings by class:** conflict **5** (F-01, F-02, F-03, F-04, F-14) · aligned **10** (F-05, F-06, F-07, F-08, F-09, F-10, F-11, F-12, F-15, F-16) · gap **1** (F-13) · risk **1** (F-17) · **total 17**.
