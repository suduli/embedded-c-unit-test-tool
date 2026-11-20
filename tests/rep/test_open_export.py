# implements: TOOL-MIG-060
"""Reconstructable open result export (WP-REP-12).

The board criterion, exercised: export passing, failing, crashed, timed-out
and partial-run cases plus result identities, expected/actual values,
diagnostics and provenance; an independent reader reconstructs the test
cases from the TCM-06 interchange and the complete results without a private
project database; the versioned JSON interchange schema is published and the
emitted documents conform to it; losses and errors are explicit. Coverage
export remains REP-10/P4 and is deliberately absent.
"""

from __future__ import annotations

import csv
import io
import json
from importlib import resources
from typing import Any

import jsonschema
import pytest

from ectt.core.determinism import FixedClock
from ectt.exh.results import (
    AssertionFailure,
    ExecutionMetadata,
    ResultSet,
    SourceLocation,
    finalize_result,
)
from ectt.rep.errors import ReportModelError
from ectt.rep.open_export import (
    OPEN_EXPORT_SCHEMA_VERSION,
    build_open_export,
    dump_open_export,
    load_open_export,
    reconstruct,
)
from ectt.tcm.datacases import (
    DataDrivenTestCase,
    refresh_digest,
)
from ectt.tcm.datacases import (
    TestCaseExpected as CaseExpected,
)
from ectt.tcm.datacases import (
    TestCaseInputs as CaseInputs,
)

CLOCK = FixedClock("2026-11-19T00:00:00+00:00")

_FAILURE = AssertionFailure(
    assertion="assert_equal",
    expected="0",
    actual="42",
    location=SourceLocation(file="test_adc.c", line=17),
)


def _result_set() -> ResultSet:
    return ResultSet(
        run_id="run-open",
        execution=ExecutionMetadata(where="host", toolchain="gcc", target_id="tgt-1"),
        results=(
            finalize_result("case.pass", "pass", "da" * 32),
            finalize_result("case.fail", "fail", "db" * 32, failures=(_FAILURE,)),
            finalize_result("case.crash", "error", "dc" * 32),
            finalize_result("case.slow", "timeout", "dd" * 32),
        ),
        not_executed=("case.stale",),
        partial=True,
        infrastructure_faults=("runner lost serial connection after case.slow",),
    )


def _case(case_id: str, requirements: tuple[str, ...] = ("REQ-1",)) -> DataDrivenTestCase:
    return DataDrivenTestCase(
        case_id=case_id,
        unit="src/adc.c",
        function="adc_read",
        inputs=CaseInputs(),
        expected=CaseExpected(),
        stubs=(),
        requirements=requirements,
    )


def _export_text() -> str:
    cases = [refresh_digest(_case("case.pass")), refresh_digest(_case("case.fail"))]
    export = build_open_export(result_set=_result_set(), cases=cases, clock=CLOCK)
    return dump_open_export(export)


# --- the export carries every outcome class and the identities -------------------------


def test_export_covers_all_outcome_classes_and_identities() -> None:
    doc: dict[str, Any] = json.loads(_export_text())
    results = {r["test_id"]: r for r in doc["result_set"]["results"]}

    assert set(results) == {"case.pass", "case.fail", "case.crash", "case.slow"}
    assert [results[k]["outcome"] for k in ("case.pass", "case.fail", "case.crash", "case.slow")] == [
        "pass",
        "fail",
        "error",
        "timeout",
    ]
    assert all(results[k]["test_digest"] for k in results)  # result identities (D-02)
    assert doc["result_set"]["not_executed"] == ["case.stale"]  # partial-run reporting
    assert doc["result_set"]["partial"] is True
    assert doc["result_set"]["infrastructure_faults"]  # run-level diagnostics
    # expected/actual values with location for the failing case
    failure = results["case.fail"]["failures"][0]
    assert failure["expected"] == "0"
    assert failure["actual"] == "42"
    assert failure["location"] == {"file": "test_adc.c", "line": 17}


def test_provenance_travels_with_its_own_digest() -> None:
    doc: dict[str, Any] = json.loads(_export_text())

    assert doc["provenance"]["tool_version"]
    assert doc["provenance"]["input_digests"]["result_set"]
    assert doc["provenance"]["input_digests"]["test_cases_csv"]
    assert doc["provenance"]["schema_versions"]["open_export"] == OPEN_EXPORT_SCHEMA_VERSION


def test_coverage_export_is_deliberately_absent() -> None:
    """verifies: the board note — coverage export remains REP-10/P4."""
    doc: dict[str, Any] = json.loads(_export_text())

    assert "coverage" not in doc


# --- published schema ------------------------------------------------------------------


def test_emitted_documents_conform_to_the_published_schema() -> None:
    schema = json.loads(resources.files("ectt.rep.schema").joinpath("open-result-1.0.schema.json").read_text(encoding="utf-8"))
    doc: dict[str, Any] = json.loads(_export_text())

    jsonschema.validate(doc, schema)


# --- persistence and integrity ---------------------------------------------------------


def test_dump_is_byte_deterministic_and_round_trips() -> None:
    export = build_open_export(result_set=_result_set(), cases=[_case("case.pass")], clock=CLOCK)
    text = dump_open_export(export)

    assert text == dump_open_export(export)
    assert load_open_export(text) == export


def test_load_refuses_tampered_section() -> None:
    doc: dict[str, Any] = json.loads(_export_text())
    doc["result_set"]["results"][0]["outcome"] = "error"

    with pytest.raises(ReportModelError) as excinfo:
        load_open_export(doc)
    assert excinfo.value.reason == "digest_mismatch"


def test_load_refuses_unknown_schema_version() -> None:
    doc: dict[str, Any] = json.loads(_export_text())
    doc["schema_version"] = "9.9"

    with pytest.raises(ReportModelError) as excinfo:
        load_open_export(doc)
    assert excinfo.value.reason == "incompatible_schema_version"


# --- the independent reader -------------------------------------------------------------


def test_independent_reader_reconstructs_cases_and_results() -> None:
    """verifies: the board criterion — no private project database consulted."""
    export = load_open_export(_export_text())

    reconstruction = reconstruct(export)

    assert reconstruction.result_set.run_id == "run-open"
    assert {r.test_id: r.outcome for r in reconstruction.result_set.results} == {
        r.test_id: r.outcome for r in _result_set().results
    }
    assert {case.case_id for case in reconstruction.cases} == {"case.pass", "case.fail"}
    assert reconstruction.digest_mismatches == ()


def test_reader_reconstructs_from_the_plain_document_only() -> None:
    """The reconstruction input is the JSON document, nothing else."""
    doc: dict[str, Any] = json.loads(_export_text())
    export = load_open_export(doc)

    reconstruction = reconstruct(export)

    assert reconstruction.cases


def test_digest_mismatch_in_cases_is_reported_not_dropped() -> None:
    """verifies: explicit loss/error handling — a drifted case row is named.

    The CSV is tampered from a *writer* that failed to update the digest
    column: the bundle is resealed with a consistent export id (the writer
    bound what it wrote), so the drift reaches the reader, which reports it.
    """
    from ectt.core.determinism import canonical_json_bytes, stable_id

    doc: dict[str, Any] = json.loads(_export_text())
    reader = csv.reader(io.StringIO(doc["test_cases_csv"]))
    rows = list(reader)
    # Drift a CONTENT cell (column 2 = unit) of the second case row: the id
    # is never derived from content (DSN-TCM-110), so the recorded digest no
    # longer matches the reconstructed content.
    rows[2][2] = "src/drifted.c"
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    doc["test_cases_csv"] = buffer.getvalue()

    body = {key: value for key, value in doc.items() if key not in ("schema_version", "export_id")}
    body["export_id"] = ""  # the builder hashes the id slot empty
    doc["export_id"] = stable_id(canonical_json_bytes(body))

    export = load_open_export(doc)
    reconstruction = reconstruct(export)

    assert reconstruction.digest_mismatches, "the drifted row must be reported"
    assert "case.pass" in reconstruction.digest_mismatches  # cases export sorted by id


def test_case_losses_travel_verbatim() -> None:
    """A case the interchange cannot express losslessly is reported explicitly."""
    lossy_case = _case("case.lossy", requirements=("REQ;1",))
    export = build_open_export(result_set=_result_set(), cases=[lossy_case], clock=CLOCK)

    assert export.test_case_losses
    assert "case.lossy" in export.test_case_losses[0]
    assert "cannot round-trip" in export.test_case_losses[0]

    doc: dict[str, Any] = json.loads(dump_open_export(export))
    assert doc["test_case_losses"] == list(export.test_case_losses)
    jsonschema.validate(
        doc,
        json.loads(resources.files("ectt.rep.schema").joinpath("open-result-1.0.schema.json").read_text(encoding="utf-8")),
    )


def test_export_id_is_stable_and_discriminating() -> None:
    first = build_open_export(result_set=_result_set(), cases=[_case("case.pass")], clock=CLOCK)
    second = build_open_export(result_set=_result_set(), cases=[_case("case.pass")], clock=CLOCK)

    assert first.export_id == second.export_id

    changed = build_open_export(
        result_set=_result_set(), cases=[_case("case.pass"), _case("case.fail")], clock=CLOCK
    )
    assert changed.export_id != first.export_id
