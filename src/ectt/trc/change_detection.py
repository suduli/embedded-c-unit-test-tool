# implements: TOOL-TRC-090
"""Requirement change detection (WP-TRC-05, DSN-TRC-070).

TOOL-TRC-090: detect when a requirement has changed since its linked test
cases were last executed or reviewed. A :class:`ReviewBaseline` stores, per
requirement, a digest of its title and text taken when its links were last
reviewed or executed. :func:`detect_changes` compares the current requirement
inventory with it:

* ``changed``  - the digest differs;
* ``removed``  - in the baseline, absent now;
* ``new``      - present now, never baselined (nothing shows its links were ever
  reviewed against this text, so its tests are flagged rather than assumed fine).

Every test linked to a changed, removed or new requirement is reported as
needing review, with the requirement ids that caused it, so a silently edited
requirement stops silently invalidating evidence. Feed
``ChangeReport.test_ids_needing_review`` to ``build_matrix(unreviewed_tests=...)``
to have the verdicts stop counting those tests.

The digest normalises line endings only (CRLF/CR to LF) so a checkout on another
platform does not look like an edit; every other difference, whitespace
included, is a change.

Satisfies: TOOL-TRC-090.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from ectt.core.determinism import canonical_json, stable_id
from ectt.trc.associations import AssociationSet
from ectt.trc.errors import TrcError
from ectt.trc.imports import RequirementRecord

__all__ = [
    "BASELINE_VERSION",
    "ChangeReport",
    "ReviewBaseline",
    "ReviewReason",
    "TestReview",
    "detect_changes",
    "dump_baseline",
    "load_baseline",
    "mark_reviewed",
    "record_baseline",
    "requirement_digest",
]

BASELINE_VERSION = "1"
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def requirement_digest(record: RequirementRecord) -> str:
    """Digest of a requirement's title and text (line endings normalised)."""
    return stable_id("requirement-text", _lf(record.title), _lf(record.text))


@dataclass(frozen=True)
class ReviewBaseline:
    """Requirement id -> digest at the time its links were last reviewed or executed."""

    digests: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {"baseline_version": BASELINE_VERSION, "digests": dict(sorted(self.digests.items()))}


@dataclass(frozen=True)
class ReviewReason:
    """Why a test needs review: which requirement and how it changed."""

    requirement_id: str
    kind: str  # "changed" | "removed" | "new"


@dataclass(frozen=True)
class TestReview:
    """A test that needs re-review, with every cause."""

    test_id: str
    reasons: tuple[ReviewReason, ...]


@dataclass(frozen=True)
class ChangeReport:
    """Outcome of comparing the current requirements with a baseline."""

    changed: tuple[str, ...]
    removed: tuple[str, ...]
    new: tuple[str, ...]
    unchanged_count: int
    tests_needing_review: tuple[TestReview, ...]

    @property
    def test_ids_needing_review(self) -> tuple[str, ...]:
        return tuple(t.test_id for t in self.tests_needing_review)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed": list(self.changed),
            "new": list(self.new),
            "removed": list(self.removed),
            "tests_needing_review": [
                {
                    "reasons": [{"kind": r.kind, "requirement_id": r.requirement_id} for r in t.reasons],
                    "test_id": t.test_id,
                }
                for t in self.tests_needing_review
            ],
            "unchanged_count": self.unchanged_count,
        }


def _by_id(records: Iterable[RequirementRecord]) -> dict[str, RequirementRecord]:
    result: dict[str, RequirementRecord] = {}
    for record in records:
        if record.requirement_id in result:
            raise TrcError(f"duplicate requirement id '{record.requirement_id}'", reason="duplicate_requirement")
        result[record.requirement_id] = record
    return result


def record_baseline(records: Iterable[RequirementRecord]) -> ReviewBaseline:
    """Baseline every requirement in ``records`` as reviewed at its current text."""
    return ReviewBaseline({rid: requirement_digest(rec) for rid, rec in sorted(_by_id(records).items())})


def mark_reviewed(
    baseline: ReviewBaseline,
    records: Iterable[RequirementRecord],
    requirement_ids: Iterable[str],
) -> ReviewBaseline:
    """Return ``baseline`` with ``requirement_ids`` re-baselined at their current text.

    Used after the linked tests have been reviewed or re-executed. An id that is
    not in ``records`` is refused: a review of a requirement that does not exist
    would silently clear nothing.
    """
    current = _by_id(records)
    digests = dict(baseline.digests)
    for rid in requirement_ids:
        if rid not in current:
            raise TrcError(f"cannot mark unknown requirement '{rid}' as reviewed", reason="unknown_requirement")
        digests[rid] = requirement_digest(current[rid])
    return ReviewBaseline(dict(sorted(digests.items())))


def detect_changes(
    baseline: ReviewBaseline,
    records: Iterable[RequirementRecord],
    associations: AssociationSet,
) -> ChangeReport:
    """Compare ``records`` with ``baseline`` and flag the tests that need review."""
    current = _by_id(records)
    changed = sorted(rid for rid, rec in current.items() if rid in baseline.digests and baseline.digests[rid] != requirement_digest(rec))
    new = sorted(rid for rid in current if rid not in baseline.digests)
    removed = sorted(rid for rid in baseline.digests if rid not in current)
    unchanged = len(current) - len(changed) - len(new)

    causes: dict[str, list[ReviewReason]] = {}
    for kind, ids in (("changed", changed), ("removed", removed), ("new", new)):
        for rid in ids:
            for test_id in associations.tests_for(rid):
                causes.setdefault(test_id, []).append(ReviewReason(rid, kind))
    reviews = tuple(TestReview(test_id, tuple(sorted(reasons, key=lambda r: (r.requirement_id, r.kind)))) for test_id, reasons in sorted(causes.items()))
    return ChangeReport(tuple(changed), tuple(removed), tuple(new), unchanged, reviews)


def dump_baseline(baseline: ReviewBaseline) -> str:
    """Deterministic JSON text of the baseline."""
    return canonical_json(baseline.to_dict())


def load_baseline(text: str) -> ReviewBaseline:
    """Strictly load a baseline; refuses unknown versions and malformed digests."""
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        raise TrcError(f"baseline is not valid JSON: {exc}", reason="invalid_baseline") from exc
    if not isinstance(doc, dict) or doc.get("baseline_version") != BASELINE_VERSION:
        raise TrcError(
            f"unsupported baseline (expected baseline_version {BASELINE_VERSION!r})",
            reason="unsupported_baseline_version",
        )
    digests = doc.get("digests")
    if not isinstance(digests, dict):
        raise TrcError("'digests' must be an object", reason="invalid_baseline")
    for rid, digest in digests.items():
        if not rid or any(c.isspace() for c in rid) or not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
            raise TrcError(f"baseline entry '{rid}' is malformed", reason="invalid_baseline")
    return ReviewBaseline(dict(sorted(digests.items())))
