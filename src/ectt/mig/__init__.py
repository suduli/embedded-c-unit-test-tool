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

__all__ = [
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
