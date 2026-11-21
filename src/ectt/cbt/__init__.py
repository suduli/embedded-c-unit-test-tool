# implements: TOOL-CBT-010, TOOL-CBT-020
"""Compiled-suite lifecycle: re-execution, impact analysis, subset runs (CMP-CBT)."""

from ectt.cbt.compare import (
    CoverageComparison,
    MetricDelta,
    RunComparison,
    compare_coverage,
    compare_runs,
    run_outcomes,
)
from ectt.cbt.errors import CbtError
from ectt.cbt.impact import ImpactResult, SourceChange, affected_cases
from ectt.cbt.minimize import Minimization, minimize_suite
from ectt.cbt.reexecute import (
    SUITE_RECORD_VERSION,
    CompiledSuiteRecord,
    ParallelReExecution,
    ReExecution,
    ReExecutionSpec,
    SubsetReExecution,
    bindings_from_cases,
    current_digests,
    dump_suite_record,
    load_suite_record,
    record_compiled_suite,
    reexecute_isolated,
    reexecute_parallel,
    reexecute_subset,
    reexecute_suite,
)

__all__ = [
    "SUITE_RECORD_VERSION",
    "CbtError",
    "CompiledSuiteRecord",
    "CoverageComparison",
    "ImpactResult",
    "MetricDelta",
    "Minimization",
    "RunComparison",
    "ParallelReExecution",
    "ReExecution",
    "ReExecutionSpec",
    "SourceChange",
    "SubsetReExecution",
    "affected_cases",
    "bindings_from_cases",
    "compare_coverage",
    "compare_runs",
    "minimize_suite",
    "current_digests",
    "dump_suite_record",
    "load_suite_record",
    "record_compiled_suite",
    "reexecute_isolated",
    "reexecute_parallel",
    "reexecute_subset",
    "reexecute_suite",
    "run_outcomes",
]
