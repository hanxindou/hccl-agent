"""Unified deterministic CLI for the G3-C formal report suite."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from tools.reporting.claim_builder import build_claim_ledger
from tools.reporting.evidence_reader import (
    CLAIM_LEDGER, DATA_LEDGER, REPORT_ROOT, ROOT, evidence_inventory, read_json, source_commit, write_json,
)
from tools.reporting.final_evidence import create_final_evidence
from tools.reporting.ledger_builder import build_data_ledger
from tools.reporting.report_renderer import render_reports
from tools.reporting.report_verifier import verify_all
from tools.reporting.schemas import CHART_FILES, REPORT_FILES, TRUTH_LABELS, USER_ACTIONS
from tools.reporting.staging import build_stage, verify_stage


def build_command() -> dict[str, Any]:
    inventory = evidence_inventory()
    ledger = build_data_ledger()
    write_json(DATA_LEDGER, ledger)
    claims = build_claim_ledger({row["metric_id"] for row in ledger["metrics"]})
    write_json(CLAIM_LEDGER, claims)
    rendered = render_reports(ledger, claims)
    verification = verify_all(persist=True)
    return {"schema_version": "g3-c-report-build-v1", "status": "PASS",
            "source_commit": inventory["source_commit"], "metric_count": ledger["metric_count"],
            "claim_count": claims["claim_count"], "formal_report_count": rendered["report_count"],
            "chart_count": rendered["chart_data"]["chart_count"], "verification": verification["status"],
            "performance_benchmark_executed": False, "real_device_api_executed": False, "runtime_api_calls": []}


def describe_command() -> dict[str, Any]:
    inventory = evidence_inventory()
    ledger = read_json(DATA_LEDGER) if DATA_LEDGER.is_file() else {"metric_count": 0}
    claims = read_json(CLAIM_LEDGER) if CLAIM_LEDGER.is_file() else {"claim_count": 0}
    return {"schema_version": "g3-c-report-description-v1", "status": "PASS",
            "read_only": True, "source_commit": source_commit(), "evidence_roots": inventory["families"],
            "report_count": sum((REPORT_ROOT / name).is_file() for name in REPORT_FILES),
            "metric_count": ledger["metric_count"], "claim_count": claims["claim_count"],
            "chart_count": len(CHART_FILES), "user_action_required": list(USER_ACTIONS),
            "truth_identities": sorted(TRUTH_LABELS), "real_device_api_executed": False, "runtime_api_calls": []}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="python -m tools.report_cli")
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("verify")
    sub.add_parser("describe")
    sub.add_parser("stage")
    sub.add_parser("verify-stage")
    evidence = sub.add_parser("evidence")
    evidence.add_argument("--output", required=True)
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build_command()
        elif args.command == "verify":
            result = verify_all(persist=True)
        elif args.command == "describe":
            result = describe_command()
        elif args.command == "stage":
            result = build_stage()
        elif args.command == "verify-stage":
            result = verify_stage()
        elif args.command == "evidence":
            result = create_final_evidence(args.output)
        else:
            raise RuntimeError(f"unknown command: {args.command}")
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
