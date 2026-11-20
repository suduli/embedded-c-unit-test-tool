"""Hand-written mutation run for ``ectt.rep`` and ``ectt.trc`` (TEST-MUT2).

Each mutant is one seeded fault (a flipped comparison, a dropped branch, a swapped
ordering) applied to a **temporary copy** of ``src``; the repository's own files are
never touched. The existing tests for the two packages run against the copy
(``-o pythonpath`` points at it). A mutant is *killed* when those tests fail (or
hang past the timeout), *survived* when they all pass.

    python docs/glm-night/overnight-20261120/mutation_rep_trc.py \
        --out docs/glm-night/overnight-20261120/mutation-rep-trc.md [--initial first_run.json]

A sanity mutant (an import-time error in ``ectt.trc``) proves the run really uses the
copy; if it survives, the run aborts.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEST_TARGETS = ["tests/rep", "tests/trc", "tests/cli/test_sharding.py"]
TIMEOUT_S = 120


@dataclass(frozen=True)
class Mutant:
    mutant_id: str
    path: str  # relative to src/
    old: str
    new: str
    description: str


M = Mutant
MUTANTS: tuple[Mutant, ...] = (
    # ---- trc.matrix ----
    M("M01", "ectt/trc/matrix.py", 'return "failed" if worst.status in ("fail", "error", "timeout") else "pass"', 'return "failed" if worst.status in ("fail", "error") else "pass"', "timeout no longer fails a requirement"),
    M("M02", "ectt/trc/matrix.py", "link.status in _EXECUTED and not link.unreviewed]", "link.status in _EXECUTED]", "unreviewed tests count toward verdicts"),
    M("M03", "ectt/trc/matrix.py", 'return "unverified"  # nothing executed', 'return "pass"  # nothing executed', "no executed test reads as pass"),
    M("M04", "ectt/trc/matrix.py", "worst = max(executed,", "worst = min(executed,", "best outcome instead of worst"),
    M("M05", "ectt/trc/matrix.py", '_EXECUTED = ("pass", "fail", "error", "timeout")', '_EXECUTED = ("pass", "fail", "error")', "timeout is not an executed outcome"),
    M("M06", "ectt/trc/matrix.py", 'status = statuses.get(test_id, "not_run")', 'status = statuses.get(test_id, "pass")', "unknown test defaults to pass"),
    M("M07", "ectt/trc/matrix.py", '"value": round(100.0 * verdicts[verdict] / total, 1) if total else 0.0,', '"value": round(100.0 * verdicts[verdict] / total, 0) if total else 0.0,', "percentage rounded to whole numbers"),
    M("M08", "ectt/trc/matrix.py", "pair_count=associations.pair_count)", "pair_count=len(rows))", "pair count taken from row count"),
    M("M09", "ectt/trc/matrix.py", "universe = set(requirement_universe) if requirement_universe is not None else set(associations.requirements())", "universe = set(associations.requirements())", "requirement universe ignored"),
    M("M10", "ectt/trc/matrix.py", "reverse.setdefault(link.test_id, []).append(row.requirement_id)", "reverse.setdefault(link.test_id, []).append(link.test_id)", "reverse view lists tests, not requirements"),
    M("M11", "ectt/trc/matrix.py", "if status not in TEST_SEVERITY:", "if status in TEST_SEVERITY:", "status vocabulary check inverted"),
    # ---- trc.associations / unlinked ----
    M("M12", "ectt/trc/associations.py", "return len(self._pairs)", "return len(self._pairs) + 1", "pair count off by one"),
    M("M13", "ectt/trc/associations.py", "if pair.requirement_id == requirement_id", "if pair.requirement_id != requirement_id", "tests_for selects the wrong pairs"),
    M("M14", "ectt/trc/associations.py", "if pair.test_id == test_id", "if pair.test_id != test_id", "requirements_for selects the wrong pairs"),
    M("M15", "ectt/trc/unlinked.py", "if req not in linked_requirements", "if req in linked_requirements", "unlinked requirements inverted"),
    M("M16", "ectt/trc/unlinked.py", "linked_tests = {pair.test_id for pair in associations.pairs}", "linked_tests = {pair.requirement_id for pair in associations.pairs}", "linked tests built from requirement ids"),
    # ---- trc.imports ----
    M("M17", "ectt/trc/imports.py", 'if "id" not in names:', 'if "id" in names:', "id column check inverted"),
    M("M18", "ectt/trc/imports.py", "if len(names) != len(set(names)):", "if len(names) == len(set(names)):", "duplicate column check inverted"),
    M("M19", "ectt/trc/imports.py", "unknown = [name for name in names if name not in CSV_COLUMNS]", "unknown = [name for name in names if name in CSV_COLUMNS]", "unknown column check inverted"),
    M("M20", "ectt/trc/imports.py", "enumerate(reader, start=2)", "enumerate(reader, start=1)", "CSV row numbers off by one"),
    M("M21", "ectt/trc/imports.py", "if record.requirement_id in seen:", "if record.requirement_id not in seen:", "duplicate requirement check inverted"),
    M("M22", "ectt/trc/imports.py", 'if not line or line.startswith("#"):', "if not line:", "plain-text comments not skipped"),
    M("M23", "ectt/trc/imports.py", 'title=(row.get("title") or "").strip(),', 'title=(row.get("title") or ""),', "CSV title not stripped"),
    M("M24", "ectt/trc/imports.py", 'title=match.group("rest").strip(),', 'title=match.group("rest"),', "plain-text title not stripped"),
    # ---- trc.change_detection ----
    M("M25", "ectt/trc/change_detection.py", r'return text.replace("\r\n", "\n").replace("\r", "\n")', r'return text.replace("\r\n", "\n")', "lone CR not normalised"),
    M("M26", "ectt/trc/change_detection.py", "baseline.digests[rid] != requirement_digest(rec)", "baseline.digests[rid] == requirement_digest(rec)", "changed detection inverted"),
    M("M27", "ectt/trc/change_detection.py", "new = sorted(rid for rid in current if rid not in baseline.digests)", "new = sorted(rid for rid in current if rid in baseline.digests)", "new detection inverted"),
    M("M28", "ectt/trc/change_detection.py", "unchanged = len(current) - len(changed) - len(new)", "unchanged = len(current) - len(changed)", "new requirements counted as unchanged"),
    M("M29", "ectt/trc/change_detection.py", '("changed", changed), ("removed", removed), ("new", new)', '("changed", changed), ("new", new)', "removed requirements flag no tests"),
    M("M30", "ectt/trc/change_detection.py", "if rid not in current:", "if rid in current:", "mark_reviewed unknown check inverted"),
    # ---- trc.source_links ----
    M("M31", "ectt/trc/source_links.py", "if later and end >= later[0].location.line:", "if later and end > later[0].location.line:", "range ending at next function start allowed"),
    M("M32", "ectt/trc/source_links.py", "if f.location.line <= start]", "if f.location.line < start]", "range starting at a function line misses it"),
    M("M33", "ectt/trc/source_links.py", 'if unit.status != "parsed":', 'if unit.status == "parsed":', "parsed check inverted"),
    M("M34", "ectt/trc/source_links.py", "if len(matches) > 1:", "if len(matches) > 2:", "two same-named functions not ambiguous"),
    M("M35", "ectt/trc/source_links.py", "if _normalise(f.location.file) == own", "if _normalise(f.location.file) != own", "functions of other files attributed to the unit"),
    M("M36", "ectt/trc/source_links.py", "start < 1 or end < start", "start < 1 or end <= start", "single-line range refused"),
    # ---- trc.reqif_export ----
    M("M37", "ectt/trc/reqif_export.py", "if len(value) > _MAX_LENGTH:", "if len(value) >= _MAX_LENGTH:", "value of exactly the maximum length refused"),
    M("M38", "ectt/trc/reqif_export.py", 'if "T" not in value:', 'if "T" in value:', "date-only time check inverted"),
    M("M39", "ectt/trc/reqif_export.py", '"true" if unreviewed else "false"', '"false" if unreviewed else "true"', "unreviewed flag inverted"),
    # ---- rep.model ----
    M("M40", "ectt/rep/model.py", "if version not in SUPPORTED_FORMAT_VERSIONS:", "if version in SUPPORTED_FORMAT_VERSIONS:", "version check inverted"),
    M("M41", "ectt/rep/model.py", "if recomputed != stored_report_id:", "if recomputed == stored_report_id:", "digest check inverted"),
    M("M42", "ectt/rep/model.py", "if entry.test_id in seen_tests:", "if entry.test_id not in seen_tests:", "duplicate test check inverted"),
    M("M43", "ectt/rep/model.py", "if cov_entry.unit in seen_units:", "if cov_entry.unit not in seen_units:", "duplicate coverage check inverted"),
    M("M44", "ectt/rep/model.py", "if covered < 0 or total < 0 or covered > total:", "if covered < 0 or total < 0 or covered >= total:", "full coverage refused"),
    M("M45", "ectt/rep/model.py", 'if status != "not_run" and not digest:', 'if status == "not_run" and not digest:', "digest rule inverted"),
    M("M46", "ectt/rep/model.py", 'generated = self.provenance.generated_at or "unknown"', 'generated = self.provenance.generated_at or ""', "missing execution time not shown as unknown"),
    M("M47", "ectt/rep/model.py", '"target": self.execution.target_id or "none",', '"target": self.execution.target_id or "",', "missing target not shown as none"),
    M("M48", "ectt/rep/model.py", "if not isinstance(partial, bool):", "if isinstance(partial, bool):", "partial type check inverted"),
    # ---- rep.summary ----
    M("M49", "ectt/rep/summary.py", "if model.run_id in seen:", "if model.run_id not in seen:", "duplicate run check inverted"),
    M("M50", "ectt/rep/summary.py", 'if target == "none":', 'if target != "none":', "none target not mapped to absent"),
    M("M51", "ectt/rep/summary.py", "key=lambda m: (m.generated_at, m.run_id))", "key=lambda m: (m.run_id, m.generated_at))", "trend ordered by run id first"),
    M("M52", "ectt/rep/summary.py", "for model in sorted(checked, key=lambda m: m.run_id):", "for model in sorted(checked, key=lambda m: m.run_id, reverse=True):", "summary runs in reverse order"),
    M("M53", "ectt/rep/summary.py", "total = sum(pair[1] for pair in figures.values())", "total = sum(pair[0] for pair in figures.values())", "trend total uses covered"),
    M("M54", "ectt/rep/summary.py", "counts[status] = counts.get(status, 0) + 1", "counts[status] = counts.get(status, 0) + 2", "status counts doubled"),
    M("M55", "ectt/rep/summary.py", "tests_total=sum(run.tests for run in runs),", "tests_total=len(runs),", "tests total is the run count"),
    # ---- rep.formats / render / open_export / from_archive ----
    M("M56", "ectt/rep/formats.py", "if name in self._formats:", "if name not in self._formats:", "duplicate format check inverted"),
    M("M57", "ectt/rep/formats.py", " or any(char.isspace() for char in name)", "", "format names may contain whitespace"),
    M("M58", "ectt/rep/formats.py", "return tuple(sorted(self._formats))", "return tuple(self._formats)", "format names in registration order"),
    M("M59", "ectt/rep/render.py", "f\"partial: {'yes' if model.partial else 'no'}\"", "f\"partial: {'no' if model.partial else 'yes'}\"", "partial flag inverted in text"),
    M("M60", "ectt/rep/render.py", 'lines.append(f"coverage: {len(figures)} units")', 'lines.append(f"coverage: {len(statuses)} units")', "coverage unit count wrong in text"),
    M("M61", "ectt/rep/open_export.py", 'if provenance.digest != raw_provenance["digest"]:', 'if provenance.digest == raw_provenance["digest"]:', "provenance digest check inverted"),
    M("M62", "ectt/rep/open_export.py", 'if recomputed != doc["export_id"]:', 'if recomputed == doc["export_id"]:', "export id check inverted"),
    M("M63", "ectt/rep/open_export.py", 'if doc.get("schema_version") != OPEN_EXPORT_SCHEMA_VERSION:', 'if doc.get("schema_version") == OPEN_EXPORT_SCHEMA_VERSION:', "export version check inverted"),
    M("M64", "ectt/rep/from_archive.py", 'if doc.get("result_set") is None:', 'if doc.get("result_set") is not None:', "missing result set check inverted"),
    M("M65", "ectt/rep/from_archive.py", 'partial=bool(doc.get("partial", False)),', "partial=False,", "archived partial flag dropped"),
    M("M66", "ectt/rep/from_archive.py", "or not isinstance(toolchain, str) or not toolchain:", "or not isinstance(toolchain, str):", "empty toolchain accepted"),
)

#: Mutants no test can kill because the mutated program behaves identically.
EQUIVALENT: dict[str, str] = {
    "M24": "the caller already strips the whole line and the regex consumes the blanks after the colon, so rest.strip() is a no-op",
}

SANITY = Mutant("S00", "ectt/trc/__init__.py", "from ectt.trc.associations import", "raise RuntimeError('sanity')\nfrom ectt.trc.associations import", "import-time error proves the copy is used")


def _run_tests(copy_src: Path) -> tuple[bool, str]:
    """Return (all tests passed, first failing test or a note)."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    # pytest splits this option like a shell would, which eats Windows backslashes: pass forward slashes.
    command = [
        sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider",
        "-o", f"pythonpath={copy_src.as_posix()}", *TEST_TARGETS,
    ]
    try:
        done = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_S, check=False)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if done.returncode == 0:
        return True, ""
    failed = next((line for line in done.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))), "")
    return False, failed.split(" - ")[0].replace("FAILED ", "").replace("ERROR ", "") or "collection or import error"


def _apply(copy_src: Path, mutant: Mutant) -> str:
    target = copy_src / mutant.path
    original = target.read_text(encoding="utf-8")
    occurrences = original.count(mutant.old)
    if occurrences != 1:
        raise SystemExit(f"{mutant.mutant_id}: snippet occurs {occurrences} times in {mutant.path}; mutant is not applicable")
    target.write_text(original.replace(mutant.old, mutant.new, 1), encoding="utf-8")
    return original


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Markdown report path")
    parser.add_argument("--json", help="write raw results here")
    parser.add_argument("--initial", help="JSON from the first run, shown as the before column")
    parser.add_argument("--only", nargs="*", help="run only these mutant ids")
    args = parser.parse_args()

    selected = [m for m in MUTANTS if not args.only or m.mutant_id in args.only]
    results: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory(prefix="ectt-mut-") as tmp:
        copy_src = Path(tmp) / "src"
        shutil.copytree(ROOT / "src", copy_src, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        original = _apply(copy_src, SANITY)
        passed, _ = _run_tests(copy_src)
        (copy_src / SANITY.path).write_text(original, encoding="utf-8")
        if passed:
            print("sanity mutant survived: the run is not using the copy; aborting", file=sys.stderr)
            return 2
        clean, note = _run_tests(copy_src)
        if not clean:
            print(f"unmutated copy fails its own tests ({note}); aborting", file=sys.stderr)
            return 2

        for mutant in selected:
            original = _apply(copy_src, mutant)
            passed, note = _run_tests(copy_src)
            (copy_src / mutant.path).write_text(original, encoding="utf-8")
            results[mutant.mutant_id] = {"state": "SURVIVED" if passed else "KILLED", "by": note}
            print(f"{mutant.mutant_id} {results[mutant.mutant_id]['state']:8} {mutant.description} {note}", flush=True)

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    initial = json.loads(Path(args.initial).read_text(encoding="utf-8")) if args.initial else None
    Path(args.out).write_text(_report(selected, results, initial), encoding="utf-8")
    return 0


def _report(selected: list[Mutant], results: dict[str, dict[str, str]], initial: dict[str, dict[str, str]] | None) -> str:
    killed = sum(1 for r in results.values() if r["state"] == "KILLED")
    total = len(results)
    equivalent = [m for m in EQUIVALENT if m in results and results[m]["state"] == "SURVIVED"]
    countable = total - len(equivalent)
    lines = [
        "# Mutation-style strengthening: ectt.rep and ectt.trc (TEST-MUT2)",
        "",
        "Hand-written mutants (a flipped comparison, a dropped branch, a swapped ordering), each applied to a",
        "temporary copy of `src/` and run against the existing tests of `tests/rep`, `tests/trc` and",
        "`tests/cli/test_sharding.py`. No file under `src/` was edited. Runner:",
        "`docs/glm-night/overnight-20261120/mutation_rep_trc.py`. A sanity mutant (an import-time error) proves each",
        "run uses the copy, and the unmutated copy must pass first.",
        "",
        f"**Final kill rate: {killed}/{total} ({100.0 * killed / total:.1f}%); "
        f"{killed}/{countable} ({100.0 * killed / countable:.1f}%) excluding {len(equivalent)} equivalent mutant(s).**"
        if total
        else "No mutants run.",
    ]
    if initial is not None:
        before = sum(1 for m in selected if initial.get(m.mutant_id, {}).get("state") == "KILLED")
        lines += [f"**Before the new tests: {before}/{total} ({100.0 * before / total:.1f}%).**" if total else ""]
    lines += ["", "| Mutant | File | Seeded fault | Before | After | Killed by |", "|---|---|---|---|---|---|"]
    for m in selected:
        after = results[m.mutant_id]
        before_state = initial[m.mutant_id]["state"] if initial and m.mutant_id in initial else "-"
        note = f"equivalent: {EQUIVALENT[m.mutant_id]}" if m.mutant_id in EQUIVALENT and after["state"] == "SURVIVED" else (after["by"] or "-")
        lines.append(f"| {m.mutant_id} | `{m.path}` | {m.description} | {before_state} | {after['state']} | {note} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
