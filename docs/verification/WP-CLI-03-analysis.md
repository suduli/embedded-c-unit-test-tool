# WP-CLI-03 — Analysis: container execution

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-CLI-03.
Derived from the SRS-001 text (TOOL-CIC-040, verification method D) and the register split
(WP-PKG-05 owns the *versioned CI container image*, INS-090):

- **AC-1 (TOOL-CIC-040, executable):** the CLI executes correctly in a container-like process
  environment — no display server variables, no TTY on stdin, plain stdio output only — with the
  WP-CLI-02 exit codes observed end-to-end through `python -m ectt.cli`.
- **AC-2 (TOOL-CIC-040, executable):** the CLI emits nothing but the requested output on stdout
  (no banner or interactive noise), so container logs stay machine-readable.
- **AC-3 (TOOL-CIC-040, installable):** the reference install-and-run sequence for a container
  image is documented (below) and is exactly the sequence this run executes in-process — the
  actual image build is WP-PKG-05's deliverable (INS-090) and is not duplicated here.

## Implementation

- `tests/cli/test_container.py` — subprocess-level demonstration of the container-safety
  contract: `python -m ectt.cli` invoked with a stripped environment (no `DISPLAY`, no `TERM`,
  stdin closed), asserting catalogue listing on stdout, exit-code fidelity for tool errors, and
  stdout cleanliness.
- No new `src/` behaviour was required: the CLI is already stdio-only with no GUI imports
  (WP-CLI-01, TOOL-CIC-020) and stable exit codes (WP-CLI-02, TOOL-CIC-030); this WP
  demonstrates and pins that contract at the process boundary.

## Reference container recipe (AC-3, for WP-PKG-05 to productise)

```
# inside a Python 3.11+ base image, non-root user, no display server:
pip install --no-cache-dir /opt/ectt          # the release package (WP-PKG-01 ships it)
python -m ectt.cli --list-commands            # smoke: exits 0, prints catalogue names
python -m ectt.cli operation.cancel --target-id 17   # unwired op exits 1 (tool error)
```

The image itself (versioning, tagging, registry publication) is WP-PKG-05 (CMP-PKG, INS-090);
WP-CLI-03 owns the *execution* contract only.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/cli/`) |
|---|---|---|
| TOOL-CIC-040 (executable within a container image) | container-safety contract pinned at process boundary | `test_container.py::test_cli_runs_headless_in_stripped_environment`, `::test_stdout_carries_only_requested_output`, `::test_unwired_operation_exit_code_in_container_env`, `::test_help_works_without_tty` |

## Not covered by this increment

- Actual container-image build and publication — WP-PKG-05 (INS-090); a docker demonstration was
  not run in this environment.
- CI pipelines and artifact caching — WP-CLI-04 (TOOL-CIC-050/070).

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
**PARTIAL**: the executable contract is demonstrated and pinned; the installable half (real
container image) belongs to WP-PKG-05 and has not been demonstrated here.
