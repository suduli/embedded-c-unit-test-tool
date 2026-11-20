"""Tests for the data-driven test case model and on-disk format (WP-TCM-02).

Covers TOOL-TCD-020, TOOL-TCD-030, TOOL-TCD-040, TOOL-TCD-140 and the D-02
digest binding, per docs/verification/WP-TCM-02-analysis.md.
"""

from __future__ import annotations

from typing import Any

import pytest

from ectt.prj.errors import (
    CommentPreservationError,
    InvalidSchemaVersionError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
)
from ectt.prj.yaml_adapter import (
    AnchorForbiddenError,
    DuplicateKeyError,
    RestrictedYamlAdapter,
)
from ectt.tcm.datacases import (
    DataDrivenTestCase,
    compute_case_digest,
    dump_test_cases_document,
    load_test_cases_file,
    parse_test_cases_document,
    refresh_digest,
    save_test_cases_file,
)
from ectt.tcm.datacases import (
    TestCaseExpected as TcmCaseExpected,
)
from ectt.tcm.datacases import (
    TestCaseInputs as TcmCaseInputs,
)
from ectt.tcm.datacases import (
    TestCasesFile as TcmCasesFile,
)
from ectt.tcm.errors import (
    DuplicateTestCaseError,
    InvalidTestCaseError,
    InvalidTestCasesFileError,
    MissingCaseFieldError,
)


def case_dict(**overrides: Any) -> dict[str, Any]:
    """A valid data-driven case as restricted YAML would load it (all strings)."""
    entry: dict[str, Any] = {
        "id": "tc.adc_read.nominal.7f3a",
        "unit": "src/a.c",
        "function": "adc_read",
        "origin": {"author": "human"},
        "requirements": ["SW-REQ-114"],
        "inputs": {
            "parameters": {"ch": "ADC_CH_VBAT"},
            "globals": {"g_adc_state": "calibrated"},
        },
        "expected": {
            "return": "4095",
            "globals": {"g_adc_state.last_error": "0"},
            "out_parameters": {},
            "comparison": {"g_adc_gain": {"relative": "1e-6"}},
        },
        "stubs": {
            "hal_read": {
                "mode": "sequence",
                "returns": ["0", "4095"],
                "expect_calls": "2",
                "out_parameters": {},
            }
        },
    }
    entry.update(overrides)
    return entry


def file_dict(cases: list[dict[str, Any]] | None = None, **extras: Any) -> dict[str, Any]:
    return {"schema_version": "1", "test_cases": cases if cases is not None else [case_dict()], **extras}


def fresh_file() -> TcmCasesFile:
    """A parsed file whose cases carry refreshed (matching) digest bindings."""
    parsed = parse_test_cases_document(file_dict())
    return TcmCasesFile(
        schema_version=parsed.schema_version,
        cases=tuple(refresh_digest(case) for case in parsed.cases),
        extra=parsed.extra,
    )


def fresh_text() -> str:
    return dump_test_cases_document(fresh_file())


# --- AC-1: the model carries every TOOL-TCD-040 field as data ---------------


def test_full_model_round_trip_carries_every_field() -> None:
    parsed = parse_test_cases_document(file_dict())
    assert parsed.schema_version == 1
    assert len(parsed.cases) == 1
    case = parsed.cases[0]
    assert case.case_id == "tc.adc_read.nominal.7f3a"
    assert case.unit == "src/a.c"
    assert case.function == "adc_read"
    assert case.inputs.parameters == {"ch": "ADC_CH_VBAT"}
    assert case.inputs.global_inits == {"g_adc_state": "calibrated"}
    assert case.expected.return_value == "4095"
    assert case.expected.global_finals == {"g_adc_state.last_error": "0"}
    assert case.expected.out_parameters == {}
    assert case.expected.comparison == {"g_adc_gain": {"relative": "1e-6"}}
    assert len(case.stubs) == 1
    stub = case.stubs[0]
    assert stub.name == "hal_read"
    assert stub.mode == "sequence"
    assert stub.returns == ("0", "4095")
    assert stub.expect_calls == "2"
    assert case.origin.author == "human"
    assert case.requirements == ("SW-REQ-114",)


# --- AC-2: incomplete cases are rejected with named errors ------------------


@pytest.mark.parametrize("section", ["inputs", "expected", "stubs"])
def test_missing_required_section_is_rejected(section: str) -> None:
    entry = case_dict()
    del entry[section]
    with pytest.raises(MissingCaseFieldError, match=section):
        parse_test_cases_document(file_dict([entry]))


def test_empty_identifier_is_rejected() -> None:
    entry = case_dict(id="  ")
    with pytest.raises(MissingCaseFieldError, match="id"):
        parse_test_cases_document(file_dict([entry]))


def test_unknown_origin_author_is_rejected() -> None:
    entry = case_dict(origin={"author": "compiler"})
    with pytest.raises(InvalidTestCaseError, match="origin author"):
        parse_test_cases_document(file_dict([entry]))


def test_unknown_structured_key_is_refused_not_dropped() -> None:
    entry = case_dict()
    entry["inputs"] = dict(entry["inputs"], bogus={"x": "1"})
    with pytest.raises(InvalidTestCasesFileError, match="bogus"):
        parse_test_cases_document(file_dict([entry]))


def test_scalar_unknown_key_is_preserved_through_round_trip() -> None:
    entry = case_dict(note="kept for the reviewer")
    parsed = parse_test_cases_document(file_dict([entry]))
    assert parsed.cases[0].extra == {"note": "kept for the reviewer"}
    refreshed = TcmCasesFile(
        schema_version=parsed.schema_version,
        cases=tuple(refresh_digest(case) for case in parsed.cases),
        extra=parsed.extra,
    )
    reparsed = parse_test_cases_document(
        RestrictedYamlAdapter().load(dump_test_cases_document(refreshed))
    )
    assert reparsed.cases[0].extra == {"note": "kept for the reviewer"}


# --- AC-3: plain-text, diffable, idempotent format ---------------------------


def test_dump_is_quoted_schema_first_deterministic_text() -> None:
    text = fresh_text()
    assert text.startswith('"schema_version": "1"\n')
    assert '"id": "tc.adc_read.nominal.7f3a"' in text
    assert "\r" not in text


def test_round_trip_is_idempotent() -> None:
    adapter = RestrictedYamlAdapter()
    first = fresh_text()
    second = dump_test_cases_document(parse_test_cases_document(adapter.load(first)))
    assert second == first
    third = dump_test_cases_document(parse_test_cases_document(adapter.load(second)))
    assert third == second


def test_two_dumps_of_same_model_are_byte_identical_and_carry_no_timestamps() -> None:
    parsed = fresh_file()
    one = dump_test_cases_document(parsed)
    two = dump_test_cases_document(parsed)
    assert one == two
    assert "generated_at" not in one
    assert "T00:" not in one


def test_yaml_hazards_are_rejected_at_text_level() -> None:
    anchored = (
        '"schema_version": "1"\n'
        '"test_cases":\n'
        '  - "id": "a"\n'
        '    "unit": &a "src/a.c"\n'
        '  - "id": "b"\n'
        '    "unit": *a\n'
    )
    with pytest.raises(AnchorForbiddenError):
        RestrictedYamlAdapter().load(anchored)
    duplicated = (
        '"schema_version": "1"\n'
        '"test_cases":\n'
        '  - "id": "a"\n'
        '    "unit": "src/a.c"\n'
        '    "unit": "src/b.c"\n'
    )
    with pytest.raises(DuplicateKeyError):
        RestrictedYamlAdapter().load(duplicated)


def test_save_is_noop_when_identical_and_guards_comments(tmp_path) -> None:
    target = tmp_path / "adc_read.tests"
    parsed = fresh_file()
    save_test_cases_file(parsed, target)
    first_bytes = target.read_bytes()
    save_test_cases_file(parsed, target)
    assert target.read_bytes() == first_bytes

    commented = first_bytes.decode("utf-8").replace(
        '"schema_version": "1"', '# reviewer note\n"schema_version": "1"'
    )
    target.write_text(commented, encoding="utf-8")
    with pytest.raises(CommentPreservationError):
        save_test_cases_file(parsed, target)
    save_test_cases_file(parsed, target, discard_comments=True)
    assert target.read_bytes() == first_bytes


# --- AC-4: stable unique identity -------------------------------------------


def edited_case(case: DataDrivenTestCase, **changes: Any) -> DataDrivenTestCase:
    """A values-only edit: same identity, new content, refreshed digest."""
    fields: dict[str, Any] = {
        "case_id": case.case_id,
        "unit": case.unit,
        "function": case.function,
        "inputs": case.inputs,
        "expected": case.expected,
        "stubs": case.stubs,
        "origin": case.origin,
        "requirements": case.requirements,
    }
    fields.update(changes)
    return refresh_digest(DataDrivenTestCase(**fields))


def test_identifier_survives_value_edit() -> None:
    case = fresh_file().cases[0]
    edited = edited_case(case, inputs=TcmCaseInputs(parameters={"ch": "ADC_CH_VREF"}))
    assert edited.case_id == case.case_id
    assert edited.inputs.parameters == {"ch": "ADC_CH_VREF"}
    assert edited.content_digest != case.content_digest
    assert not edited.stale


def test_duplicate_identifier_within_one_file_is_rejected() -> None:
    with pytest.raises(DuplicateTestCaseError, match=r"tc\.adc_read\.nominal\.7f3a"):
        parse_test_cases_document(file_dict([case_dict(), case_dict()]))


# --- AC-5: D-02 digest binding ----------------------------------------------


def test_digest_is_order_and_process_independent() -> None:
    one = case_dict()
    two = dict(reversed(list(one.items())))
    two["inputs"] = dict(reversed(list(one["inputs"].items())))
    digest_one = compute_case_digest(
        parse_test_cases_document(file_dict([one])).cases[0].content_payload()
    )
    digest_two = compute_case_digest(
        parse_test_cases_document(file_dict([two])).cases[0].content_payload()
    )
    assert digest_one == digest_two


def test_recorded_digest_binding_flags_stale_never_current() -> None:
    # tool-written record: recorded digest matches content
    round_tripped = parse_test_cases_document(RestrictedYamlAdapter().load(fresh_text()))
    assert not round_tripped.cases[0].stale
    # tampered record: digest no longer matches content -> stale, never error
    tampered = parse_test_cases_document(file_dict([case_dict(digest="0" * 64)])).cases[0]
    assert tampered.stale
    # hand-authored record without a digest is unverified -> stale
    hand = parse_test_cases_document(
        {"schema_version": "1", "test_cases": [{k: v for k, v in case_dict().items() if k != "digest"}]}
    ).cases[0]
    assert hand.recorded_digest is None
    assert hand.stale


def test_value_edit_changes_digest_and_id_stays() -> None:
    case = fresh_file().cases[0]
    edited = edited_case(
        case, expected=TcmCaseExpected(return_value="0", comparison=case.expected.comparison)
    )
    assert edited.case_id == case.case_id
    assert edited.content_digest != case.content_digest
    # identical content -> identical digest regardless of identity
    same = edited_case(
        case,
        case_id="tc.other.0000",
        expected=TcmCaseExpected(return_value="0", comparison=case.expected.comparison),
    )
    assert same.content_digest == edited.content_digest


def test_dump_refuses_to_write_a_case_without_recorded_digest() -> None:
    parsed = parse_test_cases_document(
        {"schema_version": "1", "test_cases": [{k: v for k, v in case_dict().items() if k != "digest"}]}
    )
    with pytest.raises(MissingCaseFieldError, match="recorded digest"):
        dump_test_cases_document(parsed)


# --- AC-7: schema versioning ------------------------------------------------


def test_missing_schema_version_is_rejected() -> None:
    with pytest.raises(MissingSchemaVersionError):
        parse_test_cases_document({"test_cases": [case_dict()]})


def test_unsupported_schema_version_is_rejected() -> None:
    with pytest.raises(UnsupportedSchemaVersionError):
        parse_test_cases_document(file_dict(schema_version="2"))


def test_invalid_schema_version_is_rejected() -> None:
    with pytest.raises(InvalidSchemaVersionError):
        parse_test_cases_document(file_dict(schema_version="one"))


# --- file-level behaviors ----------------------------------------------------


def test_load_and_save_round_trip_on_disk(tmp_path) -> None:
    target = tmp_path / "tests" / "src" / "a" / "a.tests"
    original = fresh_file()
    save_test_cases_file(original, target)
    loaded = load_test_cases_file(target)
    assert loaded.schema_version == original.schema_version
    assert loaded.cases[0].case_id == original.cases[0].case_id
    assert not loaded.cases[0].stale
    assert dump_test_cases_document(loaded) == dump_test_cases_document(original)


def test_unreadable_file_raises_named_error(tmp_path) -> None:
    from ectt.tcm.errors import TestCaseReadError as TcmReadError

    with pytest.raises(TcmReadError):
        load_test_cases_file(tmp_path / "missing.tests")


def test_structural_malformation_is_rejected() -> None:
    with pytest.raises(InvalidTestCasesFileError):
        parse_test_cases_document(file_dict(cases="nope"))
    with pytest.raises(InvalidTestCasesFileError):
        parse_test_cases_document(file_dict(cases=["not-a-mapping"]))
