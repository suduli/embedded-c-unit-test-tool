# SDD-002 — Interface Design

**Document ID:** SDD-002
**Version:** 0.1 (draft for review)
**Status:** Draft — tracks SRS-001 v0.1
**Upstream:** SDD-001, SRS-001 v0.1

---

<!-- nav:start -->
**Related documents** — [SRS-001](../SRS-001-requirements.md) · [ADR-001](../ADR-001-architecture-decisions.md) · [SDD-001](SDD-001-architecture.md) · **SDD-002** *(you are here)* · [SDD-003](SDD-003-data-model.md) · [SDD-004](SDD-004-traceability-architecture.md) · [Register](trace/design-elements.yaml) · [Design index](README.md)

Architecture diagrams: [specifications](diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 1. Purpose

SDD-001 describes what the components are. This document describes the
contracts between them — specifically the seven seams where a contract is
load-bearing enough that changing it unilaterally breaks something else.

A seam is listed here if at least one of these is true:

- It is published to users or extension authors, so it cannot change silently.
- It exists to isolate a decision that is not yet made (ADR-001 through -007).
- Two or more components depend on it agreeing with itself.

Anything not on this list is an internal call and may be refactored freely.

---

## 2. Seam register

| # | Seam | Between | Published | Versioned | Isolates |
|---|---|---|---|---|---|
| S1 | Analysis Model | `CMP-ANA` → L2 | Documented | Yes | Core language (ADR-001 §2) |
| S2 | Test Case Model | `CMP-TCM` ↔ L2/L3/L5 | User-facing | Yes | Data format (ADR-002) |
| S3 | Result Set | `CMP-EXH`/`CMP-EXT` → L4 | Internal | Yes | Framework and host/target |
| S4 | Coverage Model | `CMP-COV` → L4 | Internal | Yes | Coverage backend (ADR-004) |
| S5 | Report Model | `CMP-REP` → renderers | Documented | Yes | Report formats |
| S6 | Engine API | Engine ↔ front-ends | Documented | Yes | GUI technology (ADR-001 §3) |
| S7 | Extension points | Tool ↔ extensions | Documented | Yes | Compiler/framework/target/report breadth |

Plus one internal port that exists purely to keep the layer graph acyclic:

| # | Port | Declared by | Implemented by | Reason |
|---|---|---|---|---|
| P1 | `TestValidationPort` | `CMP-ATG` | `CMP-BLD`, `CMP-EXH`, `CMP-COV` | ATG (L2) must build, run, and measure (L3/L4) — DSN-ATG-110 |

---

## 3. Versioning rule

Every seam above carries an explicit `schema_version` or `interface_version` as
a **required** field, present as the first key where the encoding has an order.

- **Minor bump** — a field is added, or an enumeration gains a member that older
  readers may ignore. Readers accept any minor version at or above the one they
  were written for and ignore unknown fields.
- **Major bump** — a field is removed, renamed, or changes meaning. Readers
  **reject** a major version they do not implement and say so, naming both
  versions. They never attempt a best-effort read.

Rejection rather than degradation is deliberate. A downstream stage that
half-understands an analysis model produces a harness that compiles and is
wrong, which is worse than one that does not run (TOOL-PAR-110, TOOL-NFR-090).

Extension interfaces follow the same rule, with breaking changes documented
with a migration path (TOOL-PLG-060, DSN-API-020).

---

## 4. S1 — Analysis Model

**Producer:** `CMP-ANA` only. **Consumers:** `CMP-GEN`, `CMP-TCM`, `CMP-ATG`,
`CMP-COV`, `CMP-CBT`, `CMP-TRC`.
**Requirements:** TOOL-PAR-100, TOOL-PAR-110. **Elements:** DSN-ANA-070.

This is the most important interface in the system. It is the reason a language
change (ADR-001 §2) costs one component instead of the whole tool.

**The rule that gives it force:** no component outside `CMP-ANA` may link,
import, or invoke a C front-end. Not "should not" — the dependency is absent
from every other component's manifest, so a violation fails the build rather
than review.

### 4.1 Shape

```jsonc
{
  "schema_version": "1.0",
  "provenance": { "tool_version": "...", "front_end": "libclang 18.1.8",
                  "generated_at": "...", "inputs": [{"path": "...", "digest": "..."}] },
  "scope": { "id": "scope.driver_integration", "units": ["src/a.c", "src/b.c"] },
  "units": [{
    "path": "src/a.c",
    "status": "parsed",                    // parsed | failed  (DSN-ANA-090)
    "diagnostics": [],
    "functions": [{
      "name": "adc_read",
      "linkage": "external",               // external | internal
      "storage_class": "none",             // none | static
      "location": { "file": "src/a.c", "line": 42 },
      "return_type": "ref:type.uint16",
      "parameters": [{ "name": "ch", "type": "ref:type.adc_channel_t",
                       "direction": "in" }],  // in | out | inout | unknown
      "globals": [{ "name": "g_adc_state", "access": "rw" }],
      "calls": [{ "callee": "hal_read", "classification": "external",
                  "via": "direct" }],       // direct | function_pointer
      "decisions": [{ "id": "d1", "line": 51, "conditions": 3 }],
      "complexity": 4,
      "annotations": [{ "kind": "macro_obscured_interface", "detail": "..." }]
    }],
    "cfg": null                            // present only if the provider declares it
  }],
  "types": { "type.adc_channel_t": { "kind": "enum", "enumerators": [...] } },
  "capabilities": { "cfg": false }          // DSN-ANA-040
}
```

### 4.2 Contract points

| Point | Rule | Why |
|---|---|---|
| Type closure | `types` is transitively complete for every referenced type | A stub must compile standalone (TOOL-STB-030) |
| Scope classification | `calls[].classification` is a function of the scope, not the file | One parse serves several scopes (DSN-ING-110) |
| CFG optionality | `capabilities.cfg` is authoritative; `cfg` is `null` when false | libclang cannot supply a CFG (ADR-001 §2.1) |
| Partial results | A failed unit appears with `status: "failed"` and diagnostics | An incomplete model must be visibly incomplete (DSN-ANA-090) |
| Unhandled constructs | Recorded as `annotations`, never omitted | Feeds the greppable markers of DSN-GEN-150 |
| Decision inventory | `decisions[]` is emitted whether or not coverage runs | Reconciling against coverage output is what detects non-instrumented expressions (DSN-COV-040) |

That last point is easy to miss and expensive to retrofit. Without an
independent decision inventory from the analyzer, there is nothing to compare
the compiler's coverage output against, and a decision the compiler declined to
instrument is indistinguishable from one that was fully covered.

---

## 5. S2 — Test Case Model

**Owner:** `CMP-TCM`. **Consumers:** `CMP-GEN`, `CMP-ATG`, `CMP-EXH`,
`CMP-EXT`, `CMP-TRC`, `CMP-MIG`, `CMP-AIF`; and `CMP-GUI` across the engine API.
**Requirements:** TOOL-TCD-020..060, TOOL-TCD-140. **Elements:** DSN-TCM-020,
DSN-TCM-030, DSN-TCM-110.

User-facing, so its surface syntax is an ADR-002 decision. What is fixed here
is the *model*, which the serialisation adapter renders into whatever syntax
ADR-002 chooses.

```jsonc
{
  "schema_version": "1.0",
  "id": "tc.adc_read.nominal.7f3a",   // assigned at creation, never derived (DSN-TCM-110)
  "unit": "src/a.c", "function": "adc_read",
  "kind": "data",                      // data | c_source
  "origin": { "author": "human" },     // human | atg | ai   (+ engine/model, review state)
  "requirements": ["SW-REQ-114"],
  "inputs":   { "parameters": { "ch": "ADC_CH_VBAT" },
                "globals":    { "g_adc_state": { "calibrated": true } } },
  "expected": { "return": 4095,
                "globals": { "g_adc_state.last_error": 0 },
                "out_parameters": {},
                "comparison": { "g_adc_gain": { "tolerance": { "relative": 1e-6 } } } },
  "stubs": { "hal_read": { "mode": "sequence", "returns": [0, 4095],
                           "expect_calls": 2, "out_parameters": {} } }
}
```

### 5.1 Contract points

- **Identity is assigned, not derived.** Editing a test's values must not change
  its id, because coverage attribution, traceability links, and run comparison
  all key on it (DSN-TCM-110). A content-derived id would silently break all
  three on every edit.
- **Type-directed comparison.** How a value is compared follows from its
  declared C type in S1, with explicit per-field overrides for pointer policy,
  float tolerance, and union active member (DSN-TCM-030). Padding is excluded
  from struct comparison.
- **One model for both kinds.** A `c_source` test carries the same identity,
  requirement links, and origin as a `data` test. Everything downstream —
  selection, execution, attribution, reporting — is indifferent to which it is.
- **Origin travels with the case.** `origin` is how ATG-generated and
  AI-generated cases stay marked in every report (TOOL-ATG-070, TOOL-AIF-080)
  and how unreviewed expectations stay distinguishable from specified ones
  (TOOL-ATG-080).
- **Round-trip.** The CSV interchange of DSN-TCM-070 is defined as a lossless
  projection of this model, or it reports the loss. It is half of the
  anti-lock-in obligation (TOOL-MIG-060); the results half is S5's open output
  formats. Import loss reporting is a separate obligation (TOOL-MIG-040,
  DSN-MIG-040).

---

## 6. S3 — Result Set

**Producers:** `CMP-EXH`, `CMP-EXT`. **Consumers:** `CMP-COV` and `CMP-REP`
directly; `CMP-CBT` reads *persisted* result sets from the store rather than
the runners, which is what lets it compare a run against one recorded months
earlier.
**Requirements:** TOOL-EXE-020, TOOL-TGT-070, TOOL-CBT-040.

Normalisation happens at the runner boundary. Nothing downstream knows which
test framework ran or whether execution was on host, simulator, or hardware —
that information is present as metadata, but no logic branches on it.

```jsonc
{
  "schema_version": "1.0",
  "run_id": "...", "partial": false, "not_executed": [],   // DSN-CBT-030
  "execution": { "where": "target", "target_id": "nucleo-h743",
                 "toolchain": "arm-none-eabi-gcc-14.2", "order_seed": 20260807 },
  "results": [{
    "test_id": "tc.adc_read.nominal.7f3a",
    "outcome": "fail",       // pass | fail | error | timeout | not_run
    "duration_ms": 3,
    "failures": [{ "assertion": "expected_return", "expected": "4095",
                   "actual": "0", "location": {"file": "...", "line": 88} }]
  }],
  "infrastructure_faults": []   // flash failure, no output, reset, watchdog — DSN-EXT-070
}
```

### 6.1 Contract points

- `partial` and `not_executed` are **fields, not report options**. A subset run
  cannot be presented as a full one because the flag travels with the data
  (TOOL-CBT-040, DSN-CBT-030).
- `infrastructure_faults` is a separate channel from `results`. A rig that fails
  to flash must never read as failing software (TOOL-TGT-090).
- `timeout` is a distinct outcome from `fail`, since the diagnosis differs.
- `order_seed` is recorded so a randomised-order failure is reproducible
  (DSN-TCM-060).

---

## 7. S4 — Coverage Model

**Producer:** `CMP-COV`. **Consumers:** `CMP-CBT`, `CMP-REP`, `CMP-GUI`.
**Requirements:** TOOL-COV-060..080, TOOL-COV-120, TOOL-COV-140.

```jsonc
{
  "schema_version": "1.0",
  "mcdc": { "form": "masking", "mechanism": "gcc -fcondition-coverage",
            "gap_to_unique_cause": "..." },              // DSN-COV-020
  "files": [{
    "path": "src/a.c", "role": "uut",                    // uut | harness | stub | framework
    "lines":     [{ "line": 51, "status": "partial", "hits": 3,
                    "attributed_tests": ["tc.adc_read.nominal.7f3a"] }],
    "decisions": [{ "id": "d1", "line": 51, "status": "partial",
                    "conditions": [{ "index": 0, "true": true, "false": false }] }],
    "unmeasured":[{ "id": "d7", "line": 96,
                    "reason": "condition count exceeds compiler limit" }],
    "justified": [{ "construct": "d9", "author": "...", "date": "...",
                    "rationale": "...", "source_digest": "...",
                    "state": "valid" }]                  // valid | expired
  }]
}
```

### 7.1 Contract points

- **`mcdc.form` is data.** Every renderer is obliged to display it. TOOL-COV-060
  demands the form appear in every report; making it a field rather than a
  documentation sentence is what guarantees that (DSN-COV-020).
- **`unmeasured` is not `uncovered`.** A decision the compiler declined to
  instrument is a third state. Collapsing it into either of the other two is the
  most dangerous misreport the tool can make (DSN-COV-040).
- **`justified` has a `state`.** Bound to `source_digest`; when the source moves
  the justification expires rather than continuing to excuse code it no longer
  describes (TOOL-COV-150, DSN-COV-080).
- **`role`** comes from scope membership, not path heuristics, so UUT coverage
  separates cleanly from harness and framework coverage (TOOL-COV-160).
- **`attributed_tests`** is what makes change impact analysis (DSN-CBT-020) and
  suite minimisation (DSN-CBT-050) possible. Absent attribution is treated as
  "affected", so the conservative direction is the default.

---

## 8. S5 — Report Model

**Producer:** `CMP-REP`. **Consumers:** every renderer, including user-supplied
ones.
**Requirements:** TOOL-REP-090, TOOL-PLG-050 (the model itself); TOOL-REP-130,
TOOL-REP-150 (its versioning and offline re-rendering).
**Elements:** DSN-REP-010, with DSN-REP-110 and DSN-REP-130 discharging the
latter two.

The report model is the merge of S3, S4, the traceability matrix, the run
delta, and the provenance record — **persisted**, so that:

- adding a report format needs no tool source change (TOOL-PLG-050);
- a report regenerates from archived data with no re-execution (TOOL-REP-150);
- two renderings of one run cannot disagree, because there is one source.

```jsonc
{
  "schema_version": "1.0", "format_version": "1.0",
  "provenance": { "tool_version": "...", "build_id": "...",
                  "compiler": "...", "target": "...", "timestamp": "..." },
  "scope": { "id": "...", "included": [...], "excluded": [...] },   // TOOL-REP-140
  "results": { /* S3 */ }, "coverage": { /* S4 */ },
  "traceability": { "matrix": [...], "unlinked_requirements": [...],
                    "unlinked_tests": [...] },
  "delta": { "baseline_run": "...", "newly_failing": [...], "newly_passing": [...] },
  "advisories": [{ "kind": "partial_run" }, { "kind": "unreviewed_expectations",
                  "count": 12 }, { "kind": "ai_generated_present", "count": 3 }]
}
```

`advisories` is the single place a renderer looks to discharge its disclosure
obligations. A renderer that ignores it produces a report that overclaims, so
the renderer conformance test (§10) asserts that every advisory present in the
model appears in the output.

`format_version` is separate from `schema_version` because TOOL-REP-130 requires
archived evidence to stay interpretable: the model may evolve while a given
rendered format's definition stays pinned and published.

---

## 9. S6 — Engine API

**Between:** engine and every front-end. **Requirements:** TOOL-UIX-010,
TOOL-UIX-020, TOOL-UIX-050, TOOL-UIX-240, TOOL-UIX-330.
**Elements:** DSN-API-010..040.

### 9.1 Transport

JSON request/response over **stdio** or a **filesystem-permissioned local
socket** (Unix domain socket / named pipe). The engine API offers no TCP
transport — an open localhost port is a host-firewall and endpoint-monitoring
problem in precisely the defence, aerospace, and automotive environments this
tool targets (ADR-001 §3.3, DSN-API-030).

This constrains *this* interface, not the product forever. ADR-001 §3.3 rejects
a localhost server as the **primary** interface and explicitly allows a browser
UI as an *additional* one, which is where TOOL-UIX-400 (deferred, not rejected)
would live. Should that be built, it gets its own transport and its own
security analysis rather than widening S6.

### 9.2 Message shape

```jsonc
// request
{ "interface_version": "1.0", "id": 17, "op": "environment.build",
  "params": { "environment": "env.adc" } }

// response
{ "interface_version": "1.0", "id": 17, "status": "ok",
  "result": { ... },
  "cli_equivalent": "ectt environment build --environment env.adc",   // DSN-API-040
  "diagnostics": [ ... ] }

// progress / cancellation (unsolicited, correlated by id)
{ "interface_version": "1.0", "id": 17, "event": "progress",
  "phase": "compile", "completed": 12, "total": 40, "cancellable": true }
```

### 9.3 Contract points

- **One operation catalogue.** The CLI is generated from the same catalogue the
  API publishes (DSN-CLI-010). A capability cannot become GUI-only by omission,
  because there is no place to add one that the CLI does not see.
- **`cli_equivalent` on every response.** This is what makes the console pane of
  TOOL-UIX-240 and the GUI/CLI round-trip guarantee of TOOL-UIX-330 fall out of
  the design rather than needing separate work per operation.
- **Progress and cancellation are protocol-level**, backed by the cancellation
  tokens of DSN-CORE-040, so long operations are interruptible from any
  front-end and interruption leaves valid state (TOOL-NFR-180).
- **Front-ends hold no capability.** The API surface is the complete capability
  surface. A front-end that needs something the API cannot express is a defect
  in the API, not a reason for a front-end-local implementation.

---

## 10. S7 — Extension points

**Requirements:** TOOL-PLG-010..090, but only four of those live in `CMP-PLG`
(TOOL-PLG-010/070/080/090 → DSN-PLG-010..040). The rest are discharged at the
extension point itself, which is the design: TOOL-PLG-020 → DSN-TCH-010,
TOOL-PLG-030 → DSN-GEN-040, TOOL-PLG-040 → DSN-EXT-010, TOOL-PLG-050 →
DSN-REP-010, TOOL-PLG-060 → DSN-API-020. `CMP-PLG` publishes and loads; it does
not implement the points.

| Extension point | Contribution | Declarative only | Requirements |
|---|---|---|---|
| Compiler configuration | Invocation, flag syntax, output conventions, declared capabilities | Yes | TOOL-TCH-020/040, TOOL-PLG-020 |
| Test framework back-end | Templates + descriptor (assertion macros, runner entry, result form) | Yes | TOOL-HAR-070, TOOL-PLG-030 |
| Target execution method | `flash` / `run` / `collect` behind a documented interface | Script permitted | TOOL-TGT-120, TOOL-PLG-040 |
| Report format | Renderer over the S5 report model | Script permitted | TOOL-REP-090, TOOL-PLG-050 |

Two rules govern all four:

1. **Built-ins use the public interface.** Every shipped compiler
   configuration, framework back-end, and report format is implemented through
   the same extension point offered to users, with no private path
   (DSN-PLG-040, TOOL-PLG-090). This is the only mechanism that reliably keeps
   an extension interface sufficient — an interface with a private bypass
   accumulates gaps that nobody notices until an outside contributor hits one.
2. **Failure is isolated and named.** An extension that fails to load or
   declares an incompatible version is reported by name with the reason, and
   the tool continues with the remainder (DSN-PLG-030, TOOL-PLG-080).

Each point ships a **conformance test** an extension author can run before
publishing. For compiler configurations this includes building and running a
reference suite and confirming the declared coverage capabilities are actually
produced — a configuration that claims MC/DC it cannot deliver is worse than
one that claims nothing (TOOL-TCH-060).

For report formats the conformance test asserts the disclosure obligations: for
every entry in the model's `advisories` array (§8), and for every AI-generated
artifact's model identifier and review state (DSN-AIF-110), the corresponding
marking must appear in the rendered output. A renderer that silently drops an
advisory produces a report that overclaims, which is the one defect class this
design spends the most structure preventing.

---

## 11. P1 — `TestValidationPort`

**Declared by:** `CMP-ATG` (L2). **Implemented by:** `CMP-BLD` (L3),
`CMP-EXH` (L3), `CMP-COV` (L4). **Element:** DSN-ATG-110.

```
build(test_cases)          -> build outcome + diagnostics
execute(built, limits)     -> result set (S3)
measure(built, result_set) -> coverage delta against a baseline (S4)
```

Generation must compile, run, and measure what it produces (TOOL-ATG-050,
TOOL-ATG-060), which are capabilities of higher layers. Rather than depend
upward, `CMP-ATG` declares this port and the implementations are bound at
composition time. Two consequences worth stating: the layer graph stays acyclic
and `trace_check.py` can keep enforcing it, and generation is testable against a
stub port without a toolchain present.

`CMP-AIF` reaches the same validation through `CMP-ATG` rather than binding the
port itself, so the "compile and execute before presentation" gate of
TOOL-AIF-070 is literally the same code as TOOL-ATG-050 — one gate, not two
implementations that can drift apart.

---

## 12. Interface change control

While SRS-001 is unbaselined, these interfaces are drafts. Once SDD-001 is
baselined:

1. A change to S1, S2, S5, S6, or S7 — everything users or extension authors
   can see — requires a version increment per §3 and an entry in the interface
   changelog. S2 is on this list despite being a data format rather than an API:
   it is the most exposed surface of all, since users hand-edit it.
   S3 and S4 are internal and may change with their producers, provided S5 —
   which embeds both — is versioned accordingly.
2. A major increment on S6 or S7 requires a documented migration path
   (TOOL-PLG-060) shipped in the release that introduces it.
3. A change to S5's `format_version` requires the superseded format definition
   to remain published, so archived evidence stays interpretable
   (TOOL-REP-130).
4. Adding a consumer of S1 requires confirming it does not need the CFG, or
   declaring a dependency on `capabilities.cfg` — silently assuming the CFG is
   present is the failure mode that would erode the ADR-001 §2.4 seam.
