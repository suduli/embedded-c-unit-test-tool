# implements: TOOL-TRC-010, TOOL-TRC-020, TOOL-TRC-030, TOOL-TRC-110
"""ECTT traceability package (WP-TRC-01).

Requirement associations deduplicated to unique (requirement, test) pairs
(TOOL-TRC-010, TOOL-TRC-110), the bidirectional matrix (TOOL-TRC-020) with
per-test statuses (TOOL-TRC-030) and worst-outcome requirement verdicts with
labelled denominators (TOOL-TRC-110).
"""

from ectt.trc.associations import Association, AssociationSet
from ectt.trc.change_detection import (
    ChangeReport,
    ReviewBaseline,
    ReviewReason,
    TestReview,
    detect_changes,
    dump_baseline,
    load_baseline,
    mark_reviewed,
    record_baseline,
    requirement_digest,
)
from ectt.trc.errors import TrcError
from ectt.trc.imports import (
    CSV_COLUMNS,
    ReqIfImport,
    RequirementRecord,
    import_reqif,
    import_reqif_with_associations,
    import_requirements_csv,
    import_requirements_text,
    requirement_universe,
)
from ectt.trc.matrix import (
    TEST_SEVERITY,
    RequirementRow,
    TestLink,
    TraceabilityMatrix,
    associations_from_datacases,
    build_matrix,
)
from ectt.trc.reqif_export import REQIF_NAMESPACE, TEST_TYPE_ID, export_reqif
from ectt.trc.source_links import (
    ResolvedSourceLink,
    SourceLink,
    SourceLinkResolution,
    dump_source_links,
    load_source_links,
    resolve_source_links,
)
from ectt.trc.unlinked import UnlinkedReport, find_unlinked

__all__ = [
    "ChangeReport",
    "ReviewBaseline",
    "ReviewReason",
    "TestReview",
    "detect_changes",
    "dump_baseline",
    "load_baseline",
    "mark_reviewed",
    "record_baseline",
    "requirement_digest",
    "ResolvedSourceLink",
    "SourceLink",
    "SourceLinkResolution",
    "dump_source_links",
    "load_source_links",
    "resolve_source_links",
    "REQIF_NAMESPACE",
    "TEST_TYPE_ID",
    "export_reqif",
    "Association",
    "AssociationSet",
    "CSV_COLUMNS",
    "RequirementRecord",
    "RequirementRow",
    "TEST_SEVERITY",
    "TestLink",
    "TraceabilityMatrix",
    "TrcError",
    "UnlinkedReport",
    "associations_from_datacases",
    "build_matrix",
    "find_unlinked",
    "import_reqif",
    "import_reqif_with_associations",
    "ReqIfImport",
    "import_requirements_csv",
    "import_requirements_text",
    "requirement_universe",
]
