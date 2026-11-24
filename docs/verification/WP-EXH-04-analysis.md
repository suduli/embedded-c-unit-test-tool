# Verification Analysis Note — WP-EXH-04 (Debugger Launch with Entry Breakpoint)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-EXH-04. Derived from the SRS-001 text (TOOL-EXE-070, method *T* — "The tool
shall support launching a test case under a debugger, with the harness prepared
and execution stopped at entry to the function under test"):

- **AC-1:** the launch builder constructs the gdb command line (gdb first) with a
  breakpoint at the test function's entry (`break <function>`), the harness as the
  debuggee, and the arguments the normal run uses (e.g. `--ectt-select`); the
  working directory travels beside the argv as the normal run's cwd does. The
  argv is deterministic and golden-tested.
- **AC-2:** every refusal names its reason, in this order, before anything can
  start: `debugger_not_named` (no debugger given), `no_symbols` (the build did not
  record debug symbols — stepping needs them), `harness_not_built` (the harness
  file does not exist).
- **AC-3:** starting the debugger is behind an injected starter: the builder only
  constructs; the launcher hands the argv and the working directory to the
  starter. Tests use a recording fake — no debugger exists on this machine, and
  no test starts a real process.
- **AC-4:** paths with spaces survive intact in the argv (the argv is the
  execution contract), and the display form quotes them
  (`shlex.join`), golden-tested.

## Implementation

- `src/ectt/exh/debugger.py` — `DebugLaunch` (argv, working directory, breakpoint,
  display command line), `build_debugger_launch` (the refusals in order, then the
  deterministic argv), `start_debugger` (the injected-starter hand-off).
- `tests/exh/test_debugger.py` — the AC checks with a recording fake starter.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/exh/`) |
|---|---|---|
| TOOL-EXE-070 (launch a test case under a debugger, stopped at entry to the function under test) | `debugger.py` (`build_debugger_launch`, `start_debugger`, `DebugLaunch`) | `test_debugger.py::test_the_gdb_argv_is_golden_stable`, `::test_an_unnamed_debugger_is_refused`, `::test_a_build_without_symbols_is_refused`, `::test_an_unbuilt_harness_is_refused`, `::test_the_starter_receives_the_argv_and_the_working_directory`, `::test_paths_with_spaces_survive_and_quote_for_display`, `::test_a_refused_launch_never_starts` |

## Not covered by this increment

- **The debugger front-end decision** (TOOL-UIX-230's open question: embedded
  GDB/MI client vs. handing off to an external debugger — recorded as SRS open
  question 9) — this increment hands off to the named debugger binary behind an
  injected starter; a GDB/MI client is the owner's call.
- **Debuggers other than gdb** — gdb first, as the item directs; another debugger
  is a new argv builder behind the same refusal contract.
- **Real debugger sessions** — no debugger is installed here; the contract is
  proven with the recording starter.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
