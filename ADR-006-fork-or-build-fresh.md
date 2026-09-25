# ADR-006 — Fork UTBotCpp or Build Fresh

**Document ID:** ADR-006
**Status:** **Accepted, 2026-09-19 — build fresh. Do not fork `UnitTestBot/UTBotCpp`.**
**Relates to:** ADR-001 §2, §3, §4, §5; SDD-001 §8; SDD-005 §5.1, §5.2, §5.7; PLAN-001 §4.1, §4.2, §4.3, §5.5; SRS-001 open question 4

---

<!-- nav:start -->
**Related documents** — [SRS-001](SRS-001-requirements.md) · [ADR-001](ADR-001-architecture-decisions.md) · **ADR-006** *(you are here)* · [ADR-008](ADR-008-ai-structured-decision-provider.md) · [SDD-001](design/SDD-001-architecture.md) · [SDD-002](design/SDD-002-interfaces.md) · [SDD-003](design/SDD-003-data-model.md) · [SDD-004](design/SDD-004-traceability-architecture.md) · [SDD-005](design/SDD-005-external-integration.md) · [Register](design/trace/design-elements.yaml) · [Design index](design/README.md)

Architecture diagrams: [specifications](design/diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 1. Context

SDD-001 §8 calls this decision "the one genuine blocker," and states why in terms
no other open decision earns:

> ADR-006 is the one genuine blocker. The others can be decided late without
> rework; a fork decision arriving after implementation starts invalidates
> `CMP-ANA`, `CMP-ATG`, and the `CMP-GEN` framework back-end simultaneously.

PLAN-001 §4.2 reaches the same place from the schedule side and calls it "the
decision that cannot wait," gating `WP-ANA-01` at week 10. ADR-001 §5 records the
pre-research hypothesis — UTBotCpp is "host-Linux-oriented, C++-implemented, and
generates GoogleTest output" — and is explicit that the three validation spikes
do **not** settle it: they tested whether a fresh Python + libclang + PySide6
build is *viable*, not whether forking would be *better*.

This document supplies the missing half. It is a direct evaluation of
`UnitTestBot/UTBotCpp` against this specification, from the repository, its wiki,
and the GitHub API rather than from recollection.

**Evidence date: 2026-09-05.** Every repository observation below is a point
reading on that date and is dated where it matters. §9.3 lists what was not
verified.

---

## 2. What UTBotCpp actually is

### 2.1 Provenance, license, and scale

| Fact | Value | Source |
|---|---|---|
| Repository | `UnitTestBot/UTBotCpp`, created 2021-10-07, not a fork | GitHub API `/repos` |
| License | **Apache-2.0** (`spdx_id: "Apache-2.0"`) | GitHub API `/repos`, `license` object |
| Primary language | C++ — **1,750,913 bytes** | GitHub API `/languages` |
| Front-end languages | Kotlin 269,460 B (CLion plugin), TypeScript 231,024 B (VS Code plugin) | same |
| Stars / forks / open issues | 185 / 32 / 123 | GitHub API `/repos` |
| Top-level layout | `server/`, `vscode-plugin/`, `clion-plugin/`, `docker/`, `submodules/`, `integration-tests/` | GitHub API `/contents` |
| Submodules | `UnitTestBot/klee`, `UnitTestBot/Bear`, loguru, json, ordered-map, parallel-hashmap | `.gitmodules` |

The license is the single most favourable fact in this document for the fork
case, and it should be stated before any of the unfavourable ones. **Apache-2.0
is exactly what ADR-001 §5 recommends for ADR-005.** A fork inherits the forked
project's license for retained code, and here that inheritance costs nothing: it
satisfies `TOOL-LIC-010`'s permissive requirement, matches the express-patent-grant
rationale ADR-001 §5 gives for preferring Apache-2.0 over MIT, and creates no
tension with the LGPL dynamic-linking analysis in ADR-001 §3.4. **There is no
license obstacle to forking.** Whatever decides this, it is not licensing.

Two submodules are themselves project-maintained forks — `UnitTestBot/klee`
(the "KLEEF" engine, a fork of `klee/klee`) and `UnitTestBot/Bear`. Forking
UTBotCpp therefore means adopting three forks, not one. `UnitTestBot/klee`
resolves to `spdx_id: "NOASSERTION"` on the GitHub API, meaning GitHub could not
machine-identify its license; upstream KLEE is NCSA. That must be resolved before
any KLEEF-derived code is retained, because `TOOL-LIC-030` requires a
machine-checkable SBOM and *or-later*/identifier ambiguity is the first thing a
license auditor pulls on.

### 2.2 Maintenance status — dormant product line inside a live organisation

This is the finding that most changes the calculus, and the distinction in the
heading is the important part.

**UTBotCpp itself is dormant:**

| Signal | Observation |
|---|---|
| `main` HEAD | `df4818f`, **2024-06-14** — "Add logs to lcov (#685)" |
| Last push to any branch | **2024-10-18** (`pushed_at`) |
| Last release | **2024.3.0, published 2024-03-26** |
| Open issues with zero replies | #693 (2026-05-20), #692 (2025-04-10), #690 (2024-12-03), #689 (2024-08-29), #686 (2024-07-13) |
| PR #688 "Update KLEE" | Opened **2024-08-01** by `ladisgin` — the repository's own most prolific recent contributor. State: **open**, `mergeable_state: "clean"`, **0 comments, 0 review comments**, untouched since 2024-08-07 |
| Recent CI | The only workflow run in the current window is `Add issue to projects` (an issue-triage automation, 2026-05-20). The `Build UTBot and run unit tests` workflow the README badges is not running |
| Unmerged feature branches | `ladisgin/new_update_klee`, `ladisgin/lazy_init`, `ladisgin/compare_with_ai`, `ladisgin/update_ubuntu_version` |

PR #688 is the sharpest single data point. A clean, mergeable pull request that
updates the project's core dependency, from the project's own principal
contributor, has sat unreviewed for **over two years**. That is not a backlog;
that is an absent maintainer.

**The organisation, however, is very much alive** — and this cuts against the
naive "abandoned project" reading, so it must be stated:

| Repo | Language | Last push |
|---|---|---|
| `usvm` — Universal Symbolic Virtual Machine | Kotlin | 2026-08-31 |
| `jacodb` | Kotlin | 2026-08-31 |
| `ksmt` | Kotlin | 2026-08-11 |
| `klee` — KLEEF engine | C++ | 2026-04-18 |
| `UTBotJava` | Kotlin | 2025-10-27 |
| **`UTBotCpp`** | **C++** | **2024-10-18** |

**Read together, these are worse news for the fork case than an outright
abandonment would be.** An abandoned organisation might be revived, or its
project adopted by a community. What the table shows instead is a funded, active
research group that has *reallocated* — its symbolic-execution investment has
migrated to the JVM stack (`usvm`, `jacodb`, `ksmt`) and to KLEEF as a standalone
engine, while the C/C++ product has been left in place, unarchived and
undeprecated, for two and a quarter years. A team that is still shipping
elsewhere and still not shipping here has made a choice. Forking under those
conditions is not a partnership with an upstream; it is an **adoption with no
shared burden** — every subsequent bug, port, and dependency bump is yours alone,
while the original authors are demonstrably occupied elsewhere.

The absence of an archive banner or deprecation notice means this is inference
from repository telemetry rather than a statement from the maintainers. §9.2
records that as a limitation. But five independent signals — commits, releases,
CI, issue response, and an ignored PR from an insider — all point the same way,
and a search for any public status statement found none.

### 2.3 Architecture and pipeline

From the wiki's `utbot-inside`, `intro`, `stubs-inside`, `compile-database`,
`coverage`, and `system-requirements` pages, corroborated by the repository
layout and Dockerfile.

**Shape.** A gRPC client-server split. The server does all work; the client is an
IDE plugin (VS Code, or CLion). The wiki states the split exists specifically to
avoid "managing multiple LLVM, GCC, and solver versions on a single machine" —
which is precisely the insight ADR-001 §2.4 already borrowed, and borrowed
without needing the code.

**Pipeline** (wiki `utbot-inside`, eleven stages, condensed):

1. Client request → server
2. **Fetcher** — "fetches types, methods, global variable usages, array usages,
   includes," using **LibTooling** to parse and traverse the AST
3. **SourceToHeaderRewriter** — synthesises headers from sources
4. **FeaturesFilter** — "filters out all methods except the ones listed in
   supported syntax"
5. **Synchronizer** — reconciles stubs and wrappers across `compile_commands.json`
6. **KleeGenerator** — emits KLEE driver files, builds them to bitcode
7. **Linker** — links bitcode into one module, emits Makefiles
8. **KleeRunner** — runs KLEE on the module, per function
9. **KleeGenerator** — "parses output of KLEE and writes files of **GoogleTest**"
10. Response and file transfer to client

**Project configuration.** Requires `compile_commands.json` *and* a
project-invented `link_commands.json`, because — in the wiki's own words —
`compile_commands.json` "only contains information about compilation of
individual source files. That is not sufficient to determine function behaviour."
For CMake projects UTBotCpp can set `CMAKE_EXPORT_COMPILE_COMMANDS=ON` itself; for
Make projects it applies its **patched Bear** fork, which was modified to emit
`link_commands.json` as well. That, concretely, is what "automatic project
configuration" means — and it is narrower than the phrase suggests:
`system-requirements` states plainly that the tool "needs no manual configuration
only for CMake projects."

**Stub synthesis** (wiki `stubs-inside`). Genuinely clever and worth
understanding regardless of this decision. Stubs return a *symbolic* value:
a file-scope global plus a first-call flag, switched by a compile-time
`KLEE_MODE` macro. Under `KLEE_MODE=1` the first call creates a symbolic
variable; under `KLEE_MODE=0` — the test-execution build — the same stub returns
a global the test body has set. One emitted artifact serves both symbolic
exploration and concrete replay. The stated limit is severe, though: "UTBot is
capable of generating only simple stubs, **which do not depend on their
arguments**."

**Coverage** (wiki `coverage`). "UTBot collects **line coverage** for user
project files while running tests," via `gcov` or `llvm-cov` depending on the
compiler. Line coverage, and nothing else.

**Platforms** (wiki `system-requirements`, `windows-local`). x64 only — "x86,
ARM: not supported." Server: **Ubuntu 18.04–20.04**. Other Linux, macOS: Docker.
Windows: "via WSL only or WSL with Docker," and `windows-local` specifies "Set up
WSL with Ubuntu 18.04."

**Pinned dependency stack** (`docker/Dockerfile_base`): GCC 9, CMake 3.17.2,
gRPC 1.49.0, Z3 4.8.17, GoogleTest 1.10.0, Node.js 16, klee-uclibc v1.2, LLVM via
a `LLVM_VERSION_MAJOR` build argument — set to **14** by commit `9370dfa`,
"Update to llvm 14 (#664)," 2024-01-15. Node 16 and Ubuntu 18.04 are both past
end of standard support.

### 2.4 The fair case for forking, stated at full strength

Four things UTBotCpp solves that this project would otherwise solve itself.

1. **End-to-end KLEE integration.** Rebuilding an arbitrary project to LLVM
   bitcode from its own compile and link commands, linking a whole module, and
   driving KLEE per function is the hard, unglamorous part of symbolic test
   generation. It exists here and it has shipped.
2. **A substantially patched KLEE.** The `klee-patches` wiki page documents
   floating-point support (KLEE-Float rebased), sanitizer-instruction handlers,
   lazy initialisation of symbolic heap locations, a `bcov_check_interval`
   coverage timeout, POSIX-runtime extensions for symbolic stdin, inline-assembly
   handling, and an interactive mode reported to cut 500-function generation from
   963 s to 52.3 s. Several of these are research contributions, not
   configuration.
3. **The symbolic-stub design.** The `KLEE_MODE` duality (§2.3) is a
   non-obvious, genuinely good idea.
4. **`link_commands.json`.** The observation that a compilation database alone
   cannot determine link closure is correct, under-appreciated, and directly
   relevant to `WP-GEN-05` (link closure and unresolved-reference reporting) and
   to `CMP-ING`.

All four are real. §4 weighs them. §5 keeps three of them.

---

## 3. Where UTBotCpp collides with this specification

ADR-001 §5's three-item hypothesis is **confirmed on all three counts**, and it
understates the problem. Eight collisions, ordered by severity.

| # | Collision | Evidence | Requirement / document in conflict |
|---|---|---|---|
| 1 | **No target execution at all.** x64 host only; x86 and ARM explicitly unsupported. No cross-compilation, simulator, or on-hardware path exists anywhere in the pipeline | wiki `system-requirements` | `TOOL-TGT-010` (build harness for a cross-compiled target), `TOOL-TGT-070` (test cases execute unmodified on host *and* target). The whole `CMP-EXT` lane has no counterpart |
| 2 | **Line coverage only** | wiki `coverage` | `TOOL-COV-010`–`080`. `TOOL-COV-060` requires every report to state which MC/DC form was measured. Nothing in `CMP-COV` (10 elements, 17 requirements) is served |
| 3 | **Pinned to LLVM 14** | commit `9370dfa`, 2024-01-15; `Dockerfile_base` | SDD-005 §5.3 sets CMP-ANA's floor at **LLVM 18.1**, and §10.2 confirms as verified that Clang `-fcoverage-mcdc` first shipped in 18.1. The fork's own pin is four major versions below the floor the coverage strategy requires |
| 4 | **LibTooling throughout** | wiki `utbot-inside` — the Fetcher "uses LibTooling" | SDD-005 §5.3 marks LibTooling **REJECT**, with the reason "*no usable floor exists*" — it has no stable API. This is what makes collision #3 expensive rather than mechanical |
| 5 | **Ubuntu-resident server; Windows means WSL + Ubuntu 18.04** | wiki `system-requirements`, `windows-local` | `TOOL-UIX-040` (installable by a user with no development environment beyond a C toolchain), `TOOL-INS-030` (no language runtime, package manager, or compiler beyond the existing C toolchain). "Install WSL, then Ubuntu 18.04, then a gRPC server" is the negation of both |
| 6 | **GoogleTest output, in C++ translation units** | wiki `utbot-inside` stage 9; `utbot.org` user guide | `TOOL-HAR-060` — Unity and cmocka mandatory, "**Neither back-end shall introduce a C++ compilation or runtime dependency**." SDD-005 §5.1.1 adds the sharper problem: `#include "foo.c"` inside a C++ TU breaks on ordinary C99, so `TOOL-HAR-030` static-function testing does not survive |
| 7 | **Its C support matrix excludes what embedded C is made of** | wiki `c-syntax` | `void*` **not supported**; variadic arguments **not supported**; the ternary operator **not supported**; function pointers **partial**; and "functions depending on external state and functions whose result depends on the number of calls aren't supported." Memory-mapped register access *is* external state; `void*` handles are the HAL idiom. `WP-SPIKE-01`'s fixture — STM32F4 HAL — is exactly this code |
| 8 | **No standalone GUI, and two more front-end languages** | repo layout: `vscode-plugin/` TypeScript, `clion-plugin/` Kotlin | ADR-001 §3 and `CMP-GUI` — 27 elements, 33 requirements, 22 work packages, 85 person-weeks. A fork contributes zero to it |

Collision #7 deserves a sentence of its own, because it is the one that inverts
the fork's headline benefit. The asset being offered is *automatic test
generation*. Its own documentation says it will not generate for functions that
depend on external state — which is the defining characteristic of the driver and
HAL code this tool exists to test.

### 3.1 Two corrections to ADR-001's own text

Both should be folded into ADR-001 when this is accepted.

**ADR-001 §2.4 — "without inheriting the Docker requirement."** Imprecise, and
the reality is worse than the claim. Docker is *not* universally required: on
Ubuntu 18.04–20.04 the server installs natively from a release archive. Docker is
the *portability* mechanism for every other host. What a fork inherits is not
Docker — it is **Ubuntu**. Docker is merely how the Ubuntu assumption is smuggled
onto machines that are not Ubuntu.

**ADR-001 §5 — the three-item objection.** All three items hold, but the list is
incomplete in a way that matters. Add: dormant since mid-2024 with no upstream to
share maintenance; pinned to LLVM 14 against a required floor of 18.1;
line-coverage only; no cross-target execution; no standalone GUI; and a
generation-support matrix that excludes `void*`, variadics, and external state.

---

## 4. Effort — what a fork saves and what it costs

PLAN-001 §5.5 gives the fresh-build baseline for the three components ADR-006
resets:

| Stream | Packages | Person-weeks |
|---|---|--:|
| `WP-ANA-01`…`07` | 7 | **27** |
| `WP-ATG-01`…`05` | 5 | **24** |
| `WP-GEN-01`…`11` | 11 | **43** |
| **Total** | **23** | **94** |

PLAN-001 §4.3 separately puts "sunk effort at risk" from a late fork decision at
**60+ person-weeks** — the subset already committed by the time a late decision
lands, not the whole 94.

### 4.1 What a fork could plausibly save

Judgements, in PLAN-001's own units. They are order-of-magnitude, not estimates
from a work breakdown.

| Package | Fresh | Fork saves | Why not more |
|---|--:|--:|---|
| `WP-ATG-02` symbolic execution adapter | 8w | **~8w** | The clearest win. UTBotCpp's KLEE integration is a superset of what this asks |
| `WP-ATG-01/04/05` lifecycle, targeted generation, bounds | 11w | ~4w | Validation port and capability-limit reporting (`TOOL-ATG-080`, `100`, `110`) are this project's own honesty requirements; no counterpart upstream |
| `WP-ANA-01/02/03` front-end, extraction, call graph | 12w | ~6w | The Fetcher does this — into UTBotCpp's internal model, not `TOOL-PAR-100`'s JSON. The seam has to be built anyway |
| `WP-GEN-06/07` stub core and behaviour | 9w | ~3w | Symbolic stubs are not `TOOL-STB-040`'s configured return value / sequence / callback, nor `TOOL-STB-050`'s call-count and argument recording. Upstream states it generates "only simple stubs, which do not depend on their arguments" |
| `WP-GEN-05` link closure | 2w | ~2w | The Bear `link_commands.json` fork is directly on point |
| **Total** | | **~23–28w** | |

**Every one of those weeks sits in P2 or P3.** PLAN-001 §5.2 is unusually
explicit about why that matters: 622 person-weeks compress into a 52-week
critical path, "**P1 costs 46 of those 52 weeks**," and "the programme is not
schedule-limited by its size; it is limited by one long serial chain at the
start." A fork saves effort that is not on the constraint.

### 4.2 What a fork costs

| Cost | Rough | Confidence |
|---|--:|---|
| LibTooling port, LLVM 14 → 18.1 | 8–15w | **Low** — LibTooling has no stable API (SDD-005 §5.3). Could be materially worse |
| Removing the Ubuntu assumption for native Windows/macOS hosts | 15–25w | **Low** — the server assumes Linux paths, generated Makefiles, and Bear, which interposes on process execution. This is not a port, it is a re-hosting |
| C harness TU: Unity/cmocka back-end, de-C++-ifying generation | 10–15w | Medium — the *emitter* is maybe 4w. Making the harness a C TU so `#include "foo.c"` works and `--wrap` seams apply reaches into KleeGenerator, Linker, and SourceToHeaderRewriter |
| GUI against a C++ gRPC server | +5–8w, plus permanent | Medium — `CMP-GUI` costs 85w either way, but ADR-001 §3.5's "in-process with a Python core eliminates an entire IPC layer" is forfeited, and a protocol boundary is added between the GUI and every capability |
| Coverage | **0 saved** | High — `CMP-COV` is built fresh regardless, now in C++ without gcovr |
| Ecosystem reuse | **inverted** | High — ADR-001 §2.2 rates Python's ecosystem reuse "**Enormous** — gcovr, lizard, StrictDoc, pyOCD, Twister are all Python and importable as libraries." In C++, every one becomes a subprocess |
| Learning ~1.75 MB of unfamiliar C++ with no upstream to ask | unquantified | — |
| Re-running ADR-001 | 3 spikes' worth | High — three "High"-confidence recommendations reopen simultaneously |

### 4.3 The arithmetic, stated plainly

A fork saves roughly **23–28 person-weeks**, all of it off the critical path, and
costs roughly **38–63 person-weeks** of new work, much of it *on* the critical
path — because the LLVM port and the re-hosting must land before `WP-ANA-01` can
proceed, lengthening precisely the serial chain PLAN-001 identifies as the
binding constraint. It also inverts the ecosystem argument that carries much of
ADR-001 §2's weight, and it reopens three decisions currently held at high
confidence.

Even granting generous error bars in the fork's favour, the sign does not change.

---

## 5. Decision

**Build fresh. Do not fork `UnitTestBot/UTBotCpp`.**

**Harvest it instead.** Its Apache-2.0 license permits verbatim reuse with
attribution, so this is a floor rather than a ceiling — but the value on offer is
design knowledge, and design knowledge transfers without a fork. Four specific
items, each with an owner:

1. **The client-server toolchain-isolation split.** Already adopted in ADR-001
   §2.4, correctly attributed there. No further action; this ADR confirms the
   attribution is accurate.
2. **The `KLEE_MODE` compile-time stub duality** (§2.3) — one emitted stub
   serving both symbolic exploration and concrete replay. → input to
   `WP-GEN-06`/`WP-GEN-07` and to **ADR-003**.
3. **`link_commands.json`** — a compilation database alone cannot determine link
   closure. → input to `WP-GEN-05` and `CMP-ING`; belongs in SDD-002's ingestion
   contract.
4. **The `c-syntax` support matrix as a pre-built risk list.** It records which C
   constructs symbolic execution declines, from a team that spent years finding
   out. Reading it costs an hour; rediscovering it costs part of `WP-ATG-02`'s
   eight weeks. → input to **ADR-003** and `WP-ATG-05`'s capability-limit
   reporting.

ADR-001 §2.2's table row already listed UTBotCpp under "prior art to read." This
decision's substantive content is that **that row was right, and it is the whole
of the correct relationship.**

### 5.1 Consequential effect on ADR-001

With ADR-006 resolved as "build fresh," ADR-001 §4's stated condition is
discharged. Its core-language recommendation — "**High** … ADR-006 (§5) is the one
remaining condition that could still overturn this" — no longer carries that
qualifier, and §4.1's first bullet ("If you decide to fork UTBotCpp → core becomes
C++ … and the whole analysis reorders") is closed rather than open. ADR-001 §4's
combined position can be accepted. SDD-001 §8's blocker clears, and SDD-001 can
proceed toward baseline on that axis.

---

## 6. Status

**Accepted, 2026-09-19.**

This was PLAN-001 §4.1's "last responsible moment at week 10" item, and SDD-001
§8's "one genuine blocker" — both now clear. `CMP-ANA`, `CMP-ATG`, and the
`CMP-GEN` framework back-end proceed on ADR-001 §2.4's Python + libclang path.
ADR-003 (symbolic execution engine) should be written next and should consume
§5's items 2 and 4 from this document.

---

## 7. Consequences

**Accepted.**

- `CMP-ANA`, `CMP-ATG`, and the `CMP-GEN` framework back-end are built fresh, on
  ADR-001 §2.4's Python + libclang path, with `TOOL-PAR-100`'s JSON model held as
  the seam.
- The project owns every line from day one — the argument that matters most given
  R-06 ("insufficient contributors; the project becomes one person's maintenance
  burden," likelihood High in ADR-001 §6). Onboarding a contributor into a
  codebase the team wrote is a different problem from onboarding one into 1.75 MB
  of C++ nobody present authored.
- Symbolic test generation is built from scratch when `WP-ATG-02` is reached in
  P3, at 8 person-weeks, without KLEE's floating-point, lazy-initialisation, or
  interactive-mode patches. **This is the real cost of the decision and it should
  not be minimised.** It is affordable because ADR-001 §5 records `ATG-020`/`030`
  as *(S/C, P3)* — optional, low priority, and per SDD-005 §5.7 in a lane where
  "nothing … is production-grade for certification evidence."
- SDD-005 §5.7's warning stands undisturbed: KLEE forces a second, older LLVM
  alongside CMP-ANA's 18.1. UTBotCpp does not solve that problem; §2.3 shows it
  solves the *whole toolchain* at LLVM 14, which is the same problem one version
  further from where this project needs to be.
- ADR-001 §2.4's Docker sentence and §5's ADR-006 entry need the corrections in
  §3.1.

**Rejected — what is given up.**

- A working KLEE pipeline, today. The largest single concession.
- A patched KLEE with capabilities (symbolic floats, lazy initialisation) that
  are research contributions and will not be reproduced cheaply.
- A shipped, demonstrable artifact to point at while the fresh build is still
  months from a first report.

**Not affected either way.** `CMP-COV`, `CMP-EXT`, `CMP-TRC`, `CMP-REP`,
`CMP-QUA`, `CMP-MIG`, `CMP-PKG` and `CMP-GUI` — the majority of the specification
by requirement count — receive nothing from a fork. That is itself a finding:
UTBotCpp overlaps roughly a quarter of this project's scope, and the overlap is
concentrated in its lowest-priority quarter.

---

## 8. What would reverse this

Ordered by plausibility. Three of the four are "become a different product," and
that is the honest summary of the fork's fit.

1. **If `ATG-020`/`030` were promoted from *(S/C, P3)* to a defining P1/P2
   capability.** The strongest genuine reversal, and the one a skeptic should
   press. It is a product-strategy question, not a technical one — see §9.1.
2. **If the standalone GUI were abandoned in favour of an IDE plugin.** `CMP-GUI`'s
   85 person-weeks would evaporate and UTBotCpp's client-server, plugin-fronted
   shape would fit rather than fight. This contradicts ADR-001 §3.3's explicit
   reasoning about what "feels like a product" to the target user.
3. **If target execution (`TOOL-TGT-*`) were dropped and the tool were host-only.**
   Collision #1 disappears. So does much of the reason to prefer this tool over
   the incumbents.
4. **If a maintainer resumed UTBotCpp and moved it to a current LLVM** — merging
   PR #688 and successors. This would soften §2.2 but leave collisions #1, #2,
   #5, #6, #7 and #8 untouched. It is the least load-bearing of the four.

---

## 9. Confidence, and what is not settled

### 9.1 Confidence: **High**

Higher than the "strategic judgement" framing this question usually invites, and
the reason is specific.

The trade this decision *appears* to present — a working head start against
long-term codebase ownership — is real in general and would deserve genuine
hesitation if the head start landed on something the specification cared about
most. It does not. **UTBotCpp's one great asset is automatic test generation, and
this specification files automatic test generation as *(S/C, P3)*.** That is not a
judgement call; it is a fact about SRS-001, recorded in ADR-001 §5 and PLAN-001's
phase table. The asset sits behind the lowest-priority requirement band in the
document, while the collisions land on `TOOL-TGT-*` (P3 but mandatory),
`TOOL-COV-*`, `TOOL-HAR-060` (M), `TOOL-INS-030` (M) and `TOOL-UIX-040` (M).

Where genuine judgement does enter, it is named:

- **Effort figures in §4 are order-of-magnitude**, derived from PLAN-001's units
  by inspection. Nobody has built either path. The *ratio* is what carries the
  argument, and it would have to be wrong by roughly 2× in the fork's favour to
  change the sign.
- **"Own your codebase" versus "inherit a working one"** is a values question.
  This ADR takes a position — ownership, given R-06's High likelihood and no
  upstream to share the load — rather than presenting both sides. A project with
  a large team and an urgent demo deadline could reasonably weigh it differently,
  and should say so explicitly if it does.

### 9.2 Evidence quality — flagged honestly

Following SDD-005 §10.2's practice of marking unverified claims rather than
letting them pass as findings.

| Claim | Quality |
|---|---|
| License Apache-2.0; LLVM 14 pin; GoogleTest output; Ubuntu-only server; line-coverage-only; commit/release/PR dates | **Verified** — GitHub API, `.gitmodules`, `Dockerfile_base`, and named wiki pages, read 2026-09-05 |
| "Dormant / unmaintained" | **Inference**, not a maintainer statement. There is no archive banner and no deprecation notice. Five independent signals agree (§2.2), and no public status statement was found, but a maintainer could return |
| The `c-syntax` support matrix (collision #7) | **Undated wiki content**, describing *test-generation* support, not *parse* support. Not independently exercised by this project. The distinction matters: libclang parses `void*` fine — what is unsupported is generating tests for it |
| "KLEE 2.2 base" (wiki `klee-patches`) | **Possibly stale.** The KLEEF submodule tracks `UnitTestBot/klee`, itself pushed 2026-04-18. The wiki text may predate the submodule. `UnitTestBot/klee`'s SPDX identifier resolves to `NOASSERTION` and must be established before any KLEEF-derived code is retained |
| §4.1/§4.2 person-week figures | **Judgement**, not measurement. §9.1 states the tolerance |
| Determinism friction (below) | **Inference**, not measured |

One inference worth recording despite being unmeasured: `TOOL-NFR-060` requires
all tool outputs to be deterministic and reproducible given identical inputs.
UTBotCpp drives a time-bounded search — KLEE plus an SMT solver plus a
`bcov_check_interval` timeout. Time-bounded solver-driven search is not
reproducible by construction. This is a design-level concern about any symbolic
back-end, not a UTBotCpp defect, and it applies equally to the fresh-build path's
`WP-ATG-02`. It belongs in **ADR-003**, which should decide how generated cases
are frozen into the deterministic evidence chain (SDD-005 §5.7's rule — "the
engine never enters the evidence chain" — is the right starting point).

### 9.3 Not verified, and would not change the decision

Recorded so a reader knows the boundary of the work: the server was not built or
run; no generated harness was inspected; no test project was put through the
pipeline; the C++ source was not read beyond its size and structure; and no
maintainer was contacted. Each would sharpen §4's numbers. None would touch
collisions #1, #2, #5, #6 or #8, which are the ones doing the work — they follow
from documented, dated, verified properties of the project, not from how well it
performs.

---

## 10. Summary

| | |
|---|---|
| **Decision** | Build fresh; harvest four design ideas (§5) |
| **Confidence** | **High** |
| **Strongest evidence for** | The fork's one great asset — end-to-end KLEE-based test generation — serves `ATG-020`/`030`, which SRS-001 files as *(S/C, P3)*. It costs an inherited LLVM-14 LibTooling codebase, an Ubuntu-resident server, a C++ GoogleTest harness, line-only coverage, no target execution, and no GUI, to accelerate the lowest-priority band in the specification |
| **Strongest evidence against** | Apache-2.0. There is no license obstacle, no patent friction, and exact alignment with ADR-005's own recommendation — the objection that most often kills a fork is simply absent here, and roughly 23–28 person-weeks of genuinely hard, genuinely working KLEE integration are being declined |
| **Discharges** | ADR-001 §4's outstanding condition; SDD-001 §8's blocker; PLAN-001 §4.2's "decision that cannot wait" |
| **Feeds** | ADR-003 (§5 items 2 and 4; §9.2's determinism note) |
| **Requires** | Corrections to ADR-001 §2.4 and §5 (§3.1) |
