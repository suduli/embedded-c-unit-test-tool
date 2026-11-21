# implements: TOOL-COV-140, TOOL-COV-150
"""Coverage-by-analysis justification with digest binding (WP-COV-09)."""

from __future__ import annotations

import pytest

from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document
from ectt.cov.justification import (
    AnnotatedCoverage,
    Justification,
    annotate_coverage,
    compute_source_digest,
    evaluate_justification,
)

PAYLOAD = {
    "format_version": "2",
    "gcc_version": "14.1.0",
    "data_file": "d.gcda",
    "files": [
        {
            "file": "src/safety.c",
            "lines": [
                {"line_number": 10, "count": 0, "unexecuted_block": False},
                {"line_number": 11, "count": 0, "unexecuted_block": False},
                {"line_number": 12, "count": 3, "unexecuted_block": False},
            ],
        }
    ],
}

SOURCE = "line one\nline two\n...line ten\n"


def _justification(digest: str | None = None, **overrides: object) -> Justification:
    values: dict[str, object] = {
        "id": "J-SAFE-1",
        "file": "src/safety.c",
        "start_line": 10,
        "end_line": 11,
        "author": "safety engineer",
        "date": "2026-11-20",
        "rationale": "fault-injection branch unreachable without hardware fault",
        "source_digest": digest or compute_source_digest(SOURCE),
    }
    values.update(overrides)
    return Justification(**values)  # type: ignore[arg-type]


# --- TOOL-COV-140: justified rather than covered --------------------------------


def test_uncovered_line_in_valid_region_reports_justified() -> None:
    """verifies: TOOL-COV-140 — justified, never silently counted as covered."""
    doc = read_gcov_document(PAYLOAD)
    annotated = annotate_coverage(doc, [_justification()], {"src/safety.c": compute_source_digest(SOURCE)})
    (file,) = annotated.files
    statuses = {line.line_number: line for line in file.lines}
    assert statuses[10].status == "justified"
    assert statuses[10].justification_id == "J-SAFE-1"
    assert statuses[11].status == "justified"
    assert statuses[12].status == "covered"  # covered by test regardless of justification


def test_uncovered_line_without_justification_reports_uncovered() -> None:
    doc = read_gcov_document(PAYLOAD)
    annotated = annotate_coverage(doc, [], {})
    (file,) = annotated.files
    assert [line.status for line in file.lines] == ["uncovered", "uncovered", "covered"]


def test_partial_line_reports_partial() -> None:
    payload = {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [{"file": "src/safety.c", "lines": [{"line_number": 10, "count": 2, "unexecuted_block": True}]}],
    }
    annotated = annotate_coverage(read_gcov_document(payload), [], {})
    (file,) = annotated.files
    assert file.lines[0].status == "partial"


# --- recorded §5.4 criterion: digest binding and invalidation ---------------------


def test_source_edit_invalidates_and_shows_uncovered() -> None:
    """verifies: the recorded PLAN-001 §5.4 criterion — editing a source line under
    an accepted justification invalidates it, and the next report shows the
    construct as uncovered rather than justified."""
    accepted_digest = compute_source_digest(SOURCE)
    justification = _justification(digest=accepted_digest)
    doc = read_gcov_document(PAYLOAD)

    before = annotate_coverage(doc, [justification], {"src/safety.c": accepted_digest})
    (file_before,) = before.files
    assert file_before.lines[0].status == "justified"
    assert file_before.invalidated == ()

    edited = SOURCE.replace("line two", "line two EDITED")  # a source line changed
    after = annotate_coverage(doc, [justification], {"src/safety.c": compute_source_digest(edited)})
    (file_after,) = after.files
    assert file_after.lines[0].status == "uncovered"  # uncovered rather than justified
    assert file_after.lines[0].justification_id is None
    assert file_after.invalidated == ("J-SAFE-1",)  # advisory carries the id


def test_evaluate_justification_states() -> None:
    justification = _justification()
    assert evaluate_justification(justification, compute_source_digest(SOURCE)) == "valid"
    assert (
        evaluate_justification(justification, compute_source_digest(SOURCE + "\n")) == "invalidated"
    )


def test_missing_current_digest_is_refused() -> None:
    """verifies: AC-4 — an unverifiable justification never evaluates valid."""
    doc = read_gcov_document(PAYLOAD)
    with pytest.raises(CoverageError) as exc_info:
        annotate_coverage(doc, [_justification()], {})
    assert exc_info.value.reason == "missing_current_digest"


# --- TOOL-COV-150: author, date, rationale recorded -------------------------------


@pytest.mark.parametrize(
    "field",
    ["author", "rationale"],
)
def test_empty_author_or_rationale_is_refused(field: str) -> None:
    with pytest.raises(CoverageError) as exc_info:
        _justification(**{field: "  "})
    assert exc_info.value.reason == "missing_justification_field"


def test_malformed_date_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        _justification(date="20/11/2026")
    assert exc_info.value.reason == "invalid_justification_date"


def test_malformed_line_range_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        _justification(start_line=0)
    assert exc_info.value.reason == "invalid_line_range"
    with pytest.raises(CoverageError) as exc_info:
        _justification(end_line=9)
    assert exc_info.value.reason == "invalid_line_range"


def test_bad_digest_is_refused() -> None:
    with pytest.raises(CoverageError) as exc_info:
        _justification(digest="abc123")
    assert exc_info.value.reason == "invalid_source_digest"


def test_record_fields_are_serialised() -> None:
    """verifies: TOOL-COV-150 — author, date and rationale travel with the record."""
    justification = _justification()
    record = justification.to_dict()
    assert record["author"] == "safety engineer"
    assert record["date"] == "2026-11-20"
    assert "fault-injection" in record["rationale"]
    assert record["source_digest"] == compute_source_digest(SOURCE)


# --- determinism -------------------------------------------------------------------


def test_annotation_is_canonical_and_deterministic() -> None:
    doc = read_gcov_document(PAYLOAD)
    first = annotate_coverage(doc, [_justification()], {"src/safety.c": compute_source_digest(SOURCE)})
    second = annotate_coverage(doc, [_justification()], {"src/safety.c": compute_source_digest(SOURCE)})
    assert isinstance(first, AnnotatedCoverage)
    assert first.to_dict() == second.to_dict()
    assert first.files[0].file == "src/safety.c"
    assert [line.line_number for line in first.files[0].lines] == [10, 11, 12]
