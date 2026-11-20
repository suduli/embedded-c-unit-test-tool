# Lane B summary (2026-11-20 queue)

Executor: Claude (not the GLM agent the queue was written for). Branch `glm-night/20261120-b`, cut from
local `main` `7765236`. Nothing was pushed or merged. The token figures in the ledger are the queue's own
estimates, not measured usage.

## Counts

| State | Items |
|---|---|
| DONE | 10 (FIX-REP, FIX-TXN, CI-LINUX, WP-MIG-02, WP-MIG-05, WP-TRC-05, WP-MIG-03, WP-MIG-07, FIX-ANAGATE, TEST-MUT2) |
| PARTIAL | 2 (WP-MIG-04, WP-TRC-04) |
| SECOND-PASS only / SKIPPED / NOT-STARTED | 0 |

Each item is one commit followed by a one-line ledger commit that records its sha.

## PARTIAL items and why

- **WP-MIG-04:** TOOL-MIG-050 (CSV) is done; TOOL-MIG-030 is done for tabular exports only. Adapters for a commercial
  tool's own non-tabular export need that tool's documented sample, which is not in the repository.
- **WP-TRC-04:** TOOL-TRC-070 (ReqIF export) is done and round-trips through the importer. TOOL-TRC-100 (adapter to an
  external traceability tool) is not done: the tool is not chosen (StrictDoc or OpenFastTrace; the SRS names
  neither) and cannot be tested without it installed.

## Defects found in existing code while doing the work (all fixed, each with a regression test)

- **ReqIF importer** (`ectt.trc.imports`) only read a non-standard `REF` attribute, so standards-shaped ReqIF lost its
  identifiers and descriptions. It now reads the schema's `-REF` element form too.
- **cmocka parser** (`ectt.mig.existing_suites`) recognised only `[  OKAY    ]`; cmocka prints `[       OK ]`, so passing
  tests of a real run produced no records. `OK` is now accepted.
- **Report reader** required `execution` on every 1.1 report, so merged CI reports could not be loaded. It is now optional
  (provenance stays required).
- **Two defects found by an end-of-run review against primary sources, and fixed in a follow-up commit:**
  the Ceedling importer refused Ceedling's own stock template because it parsed `project.yml` with ectt's
  no-anchors project-file loader (Ceedling's template uses `&common_defines` / `*common_defines`; aliases are
  now resolved, scalars stay text, bombs and cycles are refused); and the ReqIF export wrote
  `REQ-IF-VERSION` `1.2` where the OMG schema fixes `1.0`, found by validating the export against the real
  XSD (zero errors now; the check is an optional test because the XSD is not vendored).
- Defects in my own first drafts, caught by tests before commit: duplicate ReqIF attribute-definition identifiers across
  object types, a header identifier that depended on the timestamp, `SourceLink` ordering over `None` fields, an analysis
  model example with a dangling type reference.

## Mutation result (TEST-MUT2)

66 hand-written mutants over `ectt.rep` and `ectt.trc`: 51 killed by the existing tests (77.3%), 14 of the 15 survivors
killed by 18 new tests, 1 equivalent (M24). Final 65/66 (98.5%); 65/65 excluding the equivalent mutant. Report:
`mutation-rep-trc.md`; runner: `mutation_rep_trc.py` (re-runnable; it uses a temp copy of `src`).

## Shared-file or other-lane changes needed

All are listed in `SECOND_PASS_B.md`: make `OutputRoot.transaction` re-entrant (`core/fs.py`); add a function end line
to `FunctionModel` and keep every occurrence in the unsupported-construct inventory (analysis schema); publish the
rendered format reference under `docs/` and update the WP-MIG-01 note for the cmocka `OK` spelling; choose the TOOL-TRC-100
tool. One reading to confirm: project saves use a `Project.transaction` of their own rather than `OutputRoot.transaction`,
because the project tree is the source tree that `OutputRoot` refuses to write into.

## Final gate (at the last lane B commit)

pytest 1689 passed, 5 skipped; ruff clean; mypy clean (150 source files); plan_check 346/344/191/642/52; trace_check
OK. Baseline at the branch point was 1457 passed, 5 skipped.
