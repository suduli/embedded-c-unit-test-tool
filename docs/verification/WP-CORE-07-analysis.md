# Verification Analysis Note — WP-CORE-07 (User Documentation and Text Externalisation)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-CORE-07. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-NFR-120 (M, P2, I) — *The tool shall provide user documentation covering
installation, every supported workflow, and every configuration option* — and
TOOL-NFR-190 (S, P2, I) — *User-facing text shall be externalized from code to permit
translation, without translation being delivered in v1.0.*

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-NFR-190): every user-facing string is carried by a
  central, frozen message catalog (`ectt.core.text`): messages are looked up by
  stable key, formatted with named placeholders, an unknown key or a missing
  placeholder is a named error, and the catalog is deterministic and serialisable.
  Translation is delivered by supplying another catalog, not by editing code — no
  translation is shipped in v1.0 (the default catalog is English-only, marked as
  such).
- AC-2 (falsifiable, from TOOL-NFR-120): a machine-readable user-documentation index
  enumerates the documentation the tool must ship: one entry for installation, one
  entry per supported workflow, and one entry per configuration option surface.
  Every entry carries a stable id, a title, a doc anchor, and a completeness status;
  the index is frozen, deterministic and serialisable.
- AC-3 (falsifiable): the index's config-option entries match the configuration
  surfaces that exist in the code (compiler configuration fields, trust record,
  verbosity levels, output root), so an option cannot exist without an index entry
  claiming its documentation.

**Owner action required (morning merge):** the actual user-facing pages
(`docs/user/installation.md`, `docs/user/workflows/*.md`, `docs/user/options/*.md`)
are outside this run's allowed paths; the index below is the complete table of
contents they must satisfy, and the ledger records their creation as a shared-file
change. WP-CORE-07 therefore lands as PARTIAL: the externalisation mechanism and the
documentation index are in; the user-facing pages themselves are not.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-NFR-190** | User-facing text shall be externalized from code to permit translation, without translation being delivered in v1.0. | `src/ectt/core/text.py` (`MessageCatalog`, `default_catalog`, `UnknownMessageKeyError`, `TextFormatError`), re-exported by `src/ectt/core/__init__.py` | **Guarantee:** user-facing text lives in a frozen catalog keyed by stable identifiers (`app.title`, `untrusted_project.warning`, `ingest.*`, `build.plan.*`, `environment.*`, `config.not_data`, `harness.generated`, `diagnostic.bundle.created`); look-ups by key, formatting with named placeholders; an unknown key raises `UnknownMessageKeyError` and a message whose placeholder is not supplied raises `TextFormatError` — both named, both deterministic. The shipped catalog is English-only and explicitly named `en` (no translation in v1.0); a translation is delivered by constructing another `MessageCatalog` — demonstrated in the tests with a German catalog substituting for the English one with no code change. Catalog keys and serialisation are sorted and byte-stable.<br><br>**Honest limits:** migrating every existing call site to catalog look-ups is incremental adoption; the catalog and the lookup discipline (what every call site must use) are what this increment establishes.<br><br>**Test evidence:** `tests/core/test_text_docs.py` — `test_catalog_lookup_and_formatting`, `test_catalog_lookup_without_values`, `test_unknown_key_is_named_error`, `test_missing_placeholder_is_named_error`, `test_translation_is_catalog_substitution_not_code_edit`, `test_default_catalog_is_english_only`, `test_catalog_keys_are_sorted_and_deterministic`, `test_catalog_is_frozen_and_malformed_rejected`. |
| **TOOL-NFR-120** | The tool shall provide user documentation covering installation, every supported workflow, and every configuration option. *(Method I)* | `src/ectt/core/docindex.py` (`documentation_index`, `UserDocumentationIndex`, `DocEntry`, `STATUS_PENDING`/`STATUS_SHIPPED`), re-exported by `src/ectt/core/__init__.py`; the table of contents is also §The index below | **Guarantee:** the machine-readable index enumerates 1 installation entry, 9 workflow entries, and 5 configuration-option entries; every entry carries a stable id, title, doc anchor under `docs/user/`, and a status; duplicate ids and unknown look-ups are named errors; the index is frozen and byte-stable. The option entries correspond one-to-one with configuration surfaces that exist in code (compiler configuration format fields, trust record, verbosity, output root, sanitizers), so an option cannot exist without an index entry claiming its documentation.<br><br>**Inspection argument:** what is inspected is the completeness discipline, not the pages — the pages (`docs/user/*.md`) are outside this run's allowed paths and are recorded as a shared-file change for the morning merge; the index is the complete table of contents they must satisfy, with every entry marked `pending-page-not-created` until a page lands.<br><br>**Test evidence:** `tests/core/test_text_docs.py` — `test_index_covers_installation_workflows_and_options`, `test_index_config_entries_match_code_surfaces`, `test_every_entry_has_title_anchor_and_status`, `test_index_is_frozen_and_deterministic`, `test_unknown_index_entry_is_named_error`, `test_index_rejects_duplicate_entries`. |

## The index (owner: create these pages)

| Entry | Title | Page | Status |
|---|---|---|---|
| `installation` | Installation | docs/user/installation.md | pending-page-not-created |
| `workflow.single_file` | Single-file testing without a build system | docs/user/workflows/single-file.md | pending-page-not-created |
| `workflow.compile_database` | Ingesting a compilation database | docs/user/workflows/compile-database.md | pending-page-not-created |
| `workflow.build_interception` | Ingesting via build interception (Bear) | docs/user/workflows/build-interception.md | pending-page-not-created |
| `workflow.compiler_config` | Adding a compiler configuration | docs/user/workflows/compiler-config.md | pending-page-not-created |
| `workflow.harness_generation` | Generating and regenerating a harness | docs/user/workflows/harness-generation.md | pending-page-not-created |
| `workflow.incremental_build` | Building with sanitizers and incremental rebuild | docs/user/workflows/building.md | pending-page-not-created |
| `workflow.test_cases_c` | Authoring test cases in C | docs/user/workflows/test-cases-c.md | pending-page-not-created |
| `workflow.security_first_run` | First run, environment verification and untrusted-project warning | docs/user/workflows/first-run-security.md | pending-page-not-created |
| `workflow.diagnostic_bundle` | Producing a diagnostic bundle for a defect report | docs/user/workflows/diagnostic-bundle.md | pending-page-not-created |
| `option.compiler_config.format` | Compiler configuration file fields | docs/user/options/compiler-config.md | pending-page-not-created |
| `option.trust_record` | Untrusted-project trust record | docs/user/options/trust-record.md | pending-page-not-created |
| `option.verbosity` | Logging verbosity levels | docs/user/options/verbosity.md | pending-page-not-created |
| `option.output_root` | Confined output root | docs/user/options/output-root.md | pending-page-not-created |
| `option.sanitizers` | Sanitizer modes and runtime options | docs/user/options/sanitizers.md | pending-page-not-created |

## Standing summary

WP-CORE-07 is recorded as **PARTIAL** in the ledger: the externalisation mechanism and
the complete documentation index are in and tested; the actual `docs/user/` pages are
an owner shared-file change (see the ledger and the morning summary).
