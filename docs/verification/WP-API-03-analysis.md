# WP-API-03 — Analysis: CLI and GUI round-trip equivalence

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-API-03.
Derived from the SRS-001 text (TOOL-UIX-330) and the recorded mechanism (SDD-001 §4.4 DSN-API-040:
"every API response carries the equivalent CLI invocation, which is what makes ... the round-trip
guarantee of TOOL-UIX-330 fall out of the design"; DSN-CLI-010: CLI and API publish one catalogue):

- **AC-1 (DSN-API-040):** every operational engine-API response carries a `cli_equivalent` string
  resolvable against the catalogue; the bootstrap hello is exempt (connection setup has no CLI
  command).
- **AC-2 (DSN-CLI-010):** the CLI and the engine API publish **exactly the same** operation set —
  the generated CLI command list equals the catalogue, and the catalogue is the API's (one source,
  no drift).
- **AC-3 (TOOL-UIX-330 engine leg):** for every catalogue operation, the `cli_equivalent` string
  parses to a command the CLI actually exposes (first token maps to a subcommand), so a state
  change made through the API is reachable from the CLI.
- **AC-4 (scope boundary / GUI leg):** the reverse leg — a project created or modified through the
  *graphical application* — is not demonstrable: no GUI exists yet (WP-GUI-01..22, TOOL-UIX-030
  unimplemented, ADR-001 §3). The GUI depends on this WP; its absence is a recorded dependency
  state, not a defect in the engine-side contract.

## Implementation

- `src/ectt/api/roundtrip.py` — `cli_equivalent_for_response(op)` (AC-1: resolver with the hello
  exemption), `verify_cli_catalogue_identity(cli_names, catalogue)` (AC-2), `verify_cli_equivalent_reachable(cli_equivalent, cli_names)`
  (AC-3).
- `tests/api/test_roundtrip.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/api/`) |
|---|---|---|
| TOOL-UIX-330 (engine leg) + DSN-API-040/DSN-CLI-010 | `roundtrip.py` validators over the shared catalogue | `test_roundtrip.py::test_every_operational_response_can_carry_cli_equivalent`, `::test_hello_has_no_cli_equivalent`, `::test_cli_command_list_equals_catalogue`, `::test_every_cli_equivalent_parses_to_an_exposed_command`, `::test_error_envelope_cli_equivalent_round_trips` |

## Not covered by this increment

- The GUI leg of TOOL-UIX-330 (blocked on CMP-GUI existence — recorded dependency state).
- State-level round-trip on real project mutations (project store writes through API operations —
  the operations themselves are future CMP-* packages; the contract verified here is the
  command-surface equivalence the design relies on).

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
**PARTIAL**: engine-side contract implemented and tested; GUI leg blocked on the unimplemented GUI.
