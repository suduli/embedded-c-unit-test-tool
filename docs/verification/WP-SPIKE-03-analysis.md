# WP-SPIKE-03 — Verification analysis: PyInstaller distribution spike onto clean Windows

Lane: VERIFY (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

WP-SPIKE-03 owns **no SRS requirements** (validation spike; PLAN-001 §5.5) and no package-specific
acceptance criterion is recorded in PLAN-001 §5.4. The per-spike pass criterion comes from
**PLAN-001 §4.4**, transcribed verbatim:

> **Pass criterion (PLAN-001 §4.4):** PyInstaller-bundled PySide6 + libclang on a clean Windows
> machine with no Python. Installs and runs **without administrative privileges**, and is not
> quarantined by default endpoint security. Record size and cold-start time.

The GitHub-board reconciliation flag stays an owner task; this run does not write the board.

## Evidence chain (criterion → evidence)

| Criterion element | Recorded evidence (`spikes/spike-03-packaging/RESULTS.md`, ADR-001 §2.3.1) | Status |
|---|---|---|
| PyInstaller bundle of PySide6 + libclang builds | Built with `python -m PyInstaller packaging.spec` on first attempt; libclang.dll (≈80.1 MB) collected via plain `binaries=[...]`, no `Config.set_library_file()` fallback needed | met |
| Frozen app runs with no Python installed | `spike03_probe.exe` runs standalone from `dist/spike03_probe/`, libclang parses OK inside the frozen exe | met (on build machine) |
| Without administrative privileges | Non-elevated shell confirmed (`IsInRole(Administrator) = False`); nothing in build or run path implicates admin rights | met |
| Size recorded | 194.2 MB onedir distribution | met |
| Cold-start time recorded | in-process cold start ≈151–172 ms; process-launch wall ≈1520–1525 ms (dominated by a fixed sleep in the probe script) | met |
| **On a clean Windows machine; not quarantined by default endpoint security** | **Not verified.** RESULTS.md §"Honest limits of this spike": Defender history on the dev machine is not representative; closing requires copying `dist/spike03_probe/` to a genuinely clean Windows VM and observing launch/Defender/SmartScreen behaviour — a manual step the spike itself declares outside what any agentic session can complete unattended | **open** |

## Test evidence

The spike artifact contains no pytest suite (its deliverables are `app.py`, `packaging.spec`,
`measure.ps1` and the recorded measurements). The repository test suite is unaffected: 399 passed,
4 skipped on this worktree at the item's gate run. WP-SPIKE-03 owns no TOOL-* requirement, so no
requirement→test mapping exists by design; its unblocks feed `WP-GUI-01`/`WP-PKG-01` and ADR-001 §2/§3.

## Constraint compliance

- No `src/` or `tests/` files edited (VERIFY lane); no board or ADR writes.
- The packaging decision itself (ADR-001 §2/§3, Accepted 2026-09-19) is not reopened; this note
  verifies recorded evidence only.

## Result

**PARTIAL — verified as `PASS (local build)`; clean-machine endpoint-security element remains open.**
Every mechanically checkable element of the §4.4 criterion has recorded, reviewable evidence. The one
open element (clean Windows VM, no Python, default endpoint security: launch without quarantine) needs
a physical clean machine or VM and a human to observe the outcome — it cannot be closed by an
unattended run. Remains for the owner: run the manual clean-VM step, then record the observation as
the closing evidence for this spike (and the input ADR-001 §2.3.1 already flags for the packaging ADR
follow-up).
