"""Long-running pipeline operation routed through OutputRoot.transaction (WP-CORE-02).

Implements: TOOL-NFR-180 — a cancelled or failed run leaves no partial
output. The existing multi-write fixture pipeline is the operation under
test: four artifacts written through one OutputRoot inside a single
transaction scope.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ectt.core.errors import CancellationToken, CancelledError
from ectt.core.fs import GITIGNORE_FILENAME, MARKER_FILENAME, OutputRoot
from tests.core.fixture_pipeline import run_pipeline

ARTIFACTS = (
    "models/analysis_model.json",
    "tests/generated_tests.json",
    "generated/stubs.c",
    "reports/summary.txt",
)


def _write_source_tree(source_dir: Path) -> None:
    source_dir.mkdir(parents=True)
    (source_dir / "adc.h").write_text(
        "#ifndef ADC_H\n"
        "#define ADC_H\n"
        "\n"
        "uint16_t adc_read_channel(uint8_t channel);\n"
        "\n"
        "#endif\n",
        encoding="utf-8",
    )
    (source_dir / "adc.c").write_text(
        '#include "adc.h"\n'
        "\n"
        "uint16_t adc_read_channel(uint8_t channel) {\n"
        "    return 0;\n"
        "}\n",
        encoding="utf-8",
    )


def _assert_only_setup_files(root: Path) -> None:
    """Rollback must leave exactly the root-setup files, no partial output."""
    remaining = sorted(
        p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
    )
    assert remaining == sorted([MARKER_FILENAME, GITIGNORE_FILENAME])


def _make_paths(tmp_path: Path) -> tuple[Path, Path]:
    source_dir = tmp_path / "source"
    _write_source_tree(source_dir)
    return source_dir, tmp_path / "out"


def test_pipeline_completes_inside_transaction(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180 — the scoped happy path writes every artifact."""
    source_dir, out = _make_paths(tmp_path)
    token = CancellationToken()

    manifest = run_pipeline(source_dir, out, token=token)

    for rel in ARTIFACTS:
        assert (out / rel).is_file()
    assert manifest, "manifest must be returned after the scope commits"


def test_cancelled_before_start_leaves_no_artifacts(tmp_path: Path) -> None:
    """verifies: TOOL-NFR-180 — a pre-cancelled token refuses to write."""
    source_dir, out = _make_paths(tmp_path)
    token = CancellationToken()
    token.cancel()

    with pytest.raises(CancelledError):
        run_pipeline(source_dir, out, token=token)

    _assert_only_setup_files(out)


def test_cancelled_midway_rolls_back_completed_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-180 — cancellation at a write boundary undoes the scope."""
    source_dir, out = _make_paths(tmp_path)
    token = CancellationToken()
    original = OutputRoot.write_json
    completed = {"count": 0}

    def cancel_after_first(self: OutputRoot, rel_path: Path | str, data: bytes) -> Path:
        result = original(self, rel_path, data)
        completed["count"] += 1
        token.cancel()
        return result

    monkeypatch.setattr(OutputRoot, "write_json", cancel_after_first)

    with pytest.raises(CancelledError):
        run_pipeline(source_dir, out, token=token)

    assert completed["count"] == 1  # first write committed, second refused
    _assert_only_setup_files(out)


def test_injected_failure_rolls_back_completed_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """verifies: TOOL-NFR-180 — an injected failure undoes earlier writes."""
    source_dir, out = _make_paths(tmp_path)
    original = OutputRoot.write_text
    calls = {"count": 0}

    def fail_on_second(
        self: OutputRoot, rel_path: Path | str, text: str, *args: object, **kwargs: object
    ) -> Path:
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("injected failure")
        return original(self, rel_path, text)  # type: ignore[arg-type]

    monkeypatch.setattr(OutputRoot, "write_text", fail_on_second)

    with pytest.raises(RuntimeError, match="injected failure"):
        run_pipeline(source_dir, out)

    assert calls["count"] == 2  # stubs.c committed, summary.txt refused
    _assert_only_setup_files(out)
