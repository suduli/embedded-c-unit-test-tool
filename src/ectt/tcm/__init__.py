"""ECTT Test Case Management.

Provides the C-authored test case surface (registration of C sources against
a generated harness, named test case sets), the data-driven test case model
with its on-disk format and digest binding, and the named error hierarchy.
"""

from ectt.tcm.ctest import (
    CSourceTestCase,
    TestCaseSet,
    register_c_source,
)
from ectt.tcm.datacases import (
    TEST_CASES_KIND,
    DataDrivenTestCase,
    StubSpec,
    TestCaseExpected,
    TestCaseInputs,
    TestCaseOrigin,
    TestCasesFile,
    compute_case_digest,
    dump_test_cases_document,
    load_test_cases_file,
    parse_test_cases_document,
    refresh_digest,
    save_test_cases_file,
)
from ectt.tcm.errors import (
    DuplicateTestCaseError,
    InvalidSelectionError,
    InvalidTestCaseError,
    InvalidTestCasesFileError,
    MissingCaseFieldError,
    NotAgainstHarnessError,
    TcmError,
    TestCaseReadError,
    UnknownTestCaseError,
)
from ectt.tcm.independence import (
    IndependenceReport,
    check_order_independence,
    execution_order,
)
from ectt.tcm.selection import (
    Selection,
    partition_cases,
)

__all__ = [
    # Errors
    "TcmError",
    "InvalidTestCaseError",
    "TestCaseReadError",
    "NotAgainstHarnessError",
    "DuplicateTestCaseError",
    "UnknownTestCaseError",
    "InvalidTestCasesFileError",
    "MissingCaseFieldError",
    "InvalidSelectionError",
    # C-authored cases
    "CSourceTestCase",
    "TestCaseSet",
    "register_c_source",
    # Data-driven cases
    "TEST_CASES_KIND",
    "TestCaseInputs",
    "TestCaseExpected",
    "TestCaseOrigin",
    "StubSpec",
    "DataDrivenTestCase",
    "TestCasesFile",
    "compute_case_digest",
    "refresh_digest",
    "parse_test_cases_document",
    "load_test_cases_file",
    "dump_test_cases_document",
    "save_test_cases_file",
    # Selection and independence
    "Selection",
    "partition_cases",
    "execution_order",
    "IndependenceReport",
    "check_order_independence",
]
