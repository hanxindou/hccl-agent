"""Agent-facing, lazy backend selection with no silent fallback."""

from __future__ import annotations

from typing import Any

from plugin.backend_registry import (
    DEFAULT_BACKEND, FALLBACK_POLICY, backend_capability, normalize_backend,
    registry_payload, validation_track_payload,
)


class BackendControlPlane:
    """Keep backend selection declarative; runtime modules load only on opt-in."""

    def list_backends(self) -> dict[str, Any]:
        return registry_payload()

    def describe(self, backend: str | None = None) -> dict[str, Any]:
        capability = backend_capability(backend)
        return self._base_selection(capability.name, "explicit request" if backend else "default backend policy")

    def select(self, backend: str | None = None, *, request_kind: str = "query") -> dict[str, Any]:
        selected = normalize_backend(backend)
        payload = self._base_selection(selected, "explicit backend request" if backend else "default backend policy")
        if selected == "ASCEND_HCCL_DIRECT":
            return self._direct_selection(payload, request_kind)
        if selected == "ASCEND_HCCL_VM":
            payload.update({
                "status": "HCCL_VM_COMMAND_REQUIRED" if request_kind == "execute" else "AVAILABLE_FOR_DRY_RUN",
                "availability": "DRY_RUN_AND_EVIDENCE_ONLY", "blocked_reason": None if request_kind != "execute" else "Use an explicit HCCL-VM dry-run or verified subprocess command; no fallback is permitted.",
                "recommended_next_action": "Use the HCCL-VM dry-run/registry/checker fixture workflow.",
            })
            return payload
        payload.update({"status": "AVAILABLE", "availability": "AVAILABLE", "blocked_reason": None, "recommended_next_action": "Run the project CPU_SIM path."})
        return payload

    def simulator_acceptance(self) -> dict[str, Any]:
        track = validation_track_payload()
        return {
            "validation_track": track["name"], "selection_reason": "independent validation track; never an execution backend",
            "execution_mode": track["execution_mode"], "availability": track["current_availability"], "status": track["readiness_status"],
            "capabilities": track["evidence_refs"], "limitations": track["prohibited_claims"], "blocked_reason": "Real-device measurement remains unavailable.",
            "evidence_refs": track["evidence_refs"], "direct_hccl_api_call": False, "real_ascend_npu_validated": False,
            "performance_claim_type": "SIMULATED_ONLY", "measured_on_real_npu": False,
        }

    @staticmethod
    def _base_selection(selected: str, reason: str) -> dict[str, Any]:
        capability = backend_capability(selected)
        return {
            "selected_backend": selected, "selection_reason": reason, "execution_mode": capability.execution_mode,
            "validation_track": None, "availability": capability.current_availability, "status": capability.readiness_status,
            "capabilities": list(capability.supported_primitives), "limitations": list(capability.prohibited_claims),
            "blocked_reason": None, "evidence_refs": list(capability.evidence_refs), "fallback_policy": FALLBACK_POLICY,
            "direct_hccl_api_call": False, "real_ascend_npu_validated": False,
            "performance_claim_type": "CPU_SIMULATION" if selected == "CPU_SIM" else "NOT_A_REAL_DEVICE_MEASUREMENT",
        }

    @staticmethod
    def _direct_selection(payload: dict[str, Any], request_kind: str) -> dict[str, Any]:
        # Local import is intentional: CPU_SIM and HCCL-VM selection never import
        # the direct readiness module, and this module never imports HCCL-VM runner.
        from plugin.direct_api_backend import diagnose_no_device, reject_runtime_request, DirectApiRuntimeRejected

        preflight = diagnose_no_device({"npu_smi_found": False, "device_nodes": (), "driver_indicators": ()})
        if request_kind == "execute":
            try:
                reject_runtime_request("all_reduce")
            except DirectApiRuntimeRejected as exc:
                payload["guard_detail"] = str(exc)
        payload.update({
            "status": preflight["status"], "availability": preflight["status"], "blocked_reason": "No authorized real Ascend NPU/device runtime is available; request was stopped before ACL/HCCL runtime.",
            "recommended_next_action": "Use direct readiness diagnose/evidence now, or provide an approved real-device environment later.",
            "runtime_api_calls": preflight["runtime_api_calls"], "runtime_initialized": False, "device_opened": False,
            "context_created": False, "stream_created": False, "communicator_created": False, "device_buffer_allocated": False,
            "collective_executed_on_real_device": False,
        })
        return payload
