# Verification Analysis Note — WP-REP-11 (Report Format Extension Point)

Analysis evidence for requirements verified under WP-REP-11. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
this package. The falsifiable criteria below are derived from the PLAN-001 §5.4 row
(`WP-REP-11`, CMP-REP, P3, 2w, TOOL-PLG-050, deps REP-01 + PLG-01, both landed) and the SRS
text, and are implemented as written. They are recorded here rather than in PLAN-001 —
register edits are owner territory (reconciliation noted in SECOND_PASS).

## Acceptance criteria (derived, falsifiable)

- **AC-1 (TOOL-PLG-050, verification method T — equivalence partitioning):** adding a report
  format is possible by consuming the documented intermediate report model, without
  re-executing tests. Structural proof in `tests/rep/test_formats.py::
  test_custom_format_added_without_reexecuting_tests`: the model is obtained from a persisted
  dump (`load_report_model(dump_report_model(...))`) — no `ResultSet` is in scope — and a
  custom `markdown` format renders from it after registration.
- **AC-2 (provider-input partitions):** valid name + callable accepted; empty/whitespace/
  non-string names refused (`invalid_format_name`); non-callable providers refused
  (`invalid_provider`); duplicate names refused (`duplicate_format`); rendering an unknown
  format refused (`unknown_format`) with the available names reported.
- **AC-3 (built-ins unchanged):** the registry ships `json` and `text` delegating byte-identically
  to the WP-REP-01 renderers; `default_format_registry()` returns a fresh instance per call so
  third-party registrations cannot mutate shared state.

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PLG-050** | Adding a report format shall be possible by consuming the documented intermediate report model, without re-executing tests. | `src/ectt/rep/formats.py` (`ReportFormatRegistry`, `default_format_registry`, `REPORT_FORMAT_CONTRACT`, `REPORT_FORMATS_POINT_ID`), the `report_formats` extension point descriptor (`src/ectt/plg/points.py`, contract `report_format`, interface version 1), the model (`src/ectt/rep/model.py`, WP-REP-01) | **Guarantee (the seam):** the plg side defines the documented extension point; WP-REP-11 provides the provider side — a named registry whose providers are pure functions `ReportModel -> str`. Registration validates the name (non-empty, whitespace-free string) and the provider (callable), refuses duplicates, and `render(model, name)` dispatches deterministically; unknown names name the available formats in the error.<br><br>**Guarantee (no re-execution):** a format consumes only the model — the fixture format never touches execution artefacts, and the acceptance test builds the model purely from a persisted dump, so the "without re-executing tests" clause is exercised literally, not just argued.<br><br>**Guarantee (built-ins stay put):** `text` and `json` are registered providers delegating to `render_text`/`render_json`; their rendered bytes are asserted identical to direct renderer calls, so the extension mechanism did not fork the built-in behaviour.<br><br>**Test evidence:** `tests/rep/test_formats.py` — `test_extension_point_descriptor_exists`, `test_custom_format_added_without_reexecuting_tests`, `test_builtin_formats_stay_byte_identical_to_direct_renderers`, `test_registry_instances_are_isolated`, `test_invalid_format_names_are_refused[*]` (empty, space, tab, None, int), `test_non_callable_provider_is_refused`, `test_duplicate_format_name_is_refused`, `test_unknown_format_render_is_refused_and_names_available_ones`, `test_custom_format_output_is_json_safe_when_requested`. |

## Design notes

- **Why a plain named registry, not a plugin loader.** TOOL-PLG-050 is about the *ability* to
  add a format against the documented model. Discovery of third-party packages is
  `ectt.plg.discovery` territory (WP-PLG-02); this registry is the dispatch point formats plug
  into either way.
- **Why the error category is `report`, not `extension`.** The registry lives in the report
  package and its failures are report-configuration failures; the WP-CORE-02 exit-code
  mapping resolves the category through its total-by-fallback path (`EXIT_TOOL_ERROR`) until
  the CLI table gains `"report"` (WP-CLI-05, SECOND_PASS).
- **Why names must be whitespace-free.** Format names appear in CLI invocations and error
  messages; the constraint keeps both unambiguous and matches the id discipline of the model.
