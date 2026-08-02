#!/usr/bin/env python3
"""Read-only G2-F-3 link/symbol/dependency audit and no-device evidence writer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[2]
sys.path.insert(0, str(TOOL_DIR))
sys.path.insert(0, str(REPO_ROOT))

from verify_manifest import load_manifest, verify_manifest, verify_repositories  # noqa: E402
from plugin.direct_api_backend import diagnose_no_device  # noqa: E402


def _run(command: list[str]) -> str:
    completed = subprocess.run(command, check=True, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    return completed.stdout


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _needed(readelf_dynamic: str) -> list[str]:
    marker = "Shared library: ["
    return [line.split(marker, 1)[1].split("]", 1)[0]
            for line in readelf_dynamic.splitlines() if marker in line]


def _cann_version(cann_root: Path) -> str:
    version_header = cann_root / "x86_64-linux/include/version/hccl_version.h"
    for line in version_header.read_text(encoding="utf-8").splitlines():
        if "HCCL_VERSION_STR" in line:
            return line.split('"', 2)[1]
    raise ValueError("HCCL_VERSION_STR not found in frozen version header")


def _library_audit(manifest: dict[str, Any], cann_root: Path) -> list[dict[str, Any]]:
    result = []
    for entry in manifest["libraries"]:
        path = Path(entry["path"].format(cann_root=str(cann_root))).resolve()
        dynamic = _run(["readelf", "-d", str(path)])
        result.append({
            "name": entry["name"],
            "canonical_realpath": str(path),
            "sha256": _sha256(path),
            "soname": entry["soname"],
            "observed_needed": _needed(dynamic),
        })
    return result


def _ldd_in_child_shell(cann_root: Path, artifact: Path) -> str:
    command = ". " + shlex.quote(str(cann_root / "set_env.sh")) + " && ldd " + shlex.quote(str(artifact))
    return _run(["bash", "-lc", command])


def _hardware_probe() -> dict[str, Any]:
    dev = Path("/dev")
    nodes = sorted(str(path) for path in dev.iterdir()
                   if path.name.casefold().startswith(("davinci", "ascend")))
    module_root = Path("/sys/module")
    indicators = sorted(path.name for path in module_root.iterdir()
                        if "ascend" in path.name.casefold() or "davinci" in path.name.casefold())
    return {
        "npu_smi_found": shutil.which("npu-smi") is not None,
        "device_nodes": nodes,
        "driver_indicators": indicators,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cann-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--link-line", type=Path, required=True)
    parser.add_argument("--cmake-configure", default="not captured")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    output = args.output
    if output.exists():
        raise ValueError(f"evidence output already exists: {output}")
    manifest = load_manifest(args.manifest)
    cann_root = args.cann_root.resolve()
    artifact = args.artifact.resolve()
    link_dynamic = _run(["readelf", "-d", str(artifact)])
    artifact_needed = _needed(link_dynamic)
    expected_needed = [entry["soname"] for entry in manifest["libraries"]]
    if not all(name in artifact_needed for name in expected_needed):
        raise ValueError("linked artifact is missing one or more frozen official NEEDED entries")
    ldd_output = _ldd_in_child_shell(cann_root, artifact)
    if "not found" in ldd_output:
        raise ValueError("ldd has unresolved transitive dependencies")

    symbol_result = verify_manifest(manifest, cann_root)
    repository_result = verify_repositories(manifest)
    no_device = diagnose_no_device(_hardware_probe())
    if no_device["status"] != "NO_DEVICE_EXPECTED":
        raise ValueError("G2-F-3 evidence is only valid for the current no-device environment")
    if not symbol_result["passed"] or not repository_result["passed"]:
        raise ValueError("frozen manifest or official repository verification failed")

    output.mkdir(parents=True)
    libraries = _library_audit(manifest, cann_root)
    link_line = args.link_line.read_text(encoding="utf-8").strip()
    build_link = {
        "status": "LINK_PASS",
        "artifact": {"canonical_realpath": str(artifact), "sha256": _sha256(artifact)},
        "cann_root": str(cann_root),
        "cann_version": _cann_version(cann_root),
        "cmake_configure": args.cmake_configure,
        "compiler": link_line.split()[0],
        "link_line": link_line,
        "readelf_needed": artifact_needed,
        "official_libraries": libraries,
        "dynamic_load": {"status": "DYNAMIC_LOAD_NOT_EXECUTED", "safety_basis": "No official contract proves dlopen side-effect-free."},
        "runtime_api_calls": [],
    }
    dependency_audit = {
        "status": "LINK_PASS",
        "ldd_command": "source set_env.sh in a child shell, then ldd linked artifact",
        "ldd_output": ldd_output,
        "resolved_only_from_cann_root": all(str(cann_root) in line for line in ldd_output.splitlines()
                                             if "libhccl.so" in line or "libhcomm.so" in line or "libacl_rt.so" in line),
        "runtime_api_calls": [],
    }
    source_commit = _run(["git", "rev-parse", "HEAD"]).strip()
    result = {
        "schema_version": "g2-f-readiness-v1",
        "checkpoint": "G2-F-3",
        "status": "COMPLETED",
        "source_commit_before_checkpoint": source_commit,
        "g2_f_readiness": "PARTIAL",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "overall": "PARTIAL",
        "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False,
        "runtime_api_calls": [],
    }
    regression = {
        "note": "Command results are recorded by the checkpoint runner; this evidence writer performs no CPU_SIM, HCCL-VM, MPI, or hccl_test execution.",
        "cpu_sim": "PASS_RECORDED_SEPARATELY",
        "g2_e": "PASS_RECORDED_SEPARATELY",
        "runtime_api_calls": [],
    }
    _write_json(output / "manifest.json", manifest)
    _write_json(output / "result.json", result)
    _write_json(output / "build_link.json", build_link)
    _write_json(output / "symbol_inventory.json", {"status": "SYMBOL_DISCOVERY_PASS", **symbol_result})
    _write_json(output / "dependency_audit.json", dependency_audit)
    _write_json(output / "no_device_diagnose.json", no_device)
    _write_json(output / "regression.json", regression)
    (output / "README.md").write_text(
        "# G2-F-3 Direct Link and No-device Readiness Evidence\n\n"
        "- Linked ELF inspection only; it was never executed.\n"
        "- Dynamic loading was not executed because its no-side-effect safety is unproven.\n"
        "- No ACL/HCCL runtime API, device, communicator, buffer, collective, HCCL-VM, MPI, or hccl_test operation was run.\n"
        "- The no-device result is `NO_DEVICE_EXPECTED`, not real-device validation.\n",
        encoding="utf-8",
    )
    checksums = [f"{_sha256(path)}  {path.name}" for path in sorted(output.iterdir())]
    (output / "SHA256SUMS").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
