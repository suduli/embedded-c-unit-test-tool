# Embedded C Unit Test Tool

An open-source unit and integration testing tool for embedded C software —
a functional alternative to VectorCAST/C++, Cantata, LDRA TBrun/LDRAunit, and
Tessy.

[![Traceability](https://github.com/suduli/embedded-c-unit-test-tool/actions/workflows/traceability.yml/badge.svg)](https://github.com/suduli/embedded-c-unit-test-tool/actions/workflows/traceability.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-design%20phase-orange)](design/README.md)

**This repository is design documentation, not yet an implementation.**
There is no source code to build or install here — what exists is a fully
specified, machine-checked architecture: what the tool must do, how it is
structured to do it, and a validator that proves the two agree. See
[Project status](#project-status) before you go looking for a binary.

## What the tool does

The tool supports the full dynamic testing workflow for C source code:

- **Project ingestion** — pull in a C codebase and its build configuration
- **Interface analysis** — parse with a production C front-end and derive an
  analysis model (no repair of non-building code; the project must already
  compile)
- **Test harness and stub generation** — synthesize the scaffolding a unit
  test needs
- **Automatic and manual test case authoring** — derive cases automatically
  and let engineers write their own against the same model
- **Execution on host and embedded targets** — run the same test case both
  ways
- **Structural coverage up to MC/DC** — measured, not instrumented; coverage
  instrumentation comes from the user's own compiler (gcov/llvm-cov)
- **Requirements traceability** — link requirements to test cases to code
  locations, and check that link, not just record it
- **Certification-oriented reporting** — evidence suitable for ISO 26262,
  IEC 61508, IEC 62304, EN 50128, DO-178C

**Out of scope for v1.0:** C++ support, Ada support, system-level/HIL test
orchestration, static analysis as a primary feature (integration only),
formal verification.

**Intended users:** embedded software engineers doing unit/integration
testing, verification engineers producing certification evidence,
quality/safety managers reviewing coverage and traceability, and CI/CD
engineers automating verification pipelines.

Full detail: [`SRS-001-requirements.md`](SRS-001-requirements.md) — 329
numbered requirements with priority, phase, and verification method.

## Architecture at a glance

24 components across 7 layers, 70 dependency edges, 243 design elements — all
allocated from the 327 in-scope requirements above, and validated by a
checker that fails the build if any requirement goes unallocated or any
diagram disagrees with the design it depicts.

| Layer | Name | Role |
|---|---|---|
| L0 | Platform and Persistence | Determinism, error handling, project storage — everything else depends on it |
| L1 | Comprehension | Reads user code and build configuration, produces the analysis model |
| L2 | Synthesis | Test case derivation and generation, consuming models only |
| L3 | Realization | Build orchestration and execution, on host and on target |
| L4 | Evidence | Coverage, change impact, reporting, traceability |
| L5 | Interfaces | The CLI and desktop front-ends, both on one published engine API |
| L6 | Assurance and Ecosystem | AI assist, migration, packaging, qualification, extension, security |

Explore it interactively:
**[suduli.github.io/embedded-c-unit-test-tool](https://suduli.github.io/embedded-c-unit-test-tool/)**
— a layer map, eight per-layer component views, a full component index with
every id spelled out, and a diagram of how the design documents connect to
one another. Each view is a self-contained page: pan, zoom, search, trace a
relationship, switch theme, export.

## Documentation map

| Document | Content |
|---|---|
| [`SRS-001-requirements.md`](SRS-001-requirements.md) | What the tool must do — 329 requirements, priority, phase, verification method |
| [`ADR-001-architecture-decisions.md`](ADR-001-architecture-decisions.md) | Core language (Python), front-end technology (PySide6), qualification scope — Accepted 2026-09-19 |
| [`ADR-006-fork-or-build-fresh.md`](ADR-006-fork-or-build-fresh.md) | Fork UTBotCpp or build fresh — Accepted: build fresh |
| [`ADR-008-ai-structured-decision-provider.md`](ADR-008-ai-structured-decision-provider.md) | AI provider for structured test-decision validation — one provider extension point, TypeSafe AI (Jev) as opt-in default |
| [`design/SDD-001-architecture.md`](design/SDD-001-architecture.md) | The seven-layer structure, all 24 components, principal flows, cross-cutting rules |
| [`design/SDD-002-interfaces.md`](design/SDD-002-interfaces.md) | The seven load-bearing seams: analysis model, test case model, coverage model, engine API, extension points |
| [`design/SDD-003-data-model.md`](design/SDD-003-data-model.md) | What is written to disk: project/output tree, file granularity, diff stability, schema migration |
| [`design/SDD-004-traceability-architecture.md`](design/SDD-004-traceability-architecture.md) | The trace meta-model, id rules, the checker, and the CI gate |
| [`design/trace/design-elements.yaml`](design/trace/design-elements.yaml) | **The authoritative register.** Where every document disagrees with this file, the document is defective |
| [`design/README.md`](design/README.md) | Full index of the design documentation, the trace artifacts, and how the diagrams are generated and checked |
| [`PLAN-001-specification-analysis-and-work-breakdown.md`](PLAN-001-specification-analysis-and-work-breakdown.md) | Specification analysis, the 181-package work breakdown with critical path, and the specification-based test design for all 323 requirements |

Every document above links to the others and to the published site — start
at any one of them and you can reach the rest.

## Why the design is machine-checked

A specification this size (329 requirements, 24 components) drifts from its
own design documents the moment someone edits one without the other. Instead
of relying on review discipline, `design/trace/design-elements.yaml` is the
single authoritative allocation of every requirement to a design element, and
[`design/trace/trace_check.py`](design/trace/trace_check.py) validates it —
run on every push:

```sh
python3 design/trace/trace_check.py --check-diagrams design/diagrams
```

It fails the build on an unallocated requirement, a reference to one that
doesn't exist, an upward layer dependency, a cycle in the component graph, or
a diagram that draws a component or an edge the register doesn't have. The
architecture diagrams are hand-authored for the editorial judgement that
requires — which twelve components share a legible page, what an edge means
in words — but the checker keeps them from silently drifting from the design
they claim to depict. See [`design/README.md`](design/README.md) for the
full rationale.

## Project status

**Design phase. Not yet baselined, no implementation exists.**

- SRS-001 is a draft (v0.1) — every in-scope requirement is allocated, but
  the specification itself hasn't been formally reviewed and frozen
- [ADR-001](ADR-001-architecture-decisions.md) — the decision covering core
  language, C front-end technology, and qualification scope — is analysis
  only; **no decision is recorded yet**, and it blocks the components whose
  shape depends on it
- Everything under `design/` is subject to change until ADR-001 resolves

If you're evaluating this project: read the SRS for what's planned, the SDDs
for how it's meant to be built, and treat the component graph as the current
best answer rather than a final one.

## License

[GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0). See
[LICENSEES](LICENSEES) for a plain-language summary — in short: use, modify,
and distribute freely, but modifications and network-served versions must
stay under the same license.

## Contributing

There is no contribution workflow yet — the design isn't baselined, so
there's no stable target to build against. If you want to get involved,
start by reading [ADR-001](ADR-001-architecture-decisions.md): the language
and qualification-scope decision it's waiting on is the highest-leverage
open question in the project.
