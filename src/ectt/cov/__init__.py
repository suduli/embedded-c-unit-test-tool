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
from ectt.cov.metrics import branch_coverage, document_metrics, statement_coverage
from ectt.cov.model import (
    SCHEMA_VERSION_CURRENT,
    GcovBranch,
    GcovCondition,
    GcovDocument,
    GcovFile,
    GcovLine,
    MetricTotals,
)

__all__ = [
    "CoverageError",
    "CoverageFormatError",
    "CoverageParseError",
    "KNOWN_FORMAT_VERSIONS",
    "SCHEMA_VERSION_CURRENT",
    "GcovBranch",
    "GcovCondition",
    "GcovDocument",
    "GcovFile",
    "GcovLine",
    "MetricTotals",
    "branch_coverage",
    "document_metrics",
    "statement_coverage",
    "read_gcov_document",
]
