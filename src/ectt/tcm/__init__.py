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
from ectt.tcm.derivation import (
    DEFAULT_MAX_VECTORS,
    STRATEGIES,
    ClassificationNode,
    DerivedValue,
    DerivedVector,
    EquivalenceClass,
    IntegerDomain,
    TreeClass,
    boundary_values,
    classification_vectors,
    derive_vectors,
    domains_from_parameters,
    equivalence_classes,
    vectors_to_cases,
)
from ectt.tcm.errors import (
    DerivationError,
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
from ectt.tcm.interchange import (
    COLUMNS,
    INTERCHANGE_VERSION,
    InterchangeExport,
    InterchangeImport,
    export_cases,
    import_cases,
)
from ectt.tcm.nested import (
    ExpectedPath,
    compare_expected,
    ctype_from_model,
    expected_trees,
    flatten_expected,
    is_nested_key,
    parse_expected_path,
    validate_expected_keys,
)
from ectt.tcm.ranged import (
    RangedInput,
    ValidRange,
    ensure_range_checking,
    expand_case,
    expand_integer_range,
    mark_robustness,
)
from ectt.tcm.selection import (
    Selection,
    partition_cases,
)

__all__ = [
    "ExpectedPath",
    "compare_expected",
    "ctype_from_model",
    "expected_trees",
    "flatten_expected",
    "is_nested_key",
    "parse_expected_path",
    "validate_expected_keys",
    "DerivationError",
    "DEFAULT_MAX_VECTORS",
    "STRATEGIES",
    "ClassificationNode",
    "DerivedValue",
    "DerivedVector",
    "EquivalenceClass",
    "IntegerDomain",
    "TreeClass",
    "boundary_values",
    "classification_vectors",
    "derive_vectors",
    "domains_from_parameters",
    "equivalence_classes",
    "vectors_to_cases",
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
    "RangeExpansionError",
    "RangeCheckingError",
    "InterchangeError",
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
    # Ranged and robustness inputs
    "RangedInput",
    "ValidRange",
    "expand_integer_range",
    "expand_case",
    "mark_robustness",
    "ensure_range_checking",
    # Interchange
    "INTERCHANGE_VERSION",
    "COLUMNS",
    "InterchangeExport",
    "InterchangeImport",
    "export_cases",
    "import_cases",
]
