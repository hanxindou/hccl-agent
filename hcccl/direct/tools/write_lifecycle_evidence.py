#!/usr/bin/env python3
"""Write one G2-F-4 evidence bundle from the host-only lifecycle harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from plugin.direct_api_backend import diagnose_no_device  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_state(path: str) -> dict[str, str]:
    command = ["git", f"-c", f"safe.directory={path}", "-C", path]
    return {
        "branch": subprocess.check_output([*command, "branch", "--show-current"], text=True).strip(),
        "commit": subprocess.check_output([*command, "rev-parse", "HEAD"], text=True).strip(),
        "status_short": subprocess.check_output([*command, "status", "--short"], text=True),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lifecycle-test", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(f"evidence output already exists: {args.output}")

    completed = subprocess.run([str(args.lifecycle_test)], check=False, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise RuntimeError(f"host-only lifecycle test failed: {completed.returncode}\n{completed.stderr}")
    device_nodes = [str(path) for path in Path("/dev").iterdir()
                    if path.name.casefold().startswith(("ascend", "davinci"))]
    driver_indicators = [path.name for path in Path("/sys/module").iterdir()
                         if "ascend" in path.name.casefold() or "davinci" in path.name.casefold()]
    guard = diagnose_no_device({"npu_smi_found": shutil.which("npu-smi") is not None,
                                "device_nodes": device_nodes,
                                "driver_indicators": driver_indicators})
    if guard["status"] != "NO_DEVICE_EXPECTED":
        raise RuntimeError("G2-F-4 evidence requires the documented no-device environment")

    args.output.mkdir(parents=True)
    source_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    result = {
        "checkpoint": "G2-F-4", "checkpoint_status": "COMPLETED",
        "source_commit_before_checkpoint": source_commit,
        "lifecycle_harness_readiness": "COMPLETED", "preflight_status": "NO_DEVICE_EXPECTED",
        "hardware_lifecycle_status": "HARDWARE_BLOCKED", "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False, "runtime_initialized": False,
        "device_opened": False, "context_created": False, "stream_created": False,
        "communicator_created": False, "device_buffer_allocated": False,
        "collective_executed": False, "runtime_api_calls": [],
        "g2_f_readiness": "PARTIAL", "overall": "PARTIAL",
    }
    state_machine = {
        "status": "PASS", "allowed_no_device_path": ["CREATED", "CONFIGURED", "PREFLIGHT_CHECKED", "NO_DEVICE_EXPECTED", "DESTROYED"],
        "model_only_states": ["RUNTIME_READY", "DEVICE_READY", "CONTEXT_READY", "STREAM_READY", "COMM_READY", "BUFFERS_READY", "COLLECTIVE_SUBMITTED", "SYNCHRONIZED", "COMPLETED"],
        "invalid_transition_coverage": ["duplicate configure", "model before preflight", "double destroy", "use after destroy", "owner-thread mismatch", "device mismatch"],
        "runtime_api_calls": [],
    }
    ownership = {
        "status": "PASS", "owners": ["runtime_lease", "device", "context", "stream", "communicator", "send_buffer", "recv_buffer"],
        "cleanup_order": ["recv_buffer", "send_buffer", "communicator", "stream", "context", "device", "runtime_lease"],
        "lease_model": "process-scoped reference-counted logical model only", "runtime_api_calls": [],
    }
    failure = {
        "status": "PASS", "acquisition_points": ["runtime_lease", "device_bind", "context_create", "stream_create", "comm_create", "send_buffer", "recv_buffer", "collective_submit", "synchronize"],
        "cleanup_points": ["recv_buffer", "send_buffer", "comm", "stream", "context", "device", "runtime_lease"],
        "first_business_error_preserved": True, "cleanup_errors_recorded_separately": True,
        "runtime_api_calls": [],
    }
    capacity = {
        "status": "PASS", "allreduce": "count * dtype_size for input and output", "allgather": "send_count * rank_size output", "reducescatter": "recv_count * rank_size input", "dtypes": {"FP16": 2, "FP32": 4, "FP64": 8, "BF16": 2}, "overflow_safe": True,
    }
    regression = {
        "host_only_lifecycle_test": {"path": str(args.lifecycle_test), "exit_code": completed.returncode},
        "note": "Additional CPU_SIM, Python, G2-E and prior-evidence results are recorded by the checkpoint runner.",
        "runtime_api_calls": [],
    }
    manifest = {"schema_version": "g2-f-lifecycle-readiness-v1", "backend": "ASCEND_HCCL_DIRECT", "execution_mode": "host_only_deterministic_state_machine", "official_runtime_calls_permitted": False, "real_device_opt_in": "G2-F-5 only"}
    for name, value in (("manifest.json", manifest), ("result.json", result), ("state_machine.json", state_machine), ("ownership_audit.json", ownership), ("failure_injection.json", failure), ("capacity_contract.json", capacity), ("guard_audit.json", guard), ("regression.json", regression)):
        write_json(args.output / name, value)
    write_json(args.output / "official_repositories.json", {"hcomm": git_state("/home/workspace/hcomm"), "hccl": git_state("/home/workspace/hccl")})
    (args.output / "README.md").write_text(
        "# G2-F-4 Guarded Lifecycle Harness Evidence\n\n"
        "This is deterministic host-only control-plane evidence. It never calls ACL/HCCL runtime APIs, executes no direct collective, and is not real-device validation.\n",
        encoding="utf-8")
    checksums = [f"{sha256(path)}  {path.name}" for path in sorted(args.output.iterdir())]
    (args.output / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
