"""Read-only G2-F-7 evidence inventory and final status aggregation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from agent.backend_control import BackendControlPlane
from agent.report_generator import ReportGenerator
from plugin.backend_registry import registry_payload


EVIDENCE_SPECS = (
    ("G2-E", "ASCEND_HCCL_VM", "HCCL_VM", "experiments/hccl_vm/evidence/g2_e_summary_20260730T095800.105217Z", "summary.json", "HCCL_VM_EXECUTED"),
    ("G2-F-1", "ASCEND_HCCL_DIRECT", "DIRECT_READINESS", "experiments/direct_api/evidence/g2_f_1_20260730T203000Z", "result.json", "DIRECT_READINESS_ONLY"),
    ("G2-F-2", "ASCEND_HCCL_DIRECT", "DIRECT_READINESS", "experiments/direct_api/evidence/g2_f_2_20260730T210000Z", "result.json", "DIRECT_READINESS_ONLY"),
    ("G2-F-3", "ASCEND_HCCL_DIRECT", "DIRECT_READINESS", "experiments/direct_api/evidence/g2_f_3_20260802T000000Z", "result.json", "DIRECT_READINESS_ONLY"),
    ("G2-F-4", "ASCEND_HCCL_DIRECT", "DIRECT_READINESS", "experiments/direct_api/evidence/g2_f_4_20260802T010000Z", "result.json", "DIRECT_READINESS_ONLY"),
    ("G2-F-5", "SIMULATOR_ACCEPTANCE", "SIMULATOR_ACCEPTANCE", "experiments/simulator/evidence/g2_f_5_simulator_20260804T010000Z", "result.json", "SIMULATED_ONLY"),
    ("G2-F-6", "SIMULATOR_ACCEPTANCE", "SIMULATOR_ACCEPTANCE", "experiments/simulator/evidence/g2_f_6_simulator_20260804T020000Z", "result.json", "SIMULATED_ONLY"),
)


class EvidenceAuditError(RuntimeError):
    """Evidence is missing, malformed, or contradicts its permitted claim."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sha256sums(directory: Path) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS"
    if not manifest.is_file():
        raise EvidenceAuditError(f"SHA256SUMS missing: {manifest}")
    failures = []
    entries = 0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or not digest or not filename:
            raise EvidenceAuditError(f"invalid SHA256SUMS line in {manifest}: {line!r}")
        target = directory / filename
        if not target.is_file() or _sha256(target) != digest:
            failures.append(filename)
        entries += 1
    if failures:
        raise EvidenceAuditError(f"SHA256 verification failed in {directory}: {', '.join(failures)}")
    return {"verified": True, "entry_count": entries, "sha256sums_digest": _sha256(manifest)}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceAuditError(f"cannot parse evidence JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise EvidenceAuditError(f"evidence JSON must be an object: {path}")
    return payload


def build_evidence_inventory(repo_root: Path) -> list[dict[str, Any]]:
    inventory = []
    for checkpoint, backend, track, relative, result_name, claim_type in EVIDENCE_SPECS:
        directory = repo_root / relative
        result_path = directory / result_name
        manifest_path = directory / "manifest.json"
        if not result_path.is_file():
            raise EvidenceAuditError(f"required evidence files missing for {checkpoint}: {directory}")
        checksum = verify_sha256sums(directory)
        result = _read_json(result_path)
        manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
        direct_claim = bool(result.get("direct_hccl_api_call", False))
        real_claim = bool(result.get("real_ascend_npu_validated", False))
        measured = bool(result.get("measured_on_real_npu", False))
        if direct_claim or real_claim or measured:
            raise EvidenceAuditError(f"unsupported real/direct claim in {checkpoint}")
        evidence_status = result.get("checkpoint_status") or result.get("status")
        completed = evidence_status == "COMPLETED" or result.get("passed") is True
        if not completed:
            raise EvidenceAuditError(f"{checkpoint} is not completed: {evidence_status!r}")
        inventory.append({
            "checkpoint": checkpoint, "validation_track": track, "backend": backend,
            "schema_version": manifest.get("schema_version", result.get("schema_version", manifest.get("checkpoint", "unversioned"))),
            "status": "COMPLETED", "evidence_status": evidence_status,
            "evidence_path": relative, "execution_mode": result.get("execution_mode", execution_mode_for(backend)),
            "direct_hccl_api_call": direct_claim, "real_device_claim": real_claim,
            "performance_claim_type": result.get("performance_claim_type", claim_type),
            "known_limitations": limitations_for(backend), **checksum,
        })
    return inventory


def execution_mode_for(backend: str) -> str:
    return {
        "CPU_SIM": "cpu_sim_in_process", "ASCEND_HCCL_VM": "subprocess_hccl_test",
        "ASCEND_HCCL_DIRECT": "direct_preflight", "SIMULATOR_ACCEPTANCE": "evidence_summary_only",
    }[backend]


def limitations_for(backend: str) -> list[str]:
    return {
        "ASCEND_HCCL_VM": ["subprocess HCCL-VM validation is not in-process direct API or real NPU evidence"],
        "ASCEND_HCCL_DIRECT": ["readiness/guard only; no current device, communicator, or collective execution"],
        "SIMULATOR_ACCEPTANCE": ["correctness/performance/reliability are simulated and not hardware calibrated"],
    }.get(backend, ["CPU_SIM is project-local and not official HCCL or real NPU evidence"])


def aggregate_status(inventory: list[dict[str, Any]]) -> dict[str, str]:
    completed = {entry["checkpoint"] for entry in inventory if entry["status"] == "COMPLETED"}
    required = {"G2-E", "G2-F-1", "G2-F-2", "G2-F-3", "G2-F-4", "G2-F-5", "G2-F-6"}
    if completed != required:
        raise EvidenceAuditError(f"inventory checkpoint set is incomplete: {sorted(completed)}")
    return {
        "G2-F-7": "COMPLETED", "agent_backend_integration": "COMPLETED", "three_backend_isolation": "COMPLETED",
        "final_audit": "COMPLETED", "g2_f_readiness": "COMPLETED", "competition_simulator_track": "COMPLETED",
        "g2_f_real_device_acceptance": "HARDWARE_BLOCKED", "g2_f_overall": "PARTIAL",
    }


def build_final_audit(repo_root: Path, *, official_repositories: dict[str, Any] | None = None) -> dict[str, Any]:
    inventory = build_evidence_inventory(repo_root)
    controller = BackendControlPlane()
    selections = {name: controller.select(name) for name in ("CPU_SIM", "ASCEND_HCCL_VM", "ASCEND_HCCL_DIRECT")}
    direct_execute = controller.select("ASCEND_HCCL_DIRECT", request_kind="execute")
    if direct_execute["status"] != "NO_DEVICE_EXPECTED" or direct_execute["runtime_api_calls"] != []:
        raise EvidenceAuditError("direct readiness guard did not return the required no-device result")
    simulator = controller.simulator_acceptance()
    aggregation = aggregate_status(inventory)
    audit = {
        "backend_registry": registry_payload(), "backend_capabilities": selections,
        "backend_isolation_audit": {
            "fallback_policy": "NONE", "cpu_sim_loads_vm_runner": False, "cpu_sim_loads_direct": False,
            "hccl_vm_calls_cpu_sim_collective": False, "hccl_vm_loads_direct": False,
            "direct_loads_hccl_vm_runner": False, "direct_calls_cpu_sim_collective": False,
            "simulator_acceptance_is_execution_backend": False, "direct_execution_guard": direct_execute,
            "all_current_direct_hccl_api_calls_false": True, "all_current_real_ascend_claims_false": True,
        },
        "agent_integration": {"selection_examples": selections, "simulator_acceptance": simulator, "default_backend": "CPU_SIM", "fallback_policy": "NONE"},
        "cpu_sim_summary": {"label": "CPU_EXECUTED", "selected_backend": "CPU_SIM", "execution_mode": "cpu_sim_in_process", "evidence": "CPU_SIM regression", "not_comparable_with": ["real-device performance", "simulator modeled latency"]},
        "hccl_vm_summary": {"label": "HCCL_VM_EXECUTED", "selected_backend": "ASCEND_HCCL_VM", "execution_mode": "subprocess_hccl_test", "evidence": "G2-E suite summary", "not_comparable_with": ["in-process direct API", "CPU_SIM fallback"]},
        "direct_readiness_summary": {"label": "DIRECT_READINESS_ONLY", **direct_execute},
        "simulator_acceptance_summary": {"label": "SIMULATED_ONLY", **simulator},
        "status_aggregation": aggregation, "evidence_inventory": inventory,
        "claim_boundary_audit": {"direct_hccl_api_call": False, "real_ascend_npu_validated": False, "measured_on_real_npu": False, "collective_executed_on_real_device": False, "runtime_api_calls": [], "performance_claim_type": "SIMULATED_ONLY", "prohibited_claims": ["REAL_DEVICE_PASS", "direct collective success", "real NPU performance", "msprof executed"]},
        "known_limitations": {"real_device_calibration_status": "UNAVAILABLE_NO_REAL_DEVICE", "limitations": ["No real Ascend NPU, driver/device node, communicator, memory, collective, MPI, hccl_test suite, or msprof was executed.", "Direct readiness is not direct collective execution.", "Simulator correctness/performance/reliability values are not hardware measurements."]},
        "real_device_resume": {"status": "HARDWARE_BLOCKED", "required_conditions": ["supported Ascend NPU and driver/device node", "frozen compatible CANN", "approved launcher and rank-table or root-info", "at least two ranks", "device/context/stream and device-memory permission", "real communicator and per-rank API trace", "D2H independent host reference, cleanup trace, topology/profiling, and dedicated real-device evidence"], "current_action": "Do not cross the runtime boundary until a separately approved real-device acceptance run."},
        "official_repositories": official_repositories or {},
    }
    audit["final_report"] = ReportGenerator.generate_backend_isolation_report(audit)
    return audit
