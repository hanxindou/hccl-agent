"""Single, runtime-free registry for G2-F-7 backend selection and claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Mapping


DEFAULT_BACKEND = "CPU_SIM"
FALLBACK_POLICY = "NONE"
EXECUTION_BACKENDS = ("CPU_SIM", "ASCEND_HCCL_VM", "ASCEND_HCCL_DIRECT")
VALIDATION_TRACKS = ("SIMULATOR_ACCEPTANCE",)


@dataclass(frozen=True)
class BackendCapability:
    name: str
    backend_type: str
    execution_mode: str
    default_or_opt_in: str
    supported_primitives: tuple[str, ...]
    supported_dtypes: tuple[str, ...]
    supported_reduce_ops: tuple[str, ...]
    required_environment: tuple[str, ...]
    hardware_requirement: str
    current_availability: str
    readiness_status: str
    evidence_refs: tuple[str, ...]
    prohibited_claims: tuple[str, ...]
    fallback_policy: str = FALLBACK_POLICY

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key, value in list(payload.items()):
            if isinstance(value, tuple):
                payload[key] = list(value)
        return payload


_BACKENDS: Mapping[str, BackendCapability] = MappingProxyType({
    "CPU_SIM": BackendCapability(
        name="CPU_SIM", backend_type="execution_backend", execution_mode="cpu_sim_in_process",
        default_or_opt_in="default", supported_primitives=("AllReduce", "AllGather", "ReduceScatter"),
        supported_dtypes=("FP32", "FP16", "BF16", "INT32"), supported_reduce_ops=("SUM", "PROD", "MAX", "MIN"),
        required_environment=("project CPU_SIM plugin",), hardware_requirement="none",
        current_availability="AVAILABLE", readiness_status="CPU_EXECUTED",
        evidence_refs=("CPU_SIM CTest", "Python CPU_SIM regression"),
        prohibited_claims=("official HCCL ABI", "real Ascend NPU performance", "direct HCCL API call"),
    ),
    "ASCEND_HCCL_VM": BackendCapability(
        name="ASCEND_HCCL_VM", backend_type="execution_backend", execution_mode="subprocess_hccl_test",
        default_or_opt_in="explicit_opt_in", supported_primitives=("AllReduce", "AllGather", "ReduceScatter"),
        supported_dtypes=("INT32",), supported_reduce_ops=("SUM",),
        required_environment=("frozen G2-E HCCL-VM configuration", "WSL official toolchain"), hardware_requirement="HCCL-VM simulator environment",
        current_availability="DRY_RUN_AND_EVIDENCE_ONLY", readiness_status="HCCL_VM_EXECUTED",
        evidence_refs=("experiments/hccl_vm/evidence/g2_e_summary_20260730T095800.105217Z",),
        prohibited_claims=("in-process direct API", "real Ascend NPU validation", "CPU_SIM fallback"),
    ),
    "ASCEND_HCCL_DIRECT": BackendCapability(
        name="ASCEND_HCCL_DIRECT", backend_type="execution_backend", execution_mode="direct_preflight",
        default_or_opt_in="explicit_opt_in", supported_primitives=("AllReduce", "AllGather", "ReduceScatter"),
        supported_dtypes=("FP32", "FP16", "BF16", "INT32"), supported_reduce_ops=("SUM", "MAX", "MIN"),
        required_environment=("frozen CANN manifest", "direct adapter build/link evidence", "real-device opt-in for execution"), hardware_requirement="real Ascend NPU for collective execution",
        current_availability="NO_DEVICE_EXPECTED", readiness_status="DIRECT_READINESS_ONLY",
        evidence_refs=("G2-F-1", "G2-F-2", "G2-F-3", "G2-F-4"),
        prohibited_claims=("current in-process direct API execution", "real Ascend NPU validation", "silent CPU_SIM or HCCL-VM fallback"),
    ),
})

_TRACKS: Mapping[str, Mapping[str, Any]] = MappingProxyType({
    "SIMULATOR_ACCEPTANCE": MappingProxyType({
        "name": "SIMULATOR_ACCEPTANCE", "type": "validation_track", "execution_mode": "evidence_summary_only",
        "current_availability": "COMPLETED_FROM_G2_F_5_AND_G2_F_6_EVIDENCE", "readiness_status": "SIMULATED_ONLY",
        "evidence_refs": ["G2-F-5 simulator correctness", "G2-F-6 simulator topology/performance/reliability"],
        "prohibited_claims": ["real-device measurement", "direct HCCL API call", "real NPU calibration"],
    }),
})


def normalize_backend(value: str | None) -> str:
    selected = DEFAULT_BACKEND if value is None else str(value).strip().upper()
    if selected not in _BACKENDS:
        raise ValueError(f"Unknown backend {value!r}; expected one of: {', '.join(EXECUTION_BACKENDS)}")
    return selected


def backend_capability(value: str | None) -> BackendCapability:
    return _BACKENDS[normalize_backend(value)]


def registry_payload() -> dict[str, Any]:
    return {
        "default_backend": DEFAULT_BACKEND, "fallback_policy": FALLBACK_POLICY,
        "execution_backends": [item.to_dict() for item in _BACKENDS.values()],
        "validation_tracks": [dict(item) for item in _TRACKS.values()],
    }


def validation_track_payload(name: str = "SIMULATOR_ACCEPTANCE") -> dict[str, Any]:
    try:
        return dict(_TRACKS[name])
    except KeyError as exc:
        raise ValueError(f"Unknown validation track {name!r}") from exc
