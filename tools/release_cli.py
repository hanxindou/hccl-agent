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
