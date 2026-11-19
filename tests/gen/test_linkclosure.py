"""Tests for the WP-GEN-05 link closure.

Verifies: TOOL-HAR-120.
"""

from __future__ import annotations

import pytest

from ectt.gen import (
    RESOLVED_BY_STUB,
    LinkClosureReport,
    UnresolvedReferenceError,
    assert_closed,
    resolve_link_closure,
)


def test_every_reference_resolves_by_one_mechanism() -> None:
    """verifies: TOOL-HAR-120"""
    report = resolve_link_closure(
        ("memset", "hal_read", "vendor_init"),
        stubs=("memset", "hal_read"),
        user_linkage=("vendor_init",),
    )
    assert report.closed
    mechanisms = {r.reference: r.resolved_by for r in report.resolved}
    assert mechanisms == {
        "hal_read": RESOLVED_BY_STUB,
        "memset": RESOLVED_BY_STUB,
        "vendor_init": "user_linkage",
    }


def test_unresolved_references_reported() -> None:
    """verifies: TOOL-HAR-120"""
    report = resolve_link_closure(("memset", "psychic_api"), stubs=("memset",))
    assert report.unresolved == ("psychic_api",)
    assert report.closed is False


def test_closure_is_enforced_not_implied() -> None:
    """verifies: TOOL-HAR-120"""
    report = resolve_link_closure(("memset", "missing_a", "missing_b"), stubs=("memset",))
    with pytest.raises(UnresolvedReferenceError) as excinfo:
        assert_closed(report)
    assert "missing_a" in str(excinfo.value)
    assert "missing_b" in str(excinfo.value)
    assert_closed(resolve_link_closure(("memset",), stubs=("memset",)))


def test_empty_reference_list_closes() -> None:
    """verifies: TOOL-HAR-120"""
    report = resolve_link_closure(())
    assert report.closed and report.resolved == () and report.unresolved == ()
    assert_closed(report)


def test_duplicate_references_deduplicated() -> None:
    """verifies: TOOL-HAR-120"""
    report = resolve_link_closure(("memset", "memset", "memset"), stubs=("memset",))
    assert len(report.resolved) == 1


def test_stub_wins_over_user_linkage() -> None:
    """verifies: TOOL-HAR-120"""
    report = resolve_link_closure(
        ("memset",), stubs=("memset",), user_linkage=("memset",)
    )
    assert report.resolved[0].resolved_by == RESOLVED_BY_STUB


def test_report_is_deterministic_and_serialisable() -> None:
    """verifies: TOOL-HAR-120"""
    first = resolve_link_closure(("z", "a", "m"), stubs=("a",))
    second = resolve_link_closure(("a", "m", "z"), stubs=("a",))
    assert first.to_dict() == second.to_dict()
    assert isinstance(first, LinkClosureReport)
