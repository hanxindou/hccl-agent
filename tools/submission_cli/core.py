"""Host-only G3-B build, reproduction, staging, and verification CLI.

The default path builds and executes only the project-owned CPU_SIM plugin.
The optional direct path compiles/link-inspects readiness artifacts and runs a
host lifecycle model; it never executes the link-audit ELF or a device API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DISTRO = "Ubuntu-22.04"
MARKER = ".hccl_submission_generated.json"
NATIVE_MANIFEST = ROOT / "hcccl/submission/native_plugin_abi_manifest.json"
DIRECT_MANIFEST = ROOT / "hcccl/submission/direct_readiness_abi_manifest.json"
DEFAULT_STAGE = ROOT / "dist/submission-staging"
RESULT_ROOT = ROOT / "dist/submission-results"
BUILD_ROOT = ROOT / "build/submission"
INSTALL_ROOT = ROOT / "dist/submission-install"
DEFAULT_CANN_ROOT = "/home/workspace/Ascend/cann-9.1.0"
G3_B2_A_EVIDENCE = ROOT / "experiments/optimization/evidence/g3_b2_a_baseline_20260807T012447Z"
G3_B2_C_EVIDENCE = ROOT / "experiments/optimization/evidence/g3_b2_c_topology_20260807T021000Z"
G3_B2_D_EVIDENCE = ROOT / "experiments/optimization/evidence/g3_b2_d_replan_20260807T023000Z"
G3_B2_E_EVIDENCE = ROOT / "experiments/optimization/evidence/g3_b2_e_agent_round1_20260807T032000Z"

EVIDENCE_DIRS = {
    "g2_e": ROOT / "experiments/hccl_vm/evidence/g2_e_summary_20260730T095800.105217Z",
    "g2_f_1": ROOT / "experiments/direct_api/evidence/g2_f_1_20260730T203000Z",
    "g2_f_2": ROOT / "experiments/direct_api/evidence/g2_f_2_20260730T210000Z",
    "g2_f_3": ROOT / "experiments/direct_api/evidence/g2_f_3_20260802T000000Z",
    "g2_f_4": ROOT / "experiments/direct_api/evidence/g2_f_4_20260802T010000Z",
    "g2_f_5": ROOT / "experiments/simulator/evidence/g2_f_5_simulator_20260804T010000Z",
    "g2_f_6": ROOT / "experiments/simulator/evidence/g2_f_6_simulator_20260804T020000Z",
    "g2_f_7": ROOT / "experiments/final_audit/evidence/g2_f_7_20260805T010000Z",
    "g3_a": ROOT / "experiments/submission/evidence/g3_a_20260806T035554Z",
}

QUICK_TEST_MODULES = [
    "tests.test_simulator_collective_correctness",
    "tests.test_failover_engine",
    "tests.test_backend_selection",
    "tests.test_plugin_bridge",
]
FULL_TEST_MODULES = QUICK_TEST_MODULES + [
    "tests.test_g2_f_6_simulator_acceptance",
    "tests.test_g2_f_7_backend_final_audit",
    "tests.test_direct_api_backend",
    "tests.test_direct_adapter_build_contract",
    "tests.test_direct_lifecycle_contract",
    "tests.test_direct_link_contract",
    "tests.submission_audit.test_g3_a_audit",
]


class SubmissionError(RuntimeError):
    """Stable CLI failure with a user-facing message."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def _run(command: Sequence[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None,
         check: bool = True) -> dict[str, Any]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    completed = subprocess.run(
        list(command), cwd=cwd, env=merged, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    result = {
        "command": list(command), "exit_code": completed.returncode,
        "stdout": completed.stdout, "stderr": completed.stderr,
    }
    if check and completed.returncode:
        tail = (completed.stderr or completed.stdout)[-4000:]
        raise SubmissionError(f"command failed ({completed.returncode}): {' '.join(command)}\n{tail}")
    return result


def _linux_path(path: Path) -> str:
    value = str(path.resolve())
    if os.name != "nt":
        return value
    drive, tail = os.path.splitdrive(value)
    if not drive:
        raise SubmissionError(f"cannot map path to WSL: {value}")
    normalized_tail = tail.lstrip("\\/").replace(os.sep, "/")
    return f"/mnt/{drive[0].lower()}/{normalized_tail}"


def _run_linux(arguments: Sequence[str], *, env: dict[str, str] | None = None,
               check: bool = True) -> dict[str, Any]:
    if os.name != "nt":
        return _run(arguments, env=env, check=check)
    assignments = " ".join(f"{key}={shlex.quote(value)}" for key, value in (env or {}).items())
    command = shlex.join(list(arguments))
    script = f"cd {shlex.quote(_linux_path(ROOT))} && {assignments + ' ' if assignments else ''}{command}"
    return _run(
        ["wsl.exe", "--distribution", DEFAULT_DISTRO, "--exec", "bash", "-lc", script],
        check=check,
    )


def _git(*arguments: str) -> str:
    return _run(["git", *arguments])["stdout"].strip()


def _normalize_public_paths(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_public_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_public_paths(item) for item in value]
    if isinstance(value, str):
        replacements = [
            (_linux_path(BUILD_ROOT), "<build>"), (_linux_path(INSTALL_ROOT), "<install>"),
            (_linux_path(DEFAULT_STAGE), "<stage>"), (_linux_path(ROOT), "<repo>"),
            (str(BUILD_ROOT.resolve()), "<build>"), (str(INSTALL_ROOT.resolve()), "<install>"),
            (str(DEFAULT_STAGE.resolve()), "<stage>"), (str(ROOT.resolve()), "<repo>"),
            (DEFAULT_CANN_ROOT, "<cann-root>"),
        ]
        result = value
        for source, replacement in replacements:
            result = result.replace(source, replacement)
        return result
    return value


def _inside(path: Path, parent: Path) -> bool:
    resolved, root = path.resolve(), parent.resolve()
    return resolved == root or root in resolved.parents


def _assert_generated_target(path: Path) -> Path:
    resolved = path.resolve()
    if not (_inside(resolved, BUILD_ROOT) or _inside(resolved, ROOT / "dist")):
        raise SubmissionError("generated output must remain under build/submission or dist")
    if resolved in {ROOT.resolve(), (ROOT / "build").resolve(), (ROOT / "dist").resolve()}:
        raise SubmissionError("refusing broad generated-output target")
    if resolved.is_symlink():
        raise SubmissionError("generated output may not be a symlink")
    return resolved


def _prepare_generated(path: Path, *, clean: bool) -> Path:
    target = _assert_generated_target(path)
    if target.exists() and any(target.iterdir()):
        marker = target / MARKER
        if not clean:
            raise SubmissionError(f"generated output exists; pass the explicit clean option: {target}")
        if not marker.is_file():
            raise SubmissionError(f"refusing to clean unmarked directory: {target}")
        try:
            shutil.rmtree(target)
        except PermissionError:
            time.sleep(0.25)
            shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    _write_json(target / MARKER, {"schema_version": "hccl-submission-generated-v1", "generated": True})
    return target


def _tool_version(command: Sequence[str]) -> str:
    result = _run_linux(command, check=False)
    return (result["stdout"] or result["stderr"]).splitlines()[0] if result["exit_code"] == 0 else "UNAVAILABLE"


def _verify_sha256sums(directory: Path) -> dict[str, Any]:
    manifest = directory / "SHA256SUMS"
    if not manifest.is_file():
        raise SubmissionError(f"SHA256SUMS missing: {directory.relative_to(ROOT).as_posix()}")
    checked = 0
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        digest, name = raw.split(None, 1)
        name = name.lstrip(" *")
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            raise SubmissionError(f"unsafe SHA256SUMS path: {name}")
        path = directory / Path(*pure.parts)
        if not path.is_file() or _sha256(path) != digest:
            raise SubmissionError(f"SHA256 mismatch: {directory.name}/{name}")
        checked += 1
    return {
        "path": directory.relative_to(ROOT).as_posix(),
        "files_checked": checked,
        "sha256sums_sha256": _sha256(manifest),
        "status": "PASS",
    }


def verify_old_evidence(names: Iterable[str]) -> list[dict[str, Any]]:
    return [_verify_sha256sums(EVIDENCE_DIRS[name]) for name in names]


def _test_count(output: str) -> int:
    match = re.search(r"(\d+) tests? passed", output)
    if match:
        return int(match.group(1))
    match = re.search(r"out of (\d+)", output)
    if match:
        return int(match.group(1))
    match = re.search(r"Ran (\d+) tests?", output)
    return int(match.group(1)) if match else 0


def check_environment() -> dict[str, Any]:
    required_paths = [
        ROOT / "hcccl/CMakeLists.txt", ROOT / "hcccl/src/hccl_comm.c",
        ROOT / "hcccl/src/hccl_algorithms.c", NATIVE_MANIFEST, DIRECT_MANIFEST,
        ROOT / "configs/submission/full_mesh_8.json", EVIDENCE_DIRS["g3_a"] / "result.json",
    ]
    required_tools = {
        name: _tool_version([name, "--version"] if name not in {"cc", "readelf", "nm", "ldd", "file"} else [name, "--version"])
        for name in ("cmake", "cc", "ctest", "readelf", "nm", "ldd", "file", "ld")
    }
    missing_paths = [path.relative_to(ROOT).as_posix() for path in required_paths if not path.exists()]
    missing_tools = [name for name, version in required_tools.items() if version == "UNAVAILABLE"]
    result = {
        "schema_version": "g3-b-check-v1",
        "status": "PASS" if not missing_paths and not missing_tools else "FAIL",
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "repository_root": "<repo>",
        "required": {"paths": "PASS" if not missing_paths else "FAIL", "tools": required_tools},
        "optional": {"cann_9_1_0": "AVAILABLE" if _run_linux(["test", "-d", DEFAULT_CANN_ROOT], check=False)["exit_code"] == 0 else "NOT_PRESENT"},
        "real_device_only": {"npu": "NOT_PROBED", "runtime_execution": "DISABLED"},
        "user_action_required": ["UA-B-001", "UA-B-002", "UA-B-003", "UA-B-004"],
        "missing_paths": missing_paths, "missing_tools": missing_tools,
        "official_asset_default": "EXCLUDE",
        "default_backend": "CPU_SIM", "fallback_policy": "NONE",
    }
    if result["status"] != "PASS":
        raise SubmissionError(json.dumps(result, sort_keys=True))
    return result


def _parse_native_audit(artifact: Path) -> dict[str, Any]:
    linux_artifact = _linux_path(artifact)
    dynamic = _run_linux(["readelf", "-d", linux_artifact])["stdout"]
    symbols_raw = _run_linux(["nm", "-D", "--defined-only", "--format=posix", linux_artifact])["stdout"]
    ldd = _run_linux(["ldd", linux_artifact])["stdout"]
    file_output = _run_linux(["file", linux_artifact])["stdout"].strip()
    symbols = []
    for line in symbols_raw.splitlines():
        if not line.strip():
            continue
        name = line.split()[0].split("@", 1)[0]
        if name.startswith("HCCL_PLUGIN_"):
            continue
        symbols.append(name)
    symbols = sorted(set(symbols))
    needed = sorted(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
    soname_match = re.search(r"Library soname: \[([^]]+)\]", dynamic)
    manifest = json.loads(NATIVE_MANIFEST.read_text(encoding="utf-8"))
    expected = sorted(manifest["exported_symbols"])
    forbidden = sorted(set(symbols) & set(manifest["forbidden_symbols"]))
    result = {
        "artifact": "<install>/lib/libhccl_plugin.so",
        "artifact_role": "CPU_SIM_REFERENCE_PLUGIN",
        "sha256": _sha256(artifact),
        "file": file_output.split(":", 1)[-1].strip(),
        "soname": soname_match.group(1) if soname_match else "MISSING",
        "needed": needed,
        "ldd": [line.strip() for line in ldd.splitlines() if line.strip()],
        "exported_symbols": symbols,
        "missing_symbols": sorted(set(expected) - set(symbols)),
        "unexpected_symbols": sorted(set(symbols) - set(expected)),
        "forbidden_symbols": forbidden,
        "official_dependencies": [name for name in needed if name in {"libhccl.so", "libhcomm.so", "libacl_rt.so", "libruntime.so"}],
    }
    result["status"] = "PASS" if (
        not result["missing_symbols"] and not result["unexpected_symbols"] and not forbidden
        and result["soname"] == manifest["soname"] and not result["official_dependencies"]
        and "ELF 64-bit" in result["file"]
    ) else "FAIL"
    if result["status"] != "PASS":
        raise SubmissionError(f"native ABI/ELF audit failed: {json.dumps(result, sort_keys=True)}")
    return result


def _build_once(name: str) -> dict[str, Any]:
    build_dir = _prepare_generated(BUILD_ROOT / name, clean=True)
    install_dir = _prepare_generated(INSTALL_ROOT / name, clean=True)
    source_epoch = _git("show", "-s", "--format=%ct", "HEAD")
    repo_linux, build_linux, install_linux = map(_linux_path, (ROOT, build_dir, install_dir))
    flags = f"-O2 -DNDEBUG -ffile-prefix-map={repo_linux}=/src -fdebug-prefix-map={repo_linux}=/src"
    configure = [
        "cmake", "-S", f"{repo_linux}/hcccl", "-B", build_linux,
        "-DCMAKE_BUILD_TYPE=Release", "-DHCCL_BACKEND=CPU_SIM",
        "-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=OFF",
        f"-DCMAKE_INSTALL_PREFIX={install_linux}", f"-DCMAKE_C_FLAGS_RELEASE={flags}",
    ]
    commands = []
    commands.append(_run_linux(configure, env={"SOURCE_DATE_EPOCH": source_epoch}))
    commands.append(_run_linux(["cmake", "--build", build_linux, "--config", "Release", "--parallel", "2"], env={"SOURCE_DATE_EPOCH": source_epoch}))
    ctest = _run_linux(["ctest", "--test-dir", build_linux, "--output-on-failure"], env={"SOURCE_DATE_EPOCH": source_epoch})
    commands.append(ctest)
    commands.append(_run_linux(["cmake", "--install", build_linux, "--prefix", install_linux], env={"SOURCE_DATE_EPOCH": source_epoch}))
    artifact = install_dir / "lib/libhccl_plugin.so"
    if not artifact.is_file():
        raise SubmissionError(f"installed CPU_SIM artifact missing: {artifact}")
    audit = _parse_native_audit(artifact)
    headers = {name: _sha256(install_dir / "include" / name) for name in ("hccl_comm.h", "hccl_algorithms.h")}
    test_count = _test_count(ctest["stdout"])
    if test_count != 12:
        raise SubmissionError(f"expected 12 CPU_SIM CTests, observed {test_count}")
    return {
        "name": name, "status": "PASS", "build_dir": f"<build>/{name}",
        "install_dir": f"<install>/{name}", "source_commit": _git("rev-parse", "HEAD"),
        "source_date_epoch": source_epoch, "cmake_options": configure[5:],
        "commands": [{"command": item["command"], "exit_code": item["exit_code"]} for item in commands],
        "ctest": {"status": "PASS", "passed": test_count, "failed": 0},
        "headers_sha256": headers, "native_audit": audit,
        "artifact_path": artifact,
    }


def _consumer_compile(install_dir: Path) -> dict[str, Any]:
    consumer = _prepare_generated(BUILD_ROOT / "installed-consumer", clean=True)
    _write_text(consumer / "main.c", """#include <hccl_comm.h>\nint main(void) { return hcclPluginGetVersion() ? 0 : 1; }\n""")
    _write_text(consumer / "CMakeLists.txt", """cmake_minimum_required(VERSION 3.10)\nproject(hccl_consumer C)\nfind_package(hccl_plugin CONFIG REQUIRED)\nadd_executable(hccl_consumer main.c)\ntarget_link_libraries(hccl_consumer PRIVATE hccl::plugin)\n""")
    output = consumer / "out"
    output.mkdir()
    prefix = _linux_path(install_dir)
    configure = _run_linux(["cmake", "-S", _linux_path(consumer), "-B", _linux_path(output), f"-DCMAKE_PREFIX_PATH={prefix}"])
    build = _run_linux(["cmake", "--build", _linux_path(output), "--parallel", "2"])
    return {"status": "PASS", "configure_exit_code": configure["exit_code"], "build_exit_code": build["exit_code"], "executed": False}


def _direct_build(cann_root: str) -> dict[str, Any]:
    available = _run_linux(["test", "-d", cann_root], check=False)["exit_code"] == 0
    if not available:
        return {"status": "ENV_BLOCKED", "reason": "explicit frozen CANN root is unavailable", "runtime_api_calls": []}
    build_dir = _prepare_generated(BUILD_ROOT / "direct-readiness", clean=True)
    build_linux = _linux_path(build_dir)
    configure_args = [
        "cmake", "-S", f"{_linux_path(ROOT)}/hcccl", "-B", build_linux,
        "-DCMAKE_BUILD_TYPE=Release", "-DHCCL_BACKEND=CPU_SIM",
        "-DHCCL_ENABLE_ASCEND_HCCL_DIRECT=ON", f"-DHCCL_CANN_ROOT={cann_root}",
    ]
    configure = _run_linux(configure_args)
    build = _run_linux(["cmake", "--build", build_linux, "--config", "Release", "--parallel", "2"])
    ctest = _run_linux(["ctest", "--test-dir", build_linux, "-R", "test_hccl_direct_lifecycle", "--output-on-failure"])
    archive = build_dir / "libhccl_direct_adapter.a"
    link_audit = build_dir / "hccl_direct_link_audit"
    if not archive.is_file() or not link_audit.is_file():
        raise SubmissionError("direct readiness archive or non-executed link-audit ELF is missing")
    archive_symbols_raw = _run_linux(["nm", "-g", "--defined-only", _linux_path(archive)])["stdout"]
    archive_symbols = sorted({
        line.rsplit(None, 1)[-1] for line in archive_symbols_raw.splitlines()
        if line.strip() and not line.rstrip().endswith(":")
    })
    dynamic = _run_linux(["readelf", "-d", _linux_path(link_audit)])["stdout"]
    needed = sorted(re.findall(r"Shared library: \[([^]]+)\]", dynamic))
    required_refs = {"libhccl.so", "libhcomm.so", "libacl_rt.so"}
    cpu_symbols = set(json.loads(NATIVE_MANIFEST.read_text(encoding="utf-8"))["exported_symbols"])
    leaked = sorted(set(archive_symbols) & cpu_symbols)
    direct_symbols = sorted(name for name in archive_symbols if name.startswith("hccl_direct_"))
    if leaked or not direct_symbols or not required_refs.issubset(needed):
        raise SubmissionError("direct readiness ABI/link isolation audit failed")
    return _normalize_public_paths({
        "status": "PASS", "artifact_type": "STATIC BUILD/LIFECYCLE READINESS ARTIFACT",
        "archive": "<build>/direct-readiness/libhccl_direct_adapter.a",
        "archive_sha256": _sha256(archive), "direct_symbols": direct_symbols,
        "cpu_sim_symbol_leakage": leaked, "link_audit_elf": "INSPECTED_NOT_EXECUTED",
        "official_library_references": sorted(required_refs), "observed_needed": needed,
        "lifecycle_ctest": {"passed": _test_count(ctest["stdout"]), "failed": 0},
        "no_device_status": "NO_DEVICE_EXPECTED", "official_runtime_execution": False,
        "direct_hccl_api_call": False, "runtime_api_calls": [],
        "commands": [
            {"command": configure["command"], "exit_code": configure["exit_code"]},
            {"command": build["command"], "exit_code": build["exit_code"]},
            {"command": ctest["command"], "exit_code": ctest["exit_code"]},
        ],
    })


def _load_config(path_value: str | None, *, submission_schema: bool) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    if not resolved.is_file():
        raise SubmissionError(f"configuration does not exist: {path_value}")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if submission_schema:
        if payload.get("schema_version") != "submission-simulator-config-v1":
            raise SubmissionError("topology config schema must be submission-simulator-config-v1")
        if payload.get("topology_source") != "SIMULATOR_CONFIG":
            raise SubmissionError("topology source must remain SIMULATOR_CONFIG")
        if payload.get("topology") not in {"FULL_MESH", "RING", "FAT_TREE", "HETEROGENEOUS"}:
            raise SubmissionError("unsupported simulator topology")
        if not isinstance(payload.get("rank_size"), int) or payload["rank_size"] < 2:
            raise SubmissionError("rank_size must be an integer >= 2")
    return {
        "path": resolved.relative_to(ROOT).as_posix() if _inside(resolved, ROOT) else "<user-config>",
        "sha256": _sha256(resolved), "payload": payload,
    }


def _simulator_replay(args: argparse.Namespace) -> dict[str, Any]:
    from simulator.collective_correctness import Case, run_case
    from simulator.g2_f_6_acceptance import ExperimentSpec, SimulatorAcceptance

    cluster = _load_config(getattr(args, "cluster_config", None), submission_schema=False)
    topology_cfg = _load_config(getattr(args, "topology_config", None), submission_schema=True)
    topology = topology_cfg["payload"]["topology"] if topology_cfg else "FULL_MESH"
    ranks = getattr(args, "rank_size", None) or (topology_cfg["payload"]["rank_size"] if topology_cfg else 8)
    seed = getattr(args, "seed", 20260806)
    message_size = getattr(args, "message_size", 1024 * 1024)
    primitive = getattr(args, "primitive", "AllReduce")
    algorithm = getattr(args, "algorithm", "Ring AllReduce")
    if ranks < 2 or message_size < 1 or primitive not in {"AllReduce", "AllGather", "ReduceScatter"}:
        raise SubmissionError("invalid rank size, message size, or primitive")
    if algorithm not in {"Ring AllReduce", "NHR", "Mesh", "Butterfly", "Fat-Tree"}:
        raise SubmissionError("unsupported algorithm")
    cases = [
        Case("AllReduce", "FP32", "SUM", 8, "FULL_MESH", "quick", 16, seed),
        Case("AllGather", "BF16", None, 8, "RING", "quick", 16, seed),
        Case("ReduceScatter", "FP16", "MAX", 8, "FAT_TREE", "quick", 16, seed),
    ]
    correctness = [run_case(case, exact=True) for case in cases]
    if not all(item["exact_match"] and not item["has_nan_or_inf"] for item in correctness):
        raise SubmissionError("representative simulator correctness failed")
    model = SimulatorAcceptance()
    chosen = ExperimentSpec("submission-quick", primitive, algorithm, topology, ranks, "injected", message_size,
                            reduce_op=None if primitive == "AllGather" else "SUM", seed=seed)
    selected = model.simulate_iteration(chosen, 0)
    comparisons = [
        model.simulate_iteration(ExperimentSpec(f"compare-{name}", "AllReduce", name, "FAT_TREE", 64, "1MB", 1024 * 1024), 0)
        for name in ("Ring AllReduce", "Fat-Tree")
    ]
    faults = model.reliability_scenarios()
    recovered = next(item for item in faults if item["collective_completion_status"] == "RECOVERED")
    no_path = next(item for item in faults if item["collective_completion_status"] == "EXPECTED_NO_PATH_FAILURE")
    return {
        "status": "PASS", "validation_track": "SIMULATOR_ACCEPTANCE",
        "topology_source": "SIMULATOR_CONFIG", "real_device_measured": False,
        "configuration": {"cluster": cluster, "topology": topology_cfg, "hardware_profile": getattr(args, "hardware_profile", "tier_medium"), "seed": seed, "message_size": message_size, "rank_size": ranks, "primitive": primitive, "algorithm": algorithm},
        "correctness_cases": [{"primitive": case.primitive, "dtype": case.dtype, "status": "PASS", "output_hash": result["output_hash"]} for case, result in zip(cases, correctness)],
        "representative_8_rank_or_injected": {"rank_size": selected["rank_size"], "simulated_collective_time_us": selected["simulated_collective_time_us"], "correctness_gate": selected["correctness_gate"]},
        "algorithm_comparison": [{"algorithm": item["algorithm"], "simulated_collective_time_us": item["simulated_collective_time_us"]} for item in comparisons],
        "fault_recovery": {"status": recovered["collective_completion_status"], "simulated_failover_time_ms": recovered["simulated_failover_time_ms"]},
        "no_alternate_path": {"status": no_path["collective_completion_status"]},
    }


def _python_regression(modules: Sequence[str], artifact: Path) -> dict[str, Any]:
    result = _run_linux(
        ["python3", "-m", "unittest", "-q", *modules],
        env={"HCCL_PLUGIN_PATH": _linux_path(artifact)},
    )
    count = _test_count(result["stderr"] + result["stdout"])
    return {"status": "PASS", "passed": count, "failed": 0, "modules": list(modules), "exit_code": result["exit_code"]}


def _g3_b2_quick_checks() -> dict[str, Any]:
    from algorithm.ring_schedule import generate_ring_schedule
    from algorithm.schedule_ir import validate_schedule
    from algorithm.schedule_selector import select_schedule
    from algorithm.topology_model import build_topology
    from algorithm.topology_schedules import generate_schedule
    representative = generate_ring_schedule("AllReduce", 8, 65539)
    invariants = validate_schedule(representative)
    topology = build_topology("asymmetric", 16)
    selector = select_schedule("AllReduce", topology, 1048579)
    hierarchical = generate_schedule("Hierarchical", "AllReduce", topology, 1048579)
    comparison = {
        "ring_schedule_hash": representative["schedule_hash"],
        "hierarchical_schedule_hash": hierarchical["schedule_hash"],
        "different": representative["schedule_hash"] != hierarchical["schedule_hash"],
    }
    if not invariants or not selector["selected_schedule_hash"] or selector["fallback"] != "NONE" or not comparison["different"]:
        raise SubmissionError("G3-B2 quick schedule checks failed")
    return {
        "status": "PASS", "schedule_invariant_count": len(invariants),
        "representative_schedule": {"primitive": "AllReduce", "rank_size": 8, "schedule_hash": representative["schedule_hash"], "phase_count": len(representative["phases"])},
        "agent_selector_output": {key: value for key, value in selector.items() if key != "selected_schedule"},
        "topology_aware_comparison": comparison, "full_benchmark_executed": False,
    }


def _g3_b2_full_checks(build_name: str) -> dict[str, Any]:
    matrix = json.loads((ROOT / "configs/optimization/g3_b2_benchmark_matrix.json").read_text(encoding="utf-8"))
    if len(matrix["performance_scenarios"]) != 18 or len(matrix["reliability_scenarios"]) != 4:
        raise SubmissionError("G3-B2 benchmark contract count drift")
    test_files = [
        "tests/optimization/test_g3_b2_baseline.py",
        "tests/optimization/test_g3_b2_schedule_ir.py",
        "tests/optimization/test_g3_b2_topology_optimization.py",
        "tests/optimization/test_g3_b2_replan_memory_pipeline.py",
        "tests/optimization/test_g3_b2_agent_ablation.py",
    ]
    focused = []
    for relative in test_files:
        run = _run_linux(["python3", _linux_path(ROOT / relative)])
        focused.append({"path": relative, "status": "PASS", "output": (run["stdout"] + run["stderr"]).strip()})
    dump = BUILD_ROOT / build_name / "schedule_ir_dump"
    parity_run = _run_linux([_linux_path(dump), "AllReduce", "8", "65539", "FP32", "SUM"])
    observed = json.loads(parity_run["stdout"])
    from algorithm.ring_schedule import generate_ring_schedule
    from algorithm.memory_model import attach_memory_report
    from algorithm.topology_model import build_topology
    from algorithm.topology_schedules import generate_schedule
    parity = observed == generate_ring_schedule("AllReduce", 8, 65539)
    memory_schedule = attach_memory_report(generate_schedule("Hierarchical", "AllReduce", build_topology("fat_tree", 64), 1024**3), 64 * 1024 * 1024)
    final_dirs = sorted((ROOT / "experiments/optimization/evidence").glob("g3_b2_f_final_*"))
    if len(final_dirs) > 1:
        raise SubmissionError("multiple G3-B2 final evidence directories")
    final_validation: dict[str, Any]
    if final_dirs:
        integrity = _verify_sha256sums(final_dirs[0])
        result = json.loads((final_dirs[0] / "result.json").read_text(encoding="utf-8"))
        if integrity["status"] != "PASS" or result.get("checkpoint") != "G3-B2":
            raise SubmissionError("G3-B2 final evidence validation failed")
        final_validation = {"status": "PASS", "path": final_dirs[0].relative_to(ROOT).as_posix(), "integrity": integrity}
    else:
        final_validation = {"status": "NOT_YET_FROZEN", "reason": "first full run precedes the single final evidence generation"}
    if not parity or not memory_schedule["memory_plan"]["within_budget"]:
        raise SubmissionError("G3-B2 parity or bounded-memory audit failed")
    return {
        "status": "PASS", "benchmark_contract": {"performance_scenarios": 18, "reliability_scenarios": 4, "sha256": _sha256(ROOT / "configs/optimization/g3_b2_benchmark_matrix.json")},
        "focused_tests": focused, "c_python_parity": {"status": "PASS", "schedule_hash": observed["schedule_hash"]},
        "bounded_memory": memory_schedule["memory_plan"], "final_evidence_validation": final_validation,
    }


def build_command(args: argparse.Namespace) -> dict[str, Any]:
    check_environment()
    if args.direct_readiness:
        if not args.cann_root:
            raise SubmissionError("--direct-readiness requires --cann-root")
        return _direct_build(args.cann_root)
    build = _build_once(args.name)
    return _public_build(build)


def _public_build(build: dict[str, Any]) -> dict[str, Any]:
    return _normalize_public_paths({key: value for key, value in build.items() if key != "artifact_path"})


def quick_command(args: argparse.Namespace, *, persist: bool = True) -> dict[str, Any]:
    environment = check_environment()
    build = _build_once("quick")
    regression = _python_regression(QUICK_TEST_MODULES, build["artifact_path"])
    replay = _simulator_replay(args)
    evidence = verify_old_evidence(["g2_f_5", "g2_f_6"])
    g3_b2 = _g3_b2_quick_checks()
    result = {
        "schema_version": "g3-b-quick-v1", "status": "PASS",
        "command": "python -m tools.submission_cli quick", "environment": environment,
        "build": _public_build(build), "python_regression": regression,
        "simulator_replay": replay, "old_evidence": evidence, "g3_b2_schedule_checks": g3_b2,
        "expensive_simulator_evidence_regenerated": False,
        "real_device_api_executed": False, "runtime_api_calls": [],
    }
    if persist:
        RESULT_ROOT.mkdir(parents=True, exist_ok=True)
        _write_json(RESULT_ROOT / "quick.json", result)
    return result


def full_command(args: argparse.Namespace) -> dict[str, Any]:
    if args.regenerate_expensive_simulator_evidence:
        raise SubmissionError("G3-B authorization forbids regenerating expensive simulator evidence")
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    def progress(step: str) -> None:
        _write_json(RESULT_ROOT / "full-progress.json", {"status": "IN_PROGRESS", "last_completed_step": step})
    environment = check_environment()
    progress("environment")
    build_a = _build_once("build-a")
    progress("build-a")
    build_b = _build_once("build-b")
    progress("build-b")
    a, b = build_a["native_audit"], build_b["native_audit"]
    comparison = {
        "binary_sha256_equal": a["sha256"] == b["sha256"],
        "soname_equal": a["soname"] == b["soname"],
        "needed_equal": a["needed"] == b["needed"],
        "symbols_equal": a["exported_symbols"] == b["exported_symbols"],
        "file_type_equal": a["file"] == b["file"],
        "headers_equal": build_a["headers_sha256"] == build_b["headers_sha256"],
        "ctest_equal": build_a["ctest"] == build_b["ctest"],
        "first_artifact_reused": False,
    }
    functional = all(value for key, value in comparison.items() if key not in {"binary_sha256_equal", "first_artifact_reused"})
    if not functional:
        raise SubmissionError("two clean builds are not functionally reproducible")
    reproducible_status = "BIT_FOR_BIT_REPRODUCIBLE" if comparison["binary_sha256_equal"] else "FUNCTIONALLY_REPRODUCIBLE"
    comparison["status"] = reproducible_status
    comparison["difference_reason"] = None if comparison["binary_sha256_equal"] else "compiler/linker metadata differs; ABI, ELF, dependencies, headers, and tests are equal"
    consumer = _consumer_compile(INSTALL_ROOT / "build-a")
    progress("installed-consumer")
    regression = _python_regression(FULL_TEST_MODULES, build_a["artifact_path"])
    progress("python-regression")
    replay = _simulator_replay(args)
    progress("simulator-replay")
    old_evidence = verify_old_evidence(EVIDENCE_DIRS.keys())
    progress("old-evidence")
    quick = quick_command(args, persist=True)
    progress("quick-regression")
    g3_b2 = _g3_b2_full_checks("build-a")
    progress("g3-b2-full-checks")
    direct = _direct_build(args.cann_root or DEFAULT_CANN_ROOT)
    progress("direct-readiness")
    stage_args = argparse.Namespace(output=str(DEFAULT_STAGE.relative_to(ROOT)), clean_output=True, include_selected_evidence=True, exclude_controlled_docs=True, exclude_official_assets=True)
    staging = stage_command(stage_args)
    progress("staging")
    verification = verify_stage(DEFAULT_STAGE)
    progress("staging-verification")
    result = {
        "schema_version": "g3-b-full-v1", "status": "PASS",
        "command": "python -m tools.submission_cli full",
        "environment": environment, "build_a": _public_build(build_a), "build_b": _public_build(build_b),
        "reproducible_build": comparison, "reproducible_build_status": reproducible_status,
        "consumer_compile": consumer, "python_regression": regression,
        "simulator_replay": replay, "old_evidence": old_evidence, "quick_regression": {"status": quick["status"]},
        "direct_readiness": direct, "staging": staging, "staging_verification": verification,
        "g3_b2_full_checks": g3_b2,
        "expensive_simulator_evidence_regenerated": False,
        "real_device_api_executed": False, "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False, "runtime_api_calls": [],
    }
    _write_json(RESULT_ROOT / "full.json", result)
    _write_json(RESULT_ROOT / "full-progress.json", {"status": "PASS", "last_completed_step": "full-summary"})
    return result


def _copy_file(source: Path, destination: Path) -> None:
    if not source.is_file() or source.is_symlink():
        raise SubmissionError(f"staging source is missing or unsafe: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def _copy_selected_tree(source: Path, destination: Path, suffixes: set[str]) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise SubmissionError(f"symlink is not allowed in staging source: {path}")
        if path.is_file() and (path.suffix.lower() in suffixes or path.name in {"CMakeLists.txt", "SHA256SUMS", "EVIDENCE_SHA256"}):
            _copy_file(path, destination / path.relative_to(source))


def _safe_result_summary(name: str, directory: Path) -> dict[str, Any]:
    source = directory / "result.json"
    payload = json.loads(source.read_text(encoding="utf-8")) if source.is_file() else {}
    allowed = {
        key: value for key, value in payload.items()
        if key in {
            "checkpoint", "checkpoint_status", "status", "overall", "validation_track",
            "performance_claim_type", "measured_on_real_npu", "direct_hccl_api_call",
            "real_ascend_npu_validated", "real_device_acceptance", "runtime_api_calls",
            "g2_f_readiness", "g2_f_overall", "competition_simulator_track",
        }
    }
    return {
        "schema_version": "g3-b-selected-evidence-summary-v1", "evidence_id": name,
        "source_path": directory.relative_to(ROOT).as_posix(),
        "source_result_sha256": _sha256(source) if source.is_file() else None,
        "source_sha256sums_sha256": _sha256(directory / "SHA256SUMS"),
        "integrity": _verify_sha256sums(directory), "selected_fields": allowed,
        "generated_summary": True, "old_evidence_modified": False,
    }


def _scan_stage(stage: Path) -> dict[str, Any]:
    patterns = {
        "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "api_key": re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|password|cookie)\s*[:=]\s*['\"]?(?:sk-|ghp_|github_pat_|AKIA|Bearer\s+)[A-Za-z0-9_./+=-]{8,}"),
        "windows_user_path": re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s]+"),
        "wsl_home": re.compile(r"/home/(?!workspace(?:/|\b))[A-Za-z0-9._-]+/"),
    }
    findings: list[dict[str, str]] = []
    for path in sorted(stage.rglob("*")):
        if path.is_symlink():
            findings.append({"path": path.relative_to(stage).as_posix(), "kind": "symlink"})
            continue
        if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".py", ".c", ".cpp", ".h", ".txt", ".cmake"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in patterns.items():
            if pattern.search(text):
                findings.append({"path": path.relative_to(stage).as_posix(), "kind": name})
    forbidden_names = []
    for path in stage.rglob("*"):
        rel = path.relative_to(stage).as_posix().casefold()
        if path.is_file() and (rel.endswith(".docx") or path.name in {"libhccl.so", "libhcomm.so", "libacl_rt.so", "libruntime.so"} or "/logs/" in f"/{rel}/" or path.name == ".env"):
            forbidden_names.append(rel)
    findings.extend({"path": name, "kind": "forbidden_asset"} for name in forbidden_names)
    return {"scan_type": "PRELIMINARY_FORBIDDEN_DATA_SCAN", "status": "PASS" if not findings else "FAIL", "findings": findings}


def _claim_boundary_audit(stage: Path) -> dict[str, Any]:
    forbidden = [
        '"real_device_api_executed": true', '"direct_hccl_api_call": true',
        '"real_ascend_npu_validated": true', '"measured_on_real_npu": true',
        '"official_direct_plugin_validated": true', "REAL_DEVICE_PASS",
    ]
    findings = []
    for rel in ("README.md", "STATUS.json", "MANIFEST.json"):
        path = stage / rel
        if not path.is_file():
            continue
        value = path.read_text(encoding="utf-8", errors="replace")
        findings.extend({"path": rel, "token": token} for token in forbidden if token in value)
    return {"status": "PASS" if not findings else "FAIL", "findings": findings, "truth_labels": ["CPU_EXECUTED", "DIRECT_READINESS_ONLY", "SIMULATED_ONLY", "REAL_DEVICE_NOT_EXECUTED"]}


def _manifest_entry(stage: Path, path: Path, source_map: dict[str, str]) -> dict[str, Any]:
    rel = path.relative_to(stage).as_posix()
    category = "RELEASE_METADATA"
    role = "STAGING_METADATA"
    if rel.startswith("native/lib/"):
        category, role = "NATIVE_PLUGIN", "CPU_SIM_REFERENCE_PLUGIN"
    elif rel.startswith("native/direct/") or rel.startswith("hcccl/direct/"):
        category, role = "NATIVE_PLUGIN", "DIRECT_READINESS_SOURCE"
    elif rel.startswith("agent/"):
        category, role = "AGENT_ENGINEERING", "AGENT_SOURCE_OR_PLACEHOLDER"
    elif rel.startswith("simulator/"):
        category, role = "SIMULATOR", "SIMULATOR_SOURCE_OR_CONFIG"
    elif rel.startswith("evidence/"):
        category, role = "EVIDENCE", "SELECTED_FROZEN_EVIDENCE"
    elif rel.startswith("tests/"):
        category, role = "TEST_TOOL", "SUBMISSION_RELEVANT_TEST"
    elif rel.startswith("tools/"):
        category, role = "TEST_TOOL", "SUBMISSION_REPRODUCTION_TOOL"
    elif rel.startswith("docs/"):
        category, role = "TECHNICAL_REPORT", "G3_B_REPRODUCTION_DOCUMENT"
    return {
        "artifact_id": "G3B-" + hashlib.sha256(rel.encode()).hexdigest()[:12].upper(),
        "source_path": source_map.get(rel, "<generated>"), "staging_path": rel,
        "category": category, "artifact_role": role, "include": True, "required": True,
        "generated": rel not in source_map, "source_commit": _git("rev-parse", "HEAD"),
        "sha256": _sha256(path), "size_bytes": path.stat().st_size,
        "license_status": "USER_ACTION_REQUIRED", "confidentiality": "SUBMISSION_ARTIFACT",
        "redistribution_status": "PROJECT_ASSET_PENDING_LICENSE" if not rel.startswith("evidence/") else "PROJECT_EVIDENCE",
        "execution_status": "HOST_EXECUTED" if rel == "native/lib/libhccl_plugin.so" else "NOT_EXECUTED_AS_STAGED_FILE",
        "evidence_level": "E3_HOST_EXECUTED" if rel == "native/lib/libhccl_plugin.so" else "E1_DOCUMENTED",
        "claim_label": "CPU_EXECUTED" if rel == "native/lib/libhccl_plugin.so" else "REAL_DEVICE_NOT_EXECUTED",
        "owner_checkpoint": "G3-B", "known_limitations": ["not a final release", "real-device API not executed"],
    }


def stage_command(args: argparse.Namespace) -> dict[str, Any]:
    if not (args.exclude_controlled_docs and args.exclude_official_assets):
        raise SubmissionError("G3-B staging requires controlled-doc and official-asset exclusion")
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    stage = _prepare_generated(output, clean=args.clean_output)
    source_map: dict[str, str] = {}

    def copy(source_rel: str, stage_rel: str | None = None) -> None:
        source = ROOT / source_rel
        destination_rel = stage_rel or source_rel
        _copy_file(source, stage / destination_rel)
        source_map[PurePosixPath(destination_rel).as_posix()] = PurePosixPath(source_rel).as_posix()

    copy("README.MD", "README.md")
    for rel in (
        "main.py", "hcccl/CMakeLists.txt", "hcccl/README.md",
        "docs/submission/reproduction_guide.md", "docs/submission/native_plugin_abi_decision.md",
        "docs/submission/submission_staging_guide.md", "docs/submission/dependency_and_redistribution_boundary.md",
        "docs/submission/claim_boundary_matrix.json", "docs/submission/requirement_matrix.json",
        "docs/submission/deliverable_inventory.json", "docs/submission/risk_register.json",
    ):
        copy(rel)
    for directory in ("agent", "algorithm", "plugin", "simulator", "skills", "topology", "hardware", "cost_model", "config", "configs/submission", "tools/submission_cli"):
        source = ROOT / directory
        _copy_selected_tree(source, stage / directory, {".py", ".json", ".md", ".txt"})
        for path in (stage / directory).rglob("*"):
            if path.is_file():
                rel = path.relative_to(stage).as_posix()
                source_map[rel] = (source / path.relative_to(stage / directory)).relative_to(ROOT).as_posix()
    _copy_selected_tree(ROOT / "hcccl", stage / "hcccl", {".c", ".cpp", ".h", ".md", ".json", ".cmake", ".map", ".in"})
    for path in (stage / "hcccl").rglob("*"):
        if path.is_file():
            rel = path.relative_to(stage).as_posix()
            source_map[rel] = (ROOT / rel).relative_to(ROOT).as_posix()
    for module in FULL_TEST_MODULES:
        rel = module.replace(".", "/") + ".py"
        copy(rel)
    if (ROOT / "tests/submission_cli").is_dir():
        _copy_selected_tree(ROOT / "tests/submission_cli", stage / "tests/submission_cli", {".py"})
        for path in (stage / "tests/submission_cli").rglob("*.py"):
            source_map[path.relative_to(stage).as_posix()] = (ROOT / path.relative_to(stage)).relative_to(ROOT).as_posix()

    artifact = None
    for candidate in (INSTALL_ROOT / "build-a/lib/libhccl_plugin.so", INSTALL_ROOT / "quick/lib/libhccl_plugin.so"):
        if candidate.is_file():
            artifact = candidate
            break
    if artifact is None:
        raise SubmissionError("stage requires a fresh CLI-generated CPU_SIM install; run quick or full first")
    _copy_file(artifact, stage / "native/lib/libhccl_plugin.so")
    source_map["native/lib/libhccl_plugin.so"] = "<generated-from-clean-build>"
    copy("hcccl/include/hccl_comm.h", "native/include/hccl_comm.h")
    copy("hcccl/include/hccl_algorithms.h", "native/include/hccl_algorithms.h")
    copy("hcccl/submission/native_plugin_abi_manifest.json", "native/ABI_MANIFEST.json")
    copy("hcccl/direct/README.md", "native/direct/README.md")
    copy("hcccl/direct/include/hccl_direct_adapter.h", "native/direct/include/hccl_direct_adapter.h")
    copy("hcccl/direct/src/hccl_direct_adapter.cpp", "native/direct/source/hccl_direct_adapter.cpp")
    copy("hcccl/direct/src/hccl_direct_link_audit.cpp", "native/direct/source/hccl_direct_link_audit.cpp")
    copy("hcccl/submission/direct_readiness_abi_manifest.json", "native/direct/ABI_MANIFEST.json")

    copy("configs/optimization/g3_b2_schedule_ir_schema.json", "algorithm/schedule_schema.json")
    copy("experiments/optimization/evidence/g3_b2_c_topology_20260807T021000Z/algorithm_support_matrix.json", "algorithm/algorithm_support_matrix.json")
    from algorithm.ring_schedule import generate_ring_schedule
    from algorithm.topology_model import build_topology
    from algorithm.topology_schedules import generate_schedule
    _write_json(stage / "algorithm/examples/ring_allreduce_8.json", generate_ring_schedule("AllReduce", 8, 65539))
    _write_json(stage / "algorithm/examples/hierarchical_allreduce_16.json", generate_schedule("Hierarchical", "AllReduce", build_topology("fat_tree", 16), 1048579))
    source_map["algorithm/examples/ring_allreduce_8.json"] = "<generated-from-frozen-schedule-generator>"
    source_map["algorithm/examples/hierarchical_allreduce_16.json"] = "<generated-from-frozen-schedule-generator>"
    _write_text(stage / "algorithm/README.md", "# Collective scheduling\n\nCanonical Schedule IR, supported algorithms, and representative CPU/simulator-only schedules. Fallback is NONE.\n")
    source_map["algorithm/README.md"] = "<generated-staging-document>"
    baseline_summary = {"result": json.loads((G3_B2_A_EVIDENCE / "result.json").read_text(encoding="utf-8")), "manifest": json.loads((G3_B2_A_EVIDENCE / "manifest.json").read_text(encoding="utf-8"))}
    final_summary = {"result": json.loads((G3_B2_E_EVIDENCE / "result.json").read_text(encoding="utf-8")), "performance": json.loads((G3_B2_E_EVIDENCE / "performance_summary.json").read_text(encoding="utf-8"))}
    _write_json(stage / "optimization/baseline_summary.json", baseline_summary)
    _write_json(stage / "optimization/final_summary.json", final_summary)
    copy("experiments/optimization/evidence/g3_b2_e_agent_round1_20260807T032000Z/ablation_summary.json", "optimization/ablation_summary.json")
    _write_text(stage / "optimization/claim_boundaries.md", "# Optimization claim boundaries\n\nAll latency, bandwidth, scale, replan, and pipeline results are SIMULATED_ONLY. The 45.59% internal result includes modeled exposed-path overlap and is not real NPU or training acceleration.\n")
    for rel in ("optimization/baseline_summary.json", "optimization/final_summary.json", "optimization/claim_boundaries.md"):
        source_map[rel] = "<generated-from-frozen-g3-b2-evidence>"
    for rel in (
        "docs/submission/g3_b2_final_code_baseline.md",
        "docs/submission/g3_b2_requirement_delta.json",
    ):
        if (ROOT / rel).is_file():
            copy(rel)

    _write_text(stage / "QUICKSTART.md", "# Quick start\n\n```text\npython -m tools.submission_cli check\npython -m tools.submission_cli quick\npython -m tools.submission_cli verify --stage .\n```\n")
    _write_text(stage / "CLAIM_BOUNDARIES.md", "# Claim boundaries\n\nCPU_SIM is host-executed project code. Direct is static/host readiness only. Scale, logical 1 GB, logical 72h, and failover are simulator-model results. No real NPU API was executed.\n")
    _write_text(stage / "reports/PLACEHOLDER_G3_C.md", "# G3-C placeholder\n\nFormal technical reports are not completed in G3-B.\n")
    _write_text(stage / "demo/PLACEHOLDER_G3_F.md", "# G3-F placeholder\n\nDemo and video material is not completed in G3-B.\n")
    status = {
        "g3_b": "COMPLETED", "native_delivery_normalization": "COMPLETED",
        "g3_b2": "COMPLETED", "collective_schedule_ir": "COMPLETED",
        "topology_aware_hierarchical_optimization": "COMPLETED",
        "agent_optimization_trace": "COMPLETED", "performance_target_achievement": "PARTIALLY_SATISFIED",
        "cpu_sim_submission_plugin": "COMPLETED", "direct_readiness_package": "COMPLETED",
        "submission_release_readiness": "PARTIAL", "g3_delivery_readiness": "PARTIAL",
        "real_device_acceptance": "HARDWARE_BLOCKED", "default_backend": "CPU_SIM",
        "fallback_policy": "NONE", "final_release_created": False,
        "real_device_api_executed": False, "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False, "measured_on_real_npu": False,
        "runtime_api_calls": [],
    }
    _write_json(stage / "STATUS.json", status)
    _write_json(stage / "claim_boundaries.json", {"schema_version": "g3-b-claim-boundaries-v1", "truth_labels": ["CPU_EXECUTED", "DIRECT_READINESS_ONLY", "SIMULATED_ONLY", "REAL_DEVICE_NOT_EXECUTED"], "real_device_api_executed": False})
    excluded = {
        "schema_version": "g3-b-excluded-assets-v1", "default_policy": "EXCLUDE",
        "assets": [
            {"id": "UA-B-001", "asset": "project license/copyright", "decision": "USER_ACTION_REQUIRED", "include": False},
            {"id": "UA-B-002", "asset": "official CANN binaries and HCOMM/HCCL source/headers", "decision": "USER_ACTION_REQUIRED", "include": False},
            {"id": "UA-B-003", "asset": "controlled competition DOCX", "decision": "USER_ACTION_REQUIRED", "include": False},
            {"id": "UA-B-004", "asset": "final platform archive format and size", "decision": "USER_ACTION_REQUIRED", "include": False},
            {"asset": "private logs, credentials, caches, superseded raw evidence", "decision": "EXCLUDE", "include": False},
        ],
    }
    _write_json(stage / "EXCLUDED_ASSETS.json", excluded)
    _write_json(stage / "release/USER_ACTION_REQUIRED.json", excluded)

    selection = {
        "schema_version": "g3-b-evidence-selection-v1",
        "policy": {
            "g2_f_5": "INCLUDE_FULL", "g2_f_6": "INCLUDE_FULL", "g3_a": "INCLUDE_FULL",
            "g2_f_7": "INCLUDE_SUMMARY_ONLY", "g2_e": "INCLUDE_SUMMARY_ONLY",
            "g2_f_1": "REFERENCE_ONLY", "g2_f_2": "INCLUDE_SUMMARY_ONLY",
            "g2_f_3": "INCLUDE_SUMMARY_ONLY", "g2_f_4": "INCLUDE_SUMMARY_ONLY",
        },
        "large_raw_evidence": "selected only; platform size remains UA-B-004",
    }
    _write_json(stage / "evidence/inventory.json", selection)
    if args.include_selected_evidence:
        for name in ("g2_f_5", "g2_f_6", "g3_a"):
            _copy_selected_tree(EVIDENCE_DIRS[name], stage / f"evidence/selected/{name}", {".json", ".md", ".txt", ".jsonl"})
            for path in (stage / f"evidence/selected/{name}").rglob("*"):
                if path.is_file():
                    source_map[path.relative_to(stage).as_posix()] = (EVIDENCE_DIRS[name] / path.relative_to(stage / f"evidence/selected/{name}")).relative_to(ROOT).as_posix()
        for name, directory in EVIDENCE_DIRS.items():
            _write_json(stage / f"evidence/summaries/{name}.json", _safe_result_summary(name, directory))
    _write_text(stage / "evidence/README.md", "# Selected evidence\n\nG2-F-5, G2-F-6, and G3-A are included in full; other frozen checkpoints use generated integrity-preserving summaries or references. Old evidence is never modified.\n")

    scan = _scan_stage(stage)
    if scan["status"] != "PASS":
        raise SubmissionError(f"preliminary forbidden-data scan failed: {scan['findings']}")
    _write_json(stage / "release/PRELIMINARY_FORBIDDEN_DATA_SCAN.json", scan)
    claim_audit = _claim_boundary_audit(stage)
    if claim_audit["status"] != "PASS":
        raise SubmissionError(f"claim boundary audit failed: {claim_audit['findings']}")
    _write_json(stage / "release/CLAIM_BOUNDARY_AUDIT.json", claim_audit)
    _write_json(stage / "release/BUILD_MANIFEST.json", {"build_mode": "CPU_SIM", "direct_readiness": "SOURCE_AND_STATIC_READINESS", "official_runtime_execution": False})
    _write_json(stage / "release/DEPENDENCY_MANIFEST.json", {"cpu_sim": _parse_native_audit(stage / "native/lib/libhccl_plugin.so")["needed"], "official_assets_included": False})

    metadata_names = {"MANIFEST.json", "SHA256SUMS", "release/submission_inclusion_manifest.json", "release/STAGING_SIZE_REPORT.json"}
    payload_files = [path for path in sorted(stage.rglob("*")) if path.is_file() and path.relative_to(stage).as_posix() not in metadata_names]
    entries = [_manifest_entry(stage, path, source_map) for path in payload_files]
    staging_paths = [entry["staging_path"] for entry in entries]
    if len(staging_paths) != len(set(staging_paths)):
        raise SubmissionError("duplicate staging path")
    manifest = {
        "schema_version": "g3-b-submission-inclusion-manifest-v1", "staging_root": "<stage>",
        "release_ready": False, "final_release_created": False,
        "official_binaries_included": False, "official_source_included": False,
        "controlled_competition_doc_included": False, "private_logs_included": False,
        "entries": entries,
    }
    _write_json(stage / "MANIFEST.json", manifest)
    _write_json(stage / "release/submission_inclusion_manifest.json", manifest)
    size = {"payload_file_count": len(entries), "payload_total_size_bytes": sum(entry["size_bytes"] for entry in entries), "platform_limit": "USER_ACTION_REQUIRED"}
    _write_json(stage / "release/STAGING_SIZE_REPORT.json", size)
    checksum_lines = [
        f"{_sha256(path)}  {path.relative_to(stage).as_posix()}"
        for path in sorted(stage.rglob("*")) if path.is_file() and path.name != "SHA256SUMS"
    ]
    _write_text(stage / "SHA256SUMS", "\n".join(checksum_lines) + "\n")
    return {
        "status": "PASS", "staging_root": "dist/submission-staging" if stage == DEFAULT_STAGE else "<stage>",
        "file_count": sum(1 for path in stage.rglob("*") if path.is_file()),
        "total_size_bytes": sum(path.stat().st_size for path in stage.rglob("*") if path.is_file()),
        "included_count": len(entries), "excluded_count": len(excluded["assets"]),
        "selected_evidence": selection["policy"], "official_assets_included": False,
        "controlled_competition_doc_included": False, "private_logs_included": False,
    }


def verify_stage(stage: Path) -> dict[str, Any]:
    stage = stage.resolve()
    if not stage.is_dir() or stage.is_symlink():
        raise SubmissionError("staging root is missing or unsafe")
    manifest_path = stage / "MANIFEST.json"
    checksum_path = stage / "SHA256SUMS"
    if not manifest_path.is_file() or not checksum_path.is_file():
        raise SubmissionError("staging manifest or SHA256SUMS is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "g3-b-submission-inclusion-manifest-v1":
        raise SubmissionError("unsupported staging manifest schema")
    entries = manifest.get("entries", [])
    staging_paths = [entry.get("staging_path") for entry in entries]
    if len(staging_paths) != len(set(staging_paths)):
        raise SubmissionError("duplicate staging path in manifest")
    for entry in entries:
        pure = PurePosixPath(entry["staging_path"])
        if pure.is_absolute() or ".." in pure.parts:
            raise SubmissionError("unsafe staging path in manifest")
        path = stage / Path(*pure.parts)
        if not path.is_file() or _sha256(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
            raise SubmissionError(f"manifest/filesystem mismatch: {entry['staging_path']}")
    checksummed = set()
    for raw in checksum_path.read_text(encoding="utf-8").splitlines():
        digest, name = raw.split(None, 1)
        name = name.lstrip(" *")
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            raise SubmissionError(f"unsafe checksum path: {name}")
        path = stage / Path(*pure.parts)
        if not path.is_file() or _sha256(path) != digest:
            raise SubmissionError(f"staging SHA256 mismatch: {name}")
        checksummed.add(name)
    actual_without_sums = {path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file() and path.name != "SHA256SUMS"}
    if checksummed != actual_without_sums:
        raise SubmissionError("SHA256SUMS does not exactly cover staging files")
    scan = _scan_stage(stage)
    claim = _claim_boundary_audit(stage)
    native = _parse_native_audit(stage / "native/lib/libhccl_plugin.so")
    required = {"native", "agent", "simulator", "evidence", "reports", "demo", "tools", "tests", "release"}
    missing = sorted(name for name in required if not (stage / name).is_dir())
    if scan["status"] != "PASS" or claim["status"] != "PASS" or missing:
        raise SubmissionError(f"staging policy verification failed: scan={scan['findings']} claim={claim['findings']} missing={missing}")
    if any(entry.get("source_path", "").startswith(("C:/Users/", "C:\\Users\\", "/home/")) for entry in entries):
        raise SubmissionError("absolute user path leaked into staging manifest")
    return {
        "schema_version": "g3-b-stage-verification-v1", "status": "PASS",
        "files_verified": len(checksummed), "manifest_entries_verified": len(entries),
        "preliminary_forbidden_data_scan": scan, "claim_boundary_audit": claim,
        "native_elf_audit": native, "controlled_competition_doc_included": False,
        "official_binaries_included": False, "official_source_included": False,
        "absolute_user_paths": [], "symlink_escape": False,
    }


def describe_command() -> dict[str, Any]:
    return {
        "schema_version": "g3-b-description-v1", "default_backend": "CPU_SIM",
        "fallback_policy": "NONE",
        "backends": {
            "CPU_SIM": "project-owned host-executed collective plugin",
            "ASCEND_HCCL_VM": "official hccl_test subprocess contract; not run by G3-B",
            "ASCEND_HCCL_DIRECT": "official-ABI build/link/guard/lifecycle readiness only",
        },
        "validation_track": "SIMULATOR_ACCEPTANCE is not a fourth backend",
        "native_artifact": "libhccl_plugin.so: CPU_SIM_REFERENCE_PLUGIN",
        "direct_artifact": "libhccl_direct_adapter.a: STATIC BUILD/LIFECYCLE READINESS ARTIFACT",
        "quick": "clean CPU_SIM build, 12 CTests, representative Python/simulator and G2-F-5/F-6 integrity",
        "full": "two clean builds, ABI/ELF/dependency/install/consumer/regression/direct-readiness/staging audits",
        "limitations": ["official plugin ABI unverified", "real device API not executed", "release readiness partial"],
        "real_device_blocked_reason": "no authorized supported NPU runtime acceptance environment",
        "staging_policy": "exclude controlled DOCX, official assets, private logs, and conditional assets by default",
    }


def clean_generated_command(target: str) -> dict[str, Any]:
    candidates: list[Path] = []
    mapping = {"build": BUILD_ROOT, "install": INSTALL_ROOT, "results": RESULT_ROOT, "stage": DEFAULT_STAGE}
    roots = mapping.values() if target == "all" else [mapping[target]]
    for root in roots:
        root = _assert_generated_target(root)
        if (root / MARKER).is_file():
            candidates.append(root)
        elif root.is_dir():
            candidates.extend(path.parent for path in root.rglob(MARKER) if path.parent.is_dir() and not path.parent.is_symlink())
    removed = []
    for path in sorted(set(candidates), key=lambda item: len(item.parts), reverse=True):
        _assert_generated_target(path)
        if not (path / MARKER).is_file():
            raise SubmissionError(f"refusing unmarked generated path: {path}")
        shutil.rmtree(path)
        removed.append(path.relative_to(ROOT).as_posix())
    return {"status": "PASS", "removed": removed, "source_or_evidence_removed": False}


def _official_repository_state(path: str) -> dict[str, Any]:
    base = ["git", "-c", f"safe.directory={path}", "-C", path]
    branch = _run_linux([*base, "branch", "--show-current"])["stdout"].strip()
    commit = _run_linux([*base, "rev-parse", "HEAD"])["stdout"].strip()
    status = _run_linux([*base, "status", "--short"])["stdout"]
    return {"path": "<official-repository>", "branch": branch, "commit": commit, "tracked_worktree_clean": status == ""}


def evidence_command(args: argparse.Namespace) -> dict[str, Any]:
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    expected_parent = (ROOT / "experiments/submission/evidence").resolve()
    if output.exists() or output.resolve().parent != expected_parent or not output.name.startswith("g3_b_"):
        raise SubmissionError("final evidence must be a new g3_b_<timestamp> directory under experiments/submission/evidence")
    full_path, quick_path = RESULT_ROOT / "full.json", RESULT_ROOT / "quick.json"
    if not full_path.is_file() or not quick_path.is_file():
        raise SubmissionError("run successful full and quick commands before final evidence generation")
    full = json.loads(full_path.read_text(encoding="utf-8"))
    quick = json.loads(quick_path.read_text(encoding="utf-8"))
    verification = verify_stage(DEFAULT_STAGE)
    if full.get("status") != "PASS" or quick.get("status") != "PASS" or verification["status"] != "PASS":
        raise SubmissionError("cannot finalize evidence from a failed reproduction result")
    official = {
        "hcomm": _official_repository_state("/home/workspace/hcomm"),
        "hccl": _official_repository_state("/home/workspace/hccl"),
    }
    expected = {
        "hcomm": ("competition/campus-2026", "c8a3dc68a37315aa1e908a971fa706abe612f6ee"),
        "hccl": ("competition/campus-2026", "2c87cc1937bab23b8574ef24017c03572d3340e2"),
    }
    for name, state in official.items():
        if (state["branch"], state["commit"]) != expected[name] or not state["tracked_worktree_clean"]:
            raise SubmissionError(f"official {name} repository state drifted")

    temp = _prepare_generated(ROOT / "dist/g3-b-final-evidence-temp", clean=True)
    native_observed = full["build_a"]["native_audit"]
    native_manifest = json.loads(NATIVE_MANIFEST.read_text(encoding="utf-8"))
    native_manifest.update({"observed_sha256": native_observed["sha256"], "observed_soname": native_observed["soname"], "observed_dependencies": native_observed["needed"], "observed_exported_symbols": native_observed["exported_symbols"], "audit_status": "PASS"})
    direct_manifest = json.loads(DIRECT_MANIFEST.read_text(encoding="utf-8"))
    direct_manifest.update({"observed_readiness": full["direct_readiness"]})
    stage_manifest = json.loads((DEFAULT_STAGE / "MANIFEST.json").read_text(encoding="utf-8"))
    stage_size = json.loads((DEFAULT_STAGE / "release/STAGING_SIZE_REPORT.json").read_text(encoding="utf-8"))
    selection = json.loads((DEFAULT_STAGE / "evidence/inventory.json").read_text(encoding="utf-8"))
    excluded = json.loads((DEFAULT_STAGE / "EXCLUDED_ASSETS.json").read_text(encoding="utf-8"))
    forbidden = json.loads((DEFAULT_STAGE / "release/PRELIMINARY_FORBIDDEN_DATA_SCAN.json").read_text(encoding="utf-8"))
    claim = json.loads((DEFAULT_STAGE / "release/CLAIM_BOUNDARY_AUDIT.json").read_text(encoding="utf-8"))
    project_commit = _git("rev-parse", "HEAD")
    stage_files = [path for path in DEFAULT_STAGE.rglob("*") if path.is_file()]
    actual_stage_file_count = len(stage_files)
    actual_stage_total_size = sum(path.stat().st_size for path in stage_files)
    result = {
        "checkpoint": "G3-B", "checkpoint_status": "COMPLETED",
        "native_delivery_normalization": "COMPLETED", "cpu_sim_submission_plugin": "COMPLETED",
        "direct_readiness_package": "COMPLETED", "reproducible_build_status": full["reproducible_build_status"],
        "submission_cli": "COMPLETED", "submission_staging": "COMPLETED",
        "c_cpp_plugin_compliance": "PARTIALLY_SATISFIED", "submission_release_readiness": "PARTIAL",
        "g3_delivery_readiness": "PARTIAL", "real_device_acceptance": "HARDWARE_BLOCKED",
        "final_release_created": False, "public_release_created": False,
        "official_binaries_included": False, "official_source_included": False,
        "controlled_competition_doc_included": False, "old_evidence_modified": False,
        "real_device_api_executed": False, "direct_hccl_api_call": False,
        "real_ascend_npu_validated": False, "measured_on_real_npu": False,
        "runtime_api_calls": [], "user_action_required": ["UA-B-001", "UA-B-002", "UA-B-003", "UA-B-004"],
    }
    manifest = {
        "schema_version": "g3-b-evidence-v1", "checkpoint": "G3-B",
        "baseline_commit": project_commit, "project_commit": project_commit,
        "worktree_revision": "G3-B checkpoint files pending the authorized local commit",
        "source_documents": ["docs/plans/g3-competition-delivery-readiness.md", "G3-A controlled requirement summaries"],
        "generated_artifacts": ["docs/submission/reproduction_guide.md", "docs/submission/native_plugin_abi_decision.md", "dist/submission-staging"],
        "cpu_sim_so_sha256": native_observed["sha256"], "cpu_sim_so_soname": native_observed["soname"],
        "exported_symbols": native_observed["exported_symbols"], "dependencies": native_observed["needed"],
        "public_header_sha256": full["build_a"]["headers_sha256"],
        "cmake_options": full["build_a"]["cmake_options"],
        "build_comparison": full["reproducible_build"],
        "direct_artifact_type": full["direct_readiness"].get("artifact_type"),
        "direct_official_library_references": full["direct_readiness"].get("official_library_references", []),
        "direct_no_device_status": full["direct_readiness"].get("no_device_status"),
        "quick_command": quick["command"], "quick_exit_status": 0,
        "full_command": full["command"], "full_exit_status": 0,
        "staging_root": "dist/submission-staging", "staging_file_count": actual_stage_file_count,
        "staging_total_size_bytes": actual_stage_total_size,
        "inclusion_count": len(stage_manifest["entries"]), "exclusion_count": len(excluded["assets"]),
        "selected_evidence": selection["policy"],
        "user_action_required": result["user_action_required"],
        "known_limitations": ["official plugin ABI unverified", "license and redistribution unresolved", "real-device API not executed", "final archive not created"],
        "official_repositories": official, "evidence_sha256": "See EVIDENCE_SHA256 for SHA256(SHA256SUMS)",
    }
    environment = {
        "compiler": full["environment"]["required"]["tools"]["cc"],
        "cmake_version": full["environment"]["required"]["tools"]["cmake"],
        "generator": "Unix Makefiles", "build_type": "Release", "source_commit": project_commit,
        "source_date_epoch": full["build_a"]["source_date_epoch"], "build_options": full["build_a"]["cmake_options"],
        "target_architecture": native_observed["file"], "host_os": full["environment"]["platform"],
        "linker": "system linker via CMake", "linker_version": _tool_version(["ld", "--version"]),
        "binary_sha256": native_observed["sha256"], "header_sha256": full["build_a"]["headers_sha256"],
        "path_normalization": ["<repo>", "<build>", "<cann-root>"],
    }
    files: dict[str, Any] = {
        "manifest.json": manifest, "result.json": result,
        "native_artifact_inventory.json": {"cpu_sim": native_observed, "direct": full["direct_readiness"], "abi_isolation": "PASS"},
        "native_plugin_abi_manifest.json": native_manifest,
        "direct_readiness_abi_manifest.json": direct_manifest,
        "build_environment.json": environment,
        "build_commands.json": {"build_a": full["build_a"]["commands"], "build_b": full["build_b"]["commands"], "direct": full["direct_readiness"].get("commands", [])},
        "reproducible_build_audit.json": full["reproducible_build"],
        "elf_dependency_audit.json": {"status": "PASS", "file": native_observed["file"], "soname": native_observed["soname"], "needed": native_observed["needed"], "ldd": native_observed["ldd"], "official_dependencies": native_observed["official_dependencies"]},
        "symbol_inventory.json": {"status": "PASS", "exported_symbols": native_observed["exported_symbols"], "missing": native_observed["missing_symbols"], "unexpected": native_observed["unexpected_symbols"], "forbidden": native_observed["forbidden_symbols"], "direct_symbols": full["direct_readiness"].get("direct_symbols", [])},
        "install_audit.json": {"status": "PASS", "headers": full["build_a"]["headers_sha256"], "consumer_compile": full["consumer_compile"], "install_tree": ["lib/libhccl_plugin.so", "include/hccl_comm.h", "include/hccl_algorithms.h", "lib/cmake/hccl_plugin"]},
        "submission_cli_contract.json": {"status": "PASS", "commands": ["check", "build", "quick", "full", "stage", "verify", "describe", "clean-generated", "evidence"], "default_backend": "CPU_SIM", "fallback_policy": "NONE", "windows_import_safety": "PASS", "wsl_linux_execution_safety": "PASS"},
        "quick_run_summary.json": quick, "full_run_summary.json": full,
        "staging_manifest.json": stage_manifest,
        "staging_tree.json": {"root": "<stage>", "paths": sorted(path.relative_to(DEFAULT_STAGE).as_posix() for path in DEFAULT_STAGE.rglob("*") if path.is_file())},
        "staging_size_report.json": stage_size, "evidence_selection_policy.json": selection,
        "excluded_assets.json": excluded, "forbidden_data_scan.json": forbidden,
        "claim_boundary_audit.json": claim,
        "regression.json": {"status": "PASS", "python": full["python_regression"], "cpu_sim_ctest": full["build_a"]["ctest"], "old_evidence": full["old_evidence"], "official_repositories": official, "old_evidence_modified": False, "runtime_api_calls": []},
    }
    for name, payload in files.items():
        _write_json(temp / name, payload)
    _write_text(temp / "README.md", "# G3-B final evidence\n\nSingle authoritative native normalization, two-clean-build, submission CLI, internal staging, and truth-boundary evidence. No ACL/HCCL runtime, device, communicator, collective, MPI, hccl_test, msprof, final archive, or real NPU operation was executed.\n")
    payload_paths = [path for path in sorted(temp.iterdir()) if path.is_file() and path.name not in {MARKER, "SHA256SUMS", "EVIDENCE_SHA256"}]
    _write_text(temp / "SHA256SUMS", "\n".join(f"{_sha256(path)}  {path.name}" for path in payload_paths) + "\n")
    evidence_digest = _sha256(temp / "SHA256SUMS")
    _write_text(temp / "EVIDENCE_SHA256", f"{evidence_digest}  SHA256SUMS\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    for path in temp.iterdir():
        if path.is_file() and path.name != MARKER:
            shutil.copyfile(path, output / path.name)
    verified = _verify_sha256sums(output)
    if verified["sha256sums_sha256"] != evidence_digest:
        raise SubmissionError("final evidence checksum verification failed")
    return {"status": "PASS", "path": output.relative_to(ROOT).as_posix(), "sha256": evidence_digest, "official_repositories": official}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        print(json.dumps({"status": "FAIL", "error": message}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)


def _add_simulator_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cluster-config")
    parser.add_argument("--topology-config")
    parser.add_argument("--hardware-profile", default="tier_medium")
    parser.add_argument("--seed", type=int, default=20260806)
    parser.add_argument("--message-size", type=int, default=1024 * 1024)
    parser.add_argument("--rank-size", type=int)
    parser.add_argument("--primitive", choices=["AllReduce", "AllGather", "ReduceScatter"], default="AllReduce")
    parser.add_argument("--algorithm", choices=["Ring AllReduce", "NHR", "Mesh", "Butterfly", "Fat-Tree"], default="Ring AllReduce")


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="python -m tools.submission_cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    build = sub.add_parser("build")
    build.add_argument("--name", default="build")
    build.add_argument("--direct-readiness", action="store_true")
    build.add_argument("--cann-root")
    quick = sub.add_parser("quick")
    _add_simulator_flags(quick)
    full = sub.add_parser("full")
    _add_simulator_flags(full)
    full.add_argument("--cann-root")
    full.add_argument("--regenerate-expensive-simulator-evidence", action="store_true")
    stage = sub.add_parser("stage")
    stage.add_argument("--output", default="dist/submission-staging")
    stage.add_argument("--clean-output", action="store_true")
    stage.add_argument("--include-selected-evidence", action="store_true")
    stage.add_argument("--exclude-controlled-docs", action="store_true")
    stage.add_argument("--exclude-official-assets", action="store_true")
    verify = sub.add_parser("verify")
    verify.add_argument("--stage", default="dist/submission-staging")
    sub.add_parser("describe")
    clean = sub.add_parser("clean-generated")
    clean.add_argument("--target", choices=["all", "build", "install", "results", "stage"], default="all")
    evidence = sub.add_parser("evidence")
    evidence.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            result = check_environment()
        elif args.command == "build":
            result = build_command(args)
        elif args.command == "quick":
            result = quick_command(args)
        elif args.command == "full":
            result = full_command(args)
        elif args.command == "stage":
            result = stage_command(args)
        elif args.command == "verify":
            path = Path(args.stage)
            result = verify_stage(path if path.is_absolute() else ROOT / path)
        elif args.command == "describe":
            result = describe_command()
        elif args.command == "clean-generated":
            result = clean_generated_command(args.target)
        elif args.command == "evidence":
            result = evidence_command(args)
        else:
            raise SubmissionError(f"unknown command: {args.command}")
    except (SubmissionError, ValueError, OSError, json.JSONDecodeError) as exc:
        if getattr(args, "command", None) == "full":
            RESULT_ROOT.mkdir(parents=True, exist_ok=True)
            _write_json(RESULT_ROOT / "full-error.json", {"status": "FAIL", "error": str(exc)})
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, default=str))
    return 0
