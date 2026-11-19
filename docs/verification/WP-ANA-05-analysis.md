# WP-ANA-05 — Analysis: control flow graph capability

Lane: BUILD (night run, chat 2) · 2026-11-18 · Worktree `wt-chat2`, branch `glm-night/chat2`, baseline `glm-night/20261117` (e2708f1).

## Acceptance criteria

RECON: no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for WP-ANA-05.
Derived from the SRS-001 texts (TOOL-PAR-070, TOOL-PAR-120) and the recorded design (SDD-001 §4.2:
"the CFG is behind a capability flag (DSN-ANA-040) precisely because libclang cannot supply one,
so consumers degrade rather than break"; ADR-001 §2.4/§2.5: the CFG-producer decision is open,
WP-SPIKE-01 confirmed extraction needs none):

- **AC-1 (DSN-ANA-040, decision-free):** a named CFG capability record exists, declaring
  unavailability with a recorded reason while the CFG-producer decision (ADR-001 §2.4) is open —
  consumers can degrade rather than break.
- **AC-2 (TOOL-PAR-120, decision-free):** cyclomatic complexity is **computed per function** from
  the real parsed translation unit (token-based decision-point count: `if/for/while/case` +
  `&&`/`||`/ternary, standard MCC approximation) and exposed as an optional in-memory
  `FunctionModel.complexity` field; functions without a computed value carry `None` and the
  persisted SDD-002 shape is unchanged (schema bump deferred — recorded below).
- **AC-3:** the computation is deterministic: same source → same complexity, byte-identical across
  runs.
- **AC-4 (ADR-sensitive boundary):** the CFG **construction** itself (TOOL-PAR-070's graph) is the
  open ADR-001 §2.4 mechanism question (libclang cannot supply a CFG; the choice of a custom
  builder vs a future C++ analyzer is not made here). Nothing in this increment claims a CFG
  exists; the capability record says it does not, with the reason.

## Implementation

- `src/ectt/ana/cfg.py` — `CFG_UNAVAILABLE_REASON`, `CfgCapability.cfg_unavailable()`,
  `count_decision_points(extent_tokens)`, `cyclomatic_complexity(decision_points)`,
  `compute_complexities(parsed_tu)` (per top-level function definition).
- `src/ectt/ana/model.py` — optional `complexity: int | None = None` on `FunctionModel`,
  included in `to_dict()` only when set (persisted 1.4 shape untouched).
- `tests/ana/test_cfg.py` — the AC checks, parsed with the real libclang front-end.

## Requirement → implementation → test-evidence table

| Requirement | Implementation | Test evidence (`tests/ana/`) |
|---|---|---|
| TOOL-PAR-120 (cyclomatic complexity per function, in the model) | `cfg.compute_complexities` + `FunctionModel.complexity` | `test_cfg.py::test_complexity_of_known_source`, `::test_complexity_is_deterministic`, `::test_complexity_formula`, `::test_function_model_carries_complexity_when_computed`, `::test_function_model_without_complexity_omits_key` |
| TOOL-PAR-070 (CFG per function) via DSN-ANA-040 degrade contract | `cfg.CfgCapability` | `::test_cfg_capability_unavailable_with_named_reason`, `::test_capability_reason_names_the_open_decision` |

## Not covered by this increment (recorded, not decided)

- The CFG data structure and its construction mechanism — **the ADR-001 §2.4 question**, not
  decided by an unattended run.
- Persisted-schema exposure of complexity (additive minor bump of the analysis model schema) —
  the in-memory model carries it; the schema bump belongs to the owning merge.
- Coverage/test-generation consumers of the CFG — downstream CMP-COV/CMP-ATG packages.

## Verification status

Gates re-run after the increment: suite green, ruff/mypy/plan_check/trace_check exit 0.
**PARTIAL** — complexity computation + capability/degrade contract landed; CFG construction is the
open ADR-sensitive remainder.
