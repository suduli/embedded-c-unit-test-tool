# Second pass (lane B) — items needing a human

| item | what is needed | why it needs a human | where |
|---|---|---|---|
| B1 | Decide whether, and in which formats, the scope statement of TOOL-REP-140 ("Every report shall identify the test scope it covers and shall state explicitly what was excluded from that scope") is added to the existing renderers (text, JSON, HTML, PDF, JUnit, Cobertura, LCOV). Only the new certification report carries one after B1; `ectt.rep.certification` builds it from data every renderer already consumes, so a shared helper is the likely shape. | Adding content changes the bytes of formats that other lanes and CI consumers pin and parse — a JUnit or Cobertura consumer may reject unknown elements — so the format list and the placement are coordination decisions, not a lane call. The requirement text is unambiguous that every report is meant; this row is about how, not whether. | src/ectt/rep/{render,html,pdf,machine_formats,coverage_interchange}.py |
