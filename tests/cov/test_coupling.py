# implements: TOOL-COV-170
"""Control coupling and data coupling between integrated units (WP-COV-11).

Control coupling pairs a caller with its callee and says whether the call was
exercised; data coupling pairs a function that writes a global with one that
reads it and says whether both sides executed. Every pair is ``exercised``,
``not_exercised`` or ``not_determinable`` with the reason. The report carries
data only: no score and no verdict about a standard's objective.
"""

from __future__ import annotations

from typing import Any

import pytest

from ectt.ana.frontend import parse
from ectt.ana.interface import extract_interfaces
from ectt.ana.model import (
    CALL_CLASSIFICATIONS,
    CALL_VIA,
    AnalysisModel,
    AnalysisUnit,
    CallModel,
    FunctionModel,
    GlobalAccessModel,
    GlobalVariableModel,
    ProvenanceModel,
    SourceLocation,
)
from ectt.cov.coupling import (
    COUPLING_STATUSES,
    DATA_PAIR_BASIS,
    CouplingReport,
    analyze_coupling,
)
from ectt.cov.errors import CoverageError
from ectt.cov.gcov import read_gcov_document

_UNIT = "src/app.c"


# --- builders ------------------------------------------------------------------------------


def _call(callee: str, line: int, *, classification: str = "internal", via: str = "direct") -> CallModel:
    return CallModel(callee=callee, classification=classification, via=via, line=line)


def _function(
    name: str,
    unit: str = _UNIT,
    *,
    calls: tuple[CallModel, ...] = (),
    globals_: tuple[GlobalAccessModel, ...] = (),
) -> FunctionModel:
    return FunctionModel(
        name=name,
        linkage="external",
        storage_class="static",
        location=SourceLocation(file=unit, line=1),
        return_type="ref:type.int",
        calls=calls,
        globals=globals_,
    )


def _global(name: str, storage_class: str = "static") -> GlobalVariableModel:
    return GlobalVariableModel(name=name, type="ref:type.int", has_initializer=False, storage_class=storage_class)


def _model(*units: AnalysisUnit) -> AnalysisModel:
    return AnalysisModel(provenance=ProvenanceModel("test", "fe", "now"), units=units)


def _line(number: int, count: int, returned: list[int]) -> dict[str, Any]:
    entry: dict[str, Any] = {"line_number": number, "count": count, "unexecuted_block": False}
    if returned:
        entry["calls"] = [
            {"returned": value, "source_block_id": 1, "destination_block_id": 2} for value in returned
        ]
    return entry


def _file(
    name: str,
    *,
    executed: dict[str, int] | None = None,
    lines: dict[int, tuple[int, list[int]]] | None = None,
) -> dict[str, Any]:
    return {
        "file": name,
        "functions": [
            {"name": function, "start_line": 1, "end_line": 9, "execution_count": count}
            for function, count in sorted((executed or {}).items())
        ],
        "lines": [_line(number, count, returned) for number, (count, returned) in sorted((lines or {}).items())],
    }


def _document(*files: dict[str, Any]) -> Any:
    return read_gcov_document(
        {"format_version": "2", "gcc_version": "14.1.0", "data_file": "d.gcda", "files": list(files)}
    )


def _chain() -> AnalysisUnit:
    return AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(
            _function("top", calls=(_call("middle", 10),)),
            _function("middle", calls=(_call("leaf", 20),)),
            _function("skip", calls=(_call("leaf", 30),)),
        ),
    )


def _chain_coverage(last_returned: int = 0, last_count: int = 0) -> Any:
    return _document(
        _file(
            _UNIT,
            executed={"top": 3, "middle": 3, "skip": 3, "leaf": 3},
            lines={10: (3, [3]), 20: (3, [3]), 30: (last_count, [last_returned])},
        )
    )


def _calls(report: CouplingReport) -> dict[tuple[str, str | None], tuple[str, str | None]]:
    return {(pair.caller, pair.callee): (pair.status, pair.reason) for pair in report.call_pairs}


def _variable(report: CouplingReport, name: str, unit: str | None = None) -> Any:
    return next(v for v in report.variables if v.variable == name and v.unit == unit)


# --- the three cases the item names ---------------------------------------------------------


def test_a_simple_call_chain_is_reported_as_exercised() -> None:
    """verifies: TOOL-COV-170 — control coupling: the calls of a chain, each exercised."""
    report = analyze_coupling(_model(_chain()), _chain_coverage(last_returned=1, last_count=1))
    assert _calls(report) == {
        ("top", "middle"): ("exercised", None),
        ("middle", "leaf"): ("exercised", None),
        ("skip", "leaf"): ("exercised", None),
    }
    by_caller = {pair.caller: pair for pair in report.call_pairs}
    assert by_caller["top"].sites[0].line == 10
    assert by_caller["top"].callee_unit == _UNIT
    assert by_caller["top"].classification == "internal"


def test_an_unexercised_call_is_reported_as_not_exercised() -> None:
    report = analyze_coupling(_model(_chain()), _chain_coverage())
    assert _calls(report)[("skip", "leaf")] == ("not_exercised", "call_site_not_reached")
    # the rest of the chain is unaffected
    assert _calls(report)[("top", "middle")] == ("exercised", None)


def test_a_call_that_never_returns_is_named_apart_from_one_never_reached() -> None:
    """A call made but not returned (count > 0, returned 0) is not read as exercised."""
    report = analyze_coupling(_model(_chain()), _chain_coverage(last_returned=0, last_count=4))
    assert _calls(report)[("skip", "leaf")] == ("not_exercised", "call_never_returned")


def test_a_global_with_no_recorded_access_is_not_determinable() -> None:
    """verifies: TOOL-COV-170 — data coupling: a global nobody is recorded on."""
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("top"),), global_variables=(_global("idle"),))
    report = analyze_coupling(_model(unit), _document(_file(_UNIT, executed={"top": 1})))
    (variable,) = report.variables
    assert variable.variable == "idle"
    assert variable.status == "not_determinable"
    assert variable.reason == "no_recorded_access"
    assert variable.pairs == () and variable.writers == () and variable.readers == ()


def test_a_written_and_read_global_forms_an_exercised_pair() -> None:
    unit = AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(
            _function("set_mode", globals_=(GlobalAccessModel("mode", "w"),)),
            _function("get_mode", globals_=(GlobalAccessModel("mode", "r"),)),
        ),
        global_variables=(_global("mode"),),
    )
    report = analyze_coupling(_model(unit), _document(_file(_UNIT, executed={"set_mode": 2, "get_mode": 5})))
    variable = _variable(report, "mode", _UNIT)
    assert variable.status == "recorded"
    assert variable.writers == (("set_mode", _UNIT),) and variable.readers == (("get_mode", _UNIT),)
    (pair,) = variable.pairs
    assert (pair.writer, pair.reader, pair.status, pair.reason) == ("set_mode", "get_mode", "exercised", None)


# --- not determinable, with the reason --------------------------------------------------------


def test_a_call_through_a_pointer_has_no_guessed_target() -> None:
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("dispatch", calls=(_call("", 40, classification="unresolved", via="function_pointer"),)),))
    # the call site did return: the call ran, but which function it coupled to is not known
    report = analyze_coupling(_model(unit), _document(_file(_UNIT, executed={"dispatch": 1}, lines={40: (1, [1])})))
    (pair,) = report.call_pairs
    assert pair.callee is None and pair.callee_unit is None
    assert (pair.status, pair.reason) == ("not_determinable", "callee_not_identified")


@pytest.mark.parametrize(
    ("coverage", "reason"),
    [
        (pytest.param(_document(), "file_not_in_coverage", id="file-not-in-coverage")),
        (pytest.param(_document(_file(_UNIT)), "call_line_not_in_coverage", id="line-not-in-coverage")),
        # a document produced without -b carries no call records at all
        (pytest.param(_document(_file(_UNIT, lines={10: (3, [])})), "no_call_data", id="no-call-data")),
    ],
)
def test_a_call_site_without_call_data_is_not_determinable(coverage: Any, reason: str) -> None:
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("top", calls=(_call("middle", 10),)),))
    report = analyze_coupling(_model(unit), coverage)
    assert _calls(report)[("top", "middle")] == ("not_determinable", reason)


def test_several_calls_on_one_line_are_not_matched_by_position() -> None:
    """Neither the model site nor the gcov call record names its callee, so two
    calls on one line are not matched by order."""
    unit = AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(_function("top", calls=(_call("first", 10), _call("second", 10))),),
    )
    both_returned = _document(_file(_UNIT, lines={10: (2, [1, 1])}))
    report = analyze_coupling(_model(unit), both_returned)
    assert _calls(report) == {
        ("top", "first"): ("not_determinable", "ambiguous_call_site"),
        ("top", "second"): ("not_determinable", "ambiguous_call_site"),
    }


def test_one_model_site_against_two_gcov_call_records_is_not_matched() -> None:
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("top", calls=(_call("middle", 10),)),))
    report = analyze_coupling(_model(unit), _document(_file(_UNIT, lines={10: (2, [1, 0])})))
    assert _calls(report)[("top", "middle")] == ("not_determinable", "ambiguous_call_site")


def test_a_call_to_a_function_defined_in_another_unit_names_that_unit() -> None:
    caller = AnalysisUnit(
        "src/app.c", "parsed", functions=(_function("top", "src/app.c", calls=(_call("helper", 10, classification="external"),)),)
    )
    callee = AnalysisUnit("src/util.c", "parsed", functions=(_function("helper", "src/util.c"),))
    coverage = _document(
        _file("src/app.c", executed={"top": 1}, lines={10: (1, [1])}),
        _file("src/util.c", executed={"helper": 1}),
    )
    report = analyze_coupling(_model(caller, callee), coverage)
    (pair,) = report.call_pairs
    assert (pair.caller_unit, pair.callee_unit, pair.status) == ("src/app.c", "src/util.c", "exercised")
    assert report.analysed_units == ("src/app.c", "src/util.c")


@pytest.mark.parametrize(
    ("executed", "status", "reason"),
    [
        (pytest.param({"set_mode": 2}, "not_determinable", "reader: function_not_in_coverage", id="reader-absent")),
        (pytest.param({"set_mode": 2, "get_mode": 0}, "not_exercised", "reader_not_executed", id="reader-idle")),
        (pytest.param({"set_mode": 0, "get_mode": 2}, "not_exercised", "writer_not_executed", id="writer-idle")),
        (
            pytest.param(
                {"set_mode": 0, "get_mode": 0},
                "not_exercised",
                "writer_not_executed_and_reader_not_executed",
                id="both-idle",
            )
        ),
    ],
)
def test_a_data_pair_that_did_not_execute_is_named(executed: dict[str, int], status: str, reason: str) -> None:
    unit = AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(
            _function("set_mode", globals_=(GlobalAccessModel("mode", "w"),)),
            _function("get_mode", globals_=(GlobalAccessModel("mode", "r"),)),
        ),
        global_variables=(_global("mode"),),
    )
    (pair,) = _variable(analyze_coupling(_model(unit), _document(_file(_UNIT, executed=executed))), "mode", _UNIT).pairs
    assert (pair.status, pair.reason) == (status, reason)


# --- identity of variables and of callees -----------------------------------------------------


def test_same_named_statics_in_two_units_are_not_coupled() -> None:
    """A file-scope static in one unit is a different variable from a same-named
    static in another; accesses are recorded by name only."""
    first = AnalysisUnit(
        "src/a.c",
        "parsed",
        functions=(_function("set_a", "src/a.c", globals_=(GlobalAccessModel("count", "w"),)),),
        global_variables=(_global("count"),),
    )
    second = AnalysisUnit(
        "src/b.c",
        "parsed",
        functions=(_function("get_b", "src/b.c", globals_=(GlobalAccessModel("count", "r"),)),),
        global_variables=(_global("count"),),
    )
    report = analyze_coupling(_model(first, second), _document())
    assert [(v.variable, v.unit, v.pairs) for v in report.variables] == [
        ("count", "src/a.c", ()),
        ("count", "src/b.c", ()),
    ]


def test_an_external_global_couples_functions_across_units() -> None:
    writer = AnalysisUnit(
        "src/a.c",
        "parsed",
        functions=(_function("publish", "src/a.c", globals_=(GlobalAccessModel("shared", "w"),)),),
        # a.c defines it; b.c only reads it, so b.c's inventory does not list it
        global_variables=(_global("shared", storage_class="none"),),
    )
    reader = AnalysisUnit(
        "src/b.c", "parsed", functions=(_function("consume", "src/b.c", globals_=(GlobalAccessModel("shared", "r"),)),)
    )
    coverage = _document(_file("src/a.c", executed={"publish": 1}), _file("src/b.c", executed={"consume": 1}))
    variable = _variable(analyze_coupling(_model(writer, reader), coverage), "shared", "src/a.c")
    assert variable.linkage == "external" and variable.defined_in_model is True
    (pair,) = variable.pairs
    assert (pair.writer_unit, pair.reader_unit, pair.status) == ("src/a.c", "src/b.c", "exercised")


def test_a_global_accessed_but_defined_in_no_analysed_unit_is_stated() -> None:
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("read", globals_=(GlobalAccessModel("elsewhere", "r"),)),))
    variable = _variable(analyze_coupling(_model(unit), _document()), "elsewhere", None)
    assert variable.unit is None and variable.defined_in_model is False
    assert variable.readers == (("read", _UNIT),) and variable.pairs == ()


def test_a_function_name_defined_in_two_units_is_not_picked() -> None:
    caller = AnalysisUnit(
        "src/app.c", "parsed", functions=(_function("top", "src/app.c", calls=(_call("helper", 10, classification="external"),)),)
    )
    helpers = tuple(
        AnalysisUnit(path, "parsed", functions=(_function("helper", path),)) for path in ("src/u1.c", "src/u2.c")
    )
    report = analyze_coupling(_model(caller, *helpers), _document(_file("src/app.c", lines={10: (1, [1])})))
    (pair,) = report.call_pairs
    assert pair.callee_unit is None  # not guessed between u1 and u2
    assert pair.status == "exercised"  # the call itself was exercised whoever answered it


# --- refused inputs -----------------------------------------------------------------------------


def test_an_unknown_call_via_is_refused() -> None:
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("top", calls=(_call("middle", 10, via="teleport"),)),))
    with pytest.raises(CoverageError) as exc_info:
        analyze_coupling(_model(unit), _document())
    assert exc_info.value.reason == "unknown_call_via"


def test_an_unknown_call_classification_is_refused() -> None:
    unit = AnalysisUnit(_UNIT, "parsed", functions=(_function("top", calls=(_call("middle", 10, classification="maybe"),)),))
    with pytest.raises(CoverageError) as exc_info:
        analyze_coupling(_model(unit), _document())
    assert exc_info.value.reason == "unknown_call_classification"


def test_an_indirect_call_that_names_a_callee_is_refused() -> None:
    """An indirect target is never guessed; a record that names one is not trusted."""
    unit = AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(_function("top", calls=(_call("middle", 10, classification="unresolved", via="function_pointer"),)),),
    )
    with pytest.raises(CoverageError) as exc_info:
        analyze_coupling(_model(unit), _document())
    assert exc_info.value.reason == "indirect_call_names_callee"


def test_an_unknown_global_access_is_refused() -> None:
    unit = AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(_function("touch", globals_=(GlobalAccessModel("mode", "x"),)),),
        global_variables=(_global("mode"),),
    )
    with pytest.raises(CoverageError) as exc_info:
        analyze_coupling(_model(unit), _document())
    assert exc_info.value.reason == "unknown_global_access"


# --- failed units, data only, byte stability ----------------------------------------------------


def test_a_failed_unit_is_listed_as_not_analysed() -> None:
    failed = AnalysisUnit("src/broken.c", "failed")
    report = analyze_coupling(_model(_chain(), failed), _chain_coverage())
    assert report.analysed_units == (_UNIT,)
    assert report.not_analysed_units == ({"unit": "src/broken.c", "reason": "unit_not_parsed"},)


def test_the_report_carries_data_only() -> None:
    """No score, percentage or verdict about a coupling objective."""
    unit = AnalysisUnit(
        _UNIT,
        "parsed",
        functions=(
            _function("top", calls=(_call("middle", 10),)),
            _function("middle"),
            _function("set_mode", globals_=(GlobalAccessModel("mode", "w"),)),
        ),
        global_variables=(_global("mode"),),
    )
    document = analyze_coupling(_model(unit), _document(_file(_UNIT, lines={10: (1, [1])}))).to_dict()
    assert set(document) == {"schema_version", "units", "call_pairs", "data_pairs_basis", "variables"}
    assert document["data_pairs_basis"] == DATA_PAIR_BASIS == "function_executed"
    assert document["call_pairs"][0]["status"] in COUPLING_STATUSES
    assert {variable["status"] for variable in document["variables"]} <= {"recorded", "not_determinable"}
    # nothing that reads as a score or a verdict about a coupling objective
    for forbidden in ("percent", "score", "verdict", "objective", "passed"):
        assert forbidden not in str(document)


def _reversed_chain() -> tuple[AnalysisModel, Any]:
    unit = AnalysisUnit(
        "./" + _UNIT,
        "parsed",
        functions=(
            _function("skip", "./" + _UNIT, calls=(_call("leaf", 30),)),
            _function("middle", "./" + _UNIT, calls=(_call("leaf", 20),)),
            _function("top", "./" + _UNIT, calls=(_call("middle", 10),)),
        ),
    )
    coverage = _document(
        _file(
            _UNIT,
            executed={"leaf": 3, "skip": 3, "middle": 3, "top": 3},
            lines={30: (1, [1]), 20: (3, [3]), 10: (3, [3])},
        )
    )
    return _model(unit), coverage


def test_output_is_byte_stable_under_input_order_and_path_spelling() -> None:
    """verifies: TOOL-COV-170 — the same content in another order and with another
    path spelling gives identical bytes."""
    first = analyze_coupling(_model(_chain()), _chain_coverage(last_returned=1, last_count=1))
    second = analyze_coupling(*_reversed_chain())
    assert first.to_json_bytes() == second.to_json_bytes()
    assert first.to_json_bytes() == analyze_coupling(_model(_chain()), _chain_coverage(last_returned=1, last_count=1)).to_json_bytes()


# --- through the real analyzer -------------------------------------------------------------------


SOURCE = b"""static int mode;
static int unused;
static int leaf(int x) { return x + 1; }
static int middle(int x) { return leaf(x) * 2; }
int top(int x) { return middle(x); }
int skipped(int x) { return leaf(x); }
static void set_mode(int m) {
    mode = m;
}
static int get_mode(void) {
    return mode;
}
int use_mode(int m) {
    set_mode(m);
    return get_mode();
}
"""


def test_the_real_analyzer_output_drives_the_analysis() -> None:
    """The analysis model the tool actually extracts, matched against gcov data."""
    unit = extract_interfaces(parse("probe.c", args=["-std=c11"], unsaved_files=[("probe.c", SOURCE)]))
    model = _model(unit)
    file = next(iter(unit.functions)).location.file
    executed = {"use_mode": 4, "set_mode": 4, "get_mode": 4, "top": 3, "middle": 3, "skipped": 0, "leaf": 3}
    lines = {
        call.line: ((0, [0]) if function.name == "skipped" else (executed[function.name], [executed[function.name]]))
        for function in unit.functions
        for call in function.calls
    }
    report = analyze_coupling(model, _document(_file(file, executed=executed, lines=lines)))

    assert _calls(report) == {
        ("middle", "leaf"): ("exercised", None),
        ("top", "middle"): ("exercised", None),
        ("skipped", "leaf"): ("not_exercised", "call_site_not_reached"),
        ("use_mode", "set_mode"): ("exercised", None),
        ("use_mode", "get_mode"): ("exercised", None),
    }
    mode = _variable(report, "mode", unit.path)
    assert [(p.writer, p.reader, p.status) for p in mode.pairs] == [("set_mode", "get_mode", "exercised")]
    unused = _variable(report, "unused", unit.path)
    assert (unused.status, unused.reason) == ("not_determinable", "no_recorded_access")


def test_the_analysis_vocabularies_are_the_ones_the_module_checks_against() -> None:
    """The refusals test the analysis model's own vocabularies, not local copies."""
    assert CALL_VIA == ("direct", "function_pointer", "undeclared")
    assert CALL_CLASSIFICATIONS == ("internal", "external", "library", "unresolved")
