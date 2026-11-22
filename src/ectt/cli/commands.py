# implements: TOOL-CBT-020, TOOL-CBT-030, TOOL-CBT-050, TOOL-CBT-060, TOOL-CBT-080
"""The change-impact CLI commands (A4): impact, subset run, comparison, minimization.

Four non-interactive commands over the CBT engine operations, printed through
lane B's report views (``ectt.rep.views``) and using the stable exit-code
table (``ectt.cli.exit_codes``): a missing input is a usage error (argparse's
conventional exit 2), a refused operation maps its exception category onto the
table, a subset run with a failed test exits ``EXIT_TEST_FAILURE``.

The parser mirrors the catalogue generator's conventions (prog ``ectt``,
``--list-commands``, ``dest="operation"``) but defines the four commands' real
arguments; :func:`cbt_catalogue_extensions` publishes the matching
``ectt.api`` ``Operation`` metadata so front-ends see the same capability
list. Folding them into ``default_catalogue`` itself is an API-surface change
recorded in the lane's second-pass file.

Every handler prints one deterministic JSON document (sorted keys, fixed
indent, no wall clock) — byte-stable across runs.

Satisfies: TOOL-CBT-020, TOOL-CBT-030, TOOL-CBT-040 (the view states the
partial run), TOOL-CBT-050, TOOL-CBT-060, TOOL-CBT-080.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO

from ectt.api.catalogue import Catalogue, Operation, default_catalogue
from ectt.cbt.compare import compare_coverage, compare_runs
from ectt.cbt.diffmap import (
    DiffImpact,
    LineRange,
    SourceDiff,
    impacts_of,
)
from ectt.cbt.minimize import minimize_suite
from ectt.cbt.reexecute import load_suite_record, reexecute_subset
from ectt.cbt.reexecute import load_suite_record as _load_suite_record
from ectt.cli.exit_codes import EXIT_TEST_FAILURE, exit_code_for_category
from ectt.cli.hostprep import prepare_and_run_host_suite
from ectt.core.errors import EcttError
from ectt.cov.metrics import MetricTotals
from ectt.ext.parity import ExecutionConfig, ExecutionPlan
from ectt.ext.profile import load_host_profile
from ectt.rep.views import minimized_suite_view, run_comparison_view, subset_run_view

__all__ = [
    "COMMAND_NAMES",
    "build_cbt_parser",
    "cbt_catalogue_extensions",
    "run_cbt_commands",
]

COMMAND_NAMES: tuple[str, ...] = (
    "cbt-impact",
    "cbt-minimize-suite",
    "cbt-subset-run",
    "cbt-compare-runs",
    "host-run",
)


def _print_json(view: dict[str, Any], stdout: TextIO) -> None:
    """One deterministic JSON document: sorted keys, fixed indent."""
    print(json.dumps(view, sort_keys=True, indent=1), file=stdout)


def _load_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"input is not valid JSON: {exc}") from exc


# --- the four commands ------------------------------------------------------------------------


def run_impact_command(args: argparse.Namespace, stdout: TextIO) -> int:
    """``cbt-impact``: a source diff through the 1.5 extents to impact results."""
    diff_data = _load_json(args.diff)
    extents_data = _load_json(args.extents)
    if not isinstance(diff_data, list):
        raise ValueError("--diff must be a JSON list of {path, old_digest, new_digest, ranges}")
    if not isinstance(extents_data, dict):
        raise ValueError("--extents must be a JSON object of path -> {function: [first, last]}")
    diffs = [
        SourceDiff(
            path=str(entry["path"]),
            old_digest=str(entry.get("old_digest", "")),
            new_digest=str(entry.get("new_digest", "")),
            ranges=tuple(
                LineRange(int(first), int(last)) for first, last in entry.get("ranges", ())
            ),
        )
        for entry in diff_data
    ]
    extents_by_path = {
        str(path): {str(name): (int(first), int(last)) for name, (first, last) in functions.items()}
        for path, functions in extents_data.items()
    }
    impacts: tuple[DiffImpact, ...] = impacts_of(diffs, extents_by_path)
    _print_json({"impacts": [dataclasses.asdict(impact) for impact in impacts]}, stdout)
    return 0


def run_subset_command(args: argparse.Namespace, stdout: TextIO) -> int:
    """``cbt-subset-run``: execute the selected tests of a recorded suite."""
    record = load_suite_record(Path(args.record).read_text(encoding="utf-8"))
    root = Path(args.root)
    current = {str(k): str(v) for k, v in _load_json(args.current).items()}
    selection = [token for token in args.select.split(",") if token]
    prefix = tuple(_load_json(args.argv_prefix)) if args.argv_prefix else ()
    subset = reexecute_subset(
        record,
        root,
        current,
        subset=selection,
        run_label=args.run_label,
        timeout_seconds=args.timeout,
        argv_prefix=prefix,
    )
    _print_json(subset_run_view(subset), stdout)
    return 0 if subset.reexecution.run.outcome == "pass" else EXIT_TEST_FAILURE


def run_compare_command(args: argparse.Namespace, stdout: TextIO) -> int:
    """``cbt-compare-runs``: one run against a baseline, with coverage deltas."""
    baseline = {str(k): str(v) for k, v in _load_json(args.baseline).items()}
    current = {str(k): str(v) for k, v in _load_json(args.current).items()}
    comparison = compare_runs(baseline, current)
    coverage = None
    if args.coverage_baseline is not None and args.coverage_current is not None:
        metrics = ("statements", "branches")
        baseline_totals = {
            metric: MetricTotals(covered=int(entry["covered"]), total=entry.get("total"))
            for metric, entry in _load_json(args.coverage_baseline).items()
        }
        current_totals = {
            metric: MetricTotals(covered=int(entry["covered"]), total=entry.get("total"))
            for metric, entry in _load_json(args.coverage_current).items()
        }
        coverage = compare_coverage(baseline_totals, current_totals, metrics=metrics)
    _print_json(run_comparison_view(comparison, coverage), stdout)
    return 0


def run_minimize_command(args: argparse.Namespace, stdout: TextIO) -> int:
    """``cbt-minimize-suite``: the loss-free minimized suite and its redundant rest."""
    coverage_data = _load_json(args.coverage)
    if not isinstance(coverage_data, dict):
        raise ValueError("--coverage must be a JSON object of test id -> list of constructs")
    coverage = {str(k): tuple(str(c) for c in v) for k, v in coverage_data.items()}
    minimization = minimize_suite(coverage)
    _print_json(minimized_suite_view(minimization, coverage), stdout)
    return 0


def run_host_command(args: argparse.Namespace, stdout: TextIO) -> int:
    """``host-run``: parity-gated, profile-labelled execution of a recorded suite."""
    profile = load_host_profile(Path(args.profile).read_text(encoding="utf-8"))

    def plan(data: dict[str, Any]) -> ExecutionPlan:
        config = ExecutionConfig(
            kind=str(data["config"]["kind"]),
            toolchain=str(data["config"]["toolchain"]),
            runner=str(data["config"]["runner"]),
            transport=str(data["config"]["transport"]),
            target_id=data["config"].get("target_id"),
            settings={str(k): str(v) for k, v in data["config"].get("settings", {}).items()},
        )
        return ExecutionPlan(
            case_digests={str(k): str(v) for k, v in data["case_digests"].items()},
            generated_code_digest=str(data["generated_code_digest"]),
            config=config,
        )

    record = _load_suite_record(Path(args.record).read_text(encoding="utf-8"))
    outcome = prepare_and_run_host_suite(
        profile=profile,
        host_plan=plan(_load_json(args.host_plan)),
        target_plan=plan(_load_json(args.target_plan)),
        record=record,
        root=Path(args.root),
        current={str(k): str(v) for k, v in _load_json(args.current).items()},
        run_label=args.run_label,
        timeout_seconds=args.timeout,
        argv_prefix=tuple(_load_json(args.argv_prefix)) if args.argv_prefix else (),
    )
    _print_json(outcome.view, stdout)
    return 0 if outcome.reexecution.run.outcome == "pass" else EXIT_TEST_FAILURE


# --- the parser and the catalogue extension ---------------------------------------------------


def build_cbt_parser() -> argparse.ArgumentParser:
    """The parser for the four CBT commands, mirroring the generator's conventions."""
    parser = argparse.ArgumentParser(
        prog="ectt",
        description=(
            "Non-interactive CLI of the ectt engine. Commands are generated "
            "from the engine operation catalogue (SDD-002 §9.3, DSN-CLI-010)."
        ),
    )
    parser.add_argument(
        "--list-commands",
        action="store_true",
        help="print the catalogue operation names and exit",
    )
    subparsers = parser.add_subparsers(dest="operation", metavar="OPERATION")

    impact = subparsers.add_parser("cbt-impact", help="map a source diff to the affected constructs")
    impact.add_argument("--diff", required=True, help="JSON list of {path, old_digest, new_digest, ranges}")
    impact.add_argument("--extents", required=True, help="JSON object of path -> {function: [first, last]}")

    subset = subparsers.add_parser("cbt-subset-run", help="execute the selected tests of a recorded suite")
    subset.add_argument("--record", required=True, help="path to the stored suite record JSON")
    subset.add_argument("--root", required=True, help="project root the record was written against")
    subset.add_argument("--current", required=True, help="JSON object of test id -> current content digest")
    subset.add_argument("--select", required=True, help="comma-separated test ids to execute")
    subset.add_argument("--run-label", required=True, help="single-token label naming this re-execution")
    subset.add_argument("--timeout", type=float, default=30.0, help="per-test timeout in seconds")
    subset.add_argument("--argv-prefix", help="JSON list prepended to the executable (interpreter stubs)")

    compare = subparsers.add_parser("cbt-compare-runs", help="compare a run against a baseline")
    compare.add_argument("--baseline", required=True, help="JSON object of test id -> outcome")
    compare.add_argument("--current", required=True, help="JSON object of test id -> outcome")
    compare.add_argument("--coverage-baseline", help="JSON metric -> {covered, total} for the baseline")
    compare.add_argument("--coverage-current", help="JSON metric -> {covered, total} for the current run")

    minimize = subparsers.add_parser("cbt-minimize-suite", help="the loss-free minimized suite")
    minimize.add_argument("--coverage", required=True, help="JSON object of test id -> list of constructs")

    host = subparsers.add_parser("host-run", help="parity-gated, profile-labelled execution of a recorded suite")
    host.add_argument("--profile", required=True, help="path to the stored host profile JSON")
    host.add_argument("--host-plan", required=True, help="JSON: {case_digests, generated_code_digest, config}")
    host.add_argument("--target-plan", required=True, help="JSON: {case_digests, generated_code_digest, config}")
    host.add_argument("--record", required=True, help="path to the stored suite record JSON")
    host.add_argument("--root", required=True, help="project root the record was written against")
    host.add_argument("--current", required=True, help="JSON object of test id -> current content digest")
    host.add_argument("--run-label", required=True, help="single-token label naming this re-execution")
    host.add_argument("--timeout", type=float, default=30.0, help="per-test timeout in seconds")
    host.add_argument("--argv-prefix", help="JSON list prepended to the executable (interpreter stubs)")
    return parser


def cbt_catalogue_extensions(catalogue: Catalogue | None = None) -> Catalogue:
    """The catalogue with the four commands' ``Operation`` metadata added.

    A fresh catalogue carrying ``default_catalogue``'s operations plus the
    four CBT commands, so front-ends see one capability list. Folding the
    operations into ``default_catalogue`` itself is an API-surface change
    (recorded in the lane's second-pass file), not this command module's.
    """
    merged = Catalogue()
    for name in (catalogue or default_catalogue()).names():
        merged.register((catalogue or default_catalogue()).get(name))
    for name, summary in (
        ("cbt-impact", "map a source diff to the affected constructs"),
        ("cbt-minimize-suite", "the loss-free minimized suite"),
        ("cbt-subset-run", "execute the selected tests of a recorded suite"),
        ("cbt-compare-runs", "compare a run against a baseline"),
        ("host-run", "parity-gated, profile-labelled execution of a recorded suite"),
    ):
        merged.register(Operation(name=name, summary=summary, cli_equivalent=f"ectt {name}"))
    return merged


_HANDLERS = {
    "cbt-impact": run_impact_command,
    "cbt-minimize-suite": run_minimize_command,
    "cbt-subset-run": run_subset_command,
    "cbt-compare-runs": run_compare_command,
    "host-run": run_host_command,
}


def run_cbt_commands(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Parse and run one CBT command; stable exit codes, deterministic output.

    Usage errors (missing or malformed input) exit with argparse's
    conventional usage code; refused operations map their exception category
    onto the documented table (TOOL-CIC-030) and never fake success.
    """
    out = stdout if stdout is not None else sys.stdout
    err = stderr if stderr is not None else sys.stderr
    parser = build_cbt_parser()
    try:
        namespace = parser.parse_args(list(argv) if argv is not None else None)
    except SystemExit as exc:
        return int(exc.code or 0)
    if namespace.operation is None:
        parser.print_usage(file=err)
        return 2
    handler = _HANDLERS.get(namespace.operation)
    if handler is None:
        print(f"ectt: error: no executor for operation: {namespace.operation}", file=err)
        return exit_code_for_category("api")
    try:
        return handler(namespace, out)
    except EcttError as exc:
        print(f"ectt: error: {exc}", file=err)
        return exit_code_for_category(exc.category)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ectt: error: {exc}", file=err)
        return exit_code_for_category("api")
