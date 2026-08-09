"""CLI for deterministic G3-D Agent/Prompt delivery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from tools.agent_delivery.authority import build_authority_artifacts, validate_authority_artifacts
from tools.agent_delivery.registry import build_registries, validate_registries
from tools.agent_delivery.trace import build_traces, replay_trace, validate_traces
from tools.agent_delivery.documentation import build_documentation, validate_documentation
from tools.agent_delivery.common import ROOT
from tools.agent_delivery.finalize import freeze_evidence, verify_final_evidence


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-D Agent/Prompt delivery tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-authority", help="Build G3-D-A authority artifacts")
    subparsers.add_parser("build-registries", help="Build G3-D-B Prompt and Skill registries")
    subparsers.add_parser("build-traces", help="Build G3-D-C normalized traces")
    subparsers.add_parser("build-docs", help="Build G3-D-D provenance documentation")
    replay = subparsers.add_parser("replay", help="Replay one frozen normalized trace offline")
    replay.add_argument("--trace", required=True)
    subparsers.add_parser("describe", help="Describe and verify current G3-D authority artifacts")
    subparsers.add_parser("verify", help="Verify current G3-D delivery artifacts")
    freeze = subparsers.add_parser("freeze-evidence", help="Freeze final G3-D-E authority evidence")
    freeze.add_argument("--evidence-root", required=True)
    freeze.add_argument("--stage", default="dist/submission-staging")
    freeze.add_argument("--focused-passed", required=True, type=int)
    freeze.add_argument("--full-pytest-passed", required=True, type=int)
    freeze.add_argument("--full-pytest-skipped", required=True, type=int)
    freeze.add_argument("--ctest-passed", required=True, type=int)
    freeze.add_argument("--linux-validation-ok", action="store_true")
    final_verify = subparsers.add_parser("final-verify", help="Verify frozen G3-D-E authority evidence")
    final_verify.add_argument("--evidence-root", required=True)
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority_artifacts())
    if args.command == "build-registries":
        return _emit(build_registries())
    if args.command == "build-traces":
        return _emit(build_traces())
    if args.command == "build-docs":
        return _emit(build_documentation())
    if args.command == "replay":
        return _emit(replay_trace(args.trace))
    if args.command == "freeze-evidence":
        evidence_root = Path(args.evidence_root)
        stage_root = Path(args.stage)
        return _emit(freeze_evidence(
            evidence_root if evidence_root.is_absolute() else ROOT / evidence_root,
            stage_root if stage_root.is_absolute() else ROOT / stage_root,
            focused_passed=args.focused_passed,
            full_pytest_passed=args.full_pytest_passed,
            full_pytest_skipped=args.full_pytest_skipped,
            ctest_passed=args.ctest_passed,
            linux_validation_ok=args.linux_validation_ok,
        ))
    if args.command == "final-verify":
        evidence_root = Path(args.evidence_root)
        return _emit(verify_final_evidence(evidence_root if evidence_root.is_absolute() else ROOT / evidence_root))
    authority = validate_authority_artifacts()
    registries = validate_registries()
    traces = validate_traces()
    documentation = validate_documentation()
    return _emit({
        "schema_version": "g3-d-delivery-verification-v1",
        "status": "PASS" if authority["status"] == registries["status"] == traces["status"] == documentation["status"] == "PASS" else "FAIL",
        "authority": authority,
        "registries": registries,
        "traces": traces,
        "documentation": documentation,
    })


if __name__ == "__main__":
    raise SystemExit(main())
