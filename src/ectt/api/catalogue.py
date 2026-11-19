"""Operation catalogue for the ectt engine API (WP-API-01).

One catalogue is the single capability surface (SDD-002 §9.3): the CLI is
generated from the same catalogue the API publishes (DSN-CLI-010), so a
capability cannot become GUI-only by omission. Every catalogue operation
carries a non-empty ``cli_equivalent`` string, which is what the CLI/GUI
round-trip guarantee (TOOL-UIX-330, WP-API-03) falls out of.

Only protocol-level operations that the recorded design already names are
registered here; engine operations (environment build, run, report ...) are
added by their owning packages as they land.

Satisfies: TOOL-UIX-010, TOOL-UIX-020, TOOL-PLG-060.
Design: SDD-002 §9.2/§9.3.
"""

from __future__ import annotations

from dataclasses import dataclass

from ectt.api.errors import ApiError

__all__ = [
    "BOOTSTRAP_VERSION",
    "INTERFACE_VERSION",
    "SUPPORTED_INTERFACE_VERSIONS",
    "Catalogue",
    "Operation",
    "default_catalogue",
]

#: Exact interface version this build publishes (SDD-002 §3: every seam
#: carries an explicit version).
INTERFACE_VERSION = "1.0"

#: Versions this build can negotiate (SDD-002 §9.2: hello selects an exact
#: common version from the client's offered list).
SUPPORTED_INTERFACE_VERSIONS: tuple[str, ...] = (INTERFACE_VERSION,)

#: Fixed bootstrap envelope version (SDD-002 §9.2).
BOOTSTRAP_VERSION = "1"


@dataclass(frozen=True)
class Operation:
    """One entry of the engine operation catalogue.

    ``cli_equivalent`` is the CLI invocation that performs the same operation;
    it is what makes a capability impossible to become GUI-only (TOOL-UIX-010).
    """

    name: str
    summary: str
    cli_equivalent: str
    since_version: str = INTERFACE_VERSION
    cancellable: bool = False


class Catalogue:
    """Registry of the engine's operations.

    Duplicate names are refused: two entries with the same ``name`` would give
    front-ends and the generated CLI divergent views of one capability.
    """

    def __init__(self) -> None:
        self._operations: dict[str, Operation] = {}

    def register(self, operation: Operation) -> None:
        """Add ``operation`` to the catalogue, refusing duplicate names."""
        if operation.name in self._operations:
            raise ApiError(
                f"operation already registered: {operation.name}",
                reason="duplicate_operation",
            )
        self._operations[operation.name] = operation

    def get(self, name: str) -> Operation:
        """Return the operation registered under ``name``."""
        try:
            return self._operations[name]
        except KeyError:
            raise ApiError(
                f"unknown operation: {name}",
                reason="unknown_operation",
            ) from None

    def has(self, name: str) -> bool:
        """Return whether ``name`` is a registered operation."""
        return name in self._operations

    def names(self) -> list[str]:
        """Return all registered operation names, sorted for determinism."""
        return sorted(self._operations)

    def cli_equivalent_for(self, name: str) -> str:
        """Return the CLI invocation equivalent to operation ``name``."""
        return self.get(name).cli_equivalent


def default_catalogue() -> Catalogue:
    """Build the catalogue with the protocol-level operations of SDD-002 §9.2."""
    catalogue = Catalogue()
    catalogue.register(
        Operation(
            name="operation.cancel",
            summary="Request cancellation of a running operation by its session ID.",
            cli_equivalent="ectt operation cancel --target-id <id>",
            cancellable=False,
        )
    )
    return catalogue
