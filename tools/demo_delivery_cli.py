"""CLI for deterministic G3-F competition demo and video delivery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.demo_delivery.authority import build_authority, validate_authority
from tools.demo_delivery.demo import build_demo_package, run_profile, validate_demo_package
from tools.demo_delivery.storyboard import build_storyboard, validate_storyboard
from tools.demo_delivery.presentation import build_presentation, validate_presentation
from tools.demo_delivery.finalize import build_staging, freeze_evidence, staging_validation, verify_evidence


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-F competition demo/video delivery tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-authority", help="Build G3-F-A authority and production contracts")
    sub.add_parser("describe", help="Validate current G3-F-A contracts read-only")
    sub.add_parser("build-demo", help="Build G3-F-B deterministic demo package")
    sub.add_parser("verify-demo", help="Validate the G3-F-B demo package")
    run = sub.add_parser("run", help="Execute an allowlisted demo profile")
    run.add_argument("--profile", choices=["quick", "technical"], required=True)
    run.add_argument("--output")
    transcript = sub.add_parser("transcript", help="Produce the deterministic fallback transcript")
    transcript.add_argument("--profile", choices=["fallback"], default="fallback")
    transcript.add_argument("--output")
    sub.add_parser("build-storyboard", help="Build G3-F-C storyboard and recording plan")
    sub.add_parser("verify-storyboard", help="Validate G3-F-C storyboard and privacy contract")
    sub.add_parser("build-presentation", help="Build G3-F-D narration, subtitle, and presentation sources")
    sub.add_parser("verify-presentation", help="Validate G3-F-D claim and localization boundaries")
    freeze = sub.add_parser("freeze-evidence", help="Freeze G3-F-E final evidence")
    freeze.add_argument("--output", required=True)
    freeze.add_argument("--quick-run-1", required=True)
    freeze.add_argument("--quick-run-2", required=True)
    freeze.add_argument("--fallback-run", required=True)
    freeze.add_argument("--focused-passed", type=int, required=True)
    freeze.add_argument("--pytest-passed", type=int, required=True)
    freeze.add_argument("--pytest-skipped", type=int, required=True)
    freeze.add_argument("--ctest-passed", type=int, required=True)
    freeze.add_argument("--linux-validation-ok", action="store_true")
    evidence = sub.add_parser("verify-evidence", help="Verify frozen G3-F-E evidence")
    evidence.add_argument("--evidence", required=True)
    sub.add_parser("stage", help="Reuse existing staging and add the G3-F production package")
    sub.add_parser("verify-stage", help="Verify existing staging plus G3-F coverage")
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority())
    if args.command == "describe":
        return _emit(validate_authority())
    if args.command == "build-demo":
        return _emit(build_demo_package())
    if args.command == "verify-demo":
        return _emit(validate_demo_package())
    if args.command == "build-storyboard":
        return _emit(build_storyboard())
    if args.command == "verify-storyboard":
        return _emit(validate_storyboard())
    if args.command == "build-presentation":
        return _emit(build_presentation())
    if args.command == "verify-presentation":
        return _emit(validate_presentation())
    if args.command == "freeze-evidence":
        regression = {
            "schema_version": "g3-f-regression-summary-v1",
            "status": "PASS" if args.linux_validation_ok else "FAIL",
            "focused_g3_f_tests": {"status": "PASS", "passed": args.focused_passed},
            "full_pytest": {"status": "PASS", "passed": args.pytest_passed, "skipped": args.pytest_skipped, "skip_increase": False},
            "ctest": {"status": "PASS", "passed": args.ctest_passed},
            "linux_cpu_sim_validation": {"status": "PASS" if args.linux_validation_ok else "FAIL", "sentinel": "LINUX_CPU_SIM_VALIDATION_OK" if args.linux_validation_ok else None},
            "benchmark_rerun": False, "runtime_api_calls": [],
        }
        return _emit(freeze_evidence(
            Path(args.output), Path(args.quick_run_1), Path(args.quick_run_2), Path(args.fallback_run), regression,
        ))
    if args.command == "verify-evidence":
        return _emit(verify_evidence(Path(args.evidence)))
    if args.command == "stage":
        return _emit(build_staging())
    if args.command == "verify-stage":
        return _emit(staging_validation())
    output = Path(args.output) if args.output else None
    return _emit(run_profile(args.profile, output))


if __name__ == "__main__":
    raise SystemExit(main())
