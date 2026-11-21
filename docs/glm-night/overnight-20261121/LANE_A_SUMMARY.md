# LANE A summary — overnight 2026-11-21

Branch `glm-night/20261121-a`, branched from local `main` 26e4330 (the plan header
referenced a690b3f; main had moved one docs-only commit further — the queue file
itself was regenerated on top of 26e4330, so the queue branched from current main as
its setup block literally specifies). Run started 17:56 IST 2026-11-21; all items
finished 19:33 IST, well before the 05:30 stop clock. The lane's token budget line
(1450k) was ignored per the plan's own instruction: no ZAI usage counter exists in
this harness.

## Counts per state

| state | count | items |
|---|---|---|
| DONE | 10 | A1, A2, A3, A4, A5, A6, A7, WP-CBT-02, WP-CBT-03, WP-CBT-04 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 0 | — |

Listed queue total was 1550k estimated tokens; the ledger's cumulative estimate is
1550k. Nothing was left un-started.

## Cross-lane merge

The lane B dependency (WP-COV-02) was satisfied: `docs/glm-night/overnight-20261121/LANE_B_LEDGER.md`
in `../wt-night-21b` records WP-COV-02 = DONE, so `git merge --no-edit glm-night/20261121-b`
was executed before WP-CBT-02 per the queue rule; the full gate was green immediately
after the merge (3442 passed, 6 skipped, 2 xfailed). **This branch now contains lane
B's commits** (cov/rep/ana work) — that is the queue's intended sharing mechanism, and
a morning merge of `glm-night/20261121-a` into main brings both lanes.

## PARTIAL / SKIPPED / SECOND-PASS items with reasons

No item ended PARTIAL, SKIPPED or SECOND-PASS. Nine second-pass **rows** were
recorded in `SECOND_PASS_A.md` for work that needs other owners or hardware:

1. **A2** — compile and run the composed generated C with a real toolchain (no C
   compiler on this machine); render the UUT call body (CMP-GEN).
2. **A3** — render the nested comparison into harness C and supply observed nested
   values from the analysis model; document the return path-key form in SDD-002 §5.1.
3. **A4** — wire the host-profile label and the parity-gated run preparation into
   CLI/report renderers; execute one real host+target run pair (needs hardware).
4. **A5** (three rows) — rep renderers should show `RunReport.marks`; a production
   composition point (CLI) must bind `BoundValidationPort`'s delegates in production
   (tests demonstrate the binding; the DSN-ATG-110 layer rule forbids atg from
   importing the lower layers itself); a values channel from the harness is needed so
   generated cases carry observed expectations.
5. **WP-CBT-02** — wire affected sets and subset runs into CLI/reports; map a source
   diff to the construct identities the coverage data uses.
6. **WP-CBT-03** — wire the run comparison into CLI/reports; decide whether the
   derived "removed" category belongs in the register wording of TOOL-CBT-050.
7. **WP-CBT-04** — wire `minimize_suite` into CLI/reports; decide greedy-vs-exact
   minimality for the register wording (exact minimum cover is NP-hard).

## Candidate defect found (not fixed; tests-only discipline in A7)

A lone trailing backslash (`"0 \"`) passes the stub value character-set checks in
`ectt.gen.stubctl` although it renders invalid C. Refusing it is a `src/` change and
A7 is tests-only; recorded in the ledger and as a comment in
`tests/gen/test_properties_seeded.py`. Owner decision.

## Shared-file changes needed

None were edited outside this lane's allowed paths. The second-pass file lists what
needs `ectt.cli`, `ectt.rep`, SDD-002 text, a C toolchain or hardware.

## Verification summary

Every item: full gate green before its commit (never `--no-verify`; one commit per
item; ledger row per item; no push, no amend, no force; nothing outside the item's
allowed paths — verified per commit's staged list).

Final gate on the finished branch (at the summary commit's parent, tree clean):

```
pytest  : 3481 passed, 6 skipped, 2 xfailed   (baseline at branch point: 3097 passed, 6 skipped)
ruff    : All checks passed!
mypy    : Success: no issues found in 183 source files
plan_check: PLAN check passed: 346 requirements; 344 unique primary allocations;
            191 packages; 642 person-weeks; dependency lower bound 52 weeks
trace_check: OK: every in-scope requirement is allocated and the design graph is well formed
```

Net new tests this run: +384 passed (3481 − 3097), +2 xfailed (lane B's pre-existing
mig xfails, inherited via the merge).

## Item → commit map

| item | commit | subject |
|---|---|---|
| A1 | 39b89bf | link-plan gate + suite records in the build step |
| A2 | e0b6786 | per-case stub bodies, result markers, reset registration |
| A3 | 24f66f6 | nested inputs.globals and composite return values |
| A4 | f10fce9 | versioned host profile and parity-gated run preparation |
| A5 | 8f79644 | bind the validation port to bld/exh, add run report marks |
| A6 | 80fc30b | mutation-style tests for gen/cbt/exh, kill rate 20/20 |
| A7 | b20819d | seeded property-style tests for gen and atg |
| WP-CBT-02 | 8a81256 | change impact analysis and subset execution (after merging lane B) |
| WP-CBT-03 | c87f3e0 | run comparison and coverage delta |
| WP-CBT-04 | 8227aed | test suite minimization by coverage redundancy |

## Assumptions taken (unattended run, conservative reading)

- Branch point: current local `main` 26e4330 (see header).
- Token budget: ignored (no usage counter in this harness); the 05:30 clock was the
  stop condition and was never reached.
- A2's scope is the union of the 11-20 second-pass rows WP-GEN-07 and FIX-GENPROTO
  that the item names; the UUT-call-body rendering (CMP-GEN) stays second-pass.
- A5's binding honors the pinned DSN-ATG-110 layer rule (`tests/atg/test_lifecycle.py`
  forbids `ectt.atg` from importing `ectt.bld`/`ectt.exh`): the port's delegates are
  injected and the tests perform the real composition; a production composition point
  is a second-pass row.
- WP-CBT-02/03/04 acceptance criteria are derived from the SRS text (PLAN-001 §5.4
  records no package-specific criterion; the tracker flag stands for reconciliation).
- Lane B's ledger check for WP-COV-02 was read at merge time; the merge brought lane
  B's committed state (its in-progress uncommitted WP-COV-07 files were not merged —
  a merge carries commits, not working trees).
