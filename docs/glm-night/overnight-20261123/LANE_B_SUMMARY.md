# Lane B summary — overnight 2026-11-23 queue (run 2026-11-27)

Branch `glm-night/20261123-b`, worktree `wt-night-23b`, branched from local `main`
b9b1262 ("Merge glm-night/20261123-a into main"). The queue text named b8ae29f as
the branch point with a 3710/6 baseline; main had moved 22 commits further when the
run started (lane A's 20261123 work plus the tracker merge were already in), and the
actual baseline was **3819 passed / 6 skipped / 1 xfailed / 1 warning** — the +109
tests, the xfail and the warning are lane A's merged work, recorded in the ledger so
lane B's own effects can be told apart from them.

## Counts per state

| State | Count | Items |
|---|---|---|
| DONE | 6 | B1, B3, B4, B5, B6, B7 |
| PARTIAL | 0 | — |
| SKIPPED (dep) | 0 | — |
| SECOND-PASS | 1 | B2 (WP-COV-06, no code written — see below) |

7 queue items, 8 commits (B1, B2, B3, B3 follow-up, B4, B5, B5 ledger, B6+B7),
all on `glm-night/20261123-b`, nothing pushed, no amend/force/`--no-verify`, no
`git add -A`. Final gate at f2b721a-equivalent tip (see "Final gate" below):
**4017 passed / 6 skipped / 2 xfailed / 1 warning** (+198 passed over the branch
baseline; the second xfail is lane B's queued fix, below).

## Commits

| Item | Commit(s) | One-line |
|---|---|---|
| B1 | 0d2275c | WP-REP-05: certification verification report + scope statement (`ectt.rep.certification`), claims checked against data, missing inputs named, target execution and MC/DC never claimed; 44 tests + analysis note |
| B2 | 6d5b62c | SECOND-PASS: WP-COV-06 blocked — the analysis model has no decision inventory to detect from (see below) |
| B3 | 3757e01 (+1f04060) | WP-COV-11: control/data coupling analysis (`ectt.cov.coupling`), statuses only, nothing guessed; + restored the eight justification exports of `ectt.cov` and added the public-surface guard tests |
| B4 | 4771742 | output robustness: probe-driven fixes across JUnit/Cobertura/LCOV/HTML (NUL and control characters broke XML, whitespace rewrite, unencodable text); 96 pinned cases, 28 failed before the fix |
| B5 | 2c00839 (+3365bfb ledger) | interchange round trips + real-tool-style imports; fixed gcovr-style Cobertura double counting (class-level + method-level `<lines>` read twice) and three lcov reader gaps (comments, VER, indexed SF) |
| B6+B7 | b877c1b | mutation battery trc/mig/prj (17/17 killed, report + runner committed) and seeded property tests (coupling, certification, matrix) |

Tests: 3819 → 4017 passed (+198), 6 skipped, 2 xfailed, 1 warning.

## SECOND-PASS and defects with reasons

### B2 — SECOND-PASS, no code written

WP-COV-06 (uninstrumentable expression detection) asked for detection working from
the analysis model's decision inventory at schema 1.5. That inventory does not
exist as data: it is a single status record hard-coded to `not_extracted` by the
assembler, the per-function `decisions[]` the published schema defines has no
field on the model, nothing writes it and the reader drops it. The dependency
WP-COV-05 is unimplemented, the PLAN-001 §5.4 criterion needs a probed condition
maximum per backend (nothing records one; no compiler here to probe), and the
GCC 14.4.0 and 15.2.0 manuals document no maximum, no limit-tuning option and no
non-instrumentable marker for `-fcondition-coverage` — checked, not recalled.
With no decisions to enumerate, every construct would be `no_data`; an
implementation would have rested on invented inputs. What is needed (decision
extraction in ectt.ana, the probe, WP-COV-05, and the SRS-Q2 MC/DC-form answer —
for the record, the gcov manual states GCC's condition coverage is masking
MC/DC) is in SECOND_PASS_B.

### B7 — defect found by the new property, queued per rule 5

The certification stability property failed: `build_certification_report`
renders criteria evaluations and traceability links in their **input order**
(`_coverage_section` / `_traceability_section`). The fix is two `sorted()` calls
(by metric, by test id). B7 is a tests-only item ("No src/ edits"), so per rule
5 the property is pinned `xfail(strict=True)` — the suite goes red the moment
the fix lands until the marker is removed — and the fix is queued in
SECOND_PASS_B. Isolated by shuffling one input at a time; the
criteria-evaluation half only shows when more than one metric is configured.

### Other rows in SECOND_PASS_B

- TOOL-REP-140's scope statement lands only in the new certification report;
  whether/how to add it to the other seven renderers is a coordination decision
  (their bytes are pinned by other lanes' consumers).
- Three packages declare exports they do not bind (`ectt.ana`,
  `ectt.ing`, `ectt.tcm` — found by an `__all__`-vs-attributes scan; the same
  defect in `ectt.cov` was fixed under B3). Outside lane B's packages.
- B4 observations outside its scope: the plain-text report writes control
  characters verbatim; the JUnit digest sits in a `hostname` attribute; the
  report model refuses a lone surrogate with a bare `UnicodeEncodeError`.

## Standing limits (carried, unchanged)

- Files from real tools are still unchecked (no coverage toolchain on this
  machine): the B6/B5 fixtures and the B2 conclusions come from the GCC manuals
  (14.4.0 and 15.2.0) and the public format descriptions (lcov geninfo(1) man
  page, gcovr 8.8 Cobertura docs), all fetched 2026-11-27 and named where used.
- `ectt.cov.call_matching` note: LCOV/Cobertura call and condition matching is
  line-based, one-to-one, and refuses ambiguity rather than guessing.

## Shared-file changes needed

None forced. Owner-facing items recorded in SECOND_PASS_B: the B7 certification
order fix (two sorted calls + remove the xfail marker), the scope-statement
placement decision (TOOL-REP-140), the three export-binding fixes (ana/ing/tcm),
and the three B4 observations above.

## Final gate output (each gate run and checked separately)

```
pytest:      4017 passed, 6 skipped, 2 xfailed, 1 warning
             (xfail 1: lane A's selfverify defect, pre-existing;
              xfail 2: the B7 certification order property, fix queued;
              warning: a pre-existing pytest collection warning)
ruff:        All checks passed!
mypy:        Success: no issues found in 201 source files
plan_check:  PLAN check passed: 346 requirements; 344 unique primary allocations;
             191 packages (all priorities/phases/categories ok; UNALLOCATED 0)
trace_check: OK: every in-scope requirement is allocated and the design graph is
             well formed
```

Process note for the morning: twice this run a finding was recorded instead of
fixed because the owning file was outside the item's allowed paths (B2 entirely;
B7's src fix) — both are queued with concrete fix descriptions, and the B7 one
is enforced by an xfail(strict=True) marker. Gate discipline used throughout:
every gate of the block run and checked separately before every commit.

Stop condition: all 7 items landed well before the 05:30 cutoff. Lane B is
complete; nothing was pushed.
