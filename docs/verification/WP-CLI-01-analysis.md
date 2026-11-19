# WP-CLI-01 — Analysis: non-interactive CLI generated from the operation catalogue

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-CLI-01.
Derived from the SRS-001 texts (TOOL-CIC-010, TOOL-CIC-020) and the recorded design
(SDD-002 §9.3, DSN-CLI-010 — "the CLI is generated from the same catalogue the API publishes"):

- **AC-1 (TOOL-CIC-010):** a non-interactive command-line interface exists and is **generated**
  from the engine operation catalogue: every catalogue operation yields a subcommand, and no
  subcommand can exist that the catalogue does not publish (one capability surface, DSN-CLI-010).
- **AC-2 (TOOL-CIC-020):** the CLI operates without a graphical environment or display server —
  its modules import no GUI/Qt dependency and dispatch works with stdin/stdout only.
- **AC-3 (TOOL-CIC-010):** invoking a catalogue operation whose engine executor is not yet wired
  in this build reports the error and exits non-zero — never emitting misleading success output
  (fail-safe per TOOL-NFR-090); invoking an unknown command is a usage error.
- **AC-4 (TOOL-CIC-010):** `--list-commands` prints exactly the catalogue operation names
  (deterministic, sorted), giving automated verification a machine-readable surface without
  interaction.
- **AC-5 (scope boundary):** stable *documented* exit codes are WP-CLI-02 (TOOL-CIC-030) and are
  not claimed here beyond the fail-safe 0-success/non-zero-failure split above; container
  execution is WP-CLI-03.

## Implementation

- `src/ectt/cli/generator.py` — `build_parser(catalogue)` builds an `argparse` parser with one
  subparser per catalogue operation (name, help = operation summary, `--target-id` params from the
  catalogue entry); `command_names(catalogue)` for the deterministic listing.
- `src/ectt/cli/dispatch.py` — `Dispatcher` registry (handlers per operation name);
  `run(argv, catalogue, dispatcher)` → exit code. Unwired catalogue operations report
  `OperationNotAvailable` and exit non-zero.
- `src/ectt/cli/errors.py` — `CliError(EcttError)` (category `cli`), `OperationNotAvailable`.
- `src/ectt/cli/__main__.py` — `python -m ectt.cli` entry without touching the shared
  `pyproject.toml`.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/cli/`) |
|---|---|---|
| TOOL-CIC-010 (all automated-verification functionality on a non-interactive CLI) | catalogue-driven parser + dispatcher + `--list-commands` | `test_generator.py::test_every_catalogue_operation_yields_a_subcommand`, `::test_no_command_outside_catalogue`, `test_dispatch.py::test_list_commands_prints_catalogue_names`, `::test_unknown_command_is_usage_error` |
| TOOL-CIC-020 (no graphical environment or display server) | no GUI/Qt imports anywhere under `src/ectt/cli/` | `test_headless.py::test_cli_modules_import_no_gui_dependencies` (AST scan of `src/ectt/cli`), `::test_dispatch_runs_without_display` |
| TOOL-CIC-010 / TOOL-NFR-090 (fail-safe on unwired op) | `OperationNotAvailable` → non-zero exit, message on stderr | `test_dispatch.py::test_unwired_catalogue_operation_fails_safe_nonzero`, `::test_wired_handler_exit_code_zero` |

## Not covered by this increment

- Stable documented exit-code table — WP-CLI-02 (TOOL-CIC-030).
- Container execution — WP-CLI-03 (TOOL-CIC-040).
- Actual engine operations: the catalogue currently publishes the protocol-level
  `operation.cancel` only; executors arrive with the owning packages (registering a handler in
  tests demonstrates the dispatch path end-to-end without claiming engine behaviour).

## Verification status

Gates re-run after the increment: suite green (with new CLI tests), ruff/mypy/plan_check/
trace_check exit 0. All five ACs met by named tests.
