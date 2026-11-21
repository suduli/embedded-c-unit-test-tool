# Second pass (lane B) — items needing a human

| item | what is needed | why it needs a human | where |
|---|---|---|---|
| B9 | While running the B9 seeded order-independence property over ectt.cov.merge, the merged document's `data_file` was found to be taken from the first admitted run in INPUT order (src/ectt/cov/merge.py, _merge_documents: `data_file=first.data_file`), so merging the same run set in a different order yields a different aggregate provenance field (counts are unaffected). A conservative fix is to take the representative from the admitted documents in a canonical order (e.g. sorted by (gcc_version, data_file)) so the merge is a pure function of the run set; src/ectt/cov/ is outside B9's allowed paths, so the merge itself was left untouched and the B9 fixture models one build's runs (shared data_file). | Order-dependent provenance is a semantic choice for the cov owner (canonical-order representative vs. carrying per-run provenance only); deciding it changes merge output bytes. | src/ectt/cov/merge.py (_merge_documents), tests/rep/test_property_merge.py |
Resolved while the run was still going: the B1 FormatSpec follow-up below was completed under item B5 (whose allowed paths include src/ectt/mig/), which moved the FormatSpec to 1.5, pointed it at analysis-model-1.5.schema.json and removed the two xfail markers (now passing for real).

