"""Migration and coexistence facilities for ectt (CMP-MIG).

The decision-free coexistence contract lives here first (WP-MIG-06,
TOOL-MIG-070). Import adapters for third-party tools are separate work
packages (WP-MIG-01..05, WP-MIG-07).
"""

from __future__ import annotations

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
    DELIMITERS,
    MappedCsvImport,
    RowOutcome,
    import_mapped_csv,
    validate_mapping,
)

__all__ = [
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
