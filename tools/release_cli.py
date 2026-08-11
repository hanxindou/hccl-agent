"""Unified G3-G release-audit CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.release_audit.authority import build_authority, validate_authority
from tools.release_audit.audits import build_audits, validate_audits
from tools.release_audit.cold_start import compare_runs, finalize_cold_start_results, run_clean_worktree
from tools.release_audit.common import RELEASE_ROOT, ROOT
from tools.release_audit.package import build_candidate, validate_release_metadata, verify_candidate
from tools.release_audit.finalize import freeze_evidence, run_clean_extraction, verify_final_evidence, synchronize_final_release_state


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-G cold-start and final release audit")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-authority")
    sub.add_parser("describe")
    sub.add_parser("preflight")
    sub.add_parser("build-audits")
    sub.add_parser("audit")
    candidate = sub.add_parser("build-candidate")
    candidate.add_argument("--no-write-tracked-metadata", action="store_true")
    sub.add_parser("verify-candidate")
    sub.add_parser("verify-release-metadata")
    extract = sub.add_parser("clean-extraction")
    extract.add_argument("--archive")
    freeze_release = sub.add_parser("freeze-evidence")
    freeze_release.add_argument("--output", required=True)
    freeze_release.add_argument("--focused-passed", required=True, type=int)
    freeze_release.add_argument("--pytest-passed", required=True, type=int)
    freeze_release.add_argument("--pytest-skipped", required=True, type=int)
    freeze_release.add_argument("--ctest-passed", required=True, type=int)
    freeze_release.add_argument("--linux-validation-ok", action="store_true")
    verify_evidence = sub.add_parser("verify-evidence")
    verify_evidence.add_argument("--evidence", required=True)
    sync = sub.add_parser("sync-final-state")
    sync.add_argument("--evidence", required=True)
    cold = sub.add_parser("cold-start")
    cold.add_argument("--run-id", choices=["run-1", "run-2"], required=True)
    cold.add_argument("--output", required=True)
    compare = sub.add_parser("compare-cold-start")
    compare.add_argument("--run-1", required=True)
    compare.add_argument("--run-2", required=True)
    compare.add_argument("--output", required=True)
    finalize = sub.add_parser("finalize-cold-start")
    finalize.add_argument("--run-1", required=True)
    finalize.add_argument("--run-2", required=True)
    finalize.add_argument("--comparison", required=True)
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority())
    if args.command in {"describe", "preflight"}:
        return _emit(validate_authority())
    if args.command == "build-audits":
        return _emit(build_audits())
    if args.command == "audit":
        return _emit(validate_audits())
    if args.command == "build-candidate":
        return _emit(build_candidate(write_tracked_metadata=not args.no_write_tracked_metadata))
    if args.command == "verify-candidate":
        return _emit(verify_candidate())
    if args.command == "verify-release-metadata":
        return _emit(validate_release_metadata())
    if args.command == "clean-extraction":
        archive = Path(args.archive) if args.archive else None
        if archive is not None and not archive.is_absolute():
            archive = ROOT / archive
        return _emit(run_clean_extraction(archive))
    if args.command == "freeze-evidence":
        regression = {
            "schema_version": "g3-g-regression-summary-v1",
            "status": "PASS" if args.linux_validation_ok else "FAIL",
            "focused_g3_g_tests": {"status": "PASS", "passed": args.focused_passed},
            "full_pytest": {"status": "PASS", "passed": args.pytest_passed, "skipped": args.pytest_skipped, "skip_increase": False},
            "ctest": {"status": "PASS", "passed": args.ctest_passed},
            "linux_cpu_sim_validation": {"status": "PASS" if args.linux_validation_ok else "FAIL", "sentinel": "LINUX_CPU_SIM_VALIDATION_OK" if args.linux_validation_ok else None},
            "benchmark_rerun": False, "runtime_api_calls": [],
        }
        return _emit(freeze_evidence(Path(args.output), regression))
    if args.command == "verify-evidence":
        evidence = Path(args.evidence)
        return _emit(verify_final_evidence(evidence if evidence.is_absolute() else ROOT / evidence))
    if args.command == "sync-final-state":
        evidence = Path(args.evidence)
        return _emit(synchronize_final_release_state(evidence if evidence.is_absolute() else ROOT / evidence))
    if args.command == "cold-start":
        output = Path(args.output)
        return _emit(run_clean_worktree(args.run_id, output if output.is_absolute() else ROOT / output))
    if args.command == "compare-cold-start":
        paths = [Path(args.run_1), Path(args.run_2), Path(args.output)]
        paths = [path if path.is_absolute() else ROOT / path for path in paths]
        return _emit(compare_runs(paths[0], paths[1], paths[2]))
    if args.command == "finalize-cold-start":
        paths = [Path(args.run_1), Path(args.run_2), Path(args.comparison)]
        paths = [path if path.is_absolute() else ROOT / path for path in paths]
        return _emit(finalize_cold_start_results(paths[0], paths[1], paths[2]))
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
