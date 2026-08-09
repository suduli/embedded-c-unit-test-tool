# Architecture diagrams

**Generated — do not edit.** Produced by [`trace/trace_check.py`](trace/trace_check.py) from [`trace/design-elements.yaml`](trace/design-elements.yaml), which is the authoritative register. Everything below is derived from the same component graph the checker validates, so it cannot drift from the design it depicts.

```sh
python3 design/trace/trace_check.py \
  --emit-mermaid design/architecture-diagrams.md
```

24 components across 7 layers, 69 dependency edges.

---

## 1. Layer map

Aggregated from the component graph: an edge means at least one component in the source layer depends on a component in the target layer, and its label is how many such dependencies there are. Dependencies within a single layer are not shown here — §3 has them.

```mermaid
flowchart TD
  L6["L6 · Assurance and Ecosystem<br/>6 components"]
  L5["L5 · Interfaces<br/>3 components"]
  L4["L4 · Evidence<br/>4 components"]
  L3["L3 · Realization<br/>3 components"]
  L2["L2 · Synthesis<br/>3 components"]
  L1["L1 · Comprehension<br/>3 components"]
  L0["L0 · Platform and Persistence<br/>2 components"]
  L1 -->|4| L0
  L1 -->|1| L6
  L2 -->|4| L0
  L2 -->|3| L1
  L2 -->|1| L6
  L3 -->|3| L0
  L3 -->|1| L1
  L3 -->|3| L2
  L3 -->|3| L6
  L4 -->|6| L0
  L4 -->|4| L1
  L4 -->|1| L2
  L4 -->|4| L3
  L4 -->|1| L6
  L5 -->|1| L0
  L6 -->|6| L0
  L6 -->|5| L2
  L6 -->|2| L4
```

| Layer | Name | Components |
|---|---|---|
| `L0` | Platform and Persistence | `CMP-CORE` `CMP-PRJ` |
| `L1` | Comprehension | `CMP-ANA` `CMP-ING` `CMP-TCH` |
| `L2` | Synthesis | `CMP-ATG` `CMP-GEN` `CMP-TCM` |
| `L3` | Realization | `CMP-BLD` `CMP-EXH` `CMP-EXT` |
| `L4` | Evidence | `CMP-CBT` `CMP-COV` `CMP-REP` `CMP-TRC` |
| `L5` | Interfaces | `CMP-API` `CMP-CLI` `CMP-GUI` |
| `L6` | Assurance and Ecosystem | `CMP-AIF` `CMP-MIG` `CMP-PKG` `CMP-PLG` `CMP-QUA` `CMP-SEC` |

---

## 2. Component dependency graph

Every component in the model, grouped by layer. An arrow is a `depends_on` edge. Arrows run downward because a dependency on a higher layer is a checker error unless the target is marked `cross_cutting: true` — those are the thick dashed nodes, and the upward arrows into them are the only ones in the diagram.

This is the whole system on one page and it is dense; it is meant as the reference view, so click to zoom. §3 is where the detail is legible without zooming.

```mermaid
flowchart TD
  subgraph L6["L6 · Assurance and Ecosystem"]
    direction LR
    CMP_AIF["CMP-AIF<br/>AI Assist<br/>Subsystem"]
    CMP_MIG["CMP-MIG<br/>Migration and<br/>Interoperability"]
    CMP_PKG["CMP-PKG<br/>Packaging,<br/>Installation and<br/>Release<br/>Engineering"]
    CMP_PLG["CMP-PLG<br/>Extension<br/>Framework"]
    CMP_QUA["CMP-QUA<br/>Qualification<br/>Evidence"]
    CMP_SEC["CMP-SEC<br/>Security and<br/>Integrity Services"]
  end
  subgraph L5["L5 · Interfaces"]
    direction LR
    CMP_API["CMP-API<br/>Engine Service<br/>Interface"]
    CMP_CLI["CMP-CLI<br/>Command Line<br/>Front-End"]
    CMP_GUI["CMP-GUI<br/>Standalone Desktop<br/>Application"]
  end
  subgraph L4["L4 · Evidence"]
    direction LR
    CMP_CBT["CMP-CBT<br/>Change Impact and<br/>Regression"]
    CMP_COV["CMP-COV<br/>Coverage Engine"]
    CMP_REP["CMP-REP<br/>Reporting Pipeline"]
    CMP_TRC["CMP-TRC<br/>Traceability<br/>Engine"]
  end
  subgraph L3["L3 · Realization"]
    direction LR
    CMP_BLD["CMP-BLD<br/>Build Orchestrator"]
    CMP_EXH["CMP-EXH<br/>Host Execution<br/>Runner"]
    CMP_EXT["CMP-EXT<br/>Target Execution<br/>Runner"]
  end
  subgraph L2["L2 · Synthesis"]
    direction LR
    CMP_ATG["CMP-ATG<br/>Automatic Test<br/>Generation"]
    CMP_GEN["CMP-GEN<br/>Generation Engine"]
    CMP_TCM["CMP-TCM<br/>Test Case Model<br/>and Store"]
  end
  subgraph L1["L1 · Comprehension"]
    direction LR
    CMP_ANA["CMP-ANA<br/>Source Analyzer"]
    CMP_ING["CMP-ING<br/>Ingestion and<br/>Scope Resolver"]
    CMP_TCH["CMP-TCH<br/>Toolchain<br/>Abstraction"]
  end
  subgraph L0["L0 · Platform and Persistence"]
    direction LR
    CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
    CMP_PRJ["CMP-PRJ<br/>Project and<br/>Workspace Store"]
  end
  CMP_AIF --> CMP_ATG
  CMP_AIF --> CMP_GEN
  CMP_AIF --> CMP_SEC
  CMP_AIF --> CMP_TCM
  CMP_ANA --> CMP_ING
  CMP_ANA --> CMP_TCH
  CMP_ATG --> CMP_ANA
  CMP_ATG --> CMP_TCM
  CMP_BLD --> CMP_GEN
  CMP_BLD --> CMP_TCH
  CMP_CBT --> CMP_ANA
  CMP_CBT --> CMP_COV
  CMP_CBT --> CMP_PRJ
  CMP_CLI --> CMP_API
  CMP_COV --> CMP_ANA
  CMP_COV --> CMP_EXH
  CMP_COV --> CMP_EXT
  CMP_COV --> CMP_TCH
  CMP_EXH --> CMP_BLD
  CMP_EXH --> CMP_SEC
  CMP_EXH --> CMP_TCM
  CMP_EXT --> CMP_BLD
  CMP_EXT --> CMP_PLG
  CMP_EXT --> CMP_SEC
  CMP_EXT --> CMP_TCM
  CMP_GEN --> CMP_ANA
  CMP_GEN --> CMP_PLG
  CMP_GEN --> CMP_TCM
  CMP_GUI --> CMP_API
  CMP_ING --> CMP_PRJ
  CMP_MIG --> CMP_GEN
  CMP_MIG --> CMP_REP
  CMP_MIG --> CMP_TCM
  CMP_PKG --> CMP_SEC
  CMP_QUA --> CMP_PKG
  CMP_QUA --> CMP_REP
  CMP_REP --> CMP_CBT
  CMP_REP --> CMP_COV
  CMP_REP --> CMP_EXH
  CMP_REP --> CMP_EXT
  CMP_REP --> CMP_PLG
  CMP_REP --> CMP_TRC
  CMP_TCH --> CMP_PLG
  CMP_TCM --> CMP_ANA
  CMP_TCM --> CMP_PRJ
  CMP_TRC --> CMP_ANA
  CMP_TRC --> CMP_PRJ
  CMP_TRC --> CMP_TCM
  classDef xcut stroke-width:3px,stroke-dasharray:5 3
  classDef ubiq stroke-width:3px
  class CMP_PLG,CMP_SEC xcut
  class CMP_CORE ubiq
```

**`CMP-CORE` edges omitted above.** 21 of the 23 other components depend on it; drawing those arrows hides the structure. The exceptions — the components that do **not** depend on `CMP-CORE` — are `CMP-CLI`, `CMP-GUI`. §3 draws every edge, including these.

---

## 3. Per-layer views

One diagram per layer, drawn complete — no edges are omitted here. Solid nodes belong to the layer; the paler nodes are dependency targets that live elsewhere, shown so the seam is visible.

### L0 · Platform and Persistence

```mermaid
flowchart LR
  subgraph L0["L0"]
    CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
    CMP_PRJ["CMP-PRJ<br/>Project and<br/>Workspace Store"]
  end
  CMP_PRJ --> CMP_CORE
  classDef ext stroke-dasharray:2 2,opacity:0.65
```

### L1 · Comprehension

```mermaid
flowchart LR
  subgraph L1["L1"]
    CMP_ANA["CMP-ANA<br/>Source Analyzer"]
    CMP_ING["CMP-ING<br/>Ingestion and<br/>Scope Resolver"]
    CMP_TCH["CMP-TCH<br/>Toolchain<br/>Abstraction"]
  end
  CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
  CMP_PLG["CMP-PLG<br/>Extension<br/>Framework"]
  CMP_PRJ["CMP-PRJ<br/>Project and<br/>Workspace Store"]
  CMP_ANA --> CMP_CORE
  CMP_ANA --> CMP_ING
  CMP_ANA --> CMP_TCH
  CMP_ING --> CMP_CORE
  CMP_ING --> CMP_PRJ
  CMP_TCH --> CMP_CORE
  CMP_TCH --> CMP_PLG
  classDef ext stroke-dasharray:2 2,opacity:0.65
  class CMP_CORE,CMP_PLG,CMP_PRJ ext
```

### L2 · Synthesis

```mermaid
flowchart LR
  subgraph L2["L2"]
    CMP_ATG["CMP-ATG<br/>Automatic Test<br/>Generation"]
    CMP_GEN["CMP-GEN<br/>Generation Engine"]
    CMP_TCM["CMP-TCM<br/>Test Case Model<br/>and Store"]
  end
  CMP_ANA["CMP-ANA<br/>Source Analyzer"]
  CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
  CMP_PLG["CMP-PLG<br/>Extension<br/>Framework"]
  CMP_PRJ["CMP-PRJ<br/>Project and<br/>Workspace Store"]
  CMP_ATG --> CMP_ANA
  CMP_ATG --> CMP_CORE
  CMP_ATG --> CMP_TCM
  CMP_GEN --> CMP_ANA
  CMP_GEN --> CMP_CORE
  CMP_GEN --> CMP_PLG
  CMP_GEN --> CMP_TCM
  CMP_TCM --> CMP_ANA
  CMP_TCM --> CMP_CORE
  CMP_TCM --> CMP_PRJ
  classDef ext stroke-dasharray:2 2,opacity:0.65
  class CMP_ANA,CMP_CORE,CMP_PLG,CMP_PRJ ext
```

### L3 · Realization

```mermaid
flowchart LR
  subgraph L3["L3"]
    CMP_BLD["CMP-BLD<br/>Build Orchestrator"]
    CMP_EXH["CMP-EXH<br/>Host Execution<br/>Runner"]
    CMP_EXT["CMP-EXT<br/>Target Execution<br/>Runner"]
  end
  CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
  CMP_GEN["CMP-GEN<br/>Generation Engine"]
  CMP_PLG["CMP-PLG<br/>Extension<br/>Framework"]
  CMP_SEC["CMP-SEC<br/>Security and<br/>Integrity Services"]
  CMP_TCH["CMP-TCH<br/>Toolchain<br/>Abstraction"]
  CMP_TCM["CMP-TCM<br/>Test Case Model<br/>and Store"]
  CMP_BLD --> CMP_CORE
  CMP_BLD --> CMP_GEN
  CMP_BLD --> CMP_TCH
  CMP_EXH --> CMP_BLD
  CMP_EXH --> CMP_CORE
  CMP_EXH --> CMP_SEC
  CMP_EXH --> CMP_TCM
  CMP_EXT --> CMP_BLD
  CMP_EXT --> CMP_CORE
  CMP_EXT --> CMP_PLG
  CMP_EXT --> CMP_SEC
  CMP_EXT --> CMP_TCM
  classDef ext stroke-dasharray:2 2,opacity:0.65
  class CMP_CORE,CMP_GEN,CMP_PLG,CMP_SEC,CMP_TCH,CMP_TCM ext
```

### L4 · Evidence

```mermaid
flowchart LR
  subgraph L4["L4"]
    CMP_CBT["CMP-CBT<br/>Change Impact and<br/>Regression"]
    CMP_COV["CMP-COV<br/>Coverage Engine"]
    CMP_REP["CMP-REP<br/>Reporting Pipeline"]
    CMP_TRC["CMP-TRC<br/>Traceability<br/>Engine"]
  end
  CMP_ANA["CMP-ANA<br/>Source Analyzer"]
  CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
  CMP_EXH["CMP-EXH<br/>Host Execution<br/>Runner"]
  CMP_EXT["CMP-EXT<br/>Target Execution<br/>Runner"]
  CMP_PLG["CMP-PLG<br/>Extension<br/>Framework"]
  CMP_PRJ["CMP-PRJ<br/>Project and<br/>Workspace Store"]
  CMP_TCH["CMP-TCH<br/>Toolchain<br/>Abstraction"]
  CMP_TCM["CMP-TCM<br/>Test Case Model<br/>and Store"]
  CMP_CBT --> CMP_ANA
  CMP_CBT --> CMP_CORE
  CMP_CBT --> CMP_COV
  CMP_CBT --> CMP_PRJ
  CMP_COV --> CMP_ANA
  CMP_COV --> CMP_CORE
  CMP_COV --> CMP_EXH
  CMP_COV --> CMP_EXT
  CMP_COV --> CMP_TCH
  CMP_REP --> CMP_CBT
  CMP_REP --> CMP_CORE
  CMP_REP --> CMP_COV
  CMP_REP --> CMP_EXH
  CMP_REP --> CMP_EXT
  CMP_REP --> CMP_PLG
  CMP_REP --> CMP_TRC
  CMP_TRC --> CMP_ANA
  CMP_TRC --> CMP_CORE
  CMP_TRC --> CMP_PRJ
  CMP_TRC --> CMP_TCM
  classDef ext stroke-dasharray:2 2,opacity:0.65
  class CMP_ANA,CMP_CORE,CMP_EXH,CMP_EXT,CMP_PLG,CMP_PRJ,CMP_TCH,CMP_TCM ext
```

### L5 · Interfaces

```mermaid
flowchart LR
  subgraph L5["L5"]
    CMP_API["CMP-API<br/>Engine Service<br/>Interface"]
    CMP_CLI["CMP-CLI<br/>Command Line<br/>Front-End"]
    CMP_GUI["CMP-GUI<br/>Standalone Desktop<br/>Application"]
  end
  CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
  CMP_API --> CMP_CORE
  CMP_CLI --> CMP_API
  CMP_GUI --> CMP_API
  classDef ext stroke-dasharray:2 2,opacity:0.65
  class CMP_CORE ext
```

### L6 · Assurance and Ecosystem

```mermaid
flowchart LR
  subgraph L6["L6"]
    CMP_AIF["CMP-AIF<br/>AI Assist<br/>Subsystem"]
    CMP_MIG["CMP-MIG<br/>Migration and<br/>Interoperability"]
    CMP_PKG["CMP-PKG<br/>Packaging,<br/>Installation and<br/>Release<br/>Engineering"]
    CMP_PLG["CMP-PLG<br/>Extension<br/>Framework"]
    CMP_QUA["CMP-QUA<br/>Qualification<br/>Evidence"]
    CMP_SEC["CMP-SEC<br/>Security and<br/>Integrity Services"]
  end
  CMP_ATG["CMP-ATG<br/>Automatic Test<br/>Generation"]
  CMP_CORE["CMP-CORE<br/>Core Platform<br/>Services"]
  CMP_GEN["CMP-GEN<br/>Generation Engine"]
  CMP_REP["CMP-REP<br/>Reporting Pipeline"]
  CMP_TCM["CMP-TCM<br/>Test Case Model<br/>and Store"]
  CMP_AIF --> CMP_ATG
  CMP_AIF --> CMP_CORE
  CMP_AIF --> CMP_GEN
  CMP_AIF --> CMP_SEC
  CMP_AIF --> CMP_TCM
  CMP_MIG --> CMP_CORE
  CMP_MIG --> CMP_GEN
  CMP_MIG --> CMP_REP
  CMP_MIG --> CMP_TCM
  CMP_PKG --> CMP_CORE
  CMP_PKG --> CMP_SEC
  CMP_PLG --> CMP_CORE
  CMP_QUA --> CMP_CORE
  CMP_QUA --> CMP_PKG
  CMP_QUA --> CMP_REP
  CMP_SEC --> CMP_CORE
  classDef ext stroke-dasharray:2 2,opacity:0.65
  class CMP_ATG,CMP_CORE,CMP_GEN,CMP_REP,CMP_TCM ext
```
