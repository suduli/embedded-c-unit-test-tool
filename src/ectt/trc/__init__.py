# implements: TOOL-TRC-010, TOOL-TRC-020, TOOL-TRC-030, TOOL-TRC-110
"""ECTT traceability package (WP-TRC-01).

Requirement associations deduplicated to unique (requirement, test) pairs
(TOOL-TRC-010, TOOL-TRC-110), the bidirectional matrix (TOOL-TRC-020) with
per-test statuses (TOOL-TRC-030) and worst-outcome requirement verdicts with
labelled denominators (TOOL-TRC-110).
"""

from ectt.trc.associations import Association, AssociationSet
from ectt.trc.errors import TrcError
from ectt.trc.matrix import (
    TEST_SEVERITY,
    RequirementRow,
    TestLink,
    TraceabilityMatrix,
    associations_from_datacases,
    build_matrix,
)
from ectt.trc.unlinked import UnlinkedReport, find_unlinked

__all__ = [
    "Association",
    "AssociationSet",
    "RequirementRow",
    "TEST_SEVERITY",
    "TestLink",
    "TraceabilityMatrix",
    "TrcError",
    "UnlinkedReport",
    "associations_from_datacases",
    "build_matrix",
    "find_unlinked",
]
