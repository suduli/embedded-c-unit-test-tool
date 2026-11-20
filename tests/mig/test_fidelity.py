# implements: TOOL-MIG-040
"""Import fidelity reporting (WP-MIG-05).

Verifies: TOOL-MIG-040 (converted / converted with loss / not converted, per
artifact), TOOL-MIG-110 (deferred compound structures, with location, in a
machine-checkable set).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.mig.ceedling import import_ceedling_project
from ectt.mig.csv_import import import_mapped_csv
from ectt.mig.errors import MigError
from ectt.mig.fidelity import (
    ArtifactFidelity,
    DeferredStructure,
    FidelityNote,
    FidelityReport,
    build_ceedling_fidelity_report,
    build_csv_fidelity_report,
    check_fidelity_report,
    dump_fidelity_report,
    load_fidelity_report,
)
from tests.mig.test_ceedling import _make_project

MAPPING = {"Case": "id", "Module": "unit", "Func": "function", "Want": "expect_return"}
CSV = (
    "Case,Module,Func,Want,Comment,Slot\n"
    "c1,a.c,f,1,,\n"
    "c2,a.c,f,2,keep me,\n"
    "c3,a.c,f,3,,2\n"
    ",a.c,f,4,,\n"
)


def _csv_report() -> FidelityReport:
    result = import_mapped_csv(CSV, MAPPING, deferred_columns={"Slot": "slot"})
    return build_csv_fidelity_report("spreadsheet.csv", result)


def test_csv_rows_are_converted_lossy_or_not_converted() -> None:
    report = _csv_report()

    status = {a.artifact: a.status for a in report.artifacts}
    assert status == {"row 1": "converted", "row 2": "converted_lossy", "row 3": "not_converted", "row 4": "not_converted"}
    assert report.counts() == {"converted": 1, "converted_lossy": 1, "not_converted": 2}


def test_lossy_row_names_the_dropped_column() -> None:
    lossy = next(a for a in _csv_report().artifacts if a.artifact == "row 2")
    assert [(n.kind, n.effect) for n in lossy.notes] == [("unmapped_column", "loss")]
    assert "Comment" in lossy.notes[0].detail


def test_rejected_rows_carry_their_reason() -> None:
    report = _csv_report()
    reasons = {a.artifact: a.notes[0].kind for a in report.artifacts if a.status == "not_converted"}
    assert reasons == {"row 3": "deferred_structure", "row 4": "missing_id"}


def test_deferred_structure_is_reported_with_location_and_not_imported() -> None:
    result = import_mapped_csv(CSV, MAPPING, deferred_columns={"Slot": "slot"})
    report = build_csv_fidelity_report("spreadsheet.csv", result)

    assert report.deferred_set() == {("slot", "row 3", "row 3, column 'Slot'")}
    assert "c3" not in [c.case_id for c in result.cases]


def test_each_deferred_kind_is_reported() -> None:
    text = "Case,Module,Func,A,B,C\nc1,a.c,f,x,,\nc2,a.c,f,,y,\nc3,a.c,f,,,z\n"
    result = import_mapped_csv(
        text,
        {"Case": "id", "Module": "unit", "Func": "function"},
        deferred_columns={"A": "slot", "B": "slot_iteration", "C": "slot_history"},
    )
    kinds = {d.kind for d in build_csv_fidelity_report("s", result).deferred}
    assert kinds == {"slot", "slot_iteration", "slot_history"}


def test_a_report_without_deferred_structures_has_an_empty_set() -> None:
    result = import_mapped_csv("Case,Module,Func\nc1,a.c,f\n", {"Case": "id", "Module": "unit", "Func": "function"})
    assert build_csv_fidelity_report("s", result).deferred_set() == frozenset()


def test_ceedling_import_is_reported_per_artifact(tmp_path: Path) -> None:
    imported = import_ceedling_project(_make_project(tmp_path / "ceed"))
    report = build_ceedling_fidelity_report("ceed", imported)

    status = {a.artifact: a.status for a in report.artifacts}
    assert status["project.yml"] == "converted"
    assert status["test/test_adc.c"] == "converted"
    assert status["test/sub/test_param.c"] == "converted_lossy"
    lossy = next(a for a in report.artifacts if a.artifact == "test/sub/test_param.c")
    assert {n.kind for n in lossy.notes} == {"parameterised_test_attribute", "duplicate_test_name"}


def test_ceedling_informational_notes_do_not_downgrade_the_status(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    (root / "project.yml").write_text(":paths:\n  :test:\n    - nowhere\n", encoding="utf-8")

    report = build_ceedling_fidelity_report("p", import_ceedling_project(root))

    (config,) = report.artifacts
    assert config.status == "converted"
    assert [(n.kind, n.effect) for n in config.notes] == [("path_matches_nothing", "info")]


def test_ceedling_unfollowed_import_downgrades_the_config(tmp_path: Path) -> None:
    root = tmp_path / "p"
    root.mkdir()
    (root / "project.yml").write_text(":import:\n  - other.yml\n:paths:\n  :test:\n    - .\n", encoding="utf-8")

    report = build_ceedling_fidelity_report("p", import_ceedling_project(root))

    assert report.artifacts[0].status == "converted_lossy"


def test_dump_is_deterministic_and_roundtrips() -> None:
    report = _csv_report()
    text = dump_fidelity_report(report)

    assert text == dump_fidelity_report(_csv_report())
    assert load_fidelity_report(text) == report


def test_sound_reports_pass_the_consistency_check(tmp_path: Path) -> None:
    assert check_fidelity_report(_csv_report()) == []
    imported = import_ceedling_project(_make_project(tmp_path / "ceed"))
    assert check_fidelity_report(build_ceedling_fidelity_report("c", imported)) == []


def test_check_flags_a_flattened_deferred_structure() -> None:
    report = FidelityReport(
        "s",
        (ArtifactFidelity("row 1", "csv_row", "converted"),),
        (DeferredStructure("slot", "row 1", "row 1, column 'S'"),),
    )
    assert any("flattened" in p for p in check_fidelity_report(report))


def test_check_flags_status_note_mismatches_and_duplicates() -> None:
    loss = FidelityNote("k", "d", "loss")
    report = FidelityReport(
        "s",
        (
            ArtifactFidelity("a", "x", "converted", (loss,)),
            ArtifactFidelity("b", "x", "converted_lossy"),
            ArtifactFidelity("c", "x", "not_converted"),
            ArtifactFidelity("c", "x", "converted"),
        ),
        (DeferredStructure("slot", "ghost", ""), DeferredStructure("slot", "ghost", "")),
    )
    problems = " | ".join(check_fidelity_report(report))
    for expected in ("records a loss", "without a recorded loss", "without a reason", "duplicate artifact", "unknown artifact", "no location", "duplicate deferred"):
        assert expected in problems


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda d: d.update(report_version="9"), "unsupported_report_version"),
        (lambda d: d["artifacts"][0].update(status="maybe"), "invalid_status"),
        (lambda d: d["artifacts"][1]["notes"][0].update(effect="meh"), "invalid_effect"),
        (lambda d: d["deferred"][0].update(kind="loop"), "invalid_deferred_kind"),
        (lambda d: d["counts"].update(converted=99), "counts_mismatch"),
        (lambda d: d.update(source=3), "invalid_report"),
    ],
)
def test_loader_refuses_tampered_reports(mutate, reason: str) -> None:  # type: ignore[no-untyped-def]
    doc = json.loads(dump_fidelity_report(_csv_report()))
    mutate(doc)
    with pytest.raises(MigError) as excinfo:
        load_fidelity_report(doc)
    assert excinfo.value.reason == reason


def test_loader_refuses_non_json_text() -> None:
    with pytest.raises(MigError) as excinfo:
        load_fidelity_report("{not json")
    assert excinfo.value.reason == "invalid_report"


def test_unknown_deferred_kind_and_mapped_deferred_column_are_refused() -> None:
    mapping = {"Case": "id", "Module": "unit", "Func": "function"}
    text = "Case,Module,Func,S\nc1,a.c,f,\n"
    with pytest.raises(MigError) as e1:
        import_mapped_csv(text, mapping, deferred_columns={"S": "loop"})
    assert e1.value.reason == "unknown_deferred_kind"
    with pytest.raises(MigError) as e2:
        import_mapped_csv(text, mapping, deferred_columns={"Case": "slot"})
    assert e2.value.reason == "deferred_column_mapped"
    with pytest.raises(MigError) as e3:
        import_mapped_csv(text, mapping, deferred_columns={"Nope": "slot"})
    assert e3.value.reason == "unknown_column"
