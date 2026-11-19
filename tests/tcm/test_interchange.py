"""Tests for test case interchange import and export (WP-TCM-06).

Covers TOOL-TCD-100, DSN-TCM-070, and the SDD-002 §5.1 round-trip contract
per docs/verification/WP-TCM-06-analysis.md.
"""

from __future__ import annotations

import csv
import io

import pytest

from ectt.tcm.datacases import (
    DataDrivenTestCase,
    refresh_digest,
)
from ectt.tcm.datacases import (
    StubSpec as TcmStubSpec,
)
from ectt.tcm.datacases import (
    TestCaseExpected as TcmCaseExpected,
)
from ectt.tcm.datacases import (
    TestCaseInputs as TcmCaseInputs,
)
from ectt.tcm.datacases import (
    TestCaseOrigin as TcmCaseOrigin,
)
from ectt.tcm.errors import InterchangeError
from ectt.tcm.interchange import COLUMNS, export_cases, import_cases


def edit_cell(text: str, column: str, transform) -> str:  # type: ignore[no-untyped-def]
    """Rewrite one column's cell in every data row via the csv module."""
    rows = list(csv.reader(io.StringIO(text)))
    index = rows[0].index(column)
    for row in rows[1:]:
        row[index] = transform(row[index])
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def append_duplicate_row(text: str) -> str:
    rows = list(csv.reader(io.StringIO(text)))
    rows.append(list(rows[1]))
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def drop_column(text: str, column: str) -> str:
    rows = list(csv.reader(io.StringIO(text)))
    index = rows[0].index(column)
    for row in rows:
        del row[index]
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(rows)
    return buffer.getvalue()


def full_case(case_id: str = "tc.adc.nominal.0001") -> DataDrivenTestCase:
    return refresh_digest(
        DataDrivenTestCase(
            case_id=case_id,
            unit="src/a.c",
            function="adc_read",
            inputs=TcmCaseInputs(
                parameters={"ch": "ADC_CH_VBAT"},
                global_inits={"g_state": "1"},
            ),
            expected=TcmCaseExpected(
                return_value="4095",
                global_finals={"g_state.last_error": "0"},
                out_parameters={"out_raw": "2048"},
                comparison={"g_gain": {"relative": "1e-6"}},
            ),
            stubs=(
                TcmStubSpec(
                    name="hal_read",
                    mode="sequence",
                    returns=("0", "4095"),
                    expect_calls="2",
                ),
            ),
            origin=TcmCaseOrigin(author="atg", engine="builtin", review_state="reviewed"),
            requirements=("SW-REQ-114", "SW-REQ-120"),
            suites=("smoke", "adc"),
            robustness=False,
        )
    )


# --- AC-1: documented deterministic export ------------------------------------


def test_export_is_deterministic_with_schema_column() -> None:
    one = export_cases([full_case("tc.b.0002"), full_case("tc.a.0001")])
    two = export_cases([full_case("tc.a.0001"), full_case("tc.b.0002")])
    assert one.text == two.text  # sorted by id, deterministic
    lines = one.text.splitlines()
    assert lines[0].startswith("ectt_interchange_version,id,unit")
    assert lines[1].split(",")[1] == "tc.a.0001"
    assert "\r" not in one.text
    assert set(COLUMNS) <= set(lines[0].split(","))


# --- AC-2: strict import -------------------------------------------------------


def test_import_reconstructs_cases() -> None:
    case = full_case()
    imported = import_cases(export_cases([case]).text)
    assert len(imported.cases) == 1
    got = imported.cases[0]
    assert got.case_id == case.case_id
    assert got.inputs.parameters == {"ch": "ADC_CH_VBAT"}
    assert got.expected.return_value == "4095"
    assert got.expected.comparison == {"g_gain": {"relative": "1e-6"}}
    assert got.stubs[0].name == "hal_read"
    assert got.stubs[0].expect_calls == "2"
    assert got.origin.author == "atg"
    assert got.requirements == ("SW-REQ-114", "SW-REQ-120")
    assert got.suites == ("smoke", "adc")
    assert got.robustness is False
    assert not got.stale
    assert imported.digest_mismatches == ()


def test_import_validates_columns_strictly() -> None:
    text = export_cases([full_case()]).text
    rows = list(csv.reader(io.StringIO(text)))
    extra = [list(row) for row in rows]
    extra[0].append("bogus")
    for row in extra[1:]:
        row.append("")
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerows(extra)
    with pytest.raises(InterchangeError, match="unknown column"):
        import_cases(buffer.getvalue())
    with pytest.raises(InterchangeError, match="missing required column"):
        import_cases(drop_column(text, "digest"))
    malformed = edit_cell(text, "input_parameters", lambda cell: "not json")
    with pytest.raises(InterchangeError, match="not valid JSON"):
        import_cases(malformed)


def test_import_rejects_duplicate_ids() -> None:
    with pytest.raises(InterchangeError, match="more than once"):
        import_cases(append_duplicate_row(export_cases([full_case()]).text))


def test_empty_id_is_rejected() -> None:
    with pytest.raises(InterchangeError, match="missing a non-empty 'id'"):
        import_cases(edit_cell(export_cases([full_case()]).text, "id", lambda cell: ""))


# --- AC-3: lossless round trip --------------------------------------------------


def test_round_trip_is_byte_identical_for_full_model() -> None:
    cases = [
        full_case("tc.a.0001"),
        refresh_digest(
            DataDrivenTestCase(
                case_id="tc.b.0002",
                unit="src/b.c",
                function="pwm_set",
                inputs=TcmCaseInputs(parameters={"duty": "50"}),
                expected=TcmCaseExpected(),
                stubs=(),
                origin=TcmCaseOrigin(),
                robustness=True,
            )
        ),
    ]
    first = export_cases(cases)
    imported = import_cases(first.text)
    second = export_cases(imported.cases)
    assert second.text == first.text
    assert second.losses == ()
    # idempotent one more time
    third = export_cases(import_cases(second.text).cases)
    assert third.text == second.text


# --- AC-4: loss reporting --------------------------------------------------------


def test_unrepresentable_content_is_reported_as_loss() -> None:
    case = refresh_digest(
        DataDrivenTestCase(
            case_id="tc.note.0001",
            unit="src/a.c",
            function="f",
            inputs=TcmCaseInputs(),
            expected=TcmCaseExpected(),
            stubs=(),
            extra={"note": "reviewer context"},
        )
    )
    exported = export_cases([case])
    assert any("'note'" in loss for loss in exported.losses)
    suite_case = refresh_digest(
        DataDrivenTestCase(
            case_id="tc.sem.0002",
            unit="src/a.c",
            function="f",
            inputs=TcmCaseInputs(),
            expected=TcmCaseExpected(),
            stubs=(),
            suites=("a;b",),
        )
    )
    exported = export_cases([suite_case])
    assert any("';'" in loss for loss in exported.losses)


def test_import_reports_digest_mismatch() -> None:
    text = export_cases([full_case()]).text
    table = list(csv.reader(io.StringIO(text)))
    original_digest = table[1][table[0].index("digest")]
    tampered = "f" * 64 if not original_digest.startswith("f") else "0" * 64
    imported = import_cases(edit_cell(text, "digest", lambda cell: tampered))
    assert imported.digest_mismatches == ("tc.adc.nominal.0001",)
    assert imported.cases[0].stale


def test_import_accepts_hand_authored_row_without_digest() -> None:
    hand = edit_cell(export_cases([full_case()]).text, "digest", lambda cell: "")
    imported = import_cases(hand)
    assert imported.digest_mismatches == ()
    assert imported.cases[0].stale  # unverified: recorded digest is absent
