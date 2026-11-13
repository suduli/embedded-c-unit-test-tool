# SDD-003 — Persistent Data Design

**Document ID:** SDD-003
**Version:** 0.1 (draft for review)
**Status:** Draft — tracks SRS-001 v0.1
**Upstream:** SDD-001, SDD-002, SRS-001 §26 (PRJ)

**Revision note — 2026-10-17:** Draft corrections for DR-15–18 and DR-13: separate
write boundaries, persistent audit facts and user fragments, explicit version
acceptance, and record/replay archive closure. These contracts require future
implementation and acceptance evidence; they do not claim delivered behavior.

---

<!-- nav:start -->
**Related documents** — [SRS-001](../SRS-001-requirements.md) · [ADR-001](../ADR-001-architecture-decisions.md) · [ADR-006](../ADR-006-fork-or-build-fresh.md) · [SDD-001](SDD-001-architecture.md) · [SDD-002](SDD-002-interfaces.md) · **SDD-003** *(you are here)* · [SDD-004](SDD-004-traceability-architecture.md) · [SDD-005](SDD-005-external-integration.md) · [Register](trace/design-elements.yaml) · [Design index](README.md)

Architecture diagrams: [specifications](diagrams) · published at [the documentation site](https://suduli.github.io/embedded-c-unit-test-tool/), which spells out every component id in full and shows how these documents connect.
<!-- nav:end -->


## 1. Purpose

What the tool writes to disk, where, in what form, and what guarantees each
artifact carries. SRS-001 §26 opens with the reason this deserves its own
document: *test projects for safety-related software have lifetimes measured in
decades*, and a project created today may have to be opened, re-executed, and
defended long after the tool version that created it is gone.

Three requirements set the frame and are worth restating as design constraints
rather than as items on a list:

- **TOOL-PRJ-060** — concurrent edits must produce localised, resolvable version
  control conflicts. This constrains *file granularity*, not file format, and it
  is the constraint most often discovered too late.
- **TOOL-PRJ-050** — an operation that does not change meaning must not change
  file content. This constrains *serialisation order*, and it is what makes a
  diff reviewable.
- **TOOL-PRJ-030** — the tool must open older projects or say precisely why it
  cannot. This constrains *schema versioning*, and it must be present from the
  first commit; retrofitting a version field onto files already in the field is
  not possible.

---

## 2. The two trees

Tool-managed state belongs to the two trees below. UUT sources and third-party
artifacts remain outside these write authorities. The distinction implements
TOOL-NFR-080 and TOOL-PRJ-080.

| | **Project tree** | **Output tree** |
|---|---|---|
| Contains | Authored state: scopes, environments, test cases, justifications, configuration, canonical user-code fragments and audit facts | Derived state: generated code, build artifacts, results, coverage, reports |
| Version controlled | Yes — this is the point | No — `.gitignore`d by default |
| Deletion consequence | Loses authored source of truth unless backed up | Generated code can be rebuilt after fragment import; run observations require an archive |
| Written by | User edits and authorized project operations | Tool generation; designated editable regions permit user edits pending import |
| Requirements | TOOL-PRJ-010, TOOL-UIX-320, TOOL-CIC-080 | TOOL-NFR-080, TOOL-PRJ-080 |

There are two explicit write authorities: project operations may update the
project root; generation/build/run/report operations may update the output root.
The roots are resolved and validated at project open. An output root nested in
the project (the default) is a separately classified excluded subtree, never
an authored-state destination. Writes require an operation-specific authority,
not a global output-only rule (DSN-CORE-060). The UUT/source tree is read-only;
project/output destinations overlapping source files or third-party artifacts
are rejected. Coexistence (TOOL-MIG-070) protects existing artifacts in both roots.

Both guards reject path traversal and resolve symlinks/junctions/reparse points
against the intended root before opening and again at replacement; an escape or
changed target fails the operation. Creation validates the nearest existing
ancestor. Project updates stage and validate content, check the original
revision/digest for concurrent edits, then atomically replace files. Multi-file
updates use a journal/commit marker with recovery so readers see one committed
revision; cancellation rolls back uncommitted state. Conflicts preserve both
versions and require resolution. UUT sources are never written through either
authority (TOOL-NFR-070).

Output is not a backup: old execution observations, diagnostics and coverage may
be irreproducible. Archive them before cleanup when needed as evidence. User
fragments must be imported successfully before generated editable files can be
regenerated or removed (§3.1).

### 2.1 Layout

```
<project>/
  ectt.project                     # project root marker, schema version, settings
  scopes/
    driver_integration.scope       # one file per test scope        (TOOL-ING-190)
    adc.scope
  environments/
    adc.host.env                   # one file per environment
    adc.target.env
  tests/
    src/adc/
      adc_read.tests               # test cases grouped per unit    (TOOL-PRJ-060)
      adc_calibrate.tests
    src/adc/adc_custom.c           # C-authored tests, user-owned
  fragments/                       # canonical authored harness/stub regions
    adc_read.stub.c                 # stable region ID + signature/source binding
  audit/
    ai-artifacts.yaml              # origin, model/prompt references, review history
  coverage/
    justifications.yaml            # coverage-by-analysis records   (TOOL-COV-140)
  requirements/
    imported.reqs                  # requirement nodes + digests    (TOOL-TRC-050/060)
  toolchains/                      # project-local compiler configs (TOOL-PLG-020)
  link-plans/                      # authored per-scope link plans (TOOL-ING-200)
  archive/
    2026-08-07T09-14-22Z/          # exported verification records  (TOOL-PRJ-100)

<output-root>/                     # default: build/ectt/, excluded from VCS
  <environment>/
    generated/                     # harness + stubs                (TOOL-HAR-090)
    build/                         # objects, binaries, per toolchain
    results/                       # result sets, raw coverage data
    reports/                       # rendered reports
  cache/                           # content-addressed analysis models (TOOL-CIC-070)
```

File extensions are indicative; the surface syntax follows ADR-002 and is confined
to one serialisation adapter (DSN-PRJ-010, DSN-TCM-020).

---

## 3. Granularity: why one file per thing

TOOL-PRJ-060 asks that concurrent edits by different users produce localised
conflicts. That is a decision about *what a file contains*, and it is the
reason for the layout above.

| Unit of work | File | Conflict behaviour |
|---|---|---|
| Two engineers edit tests for different units | Different `.tests` files | No conflict |
| Two engineers edit different test cases in one unit | Same file, different blocks | Line-level conflict, resolvable |
| Two engineers edit the same test case | Same block | Real conflict — correctly surfaced |
| One adds a scope while another adds an environment | Different files | No conflict |

The failure mode being designed away is the single `project.xml` that every
operation touches, where any two concurrent changes conflict at the whole-file
level and the merge is unreviewable. That is a common shape for commercial
tools in this space and a frequent complaint about them.

Within a `.tests` file, cases are emitted in stable id order, and each occupies
a contiguous block. Adding a case inserts a block; it never reflows the file.

### 3.1 Canonical editable code and regeneration

`fragments/` stores user-authored stub bodies and harness regions with stable
region ID, owning symbol, signature/source digest and exact code text. Generated
files embed region IDs plus the digest of the last emitted fragment, allowing
three-way comparison of canonical project text, last-emitted text, and current
output text. Direct edits in designated generated regions are supported, but
must first be imported transactionally into this canonical store (HAR-100,
STB-110/120). A clean output directory is regenerable only after that import.

Before regeneration, export, or tool-managed cleanup, scan all editable regions.
A single changed side is imported/emitted; concurrent distinct edits, missing
markers, deleted regions or incompatible signature changes stop the operation,
retain original files and both versions, and report the exact region conflict.
Changes outside editable regions also stop replacement until explicitly resolved
or preserved; they are never silently thrown away. No delete/regenerate action
may proceed while import/conflict handling is pending. The UI/CLI must expose
this status before offering cleanup. Manual external deletion before import can
lose pending edits and is not a supported recovery workflow.

Acceptance requires nontrivial harness and stub changes, import, output deletion,
and byte-equivalent fragment recovery on regeneration; plus simultaneous edits,
signature changes and damaged marker fixtures that prove conflict preservation.
This is a design acceptance obligation, not a claim of current recovery support.

---

## 4. Diff stability

TOOL-PRJ-050 requires that a semantically null operation produce a byte-identical
file. Enforced by DSN-PRJ-030 and DSN-CORE-010 together:

| Rule | Applied to |
|---|---|
| Keys emitted in a defined canonical order, never hash or insertion order | Every serialised object |
| Collections sorted by a declared key (test id, unit path, symbol name) | Every list where order is not semantic |
| Default values omitted, never written out explicitly | Every optional field |
| No incidental save timestamps, host names, or serializer user names; required authored audit fields are retained | Authored project records |
| Line endings and trailing whitespace normalised on write | Whole project tree |
| Floating-point values round-tripped through a canonical shortest form | Test case values |

The last rule matters more than it looks: a test expecting `0.1` must not
become `0.10000000000000001` on rewrite. Test data is dense with float
literals, and unstable float formatting produces enormous phantom diffs that
train reviewers to skim.

Meaningful audit facts are canonical authored state: justification author/date/
rationale/source digest (COV-150), AI model identity/generation timestamp/input
references and review history (AIF-080/090/180/190), and identified review acts
are retained in project records. They change only when that authored event
occurs, never on an unrelated save. Execution timestamps and host observations
live in results/output and archives (REP-070). Canonical determinism compares
identical logical records including their audit facts; a new execution or
review is a new input, not a serialization-only rewrite. Archival snapshots and
migration backups retain their recorded provenance unchanged.

---

## 5. Schema versioning and migration

Every structured project record carries `schema_version` as its first key
(TOOL-PRJ-020, DSN-PRJ-010). Raw C-authored tests and code fragments have a
schema-versioned sidecar containing their region identity, ownership and digests;
C source text is not prefixed with a serialization field. The project manifest
inventories those payloads and sidecars. Readers dispatch on the record version;
there is no inference from file shape.

```
read(file):
  v = file.schema_version                 # absent -> refuse, do not guess
  if v > reader.max          -> refuse, name both versions, name the tool version needed
  if v < reader.min          -> report the migration required; perform nothing
  if v not in reader.supported -> refuse, report supported versions
  otherwise -> validate and read; preserve supported optional extension fields
```

This is the authored-state policy of SDD-002 §3, including newer minor versions:
there is no automatic forward acceptance. Version comparison is numeric
major/minor, not lexical. Unknown semantic enum values are rejected. Accepted
optional extension fields round-trip unchanged; if the writer cannot preserve
them, it refuses to save. No ignored field may be silently dropped. Read-only
report consumers follow their separate seam policy, not this writable rule.
Fixtures cover too-new minor/major versions, unsupported intermediate versions,
unknown review states and preservation/refused saves.

Migration (DSN-PRJ-020, TOOL-PRJ-040) is:

- **explicit** — reported before anything is written, never a side effect of
  opening a project;
- **confirmed** — no migration runs without the user saying so, including from
  the GUI and including on upgrade (TOOL-INS-060);
- **reversible where possible** — each migration is a pure
  old-model → new-model function with a recorded inverse where one exists; where
  none exists it declares itself irreversible *before* running;
- **backed up** — the pre-migration tree is copied under `archive/` regardless.

Because installations are side-by-side (TOOL-INS-050, DSN-PKG-040), the answer
to "we cannot open this project" is always available: install the version that
made it. That is why side-by-side installation is a data-longevity requirement
rather than a packaging convenience.

---

## 6. Identity and references

| Identifier | Assigned | Stable across | Requirement |
|---|---|---|---|
| Test case id | At creation, random suffix | Edits, renames, regeneration, moves | TOOL-TCD-140 |
| Scope id | By user at creation | Membership changes | TOOL-ING-130 |
| Environment id | Derived from scope + toolchain + target | Rebuild | — |
| Requirement id | By the requirements source | Import re-runs | TOOL-TRC-010 |
| Design element id | By `design-elements.yaml` | Refactoring | SDD-004 |

Test case identity is assigned rather than derived from content. A
content-derived id would change on every edit, silently breaking coverage
attribution, requirement links, and run comparison — the three things that must
survive editing (SDD-002 §5.1).

All references to user source, requirements files, and configuration are stored
**relative to the project root** (TOOL-PRJ-070, DSN-PRJ-040); absolute paths are
rejected on write. A validation pass resolves every reference and reports the
referencing file, the missing target, and whether it was required
(TOOL-PRJ-090, DSN-PRJ-050) rather than failing at first use in a later stage.

---

## 7. Digest-bound records

Four record types carry a digest of something outside themselves. In each case
the digest exists so a change *invalidates* the record instead of silently
outdating it — the pattern that keeps stale evidence from being presented as
current.

| Record | Bound to | On mismatch | Requirement |
|---|---|---|---|
| Coverage justification | Digest of the justified source region | State becomes `expired`; reports show it as uncovered | TOOL-COV-150 |
| Generated artifact | Digest of the analysis model it came from | Artifact marked stale | TOOL-HAR-110 |
| Test case | Digest of the interface it exercises | Test marked stale | TOOL-CBT-070 |
| Requirement link | Digest of requirement text at last review | Link marked needing re-review | TOOL-TRC-090 |

An expired justification reports as uncovered, not as an error — the coverage
figure corrects itself and the report says why. Anything softer would let a
justification written for one version of a function keep excusing a different
one.

---

## 8. Archived verification records

TOOL-PRJ-100 requires a complete self-contained verification record. The manifest
states `archive_kind: record` or `replay`, with completeness status and any
missing dependency. A `record` preserves evidence and report re-rendering; it
must not claim executable replay. A `replay` adds the complete offline execution
closure below. These are distinct capabilities, not an inference from a compiler
name/version. If closure cannot be included, export remains explicitly a record
and reports why replay is unavailable.

```
manifest.json        # archive kind, schema/format versions, file sizes + SHA-256 digests
provenance.json      # tool/build/adapter identity, observed times, seeds, environment
configuration/       # resolved configuration, ordered commands/flags and working paths
tests/               # exact executed test cases and canonical user-code fragments
results/             # normalized S3 + raw runner observations and diagnostics
coverage/            # S4 + raw backend evidence, attribution and MC/DC proof locators
report-model.json    # S5 and referenced traceability/justification/provenance data
reports/             # original rendered outputs
schemas/             # published model/format definitions used by this archive
rendering/           # exact offline renderer/release + dependencies, templates/fonts
# Additional mandatory closure for archive_kind: replay:
sources/             # UUT sources, transitive headers, generated inputs and fragments
build-inputs/        # compilation database, scripts, linker files, libraries, resources
tools/               # exact release, extensions, toolchain/sysroot/runtime artifacts
replay.json          # logical path map, commands, environment, closure inventory/limits
```

Every embedded reference resolves inside the archive; original workspace paths
and endpoint identities may be recorded as inert provenance strings, never as
runtime dependencies. External symlinks are materialized safely or rejected.
Export freezes one coherent input/run snapshot and verifies all sizes/digests.
User fragment import/conflicts (§3.1) must be resolved before claiming closure.
No required renderer, template, schema, source include, link library, script,
binary or toolchain artifact is satisfied by a network URL or version label.
Copies of the exact offline release and toolchain artifacts are embedded with
checksums; a local install may be used only after matching those identities.
Distribution restrictions or unavailable artifacts make the archive `record`
with a precise missing-closure diagnostic rather than a false replay guarantee.

AI-backed re-render/replay uses captured provider responses, model identity,
parameters and input/response digests; it does not contact a live provider.
A fresh generation is a new operation requiring authorization and cannot be
claimed byte-identical to the recorded response. Ordered execution seeds and
replay-relevant environment variables are inputs. Credentials are never archived;
if an execution needs a secret-dependent input that cannot be included, record
that replay limitation without the secret.

Record verification checks evidence integrity, internal reference closure and
offline report re-rendering. Replay verification additionally checks every
build dependency, the release/toolchain identities and target prerequisites,
then rebuilds/runs using only archived inputs. Report separately whether the
record is intact, reports are reproducible, the build is reproducible and the
execution is reproducible; identify the exact differing/missing dependency
(TOOL-PRJ-110, DSN-PRJ-070). Target hardware, device state or simulator licenses
may limit execution replay even with a closed build snapshot; state those
prerequisites explicitly instead of promising hardware can be archived.

Acceptance hides the original workspace and network, uses a fresh extraction,
verifies report re-rendering for a record and build/execution for an eligible
replay archive, then alters/removes one dependency to prove a precise failure.
Archived compiler/release availability is checked, not assumed. These tests are
required future evidence; this draft does not assert current implementation.

---

## 9. Content-addressed cache

The output tree's `cache/` holds analysis models keyed by the digest of their
inputs — compilation database entry, source digests, flags, front-end version.

This serves three requirements at once with one mechanism: skipping re-ingestion
and re-analysis when nothing changed (TOOL-ING-090, TOOL-ING-100), restoring
across CI runs when keyed on the compilation database digest (TOOL-CIC-070), and
meeting the unchanged-suite re-execution budget of TOOL-NFR-040 alongside the
incremental build graph of DSN-BLD-020.

The cache is **always discardable**. A missing entry costs time, never
correctness, so a corrupted or partial cache can be deleted without thought —
which is the only cache policy that survives contact with users.

---

## 10. Data-related risks

| Risk | Where it bites | Mitigation |
|---|---|---|
| ADR-002 picks YAML and implicit typing corrupts C values — `NO` becoming boolean false, `1.10` becoming a float, a version string becoming a number | Test case data is *exactly* the content where this is dangerous | Quote all scalars on write; parse with implicit typing disabled; ADR-002 must decide with this specific hazard in view |
| Test case ids collide after a merge | Two branches create cases with the same id | Sufficient random suffix, plus a duplicate-id check in project validation |
| A project accumulates unresolvable schema history | Long-lived projects skipping many versions | Migrations chain rather than jump; side-by-side installation is the always-available fallback |
| The output tree gets committed | Users unfamiliar with the layout | Ship a `.gitignore` fragment; keep the default output root under `build/` |
| Archive grows without bound | Every run archived | Archiving is explicit, not automatic; retention is the user's policy to set |
