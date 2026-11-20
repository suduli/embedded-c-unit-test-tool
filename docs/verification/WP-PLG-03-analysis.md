# Verification Analysis Note — WP-PLG-03 (Built-ins Implemented Through Public Extension Points)

Analysis evidence for requirements verified under WP-PLG-03. Status: **implemented**
(evidence-backed).

RECON flag (board): no package-specific acceptance criterion is recorded in PLAN-001 §5.4 for
this package. Derived criteria (implemented as written; register edits are owner territory):

- **AC-1 (TOOL-PLG-090, I — inspection checklist, machine-checked):** for each built-in
  family named by the requirement — compiler configurations, framework back-ends, report
  formats — a checklist audit exercises the *same* registration path a user provider takes:
  same registry class, same validation, same namespace, same duplicate refusal. A family
  that grows a private bypass fails the checklist.
- **AC-2 (checklist soundness):** every audit names the public extension point it exercises
  (the point id must exist in the built-in plg registry), records what it exercised as
  evidence text, and is deterministic (same result on every run).

| Requirement ID | Summary Statement | Implementation Reference | Analysis Argument & Verification Evidence |
|---|---|---|---|
| **TOOL-PLG-090** | The tool's own built-in compiler configurations, framework back-ends, and report formats shall be implemented through the same public extension points available to users, so those interfaces are proven by use. | `src/ectt/plg/builtin_audit.py` (`BuiltinAudit`, `audit_builtin_compiler_configs`, `audit_builtin_framework_backends`, `audit_builtin_report_formats`, `audit_all`); the shared paths exercised: `ectt.rep.formats.ReportFormatRegistry` (WP-REP-11), `ectt.gen.backends.BackendRegistry.register_descriptor` (WP-GEN-02), `ectt.tch.config.CompilerConfigRegistry.register` + `load_compiler_config_text` (WP-TCH-02) | **Checklist (inspection, machine-checked):** each audit builds a fresh public registry and (1) registers the built-ins through the public entry point the family ships (`register_framework_builtins`, `register_host_builtins`, `default_format_registry`), (2) registers a user-supplied provider through the identical API — a custom back-end descriptor, a compiler config loaded through the public YAML validator, a custom format function — proving the shared namespace, and (3) re-registers an existing name and requires the identical duplicate refusal a user would hit, proving shared validation. The report-format audit additionally requires the built-in renders to be byte-identical to the direct public renderers, so no render bypass exists.<br><br>**Proven by use:** the three families' own built-ins are the exercising workloads — the extension points survive registration of user providers *next to* the built-ins with no special-casing.<br><br>**Test evidence:** `tests/plg/test_builtin_audit.py` — `test_builtin_family_rides_the_public_extension_point[*]`, `test_audit_points_exist_in_the_public_registry`, `test_audit_is_deterministic`, `test_report_format_audit_proves_shared_namespace_and_rendering`, `test_framework_backend_audit_proves_shared_descriptor_path`, `test_compiler_config_audit_proves_shared_loader_and_namespace`. |

## Design notes

- **Why the checklist lives in plg and imports lazily.** plg defines the contract names; gen,
  tch and rep implement them. The audits import the families inside the function bodies so no
  import cycle blurs that direction (rep already imports plg.points for the contract name).
- **Why evidence is data, not assertions buried in the audit.** The audit results are
  returned as `BuiltinAudit` records with an `ok` flag and a human-readable evidence line, so
  the inspection artefact can be reviewed (and re-run) without re-reading the code.
- **Scope:** the fourth built-in extension point (`target_execution_methods`) has no built-in
  family yet by design (execution methods are user/hardware territory; WP-EXH-02 is the
  host-run path); the checklist covers exactly the three families TOOL-PLG-090 names.
