# MC/DC capability gate and condition limit

TOOL-COV-190 (probe), part of TOOL-TCH-070; written 2026-11-28.

- Available with GCC 14 or newer only (owner answers 2026-11-27). Older GCC
  and Clang give `mcdc_not_available`; the other coverage is unaffected.
- The built-in `gcc` configuration declares `mcdc` with
  `--coverage -fcondition-coverage`; gcov needs `--conditions`.
- The limit is probed (`probe_condition_limit`). A real probe of GCC 14.4.0
  gave 64; the evidence is `tests/tch/fixtures/gcc-14.4.0-condition-limit.json`.
- Limit: `plan_mcdc` returns the flags; no build step applies them yet. Wiring
  them into the harness build and the CLI is open.
