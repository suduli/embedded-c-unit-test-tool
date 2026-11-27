# implements: TOOL-REP-090, TOOL-REP-100
"""ECTT report package: one intermediate model, many formats (WP-REP-01).

Every report format renders from the single documented intermediate model
(``ectt.rep.model``), so custom formats are added without re-running tests
(TOOL-REP-090), and identical inputs render byte-identical output
(TOOL-REP-100).
"""

from ectt.rep.certification import (
    CERTIFICATION_CLAIMS,
    CERTIFICATION_REPORT_SCHEMA_VERSION,
    KNOWN_COVERAGE_METRICS,
    UNMEASURED_METRICS,
    CertificationInputs,
    CertificationReport,
    build_certification_report,
)
from ectt.rep.coverage_interchange import (
    export_cobertura,
    export_lcov,
    import_cobertura,
    import_lcov,
)
from ectt.rep.errors import ReportModelError
from ectt.rep.formats import (
    REPORT_FORMAT_CONTRACT,
    REPORT_FORMATS_POINT_ID,
    ReportFormatRegistry,
    default_format_registry,
)
from ectt.rep.from_archive import report_from_archive, result_set_from_dict
from ectt.rep.html import render_html
from ectt.rep.machine_formats import cobertura_rate, render_cobertura, render_junit
from ectt.rep.model import (
    FORMAT_CHANGELOG,
    REPORT_MODEL_SCHEMA_VERSION,
    SUPPORTED_FORMAT_VERSIONS,
    TEST_STATUSES,
    CoverageEntry,
    ExecutionFacts,
    ReportModel,
    TestEntry,
    build_report_model,
    coverage_entry,
    dump_report_model,
    load_report_model,
    report_model_to_dict,
    test_entry,
)
from ectt.rep.pdf import render_pdf
from ectt.rep.render import render_json, render_text
from ectt.rep.summary import (
    CoverageTrend,
    CrossRunSummary,
    RunSummary,
    TrendPoint,
    build_coverage_trend,
    build_cross_run_summary,
    coverage_trend_to_dict,
    cross_run_summary_to_dict,
    dump_coverage_trend,
    dump_cross_run_summary,
)

__all__ = ["cobertura_rate",
    "export_cobertura",
    "export_lcov",
    "import_cobertura",
    "import_lcov",
    "render_cobertura",
    "render_html",
    "render_pdf",
    "render_junit",
        "FORMAT_CHANGELOG",
    "REPORT_FORMAT_CONTRACT",
    "REPORT_FORMATS_POINT_ID",
    "REPORT_MODEL_SCHEMA_VERSION",
    "SUPPORTED_FORMAT_VERSIONS",
    "TEST_STATUSES",
    "CoverageEntry",
    "CoverageTrend",
    "CrossRunSummary",
    "ExecutionFacts",
    "ReportFormatRegistry",
    "ReportModel",
    "ReportModelError",
    "RunSummary",
    "TestEntry",
    "TrendPoint",
    "build_coverage_trend",
    "build_cross_run_summary",
    "build_report_model",
    "coverage_entry",
    "coverage_trend_to_dict",
    "cross_run_summary_to_dict",
    "default_format_registry",
    "dump_coverage_trend",
    "dump_cross_run_summary",
    "dump_report_model",
    "load_report_model",
    "render_json",
    "report_from_archive",
    "render_text",
    "report_model_to_dict",
    "result_set_from_dict",
    "test_entry",
    "CERTIFICATION_CLAIMS",
    "CERTIFICATION_REPORT_SCHEMA_VERSION",
    "KNOWN_COVERAGE_METRICS",
    "UNMEASURED_METRICS",
    "CertificationInputs",
    "CertificationReport",
    "build_certification_report",
]
