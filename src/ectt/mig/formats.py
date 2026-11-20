# implements: TOOL-MIG-100
"""Interchange format reference (WP-MIG-03, DSN-MIG-080).

TOOL-MIG-100: every interchange format the tool consumes or produces is
documented to a level permitting independent implementation. Prose that nobody
runs goes stale, so the documentation here is **executable**: each format has a
:class:`FormatSpec` carrying its grammar, versioning rule, error handling, loss
policy and a worked example, and :func:`check_format_documentation` is the
inspection checklist as code:

* every required documentation field is present;
* the documented version equals the version the code actually reads or writes;
* the worked example is accepted by the format's own reader;
* a published schema file exists, is valid JSON and declares ``$schema``;
* a format has an example or a schema (a bare name is not documentation).

:func:`render_format_reference` renders the registry as one deterministic
Markdown document, so a published reference cannot drift from the code.

Formats the tool does not yet read or write are not listed; adding a format
means adding its :class:`FormatSpec` (the coverage test in ``tests/mig`` lists
the expected set).
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import resources
from typing import Any

from ectt.core.determinism import FixedClock
from ectt.mig.errors import MigError

__all__ = [
    "DIRECTIONS",
    "INTERCHANGE_FORMATS",
    "MEDIA",
    "FormatSpec",
    "check_format_documentation",
    "format_by_id",
    "render_format_reference",
]

DIRECTIONS: tuple[str, ...] = ("consumed", "produced", "both")
MEDIA: tuple[str, ...] = ("csv", "json", "text", "xml", "yaml")

_CLOCK_TEXT = "2026-11-19T00:00:00+00:00"


@dataclass(frozen=True)
class FormatSpec:
    """Documentation of one interchange format, with executable evidence."""

    format_id: str
    title: str
    direction: str
    media: str
    version: str  # "unversioned" when the format carries no version
    implemented_in: str
    grammar: str
    versioning: str
    error_handling: str
    loss_policy: str
    example: Callable[[], str] | None = None
    reader: Callable[[str], object] | None = None
    version_probe: Callable[[], str] | None = None
    schema: tuple[str, str] | None = None  # (package, resource path)


# --- worked examples (real emitted output wherever the tool has a writer) ------------------


def _result_set() -> Any:
    from ectt.exh.results import ExecutionMetadata, ResultSet, finalize_result

    return ResultSet(
        run_id="run-1",
        execution=ExecutionMetadata(where="ci-runner", toolchain="gcc"),
        results=(finalize_result("t.a", "pass", "ta" * 12), finalize_result("t.b", "pass", "tb" * 12)),
        partial=False,
    )


def _case() -> Any:
    from ectt.tcm.datacases import (
        DataDrivenTestCase,
        StubSpec,
        TestCaseExpected,
        TestCaseInputs,
        refresh_digest,
    )

    return refresh_digest(
        DataDrivenTestCase(
            case_id="adc.scale.zero",
            unit="src/adc.c",
            function="adc_scale",
            inputs=TestCaseInputs(parameters={"raw": "0"}, global_inits={"g_gain": "2"}),
            expected=TestCaseExpected(return_value="0"),
            stubs=(StubSpec(name="hal_read", mode="sequence", returns=("5", "6"), expect_calls="2"),),
            requirements=("TOOL-X-1",),
            suites=("smoke",),
        )
    )


def _tests_file_example() -> str:
    from ectt.tcm.datacases import TestCasesFile, dump_test_cases_document

    return dump_test_cases_document(TestCasesFile(schema_version=1, cases=(_case(),)))


def _tests_file_reader(text: str) -> object:
    from ectt.prj.yaml_adapter import RestrictedYamlAdapter
    from ectt.tcm.datacases import parse_test_cases_document

    return parse_test_cases_document(RestrictedYamlAdapter().load(text))


def _csv_example() -> str:
    from ectt.tcm.interchange import export_cases

    return str(export_cases([_case()]).text)


def _csv_reader(text: str) -> object:
    from ectt.tcm.interchange import import_cases

    return import_cases(text)


def _open_export_example() -> str:
    from ectt.rep.open_export import build_open_export, dump_open_export

    return dump_open_export(build_open_export(result_set=_result_set(), cases=[_case()], clock=FixedClock(_CLOCK_TEXT)))


def _open_export_reader(text: str) -> object:
    from ectt.rep.open_export import load_open_export

    return load_open_export(text)


def _report_example() -> str:
    from ectt.rep.model import build_report_model, dump_report_model

    return dump_report_model(build_report_model(_result_set(), clock=FixedClock(_CLOCK_TEXT)))


def _report_reader(text: str) -> object:
    from ectt.rep.model import load_report_model

    return load_report_model(text)


def _analysis_example() -> str:
    from ectt.ana.model import (
        AnalysisModel,
        AnalysisUnit,
        FunctionModel,
        ProvenanceModel,
        SourceLocation,
        TypeModel,
    )

    function = FunctionModel(
        name="adc_scale",
        linkage="external",
        storage_class="none",
        location=SourceLocation("src/adc.c", 12),
        return_type="ref:type.int",
    )
    unit = AnalysisUnit(path="src/adc.c", status="parsed", functions=(function,))
    model = AnalysisModel(
        provenance=ProvenanceModel("0.1.0", "libclang 18.1.8", "2026-11-19T00:00:00+00:00"),
        units=(unit,),
        types={"type.int": TypeModel(kind="builtin", name="int", size=4)},
    )
    return model.to_json()


def _analysis_reader(text: str) -> object:
    from ectt.ana.persist import read_analysis_model

    return read_analysis_model(text)


def _analysis_version() -> str:
    from ectt.ana.persist import SCHEMA_VERSION_CURRENT

    return str(SCHEMA_VERSION_CURRENT)


def _reqif_example() -> str:
    from ectt.trc import AssociationSet, RequirementRecord, build_matrix, export_reqif

    associations = AssociationSet()
    associations.add("REQ-1", "t.a")
    return export_reqif(
        build_matrix(associations, {"t.a": "pass"}),
        [RequirementRecord("REQ-1", "Scaling", "The tool shall scale readings.")],
        creation_time=_CLOCK_TEXT,
    )


def _reqif_reader(text: str) -> object:
    from ectt.trc import import_reqif

    return import_reqif(text)


def _reqif_version() -> str:
    root = ET.fromstring(_reqif_example())
    element = next((e for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "REQ-IF-VERSION"), None)
    return (element.text or "") if element is not None else ""


def _requirements_csv_reader(text: str) -> object:
    from ectt.trc import import_requirements_csv

    return import_requirements_csv(text)


def _requirements_text_reader(text: str) -> object:
    from ectt.trc import import_requirements_text

    return import_requirements_text(text)


_MAPPED_CSV_MAPPING = {"Case": "id", "Module": "unit", "Func": "function", "Arg x": "input:x", "Want": "expect_return"}


def _mapped_csv_reader(text: str) -> object:
    from ectt.mig.csv_import import import_mapped_csv

    result = import_mapped_csv(text, _MAPPED_CSV_MAPPING)
    if result.rejected:
        raise MigError(f"example rows rejected: {[r.reason for r in result.rejected]}", reason="example_rejected")
    return result


def _ceedling_reader(text: str) -> object:
    from ectt.prj.yaml_adapter import RestrictedYamlAdapter

    config = RestrictedYamlAdapter().load(text)
    if ":paths" not in config:
        raise MigError("example has no :paths: section", reason="example_invalid")
    return config


def _fidelity_example() -> str:
    from ectt.mig.csv_import import import_mapped_csv
    from ectt.mig.fidelity import build_csv_fidelity_report, dump_fidelity_report

    result = import_mapped_csv(_MAPPED_CSV_EXAMPLE, _MAPPED_CSV_MAPPING, deferred_columns={"Slot": "slot"})
    return dump_fidelity_report(build_csv_fidelity_report("spreadsheet.csv", result))


def _fidelity_reader(text: str) -> object:
    from ectt.mig.fidelity import check_fidelity_report, load_fidelity_report

    report = load_fidelity_report(text)
    problems = check_fidelity_report(report)
    if problems:
        raise MigError(f"example report is inconsistent: {problems}", reason="example_invalid")
    return report


def _fidelity_version() -> str:
    from ectt.mig.fidelity import FIDELITY_REPORT_VERSION

    return FIDELITY_REPORT_VERSION


def _links_example() -> str:
    from ectt.trc import SourceLink, dump_source_links

    return dump_source_links([SourceLink("REQ-1", "src/adc.c", function="adc_scale")])


def _links_reader(text: str) -> object:
    from ectt.trc import load_source_links

    return load_source_links(text)


def _links_version() -> str:
    from ectt.trc.source_links import SOURCE_LINKS_VERSION

    return SOURCE_LINKS_VERSION


def _baseline_example() -> str:
    from ectt.trc import RequirementRecord, dump_baseline, record_baseline

    return dump_baseline(record_baseline([RequirementRecord("REQ-1", "Scaling", "The tool shall scale readings.")]))


def _baseline_reader(text: str) -> object:
    from ectt.trc import load_baseline

    return load_baseline(text)


def _baseline_version() -> str:
    from ectt.trc.change_detection import BASELINE_VERSION

    return BASELINE_VERSION


def _unity_reader(text: str) -> object:
    from ectt.mig.existing_suites import parse_unity_output

    records, unrecognised = parse_unity_output(text)
    if unrecognised or not records:
        raise MigError("example Unity stream not fully recognised", reason="example_invalid")
    return records


def _cmocka_reader(text: str) -> object:
    from ectt.mig.existing_suites import parse_cmocka_output

    records, _context = parse_cmocka_output(text)  # RUN/LINE/summary lines are reported context
    if not records:
        raise MigError("example cmocka stream yields no verdict", reason="example_invalid")
    return records


def _csv_version() -> str:
    from ectt.tcm.interchange import INTERCHANGE_VERSION

    return INTERCHANGE_VERSION


def _tests_file_version() -> str:
    from ectt.tcm.datacases import TEST_CASES_KIND

    return str(TEST_CASES_KIND.max_version)


def _open_export_version() -> str:
    from ectt.rep.open_export import OPEN_EXPORT_SCHEMA_VERSION

    return OPEN_EXPORT_SCHEMA_VERSION


def _report_version() -> str:
    from ectt.rep.model import REPORT_MODEL_SCHEMA_VERSION

    return REPORT_MODEL_SCHEMA_VERSION


_MAPPED_CSV_EXAMPLE = "Case,Module,Func,Arg x,Want,Slot\nc1,src/adc.c,adc_scale,0,0,\nc2,src/adc.c,adc_scale,9,9,2\n"

_REQUIREMENTS_CSV_EXAMPLE = "id,title,text\nREQ-1,Scaling,The tool shall scale readings.\nREQ-2,Range,The tool shall clamp.\n"
_REQUIREMENTS_TEXT_EXAMPLE = "# one requirement per line: ID: title\nREQ-1: Scaling\nREQ-2: Range\n"
_CEEDLING_EXAMPLE = ":project:\n  :build_root: build\n:paths:\n  :test:\n    - test/**\n  :source:\n    - src/**\n"
_UNITY_EXAMPLE = "src/test_adc.c:12:test_zero:PASS\nsrc/test_adc.c:20:test_full:FAIL: Expected 4095 Was 4094\nsrc/test_adc.c:30:test_later:IGNORE\n"
_CMOCKA_EXAMPLE = "[ RUN      ] test_zero\n[       OK ] test_zero\n"


INTERCHANGE_FORMATS: tuple[FormatSpec, ...] = (
    FormatSpec(
        "tests-file",
        "Data-driven test cases file (*.tests)",
        "both",
        "yaml",
        "1",
        "ectt.tcm.datacases",
        "Restricted YAML, one document, root mapping with `schema_version` (string) and `test_cases` (list). Each case has `id`, `unit`, "
        "`function` (non-empty strings) and optional `origin`, `requirements`, `suites`, `robustness`, `inputs` (`parameters`, `globals`), "
        "`expected` (`return`, `globals`, `out_parameters`, `comparison`), `stubs` (name -> `mode`, `returns`, `expect_calls`, "
        "`out_parameters`) and `digest`. Every scalar is a string. Aliases, anchors, tags, merge keys, duplicate keys and non-string keys are rejected.",
        "`schema_version` selects the reader; an older version is read, a newer one is refused with a named error. Content digest binds each case (D-02).",
        "A malformed document, unknown key, missing required field or unsupported version raises a named project error carrying path and line where known.",
        "Lossless within the model; YAML comments are not preserved on rewrite and a save over a file containing comments is refused unless discarding is requested.",
        _tests_file_example,
        _tests_file_reader,
        _tests_file_version,
    ),
    FormatSpec(
        "test-case-csv",
        "Test case interchange (CSV)",
        "both",
        "csv",
        "1",
        "ectt.tcm.interchange",
        "CSV with a fixed header whose first column is `ectt_interchange_version`; the column set is `ectt.tcm.interchange.COLUMNS`. "
        "List-valued fields are `;`-joined; mapping-valued fields are canonical JSON cells. Rows are sorted by id; LF line endings.",
        "The version column states the format version; the reader refuses other versions and validates the column set strictly.",
        "A missing or unknown column, a malformed row, a duplicate id or an unparseable cell is a named error; rows whose recorded digest no longer matches are reported.",
        "Content the format cannot express (non-schema keys, `;` inside list fields) is reported as an explicit per-case loss, never dropped silently.",
        _csv_example,
        _csv_reader,
        _csv_version,
    ),
    FormatSpec(
        "open-result-export",
        "Reconstructable open result export (JSON)",
        "both",
        "json",
        "1.0",
        "ectt.rep.open_export",
        "One JSON object: `schema_version`, `export_id`, `result_set` (S3 exchange dictionary), `test_cases_csv` (the test-case-csv text), "
        "`test_case_losses`, `provenance` (tool version, input digests, its own digest). Published JSON Schema, draft 2020-12, `additionalProperties: false`.",
        "`schema_version` must equal the published version; a different version is refused (`incompatible_schema_version`).",
        "Tampering with any section or the id fails digest verification on load; unknown versions are refused. Coverage is deliberately absent.",
        "Case-interchange losses travel verbatim in `test_case_losses`; nothing is dropped silently.",
        _open_export_example,
        _open_export_reader,
        _open_export_version,
        ("ectt.rep", "schema/open-result-1.0.schema.json"),
    ),
    FormatSpec(
        "report-model",
        "Persisted report model (JSON)",
        "both",
        "json",
        "1.1",
        "ectt.rep.model",
        "One JSON object: `schema_version`, `report_id` (digest of the canonical body), `run_id`, `generated_at`, `partial`, `tests` (`test_id`, "
        "`status`, `digest`), `coverage` (`unit`, `covered`, `total`), and for 1.1 `provenance` (required) and `execution` (optional; absent for merged reports).",
        "The reader accepts every version in `SUPPORTED_FORMAT_VERSIONS` and refuses others; 1.0 documents must not carry `execution` or `provenance`.",
        "A stored `report_id` that does not match the recomputed digest, an unknown status, a duplicate entry or a missing required field is a named error.",
        "Lossless; the report id binds every field, so a silent edit is detected.",
        _report_example,
        _report_reader,
        _report_version,
    ),
    FormatSpec(
        "analysis-model",
        "Analysis model S1 (JSON)",
        "both",
        "json",
        "1.4",
        "ectt.ana.persist",
        "One JSON object with `schema_version` first, `provenance`, `units` (path, status, diagnostics, functions, unsupported constructs), `types`, "
        "`capabilities`, `decision_inventory`. One published JSON Schema per version under `ectt/ana/schema`.",
        "Minor versions are additive: an older minor is read with its documented defaults, a newer minor is read ignoring unknown fields, a different major is refused.",
        "A document missing a field required by its declared version, an unknown inventory status or an incompatible major version is a named error.",
        "Constructs the analyser cannot model are recorded in the unsupported-construct inventory per unit, never omitted silently.",
        _analysis_example,
        _analysis_reader,
        _analysis_version,
        ("ectt.ana.schema", "analysis-model-1.4.schema.json"),
    ),
    FormatSpec(
        "reqif",
        "ReqIF 1.2 requirements and traceability",
        "both",
        "xml",
        "1.2",
        "ectt.trc.imports, ectt.trc.reqif_export",
        "ReqIF 1.2 structure. Export: header, string datatype, object types (requirement, test case), relation and specification types, one SPEC-OBJECT per "
        "requirement and linked test, one SPEC-RELATION per unique (requirement, test) pair, one SPECIFICATION. Requirement id in the `ReqIF.Identifier` attribute; "
        "title in `LONG-NAME`; text in `ReqIF.Description`. Import reads SPEC-OBJECTs, skipping objects of type `ectt.type.TestCase`.",
        "The header carries `REQ-IF-VERSION`; import reads the documented subset of ReqIF 1.x, matching by local name.",
        "Non-well-formed XML, a SPEC-OBJECT with no identifier, an invalid or duplicate requirement id is refused naming the location. Export refuses text XML cannot carry.",
        "Export carries requirements, tests, verdicts and links; it does not carry coverage. Import keeps id, title and text only.",
        _reqif_example,
        _reqif_reader,
        _reqif_version,
    ),
    FormatSpec(
        "requirements-csv",
        "Requirements import (CSV)",
        "consumed",
        "csv",
        "unversioned",
        "ectt.trc.imports",
        "CSV with a header row naming columns from `id` (required), `title`, `text` (optional); order free; no other columns.",
        "Unversioned; the column set is the contract.",
        "A missing `id` column, an unknown column, an invalid or duplicate id is refused naming the row.",
        "Import keeps id, title and text.",
        lambda: _REQUIREMENTS_CSV_EXAMPLE,
        _requirements_csv_reader,
    ),
    FormatSpec(
        "requirements-text",
        "Requirements import (plain text)",
        "consumed",
        "text",
        "unversioned",
        "ectt.trc.imports",
        "One requirement per non-blank line as `ID: title`; lines starting with `#` are comments; the id has no whitespace or colon.",
        "Unversioned.",
        "A line without a colon, an invalid or duplicate id is refused naming the line.",
        "The text format carries id and title only; text stays empty.",
        lambda: _REQUIREMENTS_TEXT_EXAMPLE,
        _requirements_text_reader,
    ),
    FormatSpec(
        "mapped-csv",
        "Column-mapped test data import (CSV, TSV, pipe, semicolon)",
        "consumed",
        "csv",
        "unversioned",
        "ectt.mig.csv_import",
        "Delimited text with a header row plus a caller-supplied mapping of source column to target (`id`, `unit`, `function`, `requirements`, `suites`, "
        "`expect_return`, `input:<name>`, `global_init:<name>`, `expect_global:<name>`, `expect_out:<name>`, `stub:<fn>:mode|returns|expect_calls|out:<name>`). "
        "`id`, `unit`, `function` must be mapped. Delimiters: comma, semicolon, tab, pipe.",
        "Unversioned; the mapping is data supplied with each import.",
        "Empty input, duplicate headers, an unknown mapped column or target is refused; a bad row is rejected with its row number and reason, never guessed.",
        "Every row is converted or rejected with a reason; unmapped columns and dropped cells are reported; slot columns declared deferred are never flattened.",
        lambda: _MAPPED_CSV_EXAMPLE.split("\n", 1)[0] + "\n" + _MAPPED_CSV_EXAMPLE.split("\n")[1] + "\n",
        _mapped_csv_reader,
    ),
    FormatSpec(
        "ceedling-project",
        "Ceedling project file (project.yml)",
        "consumed",
        "yaml",
        "unversioned",
        "ectt.mig.ceedling",
        "Ceedling's own `project.yml` (restricted YAML: no aliases, anchors, tags or merge keys). Read sections: `:project` (`:test_file_prefix`), `:extension` "
        "(`:source`), `:paths` (`:test` entries with optional `+:`/`-:` and globs); every other section is preserved verbatim.",
        "Follows Ceedling; unversioned here.",
        "A missing, non-UTF-8, non-mapping or aliased project file, or a test path leaving the project root, is refused with a reason.",
        "Configuration is preserved verbatim; test files are registered by name, line and digest; parameterised rows, followed imports and duplicates are reported as unconverted.",
        lambda: _CEEDLING_EXAMPLE,
        _ceedling_reader,
    ),
    FormatSpec(
        "unity-output",
        "Unity test runner output",
        "consumed",
        "text",
        "unversioned",
        "ectt.mig.existing_suites",
        "Lines `file:line:test_name:PASS|FAIL|IGNORE[: message]`; a FAIL message of the form `Expected X Was Y` yields expected and actual values.",
        "Follows Unity's output; unversioned here.",
        "Unrecognised lines are reported; an empty stream yields no verdict, never a pass. The process exit status is never consulted.",
        "A FAIL without expected/actual detail is recorded as an error, not upgraded into a claim the stream cannot support.",
        lambda: _UNITY_EXAMPLE,
        _unity_reader,
    ),
    FormatSpec(
        "cmocka-output",
        "cmocka test runner output",
        "consumed",
        "text",
        "unversioned",
        "ectt.mig.existing_suites",
        "Verdict lines `[       OK ] name` (cmocka's own spelling; `[  OKAY    ] name` is accepted as an alias) and `[  FAILED  ] name`. "
        "`[ RUN      ]`, `[   LINE   ] file:line: message` and summary lines are context: reported as unrecognised, not parsed.",
        "Follows cmocka's output; unversioned here.",
        "Unrecognised lines are reported; an empty stream yields no verdict.",
        "cmocka's default stream carries no expected/actual values; failures are recorded as errors with the framework's message.",
        lambda: _CMOCKA_EXAMPLE,
        _cmocka_reader,
    ),
    FormatSpec(
        "fidelity-report",
        "Import fidelity report (JSON)",
        "both",
        "json",
        "1",
        "ectt.mig.fidelity",
        "One JSON object: `report_version`, `source`, `counts`, `artifacts` (artifact, kind, status `converted|converted_lossy|not_converted`, notes with "
        "`effect` `loss|info`), `deferred` (kind `slot|slot_iteration|slot_history`, artifact, location). Canonical key order.",
        "`report_version` must equal the published version; others are refused.",
        "An unknown status, effect or deferred kind, mismatched counts, or an inconsistency (a deferred structure whose artifact was converted) is a named error.",
        "The report is the loss account of an import; it records what was converted, lost or deferred.",
        _fidelity_example,
        _fidelity_reader,
        _fidelity_version,
    ),
    FormatSpec(
        "source-links",
        "Requirement-to-source links (JSON)",
        "both",
        "json",
        "1",
        "ectt.trc.source_links",
        "One JSON object: `links_version`, `links` (list of `requirement_id`, `unit`, and either `function` or `start_line` and `end_line`). Persist the anchored (function) form.",
        "`links_version` must equal the published version.",
        "Unknown fields, a link naming both or neither of function and range, or an invalid range is refused.",
        "A range link is persisted as the function containing it; links that do not resolve are reported, not kept as guesses.",
        _links_example,
        _links_reader,
        _links_version,
    ),
    FormatSpec(
        "review-baseline",
        "Requirement review baseline (JSON)",
        "both",
        "json",
        "1",
        "ectt.trc.change_detection",
        "One JSON object: `baseline_version`, `digests` (requirement id -> 64-hex SHA-256 of title and text, line endings normalised).",
        "`baseline_version` must equal the published version.",
        "A malformed digest, an invalid id or another version is refused.",
        "Lossless; a digest cannot be reversed to text.",
        _baseline_example,
        _baseline_reader,
        _baseline_version,
    ),
)

_REQUIRED_TEXT_FIELDS = ("grammar", "versioning", "error_handling", "loss_policy", "implemented_in", "title")


def format_by_id(format_id: str) -> FormatSpec:
    """Return the spec for ``format_id`` or raise :class:`MigError`."""
    for spec in INTERCHANGE_FORMATS:
        if spec.format_id == format_id:
            return spec
    raise MigError(f"unknown interchange format '{format_id}'", reason="unknown_format")


def _check_schema(spec: FormatSpec) -> list[str]:
    assert spec.schema is not None
    package, path = spec.schema
    try:
        text = (resources.files(package) / path).read_text(encoding="utf-8")
    except (OSError, ModuleNotFoundError) as exc:
        return [f"{spec.format_id}: published schema {package}/{path} cannot be read ({type(exc).__name__})"]
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        return [f"{spec.format_id}: published schema {package}/{path} is not valid JSON"]
    if not isinstance(doc, dict) or "$schema" not in doc:
        return [f"{spec.format_id}: published schema {package}/{path} does not declare $schema"]
    return []


def check_format_documentation(specs: Sequence[FormatSpec] = INTERCHANGE_FORMATS) -> list[str]:
    """The inspection checklist as code; returns the problems (empty when sound)."""
    problems: list[str] = []
    seen: set[str] = set()
    for spec in specs:
        name = spec.format_id
        if name in seen:
            problems.append(f"{name}: duplicate format id")
        seen.add(name)
        problems.extend(f"{name}: '{f}' is empty" for f in _REQUIRED_TEXT_FIELDS if not getattr(spec, f).strip())
        if spec.direction not in DIRECTIONS:
            problems.append(f"{name}: unknown direction '{spec.direction}'")
        if spec.media not in MEDIA:
            problems.append(f"{name}: unknown media '{spec.media}'")
        if spec.example is None and spec.schema is None:
            problems.append(f"{name}: has neither a worked example nor a published schema")
        if spec.direction in ("consumed", "both") and spec.reader is None:
            problems.append(f"{name}: is consumed but has no reader to check its example against")
        if spec.version_probe is not None:
            try:
                actual = spec.version_probe()
            except Exception as exc:  # noqa: BLE001 - any failure of a probe is a documentation defect to report
                problems.append(f"{name}: version probe failed ({type(exc).__name__}: {exc})")
            else:
                if actual != spec.version:
                    problems.append(f"{name}: documented version {spec.version!r} but the code uses {actual!r}")
        elif spec.version != "unversioned":
            problems.append(f"{name}: versioned format without a version probe")
        if spec.example is not None:
            try:
                text = spec.example()
                if not text.strip():
                    problems.append(f"{name}: worked example is empty")
                elif spec.reader is not None:
                    spec.reader(text)
            except Exception as exc:  # noqa: BLE001 - any reader failure is a documentation defect to report
                problems.append(f"{name}: worked example rejected by its reader ({type(exc).__name__}: {exc})")
        if spec.schema is not None:
            problems.extend(_check_schema(spec))
    return problems


def render_format_reference(specs: Sequence[FormatSpec] = INTERCHANGE_FORMATS) -> str:
    """Render the registry as one deterministic Markdown reference document."""
    lines = [
        "# Interchange format reference",
        "",
        "Every format the tool consumes or produces (TOOL-MIG-100). Generated from the format registry in",
        "`ectt.mig.formats`; examples are accepted by each format's own reader (`check_format_documentation`).",
        "",
        "| Format | Direction | Media | Version |",
        "|---|---|---|---|",
    ]
    ordered = sorted(specs, key=lambda s: s.format_id)
    lines.extend(f"| `{s.format_id}` | {s.direction} | {s.media} | {s.version} |" for s in ordered)
    for spec in ordered:
        lines += ["", f"## {spec.title} (`{spec.format_id}`)", ""]
        lines += [f"- **Direction:** {spec.direction}", f"- **Media:** {spec.media}", f"- **Version:** {spec.version}"]
        lines += [f"- **Implemented in:** `{spec.implemented_in}`"]
        if spec.schema is not None:
            lines.append(f"- **Published schema:** `{spec.schema[0]}` / `{spec.schema[1]}`")
        lines += ["", "**Grammar.** " + spec.grammar, "", "**Versioning.** " + spec.versioning]
        lines += ["", "**Errors.** " + spec.error_handling, "", "**Loss.** " + spec.loss_policy]
        if spec.example is not None:
            example = spec.example().rstrip("\n")
            lines += ["", "**Example.**", "", f"```{spec.media}", example, "```"]
    return "\n".join(lines) + "\n"
