"""ECTT Target Execution.

Provides simulator run planning (QEMU/Renode descriptors), debug-probe
execution and flashing planning, result-retrieval protocol parsing,
declarative hardware inventory, target-failure classification, and the
on-target footprint documentation surface.
"""

from ectt.ext.channels import (
    CHANNEL_SEMIHOSTING,
    CHANNEL_SERIAL_UART,
    RetrievalChannel,
    UnknownChannelError,
    parse_channel_output,
    semihosting_channel,
    serial_uart_channel,
)
from ectt.ext.errors import ExtError
from ectt.ext.probe import (
    FAMILY_JLINK,
    FAMILY_OPENOCD,
    FAMILY_PYOCD,
    PROBE_FAMILIES,
    ProbeDescriptor,
    ProbePlan,
    UnknownProbeError,
    jlink_descriptor,
    openocd_descriptor,
    plan_flash,
    plan_probe_run,
    pyocd_descriptor,
)
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
from ectt.ext.usermethod import (
    DuplicateMethodError,
    ExecutionMethodDescriptor,
    ExecutionMethodPlan,
    MethodRegistry,
    UnknownMethodError,
    plan_user_execution,
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
    # Result retrieval channels (WP-EXT-03)
    "CHANNEL_SEMIHOSTING",
    "CHANNEL_SERIAL_UART",
    "RetrievalChannel",
    "UnknownChannelError",
    "semihosting_channel",
    "serial_uart_channel",
    "parse_channel_output",
    # Debug-probe execution & flashing (WP-EXT-02)
    "PROBE_FAMILIES",
    "FAMILY_OPENOCD",
    "FAMILY_PYOCD",
    "FAMILY_JLINK",
    "ProbeDescriptor",
    "ProbePlan",
    "UnknownProbeError",
    "openocd_descriptor",
    "pyocd_descriptor",
    "jlink_descriptor",
    "plan_probe_run",
    "plan_flash",
    # User-supplied execution methods (WP-EXT-07)
    "DuplicateMethodError",
    "ExecutionMethodDescriptor",
    "ExecutionMethodPlan",
    "MethodRegistry",
    "plan_user_execution",
]
