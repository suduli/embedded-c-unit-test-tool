# implements: TOOL-TRC-090
"""Requirement change detection (WP-TRC-05).

Verifies: TOOL-TRC-090 — a requirement changed since its links were last
reviewed or executed marks its linked tests as needing re-review.
"""

from __future__ import annotations

import json

import pytest

from ectt.trc import (
    AssociationSet,
    RequirementRecord,
    TrcError,
    build_matrix,
    detect_changes,
    dump_baseline,
    load_baseline,
    mark_reviewed,
    record_baseline,
    requirement_digest,
)

R1 = RequirementRecord("REQ-1", "Scaling", "The tool shall scale.")
R2 = RequirementRecord("REQ-2", "Range", "The tool shall clamp.")
R3 = RequirementRecord("REQ-3", "Alarm", "The tool shall alarm.")


def _associations() -> AssociationSet:
    associations = AssociationSet()
    for requirement, test in (("REQ-1", "t.a"), ("REQ-1", "t.b"), ("REQ-2", "t.b"), ("REQ-2", "t.c"), ("REQ-3", "t.d")):
        associations.add(requirement, test)
    return associations


def test_unchanged_requirements_flag_nothing() -> None:
    baseline = record_baseline([R1, R2, R3])
    report = detect_changes(baseline, [R1, R2, R3], _associations())

    assert (report.changed, report.removed, report.new) == ((), (), ())
    assert report.unchanged_count == 3
    assert report.tests_needing_review == ()


def test_edited_text_flags_exactly_the_linked_tests_with_the_cause() -> None:
    baseline = record_baseline([R1, R2, R3])
    edited = RequirementRecord("REQ-1", "Scaling", "The tool shall scale to 12 bits.")
    report = detect_changes(baseline, [edited, R2, R3], _associations())

    assert report.changed == ("REQ-1",)
    assert report.test_ids_needing_review == ("t.a", "t.b")
    reasons = {t.test_id: [(r.requirement_id, r.kind) for r in t.reasons] for t in report.tests_needing_review}
    assert reasons == {"t.a": [("REQ-1", "changed")], "t.b": [("REQ-1", "changed")]}


def test_a_test_linked_to_two_changed_requirements_lists_both_causes() -> None:
    baseline = record_baseline([R1, R2, R3])
    e1 = RequirementRecord("REQ-1", "Scaling", "changed one")
    e2 = RequirementRecord("REQ-2", "Range", "changed two")
    report = detect_changes(baseline, [e1, e2, R3], _associations())

    shared = next(t for t in report.tests_needing_review if t.test_id == "t.b")
    assert [r.requirement_id for r in shared.reasons] == ["REQ-1", "REQ-2"]
    assert report.test_ids_needing_review == ("t.a", "t.b", "t.c")


def test_title_edits_count_as_changes() -> None:
    baseline = record_baseline([R1])
    renamed = RequirementRecord("REQ-1", "New title", R1.text)
    assert detect_changes(baseline, [renamed], _associations()).changed == ("REQ-1",)


def test_removed_requirement_flags_its_tests() -> None:
    baseline = record_baseline([R1, R2, R3])
    report = detect_changes(baseline, [R1, R2], _associations())

    assert report.removed == ("REQ-3",)
    assert report.test_ids_needing_review == ("t.d",)
    assert report.tests_needing_review[0].reasons[0].kind == "removed"


def test_new_requirement_without_baseline_is_flagged_not_assumed_reviewed() -> None:
    baseline = record_baseline([R1, R2])
    report = detect_changes(baseline, [R1, R2, R3], _associations())

    assert report.new == ("REQ-3",)
    assert report.unchanged_count == 2
    assert report.test_ids_needing_review == ("t.d",)


def test_crlf_checkout_is_not_a_change_but_whitespace_edits_are() -> None:
    multi = RequirementRecord("REQ-1", "T", "line one\nline two")
    baseline = record_baseline([multi])
    crlf = RequirementRecord("REQ-1", "T", "line one\r\nline two")
    spaced = RequirementRecord("REQ-1", "T", "line one \nline two")

    assert detect_changes(baseline, [crlf], _associations()).changed == ()
    assert detect_changes(baseline, [spaced], _associations()).changed == ("REQ-1",)
    assert requirement_digest(multi) == requirement_digest(crlf)


def test_title_text_boundary_is_part_of_the_digest() -> None:
    assert requirement_digest(RequirementRecord("R", "ab", "c")) != requirement_digest(RequirementRecord("R", "a", "bc"))


def test_mark_reviewed_clears_only_the_named_requirements() -> None:
    baseline = record_baseline([R1, R2])
    e1 = RequirementRecord("REQ-1", "Scaling", "changed one")
    e2 = RequirementRecord("REQ-2", "Range", "changed two")

    updated = mark_reviewed(baseline, [e1, e2], ["REQ-1"])
    report = detect_changes(updated, [e1, e2], _associations())

    assert report.changed == ("REQ-2",)
    assert report.test_ids_needing_review == ("t.b", "t.c")


def test_mark_reviewed_can_baseline_a_new_requirement() -> None:
    updated = mark_reviewed(record_baseline([R1]), [R1, R3], ["REQ-3"])
    assert detect_changes(updated, [R1, R3], _associations()).new == ()


def test_mark_reviewed_refuses_an_unknown_requirement() -> None:
    with pytest.raises(TrcError) as excinfo:
        mark_reviewed(record_baseline([R1]), [R1], ["REQ-404"])
    assert excinfo.value.reason == "unknown_requirement"


def test_duplicate_requirement_ids_are_refused() -> None:
    with pytest.raises(TrcError) as excinfo:
        record_baseline([R1, R1])
    assert excinfo.value.reason == "duplicate_requirement"
    with pytest.raises(TrcError):
        detect_changes(record_baseline([R1]), [R1, R1], _associations())


def test_stale_tests_stop_counting_toward_verdicts() -> None:
    """Fed into the matrix, a changed requirement's passing tests no longer verify it."""
    baseline = record_baseline([R1, R2, R3])
    edited = RequirementRecord("REQ-1", "Scaling", "changed")
    report = detect_changes(baseline, [edited, R2, R3], _associations())
    statuses = dict.fromkeys(("t.a", "t.b", "t.c", "t.d"), "pass")

    fresh = build_matrix(_associations(), statuses)
    stale = build_matrix(_associations(), statuses, unreviewed_tests=report.test_ids_needing_review)

    assert {r.requirement_id: r.verdict for r in fresh.rows} == {"REQ-1": "pass", "REQ-2": "pass", "REQ-3": "pass"}
    assert {r.requirement_id: r.verdict for r in stale.rows} == {"REQ-1": "unverified", "REQ-2": "pass", "REQ-3": "pass"}


def test_report_and_baseline_are_deterministic() -> None:
    first = dump_baseline(record_baseline([R3, R1, R2]))
    assert first == dump_baseline(record_baseline([R1, R2, R3]))
    a = detect_changes(record_baseline([R1]), [R1, R2], _associations()).to_dict()
    b = detect_changes(record_baseline([R1]), [R2, R1], _associations()).to_dict()
    assert a == b


def test_baseline_roundtrips() -> None:
    baseline = record_baseline([R1, R2])
    assert load_baseline(dump_baseline(baseline)) == baseline


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("{nope", "invalid_baseline"),
        ("[]", "unsupported_baseline_version"),
        ('{"baseline_version": "2", "digests": {}}', "unsupported_baseline_version"),
        ('{"baseline_version": "1", "digests": []}', "invalid_baseline"),
        ('{"baseline_version": "1", "digests": {"R": "xyz"}}', "invalid_baseline"),
        ('{"baseline_version": "1", "digests": {"has space": "' + "a" * 64 + '"}}', "invalid_baseline"),
    ],
)
def test_loader_refuses_bad_baselines(text: str, reason: str) -> None:
    with pytest.raises(TrcError) as excinfo:
        load_baseline(text)
    assert excinfo.value.reason == reason


def test_empty_baseline_flags_every_requirement_as_new() -> None:
    report = detect_changes(record_baseline([]), [R1, R2], _associations())
    assert report.new == ("REQ-1", "REQ-2")
    assert json.dumps(report.to_dict(), sort_keys=True)
