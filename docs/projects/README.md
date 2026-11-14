# GitHub Projects workflow — “ECTT — Delivery”

This repository keeps specifications and the work-package register
authoritative **in Git**; GitHub is used for execution status, ownership,
discussion and verification links. A dedicated private project —
**“ECTT — Delivery”** under the `suduli` account, linked to this public
repository — tracks every work package from [PLAN-001 §5.5]
(../../PLAN-001-specification-analysis-and-work-breakdown.md) as one issue per
package. The existing UDS project is untouched.

This document covers source ownership, the reconciliation workflow, the
importer (`tools/github_projects.py`), the sync workflow
(`.github/workflows/project-sync.yml`), credential setup and renewal,
recovery, and how to disable everything without losing data.

## 1. Source ownership

| Artifact | Owner | Authoritative place |
|---|---|---|
| Capability, component, phase, effort, requirement allocation, dependencies, ADR-sensitivity | The register | PLAN-001 §5.5 (edit there, then run `plan_check.py --write` + `plan_check.py`) |
| Exit criteria | PLAN-001 §5.4 | Plan document |
| Requirement text and attributes | SRS-001 | SRS document |
| Issue title | The register (`[WP-ID] Capability`) | Rewritten only when the package changes |
| Generated issue sections | The importer | Between `<!-- ectt:generated:start -->` and `<!-- ectt:generated:end -->` markers |
| Status, assignees, comments, issue state, human notes | **Humans** | Never written by the importer |
| `Depends on`, `Component`, `Phase`, `Effort`, `Work Package` project fields | The importer | Source-owned metadata, rewritten on change |

Rules the importer enforces mechanically:

- Packages are parsed **only** from PLAN-001 §5.5 (spikes included); all
  totals are derived, never hard-coded.
- Managed issues are identified by a hidden `ectt-work-package:WP-ID` marker
  in the body, discovered across **all issue states with pagination**.
- Only the generated block and source-owned field values are updated. The
  section below the generated block is human territory and survives every run.
- New items initialize in **Needs reconciliation**. Historical completion
  claims (the validation spikes, recorded complete in PLAN-001 §4.4) render as
  unverified references, never as evidence.
- Packages removed from the register are **reported, never closed or deleted**.
- Duplicate markers, title-matches without markers, or marker-carrying bodies
  without the generated block **stop the run** as conflicts.
- Dependency annotations are preserved verbatim: `code` (build-order),
  `~` schedule-only, `^` port-mediated. The importer never reinterprets
  schedule-only or port-mediated edges as blocking dependencies, and never
  sets GitHub's blocked-by relations from them.
- Normalized package content is hashed (`ectt-content-hash`): the hash covers
  only what the register owns, so a revision bump or an unrelated commit
  rewrites nothing, and unchanged reruns make **zero writes**.
- `T-*` review tasks are not imported — they remain reference material in
  `docs/reviews/` and `vcast-findings/`, avoiding duplicate tracking.

## 2. Project shape

Fields: `Status` (Needs reconciliation → Backlog → Ready → In Progress →
Review → Verification → Done), `Work Package` (text), `Component`
(single-select of the register's `CMP-*` values plus *Validation spikes*),
`Phase` (P0–P4), `Effort` (number, person-weeks — a planning estimate, never a
deadline), `Depends on` (text, register annotations preserved), and GitHub's
built-in Assignees (human-only).

Views: **Reconciliation** (table, filter `Status:"Needs reconciliation"`),
**Delivery** (board, excluding unreconciled items), **Subsystems** (table),
**Phase planning** (table, effort and dependencies). The Projects API can
create views with layout and filter, but **grouping is not settable via the
API** — after bootstrap, set grouping once in the UI (bootstrap prints the
exact manual steps for each view).

Working conventions:

- `blocked` label + a comment explaining the blocker.
- Moving to **Ready** requires resolved prerequisites and written acceptance
  criteria (packages without a §5.4 exit criterion are flagged on their issue).
- **Done** requires reviewed acceptance evidence recorded on the issue.
- PR descriptions use **`Refs #issue`** — merging alone must not close a work
  package. The PR template enforces linked work, affected requirements,
  validation results and verification evidence.

## 3. Importer — `tools/github_projects.py`

Three commands, all safe to re-run:

```sh
# 1. Preview or create the project, fields, views and the blocked label.
python tools/github_projects.py bootstrap                     # preview (no writes)
python tools/github_projects.py bootstrap --apply             # create what is missing

# 2. Emit a JSON change preview (no mutations).
python tools/github_projects.py plan --output preview.json \
       --project-number <n>

# 3. Apply a preview after re-checking source and remote state.
python tools/github_projects.py apply --preview preview.json \
       --project-number <n> --summary-file summary.md
```

Authentication uses the GitHub CLI (`gh`) the tool shells out to; no token is
read or stored by the tool itself. Repository/owner resolve from the checkout
(`origin` remote), `--repo owner/name`, or `GITHUB_REPOSITORY` in Actions.

Behaviour worth knowing:

- `plan` and `apply` refuse to run when the source gates fail
  (`design/trace/plan_check.py`, and `trace_check.py` when the design tree is
  present) — a broken register never produces writes.
- `apply --preview` verifies the source revision **and** a digest of the
  source-owned GitHub state; anything stale is rejected with exit code 2.
  Apply without `--preview` plans internally, which is equivalent.
- `--wp WP-…` (repeatable) restricts a run to a subset — this is how the
  three-package smoke test is performed during rollout.
- Exit codes: `0` success · `1` validation/parse/conflict error · `2` stale
  preview · `3` credentials or API failure. All failures print an actionable
  message.
- Interrupted runs recover by rediscovery: every rerun re-derives the state
  from markers before creating anything, so a crash mid-import leaves the next
  run to adopt the created issues instead of duplicating them.

## 4. Rollout runbook

In order (the delivery plan's §4 sequence):

1. **Baseline first.** Keep `ECTT_PROJECTS_SYNC_ENABLED` unset/false until the
   separately reviewed 191-package baseline has landed on `main`. The workflow
   skips push-sync while the flag is off — that is its default state.
2. **Bootstrap** the dedicated project:
   `python tools/github_projects.py bootstrap --apply`, then set the manual
   view grouping the API cannot set (printed by the command).
3. **Configure repository variables and secret** (see §5).
4. **Preview everything**: run the sync workflow with `mode: preview` (or
   `plan` locally) and read the counts.
5. **Smoke test**: `apply --wp WP-SPIKE-01 --wp WP-PRJ-01 --wp WP-ANA-01` — a
   spike, a documented completed package, a planned package. Verify links,
   field values, reconciliation status and that a second run changes nothing.
6. **Import the remainder** (full `apply`), confirm the board holds all
   packages, then set `ECTT_PROJECTS_SYNC_ENABLED=true` to enable automatic
   synchronization.
7. **Reconcile** foundation and near-term delivery packages first; keep
   active implementation limited to three items.

## 5. Credentials

The workflow runs under a dedicated **`ECTT_PROJECTS_TOKEN`** Actions secret.
User-owned project automation needs a credential beyond ordinary repository
automation permissions — the default `GITHUB_TOKEN` cannot manage user
projects.

- Create a classic PAT for the `suduli` account with the **`project`** scope
  (user project management) plus **`repo`** (public repository issue writes);
  a fine-grained PAT can be used instead with *Projects (user)* read/write and
  *Issues* read/write on this repository.
- Store it as the repository secret `ECTT_PROJECTS_TOKEN`. It is exposed only
  to the `sync` job of `project-sync.yml` — never to `pull_request` runs, and
  it must **not** be a copy of a local `gh` CLI credential.
- Two repository variables complete the setup:
  `gh variable set ECTT_PROJECT_NUMBER --body <n>` and
  `gh variable set ECTT_PROJECTS_SYNC_ENABLED --body false`.

**Renewal:** create the replacement token, update the secret (Actions →
Secrets → update `ECTT_PROJECTS_TOKEN`), run a `preview` dispatch to confirm
credentials work, then delete the old token at the provider. No workflow or
importer change is needed; runs pick up the new secret immediately. If a run
fails with an auth error it fails visibly (exit code 3) with the remedy in the
message — nothing is silently skipped.

## 6. Synchronization behaviour

`.github/workflows/project-sync.yml` triggers on changes to the importer, its
tests, the templates, the workflow itself, the plan, the SRS or `docs/projects/`:

- **Pull requests and branch pushes:** the importer test suite runs offline.
  No credentials, no external writes.
- **Push to `main`** (flag on): `plan` → apply with the fresh preview. The
  preview and job summary are retained as artifacts; the summary reports
  created / updated / unchanged / conflicting / retired-source counts.
- **Dispatch:** preview (default) or apply; apply is refused when the flag is
  off, preview is always safe.
- All sync runs share a concurrency group and never run in parallel; an in-
  progress run is not cancelled, so apply serialization is guaranteed.

## 7. Recovery and maintenance

- **Interrupted apply:** rerun `plan` + `apply`. Created issues are rediscovered
  by marker; item-adds and field writes complete; nothing duplicates.
- **Stale preview (exit 2):** source-owned state changed between plan and
  apply. Regenerate the preview; there is no partial application to clean up
  (stale previews are rejected before the first write).
- **Human edits:** statuses, assignees, comments and the human tail of an
  issue body are never touched. A reconciled status stays exactly where the
  team moved it, including across register changes.
- **Retired packages:** if a work package leaves the register, its issue is
  reported in the preview/summary and left open. Reconcile by hand (reopen
  scope, or explain why the issue stays).
- **Conflicts (exit 1):** duplicate markers or a rebuilt body. Fix the
  offending issue manually, then rerun; the run stops before any write.
- **Disabling synchronization:** set `ECTT_PROJECTS_SYNC_ENABLED=false` (or
  delete the variable). Push syncs stop; imported issues and all human
  activity remain. Manual preview/apply via dispatch stays available to
  operators. Rollback never deletes or closes anything.
- **Worst-case rollback:** disable the flag, stop dispatches, and work from
  the issues as plain GitHub issues. The register in Git remains the single
  source of truth; no board edit is ever written back into specifications.

## 8. Test coverage

`tests/projects/` runs offline against an in-memory GitHub double:

- the current source yields exactly **191** unique package records with the
  register-audit totals (336 allocations; 275/2/10 dependency edges);
- malformed rows, duplicate ids, unknown dependencies, unknown requirements,
  rollup mismatches, cycles and duplicate SRS lines stop the import;
- pagination finds open **and** closed issues beyond one page;
- repeated application produces zero writes; human notes, statuses and titles
  survive synchronization; retired packages are reported without destructive
  changes; interrupted creation resumes without duplicates;
- missing credentials, API failures, gate failures and stale previews produce
  actionable, correctly-coded errors;
- bootstrap is preview-first and idempotent, and Status-option updates
  preserve option ids so existing items keep their values.
