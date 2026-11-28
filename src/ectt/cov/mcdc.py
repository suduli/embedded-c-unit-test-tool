# implements: TOOL-COV-050, TOOL-COV-060, TOOL-COV-070, TOOL-COV-080, TOOL-COV-190
"""Masking MC/DC results from GCC condition records (WP-COV-05, WP-COV-06).

Input is one gcov document (merge several runs with
:func:`ectt.cov.merge.merge_run_coverage` first) and, when available, the
decisions of the analysis model (schema 1.6).

Every result states the form (``masking``) and the mechanism (GCC
``-fcondition-coverage``) with the compiler version. Nothing unmeasured is
ever counted as covered or as zero:

* MC/DC unavailable for the compiler: status ``unmeasured`` with that reason.
* A decision with no GCC record is ``unmeasured``; it is called over the
  limit only when its condition count exceeds the *probed* maximum passed in,
  never from a constant held here.
* A record that matches no known decision is still counted and listed
  without expression text, and which outcome was seen is unknown (None).
* GCC reports a condition under an odd number of ``!`` inverted; this is
  undone using the analyzer's ``negated`` flag. GCC may also swap the arms
  of a ternary whose condition has a ``!``, so there it is unknown too.
* Without decisions from the analyzer, ``decisions_known`` is False: nothing
  can then be said about decisions the compiler skipped.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any, Protocol

from ectt.cov.errors import CoverageError
from ectt.cov.model import GcovDocument

__all__ = [
    "MCDC_FORM",
    "MCDC_MECHANISM",
    "ConditionStatus",
    "DecisionCoverage",
    "McdcResult",
    "UnmeasuredDecision",
    "measure_mcdc",
]

MCDC_FORM = "masking"
MCDC_MECHANISM = "gcc -fcondition-coverage"


class _Condition(Protocol):
    @property
    def expression(self) -> str: ...

    @property
    def constant(self) -> bool: ...

    @property
    def negated(self) -> bool: ...


class _Decision(Protocol):
    """The parts of an analysis-model decision this module reads."""

    @property
    def function(self) -> str: ...

    @property
    def kind(self) -> str: ...

    @property
    def line(self) -> int: ...

    @property
    def start_line(self) -> int: ...

    @property
    def end_line(self) -> int: ...

    @property
    def expression(self) -> str: ...

    @property
    def conditions(self) -> Sequence[_Condition]: ...


@dataclass(frozen=True)
class ConditionStatus:
    """One condition of a measured decision (TOOL-COV-070).

    ``seen_true`` / ``seen_false`` refer to the condition as written in the
    source, and are None when the direction cannot be known.
    """

    index: int
    expression: str | None
    seen_true: bool | None
    seen_false: bool | None


@dataclass(frozen=True)
class DecisionCoverage:
    """One decision GCC recorded. Each condition has two outcomes."""

    file: str
    function: str | None
    line: int
    expression: str | None
    conditions: tuple[ConditionStatus, ...]
    covered: int  # outcomes covered; known even when their direction is not

    @property
    def total(self) -> int:
        return 2 * len(self.conditions)


@dataclass(frozen=True)
class UnmeasuredDecision:
    """A decision with no usable record, and why (TOOL-COV-080)."""

    function: str
    line: int
    expression: str
    conditions: int
    reason: str  # over_condition_limit | constant_decision | no_condition_record | ambiguous_record
    detail: str


@dataclass(frozen=True)
class McdcResult:
    """The MC/DC result of one source file."""

    file: str
    status: str  # "measured" | "unmeasured"
    reason: str | None
    compiler_version: str | None
    max_conditions: int | None
    decisions_known: bool
    decisions: tuple[DecisionCoverage, ...] = ()
    unmeasured: tuple[UnmeasuredDecision, ...] = ()
    form: str = MCDC_FORM
    mechanism: str = MCDC_MECHANISM

    @property
    def covered(self) -> int | None:
        return None if self.status != "measured" else sum(d.covered for d in self.decisions)

    @property
    def total(self) -> int | None:
        return None if self.status != "measured" else sum(d.total for d in self.decisions)

    @property
    def complete(self) -> bool:
        """True only when every known decision was measured."""
        return self.status == "measured" and self.decisions_known and not any(
            u.reason != "constant_decision" for u in self.unmeasured
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file,
            "status": self.status,
            "reason": self.reason,
            "form": self.form,
            "mechanism": self.mechanism,
            "compiler_version": self.compiler_version,
            "max_conditions": self.max_conditions,
            "decisions_known": self.decisions_known,
            "complete": self.complete,
            "covered": self.covered,
            "total": self.total,
            "decisions": [
                {
                    "function": d.function,
                    "line": d.line,
                    "expression": d.expression,
                    "conditions": [
                        {
                            "index": c.index,
                            "expression": c.expression,
                            "seen_true": c.seen_true,
                            "seen_false": c.seen_false,
                        }
                        for c in d.conditions
                    ],
                }
                for d in self.decisions
            ],
            "unmeasured": [
                {
                    "function": u.function,
                    "line": u.line,
                    "expression": u.expression,
                    "conditions": u.conditions,
                    "reason": u.reason,
                    "detail": u.detail,
                }
                for u in self.unmeasured
            ],
        }


def _records(document: GcovDocument, file: str) -> list[DecisionCoverage] | None:
    """The condition records of one file, or None when the file is absent."""
    matching = [f for f in document.files if f.file == file]
    if not matching:
        return None
    found: list[DecisionCoverage] = []
    for gcov_file in matching:
        for line in gcov_file.lines:
            for record in line.conditions:
                terms = record.count // 2
                not_true, not_false = set(record.not_covered_true), set(record.not_covered_false)
                consistent = (
                    record.count % 2 == 0
                    and record.covered == record.count - len(not_true) - len(not_false)
                    and all(0 <= term < terms for term in not_true | not_false)
                )
                if not consistent:
                    raise CoverageError(
                        f"condition record at {file}:{line.line_number} is inconsistent "
                        f"(count={record.count}, covered={record.covered})",
                        reason="inconsistent_condition_record",
                    )
                found.append(
                    DecisionCoverage(
                        file=file,
                        function=line.function_name,
                        line=line.line_number,
                        expression=None,
                        conditions=tuple(
                            ConditionStatus(i, None, i not in not_true, i not in not_false) for i in range(terms)
                        ),
                        covered=record.covered,
                    )
                )
    return found


def _named(record: DecisionCoverage, decision: _Decision) -> DecisionCoverage:
    """Attach source text and restore each condition's direction as written.

    GCC numbers the non-constant conditions in order.
    """
    written = [c for c in decision.conditions if not c.constant]
    swappable = decision.kind == "ternary" and any(c.negated for c in written)

    def restore(status: ConditionStatus) -> ConditionStatus:
        source = written[status.index]
        if swappable:
            return replace(status, expression=source.expression, seen_true=None, seen_false=None)
        true, false = status.seen_true, status.seen_false
        if source.negated:
            true, false = false, true
        return replace(status, expression=source.expression, seen_true=true, seen_false=false)

    return replace(record, expression=decision.expression, conditions=tuple(map(restore, record.conditions)))


def _width(decision: _Decision) -> int:
    return sum(not c.constant for c in decision.conditions)


def _match(
    records: list[DecisionCoverage], decisions: Sequence[_Decision]
) -> tuple[list[DecisionCoverage], dict[int, str]]:
    """Name records after decisions; return unmatched decisions with a reason."""
    named = list(records)
    free_records = set(range(len(records)))
    problems: dict[int, str] = {}
    open_decisions = [i for i, d in enumerate(decisions) if _width(d) > 0]

    # Pass 1: same function, predicted line and condition count, in order. When
    # fewer records than decisions share that key, which one is missing is unknown.
    keys: dict[tuple[str, int, int], list[int]] = {}
    for i in open_decisions:
        keys.setdefault((decisions[i].function, decisions[i].line, _width(decisions[i])), []).append(i)
    for (function, line, width), members in keys.items():
        candidates = sorted(
            r for r in free_records
            if (records[r].function, records[r].line, len(records[r].conditions)) == (function, line, width)
        )
        if not candidates:
            continue
        if len(candidates) != len(members):
            for i in members:
                problems[i] = "ambiguous_record"
            free_records -= set(candidates)
            continue
        for i, r in zip(members, candidates, strict=True):
            named[r] = _named(records[r], decisions[i])
            free_records.discard(r)
            open_decisions.remove(i)

    # Pass 2: the line prediction missed; accept only a unique pairing inside the span.
    for i in list(open_decisions):
        if i in problems:
            continue
        decision = decisions[i]
        candidates = [
            r for r in free_records
            if records[r].function == decision.function
            and decision.start_line <= records[r].line <= decision.end_line
            and len(records[r].conditions) == _width(decision)
        ]
        if len(candidates) == 1:
            named[candidates[0]] = _named(records[candidates[0]], decision)
            free_records.discard(candidates[0])
            open_decisions.remove(i)

    for i in open_decisions:
        problems.setdefault(i, "no_condition_record")
    return named, problems


def measure_mcdc(
    document: GcovDocument | None,
    file: str,
    *,
    decisions: Sequence[_Decision] | None = None,
    unavailable_reason: str | None = None,
    max_conditions: int | None = None,
) -> McdcResult:
    """Measure masking MC/DC for ``file``.

    ``decisions`` are that file's analysis-model decisions (None when not
    extracted). ``unavailable_reason`` is set when the compiler cannot do
    MC/DC. ``max_conditions`` is the probed limit, or None when unknown.
    """

    def unmeasured(reason: str, version: str | None) -> McdcResult:
        return McdcResult(
            file=file,
            status="unmeasured",
            reason=reason,
            compiler_version=version,
            max_conditions=max_conditions,
            decisions_known=decisions is not None,
        )

    version = None if document is None else document.gcc_version
    if unavailable_reason is not None:
        return unmeasured(unavailable_reason, version)
    if document is None:
        return unmeasured("no_coverage_data", None)
    records = _records(document, file)
    if records is None:
        return unmeasured("no_data_for_file", version)

    expected = decisions is not None and any(_width(d) > 0 for d in decisions)
    if not records and (decisions is None or expected):
        # No record anywhere: the build most likely lacked -fcondition-coverage.
        return unmeasured("no_condition_data", version)

    skipped: list[UnmeasuredDecision] = []
    if decisions is not None:
        records, problems = _match(records, decisions)
        for i, decision in enumerate(decisions):
            width = _width(decision)
            if width == 0:
                reason, detail = "constant_decision", "every condition is constant; GCC records nothing"
            elif i not in problems:
                continue
            elif max_conditions is not None and width > max_conditions:
                reason = "over_condition_limit"
                detail = f"{width} conditions exceed the probed maximum of {max_conditions}"
            elif problems[i] == "ambiguous_record":
                reason, detail = "ambiguous_record", "records on this line cannot be told apart"
            else:
                reason, detail = "no_condition_record", "GCC recorded nothing; the cause is not known"
            skipped.append(
                UnmeasuredDecision(decision.function, decision.line, decision.expression, width, reason, detail)
            )

    # A record nobody named has no known direction.
    records = [
        r
        if r.expression is not None
        else replace(r, conditions=tuple(replace(c, seen_true=None, seen_false=None) for c in r.conditions))
        for r in records
    ]

    return McdcResult(
        file=file,
        status="measured",
        reason=None,
        compiler_version=version,
        max_conditions=max_conditions,
        decisions_known=decisions is not None,
        decisions=tuple(records),
        unmeasured=tuple(skipped),
    )
