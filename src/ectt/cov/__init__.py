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

from ectt.cov.baremetal import (
    DumpFrame,
    dump_frame,
    parse_dump,
    retrieve_coverage,
    retrieve_run_coverage,
)
from ectt.cov.coupling import (
    COUPLING_SCHEMA_VERSION,
    COUPLING_STATUSES,
    DATA_PAIR_BASIS,
    CallPair,
    CallSite,
    CouplingReport,
    CouplingVariable,
    DataPair,
    analyze_coupling,
)
from ectt.cov.errors import (
    CoverageError,
    CoverageFormatError,
    CoverageParseError,
)
from ectt.cov.gcov import KNOWN_FORMAT_VERSIONS, read_gcov_document
from ectt.cov.justification import (
    LINE_STATUSES,
    AnnotatedCoverage,
    AnnotatedFile,
    AnnotatedLine,
    Justification,
    annotate_coverage,
    compute_source_digest,
    evaluate_justification,
)
from ectt.cov.mcdc import (
    MCDC_FORM,
    MCDC_MECHANISM,
    ConditionStatus,
    DecisionCoverage,
    McdcResult,
    UnmeasuredDecision,
    measure_mcdc,
)
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
    "MCDC_FORM",
    "MCDC_MECHANISM",
    "ConditionStatus",
    "DecisionCoverage",
    "McdcResult",
    "UnmeasuredDecision",
    "measure_mcdc",
    "COMPLETENESS_STATES",
    "CoverageError",
    "DumpFrame",
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
    "AnnotatedCoverage",
    "AnnotatedFile",
    "AnnotatedLine",
    "COVERAGE_ROLES",
    "Justification",
    "LINE_STATUSES",
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
    "annotate_coverage",
    "compute_source_digest",
    "evaluate_justification",
    "separate_coverage",
    "statement_coverage",
    "parse_dump",
    "read_gcov_document",
    "retrieve_coverage",
    "retrieve_run_coverage",
    "dump_frame",
    "COUPLING_SCHEMA_VERSION",
    "COUPLING_STATUSES",
    "DATA_PAIR_BASIS",
    "CallPair",
    "CallSite",
    "CouplingReport",
    "CouplingVariable",
    "DataPair",
    "analyze_coupling",
]
