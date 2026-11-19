# implements: TASK-107
"""Hand-written mutation battery for ectt.prj (TASK-107, tests only).

No product code is changed. Each mutant is a hand-written copy of one
critical prj function (or a subclass overriding exactly one method) with a
single seeded fault. The battery asserts the real implementation passes
every case and every mutant is killed; a kill-rate report is printed by the
summary test.

Mutant selection: dangling-reference reporting (TOOL-PRJ-090) and
diff-stable shard writes (TOOL-PRJ-060) are the prj contracts downstream
packages rely on; a silent fault changes project semantics without changing
file shapes.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from ectt.prj.errors import InvalidRelativePathError
from ectt.prj.references import OWNER_FILE, DanglingReference, find_dangling_references
from ectt.prj.shards import _SHARD_NAME, ShardStore


@dataclass(frozen=True)
class ExpectRaise:
    exc: type[Exception]


@dataclass(frozen=True)
class Case:
    case_id: str
    run: Callable[[Any], Any]
    expect: Any


def _killed(case: Case, impl: Any) -> bool:
    if isinstance(case.expect, ExpectRaise):
        try:
            case.run(impl)
        except case.expect.exc:
            return False  # expected failure: matches the real behaviour
        except Exception:
            return True  # a different exception is a behaviour change
        return True  # no exception where the real one raises: detected
    try:
        actual = case.run(impl)
    except Exception:
        return True
    return actual != case.expect


# --- find_dangling_references mutants --------------------------------------------------


def _classify_reference(root: Path, rel: str) -> str | None:
    """Faithful copy of references._classify (no fault)."""
    from ectt.prj.paths import resolve_project_path, validate_project_path

    try:
        normalized = validate_project_path(rel)
    except InvalidRelativePathError:
        return "invalid_path"
    try:
        target = resolve_project_path(root, normalized)
    except (OSError, RuntimeError):
        return "unresolvable"
    try:
        if not target.exists():
            return "missing_target"
        if not target.is_dir():
            return "not_a_directory"
    except (OSError, RuntimeError):
        return "unresolvable"
    return None


def _classify_drifted_reason(root: Path, rel: str) -> str | None:
    """Single fault: the missing-target reason string has drifted."""
    reason = _classify_reference(root, rel)
    return "missing" if reason == "missing_target" else reason


def _mp1_dangling_drops_output(root: Path, source_roots: list[str], output_root: str | None) -> tuple[DanglingReference, ...]:
    found: list[DanglingReference] = []
    for rel in source_roots:
        reason = _classify_reference(root, rel)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="source_root", target=rel, required=True, reason=reason)
            )
    # fault: the optional output_root branch is never checked
    return tuple(sorted(found))


def _mp2_dangling_required_flipped(root: Path, source_roots: list[str], output_root: str | None) -> tuple[DanglingReference, ...]:
    found: list[DanglingReference] = []
    for rel in source_roots:
        reason = _classify_reference(root, rel)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="source_root", target=rel, required=False, reason=reason)
            )
    if output_root:
        reason = _classify_reference(root, output_root)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="output_root", target=output_root, required=False, reason=reason)
            )
    return tuple(sorted(found))


def _mp3_dangling_reason_drifted(root: Path, source_roots: list[str], output_root: str | None) -> tuple[DanglingReference, ...]:
    found: list[DanglingReference] = []
    for rel in source_roots:
        reason = _classify_drifted_reason(root, rel)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="source_root", target=rel, required=True, reason=reason)
            )
    if output_root:
        reason = _classify_drifted_reason(root, output_root)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="output_root", target=output_root, required=False, reason=reason)
            )
    return tuple(sorted(found))


def _mp4_dangling_unsorted(root: Path, source_roots: list[str], output_root: str | None) -> tuple[DanglingReference, ...]:
    found: list[DanglingReference] = []
    for rel in source_roots:
        reason = _classify_reference(root, rel)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="source_root", target=rel, required=True, reason=reason)
            )
    if output_root:
        reason = _classify_reference(root, output_root)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="output_root", target=output_root, required=False, reason=reason)
            )
    return tuple(found)  # fault: caller order, not sorted order


def _mp5_dangling_files_accepted(root: Path, source_roots: list[str], output_root: str | None) -> tuple[DanglingReference, ...]:
    def classify(root_path: Path, rel: str) -> str | None:
        from ectt.prj.paths import resolve_project_path, validate_project_path

        try:
            normalized = validate_project_path(rel)
        except InvalidRelativePathError:
            return "invalid_path"
        try:
            target = resolve_project_path(root_path, normalized)
        except (OSError, RuntimeError):
            return "unresolvable"
        try:
            if not target.exists():
                return "missing_target"
            # fault: the not_a_directory check is dropped
        except (OSError, RuntimeError):
            return "unresolvable"
        return None

    found: list[DanglingReference] = []
    for rel in source_roots:
        reason = classify(root, rel)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="source_root", target=rel, required=True, reason=reason)
            )
    if output_root:
        reason = classify(root, output_root)
        if reason is not None:
            found.append(
                DanglingReference(owner=OWNER_FILE, kind="output_root", target=output_root, required=False, reason=reason)
            )
    return tuple(sorted(found))


def _refs_cases(base: Path) -> list[Case]:
    (base / "src").mkdir(parents=True, exist_ok=True)
    (base / "build").mkdir(parents=True, exist_ok=True)
    (base / "f.txt").write_text("x", encoding="utf-8")
    return [
        Case("healthy_project", lambda f: f(base, ["src"], "build"), ()),
        Case(
            "missing_source_root",
            lambda f: f(base, ["nope"], None),
            (DanglingReference(owner=OWNER_FILE, kind="source_root", target="nope", required=True, reason="missing_target"),),
        ),
        Case(
            "missing_output_root",
            lambda f: f(base, ["src"], "gone"),
            (DanglingReference(owner=OWNER_FILE, kind="output_root", target="gone", required=False, reason="missing_target"),),
        ),
        Case(
            "file_as_source_root",
            lambda f: f(base, ["f.txt"], None),
            (DanglingReference(owner=OWNER_FILE, kind="source_root", target="f.txt", required=True, reason="not_a_directory"),),
        ),
        Case(
            "invalid_path",
            lambda f: f(base, ["../escape"], None),
            (DanglingReference(owner=OWNER_FILE, kind="source_root", target="../escape", required=True, reason="invalid_path"),),
        ),
        Case(
            "sorted_output",
            lambda f: f(base, ["z_miss", "a_miss"], None),
            (
                DanglingReference(owner=OWNER_FILE, kind="source_root", target="a_miss", required=True, reason="missing_target"),
                DanglingReference(owner=OWNER_FILE, kind="source_root", target="z_miss", required=True, reason="missing_target"),
            ),
        ),
    ]


REFS_MUTANTS: list[tuple[str, Any, Callable[[Path], list[Case]]]] = [
    ("find_dangling_references/MP1-output-branch-dropped", _mp1_dangling_drops_output, _refs_cases),
    ("find_dangling_references/MP2-required-flipped", _mp2_dangling_required_flipped, _refs_cases),
    ("find_dangling_references/MP3-reason-drifted", _mp3_dangling_reason_drifted, _refs_cases),
    ("find_dangling_references/MP4-unsorted", _mp4_dangling_unsorted, _refs_cases),
    ("find_dangling_references/MP5-files-accepted", _mp5_dangling_files_accepted, _refs_cases),
]


# --- ShardStore mutants ----------------------------------------------------------------


class _MS1AlwaysRewrite(ShardStore):
    def write_shard(self, name: str, content: str) -> bool:
        path = self.shard_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".yaml.tmp")
        tmp.write_text(content, encoding="utf-8", newline="")
        os.replace(tmp, path)
        return True  # fault: diff stability dropped


class _MS2YmlSuffix(ShardStore):
    def shard_path(self, name: str) -> Path:
        if not _SHARD_NAME.match(name):
            raise InvalidRelativePathError(f"invalid shard name: {name!r}", reason="invalid_shard_name", path=name)
        return self._shard_dir / f"{name}.yml"  # fault: suffix drifted


class _MS3NoValidation(ShardStore):
    def shard_path(self, name: str) -> Path:
        return self._shard_dir / f"{name}.yaml"  # fault: name validation dropped


class _MS4WriteReportsFalse(ShardStore):
    def write_shard(self, name: str, content: str) -> bool:
        path = self.shard_path(name)
        try:
            previous = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            previous = None
        if previous == content:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".yaml.tmp")
        tmp.write_text(content, encoding="utf-8", newline="")
        os.replace(tmp, path)
        return False  # fault: success reported as no-change


class _MS5ReadEmptyForMissing(ShardStore):
    def read_shard(self, name: str) -> str | None:
        path = self.shard_path(name)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""  # fault: missing shard indistinguishable from empty


def _shards_cases(base: Path) -> list[Case]:
    def sub(name: str) -> Path:
        p = base / name
        p.mkdir(parents=True, exist_ok=True)
        return p

    return [
        Case("write_new_returns_true", lambda s: s(sub("c1")).write_shard("data", "alpha: 1\n"), True),
        Case(
            "unchanged_write_is_noop",
            lambda s: (lambda store: (store.write_shard("data", "alpha: 1\n"), store.write_shard("data", "alpha: 1\n"))[1])(s(sub("c2"))),
            False,
        ),
        Case("changed_write_returns_true", lambda s: (lambda store: (store.write_shard("data", "a\n"), store.write_shard("data", "b\n"))[1])(s(sub("c3"))), True),
        Case("invalid_name_raises", lambda s: s(sub("c4")).write_shard("../evil", "x"), ExpectRaise(InvalidRelativePathError)),
        Case("shard_path_suffix", lambda s: s(sub("c5")).shard_path("data").name, "data.yaml"),
        Case("read_missing_returns_none", lambda s: s(sub("c6")).read_shard("nope"), None),
        Case("roundtrip", lambda s: (lambda store: (store.write_shard("data", "alpha: 1\n"), store.read_shard("data"))[1])(s(sub("c7"))), "alpha: 1\n"),
    ]


SHARDS_MUTANTS: list[tuple[str, Any, Callable[[Path], list[Case]]]] = [
    ("ShardStore/MS1-always-rewrite", _MS1AlwaysRewrite, _shards_cases),
    ("ShardStore/MS2-yml-suffix", _MS2YmlSuffix, _shards_cases),
    ("ShardStore/MS3-no-validation", _MS3NoValidation, _shards_cases),
    ("ShardStore/MS4-write-reports-false", _MS4WriteReportsFalse, _shards_cases),
    ("ShardStore/MS5-read-empty-for-missing", _MS5ReadEmptyForMissing, _shards_cases),
]

ALL_MUTANTS = REFS_MUTANTS + SHARDS_MUTANTS


def test_real_implementations_pass_the_battery(tmp_path: Path) -> None:
    for case in _refs_cases(tmp_path / "refs"):
        assert not _killed(case, find_dangling_references), f"battery case {case.case_id} rejects the real implementation"
    for case in _shards_cases(tmp_path / "shards"):
        assert not _killed(case, ShardStore), f"battery case {case.case_id} rejects the real implementation"


@pytest.mark.parametrize(("mutant_id", "impl", "case_builder"), ALL_MUTANTS, ids=[m[0] for m in ALL_MUTANTS])
def test_mutant_is_killed(mutant_id: str, impl: Any, case_builder: Callable[[Path], list[Case]], tmp_path: Path) -> None:
    detections = [c.case_id for c in case_builder(tmp_path) if _killed(c, impl)]
    assert detections, f"mutant {mutant_id} SURVIVED the battery — add a test that kills it"


def test_kill_rate_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    killed = 0
    lines: list[str] = []
    for mutant_id, impl, case_builder in ALL_MUTANTS:
        detections = [c.case_id for c in case_builder(tmp_path) if _killed(c, impl)]
        if detections:
            killed += 1
            lines.append(f"{mutant_id}: KILLED by {', '.join(detections)}")
        else:
            lines.append(f"{mutant_id}: SURVIVED")
    rate = killed / len(ALL_MUTANTS) if ALL_MUTANTS else 1.0
    print("\nectt.prj mutation kill-rate report\n" + "\n".join(lines))
    print(f"kill rate: {killed}/{len(ALL_MUTANTS)} ({rate:.0%})")
    captured = capsys.readouterr()
    assert "SURVIVED" not in captured.out
    assert rate == 1.0
