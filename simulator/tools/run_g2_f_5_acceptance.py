#!/usr/bin/env python3
"""Run G2-F-5 simulator-only correctness acceptance and write one evidence set."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from plugin.execution_engine import HCCL_MAX, HCCL_MIN, HCCL_SUM, HCCL_FP32, ExecutionEngine
from simulator.collective_correctness import (
    Case, DTYPE_BYTES, HOST_REFERENCE_REVISION, STRESS_TOLERANCES,
    bf16_boundary_audit, host_allgather, host_allreduce, host_reducescatter,
    representative_cases, run_case,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git_state(path: str) -> dict[str, str]:
    command = ["git", "-c", f"safe.directory={path}", "-C", path]
    return {
        "branch": subprocess.check_output([*command, "branch", "--show-current"], text=True).strip(),
        "commit": subprocess.check_output([*command, "rev-parse", "HEAD"], text=True).strip(),
        "status_short": subprocess.check_output([*command, "status", "--short"], text=True),
    }


def _cpu_sim_cross_check(library: Path) -> dict[str, Any]:
    engine = ExecutionEngine(library_path=str(library))
    allreduce_input = [[1.0, -2.0, 3.0], [4.0, 5.0, -6.0], [7.0, -8.0, 9.0], [10.0, 11.0, -12.0]]
    op_constants = {"SUM": HCCL_SUM, "MAX": HCCL_MAX, "MIN": HCCL_MIN}
    allreduce = {}
    for name, op in op_constants.items():
        result = engine.execute_allreduce_data(allreduce_input, algorithm="Wrapper", op=op, data_type=HCCL_FP32)
        expected = host_allreduce(allreduce_input, name, "FP32")
        allreduce[name] = {"status": result["status"], "matches_host_reference": result["result"] == expected}
    allgather_input = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]]
    gathered = engine.execute_allgather(allgather_input, algorithm="Wrapper", data_type=HCCL_FP32)
    reducescatter_input = [
        [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0], [7.0, 8.0]],
        [[2.0, 3.0], [4.0, 5.0], [6.0, 7.0], [8.0, 9.0]],
        [[3.0, 4.0], [5.0, 6.0], [7.0, 8.0], [9.0, 10.0]],
        [[4.0, 5.0], [6.0, 7.0], [8.0, 9.0], [10.0, 11.0]],
    ]
    flattened = [[value for shard in src for value in shard] for src in reducescatter_input]
    reducescatter = {}
    for name, op in op_constants.items():
        result = engine.execute_reducescatter(reducescatter_input, data_type=HCCL_FP32, op=op)
        expected = host_reducescatter(flattened, name, "FP32")
        reducescatter[name] = {"status": result["status"], "matches_host_reference": result["result"] == expected}
    result = {
        "backend": "CPU_SIM", "rank_size": 4, "dtype": "FP32", "allreduce": allreduce,
        "allgather": {"status": gathered["status"], "matches_host_reference": gathered["result"] == host_allgather(allgather_input, "FP32")},
        "reducescatter": reducescatter,
    }
    if not all(item["status"] == "success" and item["matches_host_reference"] for item in allreduce.values()):
        raise RuntimeError("CPU_SIM AllReduce cross-check failed")
    if result["allgather"]["status"] != "success" or not result["allgather"]["matches_host_reference"]:
        raise RuntimeError("CPU_SIM AllGather cross-check failed")
    if not all(item["status"] == "success" and item["matches_host_reference"] for item in reducescatter.values()):
        raise RuntimeError("CPU_SIM ReduceScatter cross-check failed")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-sim-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f"evidence output already exists: {args.output}")
    cases = representative_cases()
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    records: list[dict[str, Any]] = []
    for case in cases:
        for exact in (True, False):
            record = run_case(case, exact=exact)
            replay = run_case(case, exact=exact)
            if record["output_hash"] != replay["output_hash"] or record["max_abs_error"] != replay["max_abs_error"]:
                raise RuntimeError("non-deterministic simulator replay")
            record["project_commit"] = source_commit
            records.append(record)
    topology_records = []
    for primitive, dtype, op in (("AllReduce", "INT32", "SUM"), ("AllGather", "FP32", None), ("ReduceScatter", "INT32", "MAX")):
        hashes = []
        for topology in ("FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS"):
            hashes.append(run_case(Case(primitive, dtype, op, 8, topology, "1KB", 1024, 424242), exact=True)["output_hash"])
        if len(set(hashes)) != 1:
            raise RuntimeError(f"topology changed {primitive} values")
        topology_records.append({"primitive": primitive, "hashes": hashes, "consistent": True})
    cross_backend = _cpu_sim_cross_check(args.cpu_sim_library)
    by_primitive = {primitive: [record for record in records if record["primitive"] == primitive] for primitive in ("AllReduce", "AllGather", "ReduceScatter")}
    result = {
        "checkpoint": "G2-F-5", "validation_track": "SIMULATOR_ACCEPTANCE", "checkpoint_status": "COMPLETED",
        "simulator_correctness_status": "SIMULATOR_CORRECTNESS_PASS", "source_commit_before_checkpoint": source_commit,
        "real_device_acceptance": "HARDWARE_BLOCKED", "real_device_calibration_status": "UNAVAILABLE_NO_REAL_DEVICE",
        "performance_claim": False, "measured_on_real_npu": False, "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False, "collective_executed_on_real_device": False,
        "runtime_initialized": False, "device_opened": False, "context_created": False, "stream_created": False,
        "communicator_created": False, "device_buffer_allocated": False, "runtime_api_calls": [],
        "competition_simulator_track": "PARTIAL", "g2_f_readiness": "PARTIAL", "overall": "PARTIAL",
    }
    matrix = {"case_count": len(records), "base_case_count": len(cases), "records": records,
              "rank_coverage": sorted({record["rank_size"] for record in records}),
              "dtype_coverage": sorted({record["dtype"] for record in records}),
              "op_coverage": sorted({record["reduce_op"] for record in records if record["reduce_op"]}),
              "topology_coverage": sorted({record["topology"] for record in records}),
              "message_coverage": sorted({record["message_label"] for record in records})}
    assumptions = {"execution_engine": "project-local pure Python simulator acceptance", "performance_claim": False,
                   "real_device_calibration_status": "UNAVAILABLE_NO_REAL_DEVICE", "topology_affects": ["metadata", "future scheduling/performance only"],
                   "topology_does_not_affect": "collective values", "known_limitations": ["FP16/BF16 software rounding only", "logical >=1GB uses sampled streaming windows", "no Ascend hardware accumulation or transport behavior is modeled"]}
    regression = {"simulator_cases": "PASS", "deterministic_replay": "PASS", "cpu_sim_cross_backend": "PASS", "runtime_api_calls": [],
                  "note": "CPU_SIM is an isolated semantic cross-check and is not direct or real-device evidence."}
    args.output.mkdir(parents=True)
    files = {
        "manifest.json": {"schema_version": "g2-f-simulator-correctness-v1", "backend": "SIMULATOR_ACCEPTANCE", "host_reference": HOST_REFERENCE_REVISION, "dtype_bytes": DTYPE_BYTES, "stress_tolerances": STRESS_TOLERANCES, "project_commit": source_commit},
        "result.json": result, "test_matrix.json": matrix,
        "allreduce_correctness.json": {"status": "PASS", "cases": by_primitive["AllReduce"]},
        "allgather_correctness.json": {"status": "PASS", "cases": by_primitive["AllGather"]},
        "reducescatter_correctness.json": {"status": "PASS", "cases": by_primitive["ReduceScatter"]},
        "precision_audit.json": {"strict_exact_dataset": "zero error and explicit 1e-6 check", "random_stress_dataset": "dtype-aware software rounding observed", "stress_tolerances": STRESS_TOLERANCES, "bf16": bf16_boundary_audit()},
        "large_message_audit.json": {"status": "PASS", "logical_large_cases": [record for record in records if record["message_label"] == "logical_1GB"], "strategy": "bounded materialized windows with deterministic streaming hashes"},
        "cross_backend_audit.json": cross_backend, "simulation_assumptions.json": assumptions,
        "regression.json": regression, "official_repositories.json": {"hcomm": _git_state("/home/workspace/hcomm"), "hccl": _git_state("/home/workspace/hccl")},
    }
    for name, value in files.items():
        _write_json(args.output / name, value)
    (args.output / "README.md").write_text("# G2-F-5 Simulator Correctness Evidence\n\nSimulator-only data correctness acceptance. This directory contains no real-device, direct API, performance, or calibration claim.\n", encoding="utf-8")
    checksums = [f"{_sha256(path)}  {path.name}" for path in sorted(args.output.iterdir())]
    (args.output / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
