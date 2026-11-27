# implements: TOOL-MIG-080
"""Coverage interchange: LCOV tracefile and Cobertura XML import/export (WP-REP-10).

Satisfies: TOOL-MIG-080 — import and export coverage data in standard
interchange formats, permitting aggregation with coverage produced by other
tools.

Export renders an ``ectt.cov`` document as an LCOV tracefile or Cobertura
XML; import parses either format back into an ordinary ``GcovDocument`` that
aggregates through ``ectt.cov.merge`` with documents of the same recorded
provenance. Cobertura's aggregate ``condition-coverage`` does not carry
per-branch taken counts, so a Cobertura import records statement counts only
and never invents branch data. Everything is deterministic: sorted output, no
wall-clock (``timestamp="0"``), no network.

Text a format cannot carry is refused with a named reason before anything is
written (``ectt.rep.output_text``): a line break or NUL in an LCOV name, a
character XML 1.0 does not allow, and text that cannot be written as UTF-8.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from typing import Any

from ectt.core.determinism import canonical_text
from ectt.cov.model import (
    GcovBranch,
    GcovDocument,
    GcovFile,
    GcovFunction,
    GcovLine,
)
from ectt.rep.errors import ReportModelError
from ectt.rep.output_text import describe, refuse_characters, xml_attribute

__all__ = [
    "export_cobertura",
    "export_lcov",
    "import_cobertura",
    "import_lcov",
]

_LCOV_TAKEN_NONE = "-"

#: An LCOV record ends at its line break and the format has no escaping, so a
#: name carrying a line break would split into records that read back as
#: something else; a NUL makes the tracefile binary to the tools that read it.
_LCOV_FORBIDDEN = re.compile(r"[\r\n\x00]")


def _error(message: str, reason: str) -> ReportModelError:
    return ReportModelError(message, reason=reason)


def _lcov_name(value: str, what: str) -> str:
    """``value`` as text on one LCOV record line, or a named refusal."""
    refuse_characters(
        value,
        what,
        forbidden=_LCOV_FORBIDDEN,
        reason="lcov_illegal_character",
        problem="a line break or NUL",
        carrier="an LCOV record",
    )
    return value


# --- export: LCOV ---------------------------------------------------------------


def export_lcov(document: GcovDocument) -> str:
    """Render the document as an LCOV tracefile (TOOL-MIG-080).

    ``TN`` names the data file; per file ``SF``, function records
    (``FN``/``FNDA``/``FNF``/``FNH``), branch records (``BRDA``/``BRF``/``BRH``)
    and line records (``DA``/``LF``/``LH``), then ``end_of_record``. A branch on
    a never-executed line reports ``taken`` as ``-`` (the LCOV convention).

    A data file, source file or function name carrying a line break or NUL is
    refused with ``lcov_illegal_character``, and one that cannot be written as
    UTF-8 with ``unencodable_text``: the format has no escaping, so such a
    tracefile would not read back as what was written.
    """
    data_file = _lcov_name(document.data_file, f"data file {describe(document.data_file)}")
    files = sorted(document.files, key=lambda f: f.file)
    for file in files:
        file_what = f"source file {describe(file.file)}"
        _lcov_name(file.file, file_what)
        for function in file.functions:
            _lcov_name(function.name, f"function {describe(function.name)} of {file_what}")

    out: list[str] = [f"TN:{data_file}"]
    for file in files:
        out.append(f"SF:{file.file}")
        functions = sorted(file.functions, key=lambda fn: (fn.start_line, fn.name))
        out.extend(f"FN:{fn.start_line},{fn.end_line},{fn.name}" for fn in functions)
        out.extend(f"FNDA:{fn.execution_count},{fn.name}" for fn in functions)
        out.append(f"FNF:{len(functions)}")
        out.append(f"FNH:{sum(1 for fn in functions if fn.execution_count > 0)}")
        branch_total = 0
        branch_hit = 0
        for line in sorted(file.lines, key=lambda ln: ln.line_number):
            for index, branch in enumerate(line.branches):
                if line.count > 0:
                    taken: str = str(branch.count)
                    taken_count = branch.count
                else:
                    taken = _LCOV_TAKEN_NONE
                    taken_count = 0
                out.append(f"BRDA:{line.line_number},{line.line_number},{index},{taken}")
                branch_total += 1
                if taken_count > 0:
                    branch_hit += 1
        out.append(f"BRF:{branch_total}")
        out.append(f"BRH:{branch_hit}")
        out.extend(
            f"DA:{line.line_number},{line.count}" for line in sorted(file.lines, key=lambda ln: ln.line_number)
        )
        out.append(f"LF:{len(file.lines)}")
        out.append(f"LH:{sum(1 for line in file.lines if line.count > 0)}")
        out.append("end_of_record")
    return canonical_text("\n".join(out) + "\n")


# --- export: Cobertura ------------------------------------------------------------


def export_cobertura(document: GcovDocument) -> str:
    """Render the document as Cobertura XML with per-line elements (TOOL-MIG-080).

    Branch-bearing lines carry ``branch="true"``; lines with condition records
    carry a ``condition-coverage`` attribute from the model's outcomes.
    ``timestamp`` is the fixed ``"0"`` (no wall-clock).
    """
    lines_valid = sum(len(f.lines) for f in document.files)
    lines_covered = sum(1 for f in document.files for line in f.lines if line.count > 0)
    out: list[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        (
            '<coverage line-rate="0" branch-rate="0"'
            f' lines-covered="{lines_covered}" lines-valid="{lines_valid}"'
            ' complexity="0" version="1.9" timestamp="0">'
        ),
        "  <sources />",
        "  <packages>",
        '    <package name="interchange" line-rate="0" branch-rate="0">',
        "      <classes>",
    ]
    for file in sorted(document.files, key=lambda f: f.file):
        # The name is written as an attribute: markup is escaped, and text XML
        # cannot carry is refused rather than written as a broken document.
        file_attr = xml_attribute(file.file, f"source file {describe(file.file)}")
        out.append(
            f"        <class name={file_attr} filename={file_attr}"
            ' line-rate="0" branch-rate="0" complexity="0">'
        )
        out.append("          <methods />")
        out.append("          <lines>")
        for line in sorted(file.lines, key=lambda ln: ln.line_number):
            if line.branches or line.conditions:
                covered_outcomes = sum(c.covered for c in line.conditions)
                total_outcomes = sum(c.count for c in line.conditions)
                condition = (
                    f' condition-coverage="{_condition_text(covered_outcomes, total_outcomes)}"'
                    if total_outcomes
                    else ""
                )
                out.append(
                    f'            <line number="{line.line_number}" hits="{line.count}"'
                    f' branch="true"{condition} />'
                )
            else:
                out.append(
                    f'            <line number="{line.line_number}" hits="{line.count}" branch="false" />'
                )
        out.append("          </lines>")
        out.append("        </class>")
    out.append("      </classes>")
    out.append("    </package>")
    out.append("  </packages>")
    out.append("</coverage>")
    return canonical_text("\n".join(out))


def _condition_text(covered: int, total: int) -> str:
    if total == 0:
        return "0% (0/0)"
    percent = covered * 100 // total if covered * 100 % total == 0 else round(covered * 100 / total)
    return f"{percent}% ({covered}/{total})"


# --- import: LCOV -----------------------------------------------------------------


def import_lcov(text: str, *, gcc_version: str = "unknown") -> GcovDocument:
    """Parse an LCOV tracefile into a coverage document (TOOL-MIG-080).

    ``DA`` counts become line counts, ``BRDA`` taken counts become branch
    counts (``-`` means a branch of a never-executed line: count 0), and
    ``FN``/``FNDA`` become function records. The ``LF``/``LH``/``BRF``/``BRH``/
    ``FNF``/``FNH`` summary records are cross-checked against the parsed
    detail records; a mismatch is a named error.
    """
    files: dict[str, dict[str, Any]] = {}
    current: dict[str, Any] | None = None

    def _int(token: str, where: str) -> int:
        try:
            value = int(token)
        except ValueError as exc:
            raise _error(f"malformed integer '{token}' in {where}", "malformed_count") from exc
        if value < 0:
            raise _error(f"negative count '{token}' in {where}", "negative_count")
        return value

    for raw_line in text.replace("\r\n", "\n").split("\n"):
        record = raw_line.strip()
        if not record:
            continue
        if record == "end_of_record":
            if current is None:
                raise _error("end_of_record without an open SF record", "unterminated_record")
            _check_summaries(current, current["file"])
            files[current["file"]] = current
            current = None
            continue
        if ":" not in record:
            raise _error(f"unknown LCOV record '{record}'", "unknown_record")
        tag, value = record.split(":", 1)
        if tag == "SF":
            if current is not None:
                raise _error(f"SF record '{value}' opened before 'end_of_record'", "unterminated_record")
            if value in files:
                raise _error(f"duplicate SF record for '{value}'", "duplicate_file")
            current = {
                "file": value,
                "functions": {},
                "function_meta": {},
                "lines": {},
                "branches": {},
                "summaries": {},
            }
            continue
        if tag == "TN":
            continue  # test name carries no counts
        if current is None:
            raise _error(f"LCOV record '{record}' outside an SF block", "orphan_record")
        where = f"{current['file']}:{tag}"
        if tag == "FN":
            parts = value.split(",")
            if len(parts) != 3:
                raise _error(f"malformed FN record '{value}' in {where}", "malformed_record")
            start_line, end_line, name = parts
            current["function_meta"][name] = (_int(start_line, where), _int(end_line, where))
        elif tag == "FNDA":
            parts = value.split(",")
            if len(parts) != 2:
                raise _error(f"malformed FNDA record '{value}' in {where}", "malformed_record")
            count, name = parts
            if name in current["functions"]:
                raise _error(f"duplicate FNDA record for '{name}' in {where}", "duplicate_function")
            if name not in current["function_meta"]:
                raise _error(f"FNDA for unknown function '{name}' in {where}", "orphan_record")
            current["functions"][name] = _int(count, where)
        elif tag in ("FNF", "FNH", "LF", "LH", "BRF", "BRH"):
            current["summaries"][tag] = _int(value, where)
        elif tag == "DA":
            parts = value.split(",")
            if len(parts) not in (2, 3):
                raise _error(f"malformed DA record '{value}' in {where}", "malformed_record")
            if parts[0] in current["lines"]:
                raise _error(f"duplicate DA record for line {parts[0]} in {where}", "duplicate_line")
            current["lines"][parts[0]] = _int(parts[1], where)
        elif tag == "BRDA":
            parts = value.split(",")
            if len(parts) != 4:
                raise _error(f"malformed BRDA record '{value}' in {where}", "malformed_record")
            line_number, _block, branch_index, taken = parts
            taken_count = 0 if taken == _LCOV_TAKEN_NONE else _int(taken, where)
            key = (line_number, branch_index)
            if key in current["branches"]:
                raise _error(f"duplicate BRDA record for {key} in {where}", "duplicate_branch")
            current["branches"][key] = taken_count
        else:
            raise _error(f"unknown LCOV record tag '{tag}'", "unknown_record")

    if current is not None:
        raise _error(f"SF record '{current['file']}' without end_of_record", "unterminated_record")
    if not files:
        raise _error("LCOV tracefile contains no SF records", "empty_tracefile")

    parsed: list[GcovFile] = []
    for path in sorted(files):
        data = files[path]
        functions = tuple(
            GcovFunction(
                name=name,
                start_line=data["function_meta"][name][0],
                end_line=data["function_meta"][name][1],
                execution_count=data["functions"][name],
            )
            for name in sorted(data["functions"])
        )
        branch_index_by_line: dict[str, list[str]] = {}
        for (line_number, branch_index) in data["branches"]:
            branch_index_by_line.setdefault(line_number, []).append(branch_index)
        gcov_lines: list[GcovLine] = []
        for number_str in sorted(data["lines"], key=int):
            branches = tuple(
                GcovBranch(count=data["branches"][(number_str, index_str)])
                for index_str in sorted(branch_index_by_line.get(number_str, []), key=int)
            )
            gcov_lines.append(
                GcovLine(line_number=int(number_str), count=data["lines"][number_str], branches=branches)
            )
        parsed.append(GcovFile(file=path, functions=functions, lines=tuple(gcov_lines)))
    return GcovDocument(
        format_version="2",
        gcc_version=gcc_version,
        data_file="interchange",
        files=tuple(parsed),
    )


def _check_summaries(data: Mapping[str, Any], where: str) -> None:
    summaries = data["summaries"]
    checks = {
        "LF": len(data["lines"]),
        "LH": sum(1 for count in data["lines"].values() if count > 0),
        "BRF": len(data["branches"]),
        "BRH": sum(1 for count in data["branches"].values() if count > 0),
        "FNF": len(data["functions"]),
        "FNH": sum(1 for count in data["functions"].values() if count > 0),
    }
    for tag, expected in checks.items():
        if tag in summaries and summaries[tag] != expected:
            raise _error(
                f"summary {tag}={summaries[tag]} disagrees with {expected} parsed records in {where}",
                "summary_mismatch",
            )


# --- import: Cobertura (statement-level) -------------------------------------------


def import_cobertura(text: str, *, gcc_version: str = "unknown") -> GcovDocument:
    """Parse Cobertura XML into a coverage document, statement level only (TOOL-MIG-080).

    Cobertura's aggregate ``condition-coverage`` carries no per-branch taken
    counts, so branch records are not invented: only per-line ``hits`` are
    imported. A line element with a non-integer or negative ``hits`` value is a
    named error.
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise _error(f"Cobertura XML is not well-formed: {exc}", "invalid_xml") from exc

    files: dict[str, list[GcovLine]] = {}
    for class_element in root.iter("class"):
        filename = class_element.get("filename")
        if not filename:
            raise _error("Cobertura class element without filename", "invalid_xml")
        for line_element in class_element.iter("line"):
            number_raw = line_element.get("number")
            hits_raw = line_element.get("hits")
            if number_raw is None or hits_raw is None:
                raise _error(f"line element missing number/hits in {filename}", "invalid_xml")
            try:
                number = int(number_raw)
                hits = int(hits_raw)
            except ValueError as exc:
                raise _error(
                    f"malformed line number/hits '{number_raw}/{hits_raw}' in {filename}",
                    "malformed_count",
                ) from exc
            if number < 1 or hits < 0:
                raise _error(
                    f"invalid line number/hits '{number_raw}/{hits_raw}' in {filename}",
                    "malformed_count",
                )
            files.setdefault(filename, []).append(GcovLine(line_number=number, count=hits))

    parsed = tuple(
        GcovFile(file=path, lines=tuple(sorted(entries, key=lambda ln: ln.line_number)))
        for path, entries in sorted(files.items())
    )
    if not parsed:
        raise _error("Cobertura XML contains no line records", "empty_tracefile")
    return GcovDocument(
        format_version="2",
        gcc_version=gcc_version,
        data_file="interchange",
        files=parsed,
    )
