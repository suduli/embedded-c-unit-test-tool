"""ECTT Test Case Management.

Provides the C-authored test case surface: registration of C sources against
a generated harness, named test case sets, and the named error hierarchy.
"""

from ectt.tcm.ctest import (
    CSourceTestCase,
    TestCaseSet,
    register_c_source,
)
from ectt.tcm.errors import (
    DuplicateTestCaseError,
    InvalidTestCaseError,
    NotAgainstHarnessError,
    TcmError,
    TestCaseReadError,
    UnknownTestCaseError,
)

__all__ = [
    # Errors
    "TcmError",
    "InvalidTestCaseError",
    "TestCaseReadError",
    "NotAgainstHarnessError",
    "DuplicateTestCaseError",
    "UnknownTestCaseError",
    # C-authored cases
    "CSourceTestCase",
    "TestCaseSet",
    "register_c_source",
]
