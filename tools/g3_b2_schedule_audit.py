"""Generate immutable, simulator-only G3-B2-B Schedule IR evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithm.ring_schedule import generate_ring_schedule
from algorithm.schedule_ir import invariant_results


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    evidence = args.evidence_dir if args.evidence_dir.is_absolute() else ROOT / args.evidence_dir
    dump = args.dump if args.dump.is_absolute() else ROOT / args.dump
    if evidence.exists() and any(evidence.iterdir()):
        raise RuntimeError(f"refusing to overwrite evidence: {evidence}")
    evidence.mkdir(parents=True, exist_ok=True)
    inventory = []
    parity = []
    invariant_audit = []
    for primitive in ("AllReduce", "AllGather", "ReduceScatter"):
        for ranks in (2, 4, 8, 16, 64):
            for boundary, size in (("divisible", ranks * 1024), ("non_divisible", ranks * 1024 + 3)):
                expected = generate_ring_schedule(primitive, ranks, size)
                observed = json.loads(subprocess.check_output([str(dump), primitive, str(ranks), str(size), "FP32", "SUM"], text=True))
                equal = observed == expected
                if not equal:
                    raise RuntimeError(f"C/Python parity mismatch: {primitive} ranks={ranks} bytes={size}")
                inventory.append({"primitive": primitive, "algorithm": "Ring", "rank_size": ranks, "message_size_bytes": size, "boundary": boundary, "phase_count": len(expected["phases"]), "schedule_hash": expected["schedule_hash"]})
                parity.append({"primitive": primitive, "rank_size": ranks, "message_size_bytes": size, "python_schedule_hash": expected["schedule_hash"], "c_schedule_hash": observed["schedule_hash"], "canonical_equal": equal})
                invariant_audit.append({"schedule_hash": expected["schedule_hash"], "results": invariant_results(expected), "all_passed": all(row["passed"] for row in invariant_results(expected))})
    schema_path = ROOT / "configs/optimization/g3_b2_schedule_ir_schema.json"
    write_json(evidence / "schedule_inventory.json", inventory)
    write_json(evidence / "invariant_audit.json", invariant_audit)
    write_json(evidence / "c_python_parity.json", parity)
    write_json(evidence / "result.json", {"checkpoint":"G3-B2-B","checkpoint_status":"COMPLETED","schedule_count":len(inventory),"invariant_count_per_schedule":len(invariant_audit[0]["results"]),"all_invariants_passed":all(row["all_passed"] for row in invariant_audit),"c_python_parity_passed":all(row["canonical_equal"] for row in parity),"public_abi_changed":False,"measured_on_real_npu":False,"real_device_api_executed":False,"truth_label":"CPU_EXECUTED"})
    write_json(evidence / "manifest.json", {"schema_version":"g3-b2-b-evidence-v1","schedule_schema_path":schema_path.relative_to(ROOT).as_posix(),"schedule_schema_sha256":sha(schema_path),"schedule_dump_path":dump.relative_to(ROOT).as_posix(),"primitive_count":3,"rank_sizes":[2,4,8,16,64],"boundaries":["divisible","non_divisible"],"fallback_policy":"NONE","truth_labels":["CPU_EXECUTED","SIMULATED_ONLY","REAL_DEVICE_NOT_EXECUTED"]})
    with (evidence / "README.md").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write("# G3-B2-B Schedule IR evidence\n\nCPU-executed canonical parity and invariant evidence for internal Ring schedules. No device or HCCL runtime API was executed.\n")
    files = sorted(path for path in evidence.iterdir() if path.is_file())
    with (evidence / "SHA256SUMS").open("w", encoding="utf-8", newline="\n") as stream:
        for path in files:
            stream.write(f"{sha(path)}  {path.name}\n")
    anchor = sha(evidence / "SHA256SUMS")
    with (evidence / "EVIDENCE_SHA256").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(f"{anchor}  SHA256SUMS\n")
    print(json.dumps({"evidence": evidence.relative_to(ROOT).as_posix(), "sha256": anchor, "schedules": len(inventory), "parity": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
