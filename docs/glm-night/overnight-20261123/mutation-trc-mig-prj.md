# Mutation battery report — trc, mig and prj (B6, overnight 2026-11-23)

Tests-only item; no `src/` edits land from B6. Mutants are hand-written
single-fault edits applied to a **temp copy** of `src/` by
`docs/glm-night/overnight-20261123/mutation_runner_trc_mig_prj.py` (adapted
from the 20261122 lane runner, as the queue instructs); the trc/mig/prj test
suites run against the copy with pytest's `pythonpath` overridden so the shadow
tree wins. A mutant is KILLED when any test fails or errors. Two survivors of
the first pass were resolved: one by a new boundary test (a real test gap),
one by replacing it with a killable mutant after showing the original was
*equivalent* (documented below, not a test gap).

## Kill rate

| Module | Battery | Mutants | Killed | Survivors | Rate |
|---|---|---|---|---|---|
| `src/ectt/trc` (verdict, extent links, ReqIF associations and export) | `mutation_runner_trc_mig_prj.py` | 7 | 7 | 0 | 100% |
| `src/ectt/mig` (Unity/cmocka verdict normalisation, format registry) | same | 4 | 4 | 0 | 100% |
| `src/ectt/prj` (shard names, diff-stable writes, save discipline, threshold config) | same | 6 | 6 | 0 | 100% |
| **Total (B6)** | | **17** | **17** | **0** | **100%** |

First pass: 14/16 scored killed with 1 BAD-MUTANT (TRC-VERDICT-2, find-string
indent) and PRJ-SAVE-2's original form surviving. After fixing the find-string,
replacing the equivalent mutant, and adding the boundary test: 17/17.

## Mutants and the case that kills each

### trc

| Mutant | Seeded fault | Killed by |
|---|---|---|
| TRC-VERDICT-1 | worst outcome -> best outcome (`max` -> `min`) | `test_matrix.py::test_verdict_is_the_worst_executed_outcome` |
| TRC-VERDICT-2 | unreviewed tests execute into the verdict | `test_change_detection.py::test_stale_tests_stop_counting_toward_verdicts` |
| TRC-VERDICT-3 | nothing-executed verdict `unverified` -> `pass` | `test_change_detection.py::test_stale_tests_stop_counting_toward_verdicts` |
| TRC-LINKS-1 | extent boundary off by one (`end <= end_line + 1`) — first pass SURVIVED | new `test_source_links.py::test_range_ending_one_line_past_the_extent_is_refused` (a range ending on `end_line + 1` must be refused `range_spans_functions`) |
| TRC-LINKS-2 | reaching past the extent becomes an approximate resolution | `test_source_links.py::test_range_reaching_beyond_the_extent_is_refused` |
| TRC-REQIF-1 | dangling SPEC-OBJECT-REF accepted | `test_reqif_associations.py::test_dangling_relation_is_refused_with_a_named_reason` |
| TRC-REQIF-2 | relation SOURCE and TARGET swapped on export | `test_property_roundtrip.py::test_reqif_roundtrip_over_seeded_inputs` (20261122) |

### mig

| Mutant | Seeded fault | Killed by |
|---|---|---|
| MIG-UNITY-1 | Unity PASS normalised as `fail` | `test_existing_suites.py::test_unity_pass_ignore_and_detailed_fail` |
| MIG-UNITY-2 | unrecognised Unity lines dropped | `test_existing_suites.py::test_unity_unrecognised_lines_are_reported` |
| MIG-CMOCKA-1 | an unfinished cmocka RUN never finalises | `test_existing_suites.py::test_cmocka_test_started_but_never_finished_is_an_error` |
| MIG-FMT-1 | version drift check inverted (`!=` -> `==`) | `test_formats.py::test_the_shipped_documentation_passes_its_own_checklist` |

### prj

| Mutant | Seeded fault | Killed by |
|---|---|---|
| PRJ-SHARD-1 | shard name accepts a leading dot | `test_mutation_strength_shards.py::test_real_shard_name_validation` (20261121) |
| PRJ-SHARD-2 | diff-stable write inverted (rewrites when unchanged, skips when changed) | `test_mutation_strength.py::test_real_implementations_pass_the_battery` (20261121) |
| PRJ-SAVE-1 | comment-preservation refusal dropped | `test_adr002_conformance.py::test_comment_loss_refused_without_discard` |
| PRJ-SAVE-2 | byte-identical no-op inverted (rewrites every save) — replaces the original PRJ-SAVE-2 | `test_project.py::test_byte_identical_resave_preserves_mtime` |
| PRJ-THRESH-1 | float threshold minimum accepted | `test_threshold_config.py::test_float_minimum_in_file_is_refused` |
| PRJ-THRESH-2 | unknown metric accepted in `allow_not_applicable` | `test_threshold_config.py::test_unknown_metric_is_refused` |

## Equivalent mutant, documented (not counted)

The first PRJ-SAVE-2 dropped the *equality* half of the source-root
confinement check: `if target == src or target.is_relative_to(src)` mutated to
`if False and target == src or target.is_relative_to(src)`. By operator
precedence that reduces to `target.is_relative_to(src)`, and a path equal to
the source root is relative to it — so the mutated check refuses exactly what
the original refuses. The mutant is *equivalent*, not a survivor: no test can
kill it, and the confinement behaviour is intact. It was replaced with the
killable byte-identical no-op mutant above, and the confinement itself stays
covered by `test_project.py`'s `ProjectLocationError` cases.

## Survivors and follow-ups

None in the final pass. The one first-pass survivor that was a real test gap
(TRC-LINKS-1) gained `test_range_ending_one_line_past_the_extent_is_refused`;
the boundary-plus-one and boundary-crossing ranges are now pinned.
