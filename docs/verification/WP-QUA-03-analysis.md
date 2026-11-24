# Verification Analysis Note — WP-QUA-03 (User-Executable Validation Suite)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-QUA-03. Derived from the SRS-001 text (TOOL-QUA-030, method *I* — "The tool shall
have a validation test suite demonstrating that it satisfies its Tool Operational
Requirements, executable by the end user"):

- **AC-1:** the suite is a list of self-checks, each declaring its id, the claim it
  proves, and its declared cost class (`instant` | `quick` | `long`). The cost is
  *declared*, never measured — the record carries no wall-clock value
  (TOOL-NFR-060 discipline).
- **AC-2:** the suite is executable by the end user on their own machine: the runner
  executes the checks with bundled inputs only — no network, no compiler, no
  debugger — and the bundled default checks prove engine fundamentals that hold
  offline.
- **AC-3:** every result is exactly one of `pass`, `fail`, `not-run`, with a named
  reason on every non-pass (`missing_tool` naming the absent tool, `check_failed`,
  `check_error`). A check that needs a tool the machine does not have is `not-run`
  and can never read as a pass.
- **AC-4:** the result record is deterministic JSON, byte-stable across runs and
  independent of the order in which the checks were presented (processed in id
  order).

## Implementation

- `src/ectt/qua/validation.py` — `ValidationCheck` (id, proves, declared cost,
  required tools, the check callable), `run_validation_suite` (offline runner:
  missing-tool gate first, then the check), `CheckOutcome`/`ValidationReport`
  (deterministic record with counts), `default_validation_checks` (bundled,
  `requires=()`: catalogue published, protocol version self-consistency,
  deterministic JSON, operational specification renders).
- `tests/qua/test_validation.py` — the AC checks.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/qua/`) |
|---|---|---|
| TOOL-QUA-030 (validation suite executable by the end user) | `validation.py` (`ValidationCheck`, `run_validation_suite`, `ValidationReport`, `default_validation_checks`) | `test_validation.py::test_every_check_passes_on_a_clean_machine`, `::test_a_failing_check_reports_fail_with_its_reason`, `::test_a_missing_tool_is_not_run_never_pass`, `::test_the_record_is_byte_stable_and_order_independent`, `::test_the_record_carries_id_proves_and_cost`, `::test_a_raising_check_fails_without_details_leaking`, `::test_invalid_check_definitions_are_refused`, `::test_the_bundled_checks_pass_offline` |

## Not covered by this increment

- Checks that exercise a real compiler/toolchain (none is installed on the
  development machine; a toolchain check would be `not-run` there by design) — the
  bundled set proves engine fundamentals only, and the `requires` gate is the
  mechanism a distribution uses to add tool-dependent checks.
- Timing measurement: the cost class is declared per check, not measured — a
  measured duration would put wall-clock into the record.
- Packaging the suite as a console entry point (a `pyproject` scripts change is
  outside this item's allowed paths); the runner is a plain function an end user
  can call.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
