# implements: DSN-TCM-060
"""Test independence: order planning and the order-independence check (WP-TCM-04).

Test cases must be independent — execution order must not affect results
(TOOL-TCD-090). Two mechanisms serve that:

- ``execution_order`` plans the run order: declared order without a seed, a
  deterministic seeded shuffle with one. The seed is recorded with the run
  (SDD-002 §6 ``order_seed``), so an order-dependent failure is reproducible
  rather than latent (DSN-TCM-060).
- ``check_order_independence`` compares two result sets for the same
  allocations under different orders — the analysis evidence behind
  TOOL-TCD-090's A verification.

Satisfies: TOOL-TCD-090; DSN-TCM-060.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from ectt.tcm.datacases import DataDrivenTestCase

__all__ = [
    "execution_order",
    "IndependenceReport",
    "check_order_independence",
]


def execution_order(
    cases: Iterable[DataDrivenTestCase],
    *,
    order_seed: int | None = None,
) -> tuple[str, ...]:
    """Plan execution order: declared order, or a deterministic seeded shuffle.

    The shuffle uses an explicitly seeded generator — never ``hash()`` or
    ``PYTHONHASHSEED`` — so the same seed yields the same order everywhere.
    The seed is what the run records as ``order_seed``.
    """
    ids = [case.case_id for case in cases]
    if order_seed is None:
        return tuple(ids)
    shuffled = list(ids)
    random.Random(order_seed).shuffle(shuffled)
    return tuple(shuffled)


@dataclass(frozen=True)
class IndependenceReport:
    """Outcome of comparing two runs that differ only in execution order."""

    order_independent: bool
    divergent: tuple[str, ...]


def check_order_independence(
    first: Mapping[str, str],
    second: Mapping[str, str],
) -> IndependenceReport:
    """Compare per-test outcomes from two orders over the same allocations.

    ``first`` and ``second`` map test id to outcome. A test is divergent when
    its outcome differs between the runs, or when it appears in only one —
    a full-suite re-run under a different order must execute the same set.
    """
    ids = sorted(set(first) | set(second))
    divergent = tuple(
        test_id for test_id in ids if first.get(test_id) != second.get(test_id)
    )
    return IndependenceReport(
        order_independent=not divergent,
        divergent=divergent,
    )
