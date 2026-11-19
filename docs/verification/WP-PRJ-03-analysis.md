# Verification Analysis Note — WP-PRJ-03 (Schema Migration with Explicit Confirmation)

Analysis evidence for requirements verified under WP-PRJ-03. No change to the published project schema: the manifest is still at version 1, its only version. The migration machinery is exercised with a test kind.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PRJ-040** | Project data migration shall be explicit, reversible where possible, and shall never occur without user confirmation. | `src/ectt/prj/migration.py` (`inspect_migration`, `migrate_file`, `revert_migration`, `MigrationRegistry`, `MigrationPlan`), `tests/prj/test_migration.py` | **Guarantee (never by side effect):** opening a file below the reader's minimum still raises `MigrationRequiredError` and writes nothing. Only the migration functions can change a file.<br><br>**Guarantee (explicit):** `inspect_migration` reads the file and returns the plan (each step, and whether it is irreversible). It writes nothing.<br><br>**Guarantee (confirmed):** `migrate_file` and `revert_migration` act only when `confirmed` is exactly `True`. Any other value (`False`, `None`, `"yes"`, `1`) raises `migration_not_confirmed` before anything is written.<br><br>**Guarantee (reversible where possible):** every confirmed migration archives the original bytes first, under `archive/migration-v<from>-to-v<to>/<file>`. `revert_migration` restores them, also under confirmation. A step with no inverse is declared irreversible in the plan, and that declaration is shown in the confirmation message before anything runs.<br><br>**Guarantee (fail safe):** each step runs on a deep copy. A raising step gives `migration_failed` with the original as cause, and nothing is written. A missing link in the chain is refused up front (`migration_chain_missing`). An archive that already holds different bytes is never overwritten (`backup_exists`). The file is replaced atomically (temp file, fsync, `os.replace`).<br><br>**Guarantee (forward only, supported target):** a target at or below the current version is refused (`migration_not_forward`, `migration_not_needed`), and a target outside the kind's supported range is refused (`target_unsupported`).<br><br>**Guarantee (deterministic):** the same input migrates to byte-identical output (TOOL-PRJ-050 in the test name).<br><br>**Test evidence:** `tests/prj/test_migration.py` — `test_opening_an_old_file_reports_migration_and_changes_nothing`, `test_inspection_reports_the_plan_and_writes_nothing`, `test_migration_refuses_without_exact_confirmation` (four non-`True` values), `test_confirmed_migration_archives_original_then_replaces_file`, `test_migration_is_deterministic`, `test_failing_step_leaves_file_and_archive_untouched`, `test_missing_step_in_the_chain_is_refused_before_anything_runs`, `test_irreversible_step_is_declared_before_running`, `test_existing_archive_with_different_content_is_never_overwritten`, `test_revert_restores_the_archived_original_only_when_confirmed`, `test_migration_is_refused_when_already_current_or_going_backwards`, `test_project_manifest_is_at_its_only_version_so_no_migration_applies`. |

## Not yet covered

- **No production migration.** The project manifest is at version 1, its only version, so there is nothing to migrate from yet. The first real migration will be the first schema bump, and it must be registered and tested then. Until then the machinery is proven only against a test kind.
- **Archive covers the manifest only.** SDD-003 §5 asks for the pre-migration *tree* to be copied under `archive/`. The current manifest is the only versioned file, so archiving that file is the whole tree today. When other versioned files exist, the archive must cover them too.
- **No CLI or GUI confirmation prompt.** The confirmation is an explicit argument. The prompt that asks the user belongs to the caller, which does not exist yet.
- **Concurrent writers are not guarded.** Two processes migrating the same file could race between the read and the replace. The project has no lock for this yet.

## Design notes

- **Why the version check uses a floor of zero.** `dispatch_schema_version` refuses versions below the minimum, which is the right behaviour for opening. Migration is the one place that must read such a file, so it reads with a floor of zero and still applies the upper bound.
- **Why confirmation is `is True`.** A truthy value such as a non-empty string must not confirm a change to the user's data. Only the literal boolean does.
- **Why the archive is written before the replace.** If the process stops between the two writes, the original still exists. Stopping after the replace leaves the archive as the recovery path.

## Night-run re-verification (2026-11-18, chat 2)

Re-ran the evidence suites on this worktree: `tests/prj/test_migration.py` → 19 passed;
with `test_shards.py` → 26 passed, 0 skipped; full suite 490 passed / 4 skipped (baseline 4).
TOOL-PRJ-040 (explicit, reversible-where-possible, never without user confirmation) is fully
evidenced: exact-confirmation refusal, archive-and-revert, deterministic steps, failing-step
safety, and the manifest's single-version no-op are all named tests. **DONE**.
