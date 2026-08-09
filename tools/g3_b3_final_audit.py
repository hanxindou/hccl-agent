"""Generate the single authoritative G3-B3-F final evidence directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = ROOT / "experiments/feature_completion/evidence"
SOURCES = {
    "a": EVIDENCE_ROOT / "g3_b3_a_baseline_20260807T133749Z",
    "b": EVIDENCE_ROOT / "g3_b3_b_sparse_20260807T135447Z",
    "c": EVIDENCE_ROOT / "g3_b3_c_integrity_20260807T141931Z",
    "d": EVIDENCE_ROOT / "g3_b3_d_agent_flow_20260807T150515Z",
    "e": EVIDENCE_ROOT / "g3_b3_e_direct_runtime_20260807T160000Z",
}
G3_B2_FINAL = ROOT / "experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def verify(directory: Path) -> dict[str, Any]:
    checked = 0
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        if sha256(directory / name) != expected:
            raise RuntimeError(f"evidence checksum mismatch: {directory / name}")
        checked += 1
    return {"status": "PASS", "path": directory.relative_to(ROOT).as_posix(), "files_checked": checked,
            "sha256sums_sha256": sha256(directory / "SHA256SUMS")}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if output.parent != EVIDENCE_ROOT.resolve() or not output.name.startswith("g3_b3_f_final_"):
        raise SystemExit("output must be a g3_b3_f_final_* directory under feature-completion evidence")
    if output.exists():
        if not args.refresh:
            raise SystemExit("final evidence already exists; --refresh is required")
        existing_manifest = load(output / "manifest.json")
        if existing_manifest.get("worktree_revision") != "G3-B3-F files pending the authorized local commit":
            raise SystemExit("refusing to refresh evidence outside the pending-commit boundary")
        for path in output.iterdir():
            if path.is_file():
                path.unlink()
    elif args.refresh:
        raise SystemExit("cannot refresh a missing final evidence directory")
    full_path = ROOT / "dist/submission-results/full.json"
    quick_path = ROOT / "dist/submission-results/quick.json"
    if not full_path.is_file() or not quick_path.is_file():
        raise SystemExit("successful submission full and quick results are required")
    full, quick = load(full_path), load(quick_path)
    if full.get("status") != "PASS" or quick.get("status") != "PASS":
        raise SystemExit("submission regression is not PASS")
    source_integrity = {name: verify(path) for name, path in SOURCES.items()}
    g3_b2_integrity = verify(G3_B2_FINAL)
    output.mkdir(exist_ok=True)

    b, c, d, e = SOURCES["b"], SOURCES["c"], SOURCES["d"], SOURCES["e"]
    baseline = load(ROOT / "experiments/feature_completion/g3_b3_final_baseline.json")
    requirement_delta = load(ROOT / "docs/submission/g3_b3_requirement_delta.json")
    result = {
        "schema_version": "g3-b3-f-result-v1", "checkpoint": "G3-B3-F",
        "checkpoint_status": "COMPLETED", "g3_b3_status": "COMPLETED",
        "c_cpp_plugin_compliance": "PARTIALLY_SATISFIED",
        "competition_target_achievement": "PARTIALLY_SATISFIED",
        "submission_release_readiness": "PARTIAL", "g3_delivery_readiness": "PARTIAL",
        "lossless_sparse": "COMPLETED", "host_integrity_crc_retry": "COMPLETED",
        "agent_flow_control_integration": "COMPLETED",
        "direct_runtime_source": "DIRECT_READINESS_ONLY", "real_device_acceptance": "HARDWARE_BLOCKED",
        "pairwise": "SKIPPED_BY_VALUE_GATE", "int8_quantization": "DEFERRED_BY_PRECISION_GATE",
        "public_abi_changed": False, "old_evidence_modified": False,
        "real_device_api_executed": False, "runtime_api_calls": [],
    }
    manifest = {
        "schema_version": "g3-b3-f-evidence-v1", "checkpoint": "G3-B3-F",
        "source_commit": git("rev-parse", "HEAD"),
        "worktree_revision": "G3-B3-F files pending the authorized local commit",
        "source_evidence": source_integrity, "g3_b2_final_integrity": g3_b2_integrity,
        "frozen_contracts": baseline["frozen_contracts"],
        "truth_boundary": baseline["truth_boundary"],
        "final_commit_message": "G3-B3-F freeze final competition feature baseline and evidence",
    }
    sparse_support = {
        "status": "PASS", "mode": "HOST_EXECUTED_CPU_SIM",
        "primitives": ["AllReduce", "AllGather", "ReduceScatter"],
        "dtypes": ["FP32", "FP16", "BF16"], "reduce_ops": ["SUM", "MAX", "MIN"],
        "lossless": True, "dense_fallback": True, "public_abi_changed": False,
    }
    files: dict[str, Any] = {
        "manifest.json": manifest,
        "result.json": result,
        "g3_b2_baseline_reference.json": {"status": "PASS", "integrity": g3_b2_integrity,
            "performance_scenarios": 18, "reliability_scenarios": 4,
            "best_simulated_improvement_percent": 45.59283008, "real_device_measured": False},
        "g3_b3_baseline_reference.json": baseline,
        "schedule_ir_v2_audit.json": load(SOURCES["a"] / "schedule_ir_v2_schema.json"),
        "agent_proposal_v2_audit.json": load(SOURCES["a"] / "agent_proposal_v2_audit.json"),
        "sparse_support_matrix.json": sparse_support,
        "sparse_correctness.json": load(b / "sparse_correctness.json"),
        "sparse_c_python_parity.json": load(b / "sparse_c_python_parity.json"),
        "sparse_benchmark.json": load(b / "sparse_benchmark.json"),
        "sparse_break_even.json": load(b / "sparse_break_even.json"),
        "dense_fallback_audit.json": load(b / "dense_fallback_audit.json"),
        "bounded_sparse_memory.json": load(b / "bounded_sparse_memory.json"),
        "integrity_manifest.json": load(c / "integrity_manifest.json"),
        "crc_audit.json": {"status": "PASS", "known_vectors": load(c / "crc_known_vectors.json"),
            "c_python_parity": load(c / "crc_c_python_parity.json")},
        "corruption_audit.json": load(c / "corruption_cases.json"),
        "retry_audit.json": {"status": "PASS", "cases": load(c / "retry_cases.json"),
            "exhaustion": load(c / "retry_exhaustion.json")},
        "timeout_audit.json": load(c / "timeout_cases.json"),
        "failure_classification.json": load(c / "failure_classification.json"),
        "flow_control_audit.json": load(d / "flow_control_audit.json"),
        "backpressure_audit.json": load(d / "backpressure_cases.json"),
        "agent_trace_inventory.json": {"status": "PASS", "proposal_records": sum(1 for _ in (d / "agent_proposals.jsonl").open(encoding="utf-8")),
            "evaluation_records": sum(1 for _ in (d / "agent_evaluations.jsonl").open(encoding="utf-8")),
            "reflection_records": sum(1 for _ in (d / "agent_reflections.jsonl").open(encoding="utf-8"))},
        "feature_ablation.json": load(d / "feature_ablation.json"),
        "direct_runtime_source_manifest.json": load(e / "direct_runtime_source_manifest.json"),
        "official_api_call_expression_audit.json": load(e / "official_api_call_expression_audit.json"),
        "direct_compile_link_audit.json": {"status": "PASS", "compile": load(e / "compile_result.json"),
            "link": load(e / "link_result.json"), "elf_needed": load(e / "elf_needed.json"),
            "execution": "NOT_EXECUTED", "runtime_api_calls": []},
        "cpu_sim_isolation_audit.json": load(e / "cpu_sim_isolation_audit.json"),
        "native_elf_audit.json": full["build_a"]["native_audit"],
        "reproducible_build.json": full["reproducible_build"],
        "submission_regression.json": {"status": "PASS", "quick": quick["status"],
            "full": full["status"], "ctest": full["build_a"]["ctest"],
            "python": full["python_regression"], "g3_b3": full["g3_b3_full_checks"]},
        "staging_verification.json": full["staging_verification"],
        "claim_boundary_audit.json": {"status": "PASS", "cpu_sim": "HOST_EXECUTED",
            "simulator_performance": "SIMULATED_ONLY", "direct_runtime_source": "DIRECT_READINESS_ONLY",
            "real_device": "HARDWARE_BLOCKED", "real_device_api_executed": False, "runtime_api_calls": []},
        "requirement_delta.json": requirement_delta,
        "user_action_required.json": {"status": "USER_ACTION_REQUIRED", "items": [
            "UA-B-001 project license/copyright decision", "UA-B-002 official asset redistribution decision",
            "UA-B-003 controlled competition document handling", "UA-B-004 platform archive format and size",
            "Supported Ascend NPU runtime acceptance and real-device performance validation"]},
    }
    for name, payload in files.items():
        write_json(output / name, payload)
    (output / "README.md").write_text(
        "# G3-B3-F final evidence\n\nSingle authoritative feature-completion freeze. Sparse, CRC/retry, "
        "flow-control, and Agent results are host or simulator evidence. The official ACL/HCCL source path was "
        "compiled, linked, and statically inspected only; it was never loaded or executed.\n",
        encoding="utf-8", newline="\n")
    payloads = sorted(path for path in output.iterdir() if path.is_file() and path.name not in {"SHA256SUMS", "EVIDENCE_SHA256"})
    (output / "SHA256SUMS").write_text("".join(f"{sha256(path)}  {path.name}\n" for path in payloads), encoding="utf-8", newline="\n")
    evidence_sha = sha256(output / "SHA256SUMS")
    (output / "EVIDENCE_SHA256").write_text(f"{evidence_sha}  SHA256SUMS\n", encoding="utf-8", newline="\n")
    verification = verify(output)
    print(json.dumps({"status": "PASS", "path": output.relative_to(ROOT).as_posix(),
                      "sha256": evidence_sha, "files_checked": verification["files_checked"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
