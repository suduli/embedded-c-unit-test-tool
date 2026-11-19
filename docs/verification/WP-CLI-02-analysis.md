# WP-CLI-02 — Analysis: stable documented exit codes

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-CLI-02.
Derived from the SRS-001 text (TOOL-CIC-030):

- **AC-1:** the CLI defines a **stable, documented** exit-code table distinguishing at least:
  success, test failure, coverage threshold failure, and tool error — the four categories named
  by TOOL-CIC-030, as named module constants (stability = constants with committed values, not
  ad-hoc literals at call sites).
- **AC-2:** the four distinguished outcomes are reachable in code: dispatching a CLI invocation
  can end in each category, and `run()` maps the outcome to the table's code.
- **AC-3:** the table is **documented**: the module docstring and the analysis note record the
  numeric value and meaning of every code, so a CI author can rely on them.
- **AC-4:** every exit other than success is distinguishable from success and from each other
  (distinct non-zero values; usage errors keep argparse's conventional 2, recorded in the table
  as the usage-error row — the requirement's four categories are covered by the named constants).
- **AC-5 (scope boundary):** the *producers* of test-failure and coverage-threshold outcomes
  (execution, coverage enforcement) are later CMP-* packages; this WP delivers the code table and
  the mapping, with handlers returning them. Container execution (TOOL-CIC-040, WP-CLI-03) is out
  of scope.

## Implementation

- `src/ectt/cli/exit_codes.py` — named constants `EXIT_SUCCESS` (0), `EXIT_TEST_FAILURE` (10),
  `EXIT_COVERAGE_THRESHOLD` (11), `EXIT_TOOL_ERROR` (1), plus `EXIT_USAGE` (2, argparse
  conventional) and `EXIT_OPERATION_NOT_AVAILABLE` (1 alias of tool error, from WP-CLI-01);
  `EXIT_CODE_TABLE` mapping value → meaning for documentation and for tests.
- `src/ectt/cli/dispatch.py` — `run()` accepts a `--result` style outcome from handlers: handlers
  return an exit code; unwired operations and `CliError` map to `EXIT_TOOL_ERROR`; usage errors
  remain argparse's 2. The provisional WP-CLI-01 constant is re-pointed at the stable table.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/cli/`) |
|---|---|---|
| TOOL-CIC-030 (documented, stable codes distinguishing the four categories) | `exit_codes.py` constants + `EXIT_CODE_TABLE` | `test_exit_codes.py::test_four_categories_have_distinct_stable_codes`, `::test_exit_code_table_documents_every_code`, `::test_success_is_zero_and_others_nonzero`, `::test_tool_error_is_returned_for_cli_error`, `::test_handler_returned_codes_pass_through`, `::test_operation_not_available_maps_to_tool_error` |

## Not covered by this increment

- A user-facing man page/doc page — the code table is documented in-module and here; a rendered
  doc page belongs to WP-CORE-07 (user documentation).
- Producers of real test-failure/coverage outcomes — CMP-EXH/CMP-COV packages.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
