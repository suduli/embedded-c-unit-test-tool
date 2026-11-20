# implements: TOOL-CIC-060
"""CI sharding and report merge (WP-CLI-05).

Two halves of one CI concern:

- ``shard_suite`` deterministically partitions a test suite across N CI
  runners: tests are assigned round-robin over their sorted order, so the
  partition is a pure function of the suite contents (input order, machine,
  and hash seed never leak in), shards differ in size by at most one, and
  every test lands in exactly one shard.
- ``merge_reports`` merges the per-runner reports back into one report
  model. Tests are unioned (a test that ran twice is refused — that is a
  scheduling bug, not a fact to paper over); per-unit coverage totals must
  agree across shards (they measure the same unit) and the merged covered
  count is the maximum, a documented lower bound on the true union — CI
  reports may understate coverage but never overstate it.

Satisfies: TOOL-CIC-060.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from ectt.cli.errors import CliError
from ectt.core.determinism import Clock
from ectt.core.provenance import build_provenance
from ectt.rep.errors import ReportModelError
from ectt.rep.model import CoverageEntry, ReportModel, TestEntry

__all__ = [
    "merge_reports",
    "shard_suite",
]


def shard_suite(test_ids: Iterable[str], shard_count: int) -> tuple[tuple[str, ...], ...]:
    """Partition test ids deterministically across ``shard_count`` runners.

    Round-robin over the sorted ids: order-free input, order-free output,
    sizes within one of each other. ``shard_count`` must be >= 1; more
    runners than tests yield empty trailing shards (a runner with no work).
    """
    if not isinstance(shard_count, int) or isinstance(shard_count, bool) or shard_count < 1:
        raise CliError(
            f"shard count must be a positive integer, got {shard_count!r}",
            reason="invalid_shard_count",
        )
    ordered = sorted(set(test_ids))
    mutable: list[list[str]] = [[] for _ in range(shard_count)]
    for index, test_id in enumerate(ordered):
        mutable[index % shard_count].append(test_id)
    return tuple(tuple(shard) for shard in mutable)


def merge_reports(models: Sequence[ReportModel], *, clock: Clock) -> ReportModel:
    """Merge per-runner shard reports into one report model (TOOL-CIC-060).

    - Tests: the union, sorted; a test id present in two shards is refused
      (``duplicate_test``) — shards run disjoint suites by construction.
    - Coverage: per unit, the totals of every shard must agree
      (``conflicting_coverage`` otherwise — they measured the same unit);
      the merged covered count is the maximum, a documented lower bound on
      the true union (never an overstatement).
    - The merged run id is the sorted shard run ids joined with ``+``;
      ``partial`` is true when any shard was partial. Execution facts are
      not merged (shards may run on different runners and toolchains); the
      provenance records each shard's report id as an input digest.
    """
    if not models:
        raise CliError("no shard reports to merge", reason="no_reports")

    entries: dict[str, TestEntry] = {}
    coverage_max: dict[str, tuple[int, int]] = {}
    run_ids: list[str] = []
    any_partial = False
    for model in models:
        if not isinstance(model, ReportModel):
            raise TypeError(f"Expected ReportModel, got {type(model).__name__}")
        run_ids.append(model.run_id)
        any_partial = any_partial or model.partial
        for entry in model.tests:
            if entry.test_id in entries:
                raise ReportModelError(
                    f"test '{entry.test_id}' appears in more than one shard report",
                    reason="duplicate_test",
                )
            entries[entry.test_id] = entry
        for unit, (covered, total) in model.coverage_figures().items():
            known = coverage_max.get(unit)
            if known is not None and known[1] != total:
                raise ReportModelError(
                    f"shard reports disagree on the total for unit '{unit}': "
                    f"{known[1]} vs {total}",
                    reason="conflicting_coverage",
                )
            if known is None or covered > known[0]:
                coverage_max[unit] = (covered, total)

    run_id = "+".join(sorted(run_ids))
    provenance = build_provenance(
        clock=clock,
        schema_versions={"report_model": "1.1"},
        input_digests={f"shard[{index}]": model.report_id for index, model in enumerate(models)},
    )
    merged = ReportModel(
        report_id="",
        run_id=run_id,
        tests=tuple(entries[key] for key in sorted(entries)),
        coverage=tuple(
            CoverageEntry(unit=unit, covered=coverage_max[unit][0], total=coverage_max[unit][1])
            for unit in sorted(coverage_max)
        ),
        partial=any_partial,
        generated_at=clock.isoformat(),
        execution=None,
        provenance=provenance,
    )
    # Give the merged report the same digest discipline as every other report:
    # recompute the id over its canonical body.
    from ectt.rep.model import _make_model

    return _make_model(
        run_id=run_id,
        tests=merged.tests,
        coverage=merged.coverage,
        partial=merged.partial,
        generated_at=merged.generated_at,
        execution=None,
        provenance=merged.provenance,
    )
