# WP-PRJ-02 — Analysis: diff-stable sharded storage for concurrent edit

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-PRJ-02.
Derived from the SRS-001 texts (TOOL-PRJ-030, TOOL-PRJ-060):

- **AC-1 (TOOL-PRJ-060):** project data can be stored **sharded**: independent concerns map to
  independent plain-text files under a `shards/` directory, so concurrent edits by different
  users produce localized, resolvable version-control conflicts — editing concern A never touches
  concern B's file.
- **AC-2 (TOOL-PRJ-060, diff stability):** rewriting a shard whose content is unchanged leaves the
  file byte-identical (no diff, no churn); a changed shard is rewritten atomically.
- **AC-3:** shard names are project-relative and validated — absolute paths and `..` escapes are
  refused with named errors (same confinement contract as TOOL-PRJ-070).
- **AC-4 (TOOL-PRJ-030):** opening a project created by an earlier version reports precisely why
  it cannot open and what migration is required — this is **already implemented and tested** in
  the schema dispatch/migration layer; this WP cites that evidence and adds no duplicate
  mechanism.
- **AC-5 (scope boundary):** concurrency *resolution* (merge tooling) is the user's VCS job —
  the requirement asks for localized conflicts, not automatic merges. Cross-process file locking
  is out of scope (no requirement names it).

## Implementation

- `src/ectt/prj/shards.py` — `ShardStore`: project-relative shard layout under `shards/`,
  name validation (`InvalidRelativePathError` reuse), diff-stable `write_shard` (returns whether
  bytes changed; atomic temp-file + `os.replace` rewrite only on change), `read_shard`.
- TOOL-PRJ-030 evidence: `tests/prj/test_schema_dispatch.py` (named `MigrationRequiredError` /
  `UnsupportedSchemaVersionError`), `tests/prj/test_migration.py::test_opening_an_old_file_reports_migration_and_changes_nothing`
  — cited, not re-implemented.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/prj/`) |
|---|---|---|
| TOOL-PRJ-060 (localized conflicts) | `ShardStore` one file per concern | `test_shards.py::test_editing_one_shard_leaves_other_shards_untouched`, `::test_shards_are_independent_plain_text_files` |
| TOOL-PRJ-060 (diff stability) | change-detecting writer | `::test_unchanged_shard_rewrite_is_byte_identical`, `::test_changed_shard_rewrites_atomically`, `::test_missing_shard_reads_none` |
| TOOL-PRJ-030 | existing schema dispatch + migration reporting (cited) | `test_schema_dispatch.py::test_schema_version_less_than_min` (MigrationRequiredError names what is required), `::test_schema_version_greater_than_max` (UnsupportedSchemaVersionError), `test_migration.py::test_opening_an_old_file_reports_migration_and_changes_nothing` |

## Not covered by this increment

- Migration of the shard layout itself (the manifest is at version 1 with no migration chain —
  `test_project_manifest_is_at_its_only_version_so_no_migration_applies`).
- Sharding integration into `Project.save` (the current single-file manifest remains the default
  until a project-file-format decision requires the split — recorded, not decided).

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
