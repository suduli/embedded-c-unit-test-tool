"""Migration and coexistence facilities for ectt (CMP-MIG).

The decision-free coexistence contract lives here first (WP-MIG-06,
TOOL-MIG-070). Import adapters for third-party tools are separate work
packages (WP-MIG-01..05, WP-MIG-07).
"""

from __future__ import annotations

from ectt.mig.assessment import (
    OUTCOMES,
    Assessment,
    ManualItem,
    assess_ceedling_project,
    assess_mapped_csv,
    dump_assessment,
)
from ectt.mig.ceedling import (
    CEEDLING_PROJECT_FILE,
    CeedlingTest,
    CeedlingTestFile,
    ImportedCeedlingProject,
    ImportNote,
    import_ceedling_project,
)
from ectt.mig.coexistence import (
    OWNED_PROJECT_PATHS,
    ForeignArtifact,
    TreeSnapshot,
    assert_no_interference,
    scan_foreign_artifacts,
    snapshot_tree,
)
from ectt.mig.csv_import import (
    DEFERRED_KINDS,
    DELIMITERS,
    MappedCsvImport,
    RowOutcome,
    import_mapped_csv,
    validate_mapping,
)
from ectt.mig.fidelity import (
    ArtifactFidelity,
    DeferredStructure,
    FidelityNote,
    FidelityReport,
    build_ceedling_fidelity_report,
    build_csv_fidelity_report,
    check_fidelity_report,
    dump_fidelity_report,
    load_fidelity_report,
)
from ectt.mig.formats import (
    INTERCHANGE_FORMATS,
    FormatSpec,
    check_format_documentation,
    format_by_id,
    render_format_reference,
)

__all__ = [
    "OUTCOMES",
    "Assessment",
    "ManualItem",
    "assess_ceedling_project",
    "assess_mapped_csv",
    "dump_assessment",
    "INTERCHANGE_FORMATS",
    "FormatSpec",
    "check_format_documentation",
    "format_by_id",
    "render_format_reference",
    "DEFERRED_KINDS",
    "ArtifactFidelity",
    "DeferredStructure",
    "FidelityNote",
    "FidelityReport",
    "build_ceedling_fidelity_report",
    "build_csv_fidelity_report",
    "check_fidelity_report",
    "dump_fidelity_report",
    "load_fidelity_report",
    "DELIMITERS",
    "MappedCsvImport",
    "RowOutcome",
    "import_mapped_csv",
    "validate_mapping",
    "CEEDLING_PROJECT_FILE",
    "CeedlingTest",
    "CeedlingTestFile",
    "ImportNote",
    "ImportedCeedlingProject",
    "import_ceedling_project",
    "OWNED_PROJECT_PATHS",
    "ForeignArtifact",
    "TreeSnapshot",
    "assert_no_interference",
    "scan_foreign_artifacts",
    "snapshot_tree",
]
