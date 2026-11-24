# Verification Analysis Note — WP-QUA-04 (Known Error List per Release)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-QUA-04. Derived from the SRS-001 text (TOOL-QUA-040, method *I* — "The tool
shall publish a documented list of known errors and their workarounds, maintained
per release"):

- **AC-1:** a known-error entry carries its id, summary, the versions it affects,
  its workaround, and its status — `open` or `fixed in <version>`.
- **AC-2:** the list is maintained as a plain-text data file and loaded strictly:
  every refusal names its reason — `duplicate_error_id`,
  `fixed_before_introduced` (a fixed-in version not after the introduced version),
  `missing_workaround` (an open entry without a workaround), `missing_field`,
  `unknown_field`, `malformed_line`, `version_malformed`,
  `fixed_missing_version` (a `fixed` status with no version).
- **AC-3:** the query returns exactly the entries that apply to a given release:
  the release is in the entry's affected versions and the error is not fixed as of
  that release (version-ordered comparison); the answer is id-sorted and
  deterministic.
- **AC-4:** version comparison is exact and order-independent of how the list was
  written (entries are returned in id order).

## Implementation

- `src/ectt/qua/known_errors.py` — `KnownError` (frozen entry), `load_known_errors`
  (strict plain-text block loader with the named refusals), `errors_for_release`
  (the id-sorted applicable query), `_version_key` (numeric per-component version
  ordering).
- `tests/qua/test_known_errors.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-040 (documented known-error list with workarounds, maintained per release) | `known_errors.py` (`KnownError`, `load_known_errors`, `errors_for_release`) | `test_known_errors.py::test_a_well_formed_list_loads`, `::test_duplicate_error_ids_are_refused`, `::test_fixed_in_not_after_introduced_is_refused`, `::test_an_open_entry_without_a_workaround_is_refused`, `::test_malformed_and_unknown_fields_are_refused`, `::test_versions_must_parse`, `::test_the_query_returns_exactly_what_applies`, `::test_a_fixed_error_stops_applying_after_its_fix`, `::test_the_query_is_id_sorted_and_deterministic` |

## Not covered by this increment

- Publishing the list as a release artifact (rendering into the report or the user
  documentation) — the model and query are the data layer; the renderer change
  belongs to the report lane.
- Free-form status vocabulary beyond `open` / `fixed in <version>` (e.g.
  `wont-fix`) — extending it is a deliberate vocabulary change once a release
  needs it.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
