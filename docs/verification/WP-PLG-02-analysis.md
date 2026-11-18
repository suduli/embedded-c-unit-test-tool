# Verification Analysis Note — WP-PLG-02 (Extension Discovery and Load Failure Isolation)

RECON: PLAN-001 §5.4 records no package-specific exit criterion for WP-PLG-02. The
acceptance criteria below are derived from the SRS-001 requirements owned by this work
package: TOOL-PLG-070 (S, P3, T) and TOOL-PLG-080 (M, P3, D).

## Acceptance criteria

- AC-1 (falsifiable, from TOOL-PLG-070): user-supplied extensions are discovered from
  a documented location — a caller-supplied extensions directory scanned for `*.py`
  files — and loaded without any reinstallation step; a well-formed extension (one
  exposing a `register(registry)` callable) loads and registers through the public
  WP-PLG-01 registry surface.
- AC-2 (falsifiable, from TOOL-PLG-080): a failing extension is reported clearly with
  its name, failure kind (`syntax_error`, `import_error`, `runtime_error`,
  `incompatible` for a module without `register`), and detail — and loading continues:
  every other well-formed extension still loads, and the report is deterministic.
- AC-3 (falsifiable): a missing extensions directory is a named error; non-`.py`
  files are ignored; the report distinguishes loaded from failed deterministically.

**Trust note:** loading a user extension executes user code; callers must consult the
WP-SEC-03 trust gate (`UntrustedProjectTracker`) before discovery, and the analysis
note records that requirement. The loader itself is mechanical and performs no trust
decisions.

## Requirement trace

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PLG-070** | The tool shall discover and load user-supplied extensions from a documented location without requiring reinstallation. | `src/ectt/plg/discovery.py` (`discover_extensions`, `load_extension_file`, `ExtensionsDirError`), re-exported by `src/ectt/plg/__init__.py` | **Guarantee:** the documented location is a caller-supplied extensions directory scanned for `*.py` files (underscore-prefixed helpers ignored, non-`.py` ignored); a well-formed extension — one exposing `register(registry)` — loads via its file location and registers through the public WP-PLG-01 registry surface, no reinstallation anywhere in the path; a missing directory is a named `ExtensionsDirError`.<br><br>**Trust gating (recorded obligation):** discovery executes user code, so callers must consult the WP-SEC-03 `UntrustedProjectTracker` before invoking it; the loader performs no trust decisions itself — that boundary stays in the security package.<br><br>**Test evidence:** `tests/plg/test_discovery.py` — `test_extensions_discovered_and_loaded_without_reinstallation`, `test_missing_directory_is_named_error`, `test_non_py_files_ignored`. |
| **TOOL-PLG-080** | The tool shall report clearly when an extension fails to load or is incompatible, and shall continue operating with the remaining functionality. *(Method D)* | `src/ectt/plg/discovery.py` (`LoadFailure`, `DiscoveryReport`, four failure kinds) | **Guarantee:** each file loads in isolation; a failing extension becomes a recorded `LoadFailure` with name, kind (`syntax_error` / `import_error` / `runtime_error` / `incompatible`) and detail, rendered as a clear one-line report, while every other extension still loads — demonstrated with four failing extensions and two good ones in one directory: both good extension points are usable afterwards, all four failures are kinded and named. The report is deterministic (sorted names) and serialisable.<br><br>**Test evidence:** `tests/plg/test_discovery.py` — `test_failures_are_isolated_and_reported_clearly`, `test_remaining_functionality_continues_after_failures`, `test_report_is_deterministic_and_frozen` (6 tests total, green in the WP-PLG-02 gate run: 737 passed, 4 skipped). |
