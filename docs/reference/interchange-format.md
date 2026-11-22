# Interchange format reference

Every format the tool consumes or produces (TOOL-MIG-100). Generated from the format registry in
`ectt.mig.formats`; examples are accepted by each format's own reader (`check_format_documentation`).

| Format | Direction | Media | Version |
|---|---|---|---|
| `analysis-model` | both | json | 1.5 |
| `ceedling-project` | consumed | yaml | unversioned |
| `cmocka-output` | consumed | text | unversioned |
| `fidelity-report` | both | json | 1 |
| `mapped-csv` | consumed | csv | unversioned |
| `open-result-export` | both | json | 1.0 |
| `report-model` | both | json | 1.1 |
| `reqif` | both | xml | 1.0 |
| `requirements-csv` | consumed | csv | unversioned |
| `requirements-text` | consumed | text | unversioned |
| `review-baseline` | both | json | 1 |
| `source-links` | both | json | 1 |
| `test-case-csv` | both | csv | 1 |
| `tests-file` | both | yaml | 1 |
| `unity-output` | consumed | text | unversioned |

## Analysis model S1 (JSON) (`analysis-model`)

- **Direction:** both
- **Media:** json
- **Version:** 1.5
- **Implemented in:** `ectt.ana.persist`
- **Published schema:** `ectt.ana.schema` / `analysis-model-1.5.schema.json`

**Grammar.** One JSON object with `schema_version` first, `provenance`, `units` (path, status, diagnostics, functions, unsupported constructs), `types`, `capabilities`, `decision_inventory`. One published JSON Schema per version under `ectt/ana/schema`.

**Versioning.** Minor versions are additive: an older minor is read with its documented defaults, a newer minor is read ignoring unknown fields, a different major is refused.

**Errors.** A document missing a field required by its declared version, an unknown inventory status or an incompatible major version is a named error.

**Loss.** Constructs the analyser cannot model are recorded in the unsupported-construct inventory per unit, never omitted silently.

**Example.**

```json
{
  "schema_version": "1.2",
  "capabilities": {
    "cfg": false
  },
  "decision_inventory": {
    "status": "not_extracted"
  },
  "provenance": {
    "front_end": "libclang 18.1.8",
    "generated_at": "2026-11-19T00:00:00+00:00",
    "inputs": [],
    "tool_version": "0.1.0"
  },
  "types": {
    "type.int": {
      "kind": "builtin",
      "name": "int"
    }
  },
  "units": [
    {
      "cfg": null,
      "diagnostics": [],
      "functions": [
        {
          "calls": [],
          "globals": [],
          "linkage": "external",
          "location": {
            "file": "src/adc.c",
            "line": 12,
            "origin": "project"
          },
          "name": "adc_scale",
          "parameters": [],
          "return_type": "ref:type.int",
          "storage_class": "none"
        }
      ],
      "path": "src/adc.c",
      "status": "parsed",
      "unsupported_constructs": []
    }
  ]
}
```

## Ceedling project file (project.yml) (`ceedling-project`)

- **Direction:** consumed
- **Media:** yaml
- **Version:** unversioned
- **Implemented in:** `ectt.mig.ceedling`

**Grammar.** Ceedling's own `project.yml` (YAML; every plain scalar stays text; anchors and aliases, which Ceedling's template uses, are resolved and counted; no explicit tags, no duplicate keys). Read sections: `:project` (`:test_file_prefix`), `:extension` (`:source`), `:paths` (`:test` entries with optional `+:`/`-:` and globs); every other section is preserved verbatim.

**Versioning.** Follows Ceedling; unversioned here.

**Errors.** A missing, non-UTF-8, non-mapping or malformed project file, a duplicate key, a cyclic alias, aliases that expand beyond a fixed size, or a test path leaving the project root, is refused with a reason.

**Loss.** Configuration is preserved with aliases resolved (the anchors themselves are not preserved, and the count is reported as information); test files are registered by name, line and digest; parameterised rows, followed imports and duplicates are reported as unconverted.

**Example.**

```yaml
:project:
  :build_root: build
:paths:
  :test:
    - test/**
  :source:
    - src/**
:defines:
  :common: &common_defines []
  :test:
    - *common_defines
    - TEST
```

## cmocka test runner output (`cmocka-output`)

- **Direction:** consumed
- **Media:** text
- **Version:** unversioned
- **Implemented in:** `ectt.mig.existing_suites`

**Grammar.** Verdict lines `[       OK ] name` (cmocka's own spelling; `[  OKAY    ] name` is accepted as an alias) and `[  FAILED  ] name`. `[ RUN      ]`, `[   LINE   ] file:line: message` and summary lines are context: reported as unrecognised, not parsed.

**Versioning.** Follows cmocka's output; unversioned here.

**Errors.** Unrecognised lines are reported; an empty stream yields no verdict.

**Loss.** cmocka's default stream carries no expected/actual values; failures are recorded as errors with the framework's message.

**Example.**

```text
[ RUN      ] test_zero
[       OK ] test_zero
```

## Import fidelity report (JSON) (`fidelity-report`)

- **Direction:** both
- **Media:** json
- **Version:** 1
- **Implemented in:** `ectt.mig.fidelity`

**Grammar.** One JSON object: `report_version`, `source`, `counts`, `artifacts` (artifact, kind, status `converted|converted_lossy|not_converted`, notes with `effect` `loss|info`), `deferred` (kind `slot|slot_iteration|slot_history`, artifact, location). Canonical key order.

**Versioning.** `report_version` must equal the published version; others are refused.

**Errors.** An unknown status, effect or deferred kind, mismatched counts, or an inconsistency (a deferred structure whose artifact was converted) is a named error.

**Loss.** The report is the loss account of an import; it records what was converted, lost or deferred.

**Example.**

```json
{
  "artifacts": [
    {
      "artifact": "row 1",
      "kind": "csv_row",
      "notes": [],
      "status": "converted"
    },
    {
      "artifact": "row 2",
      "kind": "csv_row",
      "notes": [
        {
          "detail": "slot at column 'Slot'",
          "effect": "loss",
          "kind": "deferred_structure"
        }
      ],
      "status": "not_converted"
    }
  ],
  "counts": {
    "converted": 1,
    "converted_lossy": 0,
    "not_converted": 1
  },
  "deferred": [
    {
      "artifact": "row 2",
      "kind": "slot",
      "location": "row 2, column 'Slot'"
    }
  ],
  "report_version": "1",
  "source": "spreadsheet.csv"
}
```

## Column-mapped test data import (CSV, TSV, pipe, semicolon) (`mapped-csv`)

- **Direction:** consumed
- **Media:** csv
- **Version:** unversioned
- **Implemented in:** `ectt.mig.csv_import`

**Grammar.** Delimited text with a header row plus a caller-supplied mapping of source column to target (`id`, `unit`, `function`, `requirements`, `suites`, `expect_return`, `input:<name>`, `global_init:<name>`, `expect_global:<name>`, `expect_out:<name>`, `stub:<fn>:mode|returns|expect_calls|out:<name>`). `id`, `unit`, `function` must be mapped. Delimiters: comma, semicolon, tab, pipe.

**Versioning.** Unversioned; the mapping is data supplied with each import.

**Errors.** Empty input, duplicate headers, an unknown mapped column or target is refused; a bad row is rejected with its row number and reason, never guessed.

**Loss.** Every row is converted or rejected with a reason; unmapped columns and dropped cells are reported; slot columns declared deferred are never flattened.

**Example.**

```csv
Case,Module,Func,Arg x,Want,Slot
c1,src/adc.c,adc_scale,0,0,
```

## Reconstructable open result export (JSON) (`open-result-export`)

- **Direction:** both
- **Media:** json
- **Version:** 1.0
- **Implemented in:** `ectt.rep.open_export`
- **Published schema:** `ectt.rep` / `schema/open-result-1.0.schema.json`

**Grammar.** One JSON object: `schema_version`, `export_id`, `result_set` (S3 exchange dictionary), `test_cases_csv` (the test-case-csv text), `test_case_losses`, `provenance` (tool version, input digests, its own digest). Published JSON Schema, draft 2020-12, `additionalProperties: false`.

**Versioning.** `schema_version` must equal the published version; a different version is refused (`incompatible_schema_version`).

**Errors.** Tampering with any section or the id fails digest verification on load; unknown versions are refused. Coverage is deliberately absent.

**Loss.** Case-interchange losses travel verbatim in `test_case_losses`; nothing is dropped silently.

**Example.**

```json
{
  "schema_version": "1.0",
  "export_id": "b95f002339a2e517b0fae297305d6e232275af2e62cf0acae69a0b70a5ce3f4d",
  "provenance": {
    "build_id": "unset",
    "dependencies": {},
    "digest": "f37158e1d2fd48e4e8a49c74470163c0e0a1f5c66229c2dbf61bca643c3dbd39",
    "generated_at": "2026-11-19T00:00:00+00:00",
    "input_digests": {
      "result_set": "bf1620b66c2211b8e20d0a78420d515d5a3de1f9667d538017a4f975e940d4dc",
      "test_cases_csv": "405ddb22f8ec6762f211898830d323ab445690b9a8000d8267a731e1b907723f"
    },
    "python_version": "3.13.2",
    "schema_versions": {
      "open_export": "1.0",
      "result_set": "1.0",
      "test_case_interchange": "1"
    },
    "tool_version": "0.1.0"
  },
  "result_set": {
    "execution": {
      "toolchain": "gcc",
      "where": "ci-runner"
    },
    "infrastructure_faults": [],
    "not_executed": [],
    "partial": false,
    "results": [
      {
        "outcome": "pass",
        "test_digest": "tatatatatatatatatatatata",
        "test_id": "t.a"
      },
      {
        "outcome": "pass",
        "test_digest": "tbtbtbtbtbtbtbtbtbtbtbtb",
        "test_id": "t.b"
      }
    ],
    "run_id": "run-1",
    "schema_version": "1.0"
  },
  "test_case_losses": [],
  "test_cases_csv": "ectt_interchange_version,id,unit,function,origin_author,origin_engine,origin_model,origin_review_state,requirements,suites,robustness,input_parameters,input_globals,expected_return,expected_globals,expected_out_parameters,expected_comparison,stubs,digest\n1,adc.scale.zero,src/adc.c,adc_scale,human,,,,TOOL-X-1,smoke,false,\"{\n  \"\"raw\"\": \"\"0\"\"\n}\n\",\"{\n  \"\"g_gain\"\": \"\"2\"\"\n}\n\",0,{},{},{},\"{\n  \"\"hal_read\"\": {\n    \"\"expect_calls\"\": \"\"2\"\",\n    \"\"mode\"\": \"\"sequence\"\",\n    \"\"returns\"\": [\n      \"\"5\"\",\n      \"\"6\"\"\n    ]\n  }\n}\n\",566001b23e66ef971bfc6e538bbe8dec23a2c754c6d83c5ffe6227ba0cef9e52\n"
}
```

## Persisted report model (JSON) (`report-model`)

- **Direction:** both
- **Media:** json
- **Version:** 1.1
- **Implemented in:** `ectt.rep.model`

**Grammar.** One JSON object: `schema_version`, `report_id` (digest of the canonical body), `run_id`, `generated_at`, `partial`, `tests` (`test_id`, `status`, `digest`), `coverage` (`unit`, `covered`, `total`), and for 1.1 `provenance` (required) and `execution` (optional; absent for merged reports).

**Versioning.** The reader accepts every version in `SUPPORTED_FORMAT_VERSIONS` and refuses others; 1.0 documents must not carry `execution` or `provenance`.

**Errors.** A stored `report_id` that does not match the recomputed digest, an unknown status, a duplicate entry or a missing required field is a named error.

**Loss.** Lossless; the report id binds every field, so a silent edit is detected.

**Example.**

```json
{
  "schema_version": "1.1",
  "coverage": [],
  "execution": {
    "target_id": null,
    "toolchain": "gcc",
    "where": "ci-runner"
  },
  "generated_at": "2026-11-19T00:00:00+00:00",
  "partial": false,
  "provenance": {
    "build_id": "unset",
    "dependencies": {},
    "digest": "d0dec7485ec2bb26344ca46b61ea445168be200b0925399342cd3fe36e67b8b0",
    "generated_at": "2026-11-19T00:00:00+00:00",
    "input_digests": {
      "result_set": "dc720174bc67905109108a434934bbb42dbd7a3f2ab3b601123ab1ea10d019ae"
    },
    "python_version": "3.13.2",
    "schema_versions": {
      "report_model": "1.1",
      "result_set": "1.0"
    },
    "tool_version": "0.1.0"
  },
  "report_id": "25e2685cc6f9c9f33ea0dc501e73812b9bfee71bd89cf72b3f3ffd0417076e1e",
  "run_id": "run-1",
  "tests": [
    {
      "digest": "tatatatatatatatatatatata",
      "status": "pass",
      "test_id": "t.a"
    },
    {
      "digest": "tbtbtbtbtbtbtbtbtbtbtbtb",
      "status": "pass",
      "test_id": "t.b"
    }
  ]
}
```

## ReqIF requirements and traceability (`reqif`)

- **Direction:** both
- **Media:** xml
- **Version:** 1.0
- **Implemented in:** `ectt.trc.imports, ectt.trc.reqif_export`

**Grammar.** ReqIF as defined by the OMG schema `reqif.xsd` (namespace 20110401; the header's fixed `REQ-IF-VERSION` is 1.0). Export: header, string datatype, object types (requirement, test case), relation and specification types, one SPEC-OBJECT per requirement and linked test, one SPEC-RELATION per unique (requirement, test) pair, one SPECIFICATION. Requirement id in the `ReqIF.Identifier` attribute; title in `LONG-NAME`; text in `ReqIF.Description`. Import reads SPEC-OBJECTs, skipping objects of type `ectt.type.TestCase`.

**Versioning.** The header carries `REQ-IF-VERSION`; import reads the documented subset of ReqIF 1.x, matching by local name.

**Errors.** Non-well-formed XML, a SPEC-OBJECT with no identifier, an invalid or duplicate requirement id is refused naming the location. Export refuses text XML cannot carry.

**Loss.** Export carries requirements, tests, verdicts and links; it does not carry coverage. Import keeps id, title and text only.

**Example.**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<REQ-IF xmlns="http://www.omg.org/spec/ReqIF/20110401/reqif.xsd">
  <THE-HEADER>
    <REQ-IF-HEADER IDENTIFIER="h_34c7de52beab5ad10a4119472da4da60727b117eb1b404df2f627e8491b0522b">
      <CREATION-TIME>2026-11-19T00:00:00+00:00</CREATION-TIME>
      <REPOSITORY-ID>ectt</REPOSITORY-ID>
      <REQ-IF-TOOL-ID>ectt</REQ-IF-TOOL-ID>
      <REQ-IF-VERSION>1.0</REQ-IF-VERSION>
      <SOURCE-TOOL-ID>ectt</SOURCE-TOOL-ID>
      <TITLE>ectt traceability export</TITLE>
    </REQ-IF-HEADER>
  </THE-HEADER>
  <CORE-CONTENT>
    <REQ-IF-CONTENT>
      <DATATYPES>
        <DATATYPE-DEFINITION-STRING IDENTIFIER="ectt.datatype.String" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="String" MAX-LENGTH="100000" />
      </DATATYPES>
      <SPEC-TYPES>
        <SPEC-OBJECT-TYPE IDENTIFIER="ectt.type.Requirement" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Requirement">
          <SPEC-ATTRIBUTES>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ectt.req.attr.ReqIF.Identifier" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="ReqIF.Identifier">
              <TYPE>
                <DATATYPE-DEFINITION-STRING-REF>ectt.datatype.String</DATATYPE-DEFINITION-STRING-REF>
              </TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ectt.req.attr.ReqIF.Description" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="ReqIF.Description">
              <TYPE>
                <DATATYPE-DEFINITION-STRING-REF>ectt.datatype.String</DATATYPE-DEFINITION-STRING-REF>
              </TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ectt.req.attr.Verdict" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Verdict">
              <TYPE>
                <DATATYPE-DEFINITION-STRING-REF>ectt.datatype.String</DATATYPE-DEFINITION-STRING-REF>
              </TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
          </SPEC-ATTRIBUTES>
        </SPEC-OBJECT-TYPE>
        <SPEC-OBJECT-TYPE IDENTIFIER="ectt.type.TestCase" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Test case">
          <SPEC-ATTRIBUTES>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ectt.test.attr.ReqIF.Identifier" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="ReqIF.Identifier">
              <TYPE>
                <DATATYPE-DEFINITION-STRING-REF>ectt.datatype.String</DATATYPE-DEFINITION-STRING-REF>
              </TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ectt.test.attr.Status" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Status">
              <TYPE>
                <DATATYPE-DEFINITION-STRING-REF>ectt.datatype.String</DATATYPE-DEFINITION-STRING-REF>
              </TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
            <ATTRIBUTE-DEFINITION-STRING IDENTIFIER="ectt.test.attr.Unreviewed" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Unreviewed">
              <TYPE>
                <DATATYPE-DEFINITION-STRING-REF>ectt.datatype.String</DATATYPE-DEFINITION-STRING-REF>
              </TYPE>
            </ATTRIBUTE-DEFINITION-STRING>
          </SPEC-ATTRIBUTES>
        </SPEC-OBJECT-TYPE>
        <SPEC-RELATION-TYPE IDENTIFIER="ectt.type.Verifies" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="verified by" />
        <SPECIFICATION-TYPE IDENTIFIER="ectt.type.Specification" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Requirements" />
      </SPEC-TYPES>
      <SPEC-OBJECTS>
        <SPEC-OBJECT IDENTIFIER="r_2bd9496d18d96709ad381c99cd9ac64d3177887500e3fd1f2598da80eada48ca" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Scaling">
          <TYPE>
            <SPEC-OBJECT-TYPE-REF>ectt.type.Requirement</SPEC-OBJECT-TYPE-REF>
          </TYPE>
          <VALUES>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="REQ-1">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>ectt.req.attr.ReqIF.Identifier</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="The tool shall scale readings.">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>ectt.req.attr.ReqIF.Description</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="pass">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>ectt.req.attr.Verdict</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
          </VALUES>
        </SPEC-OBJECT>
        <SPEC-OBJECT IDENTIFIER="t_3027a434ac4b271ffc1b1c5082517b9ee10de98999d8104328001fec706f73aa" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="t.a">
          <TYPE>
            <SPEC-OBJECT-TYPE-REF>ectt.type.TestCase</SPEC-OBJECT-TYPE-REF>
          </TYPE>
          <VALUES>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="t.a">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>ectt.test.attr.ReqIF.Identifier</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="pass">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>ectt.test.attr.Status</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
            <ATTRIBUTE-VALUE-STRING THE-VALUE="false">
              <DEFINITION>
                <ATTRIBUTE-DEFINITION-STRING-REF>ectt.test.attr.Unreviewed</ATTRIBUTE-DEFINITION-STRING-REF>
              </DEFINITION>
            </ATTRIBUTE-VALUE-STRING>
          </VALUES>
        </SPEC-OBJECT>
      </SPEC-OBJECTS>
      <SPEC-RELATIONS>
        <SPEC-RELATION IDENTIFIER="x_9fd90d623d792ddcc89badde6928f727aee9091a0da61163112f803962f383e8" LAST-CHANGE="2026-11-19T00:00:00+00:00">
          <TYPE>
            <SPEC-RELATION-TYPE-REF>ectt.type.Verifies</SPEC-RELATION-TYPE-REF>
          </TYPE>
          <SOURCE>
            <SPEC-OBJECT-REF>r_2bd9496d18d96709ad381c99cd9ac64d3177887500e3fd1f2598da80eada48ca</SPEC-OBJECT-REF>
          </SOURCE>
          <TARGET>
            <SPEC-OBJECT-REF>t_3027a434ac4b271ffc1b1c5082517b9ee10de98999d8104328001fec706f73aa</SPEC-OBJECT-REF>
          </TARGET>
        </SPEC-RELATION>
      </SPEC-RELATIONS>
      <SPECIFICATIONS>
        <SPECIFICATION IDENTIFIER="s_3f5315db90e670842e800cfb49974fdb74ec824a3b06af8067d598bf4f01c7e7" LAST-CHANGE="2026-11-19T00:00:00+00:00" LONG-NAME="Requirements">
          <TYPE>
            <SPECIFICATION-TYPE-REF>ectt.type.Specification</SPECIFICATION-TYPE-REF>
          </TYPE>
          <CHILDREN>
            <SPEC-HIERARCHY IDENTIFIER="p_25d9ed0da05e9f83303fa59dff97f94de5aaa33e7131db887db525165496d52e" LAST-CHANGE="2026-11-19T00:00:00+00:00">
              <OBJECT>
                <SPEC-OBJECT-REF>r_2bd9496d18d96709ad381c99cd9ac64d3177887500e3fd1f2598da80eada48ca</SPEC-OBJECT-REF>
              </OBJECT>
            </SPEC-HIERARCHY>
          </CHILDREN>
        </SPECIFICATION>
      </SPECIFICATIONS>
    </REQ-IF-CONTENT>
  </CORE-CONTENT>
</REQ-IF>
```

## Requirements import (CSV) (`requirements-csv`)

- **Direction:** consumed
- **Media:** csv
- **Version:** unversioned
- **Implemented in:** `ectt.trc.imports`

**Grammar.** CSV with a header row naming columns from `id` (required), `title`, `text` (optional); order free; no other columns.

**Versioning.** Unversioned; the column set is the contract.

**Errors.** A missing `id` column, an unknown column, an invalid or duplicate id is refused naming the row.

**Loss.** Import keeps id, title and text.

**Example.**

```csv
id,title,text
REQ-1,Scaling,The tool shall scale readings.
REQ-2,Range,The tool shall clamp.
```

## Requirements import (plain text) (`requirements-text`)

- **Direction:** consumed
- **Media:** text
- **Version:** unversioned
- **Implemented in:** `ectt.trc.imports`

**Grammar.** One requirement per non-blank line as `ID: title`; lines starting with `#` are comments; the id has no whitespace or colon.

**Versioning.** Unversioned.

**Errors.** A line without a colon, an invalid or duplicate id is refused naming the line.

**Loss.** The text format carries id and title only; text stays empty.

**Example.**

```text
# one requirement per line: ID: title
REQ-1: Scaling
REQ-2: Range
```

## Requirement review baseline (JSON) (`review-baseline`)

- **Direction:** both
- **Media:** json
- **Version:** 1
- **Implemented in:** `ectt.trc.change_detection`

**Grammar.** One JSON object: `baseline_version`, `digests` (requirement id -> 64-hex SHA-256 of title and text, line endings normalised).

**Versioning.** `baseline_version` must equal the published version.

**Errors.** A malformed digest, an invalid id or another version is refused.

**Loss.** Lossless; a digest cannot be reversed to text.

**Example.**

```json
{
  "baseline_version": "1",
  "digests": {
    "REQ-1": "d4d9f215a53d9bbb9540350a9ac160d705fdea3e55773b322e4036a1c92571f7"
  }
}
```

## Requirement-to-source links (JSON) (`source-links`)

- **Direction:** both
- **Media:** json
- **Version:** 1
- **Implemented in:** `ectt.trc.source_links`

**Grammar.** One JSON object: `links_version`, `links` (list of `requirement_id`, `unit`, and either `function` or `start_line` and `end_line`). Persist the anchored (function) form.

**Versioning.** `links_version` must equal the published version.

**Errors.** Unknown fields, a link naming both or neither of function and range, or an invalid range is refused.

**Loss.** A range link is persisted as the function containing it; links that do not resolve are reported, not kept as guesses.

**Example.**

```json
{
  "links": [
    {
      "function": "adc_scale",
      "requirement_id": "REQ-1",
      "unit": "src/adc.c"
    }
  ],
  "links_version": "1"
}
```

## Test case interchange (CSV) (`test-case-csv`)

- **Direction:** both
- **Media:** csv
- **Version:** 1
- **Implemented in:** `ectt.tcm.interchange`

**Grammar.** CSV with a fixed header whose first column is `ectt_interchange_version`; the column set is `ectt.tcm.interchange.COLUMNS`. List-valued fields are `;`-joined; mapping-valued fields are canonical JSON cells. Rows are sorted by id; LF line endings.

**Versioning.** The version column states the format version; the reader refuses other versions and validates the column set strictly.

**Errors.** A missing or unknown column, a malformed row, a duplicate id or an unparseable cell is a named error; rows whose recorded digest no longer matches are reported.

**Loss.** Content the format cannot express (non-schema keys, `;` inside list fields) is reported as an explicit per-case loss, never dropped silently.

**Example.**

```csv
ectt_interchange_version,id,unit,function,origin_author,origin_engine,origin_model,origin_review_state,requirements,suites,robustness,input_parameters,input_globals,expected_return,expected_globals,expected_out_parameters,expected_comparison,stubs,digest
1,adc.scale.zero,src/adc.c,adc_scale,human,,,,TOOL-X-1,smoke,false,"{
  ""raw"": ""0""
}
","{
  ""g_gain"": ""2""
}
",0,{},{},{},"{
  ""hal_read"": {
    ""expect_calls"": ""2"",
    ""mode"": ""sequence"",
    ""returns"": [
      ""5"",
      ""6""
    ]
  }
}
",566001b23e66ef971bfc6e538bbe8dec23a2c754c6d83c5ffe6227ba0cef9e52
```

## Data-driven test cases file (*.tests) (`tests-file`)

- **Direction:** both
- **Media:** yaml
- **Version:** 1
- **Implemented in:** `ectt.tcm.datacases`

**Grammar.** Restricted YAML, one document, root mapping with `schema_version` (string) and `test_cases` (list). Each case has `id`, `unit`, `function` (non-empty strings) and optional `origin`, `requirements`, `suites`, `robustness`, `inputs` (`parameters`, `globals`), `expected` (`return`, `globals`, `out_parameters`, `comparison`), `stubs` (name -> `mode`, `returns`, `expect_calls`, `out_parameters`) and `digest`. Every scalar is a string. Aliases, anchors, tags, merge keys, duplicate keys and non-string keys are rejected.

**Versioning.** `schema_version` selects the reader; an older version is read, a newer one is refused with a named error. Content digest binds each case (D-02).

**Errors.** A malformed document, unknown key, missing required field or unsupported version raises a named project error carrying path and line where known.

**Loss.** Lossless within the model; YAML comments are not preserved on rewrite and a save over a file containing comments is refused unless discarding is requested.

**Example.**

```yaml
"schema_version": "1"
"test_cases":
  - "digest": "566001b23e66ef971bfc6e538bbe8dec23a2c754c6d83c5ffe6227ba0cef9e52"
    "expected":
      "return": "0"
    "function": "adc_scale"
    "id": "adc.scale.zero"
    "inputs":
      "globals":
        "g_gain": "2"
      "parameters":
        "raw": "0"
    "origin":
      "author": "human"
    "requirements":
      - "TOOL-X-1"
    "stubs":
      "hal_read":
        "expect_calls": "2"
        "mode": "sequence"
        "returns":
          - "5"
          - "6"
    "suites":
      - "smoke"
    "unit": "src/adc.c"
```

## Unity test runner output (`unity-output`)

- **Direction:** consumed
- **Media:** text
- **Version:** unversioned
- **Implemented in:** `ectt.mig.existing_suites`

**Grammar.** Lines `file:line:test_name:PASS|FAIL|IGNORE[: message]`; a FAIL message of the form `Expected X Was Y` yields expected and actual values.

**Versioning.** Follows Unity's output; unversioned here.

**Errors.** Unrecognised lines are reported; an empty stream yields no verdict, never a pass. The process exit status is never consulted.

**Loss.** A FAIL without expected/actual detail is recorded as an error, not upgraded into a claim the stream cannot support.

**Example.**

```text
src/test_adc.c:12:test_zero:PASS
src/test_adc.c:20:test_full:FAIL: Expected 4095 Was 4094
src/test_adc.c:30:test_later:IGNORE
```
