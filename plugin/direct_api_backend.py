"""Pure G2-F-3 preflight and guard for the future direct HCCL backend.

This module intentionally imports neither ctypes nor CANN bindings.  It never
loads an official DSO and rejects every lifecycle or collective request before
the native runtime boundary.  Actual runtime work belongs no earlier than
G2-F-4 and must be separately opt-in on real hardware.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


BACKEND_NAME = "ASCEND_HCCL_DIRECT"
RUNTIME_API_CALLS: tuple[str, ...] = ()
_BLOCKED_OPERATIONS = frozenset({
    "acl_init", "acl_finalize", "set_device", "create_context",
    "create_stream", "allocate_device_memory", "copy_memory",
    "create_communicator", "destroy_communicator", "all_reduce",
    "all_gather", "reduce_scatter",
})


class DirectApiRuntimeRejected(RuntimeError):
    """Raised when a G2-F-3 request tries to cross the runtime boundary."""


def diagnose_no_device(probe: Mapping[str, Any]) -> dict[str, Any]:
    """Return a structured, side-effect-free hardware preflight result.

    ``probe`` is supplied by an external read-only inspector; keeping it an
    input makes this module importable on Windows without CANN or WSL.
    """
    device_nodes = tuple(str(node) for node in probe.get("device_nodes", ()))
    npu_smi_found = bool(probe.get("npu_smi_found", False))
    driver_indicators = tuple(str(item) for item in probe.get("driver_indicators", ()))
    no_device = not device_nodes and not npu_smi_found and not driver_indicators
    return {
        "backend": BACKEND_NAME,
        "status": "NO_DEVICE_EXPECTED" if no_device else "HARDWARE_PRESENT_UNVALIDATED",
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "runtime_initialized": False,
        "device_opened": False,
        "communicator_created": False,
        "collective_executed": False,
        "runtime_api_calls": list(RUNTIME_API_CALLS),
        "probe": {
            "npu_smi_found": npu_smi_found,
            "device_nodes": list(device_nodes),
            "driver_indicators": list(driver_indicators),
        },
    }


def reject_runtime_request(operation: str) -> None:
    """Reject direct lifecycle/collective work before any native call exists."""
    normalized = operation.strip().casefold().replace("-", "_")
    if normalized in _BLOCKED_OPERATIONS:
        raise DirectApiRuntimeRejected(
            f"{operation} is guarded in G2-F-3 before the ACL/HCCL runtime boundary"
        )
    raise DirectApiRuntimeRejected(
        f"{operation} is not an enabled G2-F-3 direct API operation"
    )
