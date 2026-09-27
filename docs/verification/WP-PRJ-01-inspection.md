# Verification Inspection Note — WP-PRJ-01 (Plain-Text Schema-Versioned Project Store)

Inspection evidence for requirements verified by inspection (*I*) under WP-PRJ-01:

| Requirement ID | Summary Statement | Implementation Reference | Verification Evidence |
|---|---|---|---|
| **TOOL-PRJ-010** | Plain-text, human-readable project data in restricted YAML | `src/ectt/prj/yaml_adapter.py` (`RestrictedYamlAdapter`) | `tests/prj/test_yaml_adapter.py::test_yaml_typing_hazards_roundtrip` proves plain-text restricted YAML emission and parsing with explicit string coercion. |
| **TOOL-PRJ-020** | Explicit schema version as first key in all project files | `src/ectt/prj/model.py` (`dispatch_schema_version`) & `yaml_adapter.py` | `tests/prj/test_schema_dispatch.py::test_schema_version_supported` & `test_yaml_adapter.py::test_canonical_key_ordering` prove schema_version is required and emitted as the first key. |
| **TOOL-PRJ-070** | User source/config referenced by relative POSIX paths; relocation safe | `src/ectt/prj/paths.py` (`validate_project_path`) | `tests/prj/test_paths.py` & `tests/prj/test_project.py::test_project_relocation` prove absolute/escaping path rejection and invariant resolution across tree relocation. |
| **TOOL-UIX-320** | All project and environment state stored in plain-text version-controllable files | `src/ectt/prj/project.py` (`Project.save_file`) | `tests/prj/test_project.py::test_project_create_and_no_metadata_leak` proves all configuration is serialized to plain-text Git-diffable YAML files without transient metadata. |
| **TOOL-CIC-080** | All tool configuration expressible in version-controlled files, not local GUI state | `src/ectt/prj/project.py` (`Project.create`, `Project.open`) | `tests/prj/test_project.py::test_project_relocation` proves full project configuration and authored scopes load identically from disk in headless execution contexts. |
