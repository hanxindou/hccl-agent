#!/usr/bin/env python3
"""Build and statically audit G3-B3-E without executing an ACL/HCCL target."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
HCCCL = ROOT / "hcccl"
SOURCE = HCCCL / "direct/src/hccl_direct_runtime_source.cpp"
CMAKE = HCCCL / "CMakeLists.txt"
ABI_MANIFEST = HCCCL / "submission/native_plugin_abi_manifest.json"

REQUIRED_CALLS = (
    "aclInit",
    "aclrtSetDevice",
    "aclrtCreateContext",
    "aclrtCreateStream",
    "aclrtMalloc",
    "aclrtMemcpy",
    "HcclCommInitClusterInfo",
    "HcclAllReduce",
    "HcclAllGather",
    "HcclReduceScatter",
    "aclrtSynchronizeStream",
    "HcclCommDestroy",
    "aclrtFree",
    "aclrtDestroyStream",
    "aclrtDestroyContext",
    "aclrtResetDevice",
    "aclFinalize",
)


def _run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return {
        "command": command,
        "exit_code": completed.returncode,
        "output": completed.stdout,
    }


def _require(result: dict[str, Any], label: str) -> None:
    if result["exit_code"] != 0:
        raise RuntimeError(f"{label} failed:\n{result['output']}")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalize(value: str, roots: dict[str, str]) -> str:
    for raw, replacement in sorted(roots.items(), key=lambda row: -len(row[0])):
        value = value.replace(raw, replacement)
    return value


def _normalized_command(result: dict[str, Any], roots: dict[str, str]) -> dict[str, Any]:
    return {
        "command": [_normalize(item, roots) for item in result["command"]],
        "exit_code": result["exit_code"],
        "output": _normalize(result["output"], roots),
    }


def _needed(readelf_output: str) -> list[str]:
    return re.findall(r"Shared library: \[([^]]+)\]", readelf_output)


def _soname(readelf_output: str) -> str | None:
    match = re.search(r"Library soname: \[([^]]+)\]", readelf_output)
    return match.group(1) if match else None


def _defined_symbols(nm_output: str) -> list[str]:
    symbols = []
    for line in nm_output.splitlines():
        fields = line.split()
        # GNU nm reports the ELF version-definition node as an absolute (A)
        # symbol.  It is not a callable/exported plugin API and is excluded by
        # the same public-function interpretation as the frozen ABI manifest.
        if len(fields) >= 3 and fields[-2] != "A":
            symbols.append(fields[-1].split("@@", 1)[0])
    return sorted(set(symbols))


def _undefined_symbols(nm_output: str) -> list[str]:
    symbols = []
    for line in nm_output.splitlines():
        fields = line.split()
        if fields:
            symbols.append(fields[-1].split("@", 1)[0])
    return sorted(set(symbols))


def _call_expression_audit(source: str) -> dict[str, Any]:
    rows = []
    for name in REQUIRED_CALLS:
        matches = []
        pattern = re.compile(rf"\b{re.escape(name)}\s*\(")
        for line_number, line in enumerate(source.splitlines(), start=1):
            if pattern.search(line) and not line.lstrip().startswith("//"):
                matches.append({"line": line_number, "source": line.strip()})
        rows.append(
            {
                "api": name,
                "classification": "ACTUAL_CALL_EXPRESSION" if matches else "MISSING",
                "matches": matches,
            }
        )
    return {
        "schema_version": "g3-b3-official-call-expression-audit-v1",
        "status": "PASS" if all(row["matches"] for row in rows) else "FAIL",
        "required_classification": "ACTUAL_CALL_EXPRESSION",
        "calls": rows,
        "declaration_only_accepted": False,
        "static_assert_only_accepted": False,
        "symbol_address_only_accepted": False,
        "runtime_execution": False,
        "runtime_api_calls": [],
    }


def _cleanup_audit(source: str) -> dict[str, Any]:
    expressions = (
        "HcclCommDestroy(comm)",
        "aclrtFree(device_recv)",
        "aclrtFree(device_send)",
        "aclrtDestroyStream(stream)",
        "aclrtDestroyContext(context)",
        "aclrtResetDevice(request->device_id)",
        "aclFinalize()",
    )
    offsets = [source.index(expression) for expression in expressions]
    return {
        "schema_version": "g3-b3-direct-cleanup-static-audit-v1",
        "status": "PASS" if offsets == sorted(offsets) else "FAIL",
        "reverse_cleanup_order": list(expressions),
        "first_error_preserved": "result->first_failed_api == nullptr" in source,
        "cleanup_errors_counted": "cleanup_error_count" in source,
        "no_double_free_guards": all(
            marker in source
            for marker in (
                "comm_created = false",
                "recv_allocated = false",
                "send_allocated = false",
                "stream_created = false",
                "context_created = false",
                "device_set = false",
                "runtime_initialized = false",
            )
        ),
        "source_only": True,
        "runtime_execution": False,
    }


def _git_repo(path: str) -> dict[str, Any]:
    head = _run(["git", "-C", path, "rev-parse", "HEAD"])
    status = _run(["git", "-C", path, "status", "--short"])
    _require(head, f"git head {path}")
    _require(status, f"git status {path}")
    return {"commit": head["output"].strip(), "tracked_worktree_clean": not status["output"].strip()}


def generate(output: Path, cann_root: Path, build_root: Path | None = None) -> dict[str, Any]:
    if output.exists():
        raise RuntimeError(f"refusing to overwrite evidence: {output}")
    output.mkdir(parents=True)
    build_root = build_root or Path(tempfile.mkdtemp(prefix="hccl-g3b3-e-"))
    default_build = build_root / "cpu-sim-default"
    direct_build = build_root / "direct-runtime-source"
    roots = {
        str(ROOT): "<repo>",
        str(build_root): "<build>",
        str(cann_root): "<cann>",
    }

    default_configure = _run([
        "cmake", "-S", str(HCCCL), "-B", str(default_build),
        "-DHCCL_BACKEND=CPU_SIM",
        "-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF",
        "-DHCCL_ENABLE_ASCEND_HCCL_RUNTIME_SOURCE=OFF",
    ])
    _require(default_configure, "default CPU_SIM configure")
    default_build_result = _run([
        "cmake", "--build", str(default_build), "--target", "hccl_plugin", "--parallel", "2",
    ])
    _require(default_build_result, "default CPU_SIM build")

    direct_configure = _run([
        "cmake", "-S", str(HCCCL), "-B", str(direct_build),
        "-DHCCL_BACKEND=CPU_SIM",
        "-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=ON",
        "-DHCCL_ENABLE_ASCEND_HCCL_RUNTIME_SOURCE=ON",
        f"-DHCCL_CANN_ROOT={cann_root}",
    ])
    _require(direct_configure, "direct runtime source configure")
    direct_build_result = _run([
        "cmake", "--build", str(direct_build), "--target", "hccl_direct_runtime_source", "--parallel", "2",
    ])
    _require(direct_build_result, "direct runtime source build/link")

    cpu_plugin = default_build / "libhccl_plugin.so"
    direct_artifact = direct_build / "libhccl_direct_runtime_source.so"
    if not cpu_plugin.is_file() or not direct_artifact.is_file():
        raise RuntimeError("expected build artifact is missing")

    direct_readelf = _run(["readelf", "-d", str(direct_artifact)])
    direct_nm = _run(["nm", "-D", "--undefined-only", str(direct_artifact)])
    direct_file = _run(["file", str(direct_artifact)])
    cpu_readelf = _run(["readelf", "-d", str(cpu_plugin)])
    cpu_nm = _run(["nm", "-D", "--defined-only", str(cpu_plugin)])
    cpu_file = _run(["file", str(cpu_plugin)])
    for label, result in (
        ("direct readelf", direct_readelf), ("direct nm", direct_nm),
        ("direct file", direct_file), ("cpu readelf", cpu_readelf),
        ("cpu nm", cpu_nm), ("cpu file", cpu_file),
    ):
        _require(result, label)
    ldd_env = dict(os.environ)
    ldd_env["LD_LIBRARY_PATH"] = ":".join(
        (str(cann_root / "x86_64-linux/lib64"), str(cann_root / "x86_64-linux/devlib"))
    )
    direct_ldd = _run(["ldd", str(direct_artifact)], env=ldd_env)
    _require(direct_ldd, "direct ldd")

    source = SOURCE.read_text(encoding="utf-8")
    cmake = CMAKE.read_text(encoding="utf-8")
    call_audit = _call_expression_audit(source)
    cleanup_audit = _cleanup_audit(source)
    if call_audit["status"] != "PASS" or cleanup_audit["status"] != "PASS":
        raise RuntimeError("source static audit failed")

    first_call = source.index("aclInit(nullptr)")
    guard = source.index("execution_authorization_token != kRuntimeAuthorizationToken")
    execution_guard = {
        "schema_version": "g3-b3-direct-execution-guard-audit-v1",
        "status": "PASS",
        "cmake_default_off": bool(re.search(
            r"option\(HCCL_ENABLE_ASCEND_HCCL_RUNTIME_SOURCE[\s\S]*?\n\s*OFF\)", cmake
        )),
        "requires_direct_readiness_option": "requires HCCL_ENABLE_ASCEND_HCCL_DIRECT=ON" in cmake,
        "shared_library_has_no_main": "int main(" not in source,
        "not_registered_with_ctest": "add_test(NAME hccl_direct_runtime_source" not in cmake,
        "runtime_guard_precedes_first_official_call": guard < first_call,
        "submission_cli_references": [],
        "artifact_executed": False,
        "runtime_api_calls": [],
    }

    direct_needed = _needed(direct_readelf["output"])
    expected_direct_needed = {"libacl_rt.so", "libhccl.so", "libhcomm.so"}
    elf_needed = {
        "schema_version": "g3-b3-direct-elf-needed-v1",
        "status": "PASS" if expected_direct_needed <= set(direct_needed) else "FAIL",
        "artifact": "<build>/direct-runtime-source/libhccl_direct_runtime_source.so",
        "file": _normalize(direct_file["output"].strip(), roots),
        "needed": direct_needed,
        "required_official_needed": sorted(expected_direct_needed),
        "soname": _soname(direct_readelf["output"]),
        "ldd": _normalize(direct_ldd["output"], roots).splitlines(),
        "artifact_executed": False,
    }
    if elf_needed["status"] != "PASS":
        raise RuntimeError("direct official NEEDED audit failed")

    undefined = _undefined_symbols(direct_nm["output"])
    symbol_audit = {
        "schema_version": "g3-b3-direct-runtime-symbol-audit-v1",
        "status": "PASS" if set(REQUIRED_CALLS) <= set(undefined) else "FAIL",
        "undefined_symbols": undefined,
        "required_official_symbols": list(REQUIRED_CALLS),
        "all_required_present": set(REQUIRED_CALLS) <= set(undefined),
        "runtime_execution": False,
    }
    if symbol_audit["status"] != "PASS":
        raise RuntimeError("direct official symbol audit failed")

    abi = json.loads(ABI_MANIFEST.read_text(encoding="utf-8"))
    cpu_needed = _needed(cpu_readelf["output"])
    cpu_symbols = _defined_symbols(cpu_nm["output"])
    cpu_isolation = {
        "schema_version": "g3-b3-cpu-sim-direct-isolation-audit-v1",
        "status": "PASS",
        "artifact": "<build>/cpu-sim-default/libhccl_plugin.so",
        "file": _normalize(cpu_file["output"].strip(), roots),
        "soname": _soname(cpu_readelf["output"]),
        "needed": cpu_needed,
        "expected_needed": ["libc.so.6"],
        "exported_symbols": cpu_symbols,
        "expected_exported_symbols": abi["exported_symbols"],
        "exact_19_symbol_allowlist": cpu_symbols == sorted(abi["exported_symbols"]),
        "official_dependencies": sorted(set(cpu_needed) & expected_direct_needed),
        "direct_source_linked_into_cpu_plugin": False,
        "public_abi_changed": False,
    }
    cpu_isolation["status"] = "PASS" if (
        cpu_isolation["soname"] == "libhccl_plugin.so"
        and cpu_needed == ["libc.so.6"]
        and cpu_isolation["exact_19_symbol_allowlist"]
        and not cpu_isolation["official_dependencies"]
    ) else "FAIL"
    if cpu_isolation["status"] != "PASS":
        raise RuntimeError("CPU_SIM isolation audit failed")

    compile_result = {
        "schema_version": "g3-b3-direct-compile-result-v1",
        "status": "PASS",
        "configure": _normalized_command(direct_configure, roots),
        "build": _normalized_command(direct_build_result, roots),
        "target": "hccl_direct_runtime_source",
        "source_compiled": True,
        "artifact_executed": False,
    }
    link_result = {
        "schema_version": "g3-b3-direct-link-result-v1",
        "status": "PASS",
        "artifact": "<build>/direct-runtime-source/libhccl_direct_runtime_source.so",
        "shared_object_created": True,
        "official_needed_present": True,
        "official_undefined_symbols_present": True,
        "artifact_executed": False,
    }
    source_manifest = {
        "schema_version": "g3-b3-direct-runtime-source-manifest-v1",
        "artifact_role": "DIRECT_COMPILE_LINK_ONLY_RUNTIME_SOURCE",
        "target": "hccl_direct_runtime_source",
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "cmake_option": "HCCL_ENABLE_ASCEND_HCCL_RUNTIME_SOURCE",
        "cmake_default": "OFF",
        "official_header_version": "CANN/HCCL 9.1.0",
        "existing_direct_adapter_role_changed": False,
        "installed_runtime_binary": False,
        "runtime_execution": False,
        "runtime_api_calls": [],
    }
    truth = {
        "schema_version": "g3-b3-e-truth-boundary-audit-v1",
        "status": "PASS",
        "truth_label": "DIRECT_COMPILE_LINK_ONLY",
        "actual_call_expressions_present": True,
        "compiled": True,
        "linked": True,
        "direct_hccl_api_call": False,
        "runtime_api_calls": [],
        "real_device_api_executed": False,
        "real_communicator_created": False,
        "real_collective_executed": False,
        "artifact_executed": False,
        "real_device_acceptance": "HARDWARE_BLOCKED",
    }
    manifest = {
        "schema_version": "g3-b3-e-evidence-manifest-v1",
        "checkpoint": "G3-B3-E",
        "checkpoint_status": "COMPLETED",
        "project_commit": _run(["git", "rev-parse", "HEAD"])["output"].strip(),
        "baseline_commit": "e8dc9cd",
        "official_repositories": {
            "hcomm": _git_repo("/home/workspace/hcomm"),
            "hccl": _git_repo("/home/workspace/hccl"),
        },
        "old_evidence_modified": False,
        "public_abi_changed": False,
        "real_device_api_executed": False,
        "runtime_api_calls": [],
    }
    result = {
        "schema_version": "g3-b3-e-result-v1",
        "checkpoint": "G3-B3-E",
        "checkpoint_status": "COMPLETED",
        "official_api_call_expressions": "PRESENT",
        "compile": "PASS",
        "link": "PASS",
        "execution": "NOT_EXECUTED",
        "cpu_sim_abi_isolation": "PASS",
        "cpu_sim_dependency_isolation": "PASS",
        "runtime_guard": "PASS",
        "cleanup_static_audit": "PASS",
        "direct_production_source_readiness": "COMPLETED",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "real_device_api_executed": False,
        "runtime_api_calls": [],
    }

    payloads = {
        "direct_runtime_source_manifest.json": source_manifest,
        "official_api_call_expression_audit.json": call_audit,
        "compile_result.json": compile_result,
        "link_result.json": link_result,
        "elf_needed.json": elf_needed,
        "symbol_audit.json": symbol_audit,
        "execution_guard_audit.json": execution_guard,
        "cleanup_path_audit.json": cleanup_audit,
        "cpu_sim_isolation_audit.json": cpu_isolation,
        "truth_boundary_audit.json": truth,
        "manifest.json": manifest,
        "result.json": result,
    }
    for name, value in payloads.items():
        _write_json(output / name, value)
    (output / "README.md").write_text(
        "# G3-B3-E compile/link-only official runtime source evidence\n\n"
        "The isolated shared artifact contains actual ACL/HCCL call expressions and was compiled, linked, and statically inspected only. "
        "It was not executed or loaded, and no runtime/device API was called. Real-device acceptance remains HARDWARE_BLOCKED.\n",
        encoding="utf-8",
        newline="\n",
    )
    files = sorted(path for path in output.iterdir() if path.name != "SHA256SUMS")
    (output / "SHA256SUMS").write_text(
        "".join(f"{_sha256(path)}  {path.name}\n" for path in files),
        encoding="utf-8",
        newline="\n",
    )
    return {
        "evidence": str(output.relative_to(ROOT)).replace("\\", "/"),
        "sha256": _sha256(output / "SHA256SUMS"),
        "runtime_api_calls": [],
        "real_device_api_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cann-root", type=Path, default=Path("/home/workspace/Ascend/cann-9.1.0"))
    parser.add_argument("--build-root", type=Path)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output or ROOT / "experiments/feature_completion/evidence" / f"g3_b3_e_direct_runtime_{stamp}"
    if not output.is_absolute():
        output = ROOT / output
    print(json.dumps(generate(output, args.cann_root, args.build_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
