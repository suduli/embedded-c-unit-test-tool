# LANE A summary — overnight 2026-11-22 (wiring wave)

Branch `glm-night/20261122-a`, branched from local `main` fc0631c (the plan header
referenced e5184df; main had moved one docs-only commit further — the queue file
itself was regenerated on top of fc0631c, so the branch was cut from current main
HEAD as the setup block literally specifies). Run started 11:21 IST 2026-11-22; all
items finished 12:10 IST, far before the 05:30 stop clock. The lane's token budget
line (1450k) was ignored per the plan's own instruction: no ZAI usage counter exists
in this harness.

## Counts per state

| state | count | items |
|---|---|---|
| DONE | 7 | A1, A2, A3, A4, A5, A6, A7 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 | — |

Listed queue total was 1060k estimated tokens; the ledger's cumulative estimate is
1060k. Nothing was left un-started.

## Cross-lane merge

The lane B dependency (item B2, the five stable report views) was satisfied:
`docs/glm-night/overnight-20261122/LANE_B_LEDGER.md` in `../wt-night-22b` records
B2 = DONE, so `git merge --no-edit glm-night/20261122-b` was executed before A4 per
the queue rule; the full gate was green immediately after the merge (3624 passed,
6 skipped, 1 warning). **This branch now contains lane B's commits** — a morning
merge of `glm-night/20261122-a` into main brings both lanes.

## PARTIAL / SKIPPED / SECOND-PASS items with reasons

No item ended PARTIAL, SKIPPED or SECOND-PASS. One second-pass **row** was
recorded:

1. **A4** — fold the four `cbt-*` operations into `default_catalogue`
   (`src/ectt/api/catalogue.py`) so they publish through the engine's hello
   negotiation like every other operation, and give the catalogue generator
   per-command argument metadata (today `build_parser` only emits `--target-id`,
   so the four commands carry their own parser in `ectt.cli.commands`). `ectt.api`
   is outside this item's allowed paths; the published operation surface and the
   parser-generation design are owner territory.

## Notes for the morning merge

- **Baseline flake observed once** at setup (1 failed in the first full-suite run
  on the cold worktree; immediate re-run green at exactly the plan's 3558/6, and
  every subsequent gate green). Watch the timeout-flavoured harness tests if it
  recurs; nothing was xfailing and no test was weakened.
- **Trust boundary recorded (A7)**: `spell_type` echoes the analysis model's own
  recorded type spellings; the model is built by the libclang analyzer from parsed
  C (an identifier set), so an unreachable-spelling injection is not reachable
  through the real pipeline. The authored-input gate (case ids) is pinned in
  `tests/gen/test_testbody.py`.
- **Parse gate caught a real bug (A2)**: array declarators must bind dimensions to
  the identifier (`extern unsigned char g_buf[8];`, not `unsigned char[8] g_buf`)
  and struct names are tags (`struct Frame`). Fixed in this run; the libclang
  parse tests pin it.

## Shared-file changes needed

None were edited outside this lane's allowed paths. The second-pass file lists the
`ectt.api` catalogue folding.

## Verification summary

Every item: full gate green before its commit (never `--no-verify`; one commit per
item; ledger row per item; pytest's exit code checked explicitly — the pipe-masking
mistake from the first setup run was corrected; no push, no amend, no force;
nothing outside the item's allowed paths — verified per commit's staged list).

Final gate on the finished branch (at the summary commit's parent, tree clean):

```
pytest    : 3678 passed, 6 skipped, 1 warning   (baseline at branch point: 3558 passed, 6 skipped)
ruff      : All checks passed!
mypy      : Success: no issues found in 191 source files
plan_check: PLAN check passed: 346 requirements; 344 unique primary allocations;
            191 packages; 642 person-weeks; dependency lower bound 52 weeks
trace_check: OK: every in-scope requirement is allocated and the design graph is well formed
```

Net new tests this run: +120 passed (3678 − 3558). The 2 xfailed of the 11-21 lane
B merge are not on this base (they belonged to the 20261121 branch line).

## Item → commit map

| item | commit | subject |
|---|---|---|
| A1 | a8d4255 | compose the generation run port in the CLI layer |
| A2 | 76dd767 | file-static reach and extern declarations (HAR-040) |
| A3 | 4828108 | source diff to construct identities via 1.5 extents |
| A4 | 63ec02d | CLI commands for impact, subset, compare, minimize (after merging lane B) |
| A5 | be67513 | parity-gated host run preparation in the CLI |
| A6 | 4242e2e | mutation-style tests for cli/atg/ext, kill rate 16/16 |
| A7 | b6903eb | seeded property tests for bld, cbt and gen |

## Assumptions taken (unattended run, conservative reading)

- Branch point: current local `main` fc0631c (see header).
- Token budget: ignored (no usage counter in this harness); the 05:30 clock was the
  stop condition and was never reached.
- The four CLI commands carry their own real-argument parser inside `ectt.cli`
  (mirroring the catalogue generator's conventions) with an `api.Operation` extension
  catalogue, because `ectt.api` is outside the item's allowed paths — second-pass row
  for the owner to fold them into `default_catalogue`.
- A5's `host-run` command compares the host and target plans as declarations (no
  hardware): the parity gate and labelling are fully exercised offline.
- A6's mutation runner applies mutants to a temp copy of `src/` and shadows it via
  pytest's `pythonpath` override (same mechanism as the 2026-11-21 run).
