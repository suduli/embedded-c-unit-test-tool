# implements: TOOL-COV-010, TOOL-COV-020
"""Code coverage subsystem (CMP-COV).

Owns coverage artifacts produced from the compiler backend (ADR-004: GCC first,
``gcov --json-format``; Clang support is added later and must not shape this
package). WP-COV-01 scope: statement coverage (TOOL-COV-010) and
branch/decision coverage (TOOL-COV-020) read from the documented GCC gcov
JSON format.

Satisfies: TOOL-COV-010, TOOL-COV-020.
"""

from __future__ import annotations

from ectt.cov.errors import (
    CoverageError,
    CoverageFormatError,
    CoverageParseError,
)
from ectt.cov.gcov import KNOWN_FORMAT_VERSIONS, read_gcov_document
from ectt.cov.merge import (
    COMPLETENESS_STATES,
    KNOWN_RUN_OUTCOMES,
    QUARANTINE_OUTCOMES,
    ExcludedRun,
    MergeResult,
    RunAdmission,
    RunCoverage,
    coverage_for_test,
    merge_run_coverage,
)
from ectt.cov.metrics import (
    branch_coverage,
    call_coverage,
    document_metrics,
    function_coverage,
    statement_coverage,
)
from ectt.cov.model import (
    SCHEMA_VERSION_CURRENT,
    GcovBranch,
    GcovCall,
    GcovCondition,
    GcovDocument,
    GcovFile,
    GcovFunction,
    GcovLine,
    MetricTotals,
)
from ectt.cov.separation import (
    COVERAGE_ROLES,
    RoleCoverage,
    SeparatedCoverage,
    separate_coverage,
)
from ectt.cov.thresholds import (
    THRESHOLD_METRICS,
    MetricThreshold,
    ThresholdEvaluation,
    ThresholdResult,
    enforce_thresholds,
)

__all__ = [
    "COMPLETENESS_STATES",
    "CoverageError",
    "CoverageFormatError",
    "CoverageParseError",
    "ExcludedRun",
    "KNOWN_FORMAT_VERSIONS",
    "KNOWN_RUN_OUTCOMES",
    "MergeResult",
    "MetricThreshold",
    "MetricTotals",
    "QUARANTINE_OUTCOMES",
    "RoleCoverage",
    "RunAdmission",
    "RunCoverage",
    "COVERAGE_ROLES",
    "SeparatedCoverage",
    "SCHEMA_VERSION_CURRENT",
    "GcovBranch",
    "GcovCall",
    "GcovCondition",
    "GcovDocument",
    "GcovFile",
    "GcovFunction",
    "GcovLine",
    "THRESHOLD_METRICS",
    "ThresholdEvaluation",
    "ThresholdResult",
    "branch_coverage",
    "call_coverage",
    "coverage_for_test",
    "document_metrics",
    "enforce_thresholds",
    "function_coverage",
    "merge_run_coverage",
    "separate_coverage",
    "statement_coverage",
    "read_gcov_document",
]
