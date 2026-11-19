"""Cross-compiled target build planning (WP-BLD-03).

Composes the exact cross-compile command lines for harness artifacts from a
cross compiler configuration (WP-TCH-03 roster), gating coverage kinds through
the WP-TCH-04 metric gate and reusing the WP-BLD-01 staleness planner.

Satisfies: TOOL-TGT-010.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

from ectt.bld.plan import ArtifactSpec, IncrementalPlanner
from ectt.tch.config import CompilerConfig

__all__ = [
    "CrossBuildCommand",
    "CrossBuildPlan",
    "plan_cross_build",
]


@dataclass(frozen=True)
class CrossBuildCommand:
    """One composed cross-compile command."""

    output_path: str
    command_line: str

    def to_dict(self) -> dict[str, str]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {"command_line": self.command_line, "output_path": self.output_path}


@dataclass(frozen=True)
class CrossBuildPlan:
    """The full cross-build plan for one toolchain."""

    toolchain: str
    commands: tuple[CrossBuildCommand, ...]

    def to_dict(self) -> dict[str, object]:
        """Canonical, JSON-safe mapping (deterministic key order)."""
        return {
            "commands": [command.to_dict() for command in self.commands],
            "toolchain": self.toolchain,
        }


def plan_cross_build(
    specs: tuple[ArtifactSpec, ...],
    config: CompilerConfig,
    *,
    build_root: str = "build",
    coverage_kinds: tuple[str, ...] = (),
    planner: IncrementalPlanner | None = None,
) -> CrossBuildPlan:
    """Plan the cross-compile commands for the requested artifacts.

    Commands compose deterministically from the configuration: executable,
    debug flags, coverage flags of the requested kinds (refused when the
    configuration does not declare them), compile-only and output flags, and
    the source path. Artifacts that the WP-BLD-01 planner marks up to date are
    not re-planned.
    """
    from ectt.tch.gating import gate_metrics

    gate = gate_metrics(config, coverage_kinds) if coverage_kinds else None
    coverage_flags: tuple[str, ...] = ()
    if gate is not None:
        coverage_flags = tuple(
            flag
            for kind in gate.granted
            for flag in config.coverage_flags.get(kind, ())
        )

    if planner is not None:
        specs = tuple(
            decision.spec for decision in planner.plan(specs) if decision.rebuild
        )
    commands: list[CrossBuildCommand] = []
    for spec in sorted(specs, key=lambda item: item.output_path):
        output = str(PurePosixPath(build_root) / spec.output_path)
        tokens: list[str] = [config.invocation.executable]
        tokens.extend(config.debug_flags)
        tokens.extend(coverage_flags)
        tokens.append(config.invocation.compile_only_flag)
        tokens.extend(config.optimization_flags.get("none", ()))
        tokens.append(config.invocation.output_flag)
        tokens.append(output)
        tokens.append(spec.source_path)
        commands.append(
            CrossBuildCommand(
                output_path=output,
                command_line=" ".join(tokens),
            )
        )
    return CrossBuildPlan(toolchain=config.name, commands=tuple(commands))
