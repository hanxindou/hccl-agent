"""Run the authorized WSL CPU_SIM/ELF and official-repository static audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "/mnt/f/projects/hccl-agent/scripts/submission_audit/native_static_audit.sh"
EXPECTED_EXPORTS = {
    "hcclAllReduce", "hcclAllGather", "hcclReduceScatter",
    "hcclPluginGetVersion", "hcclPluginGetAlgorithms",
}
EXPECTED_OFFICIAL = {
    "HCOMM": ("competition/campus-2026", "c8a3dc68a37315aa1e908a971fa706abe612f6ee"),
    "HCCL": ("competition/campus-2026", "2c87cc1937bab23b8574ef24017c03572d3340e2"),
}


def collect() -> dict[str, object]:
    proc = subprocess.run(
        ["wsl.exe", "-e", "bash", SCRIPT],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    try:
        stderr = proc.stderr.decode("utf-8")
    except UnicodeDecodeError:
        stderr = proc.stderr.decode("gbk", errors="replace")
    if proc.returncode:
        raise RuntimeError(f"native static audit failed ({proc.returncode}): {stderr.strip()}")
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key] = value
    exports = sorted(filter(None, values["CPU_SIM_EXPORTS"].split(",")))
    missing = sorted(EXPECTED_EXPORTS - set(exports))
    needed = sorted(filter(None, values["CPU_SIM_NEEDED"].split(",")))
    forbidden_needed = sorted(name for name in needed if name in {"libhccl.so", "libhcomm.so", "libacl_rt.so"})
    if missing or forbidden_needed:
        raise RuntimeError(f"CPU_SIM ELF contract failed: missing={missing}, forbidden_needed={forbidden_needed}")
    official: dict[str, object] = {}
    for name, (expected_branch, expected_commit) in EXPECTED_OFFICIAL.items():
        branch = values[f"{name}_BRANCH"]
        commit = values[f"{name}_COMMIT"]
        clean = values[f"{name}_TRACKED_CLEAN"] == "true"
        if branch != expected_branch or commit != expected_commit or not clean:
            raise RuntimeError(
                f"{name} frozen-state mismatch: branch={branch}, commit={commit}, clean={clean}"
            )
        official[name.lower()] = {
            "branch": branch,
            "commit": commit,
            "tracked_worktree_clean": clean,
        }
    return {
        "schema_version": "g3-a-native-static-audit-v1",
        "status": values.get("STATUS"),
        "audit_scope": "CPU_SIM build/CTest/ELF metadata plus read-only HCOMM/HCCL Git state",
        "cpu_sim": {
            "artifact": "/tmp/hccl-g3a-native-audit/libhccl_plugin.so",
            "role": "CPU_SIM_NOT_OFFICIAL_HCCL_DIRECT_PLUGIN",
            "sha256": values["CPU_SIM_SHA256"],
            "exported_symbols": exports,
            "missing_required_exports": missing,
            "needed_libraries": needed,
            "forbidden_official_dependencies": forbidden_needed,
            "ctest_passed": int(values["CPU_SIM_CTEST_PASSED"]),
            "ctest_failed": 0,
        },
        "direct_adapter": {
            "role": "STATIC_COMPILE_LINK_LIFECYCLE_READINESS_ONLY",
            "artifact_from_frozen_evidence": "/tmp/hccl-g2f-build/libhccl_direct_adapter.a",
            "sha256_from_frozen_evidence": "5eebfb97d9a26ffb10c73f58e10c2654a4823dd89afb8b4f2727606309f14c72",
            "final_plugin_so": False,
        },
        "official_repositories": official,
        "real_device_api_executed": False,
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "measured_on_real_npu": False,
        "runtime_api_calls": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = collect()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": payload["status"], "output": str(args.output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
