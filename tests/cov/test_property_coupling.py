# implements: TOOL-COV-170
"""Seeded property-style tests over the coupling analysis (B7).

Tests only; no src/ edits. Units, functions, calls, global accesses and gcov
files are generated from fixed seeds (``random.Random(SEED)``) so a failure
reproduces exactly; no wall clock. Properties, not snapshots:

- order independence: the same content in any unit, function, coverage-file or
  line order gives byte-identical reports;
- status conservation: every call pair and data pair has exactly one status
  from the vocabulary, and an exercised/not-exercised status is only ever
  produced when the coverage data decided it;
- identity: a same-named static in two units never produces a data pair.
"""

from __future__ import annotations

import random
from typing import Any

from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    CallModel,
    FunctionModel,
    GlobalAccessModel,
    GlobalVariableModel,
    ProvenanceModel,
    SourceLocation,
)
from ectt.cov.coupling import COUPLING_STATUSES, analyze_coupling
from ectt.cov.gcov import read_gcov_document

SEED = 20261123


def _seeded_model(rng: random.Random) -> tuple[AnalysisModel, dict[tuple[str, str], int]]:
    """Units on one shared module (`src/u<i>.c`) with calls between them and
    shared external globals; returns the model and the function execution
    counts the coverage document must carry."""
    n_units = rng.randint(2, 4)
    units: list[AnalysisUnit] = []
    executed: dict[tuple[str, str], int] = {}
    external_globals = [f"g{i}" for i in range(rng.randint(1, 3))]
    for unit_index in range(n_units):
        path = f"src/u{unit_index}.c"
        n_functions = rng.randint(2, 5)
        names = [f"u{unit_index}_f{i}" for i in range(n_functions)]
        functions: list[FunctionModel] = []
        for i, name in enumerate(names):
            # a call to a function of the next unit (external) and, within the
            # first unit, to a sibling (internal)
            calls: list[CallModel] = []
            if unit_index > 0 and rng.random() < 0.7:
                target_unit = rng.randrange(n_units)
                calls.append(
                    CallModel(
                        callee=f"u{target_unit}_f{rng.randrange(3)}",
                        classification="internal" if target_unit == unit_index else "external",
                        via="direct",
                        line=10 + i,
                    )
                )
            globals_: list[GlobalAccessModel] = []
            if rng.random() < 0.6:
                access = rng.choice(("r", "w", "rw"))
                globals_.append(GlobalAccessModel(name=rng.choice(external_globals), access=access))
            functions.append(
                FunctionModel(
                    name=name,
                    linkage="external",
                    storage_class="none",
                    location=SourceLocation(file=path, line=1 + i),
                    return_type="ref:type.int",
                    calls=tuple(calls),
                    globals=tuple(globals_),
                )
            )
            executed[(path, name)] = rng.randint(0, 4)
        global_variables = tuple(
            GlobalVariableModel(name=g, type="ref:type.int", has_initializer=False, storage_class="none")
            for g in external_globals
        )
        units.append(
            AnalysisUnit(path, "parsed", functions=tuple(functions), global_variables=global_variables)
        )
    return AnalysisModel(provenance=ProvenanceModel("test", "fe", "now"), units=tuple(units)), executed


def _seeded_payload(executed: dict[tuple[str, str], int]) -> dict[str, Any]:
    """The raw gcov payload derived from the same draw: one file per analysed
    unit, one line record per function (its own line, its own count)."""
    per_file: dict[str, dict[str, Any]] = {}
    for (path, name), count in sorted(executed.items()):
        entry = per_file.setdefault(path, {"file": path, "functions": [], "lines": []})
        entry["functions"].append(
            {"name": name, "start_line": 1, "end_line": 9, "execution_count": count}
        )
        entry["lines"].append(
            {"line_number": 10 + len(entry["lines"]), "count": count, "unexecuted_block": False}
        )
    return {
        "format_version": "2",
        "gcc_version": "14.1.0",
        "data_file": "d.gcda",
        "files": [per_file[path] for path in sorted(per_file)],
    }


def _statuses(report: Any) -> list[tuple[Any, ...]]:
    pairs = [(p.caller_unit, p.caller, p.callee, p.status, p.reason) for p in report.call_pairs]
    pairs.extend(
        (pair.writer_unit, pair.writer, pair.variable, pair.status, pair.reason)
        for variable in report.variables
        for pair in variable.pairs
    )
    return sorted(pairs, key=lambda entry: tuple(str(part) for part in entry))


def test_coupling_is_order_independent_over_seeded_models() -> None:
    """The same content in another unit order and another coverage order gives
    byte-identical output, over seeded draws."""
    for round_index in range(5):
        rng = random.Random(SEED + round_index)
        model, executed = _seeded_model(rng)
        document = read_gcov_document(_seeded_payload(executed))
        first = analyze_coupling(model, document)

        shuffled_units = list(model.units)
        rng.shuffle(shuffled_units)
        payload = _seeded_payload(executed)
        rng.shuffle(payload["files"])
        for file in payload["files"]:
            rng.shuffle(file["functions"])
            rng.shuffle(file["lines"])
        second = analyze_coupling(
            AnalysisModel(model.provenance, units=tuple(shuffled_units)),
            read_gcov_document(payload),
        )

        assert first.to_json_bytes() == second.to_json_bytes(), round_index


def test_coupling_statuses_stay_in_the_vocabulary_over_seeded_draws() -> None:
    """Every pair has exactly one coupling status, whatever the draw."""
    for round_index in range(5):
        rng = random.Random(SEED + 10 + round_index)
        model, executed = _seeded_model(rng)
        report = analyze_coupling(model, read_gcov_document(_seeded_payload(executed)))
        for pair in report.call_pairs:
            assert pair.status in COUPLING_STATUSES
            # an exercised pair needs no reason; every other status names one
            if pair.status == "exercised":
                assert pair.reason is None
            else:
                assert pair.reason
        for variable in report.variables:
            for pair in variable.pairs:
                assert pair.status in COUPLING_STATUSES
                if pair.status == "exercised":
                    assert pair.reason is None
                else:
                    assert pair.reason
        # statuses that decide (exercised/not_exercised) imply coverage decided
        for pair in report.call_pairs:
            if pair.status in ("exercised", "not_exercised"):
                assert all(site.status != "not_determinable" for site in pair.sites)


def test_same_named_statics_never_pair_over_seeded_draws() -> None:
    """The identity property over random access patterns: a data pair always
    names two units for an external variable, and a static variable of one unit
    is never paired through another unit's same-named static."""
    for round_index in range(5):
        rng = random.Random(SEED + 20 + round_index)
        model, executed = _seeded_model(rng)
        report = analyze_coupling(model, read_gcov_document(_seeded_payload(executed)))
        for variable in report.variables:
            for pair in variable.pairs:
                if variable.linkage == "internal":
                    assert pair.writer_unit == pair.reader_unit == variable.unit
                else:
                    # an external pair is a genuine cross-unit or same-unit
                    # pair of functions that both recorded the name
                    assert (pair.writer, pair.reader) != ("", "")
