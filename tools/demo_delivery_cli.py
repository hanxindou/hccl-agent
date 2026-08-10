"""CLI for deterministic G3-F competition demo and video delivery."""

from __future__ import annotations

import argparse
import json
from typing import Any

from tools.demo_delivery.authority import build_authority, validate_authority


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-F competition demo/video delivery tooling")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build-authority", help="Build G3-F-A authority and production contracts")
    sub.add_parser("describe", help="Validate current G3-F-A contracts read-only")
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority())
    return _emit(validate_authority())


if __name__ == "__main__":
    raise SystemExit(main())

