# Lane A summary (2026-11-20 queue)

Executor: Claude (not the GLM agent the queue was written for). Branch `glm-night/20261120-a`, cut from
local `main` `7765236`. Nothing was pushed or merged. The token figures in the ledger are the queue's own
estimates, not measured usage.

## Counts

| State | Items |
|---|---|
| DONE | 9 (WP-CBT-01, WP-ATG-01, WP-TCM-07, WP-GEN-07, FIX-GENPROTO, FIX-TCMNEST, WP-ATG-05, WP-EXT-04, TEST-PROP-TCM) |
| PARTIAL / SECOND-PASS only / SKIPPED / NOT-STARTED | 0 |

Each item is one commit followed by a one-line ledger commit that records its sha. Every item had
acceptance criteria derived and written first (the board recorded none), a verification note under
`docs/verification/` (except the two fix items and the tests-only item, whose allowed paths did not
include one; their evidence is in the commit message), tests with a happy path and error cases, and a
full gate before commit.

## The verification limit that matters most

**No C compiler is available on this machine** (checked `PATH`, LLVM, MSYS2, MinGW, Visual Studio). The C
that two items generate was therefore **not compiled or run**:

- WP-GEN-07 (programmable stubs) and FIX-GENPROTO (result-stream runtime and per-test state reset) are
  verified by parsing the generated C with libclang (the project's own frontend) with zero error
  diagnostics (also strict C89 for the harness runtime), by feeding the line shape derived from the C
  text to the real host-side reader (`ectt.exh.runner`), and by structural assertions on the text.
- The claim that state from one test never leaks into the next is argued from the state machine's text,
  not demonstrated by running two tests. A run on a machine with a C toolchain is the first thing to
  do with these two items (second-pass rows).

## Defects found by the checks themselves (all fixed)

- libclang rejected the first draft of struct output parameters in generated stubs (a by-value copy of a
  type the stub unit only forward-declares); outputs are now scalar-only and say so.
- A classification-tree conflict check treated two classes assigning the *same* value as a conflict.
- A drive path was reported twice by the portability scan.
- Two typo-versus-completeness diagnostics came out in the wrong order (a typo'd member was reported as
  "payload is missing"); structural errors are now reported first.

## Compatibility guarantees checked

- **Flat `.tests` files are byte-stable under FIX-TCMNEST:** a flat document dumped by the code on
  `main` and by this branch is byte-identical with the same case digest; both are pinned as a golden
  test.
- The lifecycle refactor in `ectt.atg` kept all earlier tests green; plain stubs (`generate_stubs`) are
  unchanged.

## Shared-file or other-lane changes needed

All are listed in `SECOND_PASS_A.md`: wire the real validation port, build step and report renderers to
the new capabilities (`ectt.bld`, `ectt.rep`, CLI); record the `review_state` vocabulary, the
`origin.engine` form and the nested path-key form in SDD-002; emit the protocol calls from the framework
back-end templates; type information for the unit-under-test globals; and the compile-and-run
verification above.

Two cross-lane notes: lane A does not depend on lane B (its capability check deliberately does not read
the unsupported-construct inventory that lane B's eligibility gate gained); and lane B owns `ectt.rep`,
which is where the machine-generated and unreviewed marks of WP-ATG-01 would be rendered.

## Final gate (at the last lane A commit)

pytest 2763 passed, 5 skipped; ruff clean; mypy clean (155 source files); plan_check
346/344/191/642/52; trace_check OK. Baseline at the branch point was 1457 passed, 5 skipped.
