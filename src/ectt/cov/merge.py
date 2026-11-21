# implements: TOOL-COV-110, TOOL-COV-120, TOOL-COV-180, TOOL-COV-220
"""Coverage merge across test executions with per-test attribution and quarantine.

Satisfies: TOOL-COV-110, TOOL-COV-120, TOOL-COV-180, and the PLAN-001 §5.4
recorded acceptance criterion for WP-COV-02 (the TOOL-COV-220 quarantine
semantics: a profile flushed by a run that then crashes is retained but
excluded from the aggregate until explicitly admitted per run; the aggregate
figure never includes quarantined data, and per-run provenance still shows it).

In the S3 result vocabulary (ectt.exh: ``pass | fail | error | timeout |
not_run``) a harness crash surfaces as outcome ``error``; there is no separate
``crash`` outcome to invent. ``not_run`` cannot carry a coverage artifact (the
test never executed), which the completeness gate handles.

Merge rules are conservative: counts sum, unexecuted flags OR, branch flags
must agree across contributing runs, condition outcomes merge by intersecting
the not-covered sets (a term is not-covered in the merge iff it was not-covered
in every contributing run), and an inconsistency is a named error — never
silently resolved.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ectt.cov.errors import CoverageError
from ectt.cov.metrics import MetricTotals, branch_coverage, statement_coverage
from ectt.cov.model import GcovBranch, GcovCondition, GcovDocument, GcovFile, GcovLine

__all__ = [
    "COMPLETENESS_STATES",
    "KNOWN_RUN_OUTCOMES",
    "QUARANTINE_OUTCOMES",
    "RunCoverage",
    "RunAdmission",
    "ExcludedRun",
    "MergeResult",
    "merge_run_coverage",
    "coverage_for_test",
]

#: Recorded completeness states for coverage artifacts (TOOL-COV-180).
COMPLETENESS_STATES: tuple[str, ...] = ("complete", "truncated", "missing")

#: S3 per-test outcome vocabulary (ectt.exh.results).
KNOWN_RUN_OUTCOMES: tuple[str, ...] = ("pass", "fail", "error", "timeout", "not_run")

#: Outcomes whose coverage artifacts are quarantined by default (TOOL-COV-220,
#: PLAN-001 §5.4 recorded criterion): the aggregate excludes them until a
#: recorded per-run admission decision explicitly admits them.
QUARANTINE_OUTCOMES: frozenset[str] = frozenset({"error", "timeout"})


@dataclass(frozen=True)
class RunCoverage:
    """One test execution's coverage artifact as recorded (never relabelled).

    ``completeness`` is one of :data:`COMPLETENESS_STATES`. A ``truncated``
    artifact may retain its partial ``document`` in per-run provenance; a
    ``missing`` artifact carries none. ``advisory`` is required whenever
    ``completeness`` is not ``complete`` and travels with the result for the
    report (TOOL-COV-180).
    """

    test_id: str
    outcome: str
    completeness: str
    document: GcovDocument | None = None
    advisory: str | None = None

    def __post_init__(self) -> None:
        if self.completeness not in COMPLETENESS_STATES:
            raise CoverageError(
                f"run '{self.test_id}' has unknown completeness state '{self.completeness}'",
                reason="unknown_completeness",
            )
        if self.outcome not in KNOWN_RUN_OUTCOMES:
            raise CoverageError(
                f"run '{self.test_id}' has unknown outcome '{self.outcome}'",
                reason="unknown_run_outcome",
            )
        if self.completeness == "complete" and self.document is None:
            raise CoverageError(
                f"run '{self.test_id}' is complete but carries no coverage document",
                reason="complete_run_without_document",
            )
        if self.completeness == "missing" and self.document is not None:
            raise CoverageError(
                f"run '{self.test_id}' is missing but carries a coverage document",
                reason="missing_run_with_document",
            )
        if self.completeness != "complete" and not self.advisory:
            raise CoverageError(
                f"run '{self.test_id}' is {self.completeness} but carries no advisory",
                reason="advisory_required",
            )


@dataclass(frozen=True)
class RunAdmission:
    """A recorded per-run admission decision (TOOL-COV-220).

    ``admitted=True`` explicitly admits a run the default rule quarantines;
    ``admitted=False`` explicitly denies a run the default rule would admit.
    """

    test_id: str
    admitted: bool
    reason: str


@dataclass(frozen=True)
class ExcludedRun:
    """A run excluded from the aggregate, with the reason and its advisory."""

    test_id: str
    outcome: str
    completeness: str
    reason: str  # "quarantined_outcome" | "denied_by_admission" | "incomplete_artifact"
    advisory: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "outcome": self.outcome,
            "completeness": self.completeness,
            "reason": self.reason,
            **({"advisory": self.advisory} if self.advisory is not None else {}),
        }


@dataclass(frozen=True)
class MergeResult:
    """Aggregate merged coverage plus per-run provenance and exclusions."""

    document: GcovDocument
    per_run: tuple[RunCoverage, ...]
    excluded: tuple[ExcludedRun, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "document": self.document.to_dict(),
            "per_run": [
                {
                    "test_id": run.test_id,
                    "outcome": run.outcome,
                    "completeness": run.completeness,
                    **({"advisory": run.advisory} if run.advisory is not None else {}),
                }
                for run in self.per_run
            ],
            "excluded": [excluded.to_dict() for excluded in self.excluded],
        }


def merge_run_coverage(
    runs: Sequence[RunCoverage],
    admissions: Mapping[str, RunAdmission] | None = None,
) -> MergeResult:
    """Merge per-run coverage into one aggregate (TOOL-COV-110).

    Admission rule (TOOL-COV-220, recorded §5.4 criterion): a run whose
    outcome is quarantined by default (``error``, ``timeout``) is excluded
    from the aggregate unless a recorded :class:`RunAdmission` admits it; a
    recorded denial excludes any run. An incomplete artifact (``truncated``/
    ``missing`` completeness) is always excluded and forces its constructs
    out of the aggregate; its advisory travels with the result (TOOL-COV-180).
    Every input run, excluded or not, stays visible in ``per_run`` provenance.
    """
    admissions = admissions or {}
    seen: set[str] = set()
    for run in runs:
        if run.test_id in seen:
            raise CoverageError(
                f"duplicate coverage record for test '{run.test_id}'",
                reason="duplicate_test_id",
            )
        seen.add(run.test_id)

    admitted_runs: list[RunCoverage] = []
    excluded: list[ExcludedRun] = []
    for run in runs:
        admission = admissions.get(run.test_id)
        if admission is not None and not admission.admitted:
            excluded.append(
                ExcludedRun(
                    test_id=run.test_id,
                    outcome=run.outcome,
                    completeness=run.completeness,
                    reason="denied_by_admission",
                    advisory=run.advisory,
                )
            )
            continue
        if run.completeness != "complete":
            excluded.append(
                ExcludedRun(
                    test_id=run.test_id,
                    outcome=run.outcome,
                    completeness=run.completeness,
                    reason="incomplete_artifact",
                    advisory=run.advisory,
                )
            )
            continue
        if run.outcome in QUARANTINE_OUTCOMES and not (admission is not None and admission.admitted):
            excluded.append(
                ExcludedRun(
                    test_id=run.test_id,
                    outcome=run.outcome,
                    completeness=run.completeness,
                    reason="quarantined_outcome",
                    advisory=run.advisory,
                )
            )
            continue
        admitted_runs.append(run)

    merged = _merge_documents([run.document for run in admitted_runs if run.document is not None])
    return MergeResult(
        document=merged,
        per_run=tuple(runs),
        excluded=tuple(excluded),
    )


def coverage_for_test(run: RunCoverage) -> dict[str, MetricTotals]:
    """Per-test statement/branch totals from one run's own record (TOOL-COV-120)."""
    if run.document is None:
        return {
            "statements": MetricTotals(covered=0, total=0),
            "branches": MetricTotals(covered=0, total=None),
        }
    return {
        "statements": statement_coverage(run.document.files),
        "branches": branch_coverage(run.document.files),
    }


def _merge_documents(documents: Sequence[GcovDocument]) -> GcovDocument:
    if not documents:
        return GcovDocument(format_version="0", gcc_version="", data_file="", files=())
    first = documents[0]
    for doc in documents[1:]:
        if doc.format_version != first.format_version:
            raise CoverageError(
                "cannot merge coverage documents of different gcov format versions "
                f"({first.format_version!r} and {doc.format_version!r})",
                reason="format_version_mismatch",
            )
        if doc.gcc_version != first.gcc_version:
            raise CoverageError(
                "cannot merge coverage documents of different compiler versions "
                f"({first.gcc_version!r} and {doc.gcc_version!r})",
                reason="gcc_version_mismatch",
            )

    files_by_path: dict[str, GcovFile] = {}
    for doc in documents:
        for file in doc.files:
            files_by_path.setdefault(file.file, GcovFile(file=file.file, lines=()))
            files_by_path[file.file] = _merge_files(files_by_path[file.file], file, file.file)
    merged_files = tuple(files_by_path[path] for path in sorted(files_by_path))
    return GcovDocument(
        format_version=first.format_version,
        gcc_version=first.gcc_version,
        data_file=first.data_file,
        files=merged_files,
        current_working_directory=first.current_working_directory,
    )


def _merge_files(existing: GcovFile, incoming: GcovFile, where: str) -> GcovFile:
    lines_by_number: dict[int, GcovLine] = {line.line_number: line for line in existing.lines}
    for line in incoming.lines:
        current = lines_by_number.get(line.line_number)
        if current is None:
            lines_by_number[line.line_number] = line
        else:
            lines_by_number[line.line_number] = _merge_lines(current, line, f"{where}:{line.line_number}")
    return GcovFile(file=existing.file, lines=tuple(lines_by_number[n] for n in sorted(lines_by_number)))


def _merge_lines(a: GcovLine, b: GcovLine, where: str) -> GcovLine:
    if len(a.branches) != len(b.branches):
        raise CoverageError(
            f"coverage records for {where} disagree on branch count "
            f"({len(a.branches)} vs {len(b.branches)}); refusing to merge differently "
            f"instrumented runs",
            reason="branch_count_mismatch",
        )
    merged_branches = tuple(_merge_branches(x, y, where) for x, y in zip(a.branches, b.branches, strict=True))

    if (a.conditions and not b.conditions) or (not a.conditions and b.conditions):
        raise CoverageError(
            f"coverage records for {where} disagree on condition instrumentation "
            f"({len(a.conditions)} vs {len(b.conditions)} condition records); an "
            f"unrecorded outcome may not be assumed covered",
            reason="condition_presence_mismatch",
        )
    if len(a.conditions) != len(b.conditions):
        raise CoverageError(
            f"coverage records for {where} disagree on the number of condition records "
            f"({len(a.conditions)} vs {len(b.conditions)})",
            reason="condition_record_count_mismatch",
        )
    merged_conditions = tuple(
        _merge_conditions(x, y, where) for x, y in zip(a.conditions, b.conditions, strict=True)
    )

    return GcovLine(
        line_number=a.line_number,
        count=a.count + b.count,
        unexecuted_block=a.unexecuted_block or b.unexecuted_block,
        function_name=a.function_name if a.function_name is not None else b.function_name,
        branches=merged_branches,
        conditions=merged_conditions,
    )


def _merge_branches(a: GcovBranch, b: GcovBranch, where: str) -> GcovBranch:
    if a.fallthrough is not None and b.fallthrough is not None and a.fallthrough != b.fallthrough:
        raise CoverageError(
            f"coverage records for {where} disagree on branch fallthrough flag",
            reason="branch_flag_mismatch",
        )
    if a.throw is not None and b.throw is not None and a.throw != b.throw:
        raise CoverageError(
            f"coverage records for {where} disagree on branch throw flag",
            reason="branch_flag_mismatch",
        )
    return GcovBranch(
        count=a.count + b.count,
        fallthrough=a.fallthrough if a.fallthrough is not None else b.fallthrough,
        throw=a.throw if a.throw is not None else b.throw,
        source_block_id=a.source_block_id if a.source_block_id is not None else b.source_block_id,
        destination_block_id=a.destination_block_id
        if a.destination_block_id is not None
        else b.destination_block_id,
    )


def _merge_conditions(a: GcovCondition, b: GcovCondition, where: str) -> GcovCondition:
    if a.count != b.count:
        raise CoverageError(
            f"coverage records for {where} disagree on condition outcome count "
            f"({a.count} vs {b.count})",
            reason="condition_count_mismatch",
        )
    # Conservative intersection: a term is not-covered-true in the merge iff it
    # was not-covered-true in EVERY contributing run (same for false); covered
    # is recomputed from the merged sets.
    not_true = tuple(sorted(set(a.not_covered_true) & set(b.not_covered_true)))
    not_false = tuple(sorted(set(a.not_covered_false) & set(b.not_covered_false)))
    covered = a.count - len(set(not_true) | set(not_false))
    return GcovCondition(count=a.count, covered=covered, not_covered_true=not_true, not_covered_false=not_false)
