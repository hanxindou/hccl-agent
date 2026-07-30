#!/usr/bin/env python3
"""Write G2-F-2 build-only evidence without loading CANN shared libraries."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import List, Tuple


FORBIDDEN_CPU_SIM_SYMBOLS = ("hcclCommInit", "hcclSetRank", "hcclAllReduce", "hcclAllGather", "hcclReduceScatter")
REQUIRED_DIRECT_SYMBOLS = ("hccl_direct_session_create", "hccl_direct_session_destroy", "hccl_direct_session_state", "hccl_direct_status_string")
FORBIDDEN_CPU_SIM_DEPENDENCY_MARKERS = ("libhccl.so", "libhcomm.so", "libacl_rt.so", "libruntime.so")


def sha256(path: Path) -> str:
    """Return the SHA-256 of a build artifact without executing it."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_symbols(archive: Path) -> List[str]:
    """Read globally defined archive symbols with nm; the archive is never loaded."""
    output = subprocess.run(
        ["nm", "-g", "--defined-only", str(archive)],
        check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    return [line.rsplit(" ", 1)[-1] for line in output.splitlines() if line.strip() and " " in line]


def cpu_sim_dependencies(library: Path) -> Tuple[str, List[str]]:
    """Read CPU_SIM dependencies and reject accidental official runtime linkage."""
    output = subprocess.run(
        ["ldd", str(library)], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout
    forbidden = [marker for marker in FORBIDDEN_CPU_SIM_DEPENDENCY_MARKERS if marker in output]
    return output, forbidden


def write_evidence(output: Path, archive: Path, cache: Path, cpu_sim_library: Path, symbols: List[str]) -> None:
    """Create evidence files and SHA256SUMS for a verified compile-only target."""
    output.mkdir(parents=True, exist_ok=False)
    forbidden = [symbol for symbol in symbols if symbol in FORBIDDEN_CPU_SIM_SYMBOLS]
    missing = [symbol for symbol in REQUIRED_DIRECT_SYMBOLS if symbol not in symbols]
    cpu_sim_ldd, cpu_sim_forbidden_dependencies = cpu_sim_dependencies(cpu_sim_library)
    report = {
        "schema_version": "g2-f-readiness-v1",
        "checkpoint": "G2-F-2",
        "status": "BUILD_ONLY_PASS" if not forbidden and not missing and not cpu_sim_forbidden_dependencies else "FAIL",
        "passed": not forbidden and not missing and not cpu_sim_forbidden_dependencies,
        "runtime_api_calls": [],
        "link_mode": "STATIC_COMPILE_ONLY",
        "archive": {"path": str(archive), "sha256": sha256(archive)},
        "cmake_cache": {"path": str(cache), "sha256": sha256(cache)},
        "direct_symbols": list(REQUIRED_DIRECT_SYMBOLS),
        "forbidden_cpu_sim_symbols": forbidden,
        "missing_direct_symbols": missing,
        "cpu_sim_library": str(cpu_sim_library),
        "cpu_sim_cann_dependencies": cpu_sim_forbidden_dependencies,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "symbols.txt").write_text("\n".join(symbols) + "\n", encoding="utf-8")
    (output / "cpu_sim_ldd.txt").write_text(cpu_sim_ldd, encoding="utf-8")
    (output / "README.md").write_text(
        "# G2-F-2 Build-only Direct Adapter Evidence\n\n"
        f"- Status: `{report['status']}`\n"
        "- Target: static `hccl_direct_adapter`; no official CANN shared library was linked or loaded.\n"
        "- Runtime API calls: none. No device, context, stream, communicator, buffer, or collective exists in this checkpoint.\n",
        encoding="utf-8",
    )
    sums = []
    for path in sorted(output.iterdir()):
        if path.name != "SHA256SUMS":
            sums.append(f"{sha256(path)}  {path.name}")
    (output / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("build-only archive ABI/symbol isolation verification failed")


def main() -> int:
    """Parse arguments and write one build-only evidence directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--cmake-cache", type=Path, required=True)
    parser.add_argument("--cpu-sim-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_evidence(
        args.output, args.archive, args.cmake_cache, args.cpu_sim_library, archive_symbols(args.archive)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
