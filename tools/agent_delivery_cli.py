"""CLI for deterministic G3-D Agent/Prompt delivery."""

from __future__ import annotations

import argparse
import json
from typing import Any

from tools.agent_delivery.authority import build_authority_artifacts, validate_authority_artifacts
from tools.agent_delivery.registry import build_registries, validate_registries
from tools.agent_delivery.trace import build_traces, replay_trace, validate_traces


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-D Agent/Prompt delivery tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-authority", help="Build G3-D-A authority artifacts")
    subparsers.add_parser("build-registries", help="Build G3-D-B Prompt and Skill registries")
    subparsers.add_parser("build-traces", help="Build G3-D-C normalized traces")
    replay = subparsers.add_parser("replay", help="Replay one frozen normalized trace offline")
    replay.add_argument("--trace", required=True)
    subparsers.add_parser("describe", help="Describe and verify current G3-D authority artifacts")
    subparsers.add_parser("verify", help="Verify current G3-D delivery artifacts")
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority_artifacts())
    if args.command == "build-registries":
        return _emit(build_registries())
    if args.command == "build-traces":
        return _emit(build_traces())
    if args.command == "replay":
        return _emit(replay_trace(args.trace))
    authority = validate_authority_artifacts()
    registries = validate_registries()
    traces = validate_traces()
    return _emit({
        "schema_version": "g3-d-delivery-verification-v1",
        "status": "PASS" if authority["status"] == registries["status"] == traces["status"] == "PASS" else "FAIL",
        "authority": authority,
        "registries": registries,
        "traces": traces,
    })


if __name__ == "__main__":
    raise SystemExit(main())
