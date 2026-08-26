# Design documentation

Design for the tool specified by [`SRS-001-requirements.md`](../SRS-001-requirements.md),
structured so that every requirement's allocation to a design element is
machine-checked rather than asserted in prose.

## Documents

| Document | Content |
|---|---|
| [`SDD-001-architecture.md`](SDD-001-architecture.md) | Architectural drivers, seven-layer structure, 24 components, principal flows, cross-cutting rules, open decisions |
| [`diagrams/`](diagrams/) | **Authored.** Nine Archify specifications — a layer map and eight per-layer component views — rendered to interactive HTML in [`../docs/diagrams/`](../docs/diagrams/) |
| [`SDD-002-interfaces.md`](SDD-002-interfaces.md) | The seven load-bearing seams (five of them published) and the one internal port: analysis model, test case model, result set, coverage model, report model, engine API, extension points |
| [`SDD-003-data-model.md`](SDD-003-data-model.md) | What is written to disk: the project/output tree split, file granularity, diff stability, schema migration, archival records |
| [`SDD-004-traceability-architecture.md`](SDD-004-traceability-architecture.md) | The trace meta-model, id rules, link types, checker, CI gate, and extension to code and tests |

## Trace artifacts

| File | Form | Edit? |
|---|---|---|
| [`trace/design-elements.yaml`](trace/design-elements.yaml) | **Authoritative** register: 24 components, 239 design elements, requirement allocation | Yes — this is the source |
| [`trace/trace_check.py`](trace/trace_check.py) | Validator and matrix generator | Yes |
| [`trace/requirement-matrix.csv`](trace/requirement-matrix.csv) | Per-requirement view: priority, phase, verification, components, elements | No — generated |
| [`trace/trace-graph.json`](trace/trace-graph.json) | Full graph, both directions | No — generated |
| [`diagrams/*.archify.json`](diagrams/) | Architecture diagram specifications | Yes — authored, and checked against the register |
| [`../docs/diagrams/*.html`](../docs/diagrams/) | Rendered interactive diagrams | No — produced by `archify deliver` |

**The register is authoritative; the SDD documents render it.** Where they
disagree, the SDD is defective. See SDD-004 §3 for why it is arranged that way.

## Checking

```sh
python3 design/trace/trace_check.py
```

```
Requirement allocation
  SRS requirements            323
  out of v1.0 scope (F)       2
  in scope                    321
  allocated                   321
  UNALLOCATED                 0
  design elements             239
  derived (no requirement)    2
  components                  24
```

followed by per-priority, per-phase and per-category tables, then:

```
OK: every in-scope requirement is allocated and the design graph is well formed
```

Fourteen classes of error, all fatal — see SDD-004 §4. In summary: an
unallocated requirement, a reference to a requirement that does not exist, a
requirement line the parser could not read (an unparsed requirement would be an
unchecked one), a parsed count that disagrees with the register's declared
count, a duplicate or malformed id, a field of the wrong shape, an unjustified
derived element, a verification method that does not cover what the element
allocates, a `refines` cycle, an unpermitted upward layer dependency, or a cycle
in the component graph.

Exit `0` clean, `1` findings, `2` could not run. Findings go to stderr, the
summary to stdout. **A run that finds errors writes no artifacts** — the script
does not get to break the fail-safe rule it exists to enforce. Requires PyYAML.

Regenerate the derived artifacts after changing the register:

```sh
python3 design/trace/trace_check.py   --emit-matrix design/trace/requirement-matrix.csv   --emit-json   design/trace/trace-graph.json
```

## Diagrams

The architecture diagrams are **authored, not generated**, which is a departure
from how everything else here is produced. A generator cannot choose which
components belong on a page together, what an edge means in words, or where the
seam between two layers is worth showing; those are editorial judgements, and a
mechanically-emitted picture of a 69-edge graph is one nobody reads.

Authoring them by hand would ordinarily make them a second source of truth that
goes stale silently — exactly the failure this directory exists to prevent. So
the freedom is bounded: the diagrams choose *how* to say things, and the checker
enforces *what* they may say.

```sh
python3 design/trace/trace_check.py --check-diagrams design/diagrams
```

That fails when a diagram draws a component or an edge the register does not
have, when it omits an edge belonging to a component it owns, or when any
component is owned by no diagram or by more than one. A node's `tag` declares
ownership: a bare layer id means the diagram is answerable for that component's
edges, and a tag ending in `context` means the node is shown only as a
dependency target. The eight component views own all 24 components exactly once.

Rebuild the HTML after editing a specification. This needs Node and the
[archify](https://github.com/tt-a1i/archify) skill (`npx skills add tt-a1i/archify -g`):

```sh
node "$ARCHIFY/bin/archify.mjs" deliver architecture   design/diagrams/<name>.archify.json docs/diagrams/<name>.html --quality showcase
```

`layer-map` is the one exception: it is delivered without `--quality showcase`.
Its eighteen aggregated edges over seven layers contain a K5, so no layout can
draw it without crossings and the showcase profile can never pass. It is a
deliberately dense map and is rendered as one.

The rendered artifacts are committed and published with GitHub Pages. They do
not render inline on GitHub the way the previous Mermaid diagrams did — that is
the cost of the trade; the specifications stay readable in a diff, and the
published pages are explorable rather than static.


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
