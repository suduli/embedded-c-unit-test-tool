"""ECTT Target Execution.

Provides simulator run planning (QEMU/Renode descriptors), debug-probe
execution and flashing planning, result-retrieval protocol parsing,
declarative hardware inventory, target-failure classification, and the
on-target footprint documentation surface.
"""

from ectt.ext.errors import ExtError
from ectt.ext.simulator import (
    FAMILY_QEMU,
    FAMILY_RENODE,
    QEMU_SIMULATOR,
    RENODE_SIMULATOR,
    SIMULATOR_FAMILIES,
    SimulatorDescriptor,
    SimulatorPlan,
    UnknownSimulatorError,
    consume_simulator_output,
    plan_simulator_run,
    qemu_descriptor,
    renode_descriptor,
)

__all__ = [
    "ExtError",
    # Simulator execution (WP-EXT-01)
    "SIMULATOR_FAMILIES",
    "FAMILY_QEMU",
    "FAMILY_RENODE",
    "QEMU_SIMULATOR",
    "RENODE_SIMULATOR",
    "SimulatorDescriptor",
    "SimulatorPlan",
    "UnknownSimulatorError",
    "qemu_descriptor",
    "renode_descriptor",
    "plan_simulator_run",
    "consume_simulator_output",
]
