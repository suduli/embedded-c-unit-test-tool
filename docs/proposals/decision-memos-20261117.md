# Decision memos D-01 to D-04 (draft, 2026-11-17)

**Status: DRAFT. Not adopted.** These memos prepare four owner decisions. They change no decision state. ADR files, `LICENSE`, `LICENSEES`, `SRS-001-requirements.md`, `design/SDD-003-data-model.md` and the decision register are unchanged. Every diff below is **unapplied**. Each applies only after the owner answers and the change process runs.

Recommendations are labelled **Recommendation** and are advice only. The owner decides.

Sources read for this memo: `EXEC-PLAN-001-unified-execution-plan.md` §6.1 (decision register), `docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md` (decision queue and the T-04 memo), `SRS-001-requirements.md` (lines 738–790), `LICENSE`, `LICENSEES`, `README.md` (license lines), `docs/reviews/2026-10-15-document-review.md` (DR-06, lines 72–78).

---

## D-01 · Licence posture (T-01, NR-01, ADR-005, P0)

**Question.** Which licence does the project ship under? The repository is public and states AGPL-3.0. SRS `TOOL-LIC-010` requires a permissive licence. One of the two must move.

### Comparison against TOOL-LIC-010 as written

`TOOL-LIC-010` (SRS-001 line 780): *"The tool's own source code shall be released under a permissive open-source license."*

| Option | Meets TOOL-LIC-010 as written? | Why |
|---|---|---|
| AGPL-3.0 (keep) | **No** | AGPL-3.0 is a strong-copyleft licence, not a permissive one. The requirement must be amended to match the code. |
| Apache-2.0 | **Yes** | Permissive, with an explicit patent grant. No requirement change. |
| MIT | **Yes** | Permissive and the simplest option. Has no express patent grant. |
| Proprietary / closed | **No** | Not open source, so it fails the "open-source" wording. The requirement must be removed or rewritten. |

Only the two permissive options satisfy the requirement without editing it.

### Options and files that would change

**a) Keep AGPL-3.0.** The code stays as it is. The requirement is amended to match.

Files: `SRS-001-requirements.md` (line 780), the `ADR-005` record (its file is not present at the worktree root; location not verified), the review note that records F-16 in `PLAN-001-specification-analysis-and-work-breakdown.md`.

```diff
--- a/SRS-001-requirements.md
+++ b/SRS-001-requirements.md
@@ TOOL-LIC-010 @@
-**TOOL-LIC-010** *(M, P1, I)* — The tool's own source code shall be released under a permissive open-source license.
+**TOOL-LIC-010** *(M, P1, I)* — The tool's own source code shall be released under the GNU Affero General Public License v3.0 (AGPL-3.0).
```

Trade-off: relicense churn is avoided, but the SRS changes to accept strong copyleft. Downstream rules (TOOL-LIC-020, process isolation for strong-copyleft components) still apply to dependencies. Check every `src/` file for AGPL headers before any change.

**b) Apache-2.0.** The code changes licence. The requirement stays as written.

Files: `LICENSE` (replace with the Apache License 2.0 text from `https://www.apache.org/licenses/LICENSE-2.0.txt`), `LICENSEES` (lines 3–18), `README.md` (line 8 badge, lines 129–134 licence section), optionally a `NOTICE` file.

```diff
--- a/README.md
+++ b/README.md
@@ line 8 @@
-[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
+[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
```

```diff
--- a/LICENSEES
+++ b/LICENSEES
@@ line 3 @@
-This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
+This project is licensed under the Apache License, Version 2.0.
```

The plain-language summary in `LICENSEES` (lines 5–18) must be rewritten for Apache-2.0 at the same time. The text is not drafted here.

**c) MIT.** Same file set as (b). `LICENSE` is replaced with the MIT text. The badge becomes `License: MIT`. The licence has no express patent grant.

**d) Proprietary / closed.** The repository goes private and the AGPL is dropped. `TOOL-LIC-010` is removed or rewritten. The repository's public status is changed by the owner outside the repo. Licence terms are owner-authored and are not drafted here.

### Risks
- **Already-published copies.** Versions already distributed under AGPL-3.0 stay under AGPL-3.0 for the people who received them. Any relicence applies going forward. **Confirm with counsel** before the change.
- **Copyright ownership.** A relicence needs rights from every copyright holder. The queue says the project is sole-authored. This was not verified against git authorship.
- **Dependency compatibility.** `TOOL-LIC-030` (SBOM) and `TOOL-LIC-060` (automatic licence check) must confirm that the chosen licence can ship with each dependency. Not checked here.

### What unblocks
- **T-01:** record ADR-005, update `LICENSE` and `LIC-010`, and re-run the gates.
- **T-02 (TASK-015):** the no-import rule has ADR-005 as its anchor.
- **WP-PKG-07 and WP-PKG-08:** LIC-010 to LIC-060 policy and separable components.
- **Gating:** publicising the repository and soliciting contributors.

### Recommendation
**Recommendation: Apache-2.0 (option b).** It satisfies `TOOL-LIC-010` as written, so no requirement changes. It adds an explicit patent grant. It keeps the change to repository files. Option (a) is the only one that edits the SRS, and that edit weakens a stated requirement. The choice between copyleft and permissive is the owner's.

---

## D-02 · Identity model (T-04, NR-04, P0)

**Question.** Stable ids plus content digests, or revision entities? The T-04 memo recommends stable ids plus digests. That is a recommendation, not a decision.

### Context
`SDD-003` §6 (Identity and references, `design/SDD-003-data-model.md` line 251) and §7 (Digest-bound records, line 274) hold the current model. The T-04 memo (`docs/reviews/2026-11-07-subsystem-requirements-and-tasks.md`, "T-04 decision memo") says the proposal's `TestRevision` and `EnvironmentRevision` model is incompatible with the accepted stable-id and digest staleness model (RV-05 F-05). It argues a digest in the result record reconciles the two.

### Options and files that would change

**a) Stable ids plus digests (memo recommendation).**

Files: `design/SDD-003-data-model.md` §6/§7, one sentence in SDD-002 S2/S3 (SDD-002 location not verified in the worktree).

```diff
--- a/design/SDD-003-data-model.md
+++ b/design/SDD-003-data-model.md
@@ ## 6. Identity and references @@
 ## 6. Identity and references
+
+> **Amendment (on owner approval of D-02, option a).** Test and result identities are stable ids bound to content digests (§7). Separate revision entities are not adopted. Digest binding is the staleness mechanism.
```

WP-TCM-02 then implements digest binding, and T-14 becomes startable.

**b) Revision entities.** The proposal's `TestRevision` and `EnvironmentRevision` are adopted. This needs a new SDD-003 section and schema churn. It conflicts with RV-05 F-05. A full patch needs its own draft, so none is given here.

**c) Defer.** No document changes. T-04 and T-14 stay blocked. Record the deferral date in the decision queue. Revisit after T-17 to T-22, which have landed.

### Risks
- Option (a) leaves the digest binding to WP-TCM-02, so the staleness guarantee is only as good as that work.
- Option (b) adds revision bookkeeping that the digest model was chosen to avoid.
- Option (c) keeps T-14 (run-integrity acceptance for WP-EXH-01/02 and WP-CBT-01) blocked, and the P1 gap in NR-17 to NR-19 stays open.

### What unblocks
- **T-04**, then **T-14**, then the run-integrity acceptance for WP-EXH-01/02 and WP-CBT-01.
- **WP-TCM-02** digest binding (watch item).

### Recommendation
**Recommendation: option (a).** The T-04 memo's reasoning holds on the evidence read: digest binding gives the executable-to-content check, and it avoids a second identity registry.

---

## D-03 · Platform order (T-05, NR-05, P1)

**Question.** Windows pilot first, Linux first, or both in parallel (`TOOL-NFR-010` and `TOOL-NFR-020`)?

### What the SRS says today
- `TOOL-NFR-010` (SRS-001 line 738): *"The tool shall run on Linux x86-64."* Tagged **M, P1**.
- `TOOL-NFR-020` (SRS-001 line 740): *"The tool shall run on Windows and macOS."* Tagged **S, P2**.

So the SRS already ranks Linux above Windows. Option (a) reverses that ranking, so it needs SRS priority edits. Option (b) matches the current text. Option (c) needs a priority change on `TOOL-NFR-020`.

Facts that bear on the choice:
- The `WP-SPIKE-03` PyInstaller spike onto clean Windows is complete (review queue).
- `.github/workflows/tests.yml` already has counterparts for both `TOOL-NFR-010` (Linux) and `TOOL-NFR-020` (Windows), so both platforms have CI today.
- SRS line 945 lists the implementation language as unspecified, and that question affects `TOOL-NFR-020`.

### Options and files that would change

**a) Windows pilot first.**

```diff
--- a/SRS-001-requirements.md
+++ b/SRS-001-requirements.md
@@ TOOL-NFR-010 / TOOL-NFR-020 @@
-**TOOL-NFR-010** *(M, P1, T)* — The tool shall run on Linux x86-64.
+**TOOL-NFR-010** *(M, P2, T)* — The tool shall run on Linux x86-64.
-**TOOL-NFR-020** *(S, P2, T)* — The tool shall run on Windows and macOS.
+**TOOL-NFR-020** *(M, P1, T)* — The tool shall run on Windows and macOS.
```

Keep the Linux CI job green as a compatibility check.

**b) Linux first.** No SRS change, since the text already matches. Record the decision and set the `WP-CORE-03` platform baseline to Linux.

**c) Both in parallel.**

```diff
--- a/SRS-001-requirements.md
+++ b/SRS-001-requirements.md
@@ TOOL-NFR-020 @@
-**TOOL-NFR-020** *(S, P2, T)* — The tool shall run on Windows and macOS.
+**TOOL-NFR-020** *(M, P1, T)* — The tool shall run on Windows and macOS.
```

### Risks
- **(a)** A priority reversal is a requirement change. It needs the change process, not just a note.
- **(b)** Windows users stay second-class for longer. The owner's development machine is Windows.
- **(c)** Highest setup and test-matrix cost. macOS coverage is named in `TOOL-NFR-020` but has no CI counterpart in the repository as read.

### What unblocks
- **T-05**, then **TASK-007 / WP-CORE-03** (platform baseline and offline guarantee, currently Blocked), and **WP-GUI-01** platform-support planning.
- The NFR-010 and NFR-020 wording note.

### Recommendation
**Recommendation: option (a), with the Linux CI job kept green.** It matches the platform the team develops on, and the Windows spike is already done. It needs the priority edits above, which are the owner's to approve.

---

## D-04 · DR-06 NFR calibration (T-06, NR-06, P2)

**Question.** How should DR-06 calibration be handled before pilot data exists?

### The defect
DR-06 (`docs/reviews/2026-10-15-document-review.md`, lines 72–78) says the 30-second target in `TOOL-NFR-030` uses undefined "typical developer hardware". The memory and own-source coverage limits (`TOOL-NFR-150` and the adjacent NFR-140) only require a documented threshold, without choosing one. Teams can pick incompatible acceptance conditions after implementation.

Current wording (SRS-001):
- `TOOL-NFR-030` (line 742): *"…shall complete in under 30 seconds on typical developer hardware."*
- `TOOL-NFR-040` (line 744): *"…shall complete in under 10 seconds on host."*
- `TOOL-NFR-150` (line 766): *"…shall operate within a documented memory ceiling…"*

### Options and files that would change

**a) Defer to post-pilot.** Mark the provisional NFRs as provisional. Calibrate from measured baselines before WP-CORE-05 exits P2, as NR-06 already requires.

```diff
--- a/SRS-001-requirements.md
+++ b/SRS-001-requirements.md
@@ TOOL-NFR-030 @@
-**TOOL-NFR-030** *(M, P2, D)* — Environment creation for a single translation unit of 1000 lines shall complete in under 30 seconds on typical developer hardware.
+**TOOL-NFR-030** *(M, P2, D)* — [PROVISIONAL, calibrate before WP-CORE-05 exits P2] Environment creation for a single translation unit of 1000 lines shall complete in under 30 seconds on typical developer hardware.
```

Apply the same marker to `TOOL-NFR-040` and `TOOL-NFR-150`. The exact marker wording is the owner's to approve.

**b) Calibrate now.** Set targets from current analysis runs. Name the reference hardware, workload and measurement method. The review's correction list in DR-06 gives the required fields. Numbers cannot be proposed honestly here, because no measured baseline is in the repository. This option needs data first.

**c) Drop DR-06.** Remove the requirement if it is no longer meaningful. This needs the owner to confirm the three NFRs are not needed.

### Risks
- **(a)** Provisional targets can still be treated as fixed. The marker must be checked at P2 exit.
- **(b)** Numbers chosen without a pilot may be wrong in both directions.
- **(c)** Removes the only defined ceiling for `TOOL-NFR-150` and the timing target in `TOOL-NFR-030`.

### What unblocks
- **T-06**, and the WP-CORE-05 NFR thresholds (NFR-030, NFR-040, NFR-050, NFR-150) at P2 entry.

### Recommendation
**Recommendation: option (a).** It is the only option that matches the review's own model (uncalibrated targets labelled as such), and it needs no invented numbers. Calibrate at P2 entry as NR-06 already requires.

---

## Summary of what each answer unlocks

| Decision | Answer unlocks | Requirement or ADR edits the answer needs |
|---|---|---|
| D-01 | T-01, T-02, WP-PKG-07, WP-PKG-08 | (a) edits `TOOL-LIC-010`. (b) and (c) edit the repository licence files only. (d) removes `TOOL-LIC-010`. |
| D-02 | T-04, T-14, WP-TCM-02 digest binding | SDD-003 §6/§7 amendment and one sentence in SDD-002 |
| D-03 | T-05, TASK-007 / WP-CORE-03, WP-GUI-01 planning | (a) and (c) edit `TOOL-NFR-010/020` priorities |
| D-04 | T-06, WP-CORE-05 thresholds | (a) adds provisional markers to NFR-030/040/150. (c) removes DR-06 NFRs. |

## Not checked in this memo
- The ADR-005 file location and the SDD-002 location were not found in the worktree.
- Source-file licence headers and git authorship were not checked (D-01 risks).
- The NFR-030/040/150 and DR-06 wording was read directly. The WP-CORE-05 line in `PLAN-001` (line 320) was taken from the RV-06 evidence note, not reopened.
