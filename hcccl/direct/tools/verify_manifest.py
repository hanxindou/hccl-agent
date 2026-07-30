#!/usr/bin/env python3
"""Read-only verifier for the frozen CANN/HCCL direct-API manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


SCHEMA_VERSION = "g2-f-direct-api-manifest-v1"
REQUIRED_LIBRARY_NAMES = {"hccl", "hcomm", "acl_rt"}


def load_manifest(path: Path) -> Dict[str, Any]:
    """Load and validate the static shape of a direct-API ABI manifest."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("unsupported direct API manifest schema")
    if manifest.get("status") != "SYMBOL_DISCOVERY_PASS":
        raise ValueError("manifest must be a symbol-discovery contract")
    libraries = manifest.get("libraries", [])
    names = {entry.get("name") for entry in libraries}
    if names != REQUIRED_LIBRARY_NAMES:
        raise ValueError("manifest must define hccl, hcomm, and acl_rt libraries")
    if not manifest.get("headers") or not manifest.get("api_contract", {}).get("functions"):
        raise ValueError("manifest must define headers and API functions")
    locality = manifest["api_contract"].get("collective_buffer_locality", {})
    if locality.get("status") != "UNRESOLVED":
        raise ValueError("collective buffer locality must remain unresolved in G2-F-1")
    for entry in libraries:
        if not entry.get("soname") or not entry.get("symbols") or not entry.get("sha256"):
            raise ValueError(f"incomplete library contract: {entry.get('name')}")
    return manifest


def _run(command: Iterable[str]) -> str:
    """Run a read-only inspection command and return its stdout."""
    return subprocess.run(
        list(command), check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def _sha256(path: Path) -> str:
    """Return a file SHA-256 without loading or executing the inspected file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve(template: str, cann_root: Path) -> Path:
    """Resolve the manifest's explicit CANN-root path template."""
    return Path(template.format(cann_root=str(cann_root)))


def verify_manifest(manifest: Dict[str, Any], cann_root: Path) -> Dict[str, Any]:
    """Verify headers, libraries, SONAMEs, NEEDED entries, and exported symbols."""
    result: Dict[str, Any] = {"headers": [], "libraries": [], "passed": True}
    for header in manifest["headers"]:
        path = _resolve(header["path"], cann_root)
        observed = _sha256(path)
        passed = observed == header["sha256"]
        result["headers"].append({"path": str(path), "sha256": observed, "passed": passed})
        result["passed"] = result["passed"] and passed

    for library in manifest["libraries"]:
        path = _resolve(library["path"], cann_root)
        dynamic = _run(["readelf", "-d", str(path)])
        symbols = _run(["nm", "-D", "--defined-only", str(path)])
        soname_ok = f"Library soname: [{library['soname']}]" in dynamic
        needed_ok = all(f"Shared library: [{entry}]" in dynamic for entry in library["needed"])
        missing_symbols = [symbol for symbol in library["symbols"] if f" {symbol}" not in symbols]
        sha_ok = _sha256(path) == library["sha256"]
        passed = soname_ok and needed_ok and sha_ok and not missing_symbols
        result["libraries"].append({
            "name": library["name"], "path": str(path), "sha256": _sha256(path),
            "soname_ok": soname_ok, "needed_ok": needed_ok, "missing_symbols": missing_symbols,
            "passed": passed,
        })
        result["passed"] = result["passed"] and passed
    return result


def _git_state(path: Path) -> Dict[str, str]:
    """Read official repository metadata using command-scoped safe.directory only."""
    base = ["git", f"-c", f"safe.directory={path}", "-C", str(path)]
    return {
        "branch": _run([*base, "branch", "--show-current"]).strip(),
        "commit": _run([*base, "rev-parse", "HEAD"]).strip(),
        "status_short": _run([*base, "status", "--short"]),
    }


def verify_repositories(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """Verify frozen official branch, commit, and clean tracked state."""
    result: Dict[str, Any] = {"passed": True, "repositories": {}}
    for name, expected in manifest["official_repositories"].items():
        observed = _git_state(Path(expected["path"]))
        passed = (
            observed["branch"] == expected["branch"]
            and observed["commit"] == expected["commit"]
            and observed["status_short"] == ""
        )
        result["repositories"][name] = {**observed, "passed": passed}
        result["passed"] = result["passed"] and passed
    return result


def write_evidence(output: Path, manifest_path: Path, report: Dict[str, Any], argv: List[str]) -> None:
    """Write G2-F-1 read-only evidence and a SHA256SUMS integrity file."""
    output.mkdir(parents=True, exist_ok=False)
    (output / "manifest.json").write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    (output / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "command.txt").write_text(" ".join(argv) + "\n", encoding="utf-8")
    (output / "README.md").write_text(
        "# G2-F-1 Direct API ABI Readiness Evidence\n\n"
        f"- Status: `{report['status']}`\n"
        "- Scope: read-only header, ELF, symbol, hash, and Git metadata verification.\n"
        "- Runtime API calls: none. No official shared library was loaded.\n"
        "- This evidence does not claim device, communicator, or collective validation.\n",
        encoding="utf-8",
    )
    lines = []
    for path in sorted(output.iterdir()):
        if path.name != "SHA256SUMS":
            lines.append(f"{_sha256(path)}  {path.name}")
    (output / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    """Run the manifest verifier without loading any official shared library."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cann-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = load_manifest(args.manifest)
    report = {
        "schema_version": "g2-f-readiness-v1",
        "checkpoint": "G2-F-1",
        "status": "SYMBOL_DISCOVERY_PASS",
        "runtime_api_calls": [],
        "manifest": verify_manifest(manifest, args.cann_root),
        "official_repositories": verify_repositories(manifest),
    }
    report["passed"] = report["manifest"]["passed"] and report["official_repositories"]["passed"]
    if not report["passed"]:
        report["status"] = "FAIL"
    if args.output:
        write_evidence(args.output, args.manifest, report, ["verify_manifest.py", *sys.argv[1:]])
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
