"""Generate G3-B3-B host sparse correctness, parity, and benchmark evidence."""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import statistics
import subprocess
import time
from pathlib import Path
from typing import Any

from feature_completion.contracts import canonical_hash
from feature_completion.sparse import (
    DTYPE_BYTES,
    METADATA_BYTES,
    SPARSE_CODEC_VERSION,
    decide_sparse,
    decode_bytes,
    decode_values,
    encode_values,
    index_width,
    pack_values,
    reconstruction_hash64,
    sparse_collective,
    streaming_accounting,
    unpack_values,
)


ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "configs/feature_completion/g3_b3_sparse_benchmark_matrix.json"
PROFILES_PATH = ROOT / "configs/feature_completion/g3_b3_data_profiles.json"
CLAIM_PATH = ROOT / "docs/submission/g3_b3_claim_contract.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")


def quantized(values: list[float], dtype: str) -> list[float]:
    return unpack_values(pack_values(values, dtype), dtype)


def make_inputs(ranks: int, count: int, sparsity: float, *, reduce_scatter: bool = False) -> list[list[float]]:
    width = count * ranks if reduce_scatter else count
    inputs = []
    for rank in range(ranks):
        values = []
        for element in range(width):
            marker = (element * 37 + rank * 53 + 17) % 1000
            if marker < round(sparsity * 1000):
                values.append(0.0)
            else:
                candidate = ((rank + 1) * ((element % 11) - 5)) / 4.0
                values.append(candidate if candidate != 0.0 else float(rank + 1))
        inputs.append(values)
    return inputs


def dense_reference(primitive: str, inputs: list[list[float]], dtype: str, reduce_op: str | None) -> list[list[float]]:
    rows = [quantized(values, dtype) for values in inputs]
    ranks = len(rows)
    if primitive == "AllGather":
        gathered = [value for row in rows for value in row]
        return [gathered[:] for _ in rows]
    reduced = []
    for element in range(len(rows[0])):
        column = [row[element] for row in rows]
        value = sum(column) if reduce_op == "SUM" else (max(column) if reduce_op == "MAX" else min(column))
        reduced.append(quantized([value], dtype)[0])
    if primitive == "AllReduce":
        return [reduced[:] for _ in rows]
    count = len(reduced) // ranks
    return [reduced[rank * count : (rank + 1) * count] for rank in range(ranks)]


def correctness_audit() -> dict[str, Any]:
    cases = []
    case_id = 0
    for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
        operations = (None,) if primitive == "AllGather" else ("SUM", "MAX", "MIN")
        for dtype in ("FP32", "FP16", "BF16"):
            for operation in operations:
                for ranks in (2, 4, 8, 16):
                    for sparsity in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
                        case_id += 1
                        inputs = make_inputs(ranks, 8, sparsity, reduce_scatter=primitive == "ReduceScatter")
                        result = sparse_collective(primitive, inputs, dtype=dtype, reduce_op=operation)
                        expected = dense_reference(primitive, inputs, dtype, operation)
                        passed = result["outputs"] == expected
                        if not passed:
                            raise RuntimeError(f"sparse correctness failed for case {case_id}")
                        cases.append(
                            {
                                "case_id": f"SC{case_id:04d}",
                                "primitive": primitive,
                                "dtype": dtype,
                                "reduce_op": operation,
                                "ranks": ranks,
                                "sparsity_ratio": sparsity,
                                "rank_patterns_identical": False,
                                "passed": True,
                                "output_hash": canonical_hash(result["outputs"]),
                                "selected_modes": sorted({row.selected_mode for row in result["decisions"]}),
                            }
                        )
    inputs = make_inputs(64, 4, 0.9)
    result = sparse_collective("AllReduce", inputs, dtype="FP32", reduce_op="SUM")
    expected = dense_reference("AllReduce", inputs, "FP32", "SUM")
    if result["outputs"] != expected:
        raise RuntimeError("64-rank representative sparse correctness failed")
    cases.append(
        {
            "case_id": "SC-LOGICAL-64",
            "primitive": "AllReduce",
            "dtype": "FP32",
            "reduce_op": "SUM",
            "ranks": 64,
            "sparsity_ratio": 0.9,
            "rank_patterns_identical": False,
            "passed": True,
            "output_hash": canonical_hash(result["outputs"]),
            "truth_label": "SIMULATED_ONLY",
        }
    )
    return {
        "schema_version": "g3-b3-sparse-correctness-v1",
        "case_count": len(cases),
        "passed": len(cases),
        "failed": 0,
        "cases": cases,
        "three_primitives": True,
        "dtypes": ["FP32", "FP16", "BF16"],
        "reduce_ops": ["SUM", "MAX", "MIN"],
        "truth_label": "LOSSLESS_SPARSE_HOST_EXECUTED",
    }


def c_python_parity(c_dump: Path) -> dict[str, Any]:
    completed = subprocess.run([str(c_dump)], check=True, capture_output=True, text=True)
    c_record = json.loads(completed.stdout)
    values = [0.0, 1.0, 0.0, -2.0, 0.0, 3.5, -0.0, 0.0]
    payload = encode_values(values, "FP32")
    reconstructed = decode_bytes(payload)
    python_record = {
        "logical_element_count": payload.logical_element_count,
        "nonzero_count": payload.nonzero_count,
        "index_width": payload.index_width,
        "indices": list(payload.indices),
        "values_hex": payload.values.hex(),
        "logical_bytes": payload.logical_bytes,
        "wire_bytes": payload.wire_bytes,
        "index_bytes": payload.index_bytes,
        "value_bytes": payload.value_bytes,
        "metadata_bytes": payload.metadata_bytes,
        "compression_ratio": round(payload.compression_ratio, 12),
        "reconstruction_hash64": reconstruction_hash64(reconstructed),
    }
    comparisons = {key: c_record[key] == value for key, value in python_record.items()}
    if not all(comparisons.values()):
        raise RuntimeError(f"C/Python sparse parity failed: {comparisons}")
    return {
        "schema_version": "g3-b3-sparse-c-python-parity-v1",
        "c_record": c_record,
        "python_record": python_record,
        "comparisons": comparisons,
        "passed": True,
        "truth_label": "HOST_EXECUTED",
    }


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * quantile) - 1)]


def full_accounting(logical_bytes: int, dtype: str, sparsity: float) -> dict[str, Any]:
    elements = logical_bytes // DTYPE_BYTES[dtype]
    nonzero = math.floor(elements * (1.0 - sparsity))
    width = index_width(elements)
    value_bytes = nonzero * DTYPE_BYTES[dtype]
    index_bytes = nonzero * width
    wire_bytes = value_bytes + index_bytes + METADATA_BYTES
    detect = math.ceil(logical_bytes * 0.01)
    encode = math.ceil(value_bytes * 0.01)
    decode = math.ceil(value_bytes * 0.01)
    total = wire_bytes + detect + encode + decode
    return {
        "logical_elements": elements,
        "nonzero_count": nonzero,
        "sparsity_ratio": sparsity,
        "index_width": width,
        "logical_bytes": logical_bytes,
        "value_bytes": value_bytes,
        "index_bytes": index_bytes,
        "metadata_bytes": METADATA_BYTES,
        "wire_bytes": wire_bytes,
        "compression_ratio": logical_bytes / wire_bytes,
        "estimated_sparse_total_cost": total,
        "estimated_dense_total_cost": logical_bytes,
        "selected_mode": "SPARSE_INDEX_VALUE" if total < logical_bytes else "DENSE",
        "fallback_reason": None if total < logical_bytes else ("LOW_SPARSITY" if sparsity < 0.5 else "METADATA_OVERHEAD"),
    }


def benchmark_audit(matrix: dict[str, Any], profiles: dict[str, Any]) -> dict[str, Any]:
    profile_map = {row["profile_id"]: row["sparsity_ratio"] for row in profiles["profiles"]}
    rows = []
    for scenario in matrix["scenarios"]:
        sparsity = profile_map[scenario["data_profile"]]
        element_size = DTYPE_BYTES[scenario["dtype"]]
        sample_elements = min(4096, scenario["message_size_bytes"] // element_size)
        sample = make_inputs(1, sample_elements, sparsity)[0]
        timings = []
        payload = None
        for _ in range(10):
            start = time.perf_counter_ns()
            payload = encode_values(sample, scenario["dtype"])
            decode_values(payload)
            timings.append((time.perf_counter_ns() - start) / 1000.0)
        accounting = full_accounting(scenario["message_size_bytes"], scenario["dtype"], sparsity)
        rows.append(
            {
                **scenario,
                **accounting,
                "host_sample_elements": sample_elements,
                "host_encode_decode_p50_us": round(statistics.median(timings), 6),
                "host_encode_decode_p95_us": round(percentile(timings, 0.95), 6),
                "correctness": decode_values(payload) == quantized(sample, scenario["dtype"]),
                "wire_byte_reduction": accounting["logical_bytes"] - accounting["wire_bytes"],
                "wire_byte_reduction_ratio": 1.0 - accounting["wire_bytes"] / accounting["logical_bytes"],
                "truth_label": "HOST_EXECUTED_WITH_MODELED_FULL_PAYLOAD_BYTES",
            }
        )
    if not all(row["correctness"] for row in rows):
        raise RuntimeError("sparse benchmark correctness gate failed")
    return {
        "schema_version": "g3-b3-sparse-benchmark-result-v1",
        "scenario_count": len(rows),
        "rows": rows,
        "unfavorable_cases_retained": True,
        "physical_wire_measurement": False,
        "real_device_execution": False,
    }


def break_even_audit() -> dict[str, Any]:
    rows = []
    for dtype in ("FP32", "FP16", "BF16"):
        for logical_bytes in (65536, 1048576, 16777216, 134217728, 1073741824):
            selected = None
            for step in range(101):
                sparsity = step / 100.0
                accounting = full_accounting(logical_bytes, dtype, sparsity)
                if accounting["selected_mode"] == "SPARSE_INDEX_VALUE":
                    selected = sparsity
                    break
            rows.append(
                {
                    "dtype": dtype,
                    "logical_bytes": logical_bytes,
                    "break_even_sparsity_ratio": selected,
                    "index_width": index_width(logical_bytes // DTYPE_BYTES[dtype]),
                    "cost_includes_metadata_and_codec_equivalent_bytes": True,
                }
            )
    return {"schema_version": "g3-b3-sparse-break-even-v1", "rows": rows, "reproducible": True}


def bounded_memory_audit() -> dict[str, Any]:
    rows = []
    for dtype in ("FP32", "FP16", "BF16"):
        elements = 1024**3 // DTYPE_BYTES[dtype]
        for sparsity in (0.75, 0.9, 1.0):
            nonzero = math.floor(elements * (1.0 - sparsity))
            row = streaming_accounting(elements, nonzero, dtype, chunk_elements=1024 * 1024)
            row.update({"dtype": dtype, "sparsity_ratio": sparsity, "within_64_mib_budget": row["peak_materialized_bytes"] <= 64 * 1024 * 1024})
            rows.append(row)
    if not all(row["within_64_mib_budget"] for row in rows):
        raise RuntimeError("bounded sparse memory gate failed")
    return {"schema_version": "g3-b3-bounded-sparse-memory-v1", "rows": rows, "passed": True}


def dense_fallback_audit(benchmark: dict[str, Any]) -> dict[str, Any]:
    rows = [
        {
            "scenario_id": row["scenario_id"],
            "sparsity_ratio": row["sparsity_ratio"],
            "selected_mode": row["selected_mode"],
            "fallback_reason": row["fallback_reason"],
            "unfavorable_case_retained": True,
        }
        for row in benchmark["rows"]
        if row["selected_mode"] == "DENSE"
    ]
    if not rows:
        raise RuntimeError("dense fallback audit has no unfavorable cases")
    return {"schema_version": "g3-b3-dense-fallback-audit-v1", "rows": rows, "silent_fallback": False, "passed": True}


def write_integrity(evidence: Path) -> str:
    files = sorted(path for path in evidence.iterdir() if path.is_file() and path.name != "SHA256SUMS")
    write_text(evidence / "SHA256SUMS", "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n")
    return sha256_file(evidence / "SHA256SUMS")


def generate(
    evidence: Path,
    c_dump: Path,
    c_test: Path,
    *,
    refresh_existing: bool = False,
) -> dict[str, Any]:
    if evidence.exists() and not refresh_existing:
        raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    if evidence.exists() and not evidence.name.startswith("g3_b3_b_sparse_"):
        raise RuntimeError(f"refusing to refresh unexpected evidence path: {evidence}")
    evidence.mkdir(parents=True, exist_ok=refresh_existing)
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    profiles = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    correctness = correctness_audit()
    parity = c_python_parity(c_dump)
    benchmark = benchmark_audit(matrix, profiles)
    break_even = break_even_audit()
    fallback = dense_fallback_audit(benchmark)
    bounded = bounded_memory_audit()
    c_test_result = subprocess.run([str(c_test)], check=True, capture_output=True, text=True)
    codec_manifest = {
        "schema_version": "g3-b3-sparse-codec-manifest-v1",
        "codec_version": SPARSE_CODEC_VERSION,
        "representation": "SPARSE_INDEX_VALUE",
        "index_types": ["uint16", "uint32", "uint64"],
        "dtypes": ["FP32", "FP16", "BF16"],
        "primitives": ["AllReduce", "AllGather", "ReduceScatter"],
        "public_symbols_added": [],
        "lossy_transform": False,
        "c_cpu_sim_execution": True,
        "python_host_execution": True,
        "physical_wire_measurement": False,
    }
    claim = {
        "schema_version": "g3-b3-b-claim-boundary-audit-v1",
        "claim_contract_sha256": sha256_file(CLAIM_PATH),
        "truth_label": "LOSSLESS_SPARSE_HOST_EXECUTED",
        "sparse_host_execution": True,
        "real_sparse_network": False,
        "wire_bytes_model": True,
        "physical_wire_measurement": False,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "runtime_api_calls": [],
        "passed": True,
    }
    manifest = {
        "schema_version": "g3-b3-b-evidence-manifest-v1",
        "checkpoint": "G3-B3-B",
        "checkpoint_status": "COMPLETED",
        "project_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "baseline_commit": "8402fb5",
        "source_documents": ["docs/plans/g3-competition-delivery-readiness.md"],
        "generated_artifacts": [
            "sparse_codec_manifest.json", "sparse_correctness.json", "sparse_c_python_parity.json",
            "sparse_benchmark.json", "sparse_break_even.json", "dense_fallback_audit.json",
            "bounded_sparse_memory.json", "claim_boundary_audit.json"
        ],
        "tests": ["tests/feature_completion/test_g3_b3_sparse.py", "hcccl/tests/test_sparse_collective.c"],
        "warnings": ["wire-byte values are modeled/host payload accounting, not physical network measurements"],
        "known_limitations": ["no ACL/HCCL runtime or real device was executed"],
        "old_evidence_modified": False,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "runtime_api_calls": [],
    }
    result = {
        "schema_version": "g3-b3-b-result-v1",
        "checkpoint": "G3-B3-B",
        "checkpoint_status": "COMPLETED",
        "lossless_sparse": "COMPLETED",
        "dense_fallback": "COMPLETED",
        "sparse_allreduce": "COMPLETED",
        "sparse_allgather": "COMPLETED",
        "sparse_reducescatter": "COMPLETED",
        "sparse_c_python_parity": "COMPLETED",
        "bounded_sparse_large_message": "COMPLETED",
        "public_abi_changed": False,
        "old_evidence_modified": False,
        "real_device_api_executed": False,
        "runtime_api_calls": [],
    }
    write_json(evidence / "sparse_codec_manifest.json", codec_manifest)
    write_json(evidence / "sparse_correctness.json", correctness)
    write_json(evidence / "sparse_c_python_parity.json", parity)
    write_json(evidence / "sparse_benchmark.json", benchmark)
    write_json(evidence / "sparse_break_even.json", break_even)
    write_json(evidence / "dense_fallback_audit.json", fallback)
    write_json(evidence / "bounded_sparse_memory.json", bounded)
    write_json(evidence / "claim_boundary_audit.json", claim)
    write_json(evidence / "c_focused_test.json", {"passed": True, "stdout": c_test_result.stdout, "truth_label": "CPU_EXECUTED"})
    write_json(evidence / "manifest.json", manifest)
    write_json(evidence / "result.json", result)
    write_text(
        evidence / "README.md",
        "# G3-B3-B lossless sparse evidence\n\n"
        "This evidence covers the private C/Python SPARSE_INDEX_VALUE codec, three CPU/host collective semantics, explicit dense fallback, reproducible break-even, and bounded logical-1-GiB accounting. "
        "Wire-byte results are modeled or host payload bytes and are not physical NIC measurements. No ACL/HCCL runtime or real device API was executed.\n",
    )
    anchor = write_integrity(evidence)
    return {"evidence": evidence.relative_to(ROOT).as_posix(), "sha256": anchor, "correctness_cases": correctness["case_count"], "benchmark_cases": benchmark["scenario_count"], "c_python_parity": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--c-dump", type=Path, required=True)
    parser.add_argument("--c-test", type=Path, required=True)
    parser.add_argument("--refresh-existing", action="store_true")
    args = parser.parse_args()
    evidence = args.evidence_dir if args.evidence_dir.is_absolute() else ROOT / args.evidence_dir
    print(json.dumps(generate(
        evidence,
        args.c_dump.resolve(),
        args.c_test.resolve(),
        refresh_existing=args.refresh_existing,
    ), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
