# Design documentation

Design for the tool specified by [`SRS-001-requirements.md`](../SRS-001-requirements.md),
structured so that every requirement's allocation to a design element is
machine-checked rather than asserted in prose.

## Documents

| Document | Content |
|---|---|
| [`SDD-001-architecture.md`](SDD-001-architecture.md) | Architectural drivers, seven-layer structure, 24 components, principal flows, cross-cutting rules, open decisions |
| [`SDD-002-interfaces.md`](SDD-002-interfaces.md) | The seven published seams and the one internal port: analysis model, test case model, result set, coverage model, report model, engine API, extension points |
| [`SDD-003-data-model.md`](SDD-003-data-model.md) | What is written to disk: the project/output tree split, file granularity, diff stability, schema migration, archival records |
| [`SDD-004-traceability-architecture.md`](SDD-004-traceability-architecture.md) | The trace meta-model, id rules, link types, checker, CI gate, and extension to code and tests |

## Trace artifacts

| File | Form | Edit? |
|---|---|---|
| [`trace/design-elements.yaml`](trace/design-elements.yaml) | **Authoritative** register: 24 components, 237 design elements, requirement allocation | Yes — this is the source |
| [`trace/trace_check.py`](trace/trace_check.py) | Validator and matrix generator | Yes |
| [`trace/requirement-matrix.csv`](trace/requirement-matrix.csv) | Per-requirement view: priority, phase, verification, components, elements | No — generated |
| [`trace/trace-graph.json`](trace/trace-graph.json) | Full graph, both directions | No — generated |

**The register is authoritative; the SDD documents render it.** Where they
disagree, the SDD is defective. See SDD-004 §3 for why it is arranged that way.

## Checking

```sh
python3 design/trace/trace_check.py
```

```
SRS requirements            323
out of v1.0 scope (F)         2
in scope                    321
allocated                   321
design elements             237
components                   24

OK: every in-scope requirement is allocated and the design graph is well formed
```

Fails on an unallocated requirement, a reference to a requirement that does not
exist, a duplicate or malformed id, an unjustified derived element, an upward
layer dependency, or a cycle in the component graph. Exit `0` clean, `1`
findings, `2` could not run. Requires PyYAML.

Regenerate the derived artifacts after changing the register:

```sh
python3 design/trace/trace_check.py \
  --emit-matrix design/trace/requirement-matrix.csv \
  --emit-json   design/trace/trace-graph.json
```

## Status

Draft, tracking SRS-001 v0.1, which is not baselined.

This design deliberately does **not** decide the implementation language, GUI
toolkit, project file syntax, symbolic execution engine, coverage backend
strategy, license, or packaging mechanism. Those are ADR-001 through ADR-007 and
none is recorded. Elements whose shape depends on an open decision carry an
`open:` field naming it; SDD-001 §8 tabulates how each outcome is absorbed.

One open decision is a genuine blocker rather than a deferral: **ADR-006**
(fork UTBotCpp or build fresh) would reset the language decision, `CMP-ANA`,
`CMP-ATG`, and the `CMP-GEN` framework back-end simultaneously. It should be
resolved before this design is baselined.
