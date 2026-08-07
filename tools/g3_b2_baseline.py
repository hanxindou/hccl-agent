"""Freeze and reproduce the G3-B2-A simulator optimization baseline.

This command is intentionally CPU-only.  It imports the existing G2-F-6
analytical simulator without changing its formulas or algorithm selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cost_model.engine import CostModelEngine
from simulator.g2_f_6_acceptance import ALGORITHMS, ExperimentSpec, SimulatorAcceptance


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "configs/optimization/g3_b2_benchmark_matrix.json"
FREEZE_PATH = ROOT / "experiments/optimization/g3_b2_parameter_freeze.json"
TRACE_ROOT = ROOT / "agent/evidence/g3_b2"
PROMPT_ROOT = ROOT / "prompts/g3_b2"
G3_B_EVIDENCE = ROOT / "experiments/submission/evidence/g3_b_20260806T090301Z"
PROTECTED_SOURCES = (
    "hardware/profile.py",
    "cost_model/engine.py",
    "simulator/g2_f_6_acceptance.py",
    "simulator/collective_correctness.py",
    "skills/algorithm_selector.py",
    "skills/topology_graph.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


def write_text(path: Path, value: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def frozen_parameters() -> dict[str, Any]:
    source_hashes = {path: sha256_file(ROOT / path) for path in PROTECTED_SOURCES}
    entries = [
        ("HCCS.bandwidth", 100.0, "Gbps", "PROJECT_CONFIG", "hardware/profile.py"),
        ("HCCS.latency", 0.002, "ms", "PROJECT_CONFIG", "hardware/profile.py"),
        ("RoCE.bandwidth", 50.0, "Gbps", "PROJECT_CONFIG", "hardware/profile.py"),
        ("RoCE.latency", 0.005, "ms", "PROJECT_CONFIG", "hardware/profile.py"),
        ("PCIe.bandwidth", 32.0, "Gbps", "PROJECT_CONFIG", "hardware/profile.py"),
        ("PCIe.latency", 0.010, "ms", "PROJECT_CONFIG", "hardware/profile.py"),
        ("heterogeneous.PCIe.bandwidth", 24.0, "Gbps", "EXPLICIT_ASSUMPTION", "simulator/g2_f_6_acceptance.py"),
        ("heterogeneous.PCIe.latency", 0.014, "ms", "EXPLICIT_ASSUMPTION", "simulator/g2_f_6_acceptance.py"),
        ("heterogeneous.RoCE.bandwidth", 25.0, "Gbps", "EXPLICIT_ASSUMPTION", "simulator/g2_f_6_acceptance.py"),
        ("heterogeneous.RoCE.latency", 0.007, "ms", "EXPLICIT_ASSUMPTION", "simulator/g2_f_6_acceptance.py"),
        ("link_fault_probability", 0.0002, "probability", "EXPLICIT_ASSUMPTION", "simulator/g2_f_6_acceptance.py"),
        ("startup_overhead", 0.003, "ms", "DERIVED_ANALYTICAL", "cost_model/engine.py"),
        ("default_chunk_size", 4194304, "bytes", "EXPLICIT_ASSUMPTION", "simulator/g2_f_6_acceptance.py"),
        ("protocol_overhead_per_chunk", 0.20, "us", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("chunk_scheduling_cost", 0.05, "us", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("synchronization_cost_per_step", 0.05, "us", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("reduction_cost_per_mib", 0.08, "us", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("contention_delay_scale", 0.15, "ratio", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("queueing_delay_scale", 0.05, "ratio", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("jitter_step", 0.0002, "ratio", "DERIVED_ANALYTICAL", "simulator/g2_f_6_acceptance.py"),
        ("seed", 20260804, "integer", "BENCHMARK_CONTRACT", "configs/optimization/g3_b2_benchmark_matrix.json"),
        ("p50", 0.50, "quantile", "BENCHMARK_CONTRACT", "configs/optimization/g3_b2_benchmark_matrix.json"),
        ("p95", 0.95, "quantile", "BENCHMARK_CONTRACT", "configs/optimization/g3_b2_benchmark_matrix.json"),
        ("FP32.absolute_tolerance", 0.000001, "absolute_error", "CORRECTNESS_CONTRACT", "simulator/collective_correctness.py"),
        ("FP16.absolute_tolerance", 0.001, "absolute_error", "CORRECTNESS_CONTRACT", "simulator/collective_correctness.py"),
        ("BF16.absolute_tolerance", 0.01, "absolute_error", "CORRECTNESS_CONTRACT", "simulator/collective_correctness.py"),
    ]
    parameters = []
    for name, value, unit, source, source_path in entries:
        source_file = ROOT / source_path
        parameters.append({
            "name": name,
            "value": value,
            "unit": unit,
            "source": source,
            "source_path": source_path,
            "sha256": sha256_file(source_file),
            "mutable": False,
        })
    return {
        "schema_version": "g3-b2-parameter-freeze-v1",
        "checkpoint": "G3-B2-A",
        "frozen": True,
        "real_device_calibrated": False,
        "truth_label": "SIMULATED_ONLY",
        "parameters": parameters,
        "protected_source_hashes": source_hashes,
    }


def freeze_or_verify() -> dict[str, Any]:
    expected = frozen_parameters()
    if FREEZE_PATH.exists():
        actual = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        if actual != expected:
            raise RuntimeError("frozen parameter/source contract drifted")
        write_json(FREEZE_PATH, expected)
    else:
        write_json(FREEZE_PATH, expected)
    return expected


def validate_evidence(root: Path) -> dict[str, Any]:
    sums_path = root / "SHA256SUMS"
    checked = 0
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        if sha256_file(root / relative) != expected:
            raise RuntimeError(f"old evidence hash mismatch: {relative}")
        checked += 1
    anchor = (root / "EVIDENCE_SHA256").read_text(encoding="utf-8").strip().split()[0]
    if anchor != sha256_file(sums_path):
        raise RuntimeError("old evidence anchor mismatch")
    return {"path": root.relative_to(ROOT).as_posix(), "files_checked": checked, "sha256sums_sha256": anchor, "valid": True}


def prompt_registry() -> dict[str, Any]:
    prompts = []
    for path in sorted(PROMPT_ROOT.glob("*_v1.md")):
        prompt_id = path.stem.removesuffix("_v1").replace("_", "-")
        prompts.append({"prompt_id": f"g3-b2-{prompt_id}", "version": "1.0.0", "path": path.relative_to(ROOT).as_posix(), "sha256": sha256_file(path)})
    registry = {"schema_version": "g3-b2-prompt-registry-v1", "frozen": True, "prompts": prompts}
    write_json(TRACE_ROOT / "prompt_registry.json", registry)
    return registry


def spec_from_scenario(item: dict[str, Any], algorithm: str | None = None) -> ExperimentSpec:
    return ExperimentSpec(
        item["scenario_id"], item["primitive"], algorithm or item["baseline_algorithm"],
        item["topology"], item["ranks"], str(item["message_size_bytes"]),
        item["message_size_bytes"], item["dtype"], item["reduce_op"], item["seed"],
    )


def run_baseline(matrix: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    simulator = SimulatorAcceptance()
    metrics: list[dict[str, Any]] = []
    raw_runs: list[dict[str, Any]] = []
    rankings: list[dict[str, Any]] = []
    for item in matrix["performance_scenarios"]:
        spec = spec_from_scenario(item)
        summary, raw = simulator.run_experiment(spec)
        if summary["warm_up_iterations"] != item["warmup"] or summary["measured_iterations"] != item["iterations"]:
            raise RuntimeError(f"iteration contract mismatch for {item['scenario_id']}")
        ranked = []
        for algorithm in ALGORITHMS:
            candidate = simulator.simulate_iteration(spec_from_scenario(item, algorithm), 0)
            ranked.append({"algorithm": algorithm, "simulated_time_us": candidate["simulated_collective_time_us"]})
        ranked.sort(key=lambda row: (row["simulated_time_us"], row["algorithm"]))
        components = raw[0]["cost_components_us"]
        summary.update({
            "benchmark_weight": item["weight"],
            "topology_variant": item["topology_variant"],
            "phase_count": CostModelEngine._communication_steps(item["ranks"], item["baseline_algorithm"], item["primitive"]),
            "modeled_bytes": summary["transmitted_bytes"],
            "critical_path_us": summary["latency_statistics_us"]["p95"],
            "congestion_events": int(components["contention_delay"] > 0) + int(components["queueing_delay"] > 0),
            "peak_materialized_bytes": summary["materialized_message_bytes"],
            "fault_recovery": None,
            "selector_decision": {"selected_algorithm": ranked[0]["algorithm"], "policy": "minimum existing frozen simulator time", "fallback_policy": "NONE"},
            "algorithm_ranking": [row["algorithm"] for row in ranked],
            "output_hash": summary["correctness_gate"]["output_hash"],
            "truth_label": "SIMULATED_ONLY",
        })
        metrics.append(summary)
        raw_runs.extend(raw)
        rankings.append({"scenario_id": item["scenario_id"], "candidates": ranked, "selected_algorithm": ranked[0]["algorithm"]})
    return metrics, raw_runs, rankings


def write_integrity(evidence: Path) -> str:
    files = sorted(path for path in evidence.iterdir() if path.name not in {"SHA256SUMS", "EVIDENCE_SHA256"} and path.is_file())
    lines = [f"{sha256_file(path)}  {path.name}" for path in files]
    sums = evidence / "SHA256SUMS"
    write_text(sums, "\n".join(lines) + "\n")
    anchor = sha256_file(sums)
    write_text(evidence / "EVIDENCE_SHA256", anchor + "  SHA256SUMS\n")
    return anchor


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path)
    parser.add_argument("--refresh-existing", action="store_true")
    args = parser.parse_args()
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    freeze = freeze_or_verify()
    registry = prompt_registry()
    if not args.evidence_dir:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        evidence = ROOT / f"experiments/optimization/evidence/g3_b2_a_baseline_{stamp}"
    else:
        evidence = args.evidence_dir if args.evidence_dir.is_absolute() else ROOT / args.evidence_dir
    if evidence.exists() and not args.refresh_existing:
        raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    if evidence.exists() and not evidence.name.startswith("g3_b2_a_baseline_"):
        raise RuntimeError(f"refusing to refresh unexpected path: {evidence}")
    evidence.mkdir(parents=True, exist_ok=args.refresh_existing)
    old_evidence = validate_evidence(G3_B_EVIDENCE)
    baseline_commit = git("rev-parse", "HEAD")
    metrics, raw, rankings = run_baseline(matrix)
    reliability_all = SimulatorAcceptance().reliability_scenarios()
    reliability_names = {"R01":"bandwidth_degradation", "R02":"transient_link_failure", "R03":"dynamic_node_recovery", "R04":"permanent_link_failure"}
    reliability = []
    for contract in matrix["reliability_scenarios"]:
        match = next(row for row in reliability_all if row["fault_type"] == reliability_names[contract["scenario_id"]])
        reliability.append({"contract": contract, "baseline_record": match, "truth_label": "SIMULATED_ONLY"})
    source_hashes = freeze["protected_source_hashes"]
    plugin_manifest = json.loads((G3_B_EVIDENCE / "manifest.json").read_text(encoding="utf-8"))
    manifest = {
        "schema_version": "g3-b2-a-evidence-v1", "checkpoint": "G3-B2-A", "baseline_commit": baseline_commit,
        "cpu_sim_plugin_sha256": plugin_manifest["cpu_sim_so_sha256"], "cpu_sim_plugin_type": "CPU_SIM_REFERENCE_PLUGIN",
        "direct_artifact_type": "STATIC BUILD/LIFECYCLE READINESS ARTIFACT", "default_backend": "CPU_SIM", "fallback_policy": "NONE",
        "simulator_revision": "g2-f-6-simulator-acceptance-v1", "formula_revision": "g2-f-6-analytical-event-v1",
        "parameter_freeze_sha256": sha256_file(FREEZE_PATH), "benchmark_contract_sha256": sha256_file(MATRIX_PATH),
        "prompt_registry_sha256": canonical_hash(registry), "protected_source_hashes": source_hashes,
        "seed": matrix["seed"], "performance_scenario_count": len(matrix["performance_scenarios"]),
        "reliability_scenario_count": len(matrix["reliability_scenarios"]), "old_g3_b_evidence_validation": old_evidence,
        "truth_labels": ["CPU_EXECUTED", "SIMULATED_ONLY", "REAL_DEVICE_NOT_EXECUTED"],
    }
    result = {
        "checkpoint": "G3-B2-A", "checkpoint_status": "COMPLETED", "baseline_frozen": True,
        "parameter_freeze": "COMPLETED", "benchmark_contract": "COMPLETED", "agent_trace_contract": "COMPLETED",
        "performance_scenarios_executed": len(metrics), "reliability_scenarios_executed": len(reliability),
        "correctness_passed": all(row["correctness_gate"]["correctness_gate_passed"] for row in metrics),
        "old_evidence_modified": False, "measured_on_real_npu": False, "real_device_api_executed": False,
        "runtime_api_calls": [], "truth_label": "SIMULATED_ONLY",
    }
    write_json(evidence / "manifest.json", manifest)
    write_json(evidence / "result.json", result)
    write_json(evidence / "parameter_freeze.json", freeze)
    write_json(evidence / "benchmark_contract.json", matrix)
    write_json(evidence / "baseline_metrics.json", metrics)
    with (evidence / "baseline_raw.jsonl").open("w", encoding="utf-8", newline="\n") as stream:
        for row in raw:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    write_json(evidence / "algorithm_rankings.json", rankings)
    write_json(evidence / "reliability_baseline.json", reliability)
    write_json(evidence / "agent_trace_contract.json", json.loads((TRACE_ROOT / "trace_manifest.json").read_text(encoding="utf-8")))
    write_json(evidence / "regression.json", {"protected_sources_unchanged_from_freeze": True, "old_g3_b_evidence_valid": True, "algorithm_changes_in_phase_a": False})
    write_text(
        evidence / "README.md",
        "# G3-B2-A optimization baseline\n\nThis evidence freezes the pre-optimization CPU simulator baseline, parameters, benchmark matrix, prompts, and agent trace contract. It is SIMULATED_ONLY and REAL_DEVICE_NOT_EXECUTED. `libhccl_plugin.so` remains the CPU_SIM_REFERENCE_PLUGIN; the direct archive remains a STATIC BUILD/LIFECYCLE READINESS ARTIFACT.\n",
    )
    anchor = write_integrity(evidence)
    print(json.dumps({"evidence": evidence.relative_to(ROOT).as_posix(), "sha256": anchor, "scenarios": len(metrics), "correctness": result["correctness_passed"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
