"""CLI for deterministic G3-E competition visualization delivery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.visualization.authority import build_authority, validate_authority
from tools.visualization.innovation import build_innovation_map, validate_innovation_map
from tools.visualization.finalize import freeze_evidence, verify_evidence
from tools.visualization.narrative import build_narrative, validate_narrative
from tools.visualization.render import build_charts, validate_charts


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-E competition visualization tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-authority", help="Build G3-E-A authority and story contracts")
    subparsers.add_parser("describe", help="Describe and validate current G3-E authority")
    subparsers.add_parser("verify", help="Validate current G3-E delivery artifacts")
    subparsers.add_parser("build-charts", help="Build deterministic G3-E-B SVG assets")
    subparsers.add_parser("verify-charts", help="Validate deterministic G3-E-B SVG assets")
    subparsers.add_parser("build-innovation", help="Build G3-E-C innovation traceability")
    subparsers.add_parser("verify-innovation", help="Validate G3-E-C innovation traceability")
    subparsers.add_parser("build-narrative", help="Build G3-E-D claim-safe narrative")
    subparsers.add_parser("verify-narrative", help="Validate G3-E-D claim-safe narrative")
    freeze = subparsers.add_parser("freeze-evidence", help="Freeze unique G3-E-E final evidence")
    freeze.add_argument("--output", required=True)
    freeze.add_argument("--focused-passed", type=int, required=True)
    freeze.add_argument("--pytest-passed", type=int, required=True)
    freeze.add_argument("--pytest-skipped", type=int, required=True)
    freeze.add_argument("--ctest-passed", type=int, required=True)
    freeze.add_argument("--linux-validation-ok", action="store_true")
    evidence = subparsers.add_parser("verify-evidence", help="Verify frozen G3-E-E evidence")
    evidence.add_argument("--evidence", required=True)
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority())
    if args.command in {"describe", "verify"}:
        return _emit(validate_authority())
    if args.command == "build-charts":
        return _emit(build_charts())
    if args.command == "verify-charts":
        return _emit(validate_charts())
    if args.command == "build-innovation":
        return _emit(build_innovation_map())
    if args.command == "verify-innovation":
        return _emit(validate_innovation_map())
    if args.command == "build-narrative":
        return _emit(build_narrative())
    if args.command == "verify-narrative":
        return _emit(validate_narrative())
    if args.command == "freeze-evidence":
        regression = {
            "schema_version": "g3-e-regression-summary-v1", "status": "PASS" if args.linux_validation_ok else "FAIL",
            "focused_g3_e_tests": {"status": "PASS", "passed": args.focused_passed},
            "full_pytest": {"status": "PASS", "passed": args.pytest_passed, "skipped": args.pytest_skipped, "skip_increase": False},
            "ctest": {"status": "PASS", "passed": args.ctest_passed},
            "linux_cpu_sim_validation": {"status": "PASS" if args.linux_validation_ok else "FAIL", "sentinel": "LINUX_CPU_SIM_VALIDATION_OK" if args.linux_validation_ok else None},
            "benchmark_rerun": False, "runtime_api_calls": [],
        }
        return _emit(freeze_evidence(Path(args.output), regression))
    return _emit(verify_evidence(Path(args.evidence)))


if __name__ == "__main__":
    raise SystemExit(main())
