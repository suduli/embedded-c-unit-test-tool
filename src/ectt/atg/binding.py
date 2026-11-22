# implements: TOOL-ATG-050, TOOL-ATG-060, DSN-ATG-110
"""The composition point of the validation port (A5).

``ectt.atg.lifecycle`` declares :class:`TestValidationPort` and the layer rule
is pinned: nothing under ``ectt.atg`` imports the builder, the runner or the
other lower layers (DSN-ATG-110). The binding therefore happens here, at
composition time, by *injection*: :class:`BoundValidationPort` takes the
build-through-``ectt.bld`` and run-through-``ectt.exh`` delegates from its
composer (the CLI/composition module — see the lane's second-pass file) and
adds what belongs to this layer:

* **coverage bookkeeping** — the constructs the injected coverage source
  reports are folded into :class:`CoverageDelta` with ``newly_covered``
  populated exactly when a construct is covered that no earlier candidate
  covered; the deltas and the covered set stay readable on the port;
* **unmeasured is explicit** — a port composed without a coverage source
  reports ``None`` and the run says ``unmeasured`` (never "uncovered").

The tests bind the real components (``ectt.bld.build_harness_suite``,
``ectt.cbt.reexecute_isolated`` over ``ectt.exh``) with a fake compile port,
because there is no C compiler on this machine — say so wherever these
results are quoted.

Satisfies: TOOL-ATG-050 (validation gate over the real components),
TOOL-ATG-060 (coverage reported through the port).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ectt.atg.lifecycle import (
    BuildOutcome,
    CoverageDelta,
    ExecutionOutcome,
    GenerationCandidate,
)

__all__ = ["BoundValidationPort"]

#: Builds one candidate through the lower layers (composition binds
#: ``ectt.bld``): the outcome is a named build failure or success.
BuildDelegate = Callable[[GenerationCandidate], BuildOutcome]

#: Executes one built candidate through the lower layers (composition binds
#: ``ectt.exh``), reporting the lifecycle's execution states.
ExecuteDelegate = Callable[[GenerationCandidate], ExecutionOutcome]

#: The constructs one candidate's run covered, as reported by the coverage
#: component the composition binds. ``None`` as the callable means the port
#: cannot measure, and says so.
CoverageSource = Callable[[GenerationCandidate], Sequence[str]] | None


class BoundValidationPort:
    """A :class:`TestValidationPort` whose build/execute are bound at composition time.

    Deterministic: no wall clock in the outcomes, no network, deltas recorded
    in measurement order. The delegates are the composition's responsibility;
    this class never imports the layers below.
    """

    def __init__(
        self,
        *,
        build: BuildDelegate,
        execute: ExecuteDelegate,
        coverage_for: CoverageSource = None,
        total_constructs: int = 0,
    ) -> None:
        if not callable(build):
            raise ValueError("build must be a callable")
        if not callable(execute):
            raise ValueError("execute must be a callable")
        if coverage_for is not None and not callable(coverage_for):
            raise ValueError("coverage_for must be a callable or None")
        if total_constructs < 0:
            raise ValueError("total_constructs must not be negative")
        self._build_delegate = build
        self._execute_delegate = execute
        self._coverage_for = coverage_for
        self._total_constructs = total_constructs
        self._covered: set[str] = set()
        self._deltas: list[CoverageDelta] = []

    # -- recorded coverage -------------------------------------------------

    @property
    def deltas(self) -> tuple[CoverageDelta, ...]:
        """The coverage deltas in measurement order (newly_covered populated)."""
        return tuple(self._deltas)

    @property
    def covered(self) -> tuple[str, ...]:
        """Every construct measured so far, sorted."""
        return tuple(sorted(self._covered))

    # -- the port protocol -------------------------------------------------

    def build(self, candidate: GenerationCandidate) -> BuildOutcome:
        """Build through the bound delegate (the harness-build step)."""
        return self._build_delegate(candidate)

    def execute(self, candidate: GenerationCandidate) -> ExecutionOutcome:
        """Execute through the bound delegate (the recorded re-execution)."""
        return self._execute_delegate(candidate)

    def measure(self, candidate: GenerationCandidate) -> CoverageDelta | None:
        """Fold the coverage source's constructs for this candidate into a delta.

        A port composed without a coverage source reports ``None``: the run
        then reports coverage as ``unmeasured`` instead of asserting an
        uncovered list (unmeasured is not uncovered).
        """
        if self._coverage_for is None:
            return None
        reported = tuple(self._coverage_for(candidate))
        before = len(self._covered)
        newly = tuple(sorted(c for c in reported if c not in self._covered))
        self._covered.update(reported)
        delta = CoverageDelta(
            covered_before=before,
            covered_after=len(self._covered),
            total=self._total_constructs,
            newly_covered=newly,
        )
        self._deltas.append(delta)
        return delta
