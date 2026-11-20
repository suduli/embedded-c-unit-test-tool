# implements: TASK-108
"""Seeded property-style tests for the restricted YAML adapter and schema dispatch.

Hand-rolled property loops over explicit ``random.Random(seed)`` instances —
deterministic seeds only, no global RNG state, no new dependencies. The
generator builds random nested documents from a conservative scalar alphabet;
any round-trip failure on generated input is a real finding, not test noise.

Covers:
- the restricted YAML adapter (ectt.prj.yaml_adapter): dump -> load round
  trips preserve the document (scalars re-materialise as their canonical
  string forms — the adapter parses every scalar as a string), and dumping
  is independent of key insertion order;
- the schema-version dispatch reader (ectt.prj.model.dispatch_schema_version):
  every integer partition behaves per SDD-003 §5.

TASK-108 note: the queue's allowed paths for this filler are tests/core and
tests/prj only, so the property suite targets the prj YAML adapter and the
prj schema-version reader; the ana schema reader's own fuzz coverage remains
with the ana queue (ledger note).
"""

from __future__ import annotations

import random
from collections.abc import Callable
from typing import Any

import pytest

from ectt.core.determinism import canonical_float_repr
from ectt.prj.errors import (
    InvalidSchemaVersionError,
    MigrationRequiredError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
)
from ectt.prj.model import FileKind, dispatch_schema_version
from ectt.prj.yaml_adapter import RestrictedYamlAdapter

SEEDS = (42, 1337, 20261119)
DOCS_PER_SEED = 25

ADAPTER = RestrictedYamlAdapter()
_KIND = FileKind(name="property", file_pattern="property.kind", min_version=2, max_version=5)

_SPECIAL_STRINGS = [
    "",
    "true",
    "false",
    "null",
    "123",
    "1.5",
    "yes",
    "-",
    "a: b",
    'quote"inside',
    "back\\slash",
    "sp ace",
    "#hash",
    "trailing ",
    "  leading",
    "semicolon;still fine",
    "unicode-ß-é-日本",
]

_SCALAR_KINDS = ("str", "int", "float", "bool")


def _random_scalar(rng: random.Random) -> Any:
    kind = rng.choice(_SCALAR_KINDS)
    if kind == "str":
        if rng.random() < 0.3:
            return rng.choice(_SPECIAL_STRINGS)
        return "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABC0123456789_-") for _ in range(rng.randint(1, 12)))
    if kind == "int":
        return rng.randint(-10**6, 10**6)
    if kind == "float":
        return rng.choice([rng.uniform(-1000, 1000), 0.0, -0.0, 1e-7, 3.14159])
    return rng.choice([True, False])


def _random_value(rng: random.Random, depth: int = 0) -> Any:
    if depth >= 3:
        return _random_scalar(rng)
    kind = rng.choice(("scalar", "scalar", "list", "dict"))
    if kind == "list":
        return [_random_value(rng, depth + 1) for _ in range(rng.randint(0, 4))]
    if kind == "dict":
        return {
            f"key_{rng.randint(0, 999)}_{position}": _random_value(rng, depth + 1)
            for position in range(rng.randint(1, 4))
        }
    return _random_scalar(rng)


def _random_doc(rng: random.Random) -> dict[str, Any]:
    doc = {
        f"field_{rng.randint(0, 99)}_{position}": _random_value(rng, 1)
        for position in range(rng.randint(1, 5))
    }
    if rng.random() < 0.5:
        doc["schema_version"] = rng.randint(1, 3)
    return doc


def _stringify(value: Any) -> Any:
    """The document as the adapter re-materialises it: every scalar is a string."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return canonical_float_repr(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return {str(key): _stringify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_stringify(item) for item in value]
    raise AssertionError(f"generator produced an unsupported value: {value!r}")


# --- round-trip property ---------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_round_trip_preserves_generated_documents(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(DOCS_PER_SEED):
        doc = _random_doc(rng)
        expected = _stringify(doc)

        loaded = ADAPTER.load(ADAPTER.dump(doc))

        assert loaded == expected


def test_float_and_bool_scalars_round_trip_through_their_canonical_forms() -> None:
    rng = random.Random(7)
    for _ in range(20):
        doc = {"value": _random_scalar(rng)}

        loaded = ADAPTER.load(ADAPTER.dump(doc))

        assert loaded == _stringify(doc)


# --- determinism property --------------------------------------------------------------


@pytest.mark.parametrize("seed", SEEDS)
def test_dump_is_independent_of_key_insertion_order(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(DOCS_PER_SEED):
        doc = _random_doc(rng)
        shuffled: dict[str, Any] = {}
        keys = list(doc)
        rng.shuffle(keys)
        for key in keys:
            shuffled[key] = doc[key]

        assert ADAPTER.dump(doc) == ADAPTER.dump(shuffled)
        assert ADAPTER.dump(doc) == ADAPTER.dump(doc)


# --- schema-version dispatch property --------------------------------------------------


def _dispatch(doc: dict[str, Any]) -> Callable[[], int]:
    return lambda: dispatch_schema_version(doc, _KIND)


@pytest.mark.parametrize("seed", SEEDS)
def test_dispatch_partitions_the_version_line(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(DOCS_PER_SEED):
        below = rng.randint(-3, _KIND.min_version - 1)
        inside = rng.randint(_KIND.min_version, _KIND.max_version)
        above = rng.randint(_KIND.max_version + 1, _KIND.max_version + 20)

        with pytest.raises(MigrationRequiredError):
            _dispatch({"schema_version": below})()

        assert dispatch_schema_version({"schema_version": inside}, _KIND) == inside
        assert dispatch_schema_version({"schema_version": str(inside)}, _KIND) == inside

        with pytest.raises(UnsupportedSchemaVersionError) as excinfo:
            _dispatch({"schema_version": above})()
        assert excinfo.value.version == above


def test_dispatch_refuses_absent_and_malformed_versions() -> None:
    rng = random.Random(99)
    malformed: list[Any] = ["3.5", "three", "", None, [], {}, rng.random()]
    for value in malformed:
        doc = {"schema_version": value} if value is not None else {"name": "x"}

        if value is None:
            with pytest.raises(MissingSchemaVersionError):
                _dispatch(doc)()
        else:
            with pytest.raises(InvalidSchemaVersionError):
                _dispatch(doc)()


def test_dispatch_accepts_whitespace_padded_integer_strings() -> None:
    for version in range(_KIND.min_version, _KIND.max_version + 1):
        assert dispatch_schema_version({"schema_version": f"  {version} "}, _KIND) == version


def test_generated_docs_with_schema_version_dispatch_cleanly() -> None:
    rng = random.Random(20261119)
    for _ in range(DOCS_PER_SEED):
        doc = _random_doc(rng)
        doc["schema_version"] = rng.randint(_KIND.min_version, _KIND.max_version)

        assert dispatch_schema_version(doc, _KIND) == doc["schema_version"]
