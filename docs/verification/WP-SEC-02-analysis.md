# Verification Analysis Note — WP-SEC-02 (Pinned Dependency Integrity Check)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-SEC-02. Derived from the security policy's supply-chain requirement (the
checker operationalises the SBOM of WP-SEC-01 against a pinned lock file):

- **AC-1:** the lock file is the pinned form `name==version --hash=sha256:<64
  lowercase hex>` per line (comments and blank lines ignored); loading is strict
  with named refusals — `malformed_line`, `bad_hash`, `duplicate_pin`.
- **AC-2:** the checker compares the installed packages against the pins and
  reports **each difference by name**, with exactly one difference per package and
  kind: `missing` (pinned, not installed), `extra` (installed, not pinned),
  `wrong_version` (both present, versions differ), `wrong_hash` (both hashes
  present and differ), `unpinned` (integrity cannot be verified: the lock entry or
  the installed evidence lacks a hash).
- **AC-3:** the checker is read-only: it takes the installed state as data and the
  lock text as text — it never installs, upgrades or writes anything, and it
  performs no network access.
- **AC-4:** the result is deterministic: differences sorted by (name, kind),
  identical inputs give identical output.

## Implementation

- `src/ectt/sec/pins.py` — `PinnedPackage`/`PinDifference`, `load_pin_lock` (strict
  lock-file loader), `check_pins` (the comparison, plain-data in, differences out).
- `tests/sec/test_pins.py` — the AC checks (installed state is always injected —
  the checker cannot touch the environment even if it wanted to).

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/sec/`) |
|---|---|---|
| Supply-chain integrity: the installed tree matches the pinned lock | `pins.py` (`load_pin_lock`, `check_pins`) | `test_pins.py::test_a_clean_match_reports_no_differences`, `::test_a_missing_pin_is_reported_by_name`, `::test_an_extra_package_is_reported_by_name`, `::test_a_wrong_version_is_reported_by_name`, `::test_a_wrong_hash_is_reported_by_name`, `::test_an_unverifiable_integrity_is_reported_as_unpinned`, `::test_a_malformed_lock_file_is_refused`, `::test_the_report_is_sorted_and_deterministic` |

## Not covered by this increment

- **Producing the lock file** (freezing the environment) — the checker consumes a
  lock; a freeze command is packaging work touching `pyproject.toml`/release
  tooling, which this item must not edit.
- **Auto-remediation** — deliberately none: the checker reports; installing or
  upgrading anything is contrary to its read-only contract.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
