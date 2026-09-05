# Validation spikes (WP-SPIKE-01..03)

Three throwaway/semi-throwaway spikes from
[`PLAN-001`](../PLAN-001-specification-analysis-and-work-breakdown.md) §4.4,
run before any architecture is frozen, to de-risk the assumed positions in
[`ADR-001`](../ADR-001-architecture-decisions.md) (Python, PySide6) while
they are still cheap to reverse. None of this is part of the tool's
implementation — see the top-level [`README.md`](../README.md)'s project
status. Each spike's own `README.md` restates its pass criterion verbatim
and links back to the plan that drove it.

| Spike | Question | Status | Verdict |
|---|---|---|---|
| [`spike-01-cfg-sufficiency`](spike-01-cfg-sufficiency/) | Can PAR-030–PAR-060 (function/type/global/call-graph extraction) be done via libclang's AST alone, without a CFG? | done | **PASS WITH DOCUMENTED GAP** — 151,558 real lines (STM32 HAL + CMSIS), 1810 functions/506 types/16 globals/1502 direct calls extracted cleanly; 32 function-pointer calls (2.1%) correctly flagged as unresolved rather than silently dropped — an IRQ/DMA-callback pattern needing points-to resolution, not a CFG. ADR-001 §2.4 does not fail. See [RESULTS.md](spike-01-cfg-sufficiency/RESULTS.md) |
| [`spike-02-nested-editor`](spike-02-nested-editor/) | Is a 4-deep nested struct with a union, function pointer, and array editable, type-validated, at interactive latency in PySide6? | done | **PASS** — all 5 checklist items hold (union at depth 4, enum/handler by name, out-of-range rejected, array rows independent), 242ms cold start. Two non-blocking findings for `WP-GUI-11`: arrays add a UI tree row beyond the schema-depth count, and range enforcement is the model's `validate()`, not the widget validator. See [RESULTS.md](spike-02-nested-editor/RESULTS.md) |
| [`spike-03-packaging`](spike-03-packaging/) | Does a PyInstaller bundle of PySide6 + libclang build, run without admin rights, and land at a defensible size/cold-start? | done | **PASS (local build)** — 194.2 MB onedir, ~162ms in-process cold start, no admin rights implicated, libclang's ctypes-loaded DLL collected without a fallback. Explicitly *not* a clean-machine result — see [RESULTS.md](spike-03-packaging/RESULTS.md#honest-limits-of-this-spike) |

Plans: [`docs/superpowers/plans/2026-09-05-spike-01-cfg-sufficiency.md`](../docs/superpowers/plans/2026-09-05-spike-01-cfg-sufficiency.md) ·
[`...spike-02-nested-editor.md`](../docs/superpowers/plans/2026-09-05-spike-02-nested-editor.md) ·
[`...spike-03-packaging.md`](../docs/superpowers/plans/2026-09-05-spike-03-packaging.md)
