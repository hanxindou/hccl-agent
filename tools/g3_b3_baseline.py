"""Freeze the independent G3-B3-A contracts and incremental host-model baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from algorithm.ring_schedule import generate_ring_schedule
from algorithm.schedule_ir import validate_schedule as validate_schedule_v1
from feature_completion.contracts import (
    AGENT_PROPOSAL_VERSION,
    SCHEDULE_IR_VERSION,
    canonical_hash,
    upgrade_dense_schedule_v2,
    validate_agent_proposal_v2,
    validate_schedule_v2,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_ROOT = ROOT / "configs/feature_completion"
SCHEDULE_SCHEMA = CONFIG_ROOT / "g3_b3_schedule_ir_v2_schema.json"
PROPOSAL_SCHEMA = CONFIG_ROOT / "g3_b3_agent_proposal_v2_schema.json"
DATA_PROFILES = CONFIG_ROOT / "g3_b3_data_profiles.json"
SPARSE_MATRIX = CONFIG_ROOT / "g3_b3_sparse_benchmark_matrix.json"
RELIABILITY_MATRIX = CONFIG_ROOT / "g3_b3_reliability_benchmark_matrix.json"
CLAIM_CONTRACT = ROOT / "docs/submission/g3_b3_claim_contract.json"
G3_B2_BASELINE = ROOT / "experiments/optimization/g3_b2_final_baseline.json"
G3_B2_MATRIX = ROOT / "configs/optimization/g3_b2_benchmark_matrix.json"
G3_B2_PARAMETERS = ROOT / "experiments/optimization/g3_b2_parameter_freeze.json"

MODEL_PARAMETERS = {
    "schema_version": "g3-b3-contract-cost-model-v1",
    "truth_label": "HOST_CONTRACT_MODEL_ONLY",
    "metadata_bytes_per_payload": 64,
    "detect_cost_us_per_mib": 0.25,
    "encode_cost_us_per_mib": 0.60,
    "decode_cost_us_per_mib": 0.40,
    "p95_multiplier": 1.05,
    "topology_bandwidth_gbps": {
        "FULL_MESH": 100.0,
        "RING": 100.0,
        "FAT_TREE": 50.0,
        "HETEROGENEOUS": 25.0,
    },
    "topology_latency_us": {
        "FULL_MESH": 2.0,
        "RING": 2.0,
        "FAT_TREE": 5.0,
        "HETEROGENEOUS": 7.0,
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_sha256sums(root: Path) -> dict[str, Any]:
    sums = root / "SHA256SUMS"
    checked = 0
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        path = root / relative
        if sha256_file(path) != expected:
            raise RuntimeError(f"G3-B2 evidence checksum mismatch: {relative}")
        checked += 1
    return {
        "path": root.relative_to(ROOT).as_posix(),
        "files_checked": checked,
        "sha256sums_sha256": sha256_file(sums),
        "valid": True,
    }


def validate_g3_b2_integrity() -> dict[str, Any]:
    baseline = json.loads(G3_B2_BASELINE.read_text(encoding="utf-8"))
    matrix_hash = sha256_file(G3_B2_MATRIX)
    parameter_hash = sha256_file(G3_B2_PARAMETERS)
    if matrix_hash != baseline["final_benchmark_matrix_sha256"]:
        raise RuntimeError("G3-B2 benchmark SHA256 drifted")
    if parameter_hash != baseline["final_parameter_set_sha256"]:
        raise RuntimeError("G3-B2 parameter SHA256 drifted")
    evidence = ROOT / baseline["final_evidence_path"]
    evidence_result = validate_sha256sums(evidence)
    changed = git("status", "--short", "--", "experiments/optimization/evidence", "experiments/optimization/g3_b2_final_baseline.json")
    if changed:
        raise RuntimeError(f"G3-B2 authority evidence has worktree changes: {changed}")
    return {
        "schema_version": "g3-b3-g3-b2-integrity-v1",
        "g3_b2_final_source_commit": baseline["final_source_commit"],
        "g3_b2_final_commit": "cc632a145b33a82c40244f9158ca0876d65ec5a0",
        "benchmark_sha256": matrix_hash,
        "parameter_sha256": parameter_hash,
        "final_evidence": evidence_result,
        "freeze_status": baseline["freeze_status"],
        "historical_performance": {
            "wins": 18,
            "ties": 0,
            "losses": 0,
            "weighted_simulated_improvement_percent": 45.59283008,
            "truth_label": "SIMULATED_ONLY",
        },
        "old_evidence_modified": False,
        "valid": True,
    }


def index_width(logical_elements: int) -> int:
    if logical_elements <= 65535:
        return 2
    if logical_elements <= 4294967295:
        return 4
    return 8


def transfer_multiplier(primitive: str, ranks: int) -> float:
    if primitive == "AllReduce":
        return 2.0 * (ranks - 1) / ranks
    return (ranks - 1) / ranks


def baseline_metrics(
    matrix: dict[str, Any], profiles: dict[str, Any]
) -> list[dict[str, Any]]:
    profile_map = {row["profile_id"]: row for row in profiles["profiles"]}
    dtype_bytes = {"FP32": 4, "FP16": 2, "BF16": 2}
    rows: list[dict[str, Any]] = []
    for scenario in matrix["scenarios"]:
        ratio = profile_map[scenario["data_profile"]]["sparsity_ratio"]
        logical = scenario["message_size_bytes"]
        element_size = dtype_bytes[scenario["dtype"]]
        elements = logical // element_size
        nonzero = int(math.floor(elements * (1.0 - ratio)))
        width = index_width(elements)
        value_bytes = nonzero * element_size
        index_bytes = nonzero * width
        metadata_bytes = MODEL_PARAMETERS["metadata_bytes_per_payload"]
        sparse_wire = value_bytes + index_bytes + metadata_bytes
        dense_wire = logical
        mib = logical / (1024 * 1024)
        detect_cost = mib * MODEL_PARAMETERS["detect_cost_us_per_mib"]
        encode_cost = mib * MODEL_PARAMETERS["encode_cost_us_per_mib"]
        decode_cost = mib * MODEL_PARAMETERS["decode_cost_us_per_mib"]
        bandwidth = MODEL_PARAMETERS["topology_bandwidth_gbps"][scenario["topology"]]
        latency = MODEL_PARAMETERS["topology_latency_us"][scenario["topology"]]
        multiplier = transfer_multiplier(scenario["primitive"], scenario["ranks"])
        dense_cost = latency + dense_wire * multiplier * 8 / (bandwidth * 1000)
        sparse_transfer_cost = latency + sparse_wire * multiplier * 8 / (bandwidth * 1000)
        sparse_total = sparse_transfer_cost + detect_cost + encode_cost + decode_cost
        rows.append(
            {
                "scenario_id": scenario["scenario_id"],
                "data_profile": scenario["data_profile"],
                "logical_bytes": logical,
                "dense_wire_bytes": dense_wire,
                "sparse_wire_bytes": sparse_wire,
                "index_bytes": index_bytes,
                "value_bytes": value_bytes,
                "metadata_bytes": metadata_bytes,
                "compression_ratio": round(dense_wire / sparse_wire, 9),
                "sparsity_ratio": ratio,
                "detect_cost_us": round(detect_cost, 9),
                "encode_cost_us": round(encode_cost, 9),
                "decode_cost_us": round(decode_cost, 9),
                "schedule_cost_us": round(sparse_transfer_cost, 9),
                "p50_us": round(dense_cost, 9),
                "p95_us": round(dense_cost * MODEL_PARAMETERS["p95_multiplier"], 9),
                "estimated_sparse_total_cost_us": round(sparse_total, 9),
                "modeled_sparse_below_dense": sparse_total < dense_cost,
                "selected_mode": "DENSE_CONTRACT_BASELINE",
                "correctness": "NOT_EXECUTED_IN_G3_B3_A",
                "dense_fallback": "NOT_EVALUATED_IN_CONTRACT_PHASE",
                "codec_execution": False,
                "truth_label": "HOST_CONTRACT_MODEL_ONLY",
            }
        )
    return rows


def compatibility_audit() -> dict[str, Any]:
    v1 = generate_ring_schedule("AllReduce", 4, 65536)
    v1_hash_before = canonical_hash(v1)
    v1_results = validate_schedule_v1(v1)
    v2 = upgrade_dense_schedule_v2(v1)
    v2_results = validate_schedule_v2(v2)
    if canonical_hash(v1) != v1_hash_before:
        raise RuntimeError("dense v2 upgrade mutated the v1 schedule")
    return {
        "schema_version": "g3-b3-v1-v2-compatibility-audit-v1",
        "v1_schema_version": v1["schema_version"],
        "v1_schedule_hash": v1["schedule_hash"],
        "v1_validation": v1_results,
        "v1_unchanged": True,
        "v2_schema_version": v2["schema_version"],
        "v2_schedule_hash": v2["schedule_hash"],
        "v2_dense_compatibility": True,
        "v2_validation": v2_results,
    }


def proposal_audit() -> dict[str, Any]:
    proposal: dict[str, Any] = {
        "schema_version": AGENT_PROPOSAL_VERSION,
        "proposal_id": "g3-b3-a-dense-contract-example",
        "schedule_algorithm": "Ring",
        "payload_mode": "DENSE",
        "sparse_codec": "NONE",
        "data_profile": "S00",
        "sparsity_ratio": 0.0,
        "logical_bytes": 65536,
        "estimated_wire_bytes": 65536,
        "metadata_overhead": 0,
        "estimated_compression_ratio": 1.0,
        "encode_cost": 0.0,
        "decode_cost": 0.0,
        "chunk_size": 16384,
        "pipeline_depth": 1,
        "credit_window": 1,
        "integrity_policy": {"checksum_type": "NONE", "reason": "contract phase"},
        "retry_policy": {"max_retries": 0, "reason": "contract phase"},
        "flow_control_policy": {"enabled": False, "reason": "contract phase"},
        "dense_fallback_condition": "SPARSE_NOT_IMPLEMENTED_IN_G3_B3_A",
        "fallback_conditions": [
            "LOW_SPARSITY",
            "METADATA_OVERHEAD",
            "UNSUPPORTED_DTYPE",
            "UNSUPPORTED_PRIMITIVE",
            "MEMORY_LIMIT",
            "CODEC_ERROR",
            "CORRECTNESS_GATE",
        ],
        "correctness_plan": ["v1 dense semantic compatibility", "reference validation"],
        "validation_plan": ["IR v2 schema", "canonical hash", "dense fallback audit"],
        "expected_benefit": "none in the contract-only baseline",
        "expected_risk": "sparse and reliability execution are intentionally not implemented in G3-B3-A",
    }
    proposal["proposal_hash"] = canonical_hash(proposal)
    validation = validate_agent_proposal_v2(proposal)
    return {"proposal": proposal, "validation": validation}


def write_integrity(evidence: Path) -> str:
    files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    lines = [f"{sha256_file(path)}  {path.name}" for path in files]
    sums = evidence / "SHA256SUMS"
    write_text(sums, "\n".join(lines) + "\n")
    return sha256_file(sums)


def generate(evidence: Path, *, refresh_existing: bool = False) -> dict[str, Any]:
    if evidence.exists() and not refresh_existing:
        raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    if evidence.exists() and not evidence.name.startswith("g3_b3_a_baseline_"):
        raise RuntimeError(f"refusing to refresh unexpected evidence path: {evidence}")
    evidence.mkdir(parents=True, exist_ok=refresh_existing)

    g3_b2 = validate_g3_b2_integrity()
    profiles = json.loads(DATA_PROFILES.read_text(encoding="utf-8"))
    sparse_matrix = json.loads(SPARSE_MATRIX.read_text(encoding="utf-8"))
    reliability_matrix = json.loads(RELIABILITY_MATRIX.read_text(encoding="utf-8"))
    metrics = baseline_metrics(sparse_matrix, profiles)
    compatibility = compatibility_audit()
    proposal = proposal_audit()

    source_commit = git("rev-parse", "HEAD")
    baseline = {
        "schema_version": "g3-b3-a-incremental-baseline-v1",
        "checkpoint": "G3-B3-A",
        "checkpoint_status": "COMPLETED",
        "freeze_status": "FROZEN",
        "source_baseline_commit": source_commit,
        "g3_b2_final_commit": g3_b2["g3_b2_final_commit"],
        "schedule_ir_version": SCHEDULE_IR_VERSION,
        "agent_proposal_version": AGENT_PROPOSAL_VERSION,
        "sparse_codec_status": "NOT_IMPLEMENTED_IN_CONTRACT_PHASE",
        "integrity_status": "NOT_IMPLEMENTED_IN_CONTRACT_PHASE",
        "retry_status": "NOT_IMPLEMENTED_IN_CONTRACT_PHASE",
        "flow_control_status": "NOT_IMPLEMENTED_IN_CONTRACT_PHASE",
        "sparse_scenario_count": len(sparse_matrix["scenarios"]),
        "reliability_scenario_count": len(reliability_matrix["scenarios"]),
        "model_parameters": MODEL_PARAMETERS,
        "contract_hashes": {
            "schedule_ir_v2_schema_sha256": sha256_file(SCHEDULE_SCHEMA),
            "agent_proposal_v2_schema_sha256": sha256_file(PROPOSAL_SCHEMA),
            "data_profiles_sha256": sha256_file(DATA_PROFILES),
            "sparse_benchmark_sha256": sha256_file(SPARSE_MATRIX),
            "reliability_benchmark_sha256": sha256_file(RELIABILITY_MATRIX),
            "claim_contract_sha256": sha256_file(CLAIM_CONTRACT),
        },
        "truth_label": "HOST_CONTRACT_MODEL_ONLY",
        "old_evidence_modified": False,
        "g3_b2_baseline_modified": False,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "runtime_api_calls": [],
    }
    manifest = {
        "schema_version": "g3-b3-a-evidence-manifest-v1",
        "checkpoint": "G3-B3-A",
        "checkpoint_status": "COMPLETED",
        "project_commit": source_commit,
        "baseline_commit": source_commit,
        "source_documents": ["docs/plans/g3-competition-delivery-readiness.md"],
        "generated_artifacts": [
            "baseline.json",
            "schedule_ir_v2_schema.json",
            "agent_proposal_v2_schema.json",
            "data_profiles.json",
            "sparse_benchmark_contract.json",
            "reliability_benchmark_contract.json",
            "claim_contract.json",
            "g3_b2_baseline_integrity.json",
            "baseline_metrics.json",
            "v1_v2_compatibility.json",
            "agent_proposal_v2_audit.json",
        ],
        "tests": ["tests/feature_completion/test_g3_b3_contracts.py"],
        "warnings": ["G3-B3-A freezes contracts only; sparse, integrity, retry, flow control, and direct runtime source are not implemented here."],
        "known_limitations": ["wire bytes and latency values are host contract models, not physical measurements"],
        "old_evidence_modified": False,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "runtime_api_calls": [],
    }
    result = {
        "schema_version": "g3-b3-a-result-v1",
        "checkpoint": "G3-B3-A",
        "checkpoint_status": "COMPLETED",
        "baseline_frozen": True,
        "schedule_ir_v2": "COMPLETED",
        "schedule_ir_v1_historical_compatibility": "PASS",
        "agent_proposal_v2": "COMPLETED",
        "sparse_profiles": "FROZEN",
        "sparse_benchmark": "FROZEN",
        "reliability_benchmark": "FROZEN",
        "claim_contract": "FROZEN",
        "algorithm_implementation_changed": False,
        "sparse_implemented": False,
        "public_abi_changed": False,
        "old_evidence_modified": False,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "runtime_api_calls": [],
    }

    copies = {
        SCHEDULE_SCHEMA: "schedule_ir_v2_schema.json",
        PROPOSAL_SCHEMA: "agent_proposal_v2_schema.json",
        DATA_PROFILES: "data_profiles.json",
        SPARSE_MATRIX: "sparse_benchmark_contract.json",
        RELIABILITY_MATRIX: "reliability_benchmark_contract.json",
        CLAIM_CONTRACT: "claim_contract.json",
    }
    for source, name in copies.items():
        shutil.copyfile(source, evidence / name)
    write_json(evidence / "baseline.json", baseline)
    write_json(evidence / "manifest.json", manifest)
    write_json(evidence / "result.json", result)
    write_json(evidence / "g3_b2_baseline_integrity.json", g3_b2)
    write_json(evidence / "baseline_metrics.json", metrics)
    write_json(evidence / "v1_v2_compatibility.json", compatibility)
    write_json(evidence / "agent_proposal_v2_audit.json", proposal)
    write_text(
        evidence / "README.md",
        "# G3-B3-A feature-completion contract baseline\n\n"
        "This authority evidence freezes Schedule IR v2, Agent proposal v2, sparse data profiles, independent incremental benchmarks, and the G3-B3 claim boundary. "
        "It does not implement or execute sparse transport, integrity/retry, flow control, official ACL/HCCL runtime, or real-device behavior. "
        "All byte and latency entries in `baseline_metrics.json` are deterministic host contract models.\n",
    )
    anchor = write_integrity(evidence)
    return {
        "evidence": evidence.relative_to(ROOT).as_posix(),
        "sha256": anchor,
        "sparse_scenarios": len(sparse_matrix["scenarios"]),
        "reliability_scenarios": len(reliability_matrix["scenarios"]),
        "g3_b2_integrity": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--refresh-existing", action="store_true")
    args = parser.parse_args()
    evidence = args.evidence_dir if args.evidence_dir.is_absolute() else ROOT / args.evidence_dir
    print(json.dumps(generate(evidence, refresh_existing=args.refresh_existing), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
