# SDD-003 — Persistent Data Design

**Document ID:** SDD-003
**Version:** 0.1 (draft for review)
**Status:** Draft — tracks SRS-001 v0.1
**Upstream:** SDD-001, SDD-002, SRS-001 §26 (PRJ)

---

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

Everything on disk belongs to exactly one of two trees, and the distinction is
the mechanism behind TOOL-NFR-080 and TOOL-PRJ-080.

| | **Project tree** | **Output tree** |
|---|---|---|
| Contains | Authored state: scopes, environments, test cases, justifications, configuration | Derived state: generated code, build artifacts, results, coverage, reports |
| Version controlled | Yes — this is the point | No — `.gitignore`d by default |
| Survives deletion | No, it is the source of truth | Yes, fully regenerable from the project tree plus user source |
| Written by | User edits and tool operations alike | Tool only |
| Requirements | TOOL-PRJ-010, TOOL-UIX-320, TOOL-CIC-080 | TOOL-NFR-080, TOOL-PRJ-080 |

The output root is resolved once at startup and every write is confined to it
by the path guard of DSN-CORE-060. User source paths are opened through a
read-only guard, so a write attempt raises rather than succeeding — TOOL-NFR-070
is enforced structurally rather than by care.

This split is also what delivers coexistence (TOOL-MIG-070): another tool's
artifacts are outside the output root, so the tool cannot disturb them.

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
  coverage/
    justifications.yaml            # coverage-by-analysis records   (TOOL-COV-140)
  requirements/
    imported.reqs                  # requirement nodes + digests    (TOOL-TRC-050/060)
  toolchains/                      # project-local compiler configs (TOOL-PLG-020)
  archive/
    2026-08-07T09-14-22Z/          # exported verification records  (TOOL-PRJ-100)

<output-root>/                     # default: build/ectt/, always ignorable
  <environment>/
    generated/                     # harness + stubs                (TOOL-HAR-090)
    build/                         # objects, binaries, per toolchain
    results/                       # result sets, raw coverage data
    reports/                       # rendered reports
  cache/                           # content-addressed analysis models (TOOL-CIC-070)
```

File extensions are indicative; the surface syntax is ADR-002 and is confined
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

---

## 4. Diff stability

TOOL-PRJ-050 requires that a semantically null operation produce a byte-identical
file. Enforced by DSN-PRJ-030 and DSN-CORE-010 together:

| Rule | Applied to |
|---|---|
| Keys emitted in a defined canonical order, never hash or insertion order | Every serialised object |
| Collections sorted by a declared key (test id, unit path, symbol name) | Every list where order is not semantic |
| Default values omitted, never written out explicitly | Every optional field |
| No timestamps, machine names, absolute paths, or user names in project files | Whole project tree |
| Line endings and trailing whitespace normalised on write | Whole project tree |
| Floating-point values round-tripped through a canonical shortest form | Test case values |

The last rule matters more than it looks: a test expecting `0.1` must not
become `0.10000000000000001` on rewrite. Test data is dense with float
literals, and unstable float formatting produces enormous phantom diffs that
train reviewers to skim.

Provenance and timestamps live in the **output tree** and in exported archives,
never in the project tree, which is what allows a project file to be
byte-stable across runs while reports remain fully stamped (TOOL-REP-070).

---

## 5. Schema versioning and migration

Every project file carries `schema_version` as its first key (TOOL-PRJ-020,
DSN-PRJ-010). Readers dispatch on it. There is no inference from file shape.

```
read(file):
  v = file.schema_version                 # absent -> refuse, do not guess
  if v > reader.max          -> refuse, name both versions, name the tool version needed
  if v < reader.min          -> report the migration required; perform nothing
  if v in reader.supported   -> read
```

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

TOOL-PRJ-100 requires exporting a complete, self-contained record of a
verification run. `archive/<timestamp>/` contains:

```
manifest.json        # schema + format versions, digests of every file in the archive
provenance.json      # tool version, build id, compiler, target, configuration digest
configuration/       # the resolved configuration, not a reference to it
tests/               # the test cases as executed
report-model.json    # S5 — sufficient to re-render every format (TOOL-REP-150)
reports/            # the formats rendered at the time
```

Two properties make this an archive rather than a copy:

- **No outward references.** Nothing in it points into the working tree, the
  installation, or a network location. It is readable from a tape (TOOL-INS-040).
- **Self-describing.** It carries its own schema and format versions, so a
  future tool can interpret it against a published definition rather than
  guessing (TOOL-REP-130).

Verification (TOOL-PRJ-110, DSN-PRJ-070) checks an archive against the current
installation and reports whether it can be reproduced, and if not, whether it is
the tool version, the toolchain, or the configuration that differs. Answering
*which* is the useful part; answering only "no" leaves an auditor with nothing
to act on.

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
