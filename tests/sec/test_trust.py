"""Tests for the WP-SEC-03 untrusted-project warning gate.

Verifies: TOOL-SEC-050.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ectt.sec import (
    TrustDecision,
    TrustRecordError,
    UntrustedProjectTracker,
    warning_text,
)


def test_unknown_project_is_untrusted(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")
    decision = tracker.decision(tmp_path)
    assert decision == TrustDecision(
        project_root=tmp_path.resolve().as_posix(), known=False
    )
    assert decision.requires_warning is True


def test_missing_record_behaves_as_nothing_trusted(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    tracker = UntrustedProjectTracker(tmp_path / "absent" / "trust.json")
    assert tracker.decision(tmp_path).known is False


def test_mark_opened_persists_and_project_becomes_known(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    record = tmp_path / "trust.json"
    tracker = UntrustedProjectTracker(record)
    tracker.mark_opened(tmp_path)
    assert tracker.decision(tmp_path).known is True
    assert tracker.decision(tmp_path).requires_warning is False
    document = json.loads(record.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1
    assert tmp_path.resolve().as_posix() in document["projects"]


def test_mark_opened_is_idempotent(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")
    tracker.mark_opened(tmp_path)
    tracker.mark_opened(tmp_path)
    document = json.loads((tmp_path / "trust.json").read_text(encoding="utf-8"))
    assert document["projects"].count(tmp_path.resolve().as_posix()) == 1


def test_record_is_deterministic_sorted_json(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    first = tmp_path / "a"
    second = tmp_path / "b"
    first.mkdir()
    second.mkdir()
    tracker_one = UntrustedProjectTracker(tmp_path / "one.json")
    tracker_two = UntrustedProjectTracker(tmp_path / "two.json")
    tracker_one.mark_opened(second)
    tracker_one.mark_opened(first)
    tracker_two.mark_opened(first)
    tracker_two.mark_opened(second)
    assert (tmp_path / "one.json").read_bytes() == (tmp_path / "two.json").read_bytes()


def test_warning_text_names_project_and_code_kinds(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")
    decision = tracker.decision(tmp_path)
    text = warning_text(decision)
    assert decision.project_root in text
    for kind in ("test cases", "stub bodies", "build scripts"):
        assert kind in text
    assert text.startswith("Warning:")


def test_known_project_produces_no_warning_requirement(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    tracker = UntrustedProjectTracker(tmp_path / "trust.json")
    tracker.mark_opened(tmp_path)
    decision = tracker.decision(tmp_path)
    assert decision.requires_warning is False


def test_malformed_record_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    record = tmp_path / "trust.json"
    record.write_text("{broken", encoding="utf-8")
    tracker = UntrustedProjectTracker(record)
    with pytest.raises(TrustRecordError):
        tracker.decision(tmp_path)


def test_wrongly_shaped_record_is_named_error(tmp_path: Path) -> None:
    """verifies: TOOL-SEC-050"""
    record = tmp_path / "trust.json"
    record.write_text(json.dumps({"projects": "not-a-list"}), encoding="utf-8")
    tracker = UntrustedProjectTracker(record)
    with pytest.raises(TrustRecordError):
        tracker.decision(tmp_path)
