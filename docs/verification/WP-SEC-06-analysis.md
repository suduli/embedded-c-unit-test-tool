# Verification Analysis Note — WP-SEC-06 (Restricted Execution Context for Harnesses)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-SEC-06. Derived from the security policy's execution-context requirement
(hardening the host execution of TOOL-EXE-010/030):

- **AC-1:** a restricted context confines the working directory (resolved inside
  the project root; an escape is refused with the named reason `path_escape`),
  scrubs the environment (only an explicit allow-list passes, values taken from
  the machine's environment; an allow-listed name absent from the machine is
  omitted, never invented), and closes inherited handles (`inherit_handles` is
  always False — a security property, not an option).
- **AC-2:** the context carries a wall-clock limit and an output size limit, both
  positive; the executed result records both limits alongside the context.
- **AC-3:** a refused context starts nothing: every refusal (`path_escape`,
  `invalid_limit`, `empty_allow_list`) is raised before the starter is invoked —
  proven with a recording fake starter whose call list stays empty.
- **AC-4:** the run goes through an injected starter (production:
  `subprocess.run` with `cwd`, the scrubbed `env`, `close_fds=True` and the
  wall-clock limit as the timeout; tests: a fake that records exactly what it was
  given). The result records the captured output truncated to the output limit
  with `stdout_truncated=True` when the limit binds, and `timed_out=True` when
  the starter reports the wall-clock limit as exceeded.
- **AC-5:** there is no C compiler, debugger or simulator on this machine: the C
  side is not exercised; verification is by fake callables (the recording
  starter) and golden text of the recorded invocation. No real process is
  started by the tests.

## Implementation

- `src/ectt/exh/restricted.py` — `RestrictedContext` (frozen), `build_context`
  (confinement + scrub + limits, refusing before anything runs),
  `RestrictedRunResult` (context, exit status, truncated output, timed-out flag),
  `run_restricted` (the injected-starter runner; `default_starter` wraps
  `subprocess.run` with `close_fds=True`).
- `tests/exh/test_restricted.py` — the AC checks with a recording fake starter.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/exh/`) |
|---|---|---|
| Restricted execution context for starting a generated harness | `restricted.py` (`build_context`, `run_restricted`, `default_starter`) | `test_restricted.py::test_the_environment_passes_only_the_allow_list`, `::test_directory_confinement_refuses_a_path_escape`, `::test_a_refused_context_starts_nothing`, `::test_the_limits_are_recorded_in_the_result`, `::test_the_output_limit_truncates_and_flags`, `::test_the_starter_receives_the_scrubbed_invocation`, `::test_a_wall_clock_exceeding_starter_reports_timed_out`, `::test_the_recorded_invocation_is_golden_stable` |

## Not covered by this increment

- **OS-level sandboxing** (job objects, seccomp, containers) — the context
  restricts what the runner passes to the process starter; a hard OS boundary is
  platform work beyond this machine's scope.
- **Pipe-level output enforcement** — the output limit is enforced on the captured
  result (truncation recorded); a starter that enforces the limit at the pipe can
  replace the default one without touching this module.
- **Real C harness launches** — no compiler on this machine; the contract is
  proven with the recording starter, and the production starter is a thin
  `subprocess.run` wrapper.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
