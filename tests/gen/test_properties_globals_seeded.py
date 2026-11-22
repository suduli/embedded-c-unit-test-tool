# implements: TOOL-HAR-040, TOOL-NFR-060
"""Seeded property-style tests for the generated C's identifier and declarator
safety (A7, tests only; no src/ edits).

Fixed seeds (the seed is the test id); no wall clock; no C compiler — the
generated text is checked by structural assertions and by libclang parsing on
disk. Properties:

* **Generated C identifier safety**: random legal identifiers in the global
  exposure inventory always render verbatim, produce exactly one declaration
  each, and every declaration parses as C99; the block is byte-stable under
  input reordering.
* **Declarator discipline**: array dimensions always bind to the identifier
  (``extern T name[dims];``), for every random shape of builtin, pointer and
  array types; a non-array never carries a suffix.

The trust boundary of the type-graph spelling is recorded in the ledger:
``spell_type`` echoes the analysis model's own recorded spellings, and the
model is built by the libclang analyzer from parsed C — an identifier set —
so an unreachable-spelling injection is not reachable through the real
pipeline. The authored-input gate (case ids) is pinned in
tests/gen/test_testbody.py.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

import pytest

from ectt.ana.frontend import parse
from ectt.ana.model import (
    AnalysisModel,
    AnalysisUnit,
    DimensionModel,
    GlobalVariableModel,
    ProvenanceModel,
    TypeModel,
)
from ectt.gen import render_global_exposure_block, resolve_global_exposures, spell_type

SEEDS = [0, 1, 7, 42, 1337]

_SAFE_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _identifier(rng: random.Random) -> str:
    head = rng.choice("abcdefghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    return head + "".join(
        rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")
        for _ in range(rng.randint(0, 40))
    )


def _graph(rng: random.Random) -> tuple[dict[str, TypeModel], list[str]]:
    """Random legal variables with builtin/pointer/array types and their ids."""
    types: dict[str, TypeModel] = {}
    names: list[str] = []
    for index in range(rng.randint(1, 5)):
        name = _identifier(rng)
        if not _SAFE_ID.match(name) or name in names:
            continue
        names.append(name)
        type_id = f"type.v{index}"
        shape = rng.choice(("builtin", "pointer", "array", "array2d"))
        if shape == "builtin":
            types[type_id] = TypeModel(kind="builtin", name=rng.choice(("int", "unsigned char", "double")))
        else:
            types["type.base"] = TypeModel(kind="builtin", name="int" if shape != "array" else "unsigned char")
            if shape == "pointer":
                types[type_id] = TypeModel(kind="pointer", target="ref:type.base")
            elif shape == "array":
                types[type_id] = TypeModel(kind="array", element_type="ref:type.base", size=rng.randint(1, 16))
            else:
                types[type_id] = TypeModel(
                    kind="array",
                    element_type="ref:type.base",
                    dimensions=(DimensionModel(size=rng.randint(1, 8)), DimensionModel(size=rng.randint(1, 8))),
                )
    return types, names


@pytest.mark.parametrize("seed", SEEDS)
def test_random_legal_identifiers_render_verbatim_and_parse(seed: int, tmp_path: Path) -> None:
    """verifies: TOOL-HAR-040 — random legal identifiers survive rendering
    verbatim, produce exactly one declaration each, and parse cleanly."""
    rng = random.Random(seed)
    types, names = _graph(rng)
    if not names:
        pytest.skip("the draw produced no usable identifiers")
    variables = tuple(
        GlobalVariableModel(
            name=name, type=f"ref:type.v{index}", has_initializer=rng.random() < 0.5, storage_class="none"
        )
        for index, name in enumerate(names)
    )
    unit = AnalysisUnit(path="uut.c", status="parsed", global_variables=variables)
    model = AnalysisModel(provenance=ProvenanceModel("0.1.0", "s", "s"), units=(unit,), types=types)
    exposures = resolve_global_exposures(unit, model.types)
    assert [e.name for e in exposures] == sorted(names)  # name-sorted, verbatim
    by_name = {e.name: e.declaration for e in exposures}
    assert len(by_name) == len(variables)
    for variable in variables:
        declaration = by_name[variable.name]
        assert declaration is not None
        assert f" {variable.name}" in declaration

    # The rendered block is byte-stable under reordering of the inventory.
    reordered = tuple(reversed(variables))
    unit2 = AnalysisUnit(path="uut.c", status="parsed", global_variables=reordered)
    block2 = render_global_exposure_block(resolve_global_exposures(unit2, model.types))
    assert block2 == render_global_exposure_block(exposures)

    # Every declaration parses as C99 (extern declarations need no definition).
    (tmp_path / "decls.c").write_text("\n".join(by_name.values()) + "\n", encoding="utf-8")
    parsed = parse(tmp_path / "decls.c", args=["-std=c99", "-pedantic"])
    assert parsed.status == "parsed"
    assert [d for d in parsed.diagnostics if d.severity in ("error", "fatal")] == []


@pytest.mark.parametrize("seed", SEEDS)
def test_array_dimensions_bind_to_the_identifier(seed: int) -> None:
    """verifies: TOOL-HAR-040 — for every random shape, array dimensions bind
    to the identifier (``extern T name[dims];``) and never to the element type."""
    rng = random.Random(seed)
    types, names = _graph(rng)
    variables = tuple(
        GlobalVariableModel(name=name, type=f"ref:type.v{index}", has_initializer=False, storage_class="none")
        for index, name in enumerate(names)
    )
    unit = AnalysisUnit(path="uut.c", status="parsed", global_variables=variables)
    for exposure in resolve_global_exposures(unit, types):
        assert exposure.declaration is not None
        if exposure.declarator_suffix:
            assert f"{exposure.name}{exposure.declarator_suffix};" in exposure.declaration
            assert "] " + exposure.name not in exposure.declaration
        else:
            assert exposure.declaration.endswith(f" {exposure.name};")


def test_a_missing_type_reference_is_none_and_a_chain_is_refused() -> None:
    """verifies: TOOL-HAR-040 — escape safety of the spelling boundary: a
    missing reference is None (never guessed) and a recursive chain is refused
    rather than looped."""
    assert spell_type("ref:type.missing", {"type.other": TypeModel(kind="builtin", name="int")}) is None
    looped = {
        "type.a": TypeModel(kind="typedef", name=None, underlying_type="ref:type.b"),
        "type.b": TypeModel(kind="typedef", name=None, underlying_type="ref:type.a"),
    }
    assert spell_type("ref:type.a", looped) is None
