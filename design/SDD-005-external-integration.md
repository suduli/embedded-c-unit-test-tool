# SDD-005 — External Open-Source Integration Architecture

**Document ID:** SDD-005
**Version:** 0.1 (draft for review)
**Status:** Draft — tracks SRS-001 v0.1, which is not yet baselined
**Upstream:** SRS-001 v0.1, ADR-001 (analysis, no decision recorded)
**Constrains:** ADR-003 (symbolic execution engine), ADR-004 (coverage backend), ADR-005 (license selection), ADR-007 (distribution and packaging)

---

<!-- nav:start -->
**Related documents** — [SRS-001](../SRS-001-requirements.md) · [ADR-001](../ADR-001-architecture-decisions.md) · [ADR-006](../ADR-006-fork-or-build-fresh.md) · [SDD-001](SDD-001-architecture.md) · [SDD-002](SDD-002-interfaces.md) · [SDD-003](SDD-003-data-model.md) · [SDD-004](SDD-004-traceability-architecture.md) · **SDD-005** *(you are here)* · [Register](trace/design-elements.yaml) · [Design index](README.md)

Architecture diagrams: [specifications](diagrams) · [integration map](oss-integration.archify.json) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/).
<!-- nav:end -->


## 1. Purpose

SRS-001 specifies a tool that measures coverage it does not instrument (A-04),
parses C it does not itself parse (A-03), and reaches targets it does not itself
flash (A-06). The tool is an **orchestrator**: a large fraction of its
observable behaviour is produced by software this project will never own.

This document enumerates that software. For each candidate it records six
things, and it is the sixth that makes the document load-bearing rather than a
reading list:

| Field | Why it is here |
|---|---|
| **Role** | The job it does for this tool, in one line |
| **Component** | The `CMP-*` it attaches to — an integration with no component is unowned |
| **Mechanism** | Vendored, linked, subprocess, or format-only. Decides the licence outcome |
| **Version floor** | The lowest version that can do the job, *and what breaks below it* |
| **Embedded suitability** | Whether it survives contact with a Cortex-M that has no heap, no stdio and no OS |
| **Recommendation** | ADOPT / ADOPT-OPTIONAL / ADAPTER-ONLY / REJECT, with the reason |

### 1.1 What this document is not

It is not a build manifest, and it decides nothing. Four ADRs listed above own
the choices this document scopes; none of them is written. What this document
does is make those decisions *smaller* by fixing the constraints they must
satisfy in advance.

It also does not list dependencies of the tool's own implementation language or
GUI toolkit. Those follow ADR-001, which is unresolved, and adding them now
would presume its outcome.

### 1.2 Why "Google Test and equivalent" is the wrong frame, slightly

The tool is **not built on** a unit test framework. It *generates harnesses for*
one and *consumes results from* it. That inversion changes the selection
criteria completely:

- A framework's **ergonomics for humans writing tests by hand barely matter**, because a generator writes the harness.
- A framework's **result output format matters enormously**, because CMP-REP has to parse it.
- A framework's **runtime footprint is decisive**, because the harness has to link and run on the target (TOOL-TGT-010).

Judged that way, the field reorders sharply, and the anchor the request names —
GoogleTest — does not come first. §5.1 sets out why, and what it *is* good for
here.

---

## 2. Selection criteria

Every candidate is judged against the SRS constraints. These are not
preferences; a candidate that fails one is capped at ADAPTER-ONLY or rejected.

| # | Constraint | Test applied to every candidate |
|---|---|---|
| **K-01** | No modification of user source | Does using it require editing the code under test, or adding annotations to it? |
| **K-02** | No replacement of the user's build system | Does it insist on owning the build, or can it be driven beside an existing one? |
| **K-03** | Only claim metrics the toolchain provides | Does it invent coverage the compiler did not measure? |
| **K-04** | Usable **air-gapped** | Does first run, or any run, need the network? Package managers that resolve at build time fail here |
| **K-05** | No administrative privileges | Can it install into a user-writable prefix? Kernel modules, drivers and system services fail here |
| **K-06** | Licence permits commercial use, redistribution, modification | See §3 — the answer depends on *mechanism*, not just on the licence |

Two further filters come from the domain rather than the constraint list:

**Bare-metal survivability.** The generated harness has to link and run on a
target with no heap, no `stdio`, no filesystem, no OS, and tens of kilobytes of
RAM (TOOL-COV-100). A dependency that assumes `malloc`, `printf`, `fork`, C++
exceptions or RTTI is not disqualified outright — it may still be fine for
host-side execution under CMP-EXH — but it cannot be on the target path.

**Evidence longevity.** Output that becomes part of a certification package has
to be re-readable years later, by an assessor, without this tool. That favours
stable documented formats over rich library APIs, and it is the reason §7 treats
*formats* as a separate integration class from *libraries*.

---

## 3. The licence rule, which decides more than it looks like it does

SRS-001 states the rule directly:

> **TOOL-LIC-020** *(M, P1, I)* — Components under strong copyleft licenses shall be invoked as separate processes and shall not be linked into the tool.

This single requirement does most of the architectural work in this document,
because it converts a licensing question into a **structural** one. The relevant
distinction is not "is this GPL?" but "how is it attached?":

| Mechanism | Licence propagates to the tool? | Consequence |
|---|---|---|
| **Vendored source** | Yes — the code is in the tree | Permissive only |
| **Linked library** | Yes — for copyleft licences, this is the trigger | Permissive only |
| **Subprocess / CLI** | No — separate program, arm's-length invocation | **Strong copyleft is acceptable here** |
| **Generated code links against** | Into the *user's* test binary, not the tool | See §3.1 — different question entirely |
| **File format only** | No code dependency at all | No licence hazard whatsoever |

The practical effect is that several of the most valuable dependencies in this
document — the ones under GPL — are perfectly usable, *provided the architecture
puts a process boundary in front of them*. That boundary is not a licensing
workaround bolted on afterwards; it is a design constraint that CMP-TCH and
CMP-EXT must satisfy from the start, and it is why both components are specified
as adapters over external executables rather than as library wrappers.

### 3.1 The licence of what the tool *emits*

A separate and easily missed question. SRS-001 requires:

> **TOOL-LIC-040** *(M, P2, I)* — Code generated by the tool shall be free of licensing restriction imposed by the tool.

The generated harness links against a test framework chosen by the *user*, and
lands in the *user's* repository. So the framework's licence is inherited by the
user's test binary, not by this tool. This has a direct design consequence:
**the framework must be pluggable**, because the tool cannot impose one
licensing outcome on every user. It is the strongest single argument for the
harness generator in CMP-GEN targeting an abstract framework interface rather
than hard-coding one framework — and it is a requirement, not a preference.

### 3.2 An inconsistency in the repository that must be resolved

SRS-001 requires the tool's own licence to be permissive:

> **TOOL-LIC-010** *(M, P1, I)* — The tool's own source code shall be released under a permissive open-source license.

The repository's [`LICENSE`](../LICENSE) file currently contains **AGPL-3.0**,
which is the strongest copyleft licence in common use and is not permissive by
any reading. [`LICENSEES`](../LICENSEES) confirms this is deliberate rather than
an accident of templating.

This is a direct contradiction with TOOL-LIC-010, and it is not cosmetic:

- AGPL-3.0 would **not** prevent commercial use, redistribution or modification, so K-06 is arguably satisfied.
- But it *would* impose the network-service source-disclosure obligation on anyone deploying a modified version as a service — which is exactly the adoption barrier a tool aimed at commercial safety-critical development cannot afford.
- And under TOOL-LIC-020's own logic, an AGPL tool linking permissive dependencies is fine, but it makes the tool itself the strong-copyleft component that *its* integrators must hold at arm's length.

**This document does not resolve it.** ADR-005 owns the licence decision and is
open. What this document records is that the conflict exists, that it is
load-bearing for every "can we link this?" question below, and that **ADR-005
should be written before the dependency set is frozen**, not after. Until then,
every recommendation in §4–§8 assumes TOOL-LIC-010 wins and the tool ends up
permissively licensed. If ADR-005 instead confirms AGPL-3.0, the linked-library
recommendations stay valid but §3.1's pluggability argument becomes considerably
more urgent.

---

## 4. Integration points

Not every component touches the outside world, and the ones that do touch it
very differently. This map is the document's spine: it says *where* external
software attaches, and therefore which components carry third-party risk.

| Component | Layer | External software attaches as | Risk carried |
|---|---|---|---|
| **CMP-ANA** Source Analyzer | L1 | **Linked** C front-end | **Highest.** A single linked dependency that defines what the tool can understand |
| **CMP-TCH** Toolchain Abstraction | L1 | **Subprocess** — compilers, `gcov`, `llvm-profdata` | Version coupling, not licensing (§6.2) |
| **CMP-ING** Ingestion | L1 | **Format** — `compile_commands.json`; optional subprocess capture | Low |
| **CMP-GEN** Generation Engine | L2 | **Emits code that links against** a framework and a mock library | Licence flows to the *user* (§3.1) |
| **CMP-ATG** Auto Test Generation | L2 | **Subprocess** — symbolic execution, fuzzing | Maturity, not licensing |
| **CMP-BLD** Build Orchestrator | L3 | **Subprocess** — build generators and drivers | Low; K-02 is the live constraint |
| **CMP-EXH** Host Runner | L3 | **Subprocess** — the test binary; optional sanitizers | Low |
| **CMP-EXT** Target Runner | L3 | **Subprocess** — simulators, probe servers, flashers | GPL-heavy; process boundary is mandatory |
| **CMP-COV** Coverage Engine | L4 | **Subprocess + format** — coverage tools and their data files | **High.** Format coupling to exact compiler builds |
| **CMP-TRC** Traceability Engine | L4 | **Format** — ReqIF, CSV | Low |
| **CMP-REP** Reporting Pipeline | L4 | **Linked** template engine; **emits** standard formats | Low |
| **CMP-SEC / CMP-PKG / CMP-QUA** | L6 | **Subprocess** — SBOM, signing, licence scanning | Low; several are *required* by the SRS |
| **CMP-PLG** Extension Framework | L6 | **Hosts** third-party code the project does not vet | Deferred to SDD-002 |

Three observations follow, and they shape everything after this section.

**Exactly one component may hold a linked C front-end.** SDD-001 §4.2 already
requires this, driven by TOOL-PAR-100. This document reinforces it from the
licensing and version-coupling side: a linked LLVM dependency is the single
largest third-party commitment the project will make, and confining it to
CMP-ANA is what keeps ADR-001's language decision reversible.

**The target path is GPL-dense and that is fine.** OpenOCD, QEMU and the GNU
toolchains are all copyleft. Every one of them is invoked as a separate process
under TOOL-LIC-020, so none of them constrains the tool's own licence. The
architecture has to keep it that way — a convenience wrapper that links
`libopenocd` would be a licensing regression, not a refactor.

**The riskiest coupling in the system is not a licence, it is a file format.**
See §6.2: `gcov` data files are tied to the exact compiler build that produced
them. That is a harder constraint to satisfy than any licence in this document.

---

## 5. The catalogue

Read the `Floor` column as *"below this, the stated job cannot be done"* — not as
"latest is better". Entries marked *unverified* are the researcher's best
estimate and **must be checked against a release tag before this document is
baselined**; §10.2 lists them together.

### 5.1 Test framework back-ends — CMP-GEN, CMP-EXH, CMP-EXT

This is the section the request asked for, and the SRS has already largely
answered it. Two requirements settle the field before any comparison begins:

> **TOOL-HAR-060** *(M, P2, T)* — The tool shall generate harnesses targeting a configurable test framework back-end, supporting at minimum Unity and cmocka. **Neither back-end shall introduce a C++ compilation or runtime dependency.**
>
> **TOOL-HAR-065** *(C, P3, T)* — The tool shall provide an **optional GoogleTest back-end for host-only execution**, for interoperability with existing GoogleTest suites and tooling. **This back-end shall not be required for any documented workflow.**

So GoogleTest's status is not an open question: it is a *Could*-priority,
host-only interoperability back-end, and Unity and cmocka are the *Must*. The
catalogue below explains why that allocation is right rather than merely
recorded.

| Project | Licence | Mechanism | Floor | Bare-metal | Verdict |
|---|---|---|---|---|---|
| **Unity** (ThrowTheSwitch) | MIT | vendored source | v2.5.2; pin **v2.6.0**+ | **Yes** — best in class | **ADOPT** (mandated) |
| **cmocka** | Apache-2.0 | vendored source | 1.1.5; pin **1.1.7**+ | **Host only** — needs heap | **ADOPT, host-side** (mandated) |
| **GoogleTest** + GoogleMock | BSD-3-Clause | generated code links against | **1.14.0** (last C++14) / **1.15.0**+ (C++17) | **No** | **ADOPT-OPTIONAL**, host-only |
| greatest | ISC | vendored source | v1.4.0 | **Yes** | ADOPT-OPTIONAL |
| CppUTest / CppUMock | BSD-3-Clause | generated code links against | v4.0 | Marginal (C++) | ADAPTER-ONLY |
| Catch2 | BSL-1.0 | format only | v2 header / **v3.0.1** compiled lib | No | ADAPTER-ONLY |
| doctest | MIT | format only | v2.4.0 (JUnit reporter) | No | ADAPTER-ONLY |
| Check | LGPL-2.1-or-later | format only | — | No (`fork()`) | **REJECT** |
| Criterion | MIT | format only | — | No (subprocess per test) | **REJECT** |
| utest.h / Acutest / munit | Unlicense / MIT / MIT | format only | — | No | **REJECT** |
| Boost.Test | BSL-1.0 | format only | — | No | **REJECT** |

#### 5.1.1 Why GoogleTest cannot be the default, stated concretely

Not a matter of taste. Three specific mechanisms:

1. **TOOL-HAR-060 forbids it outright** for the mandatory back-ends — GoogleTest is C++ by construction.
2. **It breaks `static`-function testing.** TOOL-HAR-030 requires optionally exposing `static` functions, and the standard technique is `#include "foo.c"` into the harness translation unit. Inside a *C++* TU that routinely fails on ordinary C99: designated initializers, `restrict`, implicit `void*` conversions, VLAs, `_Generic`. This is the sharpest practical reason a C tool cannot centre on GoogleTest.
3. **It cannot run on the target at all.** `std::string` and `std::vector` are pervasive and not removable, so heap, a C++ runtime and static-initialisation order are all mandatory. TOOL-TGT-070 requires test cases to execute unmodified on host *and* target; a GoogleTest back-end can never satisfy that half.

A fourth point is worth recording because it is easy to miss: **GoogleMock cannot
intercept plain C functions** without a link seam anyway. For the mocking job
that dominates embedded C unit testing, the framework the request names does not
actually do the work.

What GoogleTest *is* genuinely good for here, and why TOOL-HAR-065 exists: teams
with existing GoogleTest suites and CI dashboards, on host, in mixed C/C++
codebases. Its JUnit-shaped XML is also a lingua franca CMP-REP should read
regardless of whether the tool ever generates a GoogleTest harness.

**If adopted, pin it.** GoogleTest's "live at head" policy is incompatible with a
tool that produces certification evidence; the back-end must pin a release tag,
keep Abseil and RE2 disabled, and stay separable per TOOL-LIC-070. The C++
standard steps are the load-bearing version facts: **1.12.1** was the last C++11
line, **1.13.0** moved to C++14, **1.14.0** is the last C++14 release, and
**1.15.0** raised the floor to **C++17**.

#### 5.1.2 Unity is the target back-end; cmocka is the host back-end

The SRS mandates both, and they are not interchangeable — the split is
**host versus target**, and the document should say so plainly because a naive
capability matrix built from "both are mandatory" would claim cmocka on target,
which is false.

**Unity** survives every constraint simultaneously: three files, C89-compatible,
no heap, and — decisively — *no `stdio`*. All output goes through a single
`UNITY_OUTPUT_CHAR(c)` macro that the generated harness points straight at a UART
TX register, ITM or semihosting. That is exactly the plain-text, line-oriented,
one-way channel TOOL-TGT-060 demands. It has no auto-registration, no linker
sections and no constructors, which is why it reaches `avr-gcc` and SDCC — both
named in TOOL-TCH-050 — where nothing else in the lane does.

Two Unity cautions. Its `setjmp`-based `TEST_PROTECT`/`TEST_ABORT` does **not**
survive a HardFault or watchdog reset, so TOOL-EXE-030 isolation on target must
additionally come from CMP-EXT (a fault handler that emits a fail line and
resets, or one test per image). And its optional `generate_test_runner.rb` and
`unity_fixture.h` should both be left out — the first is Ruby (K-04/K-05), the
second drags in a `malloc`-based leak detector.

**cmocka** earns its mandate on the host side: it is the mocking-capable C
framework, it supports `__wrap_` symbol interposition, and it natively emits
JUnit XML, TAP and subunit so CMP-REP needs no parser. On target it is marginal
to unusable — `malloc`/`free` for mock queues, `setjmp`/`longjmp` for unwinding,
and `stderr` for default output. **Recommendation: ADOPT cmocka as a host-side
back-end; do not represent it as a bare-metal option.**


### 5.2 Mocking and stub generation — CMP-GEN

The generated harness has to replace the unit's callees with fakes without
touching user source (K-01). Two separable questions hide inside that: *what
runtime do the fakes use*, and *who writes them*.

**The runtime.** Exactly one candidate survives the bare-metal filter.

| Project | Licence | Mechanism | Floor | Bare-metal | Verdict |
|---|---|---|---|---|---|
| **FFF** (Fake Function Framework) | MIT | vendored source | *unverified:* ≥ 1.1; hard **C99** | **Yes** — one header, no heap, no `stdio`, no `setjmp`, no C++ | **ADOPT** |
| CMock | MIT | subprocess (Ruby) | *unverified:* ≥ 2.5.4; **Ruby ≥ 3.0** | Tunable, but `CMOCK_MEM_SIZE` defaults to 32 KB of `.bss` | ADAPTER-ONLY |
| cmocka mock API | Apache-2.0 | linked library | *unverified:* ≥ 1.1.5 | **No** — `malloc` queues, `printf` reporting, `fork`/`longjmp` isolation | REJECT |
| CppUMock (CppUTest) | BSD-3-Clause | linked library | *unverified:* ≥ 4.0 | **No** — C++, needs a working global `operator new` | REJECT |
| GoogleMock | BSD-3-Clause | format only | see §5.1 | **No** — cannot intercept free C functions without a link seam anyway | ADOPT-OPTIONAL |
| Trompeloeil | BSL-1.0 | linked library | C++14 hard floor | **No** — header-only C++ is still C++ | REJECT |
| Mimick | MIT | linked library | pre-1.0, no API stability | **No** — patches instructions; code is in read-only flash | REJECT |

FFF wins on the criteria that actually bind: it is a single header with no `.c`
file, all fake state is file-scope `static` emitted by macro expansion, and it
needs no heap, no `stdio` and no C++ runtime. The one caution is a RAM trap
rather than a licence one — `FFF_ARG_HISTORY_LEN` and `FFF_CALL_HISTORY_LEN`
both default to 50, so on a 16–32 KB part CMP-GEN **must** emit tuned values or
the harness will not link. That is an argument *for* generating rather than
hand-writing: only the tool knows the target's RAM budget.

**Who writes the fakes.** CMock is the obvious candidate and the right answer is
still to decline it. CMock is not a building block for CMP-GEN; it is a
*competitor* to it. It parses headers with its own lexer and emits both the mock
and its expectation runtime — which is precisely the job CMP-ANA and CMP-GEN
exist to do. Delegating would leave the tool with two disagreeing models of the
same header, one of them weaker than the libclang-based model it already has.
It also drags a Ruby interpreter onto the engineer's machine, which collides
with K-04 (the normal acquisition path, `gem install`, is a network operation)
and adds a second language runtime to qualify under CMP-QUA.

**Recommendation:** CMP-GEN owns stub generation and emits against vendored FFF.
CMock and Ceedling are demoted to CMP-MIG as import and coexistence adapters, so
that teams with existing Ceedling suites have a migration path rather than a
cliff. Ceedling's `project.yml` is additionally useful to CMP-ING as an
ingestion source, since it already declares source sets, include paths and
defines.

#### 5.2.1 The link seam is the enabling mechanism, and it is toolchain-specific

None of the above works without a way to make the linker prefer the fake over
the real definition. This is what makes K-01 achievable at all, and it is not
portable:

| Toolchain | Mechanism | Note |
|---|---|---|
| GNU `ld` | `--wrap` | Practical floor **binutils ≥ 2.30**: with `-flto`, older `ld` silently fails to redirect calls LTO has already inlined — *the fake is never called and the test passes for the wrong reason* |
| LLVM `lld` | `--wrap` | From approximately lld 8 |
| ARM `armlink` | `$Sub$$` / `$Super$$` | No `--wrap` |
| IAR `ilink` | `--redirect` | No `--wrap` |
| Any | exclude the real `.o` from the test link | The preferred fallback, and often the better default |

Two consequences. First, **CMP-TCH must model link-seam strategy as a per-toolchain
capability**, exactly as it already models coverage capability — it cannot assume
`--wrap`. Second, there is a hard limit that must be surfaced to the user rather
than papered over: **no link seam can intercept a call made within the same
translation unit that defines the callee**, and `static` functions are
unreachable by any of these mechanisms. LTO makes this worse. Where the tool
cannot honestly stub, it must say so.

The binutils programs themselves are GPL-3.0-or-later. Under §3 this is a
non-issue: they are invoked as separate processes, and they are the *user's own
toolchain* rather than something the project redistributes.

### 5.3 C front-end — CMP-ANA

SDD-001 §4.2 already requires that exactly one component hold a C front-end
dependency. This section says which one it should be, and the answer is
unusually clear-cut.

| Project | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **libclang** (C API, `clang-c/Index.h`) | **Apache-2.0 WITH LLVM-exception** | linked library | **LLVM 18.1** | **ADOPT** |
| Clang LibTooling / `clangAST` (C++ libs) | Apache-2.0 WITH LLVM-exception | linked library | *no usable floor exists* | **REJECT** |
| tree-sitter + tree-sitter-c | MIT | vendored source | core ≥ 0.22, ABI 14 | ADOPT-OPTIONAL |
| pycparser | BSD-3-Clause | vendored source | — | **REJECT** |
| CIL / goblint-cil, Coccinelle | BSD-3-Clause / GPL-2.0-only | subprocess | — | **REJECT** |
| clang-tidy | Apache-2.0 WITH LLVM-exception | subprocess | same major as libclang | ADOPT-OPTIONAL |
| cppcheck | **GPL-3.0-or-later** | subprocess | *unverified:* 2.11 | ADAPTER-ONLY |

**libclang is the only viable choice**, for three reasons that compound. It is
the only Clang interface with an **ABI stability commitment**; it is the only one
shippable as a **prebuilt binary** that survives whatever compiler and standard
library the user has; and its licence exception is precisely what keeps LLVM
attribution obligations off the user's generated harness binaries (TOOL-LIC-040).

*What the LLVM exception buys:* plain Apache-2.0 carries notice and attribution
obligations that would otherwise attach to binaries incorporating LLVM code. The
LLVM exception removes them for code compiled with or linked against LLVM
runtime components. Recording this matters because a licence scanner that sees
bare "Apache-2.0" will raise a NOTICE-file obligation that does not in fact apply.

**LibTooling is rejected on ABI, not on capability.** Clang's C++ libraries carry
*no* source or binary compatibility guarantee; the AST and Tooling APIs change
every six-month release, and the C++ ABI additionally depends on libstdc++ vs
libc++ and on `_GLIBCXX_USE_CXX11_ABI`. A binary built against 18.1 will not load
against 19. That would force the user's C++ toolchain to match the tool's, which
is unacceptable for a tool that must install without admin rights into arbitrary
environments.

**Why the floor is LLVM 18.1 and not lower.** Parsing alone would work on
something older. The floor is set by *coverage*: A-05 and TOOL-COV-050 need
Clang ≥ 18 for MC/DC, and pinning the parser to the same major as the minimum
coverage-capable Clang avoids carrying two LLVM trees in one air-gapped release
archive. This is a packaging decision expressed as a version floor, and it should
be recorded as such so a later reviewer does not "optimise" it away.

**tree-sitter earns a place beside libclang, not instead of it.** It is the right
tool for CMP-GUI syntax highlighting and folding, for cheaply enumerating
candidate function names before paying for a full libclang parse, and for
per-function change detection in CMP-CBT. Vendor the generated `parser.c`; never
require the Node-based grammar generator at build time.

**Rejections worth recording.** pycparser cannot parse real embedded C — it
rejects GNU dialect extensions by design, and needs pre-preprocessed input, which
destroys the macro provenance CMP-ANA needs. CIL and Coccinelle *rewrite* the
code (loop normalisation, expression splitting), which destroys the 1:1 source
location mapping TOOL-COV-070 depends on to report which conditions went
uncovered.

### 5.4 Build and compilation database — CMP-ING, CMP-BLD

The binding requirement here is not K-02 alone but a sharper one:

> **TOOL-INS-030** *(M, P2, D)* — Installation shall not require the user to install or configure a language runtime, package manager, or compiler beyond their existing C toolchain.

That forbids requiring CMake to build the harness. The consequence is a clean
split: **read-side** tools extract a compilation database from the user's
project; **write-side**, the tool emits and runs its own build.

| Project | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **Ninja** | Apache-2.0 | vendored subprocess (~500 KB) | **1.10.0**; prefer 1.11 | **ADOPT** — the harness build |
| CMake | BSD-3-Clause | subprocess (user-supplied) | user **3.20**; tool's own project 3.21 | ADOPT-OPTIONAL — the documented ingestion path (TOOL-ING-040) |
| Meson | Apache-2.0 | subprocess | *unverified:* 1.0.0 | ADOPT-OPTIONAL — detect, never bundle |
| Bear | **GPL-3.0-or-later** *(unverified)* | subprocess | ≥ 3.0.0 | ADAPTER-ONLY — TOOL-ING-050 fallback; **no Windows support, ever** |
| compiledb | GPL-3.0-only | subprocess | 0.10.x | ADAPTER-ONLY |
| `intercept-build` | Apache-2.0 WITH LLVM-exception | subprocess | same LLVM pin | ADAPTER-ONLY |

**The tool generates its own `build.ninja` and ships a vendored Ninja.** This is
the only arrangement that satisfies TOOL-INS-030 without requiring the user to
have installed any build tool at all. Ninja 1.10 is the floor because below it
`ninja -t compdb` requires explicit rule names, so generic compilation-database
extraction from a Ninja-backed user project is impossible.

CMake is read-side only: configure into a **scratch directory** with `-S`/`-B`
(CMake ≥ 3.13) and harvest `compile_commands.json`. Never edit the user's
`CMakeLists.txt` — that is what K-02 forbids.

Because none of the interception tools works on Windows, and the SRS requires a
Windows desktop front-end, **the tool must provide its own compiler-wrapper shim**
as the portable fallback. Bear cannot be the primary answer.

### 5.5 Coverage — CMP-COV

The most consequential section in this document, and the one where a wrong
number changes a design decision rather than a footnote.

| Project | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **GCC `gcov` / `gcov-tool`** | GPL-3.0-or-later *(no runtime exception on the binaries)* | **subprocess** | **GCC 14.1** for MC/DC | **ADOPT** |
| **Clang `llvm-cov` / `llvm-profdata`** | Apache-2.0 WITH LLVM-exception | **subprocess** | **Clang 18.1** for MC/DC | **ADOPT** |
| **`libgcov` freestanding dump** (`-fprofile-info-section`, `__gcov_info_to_gcda()`) | GPL-3.0-or-later **WITH GCC Runtime Library Exception** | generated code links against | **GCC 11** / **GCC 12** | **ADOPT** — the bare-metal path |
| LLVM `compiler-rt` profile buffer API | Apache-2.0 WITH LLVM-exception | generated code links against | Clang 18.1 for MC/DC counters | ADOPT-OPTIONAL |
| gcovr | BSD-3-Clause | subprocess | **8.0**; prefer **8.2** | ADAPTER-ONLY |
| lcov / genhtml + `.info` | GPL-2.0-or-later | subprocess | *unverified:* 2.1–2.3 for MC/DC | ADAPTER-ONLY |
| grcov | MPL-2.0 | subprocess | *no version reads MC/DC* | **REJECT** |
| kcov | GPL-2.0-only | subprocess | — | **REJECT** — line coverage only |
| BullseyeCoverage | **Proprietary** | subprocess | — | **REJECT** — fails K-06 |

#### 5.5.1 MC/DC: what the toolchain actually gives you

There are exactly two open-source sources of MC/DC, and **both implement masking
MC/DC, not unique-cause**. TOOL-COV-060 already requires every report to state
which form is measured and by which mechanism; this is the fact it must state.

| | **GCC** | **Clang / LLVM** |
|---|---|---|
| Flag | `-fcondition-coverage` | `-fcoverage-mcdc` |
| First release | **GCC 14** (May 2024) | **LLVM 18.1.0** (Mar 2024) |
| Reader | `gcov --conditions` | `llvm-cov --show-mcdc` |
| MC/DC form | **Masking** | **Masking** |
| Conditions per decision | 64 (64-bit mask) | **default 6**, tunable |
| Practical floor | **14.2** — lcov documents 14.2, i.e. 14.1's output was not yet consumable downstream | 18.1 |

Two traps, both of which produce **silent evidence gaps** — the worst possible
failure mode for a certification tool:

**Clang's default limit is 6 conditions per decision.** Ordinary automotive guard
expressions exceed that and then simply *drop out* of MC/DC instrumentation. The
limit is tunable via the `cc1` option `-fmcdc-max-conditions`. (*Unverified:*
whether that option shipped with the original LLVM 18 implementation or arrived
in 19 — treat the availability as needing confirmation against the pinned
`clang -cc1 --help`, not prose.) TOOL-COV-080 already requires reporting
expressions the compiler could not instrument; **this is the mechanism that makes
that requirement non-optional.**

**`-fcoverage-mcdc` alone does nothing.** It is only meaningful with frontend
instrumentation — the full triple is
`-fprofile-instr-generate -fcoverage-mapping -fcoverage-mcdc`. Paired instead
with IR-level PGO (`-fprofile-generate`) it compiles cleanly and produces **no
MC/DC records at all**. CMP-TCH must therefore model the whole flag triple as a
single capability, never as independent flags.

#### 5.5.2 The `gcov` version lock is a first-class architectural constraint

`.gcno` and `.gcda` files carry a four-byte version stamp, and a `gcov` binary
**refuses to read data produced by any other GCC**. The coverage *reader* is
therefore a property of the user's toolchain, not of this tool. Three
consequences, all of which belong in CMP-TCH's design rather than being
discovered during integration:

1. The toolchain descriptor must carry an **explicit `gcov` path** — `arm-none-eabi-gcov`, never the host `gcov`.
2. **Cross-toolchain coverage merging is impossible at the `.gcda` level.** TOOL-COV-110 merging must therefore happen in the tool's own normalised coverage model, above the raw format.
3. Parse `gcov --json-format` (GCC ≥ 9), **never** the human-readable `.gcov` text, which changes between releases without notice.

#### 5.5.3 The licence keystone of the bare-metal path

TOOL-COV-100 requires retrieving coverage from a target with no filesystem and
no OS. On GNU toolchains the answer is `-fprofile-info-section` (**GCC ≥ 11**)
plus `__gcov_info_to_gcda()` from `<gcov.h>` (**GCC ≥ 12**), which lets the
harness serialise counters out over the same one-way channel it uses for results.

The licence question this raises is the single most important one in the
document, and it resolves cleanly: **`libgcov`, linked into the user's test
binary, is covered by the GCC Runtime Library Exception.** The generated test
executable is therefore *not* made GPL. This is what makes the bare-metal
coverage path licence-safe under TOOL-LIC-040, and it should be recorded
explicitly in the SBOM rationale so a later audit does not misread it.

Note the asymmetry, because it is easy to state wrongly: the **`gcov` and
`gcov-tool` binaries carry no such exception** and are plain GPL-3.0-or-later.
They must stay subprocess-only. LLVM's coverage stack, by contrast, is
Apache-2.0 WITH LLVM-exception and *could* legally be linked — it is kept as a
subprocess for v1.0 to keep CMP-PKG light, not because the licence requires it.

### 5.6 Target execution — CMP-EXT

Every viable flasher and simulator is a separate-process CLI, which is exactly
what TOOL-LIC-020 wants. The licence question therefore collapses to *never link,
never bundle GPL binaries*, and the real risks become operational.

| Project | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **QEMU** (system mode) | GPL-2.0-only | subprocess | *capability, not version* — see below | **ADOPT** (TOOL-TGT-020) |
| **Renode** | **MIT** | subprocess | *unverified:* 1.14 | **ADOPT** |
| **OpenOCD** | GPL-2.0-or-later | subprocess | **0.12.0** (Feb 2023) | **ADOPT** (TOOL-TGT-040) |
| **pyOCD** | Apache-2.0 | subprocess | **0.36.0**, **Python ≥ 3.9** | **ADOPT** (TOOL-TGT-040) |
| probe-rs | Apache-2.0 OR MIT | subprocess | *unverified:* 0.24; prefer 0.27 | ADOPT-OPTIONAL |
| **J-Link** (`JLinkExe`, `JLinkGDBServer`) | **Proprietary** — SEGGER EULA | subprocess, user-installed | *unverified:* pack 7.80 | **ADAPTER-ONLY** — never bundle |
| **SEGGER RTT** target source | **Proprietary** — grant conditioned on use with a SEGGER probe | — | — | **REJECT for generated code** |
| Semihosting + UART (pySerial) | protocol is an open Arm spec; pySerial BSD-3-Clause | vendored / tool-authored stub | pySerial 3.5 | **ADOPT** — the mandatory floor |

**Three findings worth calling out.**

**SEGGER RTT must never be emitted into generated harnesses.** Its target-side
source is licensed for use only with SEGGER J-Link probes. Emitting it into the
user's harness would impose a probe-vendor restriction on the user's own code,
which directly violates TOOL-LIC-040. Semihosting plus a user-ported UART writer
must be the mandatory transports (as TOOL-TGT-050 already requires); RTT is
strictly opt-in and user-supplied.

**J-Link is proprietary and must not be listed as open source.** TOOL-TGT-040
names it alongside OpenOCD and pyOCD, so the tool must drive it — but by
subprocess against a user-installed copy, with the discovered version recorded in
the run evidence, never bundled.

**QEMU should be constrained by capability, not by version.** The runner needs
`SYS_EXIT_EXTENDED` so a target can return a status word rather than a bare
reason code, and it needs exit-code propagation for the specific machine model in
use. That behaviour varies **per machine model, not per QEMU release**, so a
version floor is the wrong shape of requirement. CMP-EXT should probe for it and
record the result, exactly as CMP-TCH probes compiler capability.

Two operational hazards that are not licence problems but will bite: pyOCD
downloads CMSIS-Packs by default, which fails K-04 unless packs are pre-staged;
and Windows WinUSB driver installation collides with K-05. Both must be handled
as documented preconditions rather than discovered at first run.

### 5.7 Automatic test generation — CMP-ATG

Nothing in this lane is production-grade for certification evidence, and the
document should say so rather than imply otherwise.

| Project | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **CBMC** | *unverified:* modified 4-clause BSD | subprocess | *unverified:* 5.95; prefer 6.x | ADOPT-OPTIONAL — better of the two on embedded C |
| **KLEE** | NCSA (permissive) | subprocess | KLEE 3.0 + **LLVM 13–14** | ADOPT-OPTIONAL — output is mechanically translatable |
| libFuzzer | Apache-2.0 WITH LLVM-exception | generated code links against | rides the Clang 18 pin | ADOPT-OPTIONAL |
| AFL++ / honggfuzz | Apache-2.0 | subprocess | *unverified:* AFL++ 4.00 | ADAPTER-ONLY |
| SymCC | **GPL-3.0** | — | — | **REJECT** — would contaminate the user's built artefacts |
| angr, FuSeBMC | BSD-2-Clause / mixed | — | — | **REJECT** — non-mechanical output, research-grade |
| RapidCheck | BSD-2-Clause | — | — | **REJECT** — C++ |

The only defensible architecture is: **an external engine proposes input vectors;
the tool then compiles and runs them with the *user's* compiler and measures
coverage there.** The engine never enters the evidence chain. That keeps A-04 and
K-03 intact — the coverage evidence still comes from the user's toolchain, not
from a symbolic executor's model of it.

**KLEE's LLVM coupling is the whole story.** Each KLEE release accepts a narrow
LLVM range *and* requires the unit under test to be compiled to bitcode by a
`clang` from that same range. Since CMP-ANA independently pins LLVM 18.1, adopting
KLEE means **carrying a second, older LLVM** solely for ATG. That cost is the
reason this is ADOPT-OPTIONAL and gated behind explicit opt-in, and it is a
direct input to ADR-003.

### 5.8 Traceability and reporting — CMP-TRC, CMP-REP

Almost no linking hazard in this lane, and one enormous evidence hazard.

| Project / format | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **ReqIF 1.2** (OMG formal/2016-07-01) + `reqif` library | Apache-2.0 | vendored source | format 1.2; accept 1.0.1/1.1 on import | **ADOPT** — canonical interchange |
| **Jinja2** | BSD-3-Clause | **linked library** | **≥ 3.1.6** — hard floor, see below | **ADOPT** |
| WeasyPrint | BSD-3-Clause | linked library, behind a capability probe | ≥ 53 | ADOPT-OPTIONAL |
| **Pandoc** | **GPL-2.0-or-later** | **subprocess**, user-supplied | — | ADAPTER-ONLY — **never linked, never bundled** |
| Asciidoctor | MIT | subprocess (Ruby) | — | **REJECT** — Ruby runtime vs K-04/K-05 |
| StrictDoc | Apache-2.0 | subprocess + format | *unverified:* ≥ 0.0.55 | ADOPT-OPTIONAL |
| Doorstop | **LGPL-3.0-only** | **format only** | *unverified:* ≥ 3.0 | ADAPTER-ONLY — parse the YAML, never import the package |
| Sphinx-Needs | MIT | format only (`needs.json`) | *unverified:* ≥ 2.0.0 | ADOPT-OPTIONAL |
| OSLC / Eclipse Lyo | EPL-2.0 | subprocess | — | **REJECT** — network (K-04) and JVM (K-05) |

**Jinja2 ≥ 3.1.6 is a hard floor, not a preference.** Users supply report
templates, so a template-sandbox escape is arbitrary code execution inside the
tool. 3.1.6 fixed CVE-2025-27516, following a chain through 3.1.5, 3.1.4 and
3.1.3. This floor should be enforced by CMP-SEC, not merely documented.

**JUnit XML has no normative schema.** It is an Ant 1.x accident with
per-consumer dialects, and it cannot express MC/DC, requirement links, or
host-versus-target provenance. It must therefore **never be the primary audit
artefact**. The primary evidence format must be the tool's own versioned format
with a shipped, versioned schema under CMP-QUA; JUnit XML and Cobertura XML are
demoted to lossy CI-dashboard exports. For export, pin a *specific published
dialect* rather than "JUnit XML".

### 5.9 Supply chain, packaging and dynamic analysis — CMP-PKG, CMP-SEC, CMP-QUA

Two SRS requirements make this section mandatory rather than aspirational:
TOOL-LIC-030 requires an SBOM listing every dependency, version and licence, and
TOOL-LIC-060 requires the build to **verify licences automatically and fail** on
introduction of a disallowed one.

| Project | Licence | Mechanism | Floor | Verdict |
|---|---|---|---|---|
| **CycloneDX** (primary SBOM) | spec; CC0 identifier data | format | **1.5**, prefer **1.6** (= ECMA-424) | **ADOPT** |
| **SPDX** (secondary SBOM) | spec | format | **2.3**; *not* 3.0 — ISO/IEC 5962:2021 standardises 2.2.1 | **ADOPT** |
| syft | Apache-2.0 | subprocess | — | ADOPT — generates both at release |
| **`reuse`** (fsfe/reuse-tool) | **GPL-3.0-or-later** | **subprocess, CI-time only** | — | ADOPT — as a hard-failing CI gate; **never vendored** |
| ScanCode Toolkit | Apache-2.0 (licence data CC-BY-4.0) | subprocess | — | ADOPT-OPTIONAL |
| cosign / Sigstore | Apache-2.0 | subprocess | **>= 2.0**, prefer 2.2 | ADOPT, plus an unconditional detached signature for offline verification |
| in-toto / SLSA | Apache-2.0 | format | attestation v1.0 | ADOPT |
| PyInstaller | GPL-2.0-or-later **WITH exception** | build-time | >= 6.0 | ADOPT-OPTIONAL |
| diffoscope | GPL-3.0-or-later | subprocess, CI-time | — | ADOPT-OPTIONAL |
| Conan | MIT | build-time | >= 2.0 (2.x is a total break from 1.x) | ADOPT-OPTIONAL |

Note the trap in the row that matters most: **the licence-verification tool is
itself GPL-3.0-or-later.** `reuse` stays safe only because it runs as a CI-time
subprocess over the project's own sources. If it were ever vendored into the
release archive on the strength of a row reading "Apache-2.0 (tooling)",
TOOL-LIC-020 would be violated by the very component whose job is to prevent that.

**Vendoring a schema is not the same as emitting a format.** §7 makes the general point, but it has a concrete consequence here: `coverage-04.dtd` ships
with Cobertura (GPL-2.0) and `junit-10.xsd` ships inside a Jenkins plugin.
Emitting those formats carries no obligation; *copying the schema files into
`third_party/`* copies licensed artefacts, and TOOL-LIC-030's SBOM discipline
covers every file there — schemas included.

#### 5.9.1 Sanitizers, and a correction worth stating

Sanitizers discharge TOOL-EXE-090. Two facts about them are commonly stated
wrongly, and both were flagged in verification:

**GCC's `libsanitizer` is not GPL.** It is an in-tree copy of LLVM `compiler-rt`
and keeps the upstream permissive licence. A reviewer who believes GCC's ASan
runtime is GPL-3.0 will wrongly conclude that linking it into a generated harness
triggers TOOL-LIC-020, and will reject a capability that is in fact licence-clean.

**Sanitizers are linked, not subprocessed.** The runtime is linked into the
harness executable by the compiler driver via `-fsanitize=...`. Only **Valgrind**
is a subprocess. This matters for CMP-BLD, because CMP-TCH must probe for
`libclang_rt.*` / `libasan` availability *per cross target* — the same per-target
availability problem the coverage runtimes have.

| Tool | Licence | Mechanism | Host | Bare metal |
|---|---|---|---|---|
| ASan | Apache-2.0 WITH LLVM-exception | generated code links against | GCC >= 4.9 / Clang >= 3.1; assume >= 8 | **No** |
| UBSan | Apache-2.0 WITH LLVM-exception | generated code links against | as above | **Yes**, but only in `-fsanitize-undefined-trap-on-error` or `-fsanitize-minimal-runtime` mode |
| MSan / TSan | Apache-2.0 WITH LLVM-exception | generated code links against | Clang only | No |
| Valgrind | GPL-2.0-or-later; `valgrind.h` under a BSD-style licence | **subprocess** | Linux/macOS only | No |

UBSan in trap mode is the **only** on-target option: the ordinary UBSan
diagnostic runtime pulls in `printf`. The `valgrind.h` BSD-style exception is
load-bearing if the tool ever emits `VALGRIND_*` client requests into a harness —
a flat "GPL-2.0-only" would wrongly forbid that.

---

## 6. Version compatibility constraints

### 6.1 The floors that are actually binding

| Dependency | Floor | What breaks below it |
|---|---|---|
| **GCC** (MC/DC) | **14.1**, practically **14.2** | No `-fcondition-coverage` at all; TOOL-COV-050 unsatisfiable, and TOOL-TCH-070 must refuse the request |
| **Clang / LLVM** (MC/DC) | **18.1.0** | No `-fcoverage-mcdc` at all |
| **GCC** (bare-metal coverage) | **11**, then **12** | 11 for `-fprofile-info-section`; 12 for `__gcov_info_to_gcda()`. Below 12 the `gcov_info` struct is version-private and hand-serialising it will break |
| **GCC** (`gcov` JSON) | **9** | Only the human-readable `.gcov` text, which changes between releases without notice |
| **libclang** | **LLVM 18.1** | Set by the MC/DC floor, to avoid shipping two LLVM trees in one air-gapped archive |
| **Ninja** | **1.10.0** | `ninja -t compdb` needs explicit rule names — no generic database extraction |
| **CMake** (user) | **3.20** | `-S`/`-B` at 3.13; presets v1/v2/v3 at 3.19/3.20/3.21 |
| **Jinja2** | **3.1.6** | CVE-2025-27516 sandbox escape — arbitrary code execution via a user-supplied template |
| **pyOCD** | **0.36.0**, **Python >= 3.9** | Below 3.9 the wheel chain falls back to source builds needing a C toolchain and Rust — an air-gap installability failure, not a functional one |
| **OpenOCD** | **0.12.0** | No `rtt setup/start` commands; incomplete `SYS_EXIT` handling, so a target run cannot report pass/fail |
| **cosign** | **2.0** | v1 keyless flow and bundle layout removed; verification commands changed incompatibly |
| **GoogleTest** | **1.14.0** (C++14) or **1.15.0** (C++17) | The C++ standard step is the real boundary, not the tag number |
| **Unity** | **2.5.2**, pin **2.6.0**+ | Below 2.5.2, no supported CMake/Meson build files, forcing a hand-rolled build fragment |
| **cmocka** | **1.1.5**, pin **1.1.7**+ | No `cmocka_set_test_filter()` — per-test isolation and per-test coverage attribution both become unimplementable |
| **gcovr** | **8.0**, prefer **8.2** | Condition-coverage data silently dropped; 8.0/8.1 throw on real GCC 14 output |

### 6.2 The three couplings that are not simple floors

A floor says "at least X". These three say something harder, and each is an
architectural constraint on a named component rather than a packaging detail.

**1. The `gcov` version lock — CMP-TCH.** Not "at least GCC 14" but *"exactly the
GCC that built the object"*. The reader is a property of the user's toolchain, so
the toolchain descriptor must carry an explicit `gcov` path, and cross-toolchain
merging is impossible at the `.gcda` level. See §5.5.2.

**2. The KLEE-to-LLVM range — CMP-ATG.** Not "at least LLVM 13" but *"LLVM 13–14
inclusive, and the unit under test must be compiled to bitcode by a `clang` from
that same range"*. Since CMP-ANA pins LLVM 18.1, adopting KLEE means carrying two
LLVM versions. That is an input to ADR-003, not an implementation detail.

**3. The libclang ABI boundary — CMP-ANA.** Not a floor but a *contract choice*:
the C API carries a stability commitment and the C++ libraries carry none. This
is why 5.3 rejects LibTooling on ABI rather than on capability.

### 6.3 Capability probing beats version pinning

Three cases resist version constraints entirely, and CMP-TCH should treat them as
**probed capabilities** recorded in the run evidence:

- **QEMU semihosting exit-code propagation** varies per machine model, not per release (§5.6).
- **Sanitizer and profile runtime availability** (`libclang_rt.*`, `libasan`) varies per cross target, not per compiler version (§5.9.1).
- **Link-seam mechanism** varies per toolchain vendor — `--wrap`, `$Sub$$`, `--redirect`, or object exclusion (§5.2.1).

This generalises a rule the SRS already states for coverage in TOOL-TCH-060: the
toolchain declares what it can do, and the tool refuses what it cannot. The same
discipline should govern every external capability, not only coverage metrics.

---

## 7. Formats are not dependencies

A recurring category error in dependency documents is to treat "we emit Cobertura
XML" as a dependency on Cobertura. It is not. Emitting a format copies nothing,
links nothing and redistributes nothing, so it imports none of the originating
tool's obligations. Cobertura is GPL-2.0 and JaCoCo is EPL-2.0; producing files
that conform to their DTDs imports neither.

This distinction is worth recording explicitly in the SBOM rationale so that a
later audit does not misread an emitted format as a linked dependency — and so
that the reverse mistake is not made either. **Vendoring the schema file is a
different act from emitting the format**, and it does copy a licensed artefact
(§5.9).

| Format | Used for | Status |
|---|---|---|
| **ReqIF 1.2** | Requirements interchange — CMP-TRC | **ADOPT** as canonical |
| **TAP 14** | Target-to-host wire protocol | ADOPT — survives a lossy one-way serial link |
| **JUnit XML** | CI dashboards | Export only; **never the audit artefact** — no normative schema exists |
| **Cobertura XML** | CI coverage dashboards | Export only, first priority |
| **JaCoCo XML** | CI coverage dashboards | Export only, on demand |
| **SARIF 2.1.0** | Tool diagnostics | ADOPT-OPTIONAL |
| **CycloneDX 1.6 / SPDX 2.3** | SBOM — TOOL-LIC-030 | **ADOPT** |

The primary evidence format must be the tool's own, versioned, with a shipped
schema under CMP-QUA. Everything in the table above is an export.

---

## 8. Rejected, and why

A rejection with a stated reason is worth more than a silent omission, because it
stops the same candidate being re-proposed every six months. Grouped by the
reason that actually kills it.

**Rejected on bare-metal impossibility.** Check, Criterion, utest.h, Acutest,
munit and Boost.Test all isolate tests with `fork()` or a spawned subprocess.
There is no process model on a bare-metal Cortex-M, so no version of any of them
can satisfy TOOL-TGT-070. Several also auto-register tests through linker-section
tricks that do not survive SDCC or avr-gcc, both named in TOOL-TCH-050.

**Rejected on C++.** Trompeloeil, RapidCheck and Catch2 as a *generation* target.
Header-only C++ is still C++; TOOL-HAR-060 forbids it in the mandatory back-ends,
and v1.0 excludes C++ support outright.

**Rejected on ABI or API instability.** Clang LibTooling (no compatibility
guarantee at all, §5.3) and Mimick (pre-1.0, and it rewrites instructions at
runtime — which additionally destroys the argument that the code under test is
the code that ships, the one claim a qualification case cannot give up).

**Rejected on fidelity.** pycparser cannot parse real embedded C. CIL and
Coccinelle rewrite the source, destroying the location mapping TOOL-COV-070
needs. grcov and kcov cannot read MC/DC or branch data at all — for grcov, *the
floor that matters does not exist*.

**Rejected on runtime footprint of the toolchain, not the target.** Asciidoctor
and the CMock/Ceedling stack each require a language interpreter the user may not
have and the tool may not install (K-04, K-05). OSLC/Eclipse Lyo needs a JVM and
a network.

**Rejected on licence.** SymCC (GPL-3.0 in a position where it would contaminate
the user's built artefacts) and BullseyeCoverage (proprietary, fails K-06).
**SEGGER RTT target source** is rejected specifically for *generated code*: its
grant is conditioned on use with a SEGGER probe, so emitting it into a user's
harness would impose a probe-vendor restriction on the user's own code, violating
TOOL-LIC-040.

One rejection is recorded here with a **corrected rationale**, because the
original reasoning was wrong in a way that would not have survived review.
**Check** was initially rejected partly on TOOL-LIC-050. That is a misreading:
TOOL-LIC-050 forbids bundling components whose licence *prohibits commercial
use*, and LGPL-2.1 permits commercial use. The correct objections to Check are
the `fork()` isolation model, the relinking and object-provision obligations that
LGPL-2.1 static linking would impose on the *user's* firmware, and the project's
apparent dormancy. A rejection justified by a misapplied constraint is worse than
no justification, because overturning the bad reason takes the good ones with it.

---

## 9. The integration diagram

The map is [`oss-integration.archify.json`](oss-integration.archify.json),
rendered to [`../docs/oss-integration.html`](../docs/oss-integration.html).

It shows the five components that carry external attachments, and for each
external project the **mechanism** and the **licence** — because §3 established
that those two together, not the licence alone, decide the outcome. Three bands
of meaning are encoded in the node subtitles:

- **LINKED** — into the tool binary. Permissive licences only. Exactly one entry: libclang.
- **HARNESS LINK** — into the *user's* test binary. The licence flows to the user, not to this project.
- **SUBPROCESS** — a separate program. Strong copyleft is safe here, which is why the GPL entries sit in this band.

### 9.1 Why this diagram is not machine-checked, unlike the other nine

The diagrams under [`diagrams/`](diagrams/) are validated by
`trace_check.py --check-diagrams`, which enforces that a diagram may not draw a
component or an edge the register does not contain. That rule is what keeps them
honest, and it is also precisely why this diagram cannot live there: **its nodes
are third-party projects, which are deliberately not register components.** Adding
them to the register to satisfy the checker would corrupt the register's meaning —
it holds *design elements this project is answerable for*.

So this map sits beside [`doc-map.archify.json`](doc-map.archify.json) in
`design/`, following the precedent that file already set for a diagram whose
nodes are not components. The checker's glob is non-recursive over
`design/diagrams/`, so neither file is picked up, and the eight component views
still own all 24 components exactly once. Verified: `trace_check.py
--check-diagrams design/diagrams` passes unchanged after this document was added.

**The honest cost:** this diagram is authored and unchecked, so it can go stale
silently — the exact failure mode SDD-004 exists to prevent. The way to close
that gap later is to give the OSS catalogue its own machine-readable register
(`design/trace/oss-dependencies.yaml`) carrying project, licence, mechanism,
version floor and `CMP-*` allocation, and extend the checker to validate this
diagram against it and this document against both. That is deliberately **not**
done here: it is a change to the traceability architecture, which is SDD-004's
territory and deserves its own decision rather than being smuggled in with a
dependency list.

---

## 10. What this constrains, and what is still uncertain

### 10.1 Inputs to the open ADRs

This document does not decide anything. It does narrow four open decisions:

| ADR | What this document contributes |
|---|---|
| **ADR-003** — symbolic execution engine | KLEE forces a **second LLVM** (13–14) alongside CMP-ANA's 18.1. CBMC does not. That packaging cost, not raw capability, should drive the choice (§5.7, §6.2) |
| **ADR-004** — coverage backend | Both open-source MC/DC sources give **masking** MC/DC, and each has a different silent-failure mode: Clang's 6-condition default and GCC's version-locked data files (§5.5) |
| **ADR-005** — licence selection | The repository's AGPL-3.0 `LICENSE` contradicts TOOL-LIC-010. **This should be settled before the dependency set is frozen** (§3.2) |
| **ADR-007** — distribution and packaging | TOOL-INS-030 plus K-04/K-05 rule out every interpreter-based dependency and every build tool the user must install. Vendored Ninja is the consequence (§5.4) |

### 10.2 Version claims that must be re-verified before baseline

Verification flagged these as plausible but unconfirmed. **They are marked
*unverified* in the tables above and must be checked against a release tag,
changelog or `--help` output before this document is baselined.** They are
ordered by how much a wrong value would cost.

1. **GCC's condition-coverage term limit and its exact masking-MC/DC wording.** Read the GCC 14/15 `gcov` manual node directly and put the wording into the CMP-QUA evidence template — TOOL-COV-060 requires the report to state it.
2. **LLVM's `-fmcdc-max-conditions` default, whether it exists in 18 or only 19, and the true test-vector cap.** Take these from the pinned `clang -cc1 --help`, not from prose.
3. **lcov's actual `--mcdc-coverage` release** (stated as 2.3; likely earlier in the 2.x line).
4. **GoogleTest's `CMakeLists.txt` minimum at the exact pinned tag** (stated as 3.16 at 1.15.0; likely ~3.13).
5. **QEMU semihosting exit-code behaviour** — probe per machine model rather than pinning a version (§6.3).
6. **SPDX identifiers** for Bear, cppcheck and Valgrind — the *or-later* distinction is the first thing an auditor checks, and TOOL-LIC-030 requires the SBOM to be machine-checkable.
7. Feature-to-release attributions for Unity, cmocka, greatest, doctest, FFF and CMock.

The following **were** confirmed and are safe to baseline as stated: Clang
`-fcoverage-mcdc` first shipped in **LLVM 18.1.0**; GCC `-fcondition-coverage` and
`gcov --conditions` first shipped in **GCC 14**; `gcov --json-format` from **GCC 9**;
`-fprofile-info-section` from **GCC 11**; `__gcov_info_to_gcda()` from **GCC 12**;
`libgcov` covered by the **GCC Runtime Library Exception**; the GoogleTest C++
steps (1.12.1 last C++11, 1.13.0 → C++14, 1.14.0 last C++14, 1.15.0 → C++17);
CMake `-S`/`-B` at 3.13 and presets v1/v2/v3 at 3.19/3.20/3.21; Ninja `compdb`
without rule names and dyndep at 1.10; OpenOCD 0.12.0; the Jinja2 CVE chain
through 3.1.6; SARIF 2.1.0; CycloneDX 1.6 = ECMA-424; SPDX 2.2.1 = ISO/IEC
5962:2021; ReqIF 1.2 = OMG formal/2016-07-01; cosign 2.0 breaking v1 verification.

### 10.3 The three risks worth carrying forward

**A silent evidence gap is the worst failure mode this tool has.** Two mechanisms
in §5.5 produce one: Clang's 6-condition MC/DC default, and `-fcoverage-mcdc`
paired with the wrong instrumentation flag. Both compile cleanly and produce no
error. TOOL-COV-080 already requires reporting what could not be instrumented;
these are the mechanisms that make it non-negotiable.

**The `gcov` version lock is a design constraint, not an integration detail.** It
must be in CMP-TCH's toolchain descriptor from the start (§5.5.2).

**The licence-verification tool is itself GPL-3.0-or-later.** `reuse` is safe as a
CI-time subprocess and unsafe vendored (§5.9). The document that records the
licence rule should not be the one that breaks it.
