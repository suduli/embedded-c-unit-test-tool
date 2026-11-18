# T-02 draft: no-import rule for vcast-findings material (2026-11-18)

**Status: DRAFT. Not adopted.** This proposal depends on owner decision **D-01** (licence posture, ADR-005). The rule's consequence anchor is ADR-005, and it must not be adopted before D-01 is answered. Nothing here changes a requirement, an ADR or a decision state. See `docs/proposals/decision-memos-20261117.md` for D-01.

Prepared under TASK-015 of EXEC-PLAN-001. The prototype check is `tests/core/test_no_vcast_import.py`.

## Problem

The `vcast-findings/` tree holds material recovered from third-party binaries (for example `vcastqt.exe`, `VcAppLib.dll`, `vcapplib-sql-strings.json`, `vcapplib-recovered-schema.sql`). That material is not ours to reuse. If the tool's source reproduces recovered strings or identifiers, the tool could carry vendor content into its own code. Nothing currently checks for that.

## Proposed requirement text (draft, unadopted)

> **TOOL-LIC-0xx (proposed).** The tool's source code shall not reproduce any string, SQL statement or identifier recovered from third-party binaries held in the reverse-engineering findings. Conformance is checked automatically against the findings, read in memory only, and the check shall fail the build on any match.

Numbering and priority are for the owner to assign. This draft adds no ID to the SRS.

## Proposed ADR-005 addendum (draft, unadopted)

> **Consequence (proposed).** Findings assets are read-only inputs to a conformance check. They are never copied into the repository, never vendored, and never imported. The check builds its deny-list in memory and writes nothing from the findings.

## Check design

1. **Deny-list construction** (in memory, nothing written):
   - `vcapplib-sql-strings.json`: each record's `text`, kept when at least 16 characters after trimming.
   - `vcapplib-recovered-schema.sql`: each non-comment line, same length floor.
   - `*-symbols.json`: export `names` and import `symbols`, same length floor.
   - The 16-character floor keeps short common words (for example `TAG`) out of the list. A test covers this.
2. **Scan**: every file under `src/` is read as text, whitespace-normalised, and checked for each entry as a substring. Output is sorted, so the result is deterministic.
3. **Result**: any hit is reported as `path: token`. The check fails if any hit exists or if the deny-list is empty (an empty list means the findings were not read).

### What the check does not catch

- **Near-identical copies.** Only exact matches after whitespace normalisation are detected. Renamed identifiers, reformatted SQL with different keywords and paraphrases pass. A near-match detector is a separate design and is not proposed here.
- **Short identifiers.** Anything under 16 characters is not checked. This trades coverage for a low false-positive rate.
- **Non-text sources.** Binary files under `src/` are skipped.

## Prototype status

`tests/core/test_no_vcast_import.py` contains 5 tests:

| Test | Runs without findings? | Result |
|---|---|---|
| `test_planted_fixture_string_is_detected` | yes | passes: a planted string in a temp `src/` is reported |
| `test_clean_fixture_source_passes` | yes | passes |
| `test_short_tokens_are_not_denied` | yes | passes |
| `test_scan_output_is_deterministic` | yes | passes |
| `test_repository_source_contains_no_findings_material` | only when findings are reachable | passes against the real findings and `src/` |

- **Reachability.** The findings tree is not in the worktree. It is gitignored in the `Unit` checkout, so the real-scan test is skipped here. Set `ECTT_VCAST_FINDINGS` to the findings folder to run it. With `ECTT_VCAST_FINDINGS=E:/projects/UDS_Simulator/Unit/vcast-findings`, the file gives 5 passed.
- **Deny-list size.** Against the current findings the deny-list holds 16,209 entries. Its contents are not reproduced here.
- **Fixtures.** The planted fixture uses a synthetic string (`CREATE TABLE FIXTURE_ONLY ...`) that does not come from the findings.

## Open points for the owner (after D-01)

1. Where the check runs. If it runs only in a local environment with the findings present, CI would skip it. If it must run in CI, the findings would need to be published as a controlled input, which conflicts with the no-import intent. The owner decides.
2. Whether the 16-character floor is right. A lower floor catches more and risks false positives in ordinary code.
3. Whether to add the near-match detector as a separate work package.

## Depends on

- **D-01 / ADR-005**: the rule is anchored to the licence decision. Not adopted before D-01.
- The findings assets staying gitignored in the `Unit` checkout.

## Recommendation

**Recommendation: adopt the exact-match check as a required test once D-01 is answered, with the real scan run in the owner's local gate.** It is cheap and deterministic, and it catches direct copying. It is not proof of no-copying. Near-match detection needs its own decision.
