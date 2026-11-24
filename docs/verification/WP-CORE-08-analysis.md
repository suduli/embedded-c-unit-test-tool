# Verification Analysis Note — WP-CORE-08 (Self-Verification of the Tool's Own Source)

Lane: A (night run) · 2026-11-23 · Worktree `wt-night-23a`, branch `glm-night/20261123-a`, baseline local `main` (80cf5c6).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
WP-CORE-08. Derived from the integrity requirement of the security policy (the
tool can prove its own installed tree matches what was shipped):

- **AC-1:** a manifest records the SHA-256 of every file of a package tree, as
  deterministic canonical JSON (`manifest_version`, `files` mapping of
  project-relative POSIX path to 64-hex digest), sorted, with `__pycache__`
  directories and `.pyc` files ignored everywhere.
- **AC-2:** verification names every difference: `changed` (present in both, digest
  differs), `missing` (in the manifest, not in the tree), `unexpected` (in the
  tree, not in the manifest); the verdict is clean exactly when all three lists
  are empty.
- **AC-3:** the manifest itself is load-verified: a malformed document, an unknown
  manifest version, a non-hex digest or a non-mapping file entry is refused with
  the named reason `manifest_tampered` (plus `manifest_malformed`,
  `manifest_version`) — never silently accepted as clean.
- **AC-4:** no manifest generated from this repository's tree is committed as a
  fixed file: the functions operate on any tree, and the tests build their own
  temp trees (the shipped tree's manifest is produced at packaging time, an owner
  concern).

## Implementation

- `src/ectt/core/selfverify.py` — `write_manifest` (the tree walk + digest map,
  canonical JSON), `verify_tree` (strict manifest load + the three difference
  lists), `SelfVerification` (the verdict record), `SelfVerificationError` (named
  refusals).
- `tests/core/test_selfverify.py` — the AC checks on temp trees.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/core/`) |
|---|---|---|
| The tool can verify its own installed source against a manifest | `selfverify.py` (`write_manifest`, `verify_tree`, `SelfVerification`) | `test_selfverify.py::test_a_clean_tree_verifies`, `::test_a_changed_file_is_named`, `::test_a_missing_file_is_named`, `::test_an_unexpected_file_is_named`, `::test_pycache_is_ignored`, `::test_a_tampered_manifest_is_refused`, `::test_the_manifest_is_deterministic_and_round_trips`, `::test_nested_directories_are_covered` |

## Not covered by this increment

- **Generating the shipped manifest at packaging time** (wiring it into the
  release build) — a packaging/`pyproject` concern outside this item's allowed
  paths; the functions are packaging-agnostic.
- **Signing the manifest** — signing keys are the owner's (as recorded for
  WP-SEC-01); an unsigned manifest detects drift, not malice.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
