# LANE A summary — overnight 2026-11-23 (qualification, security, coverage depth)

Branch `glm-night/20261123-a`, branched from local `main` 80cf5c6 (the plan header
referenced b8ae29f; main had moved one docs-only commit further — the queue file
itself is the tip commit, so the branch was cut from current main HEAD as the setup
block literally specifies). Run started 00:11 IST 2026-11-23; all items finished
00:56 IST, well before the 05:30 stop clock. The lane's token budget line (1450k)
was ignored per the plan's own instruction: no ZAI usage counter exists in this
harness.

## Counts per state

| state | count | items |
|---|---|---|
| DONE | 9 | A1, A2, A3, A4, A5, A6, A7, A8, A9 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 | — |

Listed queue total was 1330k estimated tokens; the ledger's cumulative estimate is
1330k. Nothing was left un-started.

## PARTIAL / SKIPPED / SECOND-PASS items with reasons

No item ended PARTIAL, SKIPPED or SECOND-PASS. Two second-pass **rows** were
recorded:

1. **A3** — release signing for the SBOM (signature field + key management): the
   keys are the owner's; the mechanism is an owner decision. The generator carries
   the named `signing_not_configured` marker and the document has no signature
   field.
2. **A9 (defect found)** — `verify_tree` (src/ectt/core/selfverify.py, landed by
   A7) counts a deleted file as **changed as well as missing**, contradicting the
   module's own contract ("changed = present in both, digest differs"). Found by
   A9's random-mutation oracle; per plan rule 5 the strict test is
   `xfail(strict=True, reason=...)` and the one-line src fix is queued as the
   second-pass row (A9 is a tests-only item; src is outside its paths).

## Defects and findings worth the morning's attention

- **A9 defect (see above):** one-line fix in `verify_tree` — change the digest
  comparison to require the path to be present in the tree, then un-xfail
  `test_changed_excludes_missing_files` (the strict marker forces it).
- **A3 spec source:** CycloneDX field names were taken from the actual 1.5 JSON
  schema (`schema/bom-1.5.schema.json`, `github.com/CycloneDX/specification` tag
  1.5, fetched 2026-11-23) — source recorded in the ledger and the analysis note.
- **A8 equivalent mutant:** SEC-PINS-3 (drop the final sort in `check_pins`) is
  behaviorally equivalent — one difference per package and the loop already
  iterates names in sorted order — documented in the mutation report instead of an
  unkillable test.
- **A5/A6 machine limits:** no compiler, debugger or simulator — verification is
  by recording fake starters, golden text and parse-only checks (say-so recorded
  in the ledger and the analysis notes).

## Shared-file changes needed

None were edited outside this lane's allowed paths. The second-pass file lists the
signing owner decision and the selfverify fix.

## Verification summary

Every item: full gate green before its commit (never `--no-verify`; one commit per
item; ledger row per item; pytest's exit code checked explicitly; no push, no
amend, no force; nothing outside the item's allowed paths — verified per commit's
staged list).

Final gate on the finished branch (at the summary commit's parent, tree clean):

```
pytest    : 3819 passed, 6 skipped, 1 xfailed, 1 warning   (baseline at branch point: 3710 passed, 6 skipped)
ruff      : All checks passed!
mypy      : Success: no issues found in 198 source files
plan_check: PLAN check passed: 346 requirements; 344 unique primary allocations;
            191 packages; 642 person-weeks; dependency lower bound 52 weeks
trace_check: OK: every in-scope requirement is allocated and the design graph is well formed
```

Net new tests this run: +109 passed (3819 − 3710), plus 1 strict xfail (the A9
defect marker).

## Item → commit map

| item | commit | subject |
|---|---|---|
| A1 | 0875796 | user-executable validation suite (WP-QUA-03) |
| A2 | 465e1da | known error list per release (WP-QUA-04) |
| A3 | 0519043 | SBOM generation, CycloneDX 1.5 (WP-SEC-01) |
| A4 | f317862 | pinned dependency integrity check (WP-SEC-02) |
| A5 | 4518d2f | restricted execution context for harnesses (WP-SEC-06) |
| A6 | 2db247b | debugger launch with entry breakpoint (WP-EXH-04) |
| A7 | ab53fb7 | self-verification of the tool's own source (WP-CORE-08) |
| A8 | a8519db | mutation tests for qua/sec/exh, 16/17 (1 equivalent) |
| A9 | 8e6b02b | seeded property tests for qua, sec and core |

## Assumptions taken (unattended run, conservative reading)

- Branch point: current local `main` 80cf5c6 (see header).
- Token budget: ignored (no usage counter in this harness); the 05:30 clock was
  the stop condition and was never reached.
- A3's SBOM generator reads installed metadata through an injected reader
  (default `importlib.metadata`); installed distributions record no trustworthy
  package-artifact hash, so none is reported rather than invented.
- A5's restricted context and A6's debugger launch are proven with recording fake
  starters (no real process is started by any test); OS-level sandboxing and a
  GDB/MI front-end remain owner/platform work (SRS open question 9 stands).
- A7's functions operate on any tree; the shipped manifest generation and its
  signing are packaging-time owner concerns.
- A9's defect marker is xfail(strict=True) by plan rule 5; the fix is queued in
  the second-pass file, not self-applied (tests-only item).
