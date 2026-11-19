# implements: TOOL-REP-090, TOOL-REP-100
"""ECTT report package: one intermediate model, many formats (WP-REP-01).

Every report format renders from the single documented intermediate model
(``ectt.rep.model``), so custom formats are added without re-running tests
(TOOL-REP-090), and identical inputs render byte-identical output
(TOOL-REP-100).
"""

from ectt.rep.errors import ReportModelError
from ectt.rep.formats import (
    REPORT_FORMAT_CONTRACT,
    REPORT_FORMATS_POINT_ID,
    ReportFormatRegistry,
    default_format_registry,
)
from ectt.rep.model import (
    REPORT_MODEL_SCHEMA_VERSION,
    TEST_STATUSES,
    CoverageEntry,
    ReportModel,
    TestEntry,
    build_report_model,
    coverage_entry,
    dump_report_model,
    load_report_model,
    report_model_to_dict,
    test_entry,
)
from ectt.rep.render import render_json, render_text

__all__ = [
    "REPORT_FORMAT_CONTRACT",
    "REPORT_FORMATS_POINT_ID",
    "REPORT_MODEL_SCHEMA_VERSION",
    "TEST_STATUSES",
    "CoverageEntry",
    "ReportFormatRegistry",
    "ReportModel",
    "ReportModelError",
    "TestEntry",
    "build_report_model",
    "coverage_entry",
    "default_format_registry",
    "dump_report_model",
    "load_report_model",
    "render_json",
    "render_text",
    "report_model_to_dict",
    "test_entry",
]
