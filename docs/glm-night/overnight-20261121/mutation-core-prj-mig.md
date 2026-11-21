# Mutation battery report — core, prj, mig (B8, overnight 2026-11-21)

Tests only; no `src/` edits (queue rule). Each mutant is a hand-written copy of one
critical function/contract with a single seeded fault, executed in isolation — the
repo-established mutation-battery pattern (TASK-107). The real implementation is the
oracle: a mutant is killed when its outcome differs from the real implementation on
the same case vector.

## Kill rates

| Module | Battery | Mutants | Killed | Survivors | Rate |
|---|---|---|---|---|---|
| `src/ectt/core` (fs confinement, `OutputRoot.resolve_path`) | `tests/core/test_mutation_strength_fs.py` | 2 | 2 | 0 | 100% |
| `src/ectt/prj` (shard-name validation, read_shards one-key contract) | `tests/prj/test_mutation_strength_shards.py` | 2 | 2 | 0 | 100% |
| `src/ectt/mig` (Unity/cmocka verdict normalisation) | `tests/mig/test_mutation_strength.py` | 5 | 5 | 0 | 100% |
| **Total (this lane's B8 additions)** | | **9** | **9** | **0** | **100%** |

Pre-existing batteries (unchanged, still passing): `tests/core/test_mutation_strength.py`
(canonical text / float / stable-id contracts) and `tests/prj/test_mutation_strength.py`
(project file kinds / save discipline). This report covers the B8 additions.

## Mutants and the case that kills each

### core/fs (tests/core/test_mutation_strength_fs.py)

| Mutant | Seeded fault | Killed by |
|---|---|---|
| fs-m1-absolute-check-dropped | the `absolute_path` rejection is removed | an absolute path landing *inside* the output root (`<root>/inside.txt`): real refuses (`absolute_path`), mutant resolves it |
| fs-m2-root-target-check-dropped | the `root_target` rejection is removed | `resolve_path(".")`: real refuses (`root_target`), mutant resolves the root itself as a file target |

### prj (tests/prj/test_mutation_strength_shards.py)

| Mutant | Seeded fault | Killed by |
|---|---|---|
| prj-m1-shard-name-lax | shard-name regex allows a leading dot (`[A-Za-z0-9._-]+`) | `shard_path(".git")`: real refuses (`invalid_shard_name`), mutant accepts (a `.git` shard would collide with VCS-visible files) |
| prj-m2-one-key-contract-dropped | `read_shards`' one-top-level-key check is removed | a shard holding two keys: real refuses (`invalid_shard`), mutant silently merges |

### mig (tests/mig/test_mutation_strength.py)

| Mutant | Seeded fault | Killed by |
|---|---|---|
| mig-m1-unity-underdetailed-fail-becomes-fail | FAIL without detail becomes `fail` | `f.c:12:test_a:FAIL` must normalise to `error` (an under-detailed failure is never upgraded into a claim it cannot support) |
| mig-m2-unity-ignore-becomes-pass | IGNORE becomes `pass` | `test_b:IGNORE` must be `not_run` |
| mig-m3-unity-unrecognised-dropped | unrecognised lines are dropped | a non-Unity line must be reported in `unrecognised_lines` (never a silent pass) |
| mig-m4-cmocka-failed-becomes-pass | FAILED verdict maps to `pass` | `[  FAILED  ] broken` must be `error` |
| mig-m5-cmocka-unfinished-silent-pass | the trailing unfinished-RUN finalisation is dropped | a RUN with no verdict at stream end must be `error` |

## Survivors and follow-ups

None — all nine mutants were killed by the shipped case vectors, so no additional
tests were required. The kill vectors above are exactly the shipped behavioural
contracts (SDD-003 confinement, TOOL-PRJ-060 shard discipline, TOOL-MIG-010
normalisation rules), which the batteries now pin as regression-sensitive.
