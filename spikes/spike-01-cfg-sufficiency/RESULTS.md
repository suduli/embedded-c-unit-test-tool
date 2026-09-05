# Spike 01 — Results: CFG Sufficiency

## Pass criterion (verbatim, PLAN-001 §4.4)

> Function, type, global and call-graph extraction complete on a ≥20 kLOC
> embedded project with vendor headers, with no construct requiring a CFG.
> If a CFG is needed, §2.4 of ADR-001 fails and the C++ analyzer moves from
> "later" to "now".

## Fixture

`STMicroelectronics/STM32CubeF4` (BSD-3-Clause), sparse-checked-out via
`fetch_fixture.sh` — `Drivers/CMSIS/Include`, `Drivers/CMSIS/Device/ST/STM32F4xx/Include`,
and the full `Drivers/STM32F4xx_HAL_Driver` (`Inc` + `Src`). Not vendored
into this repository (gitignored `fixture/`).

- **94** `.c` files parsed, all under `Drivers/STM32F4xx_HAL_Driver/Src`
- **151,558 lines** counted across those files — **7.5× the 20,000-line
  floor**
- **0 files with parse diagnostics** — every file parsed cleanly against
  the `thumbv7em-none-eabi` target, no vendor construct required a
  workaround beyond the one described below

## Extraction totals (deduplicated — see "Deviations")

| | Count |
|---|--:|
| Functions | 1,810 |
| Types (struct/union/enum/typedef) | 506 |
| Globals | 16 |
| Direct calls (AST-resolved) | 1,502 |
| Indirect calls (function-pointer dispatch, AST-unresolved) | 32 |

Indirect calls are **2.1%** of all call sites (32 of 1,534).

## The central question: do any of the 32 indirect calls need a CFG?

No. All 32 were inspected; every one is the same well-understood pattern:
an interrupt/DMA-completion **callback dispatch through a handle struct's
function-pointer field** — e.g. `HAL_DMA_IRQHandler` invoking
`hdma->XferCpltCallback(hdma)`. Five representative examples, with file
and line so they can be spot-checked against the real HAL source:

| File | Caller | Expression | Declared type | Line |
|---|---|---|---|--:|
| `stm32f4xx_hal_dma.c` | `HAL_DMA_IRQHandler` | `XferCpltCallback` | `void (*)(struct __DMA_HandleTypeDef *)` | 895 |
| `stm32f4xx_hal_adc.c` | `ADC_DMAConvCplt` | `XferErrorCallback` | `void (*)(struct __DMA_HandleTypeDef *)` | 2052 |
| `stm32f4xx_hal_i2c.c` | `I2C_ITError` | `XferAbortCallback` | `void (*)(struct __DMA_HandleTypeDef *)` | 6457 |
| `stm32f4xx_hal_exti.c` | `HAL_EXTI_IRQHandler` | `PendingCallback` | `void (*)(void)` | 452 |
| `stm32f4xx_hal_i2s.c` | `HAL_I2S_IRQHandler` | `IrqHandlerISR` | `void (*)(struct __I2S_HandleTypeDef *)` | 1662 |

This is exactly the class of construct PLAN-001 §4.4 anticipated as the
likely gap: none of it requires statement-level control-flow reasoning
(no dominance, no reachability, no loop analysis). Resolving *which*
concrete function each pointer could hold at a given call site is a
**points-to / symbol-table problem** — tractable by matching the
function-pointer field's declared type against candidate functions
assigned to it elsewhere in the codebase — and that is a fundamentally
different (and cheaper) technique than building a CFG. The extraction
engine correctly recorded every one of these as an explicit, typed,
located "unresolved" edge rather than silently dropping it or
misattributing it to the wrong caller — which is the actual thing this
spike needed to prove capable of happening honestly.

**Recommendation:** track function-pointer call-graph resolution as a
scoped enhancement to `WP-ANA-03` (call graph and scope classification),
using the function-pointer's declared type plus a project-wide index of
same-typed function assignments. Do **not** treat this as a reason to
pull `WP-ANA-05` (the separate, later, genuinely CFG-based work package)
forward — nothing found here needed it.

## Deviations from the plan (what, and why)

1. **Freestanding standard headers had to be supplied.** `-target
   thumbv7em-none-eabi` selects a bare-metal target with no bundled C
   library, so `<stdint.h>`/`<stddef.h>` — which every CMSIS/HAL file
   includes — don't exist for libclang to find. Added
   `freestanding_stubs/{stdint.h,stddef.h}` (minimal, standard-conforming
   typedefs only) and prepended that directory to the include path in
   `parse_args_for`. This is not a HAL-specific workaround; any bare-metal
   `-target` parse needs it, and the real `CMP-ANA` will need the same
   thing (or a bundled freestanding sysroot) regardless of which vendor
   codebase it points at.
2. **Deduplication was required to get a meaningful count at all.**
   `stm32f4xx_hal.c`'s own translation unit contains 1,858 top-level
   cursors, of which only ~30 are actually declared in that file — the
   rest arrive from shared headers (`stm32f4xx_hal.h` alone pulls in
   roughly 40 per-peripheral headers once every HAL module is enabled).
   Summing `len(result.functions)` etc. per file, as the plan's original
   `run_spike.py` did, inflates "functions" from a real **1,810** to a
   nonsensical **19,974** (see `report.json`'s
   `totals_raw_per_tu_summed` vs `totals`) — an **11×** multiplier purely
   from re-parsing shared headers once per including file. Fixed by
   deduplicating on declaration identity (`(file, line, name)` for
   functions/globals; `(file, name, kind)` for types, which carry no
   line) across the whole run — the standard per-TU-index-then-merge
   pattern. **This is itself a finding worth carrying to `WP-ANA-04`**
   (analysis model persistence): the real analyzer needs the same
   project-wide merge step, not just per-file extraction, or its own
   counts will be equally meaningless.

## Verdict

**`PASS WITH DOCUMENTED GAP`**

Function, type, global, and call-graph extraction completed cleanly on
151,558 lines (7.5× the floor) of real, unmodified vendor embedded C, with
zero parse errors. The only gap — 32 function-pointer call sites (2.1% of
all calls) that AST-only extraction cannot resolve to a concrete callee —
is exactly the kind of bounded, well-understood under-approximation
PLAN-001 §4.4 flagged as the expected risk, not a sign that CFG-level
analysis is required. Per §4.4: **ADR-001 §2.4 does not fail**, and the
C++ analyzer question stays "later," not "now."
