# implements: DSN-CORE-060
"""Hand-written mutation battery for OutputRoot.resolve_path confinement (B8).

No product code is changed. The mutants are hand-written copies of the
path-confinement discipline (fs.OutputRoot.resolve_path) with a single
seeded fault each, executed in isolation. The real implementation is the
oracle: every case the real code refuses must also be refused by every
mutant for the same named reason — a mutant that lets a case through is
killed by the difference.

Note on the queue's "temp copy" wording: the mutants are hand-written copies
executed in isolation and never touch the product module (repo-established
mutation-battery pattern, TASK-107).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ectt.core.fs import OutputRoot, PathConfinementError


def _real_resolve(root: Path, rel_path: str) -> Path:
    return OutputRoot(root, source_roots=[]).resolve_path(rel_path)


def _copy_resolve(root: Path, rel_path: str, *, drop_absolute: bool, drop_root_target: bool) -> Path:
    """Hand-written copy of the confinement discipline with one seeded fault."""
    p = Path(rel_path)
    if not drop_absolute and p.is_absolute():
        raise PathConfinementError("absolute", reason="absolute_path", path=p)
    candidate = root / p
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise PathConfinementError("escape", reason="path_escape", path=p)
    if not drop_root_target and resolved == root:
        raise PathConfinementError("root target", reason="root_target", path=p)
    return resolved


@pytest.mark.parametrize(
    "rel_path, expected_reason",
    [
        ("a/b/c.txt", None),
        ("a/../../x", "path_escape"),
        (".", "root_target"),
    ],
    ids=["relative_ok", "dot_dot_escape", "root_target_forbidden"],
)
def test_real_confinement_discipline(tmp_path: Path, rel_path: str, expected_reason: str | None) -> None:
    root = tmp_path / "out"
    root.mkdir()
    if expected_reason is None:
        resolved = _real_resolve(root, rel_path)
        assert resolved.is_relative_to(root)
    else:
        with pytest.raises(PathConfinementError) as exc_info:
            _real_resolve(root, rel_path)
        assert exc_info.value.reason == expected_reason


@pytest.mark.parametrize(
    "rel_path",
    ["/etc/passwd", "C:/Windows/x"],
    ids=["rooted_path", "drive_letter"],
)
def test_real_confinement_refuses_all_platform_absolute_forms(tmp_path: Path, rel_path: str) -> None:
    """Every non-relative form is refused under a named rule (the exact rule is
    platform-ordered: absolute_path where the form is absolute, else path_escape)."""
    root = tmp_path / "out"
    root.mkdir()
    with pytest.raises(PathConfinementError):
        _real_resolve(root, rel_path)


def test_mutant_dropping_absolute_check_is_killed(tmp_path: Path) -> None:
    """An absolute path landing INSIDE the root is refused only by the
    absolute_path rule; a mutant without it lets the case through."""
    root = tmp_path / "out"
    root.mkdir()
    inside_absolute = str(root / "inside.txt")
    with pytest.raises(PathConfinementError) as exc_info:
        _real_resolve(root, inside_absolute)
    assert exc_info.value.reason == "absolute_path"
    # the mutant resolves the same path happily — that difference is the kill
    escaped = _copy_resolve(root, inside_absolute, drop_absolute=True, drop_root_target=False)
    assert escaped == (root / "inside.txt").resolve()


def test_mutant_dropping_root_target_check_is_killed(tmp_path: Path) -> None:
    root = tmp_path / "out"
    root.mkdir()
    with pytest.raises(PathConfinementError) as exc_info:
        _real_resolve(root, ".")
    assert exc_info.value.reason == "root_target"
    assert _copy_resolve(root, ".", drop_absolute=False, drop_root_target=True) == root.resolve()


def test_fs_kill_rate_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A mutant is killed when its outcome differs from the real implementation
    on the same probe (real refuses, mutant resolves — or vice versa)."""
    root = tmp_path / "out"
    root.mkdir()
    inside_absolute = str(root / "inside.txt")
    probes = (inside_absolute, ".")

    def outcome(resolve: Any, probe: str) -> str:
        try:
            return f"resolved:{resolve(root, probe)}"
        except PathConfinementError as exc:
            return f"refused:{exc.reason}"

    killed = 0
    total = 2
    mutants = (
        ("fs-m1-absolute-check-dropped", {"drop_absolute": True, "drop_root_target": False}),
        ("fs-m2-root-target-check-dropped", {"drop_absolute": False, "drop_root_target": True}),
    )
    for name, kwargs in mutants:
        differing = [
            probe
            for probe in probes
            if outcome(_real_resolve, probe) != outcome(lambda r, p, kw=kwargs: _copy_resolve(r, p, **kw), probe)
        ]
        survived = not differing
        print(f"  {name}: {'killed by ' + str(differing) if not survived else 'SURVIVED'}")
        if not survived:
            killed += 1
    print(f"core/fs confinement kill rate: {killed}/{total}")
    assert killed == total
