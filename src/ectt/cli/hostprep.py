# implements: TOOL-TGT-130
"""The host run preparation: parity gate first, profile-labelled results (A5).

Wires the host profile (``ectt.ext``) into the CLI run preparation:

1. **check_parity runs first** — the host and target plans must describe the
   same cases and the same generated code (only the configuration may differ);
   a refusal raises ``ParityGateError`` with its named reasons and **nothing
   runs** — no process is started on a refused preparation.
2. **every host-executed result is labelled** with the governing profile
   (``label_host_results``) and printed through lane B's
   ``host_profile_view``; the profile's ABI differences ride beside the view,
   with an unmeasured dimension shown as ``unknown`` — never a guess.

Hardware is not available to this machine, so no target run happens here: the
target plan is a declaration the parity gate compares against, and the host
execution re-runs a recorded suite (a caller-supplied ``argv_prefix`` hosts it
on an interpreter in tests).

Satisfies: TOOL-TGT-130 (run preparation wiring).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ectt.cbt.reexecute import CompiledSuiteRecord, ReExecution, reexecute_isolated
from ectt.ext.parity import prepare_host_proxy_run
from ectt.ext.profile import (
    ABI_DIMENSIONS,
    UNKNOWN_ABI,
    HostProfile,
    LabelledResults,
    abi_difference,
    label_host_results,
)
from ectt.rep.views import host_profile_view

__all__ = ["HostRunOutcome", "prepare_and_run_host_suite"]


@dataclass(frozen=True)
class HostRunOutcome:
    """One gated, executed, labelled host run and everything reports need."""

    #: The preparation the parity gate returned (carries the report).
    preparation: Any
    #: The executed run of the recorded suite.
    reexecution: ReExecution
    #: The profile-labelled result set (one label per result).
    labelled: LabelledResults
    #: The deterministic report document (host_profile_view + the ABI map).
    view: dict[str, Any]


def profile_abi_map(profile: HostProfile) -> dict[str, str]:
    """Every measurable ABI dimension with its value — or ``unknown``.

    A dimension the profile never measured is reported as the explicit
    ``unknown`` marker (TOOL-TGT-130), so a report can never read a gap as
    "same".
    """
    return {
        dimension: (value if measured else UNKNOWN_ABI)
        for dimension in ABI_DIMENSIONS
        for value, measured in (abi_difference(profile, dimension),)
    }


def prepare_and_run_host_suite(
    *,
    profile: HostProfile,
    host_plan: Any,
    target_plan: Any,
    record: CompiledSuiteRecord,
    root: Path | str,
    current: Mapping[str, str],
    run_label: str,
    timeout_seconds: float = 30.0,
    argv_prefix: Sequence[str] = (),
) -> HostRunOutcome:
    """Prepare (parity-gated), execute, and label one host run.

    The parity gate runs before anything else; a refusal propagates with its
    named reasons and no process is started. On success the recorded suite is
    re-executed (no regeneration, binary integrity, per-test isolation), every
    result is labelled with the governing profile, and the view is assembled
    deterministically: lane B's ``host_profile_view`` plus the profile's ABI
    map (unmeasured dimensions as ``unknown``) and the parity report's
    configuration differences.
    """
    preparation = prepare_host_proxy_run(profile, host_plan, target_plan)
    rexec = reexecute_isolated(
        record,
        root,
        current,
        run_label=run_label,
        timeout_seconds=timeout_seconds,
        argv_prefix=argv_prefix,
    )
    labelled = label_host_results(profile, rexec.run.result_set)
    view = host_profile_view(labelled)
    view = {
        **view,
        "abi": profile_abi_map(profile),
        "config_differences": list(preparation.parity.config_differences),
        "outcome": rexec.run.outcome,
    }
    return HostRunOutcome(
        preparation=preparation,
        reexecution=rexec,
        labelled=labelled,
        view=view,
    )
