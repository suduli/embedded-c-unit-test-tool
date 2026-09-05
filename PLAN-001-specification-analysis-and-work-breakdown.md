# PLAN-001 — Specification Analysis and Work Breakdown

**Status:** Draft v0.1 — analysis, not a commitment
**Upstream:** [`SRS-001`](SRS-001-requirements.md) v0.1 (draft, not baselined) · [`ADR-001`](ADR-001-architecture-decisions.md) (analysis, no decision recorded) · [`SDD-001`](design/SDD-001-architecture.md) · [`SDD-002`](design/SDD-002-interfaces.md) · [`design/trace/design-elements.yaml`](design/trace/design-elements.yaml)
**Covers:** all 323 SRS-001 requirements
**Method:** specification-based, in three layers — specification analysis, work breakdown, and specification-based test design

---

## 1. Purpose and how to read this

This document does three things with SRS-001, in order, and each layer feeds the next:

| Layer | Question it answers | Where |
|---|---|---|
| **1 — Specification analysis** | Is the specification sound enough to build from? Where is it ambiguous, untestable, internally inconsistent, or blocked on a decision? | §3 |
| **2 — Work breakdown** | What are the units of work, in what order, with what dependencies and exit criteria? | §5 |
| **3 — Specification-based test design** | How is each requirement verified — by which black-box technique, against which observable? | §6 |

It does **not** re-decide anything SRS-001, ADR-001 or the SDD set already decides, and it does not modify the
authoritative register in `design/trace/design-elements.yaml`. Where this document and that register disagree,
the register wins and this document is defective — the same rule SRS-001 and the SDD set already operate under.

### 1.1 The standing decision assumption

ADR-001 records **no decision**. This analysis proceeds on the position ADR-001 itself recommends, so that the
work breakdown can be concrete:

| Decision | Assumed position | ADR-001 confidence |
|---|---|---|
| Qualification scope | Tier 1 (discipline) in v1.0, Tier 2 (documentation) in v1.1, Tier 3 never. Target *qualifiable*, not *qualified*. | High |
| Core language | Python, with the `TOOL-PAR-100` JSON analysis model held as an inviolable seam permitting a later C++ LibTooling analyzer | Moderate-high |
| GUI | PySide6 (Qt), standalone desktop, dynamically linked, LGPL recorded in the SBOM | Moderate-high |

**57 of 183 work packages are marked ADR-sensitive (●)** — their shape changes if that position is reversed.
§4.3 gives the blast radius. This assumption is a planning device, not a decision: nothing here authorises
closing ADR-001, and §4 states what it costs to be wrong.

### 1.2 What is generated versus written

The register (§5.3), the phase rollup (§5.1), the technique table (§6.2) and Appendix A are **generated from a
single work-package dataset** and cross-checked against `design/trace/requirement-matrix.csv`. They cannot
disagree with each other. The audit in §7 is arithmetic, not assertion. The prose is written.

---

## 2. The specification at a glance

323 requirements across 24 categories. Independently counted from `SRS-001-requirements.md` and reconciled
against `design/trace/requirement-matrix.csv` — both yield 323, with no id in one and absent from the other.

| Attribute | Distribution |
|---|---|
| **Priority** | Must 199 · Should 107 · Could 15 · Future 2 |
| **Phase** | P1 35 · P2 145 · P3 101 · P4 40 · deferred 2 |
| **Verification** | Test 231 · Inspection 52 · Demonstration 24 · Analysis 14 · n/a 2 |

Must-priority requirements are not front-loaded: **P1 33, P2 99, P3 48, P4 19**. Two thirds of the
non-negotiable scope sits at P2 or later, which is the first sign that "MVP" here means *thin*, not *complete*.

### 2.1 Requirement load by category

| Cat | Total | M | S | C | F | P1 | P2 | P3 | P4 | T | I | D | A |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| UIX | 40 | 27 | 10 | 1 | 2 | 2 | 22 | 10 | 4 | 31 | 3 | 2 | 2 |
| AIF | 21 | 14 | 5 | 2 | 0 | 0 | 0 | 19 | 2 | 15 | 3 | 1 | 2 |
| ING | 19 | 8 | 9 | 2 | 0 | 4 | 14 | 1 | 0 | 16 | 1 | 2 | 0 |
| NFR | 19 | 12 | 7 | 0 | 0 | 4 | 14 | 1 | 0 | 6 | 6 | 4 | 3 |
| COV | 17 | 12 | 5 | 0 | 0 | 5 | 0 | 9 | 3 | 15 | 2 | 0 | 0 |
| REP | 15 | 11 | 4 | 0 | 0 | 3 | 3 | 2 | 7 | 12 | 2 | 0 | 1 |
| STB | 14 | 9 | 5 | 0 | 0 | 0 | 13 | 1 | 0 | 14 | 0 | 0 | 0 |
| TCD | 14 | 8 | 5 | 1 | 0 | 1 | 11 | 2 | 0 | 12 | 1 | 0 | 1 |
| HAR | 13 | 9 | 3 | 1 | 0 | 0 | 12 | 1 | 0 | 11 | 1 | 0 | 1 |
| PAR | 13 | 7 | 5 | 1 | 0 | 0 | 12 | 1 | 0 | 12 | 0 | 0 | 1 |
| SEC | 12 | 10 | 2 | 0 | 0 | 0 | 8 | 4 | 0 | 5 | 5 | 2 | 0 |
| TGT | 12 | 8 | 3 | 1 | 0 | 0 | 0 | 12 | 0 | 9 | 0 | 1 | 2 |
| ATG | 11 | 5 | 5 | 1 | 0 | 0 | 0 | 11 | 0 | 9 | 1 | 1 | 0 |
| INS | 11 | 9 | 2 | 0 | 0 | 0 | 10 | 1 | 0 | 4 | 1 | 6 | 0 |
| PRJ | 11 | 9 | 2 | 0 | 0 | 0 | 8 | 1 | 2 | 7 | 4 | 0 | 0 |
| MIG | 10 | 4 | 5 | 1 | 0 | 0 | 4 | 4 | 2 | 9 | 1 | 0 | 0 |
| QUA | 10 | 7 | 2 | 1 | 0 | 0 | 0 | 0 | 10 | 1 | 9 | 0 | 0 |
| TCH | 10 | 5 | 4 | 1 | 0 | 2 | 0 | 8 | 0 | 8 | 1 | 1 | 0 |
| TRC | 10 | 4 | 5 | 1 | 0 | 0 | 0 | 0 | 10 | 10 | 0 | 0 | 0 |
| EXE | 9 | 5 | 4 | 0 | 0 | 7 | 2 | 0 | 0 | 9 | 0 | 0 | 0 |
| PLG | 9 | 5 | 4 | 0 | 0 | 0 | 4 | 5 | 0 | 5 | 2 | 1 | 1 |
| CBT | 8 | 2 | 5 | 1 | 0 | 0 | 2 | 6 | 0 | 7 | 1 | 0 | 0 |
| CIC | 8 | 4 | 4 | 0 | 0 | 4 | 3 | 1 | 0 | 4 | 1 | 3 | 0 |
| LIC | 7 | 5 | 2 | 0 | 0 | 3 | 3 | 1 | 0 | 0 | 7 | 0 | 0 |

Three shapes in this table drive everything downstream:

- **UIX is 12% of the specification and the single largest category**, is 27 Must, and is gated on the one
  ADR-001 sub-decision with no fallback (§4.2). It also contains the component ADR-001 §6 names its own highest
  schedule risk.
- **QUA, TRC and LIC contain almost no tests** — 9 of 10 QUA requirements and all 7 LIC requirements verify by
  inspection. These are document-and-argument deliverables, not code, and they are systematically
  under-estimated when a plan counts requirements rather than reading them.
- **AIF, ATG, TGT and TRC have no P1 or P2 content at all.** Four whole subsystems begin at P3 or later.

---

## 3. Layer 1 — Specification analysis

### 3.1 Criteria applied

Every requirement was judged against nine defect classes. A requirement that is terse but unambiguous is not a
defect, and a technology choice the SRS defers *on purpose* (it lists nine such deferrals in §27) is
`DECISION-BLOCKED` at most, never `AMBIGUOUS`.

`AMBIGUOUS` · `UNTESTABLE` · `UNMEASURABLE` · `INCOMPLETE` · `CONFLICT` · `REDUNDANT` · `GAP` ·
`DECISION-BLOCKED` · `MISALLOCATED`

### 3.2 Findings

| # | Class | Severity | Requirements | Summary |
|---|---|:--:|---|---|
| **F-01** | CONFLICT | **blocker** | 35 P1 reqs vs HAR-\*, PAR-\* | The P1 host-based MVP is not self-contained: it cannot be delivered without 14 requirements the SRS phases at P2 |
| **F-02** | DECISION-BLOCKED | **blocker** | PAR-\*, ATG-\*, HAR-060 | ADR-006 (fork UTBotCpp vs build fresh) is unresolved and is not covered by the ADR-001 assumption |
| **F-03** | CONFLICT | major | TCD-010 vs HAR-010 | `TCD-010` (M, **P1**) requires test cases "against the generated harness"; all harness generation is P2 |
| **F-04** | CONFLICT | major | UIX-030 vs UIX-150/160/170 | `UIX-030` (M, **P2**) promises a GUI supporting "the complete test workflow — … test authoring …"; every test-authoring requirement is P3 |
| **F-05** | CONFLICT | major | COV-150 vs COV-140 | `COV-150` is **Must, P3** and constrains `COV-140`, which is **Should, P4**. A Must depends on a Should scheduled a phase later |
| **F-06** | MISALLOCATED | major | TCH-080 | Allocated to `CMP-TCH` (L1) but describes build orchestration, which is `CMP-BLD` (L3). As written it implies an upward dependency the layering rule forbids |
| **F-07** | UNTESTABLE | major | COV-150, CBT-040 | Recorded verification **I** (inspection), but both state dynamic, observable behaviour — justification expiry and partial-run disclosure. Inspection cannot verify either |
| **F-08** | UNMEASURABLE | major | NFR-050 | Recorded verification **A** (analysis) but states concrete thresholds (500 translation units, 10,000 test cases). A Must scale requirement with numbers in it is a test, not an argument |
| **F-09** | INCOMPLETE | major | COV-100 | Recorded **T**, but "retrieve coverage from bare-metal targets with no filesystem and no OS" is only demonstrable with hardware or a simulator in the loop. The SRS never says which satisfies it |
| **F-10** | GAP | major | — | **No requirement protects the integrity of generated evidence.** `SEC-010` signs *releases*; nothing signs or hashes the verification report or the archived record from `PRJ-100`, which is the artifact an auditor actually relies on |
| **F-11** | GAP | major | COV-010/020/050 | **No requirement addresses optimisation level or object-code coverage.** Structural coverage is measured on an instrumented, typically unoptimised build; the software that ships is optimised. DO-178C Level A requires this gap to be addressed explicitly |
| **F-12** | DECISION-BLOCKED | major | COV-050/060/090 | MC/DC form (masking vs unique-cause) is open (SRS §27 q2). `COV-090` permits *documenting the gap* instead of closing it — acceptable to some certification authorities, not all |
| **F-13** | AMBIGUOUS | minor | ING-190, TCD-030 | Both mandate "plain-text, version-controllable" without naming a format; SRS §27 q6 and q8 ask whether they are the same artifact. Blocks nothing until `WP-TCM-02` starts |
| **F-14** | REDUNDANT | minor | NFR-110 vs INS-020 | "Installation shall not require administrative privileges" appears twice, allocated to two components (`CMP-CORE`, `CMP-PKG`) |
| **F-15** | INCOMPLETE | minor | HAR-100, STB-120 | Both promise to "preserve user modifications … or report conflicts" without defining what makes a user region untenable. `DSN-GEN-070` defines the contract; the SRS does not |
| **F-16** | CONFLICT | **blocker** | LIC-010 | **The repository contradicts its own P1 requirement today.** `LIC-010` (M, **P1**, I) requires the tool's source under a *permissive* licence; `LICENSE`, `LICENSEES` and the README all state **AGPL-3.0**, the strongest copyleft available |

**F-16 deserves separate mention** because it is the only finding that is already false in the repository
rather than merely unresolved in the specification. `LIC-010` is Must-priority, P1, and verified by
inspection — so it is checkable today, and today it fails. The tension is sharpened by `LIC-020`, which
requires *strong-copyleft dependencies* to be held at process boundaries and never linked: the project applies
a copyleft-avoidance rule to everything it consumes while being AGPL itself. That is a defensible position for
a product, but it is not the position `LIC-010` states, and one of the two has to move. It is also the finding
with the largest commercial consequence (R-8): AGPL is the licence most likely to stall legal review at
exactly the automotive, aerospace and defence users this tool targets. Resolving it costs nothing now and
becomes progressively harder as the contributor set grows.

Two positives worth recording, because they are the cases most specifications get wrong:

- The two `Future` requirements (`UIX-390`, `UIX-400`) are correctly excluded from allocation and correctly
  carry no phase or verification method, exactly as `design-elements.yaml` requires.
- The **"nothing overclaimed"** rule in SDD-001 §7 — six independent elements ensuring *verified*,
  *unverified* and *asserted-but-unreviewed* can never be confused — is the strongest thing in this design.
  F-07 is a defect precisely because it weakens two members of that family.

### 3.3 F-01 in detail: the P1 phase boundary does not hold

This is the finding with the largest planning consequence, so it is stated quantitatively rather than as an
opinion. Building the dependency closure of every P1 work package and asking which non-P1 packages are pulled
in with it gives:

| | |
|---|--:|
| P1 work packages declared | 22 |
| Non-P1 packages they cannot start without | 6 |
| Additional effort those carry | 23 person-weeks |
| **Requirements the SRS phases after P1 that P1 cannot ship without** | **14** |

`HAR-010` `HAR-020` `HAR-040` `HAR-050` · `PAR-010` `PAR-020` `PAR-030` `PAR-040` `PAR-050` `PAR-100`
`PAR-110` · `NFR-090` `NFR-180` · `PLG-010`

The mechanism is direct. `EXE-010` (M, P1) builds and executes *the test harness*. `TCD-010` (M, P1) authors
test cases *against the generated harness*. `COV-010`/`COV-020` (M, P1) measure coverage of a running harness.
But every `HAR-*` requirement is P2, and harness generation consumes the analysis model, so every `PAR-*`
requirement it depends on is P2 as well. **P1 as written describes running a harness that P1 provides no way to
produce.**

The real P1 scope is therefore **49 requirements, not 35** — 40% larger — and 65 declared person-weeks become
88. Two resolutions are available, and this is a decision for the SRS owner, not for this plan:

1. **Re-phase.** Move the 14 requirements above into P1. Honest, and makes the phase model self-consistent.
2. **Redefine P1.** Accept a hand-written harness for P1 and amend `TCD-010` to drop "the generated harness".
   Keeps P1 genuinely small, but it is then no longer the MVP of *this* tool — it is a test runner.

Recommendation: **option 1**. Option 2 produces a P1 that demonstrates nothing a developer could not get from
Unity and a Makefile, which forfeits the only purpose an MVP has.

---

## 4. Decision dependencies

### 4.1 The open decision register

Ten open decisions, from three sources, deduplicated. Several SRS §27 open questions *are* ADRs; where they
are, the ADR is authoritative and the §27 entry is a restatement.

| Decision | Source | Gates | Last responsible moment |
|---|---|---|---|
| **ADR-006** — fork UTBotCpp or build fresh | ADR-001 §5, SDD-001 §8 | `CMP-ANA`, `CMP-ATG`, `CMP-GEN` framework back-end — **whole components, not elements** | **Now.** Before `WP-ANA-01` starts (week 10) |
| **ADR-001 §1** — qualification scope | ADR-001, §27 q5 | All 8 `WP-QUA-*`; the evidence shape of `WP-REP-05` | Before `WP-QUA-01` (P4) — but see §4.4 |
| **ADR-001 §2** — core language | ADR-001, §27 q4 | `WP-ANA-01`, and the packaging shape of `WP-PKG-01` | Before `WP-ANA-01` (week 10) |
| **ADR-001 §3** — GUI technology | ADR-001, §27 q1 | All 22 `WP-GUI-*` (33 requirements) | Before `WP-GUI-01` (P2) |
| **ADR-002** — project/test data format | ADR-001 §5, §27 q6, q8 | `WP-TCM-02`, `WP-PRJ-01` | Before `WP-PRJ-01` (week 3) |
| **ADR-003** — symbolic execution engine | ADR-001 §5, §27 q3 | `WP-ATG-02`, `WP-ATG-03` | Before `WP-ATG-02` (P3) |
| **ADR-004** — coverage backend strategy | ADR-001 §5 | `WP-COV-01` and every downstream coverage package | Before `WP-COV-01` (week 35) |
| **ADR-005** — license selection | ADR-001 §5 | `WP-PKG-07` | Before first public release |
| **ADR-007** — distribution and packaging | ADR-001 §5 | `WP-PKG-01` | Before `WP-PKG-01` (P2) |
| **§27 q2** — MC/DC form | SRS §27 | `WP-COV-05`, `WP-COV-10`, `WP-REP-04` | Before `WP-COV-05` (P3) |
| **§27 q9** — debugger front-end | SRS §27, SDD-001 §8 | `WP-EXH-04`, `WP-GUI-15` | Before `WP-EXH-04` (P2) |

### 4.2 Decision order, and one correction to ADR-001

ADR-001 §0 argues qualification scope must be decided **first**, because it reframes the other two. Against the
dependency structure that claim is **half right, and the half that is wrong matters**.

Qualification scope is genuinely upstream *in reasoning* — it is what makes "Python is fast enough to be
auditable" an acceptable sentence. But it gates no work package before P4, whereas ADR-006 gates `WP-ANA-01`
at week 10 and ADR-002 gates `WP-PRJ-01` at week 3. Ordered by last responsible moment rather than by
rhetorical dependency:

**ADR-002 (week 3) → ADR-006 (week 10) → ADR-001 §2 (week 10) → ADR-001 §3 (P2 start) → ADR-004 (week 35) → the rest.**

ADR-001 §1 (qualification scope) should still be *reasoned about* first, and recorded early because it is
cheap to record and expensive to reopen. But **ADR-006 is the decision that cannot wait**, and ADR-001 does not
say so — SDD-001 §8 does, calling it "the one genuine blocker" and noting it "must be resolved before SDD-001
is baselined". A fork decision arriving after implementation starts invalidates `CMP-ANA`, `CMP-ATG` and the
`CMP-GEN` framework back-end simultaneously — three components, 53 requirements, and the entire assumed
language position, because a fork resets the core to C++.

**The user's standing assumption covers ADR-001 and therefore does not cover this.** Planning on ADR-001's
recommended position while ADR-006 remains open is planning on sand: choosing Python is only coherent if the
fork question is already answered "build fresh".

### 4.3 Blast radius if the assumption is reversed

| Reversal | Work packages invalidated | Sunk effort at risk | Recoverable |
|---|--:|--:|---|
| Core language → C++ or Rust | `WP-ANA-01/02/03/05/06`, `WP-CORE-03`, `WP-PKG-01` | 30 person-weeks | The `TOOL-PAR-100` JSON model seam is what makes this survivable: downstream L2–L5 packages consume the model, not the analyzer. **Hold that seam absolutely.** |
| GUI → non-Qt | All 22 `WP-GUI-*` | 85 person-weeks | Fully. `CMP-GUI` holds no capability of its own; its data contract is the test case model. A technology change is an L5 rewrite and nothing else moves |
| Qualification → Tier 2/3 in v1.0 | `WP-QUA-01..08`, `WP-REP-05`, `WP-AIF-12` | 33 person-weeks, plus unbudgeted certification-body engagement | Partly. Tier 2 is mostly additional documentation over the same evidence; Tier 3 is a different project |
| **ADR-006 → fork UTBotCpp** | `CMP-ANA`, `CMP-ATG`, `CMP-GEN` back-end — **and the language decision with them** | 60+ person-weeks | **Not absorbed by the design.** SDD-001 §8 says so explicitly |

### 4.4 The three validation spikes

ADR-001 §4.2 proposes three spikes. They are work packages here (`WP-SPIKE-01..03`, 4 person-weeks total),
and each needs a pass criterion sharper than "it worked":

| Spike | Must demonstrate | Pass criterion | Unblocks |
|---|---|---|---|
| `WP-SPIKE-01` | `PAR-030`–`PAR-060` against a real embedded codebase using python-clang | Function, type, global and call-graph extraction complete on a ≥20 kLOC embedded project with vendor headers, **with no construct requiring a CFG**. If a CFG is needed, §2.4 of ADR-001 fails and the C++ analyzer moves from "later" to "now" | ADR-001 §2, `WP-ANA-05` |
| `WP-SPIKE-02` | The type-aware nested test data editor in PySide6 against a struct-heavy interface | A 4-deep nested struct containing a union, a function-pointer member and a fixed array is editable at every level, type-validated, with enum constants by name, at interactive latency | ADR-001 §3, `WP-GUI-11` |
| `WP-SPIKE-03` | PyInstaller-bundled PySide6 + libclang on a clean Windows machine with no Python | Installs and runs **without administrative privileges**, and is not quarantined by default endpoint security. Record size and cold-start time | ADR-001 §2/§3, `WP-PKG-01` |

`WP-SPIKE-02` is the one that matters most. ADR-001 §6 (R-02) and SDD-001 §9 both name the nested editor the
schedule driver, and `WP-GUI-11` is the single largest work package in this plan at 8 person-weeks. It should
be prototyped **before the architecture is frozen**, not after `WP-GUI-10` has committed to an editor model.

---

## 5. Layer 2 — Work breakdown

### 5.1 Method and shape

**180 work packages plus 3 validation spikes**, organised into 24 work streams that align one-to-one with the
components in SDD-001 §5. A work package is a cohesive, independently deliverable capability — not one per
requirement (that would be 321 tasks with no structure) and not one per SRS category (that would be 24 buckets
with no schedule). Every non-Future requirement lands in **exactly one** package; §7 proves it arithmetically.

Three rules were applied and are worth stating because they are where a work breakdown usually goes wrong:

1. **Dependencies obey the layering rule.** A package may depend on its own layer, a lower one, or a
   cross-cutting component — and only `CMP-PLG` and `CMP-SEC` are cross-cutting. Every edge was checked
   mechanically; the audit reports **zero upward violations and zero cycles**.
2. **Three kinds of dependency are distinguished**, because conflating them is what produces phantom layering
   violations:
   - *code* (260 edges) — a real build-order dependency, bound by the layering rule
   - *port-mediated* `^` (2 edges) — an inverted dependency bound at composition time. `WP-ATG-01` and
     `WP-ATG-04` need to build, run and measure, all of which live above L2. They declare
     `TestValidationPort` (`DSN-ATG-110`) rather than depending upward, exactly as SDD-001 §4.3 requires
   - *schedule-only* `~` (10 edges) — one package cannot be **demonstrated** until another exists, but no code
     depends on it. `WP-CORE-05` (performance envelope) cannot be measured before there is something to
     measure; that is not a dependency of `CMP-CORE` on `CMP-GEN`
3. **Exit criteria are observable.** "Implemented", "working" and "code complete" were rejected. §5.4 gives
   the pattern.

### 5.2 Phase rollup and calendar

| Phase | Work packages | Requirements | Effort (person-weeks) | Cumulative calendar (weeks) |
|---|--:|--:|--:|--:|
| P0 — validation spikes | 3 | 0 | 4 | 2 |
| P1 — host-based MVP | 22 | 52 | 65 | 46 |
| P2 — automation layer | 64 | 132 | 215 | 47 |
| P3 — safety coverage and on-target | 66 | 101 | 239 | 52 |
| P4 — traceability, reporting, qualification | 28 | 36 | 99 | 52 |
| **Total** | **183** | **321** | **622** | **52** |

The calendar column is the critical path at unlimited parallelism, not the sum of the effort column. Read the
two together and the shape of the programme is clear:

- **622 person-weeks of effort compress into a 52-week critical path** — about **12 engineers** to stay on it.
  A smaller team does not take 52 weeks; it takes proportionally longer, because the path is already saturated.
- **P1 costs 46 of those 52 weeks.** Not because P1 is large, but because it is *deep*: the chain from
  determinism through the project store, ingestion, parsing, the analysis model, harness generation, build,
  execution and coverage to the first report is 12 packages long and almost entirely serial.
- **P2 adds one week of calendar for 215 person-weeks of effort.** Once the spine exists, the work fans out.
  Peak concurrency is 25 live work packages around week 43.

That asymmetry is the single most useful planning fact in this document. **The programme is not
schedule-limited by its size; it is limited by one long serial chain at the start.** Effort spent shortening
that chain is worth several times the same effort spent anywhere else.

### 5.3 The critical path

| # | WP | Phase | Effort | Starts wk | Capability |
|--:|---|:--:|--:|--:|---|
| 1 | `WP-CORE-01` | P1 | 3w | 0 | Determinism, source immutability, output confinement |
| 2 | `WP-PRJ-01` | P1 | 4w | 3 | Plain-text schema-versioned project store |
| 3 | `WP-ING-01` | P1 | 3w | 7 | Compilation database ingestion |
| 4 | `WP-ANA-01` | P2 ⚠ | 4w | 10 | C front-end binding and dialect support |
| 5 | `WP-ANA-02` | P2 ⚠ | 5w | 14 | Interface and type extraction |
| 6 | `WP-ANA-04` | P2 ⚠ | 3w | 19 | Analysis model persistence and schema versioning |
| 7 | `WP-GEN-01` | P2 ⚠ | 5w | 22 | Harness generation core |
| 8 | `WP-BLD-01` | P1 | 4w | 27 | Host build orchestration |
| 9 | `WP-EXH-01` | P1 | 4w | 31 | Host execution and result reporting |
| 10 | `WP-COV-01` | P1 | 4w | 35 | Statement and branch coverage |
| 11 | `WP-COV-02` | P1 | 4w | 39 | Coverage merge and per-test attribution |
| 12 | `WP-REP-02` | P1 | 3w | 43 | JUnit and Cobertura/LCOV output |

⚠ marks the four packages that carry F-01: **a third of the path to the P1 MVP is work the SRS phases at P2.**

Two observations for anyone trying to shorten this:

- **Steps 4–7 are the compressible part.** They are 17 of the 46 weeks and they are pure analysis-and-generation
  work with a clean input (the compilation database) and a clean output (the JSON model). They parallelise
  internally better than the table suggests, and `WP-SPIKE-01` de-risks them for one week.
- **Steps 1–3 are not compressible and must not be rushed.** Determinism, output confinement and the on-disk
  project format are the properties every later package assumes and none can retrofit. `WP-CORE-01` is three
  weeks at the very front of a 52-week programme; it is the cheapest insurance available.

### 5.4 Exit criteria pattern

Each package's exit criterion is written so a reviewer who did not do the work can falsify it. Examples from
the foundation and the certification-critical packages:

| WP | Exit criterion |
|---|---|
| `WP-CORE-01` | Two runs from identical inputs on different machines produce byte-identical generated artifacts; a write attempted outside the configured output root fails and is reported; no user source file's mtime or content changes across a full run |
| `WP-ANA-04` | A model emitted by the analyzer validates against its published schema, carries a schema version, and is rejected with a named reason by a consumer pinned to an incompatible version |
| `WP-GEN-04` | Regenerating a harness whose user region is still valid preserves it byte-for-byte; regenerating one whose UUT signature changed incompatibly reports a conflict and writes nothing |
| `WP-COV-05` | For a decision with N conditions, the report names which conditions were unexercised true and unexercised false, and every report states the MC/DC form obtained and the compiler mechanism that produced it |
| `WP-COV-09` | Editing a source line under an accepted justification invalidates that justification, and the next report shows the construct as uncovered rather than justified |
| `WP-EXH-02` | A test case that segfaults, one that hangs past the timeout, and one that calls `abort()` are each reported as a failure with the remaining cases still executed |
| `WP-REP-01` | Two different renderers over one persisted report model cannot disagree on any test's status or any coverage figure; re-running the renderer produces byte-identical output excluding timestamps |
| `WP-QUA-07` | Documentation states, in one place, what qualification evidence is provided and what remains the user's responsibility, and no other document claims more |

### 5.5 The work package register

`Start` is the earliest phase the package may begin. `Depends on` uses `~` for schedule-only and `^` for
port-mediated edges, per §5.1. `●` marks ADR-sensitivity.

#### Validation spikes

3 work packages · 0 requirements · 4 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-SPIKE-01` | CFG sufficiency spike: python-clang against real embedded code | — | P0 | 1w | — | — | ● |
| `WP-SPIKE-02` | Nested type-aware test data editor spike in PySide6 | — | P0 | 2w | — | — | ● |
| `WP-SPIKE-03` | PyInstaller distribution spike onto clean Windows | — | P0 | 1w | — | — | ● |

#### L0 — Platform and Persistence

13 work packages · 33 requirements · 38 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-CORE-01` | Determinism, source immutability and output confinement | CMP-CORE | P1 | 3w | NFR-060 NFR-070 NFR-080 PRJ-050 PRJ-080 | — |  |
| `WP-CORE-02` | Structured error model, fail-safe termination and cancellation | CMP-CORE | P2 | 3w | NFR-090 NFR-180 | CORE-01 |  |
| `WP-CORE-03` | Platform baseline and offline guarantee | CMP-CORE | P1 | 2w | NFR-010 NFR-020 NFR-100 | — | ● |
| `WP-CORE-04` | Provenance record and version identification | CMP-CORE | P2 | 2w | QUA-060 INS-110 | CORE-01 |  |
| `WP-CORE-05` | Performance, scale and memory envelope | CMP-CORE | P2 | 4w | NFR-030 NFR-040 NFR-050 NFR-150 | ~ANA-04 ~GEN-01 | ● |
| `WP-CORE-06` | Logging and diagnostic bundle | CMP-CORE | P2 | 2w | NFR-130 NFR-160 | CORE-02 SEC-04 |  |
| `WP-CORE-07` | User documentation and text externalisation | CMP-CORE | P2 | 4w | NFR-120 NFR-190 | — |  |
| `WP-CORE-08` | Self-verification of the tool's own source | CMP-CORE | P2 | 3w | NFR-140 NFR-170 | ~EXH-01 ~COV-01 | ● |
| `WP-PRJ-01` | Plain-text schema-versioned project store | CMP-PRJ | P1 | 4w | PRJ-010 PRJ-020 PRJ-070 UIX-320 CIC-080 | CORE-01 | ● |
| `WP-PRJ-02` | Diff-stable sharded storage for concurrent edit | CMP-PRJ | P2 | 3w | PRJ-030 PRJ-060 | PRJ-01 |  |
| `WP-PRJ-03` | Schema migration with explicit confirmation | CMP-PRJ | P2 | 3w | PRJ-040 | PRJ-01 |  |
| `WP-PRJ-04` | Dangling reference detection | CMP-PRJ | P3 | 1w | PRJ-090 | PRJ-01 |  |
| `WP-PRJ-05` | Archival export and reproduction verification | CMP-PRJ | P4 | 4w | PRJ-100 PRJ-110 | PRJ-01 CORE-04 ~REP-06 |  |

#### L1 — Comprehension

20 work packages · 44 requirements · 68 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-ANA-01` | C front-end binding and dialect support | CMP-ANA | P2 | 4w | PAR-010 PAR-020 | ING-01 | ● |
| `WP-ANA-02` | Interface and type extraction | CMP-ANA | P2 | 5w | PAR-030 PAR-040 PAR-050 | ANA-01 | ● |
| `WP-ANA-03` | Call graph and scope classification | CMP-ANA | P2 | 3w | PAR-060 | ANA-02 | ● |
| `WP-ANA-04` | Analysis model persistence and schema versioning | CMP-ANA | P2 | 3w | PAR-100 PAR-110 | ANA-02 |  |
| `WP-ANA-05` | Control flow graph capability | CMP-ANA | P2 | 6w | PAR-070 PAR-120 | ANA-01 SPIKE-01 | ● |
| `WP-ANA-06` | Static function testability and macro resolution | CMP-ANA | P2 | 4w | PAR-080 PAR-090 | ANA-02 | ● |
| `WP-ANA-07` | Partial-failure resilience | CMP-ANA | P2 | 2w | PAR-130 | ANA-01 CORE-02 |  |
| `WP-ING-01` | Compilation database ingestion | CMP-ING | P1 | 3w | ING-010 ING-020 ING-030 ING-040 | PRJ-01 |  |
| `WP-ING-02` | Alternative ingestion paths | CMP-ING | P2 | 3w | ING-050 ING-060 ING-080 | ING-01 |  |
| `WP-ING-03` | Ingestion diagnostics, persistence and staleness | CMP-ING | P2 | 3w | ING-070 ING-090 ING-100 | ING-01 |  |
| `WP-ING-04` | Test scope model and resolution | CMP-ING | P2 | 5w | ING-120 ING-130 ING-140 ING-150 ING-190 | ING-01 |  |
| `WP-ING-05` | Scope conflict detection and external dependency reporting | CMP-ING | P2 | 3w | ING-160 ING-170 ING-180 | ING-04 ANA-03 |  |
| `WP-ING-06` | Multi-toolchain ingestion | CMP-ING | P3 | 2w | ING-110 | ING-01 TCH-01 |  |
| `WP-TCH-01` | Declarative compiler configuration format | CMP-TCH | P1 | 3w | TCH-020 PLG-020 | PLG-01 |  |
| `WP-TCH-02` | Host compiler support: GCC and Clang | CMP-TCH | P1 | 2w | TCH-010 | TCH-01 |  |
| `WP-TCH-03` | Cross-toolchain support and shipped configurations | CMP-TCH | P3 | 5w | TCH-030 TCH-040 TCH-050 | TCH-01 |  |
| `WP-TCH-04` | Capability declaration and compiler version gating | CMP-TCH | P3 | 3w | TCH-060 TCH-070 | TCH-01 |  |
| `WP-TCH-05` | Multi-toolchain builds and reproducible containers | CMP-TCH | P3 | 3w | TCH-080 TCH-090 | TCH-03 ~BLD-01 |  |
| `WP-TCH-06` | Proprietary compiler support | CMP-TCH | P3 | 4w | TCH-100 | TCH-03 |  |
| `WP-TCH-07` | First-run environment verification | CMP-TCH | P2 | 2w | INS-080 | TCH-02 |  |

#### L2 — Synthesis

23 work packages · 55 requirements · 92 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-ATG-01` | Validation port and generated-case lifecycle | CMP-ATG | P3 | 4w | ATG-040 ATG-050 ATG-070 ATG-080 | TCM-02 ^EXH-01 |  |
| `WP-ATG-02` | Symbolic execution engine adapter | CMP-ATG | P3 | 8w | ATG-010 ATG-020 | ATG-01 ANA-05 | ● |
| `WP-ATG-03` | Bounded model checking engine | CMP-ATG | P3 | 5w | ATG-030 | ATG-01 | ● |
| `WP-ATG-04` | Targeted generation against uncovered constructs | CMP-ATG | P3 | 4w | ATG-090 | ATG-02 ^COV-01 |  |
| `WP-ATG-05` | Generation reporting, bounds and capability limits | CMP-ATG | P3 | 3w | ATG-060 ATG-100 ATG-110 | ATG-01 |  |
| `WP-GEN-01` | Harness generation core | CMP-GEN | P2 | 5w | HAR-010 HAR-020 HAR-040 HAR-050 | ANA-04 |  |
| `WP-GEN-02` | Framework back-ends: Unity and cmocka | CMP-GEN | P2 | 4w | HAR-060 HAR-070 PLG-030 | GEN-01 PLG-01 | ● |
| `WP-GEN-03` | Static exposure and integration-scope harness | CMP-GEN | P2 | 4w | HAR-030 HAR-080 | GEN-01 ING-04 ANA-06 |  |
| `WP-GEN-04` | Regeneration contract and conflict reporting | CMP-GEN | P2 | 5w | HAR-090 HAR-100 HAR-110 CBT-070 | GEN-01 |  |
| `WP-GEN-05` | Link closure and unresolved reference reporting | CMP-GEN | P2 | 2w | HAR-120 | GEN-06 ANA-03 ~BLD-01 |  |
| `WP-GEN-06` | Stub generation core | CMP-GEN | P2 | 4w | STB-010 STB-020 STB-030 | ANA-04 ING-05 |  |
| `WP-GEN-07` | Stub behaviour programming | CMP-GEN | P2 | 5w | STB-040 STB-050 STB-060 STB-070 | GEN-06 TCM-02 |  |
| `WP-GEN-08` | Stub scope control and indirect-call stubbing | CMP-GEN | P2 | 4w | STB-080 STB-100 STB-140 | GEN-06 ANA-03 |  |
| `WP-GEN-09` | Stub regeneration and unsupported-construct flagging | CMP-GEN | P2 | 4w | STB-110 STB-120 STB-130 | GEN-04 GEN-06 |  |
| `WP-GEN-10` | GoogleTest back-end (host only) | CMP-GEN | P3 | 3w | HAR-065 | GEN-02 |  |
| `WP-GEN-11` | Call wrapping of intra-unit calls | CMP-GEN | P3 | 3w | STB-090 | GEN-08 ANA-03 |  |
| `WP-TCM-01` | Test cases authored in C | CMP-TCM | P1 | 2w | TCD-010 | GEN-01 |  |
| `WP-TCM-02` | Data-driven test case model and on-disk format | CMP-TCM | P2 | 5w | TCD-020 TCD-030 TCD-040 TCD-140 | PRJ-01 ANA-04 | ● |
| `WP-TCM-03` | Expected-value comparison engine | CMP-TCM | P2 | 4w | TCD-050 TCD-060 | TCM-02 |  |
| `WP-TCM-04` | Suites, selective execution and test independence | CMP-TCM | P2 | 3w | TCD-080 TCD-090 | TCM-02 |  |
| `WP-TCM-05` | Ranged and robustness input generation | CMP-TCM | P2 | 3w | TCD-070 TCD-130 | TCM-02 |  |
| `WP-TCM-06` | Test case interchange import and export | CMP-TCM | P2 | 3w | TCD-100 MIG-060 | TCM-02 |  |
| `WP-TCM-07` | Boundary, equivalence and classification-tree derivation | CMP-TCM | P3 | 5w | TCD-110 TCD-120 | TCM-02 ANA-02 |  |

#### L3 — Realization

14 work packages · 22 requirements · 51 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-BLD-01` | Host build orchestration and incremental rebuild | CMP-BLD | P1 | 4w | EXE-080 | TCH-02 GEN-01 |  |
| `WP-BLD-02` | Sanitizer integration | CMP-BLD | P2 | 2w | EXE-090 | BLD-01 |  |
| `WP-BLD-03` | Cross-compiled target build | CMP-BLD | P3 | 3w | TGT-010 | BLD-01 TCH-03 |  |
| `WP-EXH-01` | Host execution and per-test result reporting | CMP-EXH | P1 | 4w | EXE-010 EXE-020 | BLD-01 TCM-01 |  |
| `WP-EXH-02` | Crash isolation, timeout and process exit status | CMP-EXH | P1 | 3w | EXE-030 EXE-040 EXE-060 | EXH-01 CORE-02 |  |
| `WP-EXH-03` | Parallel test execution | CMP-EXH | P1 | 2w | EXE-050 | EXH-02 |  |
| `WP-EXH-04` | Debugger launch with entry breakpoint | CMP-EXH | P2 | 4w | EXE-070 | EXH-01 | ● |
| `WP-EXT-01` | Simulator execution: QEMU and Renode | CMP-EXT | P3 | 5w | TGT-020 | BLD-03 |  |
| `WP-EXT-02` | Hardware execution and flashing via debug probe | CMP-EXT | P3 | 6w | TGT-030 TGT-040 | BLD-03 |  |
| `WP-EXT-03` | Target result retrieval channels and protocol | CMP-EXT | P3 | 4w | TGT-050 TGT-060 | EXT-01 SEC-07 |  |
| `WP-EXT-04` | Host and target test parity | CMP-EXT | P3 | 3w | TGT-070 | EXT-03 EXH-01 |  |
| `WP-EXT-05` | Hardware inventory and target failure classification | CMP-EXT | P3 | 4w | TGT-080 TGT-090 | EXT-02 |  |
| `WP-EXT-06` | Suite splitting and on-target footprint documentation | CMP-EXT | P3 | 4w | TGT-100 TGT-110 | EXT-02 |  |
| `WP-EXT-07` | User-supplied target execution methods | CMP-EXT | P3 | 3w | TGT-120 PLG-040 | EXT-02 PLG-01 |  |

#### L4 — Evidence

31 work packages · 51 requirements · 112 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-CBT-01` | Suite re-execution without regeneration | CMP-CBT | P2 | 2w | CBT-010 | EXH-01 TCM-02 |  |
| `WP-CBT-02` | Change impact analysis and subset execution | CMP-CBT | P3 | 5w | CBT-020 CBT-030 CBT-040 | CBT-01 COV-02 |  |
| `WP-CBT-03` | Run comparison and coverage delta | CMP-CBT | P3 | 3w | CBT-050 CBT-060 | CBT-01 COV-02 |  |
| `WP-CBT-04` | Test suite minimization | CMP-CBT | P3 | 3w | CBT-080 | CBT-02 |  |
| `WP-COV-01` | Statement and branch coverage from compiler backend | CMP-COV | P1 | 4w | COV-010 COV-020 | EXH-01 TCH-02 | ● |
| `WP-COV-02` | Coverage merge and per-test attribution | CMP-COV | P1 | 4w | COV-110 COV-120 | COV-01 |  |
| `WP-COV-03` | Coverage threshold enforcement | CMP-COV | P1 | 1w | COV-130 | COV-02 |  |
| `WP-COV-04` | Function and function-call coverage | CMP-COV | P3 | 2w | COV-030 COV-040 | COV-01 |  |
| `WP-COV-05` | MC/DC measurement and form declaration | CMP-COV | P3 | 6w | COV-050 COV-060 COV-070 | COV-01 TCH-04 | ● |
| `WP-COV-06` | Uninstrumentable expression detection | CMP-COV | P3 | 3w | COV-080 | COV-05 |  |
| `WP-COV-07` | Bare-metal coverage retrieval | CMP-COV | P3 | 5w | COV-100 | COV-01 EXT-03 |  |
| `WP-COV-08` | Unit-under-test versus harness coverage separation | CMP-COV | P3 | 2w | COV-160 | COV-01 ING-04 |  |
| `WP-COV-09` | Coverage-by-analysis justification with digest binding | CMP-COV | P3 | 4w | COV-140 COV-150 | COV-01 PRJ-01 |  |
| `WP-COV-10` | Unique-cause MC/DC support or documented gap | CMP-COV | P4 | 6w | COV-090 | COV-05 | ● |
| `WP-COV-11` | Control coupling and data coupling analysis | CMP-COV | P4 | 6w | COV-170 | COV-01 ANA-03 ING-04 | ● |
| `WP-REP-01` | Single intermediate report model | CMP-REP | P1 | 4w | REP-090 REP-100 | CORE-01 EXH-01 |  |
| `WP-REP-02` | Machine-readable outputs: JUnit and Cobertura/LCOV | CMP-REP | P1 | 3w | REP-010 REP-020 | REP-01 COV-02 |  |
| `WP-REP-03` | HTML report with annotated source | CMP-REP | P1 | 4w | REP-030 REP-040 | REP-01 COV-01 |  |
| `WP-REP-04` | MC/DC condition detail rendering | CMP-REP | P3 | 3w | REP-050 | REP-03 COV-05 |  |
| `WP-REP-05` | Certification verification report and scope statement | CMP-REP | P4 | 5w | REP-060 REP-140 | REP-01 TRC-01 COV-09 | ● |
| `WP-REP-06` | Report provenance and format version stability | CMP-REP | P4 | 3w | REP-070 REP-130 | REP-01 CORE-04 |  |
| `WP-REP-07` | Paginated PDF archival rendering | CMP-REP | P4 | 4w | REP-080 | REP-03 |  |
| `WP-REP-08` | Cross-unit summary and coverage trend | CMP-REP | P3 | 4w | REP-110 REP-120 | REP-01 |  |
| `WP-REP-09` | Report generation from archived result data | CMP-REP | P4 | 3w | REP-150 | REP-01 PRJ-05 |  |
| `WP-REP-10` | Coverage interchange import and export | CMP-REP | P4 | 3w | MIG-080 | REP-01 COV-02 |  |
| `WP-REP-11` | Report format extension point | CMP-REP | P3 | 2w | PLG-050 | REP-01 PLG-01 |  |
| `WP-TRC-01` | Requirement association and bidirectional matrix | CMP-TRC | P4 | 4w | TRC-010 TRC-020 TRC-030 | TCM-02 REP-01 |  |
| `WP-TRC-02` | Unlinked requirement and unlinked test reporting | CMP-TRC | P4 | 2w | TRC-040 | TRC-01 |  |
| `WP-TRC-03` | Requirement import from ReqIF, CSV and plain text | CMP-TRC | P4 | 4w | TRC-050 TRC-060 | TRC-01 |  |
| `WP-TRC-04` | ReqIF export and external traceability tool interop | CMP-TRC | P4 | 4w | TRC-070 TRC-100 | TRC-03 |  |
| `WP-TRC-05` | Source-element linking and requirement change detection | CMP-TRC | P4 | 4w | TRC-080 TRC-090 | TRC-01 ANA-02 |  |

#### L5 — Interfaces

30 work packages · 45 requirements · 106 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-API-01` | Engine API protocol, operation catalogue and versioning | CMP-API | P1 | 4w | UIX-010 UIX-020 PLG-060 | CORE-02 |  |
| `WP-API-02` | Local-only transport with no network listener | CMP-API | P2 | 2w | UIX-050 | API-01 |  |
| `WP-API-03` | CLI and GUI round-trip equivalence | CMP-API | P2 | 3w | UIX-330 | API-01 CLI-01 |  |
| `WP-CLI-01` | Non-interactive CLI generated from the operation catalogue | CMP-CLI | P1 | 3w | CIC-010 CIC-020 | API-01 |  |
| `WP-CLI-02` | Stable documented exit codes | CMP-CLI | P1 | 1w | CIC-030 | CLI-01 CORE-02 |  |
| `WP-CLI-03` | Container execution | CMP-CLI | P1 | 2w | CIC-040 | CLI-01 |  |
| `WP-CLI-04` | Reference CI pipelines and artifact caching | CMP-CLI | P2 | 3w | CIC-050 CIC-070 | CLI-03 |  |
| `WP-CLI-05` | CI sharding and report merge | CMP-CLI | P3 | 3w | CIC-060 | CLI-04 REP-08 |  |
| `WP-GUI-01` | Application shell, installability and platform support | CMP-GUI | P2 | 6w | UIX-030 UIX-040 UIX-340 UIX-350 | API-01 SPIKE-03 | ● |
| `WP-GUI-02` | Project and environment management workflow | CMP-GUI | P2 | 5w | UIX-060 UIX-070 UIX-100 | GUI-01 PRJ-01 | ● |
| `WP-GUI-03` | Integration scope creation and dependency preview | CMP-GUI | P2 | 3w | UIX-080 | GUI-02 ING-05 | ● |
| `WP-GUI-04` | Build progress and navigable compiler diagnostics | CMP-GUI | P2 | 3w | UIX-090 | GUI-02 BLD-01 | ● |
| `WP-GUI-05` | Navigation tree, status aggregation, filter and search | CMP-GUI | P2 | 5w | UIX-110 UIX-120 UIX-130 UIX-140 | GUI-02 | ● |
| `WP-GUI-06` | Execution control and per-test result presentation | CMP-GUI | P2 | 4w | UIX-210 UIX-220 | GUI-05 EXH-01 | ● |
| `WP-GUI-07` | Console pane reproducing engine commands | CMP-GUI | P2 | 2w | UIX-240 | GUI-01 API-03 | ● |
| `WP-GUI-08` | Coverage annotation and drill-down summary views | CMP-GUI | P2 | 4w | UIX-250 UIX-280 | GUI-05 COV-02 | ● |
| `WP-GUI-09` | Actionable error messaging | CMP-GUI | P2 | 2w | UIX-360 | GUI-01 CORE-02 | ● |
| `WP-GUI-10` | Tabular data-driven test case editor | CMP-GUI | P3 | 5w | UIX-150 | GUI-05 TCM-02 | ● |
| `WP-GUI-11` | Nested type-aware value editor | CMP-GUI | P3 | 8w | UIX-160 UIX-170 | GUI-10 SPIKE-02 ANA-02 | ● |
| `WP-GUI-12` | Stub configuration view | CMP-GUI | P3 | 4w | UIX-180 | GUI-10 GEN-07 | ● |
| `WP-GUI-13` | Ranged and boundary input authoring | CMP-GUI | P3 | 3w | UIX-190 | GUI-10 TCM-05 | ● |
| `WP-GUI-14` | C source test editor with syntax highlighting | CMP-GUI | P3 | 3w | UIX-200 | GUI-10 TCM-01 | ● |
| `WP-GUI-15` | Debugger launch from the application | CMP-GUI | P3 | 4w | UIX-230 | GUI-06 EXH-04 | ● |
| `WP-GUI-16` | MC/DC per-condition detail view | CMP-GUI | P3 | 3w | UIX-260 | GUI-08 COV-05 | ● |
| `WP-GUI-17` | Graphical control flow view with coverage overlay | CMP-GUI | P3 | 5w | UIX-270 | GUI-08 ANA-05 | ● |
| `WP-GUI-18` | Non-blocking interface during long operations | CMP-GUI | P3 | 4w | UIX-370 | GUI-01 CORE-02 | ● |
| `WP-GUI-19` | Coverage-by-analysis justification capture | CMP-GUI | P4 | 3w | UIX-290 | GUI-08 COV-09 | ● |
| `WP-GUI-20` | In-application report generation and viewing | CMP-GUI | P4 | 3w | UIX-300 | GUI-08 REP-05 | ● |
| `WP-GUI-21` | Traceability matrix view with navigation | CMP-GUI | P4 | 3w | UIX-310 | GUI-05 TRC-01 | ● |
| `WP-GUI-22` | Keyboard-driven workflow | CMP-GUI | P4 | 3w | UIX-380 | GUI-05 | ● |

#### L6 — Assurance and Ecosystem

49 work packages · 71 requirements · 151 person-weeks

| WP | Capability delivered | Comp | Start | Effort | Reqs | Depends on | ADR |
|---|---|---|:--:|--:|---|---|:--:|
| `WP-AIF-01` | Provider abstraction and local model runtime | CMP-AIF | P3 | 5w | AIF-020 AIF-050 | CORE-03 |  |
| `WP-AIF-02` | Optionality, separability and default-off | CMP-AIF | P3 | 2w | AIF-010 | AIF-01 |  |
| `WP-AIF-03` | Data egress control and pre-use disclosure | CMP-AIF | P3 | 3w | AIF-030 AIF-040 | AIF-01 SEC-08 |  |
| `WP-AIF-04` | Generated artifact validation and rejection recording | CMP-AIF | P3 | 4w | AIF-070 AIF-210 | AIF-01 ATG-01 |  |
| `WP-AIF-05` | Immutable AI provenance and review state | CMP-AIF | P3 | 5w | AIF-080 AIF-090 AIF-160 AIF-180 AIF-190 | AIF-01 CORE-04 |  |
| `WP-AIF-06` | Time and token bounds on AI operations | CMP-AIF | P3 | 2w | AIF-150 | AIF-01 |  |
| `WP-AIF-07` | Local model integrity and hardware requirements | CMP-AIF | P3 | 3w | AIF-170 AIF-200 | AIF-01 SEC-01 |  |
| `WP-AIF-08` | AI-assisted test case generation | CMP-AIF | P3 | 4w | AIF-060 | AIF-04 COV-01 |  |
| `WP-AIF-09` | AI-assisted stub body generation | CMP-AIF | P3 | 3w | AIF-110 | AIF-04 GEN-06 |  |
| `WP-AIF-10` | AI-assisted test failure explanation | CMP-AIF | P3 | 3w | AIF-120 | AIF-01 EXH-01 |  |
| `WP-AIF-11` | AI-assisted naming and documentation | CMP-AIF | P3 | 2w | AIF-140 | AIF-04 |  |
| `WP-AIF-12` | Certification evidence exclusion mode | CMP-AIF | P4 | 2w | AIF-100 | AIF-05 REP-05 | ● |
| `WP-AIF-13` | AI-proposed requirement-to-test links | CMP-AIF | P4 | 3w | AIF-130 | AIF-01 TRC-01 |  |
| `WP-MIG-01` | Execution of existing Unity and cmocka suites | CMP-MIG | P2 | 4w | MIG-010 | GEN-02 EXH-01 |  |
| `WP-MIG-02` | Ceedling project import | CMP-MIG | P2 | 4w | MIG-020 | MIG-01 ING-01 |  |
| `WP-MIG-03` | Interchange format documentation | CMP-MIG | P2 | 2w | MIG-100 | TCM-06 |  |
| `WP-MIG-04` | Commercial tool and CSV test data import | CMP-MIG | P3 | 6w | MIG-030 MIG-050 | TCM-06 |  |
| `WP-MIG-05` | Import fidelity reporting | CMP-MIG | P3 | 3w | MIG-040 | MIG-04 |  |
| `WP-MIG-06` | Coexistence with another tool on one project | CMP-MIG | P3 | 3w | MIG-070 | CORE-01 PRJ-01 |  |
| `WP-MIG-07` | Migration assessment mode | CMP-MIG | P4 | 4w | MIG-090 | MIG-05 |  |
| `WP-PKG-01` | Offline, non-admin, runtime-free installation | CMP-PKG | P2 | 6w | INS-010 INS-020 INS-030 | SPIKE-03 CORE-03 | ● |
| `WP-PKG-02` | Self-contained archivable release identity | CMP-PKG | P2 | 3w | INS-040 QUA-050 | PKG-01 CORE-04 |  |
| `WP-PKG-03` | Side-by-side versions and confirmed upgrade | CMP-PKG | P2 | 4w | INS-050 INS-060 | PKG-01 PRJ-03 |  |
| `WP-PKG-04` | Documented uninstallation | CMP-PKG | P2 | 1w | INS-070 | PKG-01 |  |
| `WP-PKG-05` | Versioned CI container image | CMP-PKG | P2 | 2w | INS-090 | PKG-01 CLI-03 |  |
| `WP-PKG-06` | Shared read-only multi-user installation | CMP-PKG | P3 | 3w | INS-100 | PKG-01 |  |
| `WP-PKG-07` | License policy, process isolation and automated enforcement | CMP-PKG | P1 | 3w | LIC-010 LIC-020 LIC-030 LIC-040 LIC-050 LIC-060 | — | ● |
| `WP-PKG-08` | Separable restrictively-licensed optional components | CMP-PKG | P3 | 2w | LIC-070 | PKG-07 | ● |
| `WP-PKG-09` | Installation without administrative privileges | CMP-PKG | P2 | 1w | NFR-110 | PKG-01 |  |
| `WP-PLG-01` | Extension point definition and versioning | CMP-PLG | P2 | 3w | PLG-010 | CORE-02 |  |
| `WP-PLG-02` | Extension discovery and load failure isolation | CMP-PLG | P3 | 3w | PLG-070 PLG-080 | PLG-01 |  |
| `WP-PLG-03` | Built-ins implemented through public extension points | CMP-PLG | P3 | 3w | PLG-090 | PLG-01 ~TCH-01 ~GEN-02 ~REP-11 |  |
| `WP-QUA-01` | Tool classification analysis and confidence level | CMP-QUA | P4 | 3w | QUA-010 | CORE-04 | ● |
| `WP-QUA-02` | Tool operational requirements specification | CMP-QUA | P4 | 4w | QUA-020 | QUA-01 | ● |
| `WP-QUA-03` | User-executable validation suite | CMP-QUA | P4 | 6w | QUA-030 | QUA-02 CORE-08 | ● |
| `WP-QUA-04` | Known error list maintained per release | CMP-QUA | P4 | 2w | QUA-040 | PKG-02 |  |
| `WP-QUA-05` | Development process and change control documentation | CMP-QUA | P4 | 3w | QUA-070 | — |  |
| `WP-QUA-06` | Standards objective mapping | CMP-QUA | P4 | 4w | QUA-080 | QUA-02 | ● |
| `WP-QUA-07` | Explicit statement of what is and is not qualified | CMP-QUA | P4 | 1w | QUA-090 | QUA-01 | ● |
| `WP-QUA-08` | Templates for user tool qualification artifacts | CMP-QUA | P4 | 3w | QUA-100 | QUA-06 | ● |
| `WP-SEC-01` | Release signing and Software Bill of Materials | CMP-SEC | P2 | 3w | SEC-010 SEC-020 | PKG-02 |  |
| `WP-SEC-02` | Reproducible build and pinned dependency integrity | CMP-SEC | P2 | 4w | SEC-030 SEC-040 | SEC-01 | ● |
| `WP-SEC-03` | Untrusted-project warning and configuration-is-data | CMP-SEC | P2 | 3w | SEC-050 SEC-070 | PRJ-01 |  |
| `WP-SEC-04` | Log and diagnostic content control | CMP-SEC | P2 | 2w | SEC-120 | CORE-01 |  |
| `WP-SEC-05` | Security disclosure process and supported-version policy | CMP-SEC | P2 | 1w | SEC-080 | — |  |
| `WP-SEC-06` | Restricted execution context for harnesses | CMP-SEC | P3 | 4w | SEC-060 | EXH-02 | ● |
| `WP-SEC-07` | Target-supplied data treated as untrusted | CMP-SEC | P3 | 2w | SEC-090 | CORE-02 |  |
| `WP-SEC-08` | Credential storage via platform secure storage | CMP-SEC | P3 | 3w | SEC-110 | CORE-03 | ● |
| `WP-SEC-09` | Dependency vulnerability scanning in CI | CMP-SEC | P3 | 2w | SEC-100 | SEC-01 |  |

---

## 6. Layer 3 — Specification-based test design

### 6.1 Method

Black-box test design against the requirement text, in the ISTQB sense: conditions are derived from what the
specification *states*, never from an implementation it does not mandate. Where a requirement is too vague to
derive a condition from, that is recorded as an `UNTESTABLE` finding in §3.2 rather than papered over with a
smoke test.

Technique selection follows a documented rule, applied to the requirement text and its recorded verification
method, with **83 assignments made by judgement** where the rule would have been too coarse — chiefly the
requirements whose failure would produce *wrong certification evidence*. The remaining **240 follow the rule**:

| Condition in the requirement text | Technique |
|---|---|
| Recorded verification is `I` | Inspection checklist |
| Recorded verification is `A` | Analysis argument |
| Recorded verification is `D` | Scenario (demonstration) |
| Enumerates concrete alternatives (`GCC and Clang`, `C89, C99, C11, C17`, `OpenOCD, pyOCD, and J-Link`) | Pairwise |
| Names a limit, threshold, count, size, timeout or tolerance | Boundary value analysis |
| Implies a lifecycle (`stale`, `unreviewed`, `invalidated`, `since ... last`, `migrat*`) | State transition |
| Behaviour depends on a combination of conditions (`either`, `or shall`, `unless`, `shall refuse`) | Decision table |
| Otherwise — valid and invalid input classes | Equivalence partitioning |

### 6.2 Technique distribution
| Technique | Requirements | Share |
|---|--:|--:|
| EQUIVALENCE PARTITIONING | 136 | 42% |
| INSPECTION CHECKLIST | 50 | 15% |
| BOUNDARY VALUE ANALYSIS | 30 | 9% |
| DECISION TABLE | 26 | 8% |
| SCENARIO (demonstration) | 23 | 7% |
| STATE TRANSITION | 22 | 6% |
| PAIRWISE | 21 | 6% |
| ANALYSIS ARGUMENT | 13 | 4% |
| — (deferred) | 2 | 0% |
| **Total** | **323** | **100%** |

Equivalence partitioning at 42% is high but honest: a large part of this specification is of the form "the tool
shall accept X and report Y", which is exactly what EP is for. The distribution is worth reading for what is
*thin* rather than what is thick:

- **Boundary value analysis is only 30 requirements** because the SRS states remarkably few numbers. That is
  itself a finding (F-08): a specification for a verification tool that names three numeric thresholds in 323
  requirements is under-constrained on performance and scale.
- **Decision tables cluster in exactly the right place** — coverage, AI artifact acceptance, regeneration
  conflict, and target failure classification. These are the multi-condition behaviours where a missed
  combination becomes a wrong result rather than a visible bug.
- **50 inspection checklists and 13 analysis arguments are 20% of the specification** and produce no
  executable test. They are real deliverables with real cost, concentrated in QUA (9 of 10), LIC (7 of 7) and
  NFR (6 of 19), and they are the work most likely to be deferred into a v1.0 that then cannot claim
  qualifiability.

### 6.3 Verification method reconciliation

Technique family cross-checked against the recorded verification method for all 323 requirements:

| Recorded | Test technique | Inspection | Analysis | Demonstration | n/a |
|---|--:|--:|--:|--:|--:|
| T (231) | 230 | — | — | 1 | — |
| I (52) | 2 | 50 | — | — | — |
| D (24) | 2 | — | — | 22 | — |
| A (14) | 1 | — | 13 | — | — |
| n/a (2) | — | — | — | — | 2 |

**Six mismatches in 323.** The specification is unusually well disciplined here, which makes each mismatch
worth acting on rather than dismissing — and three of the six sit in the "nothing overclaimed" family:

| Requirement | Recorded | Should be | Why |
|---|:--:|:--:|---|
| `COV-150` | I | **T** | Justification invalidation on source change is dynamic behaviour. Inspection cannot verify that an edit expires a justification — and if it silently does not, a report claims justified coverage that no longer holds |
| `CBT-040` | I | **T** | "All reports shall state clearly that the run was partial" is observable output. If a partial run ever renders as complete, every downstream coverage claim is overstated |
| `NFR-050` | A | **T** | Names 500 translation units and 10,000 test cases. Numbers are tested, not argued |
| `COV-100` | T | **T + D** | Bare-metal coverage retrieval is testable on a simulator and demonstrable on hardware. The SRS should say which satisfies it |
| 2 x `D` to test | D | review | Two demonstration requirements have testable cores; low priority |

### 6.4 The tool's own test architecture

A testing tool must be verified more rigorously than the code it tests, because **a false negative here becomes
a false certification claim downstream**. `NFR-140` (documented self-coverage threshold) and `NFR-170` (test the
tool's own C components) are the only two requirements that address this, and between them they are not
sufficient. The following is derived from the specification's own obligations rather than added as opinion.

**Reference C corpus.** Ingestion, parsing and generation are only as good as the C they have seen. The corpus
must cover what `PAR-020`, `PAR-040` and `STB-130` commit the tool to handling: bit-fields, anonymous unions,
function pointers and function-pointer struct members, `volatile` and `const volatile`, variadic functions,
K&R-style declarations under C89, GNU extensions, inline assembly, compiler-specific attributes and pragmas,
deeply nested and self-referential types, and generated code. `STB-130`'s "consistent, greppable marker" for
constructs it could not handle is the observable that makes this corpus testable rather than aspirational.

**Differential testing against ground truth.** `COV-010` and `COV-020` measure coverage *from the user's own
gcov/llvm-cov* rather than instrumenting. That is the right architectural choice and it creates a precise test
oracle: for any corpus program and test set, the tool's reported coverage must agree with the backend's own
report, line for line. Any disagreement is a defect in the adapter. This is the single highest-value test
harness the project can build, and it is cheap because the oracle already exists.

**Golden-file and diff-stability testing.** `PRJ-050`, `REP-100` and `NFR-060` require byte-stable output. The
test is mechanical: run twice, on two machines, and diff. Extend it to the case `PRJ-050` actually cares about —
a semantically null edit (reordering a test case, reopening and resaving a project) must produce **no diff at
all**, not merely a valid file.

**Cross-toolchain matrix, reduced pairwise.** `TCH-050` commits to six shipped configurations; `PAR-020` to
five dialects; `TGT-020` through `TGT-040` to two simulators and three probes. The full cross-product is not
runnable on every change. Pairwise reduction over (toolchain x dialect x coverage kind x target) keeps it
tractable, with the full matrix run at release rather than per-commit.

**Target-in-the-loop.** `TGT-030`, `TGT-040` and `COV-100` cannot be verified on a simulator alone — flash
failure, watchdog reset and semihosting behaviour are exactly what `TGT-090` requires the tool to distinguish,
and a simulator will not reproduce them faithfully. A minimum of one physical board per supported probe family
is a hard prerequisite for P3, and should be budgeted as such.

**Negative testing — what the tool must refuse.** More of this specification is about refusal than is obvious:
`TCH-060` (refuse an unsupported metric), `SEC-070` (never execute configuration), `NFR-090` (fail rather than
emit incomplete results), `AIF-070` (discard artifacts that fail to compile), `COV-080` (report expressions the
compiler declined to instrument). Each needs a test that the refusal *happens*, because every one of them fails
silently in the direction of an over-optimistic result.

**Self-hosting, and its limit.** `NFR-170` proposes the tool test its own C components. Useful as a
demonstration, but circular as evidence: a coverage defect that hides a gap will hide it in the tool's own
report too. Self-hosting is a usability signal, not verification evidence, and `QUA-030`'s user-executable
validation suite — which runs against known-answer cases rather than against the tool's own source — is what
actually discharges the obligation.

### 6.5 Phase acceptance gates

| Phase | Gate |
|---|---|
| **P0** | All three spikes report against their §4.4 pass criteria. `WP-SPIKE-01`'s result is recorded in ADR-001 before the language decision is closed |
| **P1** | On a real 20 kLOC-or-larger embedded project: ingest, generate, build, execute, measure statement and branch coverage, and emit JUnit + Cobertura + HTML, from a non-interactive CLI, with a non-zero exit on failure and byte-identical output across two runs |
| **P2** | Harness and stub generation regenerate without losing user edits; a data-driven test case survives a round trip through the on-disk format unchanged; the GUI performs the full P2 workflow and the console pane reproduces every action as a CLI invocation |
| **P3** | The same test case passes on host and on physical target unmodified; MC/DC is measured and every report names the form obtained; coverage from a bare-metal target with no filesystem is retrieved and merged |
| **P4** | A verification report is generated containing tool identification, configuration, results, per-metric coverage, justified exclusions and the traceability matrix — and an auditor can reproduce it from the archived record alone |

---

## 7. Coverage audit

This section is arithmetic. Every figure is recomputed from `SRS-001-requirements.md`,
`design/trace/requirement-matrix.csv` and the work-package dataset that generates §5.5 and Appendix A. If any
of them drifts, these numbers stop reconciling and the document is wrong on its face.

### 7.1 Requirement allocation

| Check | Result |
|---|---|
| Requirement ids in SRS-001 | **323** |
| Ids in `requirement-matrix.csv` | **323** |
| In SRS but not the matrix | **none** |
| In the matrix but not the SRS | **none** |
| Future-priority, correctly not allocated | **2** (`UIX-390`, `UIX-400`) |
| Expected allocations (323 − 2) | **321** |
| Allocation entries in the work breakdown | **321** |
| Distinct requirements allocated | **321** |
| **Orphans** — expected but in no work package | **none** |
| **Double-allocated** — in more than one work package | **none** |
| **Future requirements wrongly allocated** | **none** |

**Verdict: 100% allocation of all 321 non-Future requirements, each to exactly one work package.**

Five requirements are legitimately discharged by more than one *design element* per SDD-001 §5 — `COV-060`,
`EXE-010`, `MIG-060`, `PRJ-050`, `UIX-320`. A work package register cannot express that without breaking the
exactly-once rule, so each is assigned a single **owning** package with the collaborating component named:

| Requirement | Owning WP | Collaborating component |
|---|---|---|
| `COV-060` | `WP-COV-05` | `CMP-CORE` supplies the provenance record the declaration is embedded in |
| `EXE-010` | `WP-EXH-01` | `CMP-BLD` supplies the build half via `WP-BLD-01` |
| `MIG-060` | `WP-TCM-06` | `CMP-REP` supplies the results half via `WP-REP-10` |
| `PRJ-050` | `WP-CORE-01` | `CMP-PRJ` applies it to project files in `WP-PRJ-02` |
| `UIX-320` | `WP-PRJ-01` | `CMP-CORE` enforces output confinement in `WP-CORE-01` |

### 7.2 Structural audit of the breakdown

| Check | Result |
|---|---|
| Work packages | 180 (plus 3 validation spikes) |
| Dependency edges | 272 — 260 code, 2 port-mediated, 10 schedule-only |
| **Unresolved dependencies** | **none** |
| **Upward layer violations** (code edges) | **none** |
| **Cycles** | **none** |
| **Phase inconsistencies** (a package starting later than a requirement it holds) | **none** |

Three inconsistencies were found and fixed during construction, and each is a finding about the specification
rather than about the plan:

- `STB-080`, `STB-100` and `STB-140` are P2 but were grouped with `STB-090` (P3). Split into `WP-GEN-08` (P2)
  and `WP-GEN-11` (P3).
- `COV-150` (**Must, P3**) constrains `COV-140` (**Should, P4**) — finding **F-05**. The owning package starts
  at P3; the SRS phase-priority inversion remains and needs an SRS decision.
- `LIC-030` (SBOM) is P1 but naturally belongs with the release-signing machinery of `SEC-010`/`SEC-020` (P2).
  Moved into the P1 licensing package, which means **the SBOM must exist before the signing infrastructure
  that will eventually publish it** — deliberate, and correct for a project whose dependency licences gate
  its own architecture.

### 7.3 Coverage by phase and priority

| | P1 | P2 | P3 | P4 | n/a | Total |
|---|--:|--:|--:|--:|--:|--:|
| **Must** | 33 | 99 | 48 | 19 | — | 199 |
| **Should** | 2 | 45 | 44 | 16 | — | 107 |
| **Could** | — | 1 | 9 | 5 | — | 15 |
| **Future** | — | — | — | — | 2 | 2 |
| **Total** | 35 | 145 | 101 | 40 | 2 | 323 |
| *Allocated* | *35* | *145* | *101* | *40* | *0* | *321* |

---

## 8. Risk register

Ranked. The ordering is by expected cost to the programme, not by likelihood alone.

| # | Risk | Threatens | L | I | Early warning sign | Mitigation | Fallback |
|---|---|---|:--:|:--:|---|---|---|
| **R-1** | **Scope.** 321 requirements, 622 person-weeks, no implementation yet, open-source resourcing | Everything | High | High | P1 slips past week 60 with fewer than 8 engineers | Cut to a defensible v1.0 — see §8.1 | Ship P1+P2 as v1.0 and re-scope publicly |
| **R-2** | **ADR-006 unresolved.** A fork decision after implementation starts invalidates three components and the language choice | `CMP-ANA`, `CMP-ATG`, `CMP-GEN` | Med | **Very high** | `WP-ANA-01` starting with ADR-006 still open | Decide before week 10. SDD-001 §8 already flags it as the one blocker | None. This is why it is a blocker |
| **R-3** | **The nested test data editor** (`WP-GUI-11`, 8w) is the largest package and ADR-001 §6 R-02 names it the schedule driver | 33 UIX requirements | High | High | `WP-SPIKE-02` exceeding two weeks, or producing a prototype that is slow at 3+ nesting levels | Run `WP-SPIKE-02` before architecture freeze | Ship a flat editor for scalars and a raw C fallback for aggregates; degrade the claim, not the tool |
| **R-4** | **MC/DC form inadequate for an assessor.** `COV-090` permits documenting the gap rather than closing it | `COV-050`, `REP-050`, all certification claims | Med | **Very high** | A pilot user's assessor rejects masking MC/DC | `DSN-COV-020` makes the form a data field rendered in every report, so it can never be misread | Implement unique-cause via source transformation — a large, unbudgeted change |
| **R-5** | **libclang insufficiency.** No CFG from libclang; `PAR-070` and `ATG-*` need one | `WP-ANA-05`, `WP-ATG-02`, `WP-GUI-17` | Med | High | `WP-SPIKE-01` finding constructs needing a CFG | `DSN-ANA-040` capability flag lets consumers degrade rather than break | Bring the C++ LibTooling analyzer forward; the `PAR-100` seam makes this a component swap |
| **R-6** | **Coverage backend absent on embedded toolchains.** Measuring from the user's gcov/llvm-cov is right, but many embedded compilers have no such backend | `COV-*` on non-GNU targets | High | Med | `TCH-100` proprietary compiler work finding no coverage path | `TCH-060` requires refusing an unsupported metric rather than reporting an empty one — the failure is honest | Document the supported matrix narrowly and early; do not imply universality |
| **R-7** | **Adoption against qualified incumbents.** VectorCAST, Cantata, LDRA and Tessy ship qualification kits; this ships "qualifiable" | Whole product thesis | High | High | Pilot users asking for a qualification kit and not returning | `MIG-*` is the adoption mechanism, correctly identified as such in SRS §23 | Fund a Tier 2 documentation package earlier than v1.1 |
| **R-8** | **Licence friction.** The repository is currently AGPL-3.0 while `LIC-010` requires a **permissive** licence for the tool's own source | `WP-PKG-07`, adoption by commercial embedded users | **High** | High | Legal review at a pilot user stalling on AGPL | Resolve ADR-005 before first public release; `LIC-010` and the current `LICENSE` file are in direct conflict today | Dual-licence, or relicense while the contributor set is still small |
| **R-9** | **Evidence integrity gap** (F-10). Nothing signs or hashes the verification report or archived record | `REP-060`, `PRJ-100`, every audit | Med | High | An auditor asking how a report is known to be unaltered | Add a requirement; extend `DSN-CORE-100` provenance to cover evidence artifacts | Manual counter-signature procedure documented for users |
| **R-10** | **Optimisation-level coverage gap** (F-11). Coverage measured on an unoptimised build; shipped code is optimised | All structural coverage claims | Med | High | A DO-178C Level A user asking for object-code coverage | Add a requirement stating the measurement build explicitly | Document the limitation prominently under `QUA-090` |
| **R-11** | **Symbolic execution destabilises builds** | `WP-ATG-02`, `WP-ATG-03` | Med | Low | Install-size or build-time regressions traced to the engine | `DSN-ATG-020` keeps the component optional and off the default install path | Drop `ATG-020` to Could; `ATG-010` can be met by simpler generation |
| **R-12** | **Unbounded compiler and target support burden** | `CMP-TCH`, `CMP-EXT` | High | Med | A queue of "please support compiler X" issues with no contributor | `DSN-PLG-040` requires built-ins to use the public extension points, which is what makes third-party configs viable | Publish the extension guide early and treat configs as community contributions |

### 8.1 R-1 in detail: what a defensible v1.0 actually cuts

R-1 is the risk most likely to sink the programme, and "cut scope" is useless advice without naming what goes.
The Must-priority requirements genuinely worth cutting from v1.0 — because each is separable, none is load
bearing for another, and each can be added without rework:

| Cut | Requirements | Saves | Why it is safe to cut |
|---|---|--:|---|
| **The entire AI subsystem** | all 21 `AIF-*` (14 Must) | 41w | `AIF-010` already requires full functionality with AI disabled and default-off. `CMP-AIF` is structurally quarantined per SDD-001 §4.5 — removing it changes nothing else. It is the largest separable block in the specification |
| **Automatic test generation** | all 11 `ATG-*` (4 Must) | 24w | Optional by design, off the default install path, and gated on an unresolved ADR-003. `TCD-110` (boundary/equivalence derivation) delivers most of the practical value at a fraction of the cost |
| **Bounded model checking** | `ATG-030` | included above | A second engine before the first one ships |
| **Proprietary compiler support** | `TCH-100` | 4w | Could-priority already; needs vendor access the project does not have |
| **Coupling analysis** | `COV-170` | 6w | P4, Should, and only required by DO-178C users who are not the initial audience |
| **PDF rendering** | `REP-080` | 4w | Archival matters; the *format* can be HTML plus a documented print path for v1.0 |

**Total: 79 person-weeks, or 12% of the programme, without touching a single requirement that another
requirement depends on.** That is the cut to take first, and it is available precisely because SDD-001 made
`CMP-AIF` and `CMP-ATG` separable by design — which is the clearest return the architecture work has already
produced.

What must **not** be cut, whatever the pressure: `CORE-01` determinism, the `PAR-100` model seam, the
"nothing overclaimed" family (`COV-080`, `CBT-040`, `ATG-080`, `AIF-090`, `QUA-090`), and `QUA-090` itself.
Those are what separate a tool whose output is evidence from one whose output merely looks like evidence.

---

## 9. Change control

This document is downstream of SRS-001, ADR-001 and the SDD set, and derived from
`design/trace/requirement-matrix.csv`. It goes stale the moment any of them moves.

| Upstream change | Effect here |
|---|---|
| A requirement added, deleted or re-phased in SRS-001 | §2, §5.5, §7 and Appendix A must be regenerated; the allocation audit will fail until the new requirement is placed in a work package |
| ADR-001 recorded with a different position | §1.1, §4.3 and all 57 ADR-sensitive packages need review |
| **ADR-006 recorded as "fork"** | §4, §5 and §8 need substantial rework; the language assumption in §1.1 falls |
| Any of F-01 to F-15 resolved in SRS-001 | The corresponding finding is struck and §3.3 re-derived |
| A component added or a layer edge changed in SDD-001 | The dependency audit in §7.2 must be re-run |

**Open actions arising from this analysis**, in the order they need answering:

1. **Decide ADR-006** (fork UTBotCpp or build fresh). Blocks `WP-ANA-01` at week 10 and invalidates the ADR-001
   language assumption if answered "fork". SDD-001 §8 already names it the one genuine blocker.
2. **Resolve F-01** — re-phase the 14 requirements into P1, or amend `TCD-010`. §3.3 recommends re-phasing.
3. **Resolve F-16 (`LIC-010` vs the repository's current AGPL licence)** — these are in direct conflict today
   and the conflict is visible to anyone who reads both files.
4. **Correct the verification methods** on `COV-150`, `CBT-040` and `NFR-050` (F-07, F-08).
5. **Add requirements for the two gaps** — evidence integrity (F-10) and coverage measurement build (F-11).
6. **Run the three spikes** before freezing the architecture, `WP-SPIKE-02` first.
7. **Decide ADR-002** (project and test data format) — it gates `WP-PRJ-01` at week 3, the earliest gate of all.

---

## Appendix A — Requirement index

Every requirement in SRS-001, its work package, and the test design technique derived for it. Generated from
the same dataset as §5.5; see §7 for the audit that proves it complete.
| Requirement | Pri | Phase | V | Work package | Test design technique |
|---|:--:|:--:|:--:|---|---|
| `TOOL-AIF-010` | M | P3 | T | `WP-AIF-02` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-020` | M | P3 | T | `WP-AIF-01` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-030` | M | P3 | T | `WP-AIF-03` | DECISION TABLE |
| `TOOL-AIF-040` | M | P3 | D | `WP-AIF-03` | SCENARIO (demonstration) |
| `TOOL-AIF-050` | M | P3 | A | `WP-AIF-01` | ANALYSIS ARGUMENT |
| `TOOL-AIF-060` | S | P3 | T | `WP-AIF-08` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-070` | M | P3 | T | `WP-AIF-04` | DECISION TABLE |
| `TOOL-AIF-080` | M | P3 | I | `WP-AIF-05` | INSPECTION CHECKLIST |
| `TOOL-AIF-090` | M | P3 | T | `WP-AIF-05` | STATE TRANSITION |
| `TOOL-AIF-100` | M | P4 | T | `WP-AIF-12` | DECISION TABLE |
| `TOOL-AIF-110` | S | P3 | T | `WP-AIF-09` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-120` | S | P3 | T | `WP-AIF-10` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-130` | C | P4 | T | `WP-AIF-13` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-140` | C | P3 | T | `WP-AIF-11` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-150` | M | P3 | T | `WP-AIF-06` | BOUNDARY VALUE ANALYSIS |
| `TOOL-AIF-160` | S | P3 | A | `WP-AIF-05` | ANALYSIS ARGUMENT |
| `TOOL-AIF-170` | M | P3 | I | `WP-AIF-07` | INSPECTION CHECKLIST |
| `TOOL-AIF-180` | M | P3 | T | `WP-AIF-05` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-190` | M | P3 | I | `WP-AIF-05` | INSPECTION CHECKLIST |
| `TOOL-AIF-200` | S | P3 | T | `WP-AIF-07` | EQUIVALENCE PARTITIONING |
| `TOOL-AIF-210` | M | P3 | T | `WP-AIF-04` | STATE TRANSITION |
| `TOOL-ATG-010` | S | P3 | T | `WP-ATG-02` | EQUIVALENCE PARTITIONING |
| `TOOL-ATG-020` | S | P3 | T | `WP-ATG-02` | EQUIVALENCE PARTITIONING |
| `TOOL-ATG-030` | C | P3 | T | `WP-ATG-03` | EQUIVALENCE PARTITIONING |
| `TOOL-ATG-040` | M | P3 | T | `WP-ATG-01` | EQUIVALENCE PARTITIONING |
| `TOOL-ATG-050` | M | P3 | T | `WP-ATG-01` | DECISION TABLE |
| `TOOL-ATG-060` | M | P3 | T | `WP-ATG-05` | EQUIVALENCE PARTITIONING |
| `TOOL-ATG-070` | M | P3 | I | `WP-ATG-01` | INSPECTION CHECKLIST |
| `TOOL-ATG-080` | M | P3 | T | `WP-ATG-01` | STATE TRANSITION |
| `TOOL-ATG-090` | S | P3 | T | `WP-ATG-04` | DECISION TABLE |
| `TOOL-ATG-100` | S | P3 | D | `WP-ATG-05` | BOUNDARY VALUE ANALYSIS |
| `TOOL-ATG-110` | S | P3 | T | `WP-ATG-05` | BOUNDARY VALUE ANALYSIS |
| `TOOL-CBT-010` | M | P2 | T | `WP-CBT-01` | EQUIVALENCE PARTITIONING |
| `TOOL-CBT-020` | S | P3 | T | `WP-CBT-02` | EQUIVALENCE PARTITIONING |
| `TOOL-CBT-030` | S | P3 | T | `WP-CBT-02` | BOUNDARY VALUE ANALYSIS |
| `TOOL-CBT-040` | M | P3 | I | `WP-CBT-02` | STATE TRANSITION |
| `TOOL-CBT-050` | S | P3 | T | `WP-CBT-03` | STATE TRANSITION |
| `TOOL-CBT-060` | S | P3 | T | `WP-CBT-03` | STATE TRANSITION |
| `TOOL-CBT-070` | S | P2 | T | `WP-GEN-04` | STATE TRANSITION |
| `TOOL-CBT-080` | C | P3 | T | `WP-CBT-04` | EQUIVALENCE PARTITIONING |
| `TOOL-CIC-010` | M | P1 | D | `WP-CLI-01` | SCENARIO (demonstration) |
| `TOOL-CIC-020` | M | P1 | T | `WP-CLI-01` | EQUIVALENCE PARTITIONING |
| `TOOL-CIC-030` | M | P1 | T | `WP-CLI-02` | DECISION TABLE |
| `TOOL-CIC-040` | M | P1 | D | `WP-CLI-03` | SCENARIO (demonstration) |
| `TOOL-CIC-050` | S | P2 | D | `WP-CLI-04` | SCENARIO (demonstration) |
| `TOOL-CIC-060` | S | P3 | T | `WP-CLI-05` | EQUIVALENCE PARTITIONING |
| `TOOL-CIC-070` | S | P2 | T | `WP-CLI-04` | EQUIVALENCE PARTITIONING |
| `TOOL-CIC-080` | S | P2 | I | `WP-PRJ-01` | INSPECTION CHECKLIST |
| `TOOL-COV-010` | M | P1 | T | `WP-COV-01` | EQUIVALENCE PARTITIONING |
| `TOOL-COV-020` | M | P1 | T | `WP-COV-01` | DECISION TABLE |
| `TOOL-COV-030` | M | P3 | T | `WP-COV-04` | EQUIVALENCE PARTITIONING |
| `TOOL-COV-040` | S | P3 | T | `WP-COV-04` | EQUIVALENCE PARTITIONING |
| `TOOL-COV-050` | M | P3 | T | `WP-COV-05` | DECISION TABLE |
| `TOOL-COV-060` | M | P3 | I | `WP-COV-05` | INSPECTION CHECKLIST |
| `TOOL-COV-070` | M | P3 | T | `WP-COV-05` | DECISION TABLE |
| `TOOL-COV-080` | M | P3 | T | `WP-COV-06` | BOUNDARY VALUE ANALYSIS |
| `TOOL-COV-090` | S | P4 | T | `WP-COV-10` | DECISION TABLE |
| `TOOL-COV-100` | M | P3 | T | `WP-COV-07` | SCENARIO (demonstration) |
| `TOOL-COV-110` | M | P1 | T | `WP-COV-02` | EQUIVALENCE PARTITIONING |
| `TOOL-COV-120` | M | P1 | T | `WP-COV-02` | EQUIVALENCE PARTITIONING |
| `TOOL-COV-130` | M | P1 | T | `WP-COV-03` | BOUNDARY VALUE ANALYSIS |
| `TOOL-COV-140` | S | P4 | T | `WP-COV-09` | STATE TRANSITION |
| `TOOL-COV-150` | M | P3 | I | `WP-COV-09` | STATE TRANSITION |
| `TOOL-COV-160` | S | P3 | T | `WP-COV-08` | EQUIVALENCE PARTITIONING |
| `TOOL-COV-170` | S | P4 | T | `WP-COV-11` | DECISION TABLE |
| `TOOL-EXE-010` | M | P1 | T | `WP-EXH-01` | EQUIVALENCE PARTITIONING |
| `TOOL-EXE-020` | M | P1 | T | `WP-EXH-01` | EQUIVALENCE PARTITIONING |
| `TOOL-EXE-030` | M | P1 | T | `WP-EXH-02` | DECISION TABLE |
| `TOOL-EXE-040` | M | P1 | T | `WP-EXH-02` | BOUNDARY VALUE ANALYSIS |
| `TOOL-EXE-050` | S | P1 | T | `WP-EXH-03` | BOUNDARY VALUE ANALYSIS |
| `TOOL-EXE-060` | M | P1 | T | `WP-EXH-02` | DECISION TABLE |
| `TOOL-EXE-070` | S | P2 | T | `WP-EXH-04` | EQUIVALENCE PARTITIONING |
| `TOOL-EXE-080` | S | P1 | T | `WP-BLD-01` | STATE TRANSITION |
| `TOOL-EXE-090` | S | P2 | T | `WP-BLD-02` | BOUNDARY VALUE ANALYSIS |
| `TOOL-HAR-010` | M | P2 | T | `WP-GEN-01` | EQUIVALENCE PARTITIONING |
| `TOOL-HAR-020` | M | P2 | T | `WP-GEN-01` | EQUIVALENCE PARTITIONING |
| `TOOL-HAR-030` | S | P2 | T | `WP-GEN-03` | EQUIVALENCE PARTITIONING |
| `TOOL-HAR-040` | M | P2 | T | `WP-GEN-01` | BOUNDARY VALUE ANALYSIS |
| `TOOL-HAR-050` | M | P2 | T | `WP-GEN-01` | EQUIVALENCE PARTITIONING |
| `TOOL-HAR-060` | M | P2 | T | `WP-GEN-02` | PAIRWISE |
| `TOOL-HAR-065` | C | P3 | T | `WP-GEN-10` | EQUIVALENCE PARTITIONING |
| `TOOL-HAR-070` | S | P2 | A | `WP-GEN-02` | ANALYSIS ARGUMENT |
| `TOOL-HAR-080` | M | P2 | T | `WP-GEN-03` | EQUIVALENCE PARTITIONING |
| `TOOL-HAR-090` | M | P2 | I | `WP-GEN-04` | INSPECTION CHECKLIST |
| `TOOL-HAR-100` | M | P2 | T | `WP-GEN-04` | DECISION TABLE |
| `TOOL-HAR-110` | S | P2 | T | `WP-GEN-04` | STATE TRANSITION |
| `TOOL-HAR-120` | M | P2 | T | `WP-GEN-05` | DECISION TABLE |
| `TOOL-ING-010` | M | P1 | T | `WP-ING-01` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-020` | M | P1 | T | `WP-ING-01` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-030` | M | P1 | T | `WP-ING-01` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-040` | M | P1 | D | `WP-ING-01` | SCENARIO (demonstration) |
| `TOOL-ING-050` | S | P2 | D | `WP-ING-02` | SCENARIO (demonstration) |
| `TOOL-ING-060` | S | P2 | T | `WP-ING-02` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-070` | S | P2 | T | `WP-ING-03` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-080` | C | P2 | T | `WP-ING-02` | BOUNDARY VALUE ANALYSIS |
| `TOOL-ING-090` | S | P2 | T | `WP-ING-03` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-100` | S | P2 | T | `WP-ING-03` | STATE TRANSITION |
| `TOOL-ING-110` | C | P3 | T | `WP-ING-06` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-120` | M | P2 | T | `WP-ING-04` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-130` | M | P2 | T | `WP-ING-04` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-140` | M | P2 | T | `WP-ING-04` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-150` | M | P2 | T | `WP-ING-04` | PAIRWISE |
| `TOOL-ING-160` | S | P2 | T | `WP-ING-05` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-170` | S | P2 | T | `WP-ING-05` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-180` | S | P2 | T | `WP-ING-05` | EQUIVALENCE PARTITIONING |
| `TOOL-ING-190` | S | P2 | I | `WP-ING-04` | INSPECTION CHECKLIST |
| `TOOL-INS-010` | M | P2 | D | `WP-PKG-01` | SCENARIO (demonstration) |
| `TOOL-INS-020` | M | P2 | D | `WP-PKG-01` | SCENARIO (demonstration) |
| `TOOL-INS-030` | M | P2 | D | `WP-PKG-01` | SCENARIO (demonstration) |
| `TOOL-INS-040` | M | P2 | I | `WP-PKG-02` | INSPECTION CHECKLIST |
| `TOOL-INS-050` | M | P2 | T | `WP-PKG-03` | PAIRWISE |
| `TOOL-INS-060` | M | P2 | T | `WP-PKG-03` | DECISION TABLE |
| `TOOL-INS-070` | M | P2 | D | `WP-PKG-04` | SCENARIO (demonstration) |
| `TOOL-INS-080` | M | P2 | T | `WP-TCH-07` | EQUIVALENCE PARTITIONING |
| `TOOL-INS-090` | S | P2 | D | `WP-PKG-05` | SCENARIO (demonstration) |
| `TOOL-INS-100` | S | P3 | D | `WP-PKG-06` | SCENARIO (demonstration) |
| `TOOL-INS-110` | M | P2 | T | `WP-CORE-04` | EQUIVALENCE PARTITIONING |
| `TOOL-LIC-010` | M | P1 | I | `WP-PKG-07` | INSPECTION CHECKLIST |
| `TOOL-LIC-020` | M | P1 | I | `WP-PKG-07` | INSPECTION CHECKLIST |
| `TOOL-LIC-030` | M | P1 | I | `WP-PKG-07` | INSPECTION CHECKLIST |
| `TOOL-LIC-040` | M | P2 | I | `WP-PKG-07` | INSPECTION CHECKLIST |
| `TOOL-LIC-050` | M | P2 | I | `WP-PKG-07` | INSPECTION CHECKLIST |
| `TOOL-LIC-060` | S | P2 | I | `WP-PKG-07` | INSPECTION CHECKLIST |
| `TOOL-LIC-070` | S | P3 | I | `WP-PKG-08` | INSPECTION CHECKLIST |
| `TOOL-MIG-010` | M | P2 | T | `WP-MIG-01` | EQUIVALENCE PARTITIONING |
| `TOOL-MIG-020` | S | P2 | T | `WP-MIG-02` | EQUIVALENCE PARTITIONING |
| `TOOL-MIG-030` | S | P3 | T | `WP-MIG-04` | EQUIVALENCE PARTITIONING |
| `TOOL-MIG-040` | M | P3 | T | `WP-MIG-05` | DECISION TABLE |
| `TOOL-MIG-050` | S | P3 | T | `WP-MIG-04` | PAIRWISE |
| `TOOL-MIG-060` | M | P2 | T | `WP-TCM-06` | EQUIVALENCE PARTITIONING |
| `TOOL-MIG-070` | S | P3 | T | `WP-MIG-06` | EQUIVALENCE PARTITIONING |
| `TOOL-MIG-080` | S | P4 | T | `WP-REP-10` | EQUIVALENCE PARTITIONING |
| `TOOL-MIG-090` | C | P4 | T | `WP-MIG-07` | STATE TRANSITION |
| `TOOL-MIG-100` | M | P2 | I | `WP-MIG-03` | INSPECTION CHECKLIST |
| `TOOL-NFR-010` | M | P1 | T | `WP-CORE-03` | BOUNDARY VALUE ANALYSIS |
| `TOOL-NFR-020` | S | P2 | T | `WP-CORE-03` | EQUIVALENCE PARTITIONING |
| `TOOL-NFR-030` | M | P2 | D | `WP-CORE-05` | SCENARIO (demonstration) |
| `TOOL-NFR-040` | S | P2 | D | `WP-CORE-05` | SCENARIO (demonstration) |
| `TOOL-NFR-050` | M | P2 | A | `WP-CORE-05` | BOUNDARY VALUE ANALYSIS |
| `TOOL-NFR-060` | M | P1 | A | `WP-CORE-01` | ANALYSIS ARGUMENT |
| `TOOL-NFR-070` | M | P1 | I | `WP-CORE-01` | INSPECTION CHECKLIST |
| `TOOL-NFR-080` | M | P1 | I | `WP-CORE-01` | INSPECTION CHECKLIST |
| `TOOL-NFR-090` | M | P2 | T | `WP-CORE-02` | DECISION TABLE |
| `TOOL-NFR-100` | M | P2 | I | `WP-CORE-03` | INSPECTION CHECKLIST |
| `TOOL-NFR-110` | S | P2 | I | `WP-PKG-09` | INSPECTION CHECKLIST |
| `TOOL-NFR-120` | M | P2 | I | `WP-CORE-07` | INSPECTION CHECKLIST |
| `TOOL-NFR-130` | S | P2 | T | `WP-CORE-06` | EQUIVALENCE PARTITIONING |
| `TOOL-NFR-140` | M | P2 | A | `WP-CORE-08` | ANALYSIS ARGUMENT |
| `TOOL-NFR-150` | S | P2 | D | `WP-CORE-05` | SCENARIO (demonstration) |
| `TOOL-NFR-160` | M | P2 | T | `WP-CORE-06` | BOUNDARY VALUE ANALYSIS |
| `TOOL-NFR-170` | S | P3 | D | `WP-CORE-08` | SCENARIO (demonstration) |
| `TOOL-NFR-180` | M | P2 | T | `WP-CORE-02` | STATE TRANSITION |
| `TOOL-NFR-190` | S | P2 | I | `WP-CORE-07` | INSPECTION CHECKLIST |
| `TOOL-PAR-010` | M | P2 | T | `WP-ANA-01` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-020` | M | P2 | T | `WP-ANA-01` | PAIRWISE |
| `TOOL-PAR-030` | M | P2 | T | `WP-ANA-02` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-040` | M | P2 | T | `WP-ANA-02` | PAIRWISE |
| `TOOL-PAR-050` | M | P2 | T | `WP-ANA-02` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-060` | M | P2 | T | `WP-ANA-03` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-070` | S | P2 | T | `WP-ANA-05` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-080` | S | P2 | T | `WP-ANA-06` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-090` | S | P2 | T | `WP-ANA-06` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-100` | M | P2 | T | `WP-ANA-04` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-110` | S | P2 | A | `WP-ANA-04` | ANALYSIS ARGUMENT |
| `TOOL-PAR-120` | C | P3 | T | `WP-ANA-05` | EQUIVALENCE PARTITIONING |
| `TOOL-PAR-130` | S | P2 | T | `WP-ANA-07` | DECISION TABLE |
| `TOOL-PLG-010` | M | P2 | A | `WP-PLG-01` | ANALYSIS ARGUMENT |
| `TOOL-PLG-020` | M | P2 | T | `WP-TCH-01` | EQUIVALENCE PARTITIONING |
| `TOOL-PLG-030` | M | P2 | T | `WP-GEN-02` | EQUIVALENCE PARTITIONING |
| `TOOL-PLG-040` | S | P3 | T | `WP-EXT-07` | EQUIVALENCE PARTITIONING |
| `TOOL-PLG-050` | S | P3 | T | `WP-REP-11` | EQUIVALENCE PARTITIONING |
| `TOOL-PLG-060` | M | P2 | I | `WP-API-01` | INSPECTION CHECKLIST |
| `TOOL-PLG-070` | S | P3 | T | `WP-PLG-02` | EQUIVALENCE PARTITIONING |
| `TOOL-PLG-080` | M | P3 | D | `WP-PLG-02` | DECISION TABLE |
| `TOOL-PLG-090` | S | P3 | I | `WP-PLG-03` | INSPECTION CHECKLIST |
| `TOOL-PRJ-010` | M | P2 | I | `WP-PRJ-01` | INSPECTION CHECKLIST |
| `TOOL-PRJ-020` | M | P2 | I | `WP-PRJ-01` | INSPECTION CHECKLIST |
| `TOOL-PRJ-030` | M | P2 | T | `WP-PRJ-02` | STATE TRANSITION |
| `TOOL-PRJ-040` | M | P2 | T | `WP-PRJ-03` | DECISION TABLE |
| `TOOL-PRJ-050` | M | P2 | T | `WP-CORE-01` | EQUIVALENCE PARTITIONING |
| `TOOL-PRJ-060` | M | P2 | T | `WP-PRJ-02` | EQUIVALENCE PARTITIONING |
| `TOOL-PRJ-070` | M | P2 | I | `WP-PRJ-01` | INSPECTION CHECKLIST |
| `TOOL-PRJ-080` | M | P2 | I | `WP-CORE-01` | INSPECTION CHECKLIST |
| `TOOL-PRJ-090` | S | P3 | T | `WP-PRJ-04` | EQUIVALENCE PARTITIONING |
| `TOOL-PRJ-100` | M | P4 | T | `WP-PRJ-05` | EQUIVALENCE PARTITIONING |
| `TOOL-PRJ-110` | S | P4 | T | `WP-PRJ-05` | STATE TRANSITION |
| `TOOL-QUA-010` | M | P4 | I | `WP-QUA-01` | INSPECTION CHECKLIST |
| `TOOL-QUA-020` | M | P4 | I | `WP-QUA-02` | INSPECTION CHECKLIST |
| `TOOL-QUA-030` | M | P4 | I | `WP-QUA-03` | INSPECTION CHECKLIST |
| `TOOL-QUA-040` | M | P4 | I | `WP-QUA-04` | INSPECTION CHECKLIST |
| `TOOL-QUA-050` | M | P4 | I | `WP-PKG-02` | INSPECTION CHECKLIST |
| `TOOL-QUA-060` | M | P4 | T | `WP-CORE-04` | EQUIVALENCE PARTITIONING |
| `TOOL-QUA-070` | S | P4 | I | `WP-QUA-05` | INSPECTION CHECKLIST |
| `TOOL-QUA-080` | S | P4 | I | `WP-QUA-06` | INSPECTION CHECKLIST |
| `TOOL-QUA-090` | M | P4 | I | `WP-QUA-07` | INSPECTION CHECKLIST |
| `TOOL-QUA-100` | C | P4 | I | `WP-QUA-08` | INSPECTION CHECKLIST |
| `TOOL-REP-010` | M | P1 | T | `WP-REP-02` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-020` | M | P1 | T | `WP-REP-02` | PAIRWISE |
| `TOOL-REP-030` | M | P1 | T | `WP-REP-03` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-040` | M | P2 | T | `WP-REP-03` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-050` | M | P3 | T | `WP-REP-04` | BOUNDARY VALUE ANALYSIS |
| `TOOL-REP-060` | M | P4 | T | `WP-REP-05` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-070` | M | P4 | I | `WP-REP-06` | INSPECTION CHECKLIST |
| `TOOL-REP-080` | M | P4 | T | `WP-REP-07` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-090` | S | P2 | A | `WP-REP-01` | ANALYSIS ARGUMENT |
| `TOOL-REP-100` | M | P2 | T | `WP-REP-01` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-110` | S | P3 | T | `WP-REP-08` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-120` | S | P4 | T | `WP-REP-08` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-130` | M | P4 | I | `WP-REP-06` | INSPECTION CHECKLIST |
| `TOOL-REP-140` | M | P4 | T | `WP-REP-05` | EQUIVALENCE PARTITIONING |
| `TOOL-REP-150` | S | P4 | T | `WP-REP-09` | STATE TRANSITION |
| `TOOL-SEC-010` | M | P2 | I | `WP-SEC-01` | INSPECTION CHECKLIST |
| `TOOL-SEC-020` | M | P2 | I | `WP-SEC-01` | INSPECTION CHECKLIST |
| `TOOL-SEC-030` | M | P2 | D | `WP-SEC-02` | SCENARIO (demonstration) |
| `TOOL-SEC-040` | M | P2 | I | `WP-SEC-02` | INSPECTION CHECKLIST |
| `TOOL-SEC-050` | M | P2 | D | `WP-SEC-03` | SCENARIO (demonstration) |
| `TOOL-SEC-060` | S | P3 | T | `WP-SEC-06` | BOUNDARY VALUE ANALYSIS |
| `TOOL-SEC-070` | M | P2 | T | `WP-SEC-03` | EQUIVALENCE PARTITIONING |
| `TOOL-SEC-080` | M | P2 | I | `WP-SEC-05` | INSPECTION CHECKLIST |
| `TOOL-SEC-090` | M | P3 | T | `WP-SEC-07` | EQUIVALENCE PARTITIONING |
| `TOOL-SEC-100` | S | P3 | I | `WP-SEC-09` | INSPECTION CHECKLIST |
| `TOOL-SEC-110` | M | P3 | T | `WP-SEC-08` | EQUIVALENCE PARTITIONING |
| `TOOL-SEC-120` | M | P2 | T | `WP-SEC-04` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-010` | M | P2 | T | `WP-GEN-06` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-020` | M | P2 | T | `WP-GEN-06` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-030` | M | P2 | T | `WP-GEN-06` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-040` | M | P2 | T | `WP-GEN-07` | STATE TRANSITION |
| `TOOL-STB-050` | M | P2 | T | `WP-GEN-07` | BOUNDARY VALUE ANALYSIS |
| `TOOL-STB-060` | S | P2 | T | `WP-GEN-07` | STATE TRANSITION |
| `TOOL-STB-070` | M | P2 | T | `WP-GEN-07` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-080` | M | P2 | T | `WP-GEN-08` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-090` | S | P3 | T | `WP-GEN-11` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-100` | S | P2 | T | `WP-GEN-08` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-110` | M | P2 | T | `WP-GEN-09` | BOUNDARY VALUE ANALYSIS |
| `TOOL-STB-120` | M | P2 | T | `WP-GEN-09` | DECISION TABLE |
| `TOOL-STB-130` | S | P2 | T | `WP-GEN-09` | EQUIVALENCE PARTITIONING |
| `TOOL-STB-140` | S | P2 | T | `WP-GEN-08` | EQUIVALENCE PARTITIONING |
| `TOOL-TCD-010` | M | P1 | T | `WP-TCM-01` | EQUIVALENCE PARTITIONING |
| `TOOL-TCD-020` | M | P2 | T | `WP-TCM-02` | EQUIVALENCE PARTITIONING |
| `TOOL-TCD-030` | M | P2 | I | `WP-TCM-02` | INSPECTION CHECKLIST |
| `TOOL-TCD-040` | M | P2 | T | `WP-TCM-02` | EQUIVALENCE PARTITIONING |
| `TOOL-TCD-050` | M | P2 | T | `WP-TCM-03` | PAIRWISE |
| `TOOL-TCD-060` | M | P2 | T | `WP-TCM-03` | BOUNDARY VALUE ANALYSIS |
| `TOOL-TCD-070` | S | P2 | T | `WP-TCM-05` | BOUNDARY VALUE ANALYSIS |
| `TOOL-TCD-080` | S | P2 | T | `WP-TCM-04` | EQUIVALENCE PARTITIONING |
| `TOOL-TCD-090` | M | P2 | A | `WP-TCM-04` | ANALYSIS ARGUMENT |
| `TOOL-TCD-100` | S | P2 | T | `WP-TCM-06` | PAIRWISE |
| `TOOL-TCD-110` | S | P3 | T | `WP-TCM-07` | BOUNDARY VALUE ANALYSIS |
| `TOOL-TCD-120` | C | P3 | T | `WP-TCM-07` | EQUIVALENCE PARTITIONING |
| `TOOL-TCD-130` | S | P2 | T | `WP-TCM-05` | BOUNDARY VALUE ANALYSIS |
| `TOOL-TCD-140` | M | P2 | T | `WP-TCM-02` | STATE TRANSITION |
| `TOOL-TCH-010` | M | P1 | T | `WP-TCH-02` | PAIRWISE |
| `TOOL-TCH-020` | M | P1 | T | `WP-TCH-01` | EQUIVALENCE PARTITIONING |
| `TOOL-TCH-030` | M | P3 | T | `WP-TCH-03` | BOUNDARY VALUE ANALYSIS |
| `TOOL-TCH-040` | S | P3 | T | `WP-TCH-03` | EQUIVALENCE PARTITIONING |
| `TOOL-TCH-050` | S | P3 | I | `WP-TCH-03` | INSPECTION CHECKLIST |
| `TOOL-TCH-060` | M | P3 | T | `WP-TCH-04` | DECISION TABLE |
| `TOOL-TCH-070` | M | P3 | T | `WP-TCH-04` | DECISION TABLE |
| `TOOL-TCH-080` | S | P3 | T | `WP-TCH-05` | PAIRWISE |
| `TOOL-TCH-090` | S | P3 | D | `WP-TCH-05` | SCENARIO (demonstration) |
| `TOOL-TCH-100` | C | P3 | T | `WP-TCH-06` | PAIRWISE |
| `TOOL-TGT-010` | M | P3 | T | `WP-BLD-03` | EQUIVALENCE PARTITIONING |
| `TOOL-TGT-020` | M | P3 | T | `WP-EXT-01` | PAIRWISE |
| `TOOL-TGT-030` | M | P3 | T | `WP-EXT-02` | EQUIVALENCE PARTITIONING |
| `TOOL-TGT-040` | M | P3 | T | `WP-EXT-02` | PAIRWISE |
| `TOOL-TGT-050` | M | P3 | T | `WP-EXT-03` | PAIRWISE |
| `TOOL-TGT-060` | M | P3 | A | `WP-EXT-03` | ANALYSIS ARGUMENT |
| `TOOL-TGT-070` | M | P3 | T | `WP-EXT-04` | PAIRWISE |
| `TOOL-TGT-080` | S | P3 | D | `WP-EXT-05` | SCENARIO (demonstration) |
| `TOOL-TGT-090` | S | P3 | T | `WP-EXT-05` | DECISION TABLE |
| `TOOL-TGT-100` | S | P3 | T | `WP-EXT-06` | BOUNDARY VALUE ANALYSIS |
| `TOOL-TGT-110` | M | P3 | A | `WP-EXT-06` | ANALYSIS ARGUMENT |
| `TOOL-TGT-120` | C | P3 | T | `WP-EXT-07` | EQUIVALENCE PARTITIONING |
| `TOOL-TRC-010` | M | P4 | T | `WP-TRC-01` | EQUIVALENCE PARTITIONING |
| `TOOL-TRC-020` | M | P4 | T | `WP-TRC-01` | PAIRWISE |
| `TOOL-TRC-030` | M | P4 | T | `WP-TRC-01` | STATE TRANSITION |
| `TOOL-TRC-040` | M | P4 | T | `WP-TRC-02` | EQUIVALENCE PARTITIONING |
| `TOOL-TRC-050` | S | P4 | T | `WP-TRC-03` | PAIRWISE |
| `TOOL-TRC-060` | S | P4 | T | `WP-TRC-03` | PAIRWISE |
| `TOOL-TRC-070` | S | P4 | T | `WP-TRC-04` | PAIRWISE |
| `TOOL-TRC-080` | S | P4 | T | `WP-TRC-05` | EQUIVALENCE PARTITIONING |
| `TOOL-TRC-090` | S | P4 | T | `WP-TRC-05` | STATE TRANSITION |
| `TOOL-TRC-100` | C | P4 | T | `WP-TRC-04` | DECISION TABLE |
| `TOOL-UIX-010` | M | P1 | A | `WP-API-01` | ANALYSIS ARGUMENT |
| `TOOL-UIX-020` | M | P2 | A | `WP-API-01` | ANALYSIS ARGUMENT |
| `TOOL-UIX-030` | M | P2 | D | `WP-GUI-01` | SCENARIO (demonstration) |
| `TOOL-UIX-040` | M | P2 | I | `WP-GUI-01` | INSPECTION CHECKLIST |
| `TOOL-UIX-050` | M | P2 | T | `WP-API-02` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-060` | M | P2 | T | `WP-GUI-02` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-070` | M | P2 | T | `WP-GUI-02` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-080` | M | P2 | T | `WP-GUI-03` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-090` | M | P2 | T | `WP-GUI-04` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-100` | S | P2 | T | `WP-GUI-02` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-110` | M | P2 | T | `WP-GUI-05` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-120` | M | P2 | T | `WP-GUI-05` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-130` | M | P2 | T | `WP-GUI-05` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-140` | S | P2 | T | `WP-GUI-05` | BOUNDARY VALUE ANALYSIS |
| `TOOL-UIX-150` | M | P3 | T | `WP-GUI-10` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-160` | M | P3 | T | `WP-GUI-11` | BOUNDARY VALUE ANALYSIS |
| `TOOL-UIX-170` | M | P3 | T | `WP-GUI-11` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-180` | M | P3 | T | `WP-GUI-12` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-190` | S | P3 | T | `WP-GUI-13` | BOUNDARY VALUE ANALYSIS |
| `TOOL-UIX-200` | S | P3 | T | `WP-GUI-14` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-210` | M | P2 | T | `WP-GUI-06` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-220` | M | P2 | T | `WP-GUI-06` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-230` | M | P3 | T | `WP-GUI-15` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-240` | S | P2 | T | `WP-GUI-07` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-250` | M | P2 | T | `WP-GUI-08` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-260` | M | P3 | T | `WP-GUI-16` | BOUNDARY VALUE ANALYSIS |
| `TOOL-UIX-270` | S | P3 | T | `WP-GUI-17` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-280` | M | P2 | T | `WP-GUI-08` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-290` | S | P4 | T | `WP-GUI-19` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-300` | M | P4 | T | `WP-GUI-20` | BOUNDARY VALUE ANALYSIS |
| `TOOL-UIX-310` | S | P4 | T | `WP-GUI-21` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-320` | M | P1 | I | `WP-PRJ-01` | INSPECTION CHECKLIST |
| `TOOL-UIX-330` | M | P2 | T | `WP-API-03` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-340` | M | P2 | T | `WP-GUI-01` | PAIRWISE |
| `TOOL-UIX-350` | M | P2 | I | `WP-GUI-01` | INSPECTION CHECKLIST |
| `TOOL-UIX-360` | S | P2 | D | `WP-GUI-09` | SCENARIO (demonstration) |
| `TOOL-UIX-370` | S | P3 | T | `WP-GUI-18` | BOUNDARY VALUE ANALYSIS |
| `TOOL-UIX-380` | C | P4 | T | `WP-GUI-22` | EQUIVALENCE PARTITIONING |
| `TOOL-UIX-390` | F | — | — | — (Future, not allocated) | — (deferred) |
| `TOOL-UIX-400` | F | — | — | — (Future, not allocated) | — (deferred) |

---

*Generated 2026-08-27. Regenerate §2, §5.5, §6.2, §7 and Appendix A whenever `design/trace/requirement-matrix.csv` changes.*
