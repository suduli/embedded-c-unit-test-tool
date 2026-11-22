# implements: TOOL-COV-140, TOOL-COV-150
"""Coverage-by-analysis justification with digest binding (CMP-COV).

Satisfies: TOOL-COV-140 (record a user-supplied justification for code that
cannot be covered by test; reports show it as justified rather than covered)
and TOOL-COV-150 (justifications record author, date and rationale, and are
invalidated when the associated source changes), plus the recorded PLAN-001
§5.4 acceptance criterion: editing a source line under an accepted
justification invalidates it, and the next report shows the construct as
uncovered rather than justified.

Binding granularity is deliberately the whole source file: a justification
records the source digest at acceptance time; when the current digest of that
file differs, the justification evaluates ``invalidated``. This is
conservative — editing any line of the file invalidates, so a stale
justification is never shown as valid.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ectt.cov.errors import CoverageError
from ectt.cov.model import GcovDocument

__all__ = [
    "LINE_STATUSES",
    "AnnotatedLine",
    "AnnotatedFile",
    "AnnotatedCoverage",
    "Justification",
    "compute_source_digest",
    "evaluate_justification",
    "annotate_coverage",
]

#: Per-line annotation vocabulary (TOOL-COV-140: justified rather than covered).
LINE_STATUSES: tuple[str, ...] = ("covered", "partial", "uncovered", "justified")

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def compute_source_digest(content: str) -> str:
    """SHA-256 of source content with line endings normalised to ``\\n``.

    The justification binds to this digest at acceptance time; the caller
    recomputes it from the current source to detect edits (TOOL-COV-150).
    """
    normalised = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Justification:
    """One accepted coverage-by-analysis justification (TOOL-COV-140/150).

    ``source_digest`` is the digest of the associated source file's content at
    acceptance time; ``author``/``date``/``rationale`` are mandatory
    (TOOL-COV-150); ``date`` is authored acceptance data, never a wall-clock
    read.
    """

    id: str
    file: str
    start_line: int
    end_line: int
    author: str
    date: str
    rationale: str
    source_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id or any(char.isspace() for char in self.id):
            raise CoverageError(
                f"justification id must be a non-empty string without whitespace, got {self.id!r}",
                reason="invalid_justification_id",
            )
        if not isinstance(self.file, str) or not self.file:
            raise CoverageError(
                f"justification '{self.id}' must name its source file",
                reason="invalid_justification_file",
            )
        if not isinstance(self.start_line, int) or isinstance(self.start_line, bool) or self.start_line < 1:
            raise CoverageError(
                f"justification '{self.id}' start_line must be a positive integer",
                reason="invalid_line_range",
            )
        if not isinstance(self.end_line, int) or isinstance(self.end_line, bool) or self.end_line < self.start_line:
            raise CoverageError(
                f"justification '{self.id}' end_line {self.end_line} is before start_line {self.start_line}",
                reason="invalid_line_range",
            )
        for field_name in ("author", "rationale"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise CoverageError(
                    f"justification '{self.id}' requires a non-empty {field_name} (TOOL-COV-150)",
                    reason="missing_justification_field",
                )
        if not isinstance(self.date, str) or not _DATE_RE.match(self.date):
            raise CoverageError(
                f"justification '{self.id}' date must be an ISO YYYY-MM-DD string, got {self.date!r}",
                reason="invalid_justification_date",
            )
        if not isinstance(self.source_digest, str) or not _DIGEST_RE.match(self.source_digest):
            raise CoverageError(
                f"justification '{self.id}' source_digest must be a 64-hex sha256 digest",
                reason="invalid_source_digest",
            )

    def covers_line(self, line_number: int) -> bool:
        """True when the line number lies inside the justified region."""
        return self.start_line <= line_number <= self.end_line

    def to_dict(self) -> dict[str, Any]:
        return {
            "author": self.author,
            "date": self.date,
            "end_line": self.end_line,
            "file": self.file,
            "id": self.id,
            "rationale": self.rationale,
            "source_digest": self.source_digest,
            "start_line": self.start_line,
        }


def evaluate_justification(justification: Justification, current_digest: str) -> str:
    """Evaluate a justification against the current source digest.

    Returns ``"valid"`` when the digests match and ``"invalidated"`` when the
    associated source changed (TOOL-COV-150, recorded §5.4 criterion). A
    missing digest never evaluates valid — callers must supply one.
    """
    if not isinstance(current_digest, str) or not _DIGEST_RE.match(current_digest):
        raise CoverageError(
            f"current digest for '{justification.file}' must be a 64-hex sha256 digest",
            reason="invalid_source_digest",
        )
    return "valid" if current_digest == justification.source_digest else "invalidated"


@dataclass(frozen=True)
class AnnotatedLine:
    """One instrumented line's base count and its report-facing status."""

    line_number: int
    count: int
    status: str  # one of LINE_STATUSES
    justification_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "justification_id": self.justification_id,
            "line_number": self.line_number,
            "status": self.status,
        }


@dataclass(frozen=True)
class AnnotatedFile:
    """One file's annotated lines plus its invalidated justification ids."""

    file: str
    lines: tuple[AnnotatedLine, ...]
    invalidated: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "invalidated": list(self.invalidated),
            "lines": [line.to_dict() for line in self.lines],
        }


@dataclass(frozen=True)
class AnnotatedCoverage:
    """A coverage document annotated with justification statuses."""

    files: tuple[AnnotatedFile, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "files": [f.to_dict() for f in self.files],
        }


def annotate_coverage(
    document: GcovDocument,
    justifications: Sequence[Justification],
    current_digests: Mapping[str, str],
) -> AnnotatedCoverage:
    """Annotate a coverage document per the justification ledger (TOOL-COV-140).

    For each instrumented line: a line covered by test reports ``covered``
    regardless of justifications; an uncovered line inside a region whose
    justification evaluates valid reports ``justified``; an uncovered line
    inside a region whose justification was invalidated (the recorded §5.4
    criterion) reports ``uncovered``, with the justification id listed in the
    file's ``invalidated`` advisories. Digests for every justified file are
    mandatory — an unverifiable justification never evaluates valid.
    """
    by_file: dict[str, list[Justification]] = {}
    for justification in justifications:
        by_file.setdefault(justification.file, []).append(justification)

    annotated: list[AnnotatedFile] = []
    for file in sorted(document.files, key=lambda f: f.file):
        file_justifications = by_file.get(file.file, ())
        invalidated: list[str] = []
        valid: list[Justification] = []
        if file_justifications:
            current_digest = current_digests.get(file.file)
            if current_digest is None:
                raise CoverageError(
                    f"no current digest supplied for justified file '{file.file}'; "
                    f"an unverifiable justification never evaluates valid",
                    reason="missing_current_digest",
                )
            for justification in file_justifications:
                if evaluate_justification(justification, current_digest) == "invalidated":
                    invalidated.append(justification.id)
                else:
                    valid.append(justification)

        lines: list[AnnotatedLine] = []
        for line in file.lines:
            if line.count > 0:
                status = "partial" if line.unexecuted_block else "covered"
                lines.append(AnnotatedLine(line_number=line.line_number, count=line.count, status=status))
                continue
            applicable = [j for j in valid if j.covers_line(line.line_number)]
            if applicable:
                owner = min(applicable, key=lambda j: j.id)
                lines.append(
                    AnnotatedLine(
                        line_number=line.line_number,
                        count=line.count,
                        status="justified",
                        justification_id=owner.id,
                    )
                )
            else:
                lines.append(AnnotatedLine(line_number=line.line_number, count=line.count, status="uncovered"))
        annotated.append(AnnotatedFile(file=file.file, lines=tuple(lines), invalidated=tuple(invalidated)))
    return AnnotatedCoverage(files=tuple(annotated))
