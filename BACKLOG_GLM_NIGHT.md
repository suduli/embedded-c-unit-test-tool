# BACKLOG_GLM_NIGHT — unattended overnight backlog for the GLM agent

Generated 2026-11-17. Budget: ~3,000,000 tokens. Core queue ≈ 2.9M; reserve queue ≈ 1.1M (only start when core is done and budget remains).

Repos: **SIM** = `E:\projects\UDS_Simulator\UDS-SIMULATION` (site, docs-site, mcp-server). **UNIT** = `E:\projects\UDS_Simulator\Unit` (ECTT test tool).
Most tasks are SIM. Only TASK-024 touches UNIT (docs only).

---

## 1. Summary of areas covered

| Area | Tasks | Source of the work |
|---|---|---|
| Setup / baseline | 000 | needed for safe overnight run |
| SEO | 001–006 | `SEO/ACTION-PLAN.md` (P0-1, P0-3, P1-1, P1-3, P2-2, P2-3), `docs/seo/AI-VISIBILITY-PLAN.md` §1.1 |
| SID test cases / test health | 007–009 | `tests/test-data/sid-*/…report.json`, `scripts/orchestrate-sid-test-reviews.mjs`, `docs-site/__tests__/sid-schemas.test.ts`, GH #391 (failing scheduled regression) |
| docs-site update | 010–012 | GH #228–232 (SID 0x10 page), #112, #119 |
| UI redesign | 013–014 | `docs/admin-redesign/PLAN.md` (visual baselines unchecked), GH #150 |
| MCP | 015–016 | `openspec/changes/add-user-aware-uds-mcp` (24 open), `docs/mcp/*` |
| Post marketing | 017–019 | `daily-uds-linkedin-post/`, GH #310 #151 |
| New planning | 020–021 | GH #184 (public roadmap), UNIT `PLAN-001` status vs. commits |
| Other gaps | 022–024 | dependency audit, broken links, `SequenceEngine.ts` TODO |
| Final report | 025 | morning review pack |

Not planned (deliberately excluded, see §4): payments/RLS/migrations, deployments, social account creation, publishing anything, closing issues, MCP gated work packages WP17–WP20 / G6–G8 (they need owner gates and real credentials).

## 2. Token estimate

| Queue | Tasks | Est. tokens |
|---|---|---|
| Core | TASK-000 … TASK-025 | **2,900,000** (sum in the table in §5) |
| Reserve | TASK-101 … TASK-107 | 1,130,000 |
| Hard stop | — | stop starting new tasks at ~2.85M used; leave 150k for TASK-025 |

Estimates are rough (±40%). The agent must track its own running total in the log (see §3.6).

---

## 3. Agent instructions (READ FIRST, FOLLOW EXACTLY)

You are an unattended executor. No human will answer questions. When something is ambiguous, pick the most conservative reading, record the assumption in the log, and continue.

### 3.1 Branch and isolation (SIM has uncommitted human work — do not disturb it)

`E:\projects\UDS_Simulator\UDS-SIMULATION` currently has a dirty working tree on branch `chore/mcp-use-adoption-plan` (modified `mcp-server/src/http/start.ts`, `src/App.tsx`, `src/utils/redirect.ts`, a security test, `.claude/settings.local.json`). **Never edit, stash, reset, checkout over, or commit those.** Work in a separate worktree:

```bash
cd /e/projects/UDS_Simulator/UDS-SIMULATION
git fetch origin
git worktree add ../wt-glm-night -b glm-night/20261117 origin/main
cd ../wt-glm-night
npm ci && (cd docs-site && npm ci) && (cd mcp-server && npm ci)
```

All SIM work happens in `E:\projects\UDS_Simulator\wt-glm-night` on branch `glm-night/20261117`. If `origin/main` is not available, branch from local `main`. Never work on `main`.
For UNIT (TASK-024 only): `git -C /e/projects/UDS_Simulator/Unit worktree add ../wt-unit-glm-night -b glm-night/20261117 main`.

### 3.2 Commit workflow

- One commit per task (a small number of extra commits is fine for a large task). Stage only the files the task touches (`git add <paths>`, never `git add -A`).
- Commit message format, exactly:
  `[GLM-NIGHT] TASK-012: <imperative summary under 70 chars>`
  body: what changed, why, how verified (commands + result), and `Files:` list. End with `Co-Authored-By: GLM Agent <noreply@example.com>`.
- Marker for non-task commits: `[GLM-NIGHT] LOG: …`. Morning filter: `git log --grep='\[GLM-NIGHT\]' --oneline`.
- Only commit when the task's acceptance criteria pass and its verification commands are green (or the failure is pre-existing — see 3.4). Never commit with failing tests that you introduced.
- Never: `git push --force`, `git reset --hard` on shared refs, `git rebase` of pushed work, `--no-verify`, amending previous task commits.
- Push the branch to origin at the end of each phase with plain `git push -u origin glm-night/20261117` (never to `main`, never force). If push fails, continue and note it.

### 3.3 Safety rules (hard)

1. Do NOT deploy, run `vercel`, change Vercel/Cloudflare/Supabase/Razorpay/PostHog/Resend settings, or touch production URLs except read-only `GET`s (e.g. `curl` of public pages).
2. Do NOT apply migrations or run SQL against any database. Writing a migration *file* is out of scope for this backlog.
3. Do NOT read, print, or commit secrets (`.env*`, keys, tokens). Do not paste credentials into logs.
4. Do NOT send emails, post to social networks, create accounts, open/close/comment on GitHub issues or PRs, or merge anything.
5. Do NOT delete files except ones the task explicitly names, and never delete tests to make them pass. Never weaken an assertion or coverage threshold to get green.
6. Do NOT touch payment, billing, RLS, auth, or `openspec/changes/harden-*` code.
7. Do NOT upgrade major dependency versions. TASK-022 is report-only.
8. No file in the repo may contain placeholder testimonials, fake logos, or invented metrics.
9. If a command would run longer than 15 minutes or needs interactive input, kill it and mark the task BLOCKED.

### 3.4 Failure handling — never stop the run

For each task: do the work → run the verification commands → commit. If it cannot be completed:
- Spend at most **1.5× the task's token estimate**. At that point stop work on it.
- `git stash` nothing; instead discard only your own uncommitted changes for that task (`git restore` the paths you edited) so the next task starts clean.
- Set the task's status to `BLOCKED` or `FAILED` in the log with a one-paragraph reason (command, error excerpt, what you tried).
- Move on to the next task whose dependencies are not blocked. A task depending on a BLOCKED task becomes `SKIPPED (dep)`.
- Pre-existing failures: before TASK-001, TASK-000 records a baseline. A test that fails in the baseline and still fails the same way is not your regression; note it and do not fix it unless the task says so.

### 3.5 Verification defaults

- SIM root: `npx tsc -b`, `npx eslint <touched files>`, `npx vitest run <touched test paths>`.
- docs-site: `cd docs-site && npx eslint <files> && npx vitest run && node --test __tests__/docs-baseline.test.mjs`. Run `npm run build` (in docs-site) only when a task says so; it is slow.
- mcp-server: `cd mcp-server && npm run build && npm run test:<suite>` for the touched area.
- Run the narrowest check first, the full suite once at the end of each phase.

### 3.6 Logging (the morning review reads this)

Maintain `docs/glm-night/GLM_NIGHT_LOG.md` in the worktree (create in TASK-000). After every task append one row and commit it together with the task:

`| TASK-id | DONE/PARTIAL/BLOCKED/FAILED/SKIPPED | commit sha | tokens used (est.) | cumulative | notes / assumptions / follow-ups |`

Also keep a section "Decisions & assumptions" and a section "Ideas not done". When cumulative tokens ≥ 2.85M, jump to TASK-025.

### 3.7 Order of execution

Run Core in numeric order (dependencies are already respected). After TASK-025 is committed, if budget remains, run Reserve tasks in order, committing a refreshed TASK-025 report afterwards (`[GLM-NIGHT] TASK-025: refresh report`).

---

## 4. Do-not-touch list (noted from discovery)

- `openspec/changes/harden-payment-replay-atomicity` (15 open) and `harden-database-rls-performance` (4 open): payments/RLS.
- `openspec/changes/2026-01-09-add-sandbox-execution` (127 open): large, needs design decisions; only R-reserve may do a read-only triage.
- GH #291–306 "Review Branch" issues and #357–363 MCP gates: owner review/credential gated.
- GH #310–313 social account/automation: accounts cannot be created unattended (TASK-018 only writes a design doc).
- PostHog/GA/Clarity dashboards, live site, Supabase production.
- The dirty files listed in §3.1.

---

## 5. Core queue

Size key: S ≤ 80k, M 80–150k, L 150–250k.

| ID | Title | Area | Est. tokens | Depends |
|---|---|---|---|---|
| TASK-000 | Worktree, baseline, log file | setup | 30k | — |
| TASK-001 | Fix 7 sitemap URLs serving the homepage shell | SEO | 120k | 000 |
| TASK-002 | Rewrite titles/meta where pages already rank | SEO | 100k | 000 |
| TASK-003 | Build NRC reference page in docs-site | SEO | 150k | 000 |
| TASK-004 | Image alt text + LCP-friendly loading | SEO | 60k | 000 |
| TASK-005 | Fix inverted internal linking + truthful `lastmod` | SEO | 80k | 001 |
| TASK-006 | Question-phrased headings pilot (SID 0x27, 0x10) | SEO | 120k | 000 |
| TASK-007 | SID test-data integrity audit (all 19 SIDs) | SID tests | 100k | 000 |
| TASK-008 | Vitest schema tests for all 19 SID reports | SID tests | 150k | 007 |
| TASK-009 | Diagnose scheduled-regression failure (GH #391) | SID tests | 180k | 000 |
| TASK-010 | SID 0x10 docs page cleanup (GH #228–232) | docs-site | 220k | 000 |
| TASK-011 | Docs frontmatter/metadata contract check (GH #112) | docs-site | 100k | 000 |
| TASK-012 | Docs shell static a11y fixes (GH #119) | docs-site | 100k | 010 |
| TASK-013 | Admin redesign visual baselines 375/768/1440 | UI redesign | 120k | 000 |
| TASK-014 | ECU response packet UI + timing panel (GH #150) | UI redesign | 250k | 000 |
| TASK-015 | `add-user-aware-uds-mcp`: implement code-only open tasks | MCP | 250k | 000 |
| TASK-016 | MCP docs consistency pass (guide, clients, status) | MCP | 80k | 015 |
| TASK-017 | Draft 14 days of LinkedIn posts (drafts only) | marketing | 150k | 000 |
| TASK-018 | Social post automation design doc (GH #310/#311) | marketing | 70k | — |
| TASK-019 | Pre-launch verification matrix doc + script (GH #151) | marketing | 80k | 000 |
| TASK-020 | Public ROADMAP.md draft (GH #184) | planning | 80k | 000 |
| TASK-021 | Next-quarter feature plan from open issues | planning | 70k | 020 |
| TASK-022 | Dependency audit report (report only) | gaps | 50k | 000 |
| TASK-023 | Broken-link and dead-reference check across docs | gaps | 70k | 000 |
| TASK-024 | UNIT: PLAN-001 progress vs. commits report | gaps/planning | 120k | — |
| TASK-025 | Morning review pack | review | 150k | all |

Sum ≈ 2.9M (TASK-025 reserved last).

### TASK-000 — Worktree, baseline, log
- Do: §3.1 setup. Run `npx tsc -b`, `npx vitest run` (root), `cd docs-site && npx vitest run`, `cd mcp-server && npm test` (skip suites needing DB/network; note them). Save results to `docs/glm-night/baseline.md` (pass/fail counts, failing test names, durations). Create `docs/glm-night/GLM_NIGHT_LOG.md` with the table header and the two extra sections.
- Files: `docs/glm-night/*`.
- Done when: both files exist, baseline lists every failing suite by name, commit `[GLM-NIGHT] TASK-000: …` exists.

### TASK-001 — Seven sitemap URLs serve the homepage shell
- Source: `SEO/ACTION-PLAN.md` P0-1. Routes: `/flashing /cluster /report /donate /refund-policy /acceptable-use /security-policy`.
- Do: add `ROUTES` entries (title, desc, h1, lede, ~500+ chars real prose, sections) in `scripts/inject-metadata.cjs` for the 4 trust pages (`/donate`, `/refund-policy`, `/acceptable-use`, `/security-policy`) using wording consistent with the existing legal pages in `src/` (do not invent legal terms; summarize what the existing pages say). For `/flashing /cluster /report` add an above-the-fold explainer entry the same way. Mirror all seven in `scripts/prerender.cjs`. Do not touch `vercel.json` or `public/sitemap.xml` unless an entry has no honest content.
- Verify: `node scripts/inject-metadata.cjs` passes the 500-char gate; each `dist/<route>/index.html` has a unique `<title>` and a self-canonical; `node scripts/validate-schema.cjs`.
- Done when: after a local `npm run build` + inject, 0 of the 7 pages have canonical `https://udssimulator.com/` and 8 distinct titles exist across them and home. Record evidence in the commit body.

### TASK-002 — Rewrite snippets where ranking already exists
- Source: ACTION-PLAN P0-3 (read the section for the exact page list and measured queries).
- Do: edit the titles/descriptions in `src/components/layout/SEO.tsx` and `scripts/inject-metadata.cjs` for the pages listed; titles ≤ 60 chars, descriptions 140–160 chars, lead with the query term, no keyword stuffing, no unverifiable claims.
- Verify: a small node script (add `scripts/check-seo-lengths.cjs`) that asserts the length limits for all routes; run it and `npx tsc -b`.
- Done when: script passes and is referenced in the commit; no two routes share a title.

### TASK-003 — NRC reference page (docs-site)
- Source: ACTION-PLAN P1-1. Build `docs-site/app/docs/nrc-reference/page.mdx` (follow an existing `sid_0x*` page for layout components), with a table of every ISO 14229-1 NRC (code, name, meaning, typical services) drawn from existing repo content (`docs-site/data/`, `docs-site/learning/*`, the `sid_0x*` pages, `src/` NRC constants). Do not invent codes; if a value is not in the repo, mark it "see ISO 14229-1" rather than guessing.
- Also: add to `_meta`/sidebar, add `TechArticle` metadata like sibling pages, link it from each `sid_0x*` page's NRC section (append a single link line only).
- Verify: `cd docs-site && npm run build:md && npx vitest run && node --test __tests__/docs-baseline.test.mjs`.
- Done when: page renders in `next build` (run once), appears in `lib/doc-meta.json`, passes baseline test.

### TASK-004 — Image alt text and LCP-friendly loading
- Source: ACTION-PLAN P1-3. Do: add meaningful `alt`, `width/height`, `loading="lazy"` (not on the LCP image; that one gets `fetchpriority="high"`) across `src/` and `docs-site/` image usages named in the plan. Decorative images get `alt=""`.
- Verify: eslint on touched files; `grep` shows no `<img` without `alt` in touched dirs; `npx tsc -b`.
- Done when: before/after count of `<img>` without alt is in the commit body and is 0 for touched dirs.

### TASK-005 — Internal linking and truthful lastmod
- Source: ACTION-PLAN P2-2, P2-3. Do: fix link direction as described in the plan; make `public/sitemap.xml` generation use real git dates per URL (extend an existing script or add `scripts/generate-sitemap-lastmod.cjs`; do not hand-edit dates).
- Verify: `node scripts/verify-sitemap-status.cjs --sitemap public/sitemap.xml` offline mode if available, else a unit check; ensure the 7 routes from TASK-001 are still present or intentionally removed with reason.
- Done when: no `lastmod` is identical across all URLs; script is deterministic (two runs, same output).

### TASK-006 — Question-phrased headings pilot
- Source: `docs/seo/AI-VISIBILITY-PLAN.md` §1.1: "Do one page (0x27) first." Do 0x27 and 0x10 only. Convert 2–4 `<DocSection title>` values per page to the question forms in the plan; keep short TOC labels (check `_meta` does not inherit long titles).
- Verify: `npm run build:md` regenerates `.md` mirrors; docs-site vitest + baseline test.
- Done when: pilot pages only; remaining 17 pages queued as R-103.

### TASK-007 — SID test-data integrity audit
- Source: `tests/test-data/sid-*/SID*_TestCases_report.json`; `scripts/orchestrate-sid-test-reviews.mjs` (use `--dry-run`, NO API calls, NO network).
- Do: run `node scripts/orchestrate-sid-test-reviews.mjs --dry-run`; write `docs/glm-night/sid-test-audit.md`: per SID — case count, pass/fail counts, duplicate IDs, cases lacking expected NRC/response, mismatches with the matching `docs-site/app/docs/sid_0x*` page. Do not edit test data in this task.
- Done when: all 19 SIDs have a row; findings are specific (file + case id).

### TASK-008 — Vitest schema tests for all 19 SID reports
- Depends on 007. Extend `docs-site/__tests__/sid-schemas.test.ts` (or add `sid-reports.test.ts`) so every SID report: parses, has unique case IDs, every case has id/name/request/expected, and counts in the summary equal the actual counts. Known-bad data found in TASK-007 → mark with `it.todo` plus an entry in the log, not a weakened assertion.
- Verify: `cd docs-site && npx vitest run`.
- Done when: ≥ 19 × 4 assertions run; suite green apart from documented `todo`s.

### TASK-009 — Diagnose scheduled regression failure (GH #391)
- Read the newest "Scheduled Full Regression Test Failed" issue body (read-only `gh issue view 391`, read-only). Reproduce locally with `npm run test:regression:quick` / `test:regression:sid` where possible (no network to prod).
- Do: write `docs/glm-night/regression-391-diagnosis.md` (root cause, evidence, affected tests, proposed fix). If the cause is a test/fixture bug in a file under `tests/` or `scripts/` (not product/payment code), fix it with minimal change and add a regression guard; otherwise stop at the diagnosis.
- Done when: a root-cause statement backed by log excerpts exists; any code fix has a failing-then-passing run recorded.

### TASK-010 — SID 0x10 docs page cleanup
- Source: GH #228 (remove decorative KPI cards), #229 (remove Meteors/BorderBeam/RetroGrid), #231 (remove marketing CTA in Session Transition Logic), #230 (sticky sidebar TOC for 11 sections), #232 (visual hierarchy). Page: `docs-site/app/docs/sid_0x10/page.mdx`.
- Do: apply in that order, one commit if small, else one per issue number (`TASK-010a…`). Respect `prefers-reduced-motion` for anything that remains. Reuse existing TOC component if one exists elsewhere in `docs-site/components`.
- Verify: docs-site lint, vitest, `npm run build:md`, `next build` once; take screenshots only if a headless browser is available (`npm run test:sid-ui:browser`), else skip.
- Done when: none of Meteors/BorderBeam/RetroGrid/KPI-card/CTA imports remain in the page; TOC links resolve to existing ids.

### TASK-011 — Docs frontmatter/metadata contract check (GH #112)
- Do: define the schema (title, description, sid, since, dateModified) in `docs-site/lib/doc-contract.ts`; add `docs-site/scripts/check-doc-contract.mjs` that validates every `sid_0x*` page; wire into `docs-baseline.test.mjs` as a new test. Fix trivially fixable violations (missing description text taken from the page's existing intro paragraph); list the rest in the log.
- Done when: the script runs in < 30s, new test passes, violations list is empty or logged.

### TASK-012 — Docs shell static a11y fixes (GH #119)
- Do: run `scripts/validate-accessibility.js` (existing) on built docs output if it supports a path, plus static checks: heading order, landmark roles, link names, focus-visible styles, `aria-label` on icon buttons, contrast of tokens in `docs-site/theme.config.jsx`/Tailwind config (compute ratios in a script; fix tokens only if the fix is ≥ AA and visually minimal).
- Done when: report `docs/glm-night/a11y-docs-shell.md` with before/after counts; no regression in vitest.

### TASK-013 — Admin redesign visual baselines
- Source: `docs/admin-redesign/PLAN.md` line 85 (unchecked "Visual baselines 375/768/1440 not added"). Use the existing admin test harness (`tests/admin/run-admin-suite.cjs`, `tests/theme/visual-diff.cjs`) to add baseline capture + diff for 375/768/1440. Run against a local dev server with mocked/fixture data only. If the harness needs live credentials, mark BLOCKED.
- Done when: baseline images committed under `tests/admin/baselines/`, a diff run against themselves reports 0 diff, PLAN.md checkbox ticked.

### TASK-014 — ECU response packet UI + timing panel (GH #150)
- Do: read the issue text (read-only) and the current response component(s) under `src/`; add a response packet breakdown (SID/NRC/data/payload bytes), a simulation log list and a timing panel (P2/P2* values from existing session timing constants — do not invent numbers). Keep it behind existing component structure; no new dependencies. Vitest + Testing Library tests for rendering, empty state, and NRC state. Dark/light via existing tokens, keyboard-focusable, aria-labelled.
- Verify: `npx tsc -b`, eslint, `npx vitest run <new tests>`, `npm run test:theme:visibility` if runnable offline.
- Done when: the three panels render for a positive and negative response in tests.

### TASK-015 — `add-user-aware-uds-mcp` code-only open tasks
- Source: `openspec/changes/add-user-aware-uds-mcp/tasks.md` (24 open / 55 done).
- Do: classify each open item as CODE-ONLY / NEEDS-OWNER (credentials, hosted env, real clients, DB gates). Implement CODE-ONLY items in `mcp-server/src` with tests; tick boxes in `tasks.md` only for items finished and verified. Write the classification table into the log. Do not edit `mcp-server/src/http/start.ts` in the main checkout (it is dirty there; in the worktree it is clean — fine, but re-read it first).
- Verify: `cd mcp-server && npm run build && npm run test:contracts test:runtime test:protocol test:docs` (the non-DB suites in `package.json`).
- Done when: every ticked box has a test or command referenced in its line; NEEDS-OWNER items are untouched.

### TASK-016 — MCP docs consistency pass
- Do: compare `docs/mcp/user-guide.md`, `docs/mcp/clients/*.md`, `docs/mcp/remote-docs.md` against the tool list and options in `mcp-server/src` (names, flags, env vars, versions). Fix discrepancies in docs only. Run markdown link check from TASK-023's script once available (else a simple regex check).
- Done when: a table of fixes is in the commit body; no tool name in docs that is absent from `mcp-server/src`.

### TASK-017 — Draft 14 days of LinkedIn posts
- Folder: `E:\projects\UDS_Simulator\daily-uds-linkedin-post` (separate from git repos — look at `GEMINI.md`, `config/`, `posts/tracker.csv` for format and voice). Create 14 draft files in `posts/drafts-GLM-NIGHT/`, one per day, each: hook, body (≤ 1,300 chars), 3–5 hashtags, link target on udssimulator.com, and a technical-accuracy source note (ISO 14229 SID reference from `docs-site/learning/*`). Topics: pick SIDs/NRCs not already in `tracker.csv`. No fabricated stats or testimonials. DO NOT edit `tracker.csv`, DO NOT post anything.
- Since this folder may not be a git repo: if so, copy the drafts into the worktree under `marketing/linkedin-drafts/` and commit there instead.
- Done when: 14 distinct drafts exist and a lint script (character limit, no duplicates against tracker) passes.

### TASK-018 — Social post automation design doc
- Source: GH #310/#311. Write `docs/marketing/social-automation-design.md`: architecture for scheduled posting (queue, approvals, per-platform adapters for Instagram/Facebook/X, rate limits, secrets handling, dry-run mode, audit log, kill switch). Explicitly state which parts need owner-created accounts/keys. No code, no accounts.
- Done when: doc has data model, sequence diagram (mermaid, validated syntax), failure modes, and a phased rollout.

### TASK-019 — Pre-launch verification matrix (GH #151)
- Write `docs/launch/prelaunch-matrix.md` (device × browser × network × payment-test-mode × analytics-consent) with pass criteria, and `scripts/prelaunch-matrix-check.cjs` that executes the automatable rows against a given base URL using read-only GETs and the existing `scripts/page-health-crawler.cjs`. Default base URL = `http://localhost:5173`; do not run it against production.
- Done when: script `--dry-run` lists all rows and exits 0; the manual rows are labelled MANUAL.

### TASK-020 — Public ROADMAP.md draft (GH #184)
- Build `ROADMAP.md` in the SIM worktree from: open GH issues (read-only list), `openspec` changes, `docs/mcp/progress/status.json`, `docs/seo/*`. Now/Next/Later, no dates the repo does not support, no promises for gated MCP items beyond "in progress".
- Done when: every roadmap item cites an issue number or doc path.

### TASK-021 — Next-quarter feature plan
- Using TASK-020 output, write `docs/planning/next-quarter-plan.md`: ranked themes, dependencies, risks, size (S/M/L), what can be done by an agent vs. needs the owner, and an explicit "not now" list (payment hardening, sandbox execution).
- Done when: each theme links to issues/specs.

### TASK-022 — Dependency audit (report only)
- In root, docs-site, mcp-server: `npm outdated --json` and `npm audit --json` (read-only). Write `docs/glm-night/dependency-audit.md`: table of packages with current/wanted/latest, severity of advisories, and a recommended safe-upgrade batch (patch/minor only). Do NOT modify `package.json` or lockfiles.
- Done when: three tables (one per package) and a prioritized upgrade list.

### TASK-023 — Broken-link and dead-reference check
- Add `scripts/check-doc-links.mjs` (no network): scans `docs/**/*.md`, `docs-site/**/*.md(x)`, `openspec/**`, root `*.md` for relative links and `#anchors` that do not resolve, and for referenced file paths that do not exist. Output a report `docs/glm-night/broken-links.md`. Fix only unambiguous cases (renamed file with a single obvious target); list the rest.
- Done when: script is deterministic, report generated, count before/after in the commit body.

### TASK-024 — UNIT: PLAN-001 progress report
- Repo UNIT (worktree per §3.1). Compare the WP register in `PLAN-001-specification-analysis-and-work-breakdown.md` §5.5 with `git log` ("Implement T-NN"/WP ids), `src/`, `tests/` and `docs/verification`. Write `docs/reports/plan-001-progress-20261117.md`: per WP — status (done / partial / not started), evidence (commit/test path), next 5 packages on the critical path, and consistency notes (e.g., exit criteria in §5.4 with no matching test). Docs only; do not edit source, ADRs, SRS or the AIDLC state files.
- Done when: every WP in the register has a status with evidence.

### TASK-025 — Morning review pack
- Create `docs/glm-night/MORNING_REVIEW.md`: table of all tasks with status/commit/tokens, `git log --grep='\[GLM-NIGHT\]' --stat` summary, list of BLOCKED/FAILED with reasons, assumptions needing owner decision, suggested review order (highest risk first: TASK-001, 010, 014, 015), and the exact commands to review, merge or discard the branch. Push the branch.
- Done when: every task id from this file appears exactly once.

---

## 6. Reserve queue (only after TASK-025; same rules)

| ID | Title | Est. | Notes |
|---|---|---|---|
| TASK-101 | Onboarding tour auto-trigger for new users (GH #58) | 200k | frontend, with tests; no analytics changes |
| TASK-102 | Strengthen weak MCP oracles (`docs/mcp/plans/weak_oracle_backlog_20261106.md`) | 180k | tests only |
| TASK-103 | Question headings batch for remaining 17 SID pages (SEO §1.1) | 250k | only if TASK-006 was reviewed good — otherwise do 5 pages |
| TASK-104 | `add-docs-ascii-diagrams` (23 open) — implement 5 diagrams | 150k | docs-site `check:diagrams` must pass |
| TASK-105 | `add-cross-host-delegation` 4 open tasks: classify, docs-only items | 80k | |
| TASK-106 | Expand thin docs pages that already rank (ACTION-PLAN P2-1) | 100k | real content from `docs-site/learning/*` only |
| TASK-107 | SID negative-response test cases: add missing NRC cases for SIDs flagged in TASK-007 | 150k | tests/test-data only, keep schema from TASK-008 green |

Also available as a read-only filler: triage `add-sandbox-execution` tasks into a Now/Later table (no code) — 60k.

---

## 7. Morning review commands

```bash
cd /e/projects/UDS_Simulator/wt-glm-night
git log --grep='\[GLM-NIGHT\]' --oneline
git log --grep='TASK-014' --stat
cat docs/glm-night/MORNING_REVIEW.md
# accept:   open a PR glm-night/20261117 -> main (do not auto-merge)
# discard:  git worktree remove ../wt-glm-night && git branch -D glm-night/20261117
```
