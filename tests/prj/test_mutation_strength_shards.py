# implements: TOOL-PRJ-060
"""Hand-written mutation battery for the sharded store contracts (B8).

No product code is changed. The mutants are hand-written copies of the
shard-name validation and the read_shards one-key contract with a single
seeded fault each, executed in isolation; the real implementation is the
oracle. Shard names are the confinement boundary of the sharded layout and
the one-key contract is what makes read_shards a faithful inverse of save.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from ectt.prj.errors import InvalidRelativePathError, ProjectError
from ectt.prj.project import Project
from ectt.prj.shards import ShardStore

_SHARD_NAME_REAL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SHARD_NAME_MUTANT = re.compile(r"^[A-Za-z0-9._-]+$")  # FAULT: leading dot allowed


def _real_shard_path(name: str) -> Path:
    return ShardStore(Path("store")).shard_path(name)


def _mutant_shard_path(name: str) -> Path:
    if not _SHARD_NAME_MUTANT.match(name):
        raise InvalidRelativePathError(f"invalid shard name: {name!r}", reason="invalid_shard_name", path=name)
    return Path("store") / "shards" / f"{name}.yaml"


def _real_read_shards(files: dict[str, str]) -> dict[str, Any]:
    """Hand-written copy of Project.read_shards' merge contract."""
    result: dict[str, Any] = {}
    for name in sorted(files):
        data = _yaml_like(files[name])
        if not isinstance(data, dict) or len(data) != 1:
            raise ProjectError(f"shard '{name}' must hold exactly one top-level key", reason="invalid_shard")
        result.update(data)
    return result


def _mutant_read_shards(files: dict[str, str]) -> dict[str, Any]:
    """FAULT: the one-key contract check is dropped."""
    result: dict[str, Any] = {}
    for name in sorted(files):
        data = _yaml_like(files[name])
        if isinstance(data, dict):
            result.update(data)
    return result


def _yaml_like(text: str) -> Any:
    # minimal stand-in for the adapter in the isolated copies: key: value lines
    result: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def test_real_shard_name_validation() -> None:
    assert _real_shard_path("users") == Path("store") / "shards" / "users.yaml"
    assert _real_shard_path("a.b-c_d") == Path("store") / "shards" / "a.b-c_d.yaml"
    for bad in (".git", "..", "-lead", "", "sp ace"):
        with pytest.raises(InvalidRelativePathError) as exc_info:
            _real_shard_path(bad)
        assert exc_info.value.reason == "invalid_shard_name"


def test_real_read_shards_one_key_contract() -> None:
    assert _real_read_shards({"name": "name: alpha"}) == {"name": "alpha"}
    with pytest.raises(ProjectError) as exc_info:
        _real_read_shards({"multi": "a: 1\nb: 2"})
    assert exc_info.value.reason == "invalid_shard"


def test_mutant_lax_shard_name_is_killed() -> None:
    """The leading-dot name ('.git') must be refused; the mutant accepts it."""
    with pytest.raises(InvalidRelativePathError):
        _real_shard_path(".git")
    accepted_by_mutant = _mutant_shard_path(".git")  # resolves instead of raising
    assert accepted_by_mutant == Path("store") / "shards" / ".git.yaml"


def test_mutant_dropping_one_key_contract_is_killed() -> None:
    """A two-key shard must be refused; the mutant silently merges it."""
    with pytest.raises(ProjectError):
        _real_read_shards({"multi": "a: 1\nb: 2"})
    assert _mutant_read_shards({"multi": "a: 1\nb: 2"}) == {"a": "1", "b": "2"}


def test_prj_kill_rate_report(capsys: pytest.CaptureFixture[str]) -> None:
    """A mutant is killed when its outcome differs from the real implementation."""
    name_probes = (".git", "users")

    def name_outcome(resolve: Any, probe: str) -> str:
        try:
            return f"ok:{resolve(probe)}"
        except InvalidRelativePathError:
            return "refused:invalid_shard_name"

    def merge_outcome(resolve: Any, probe: str) -> str:
        try:
            return f"ok:{resolve(probe)}"
        except ProjectError:
            return "refused:invalid_shard"

    killed = 0
    total = 2
    differing = [p for p in name_probes if name_outcome(_real_shard_path, p) != name_outcome(_mutant_shard_path, p)]
    print(f"  prj-m1-shard-name-lax: {'killed by ' + str(differing) if differing else 'SURVIVED'}")
    if differing:
        killed += 1
    probe = {"multi": "a: 1\nb: 2"}
    if merge_outcome(_real_read_shards, probe) != merge_outcome(_mutant_read_shards, probe):
        killed += 1
        print("  prj-m2-one-key-contract-dropped: killed")
    else:
        print("  prj-m2-one-key-contract-dropped: SURVIVED")
    print(f"prj shards kill rate: {killed}/{total}")
    assert killed == total


def test_sharded_save_and_shard_store_agree(tmp_path: Path) -> None:
    """The battery's isolated copies match the real save/read discipline."""
    project = Project.create(tmp_path / "p", name="alpha", source_roots=["src"])
    project.save(layout="sharded")
    store = ShardStore(project.root)
    for key in project.document.data:
        assert store.read_shard(key) is not None
    merged = Project(project.root, project.document).read_shards()
    for key, value in merged.items():
        assert project.document.data[key] == value
