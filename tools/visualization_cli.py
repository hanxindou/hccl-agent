"""CLI for deterministic G3-E competition visualization delivery."""

from __future__ import annotations

import argparse
import json
from typing import Any

from tools.visualization.authority import build_authority, validate_authority


def _emit(value: dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="G3-E competition visualization tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build-authority", help="Build G3-E-A authority and story contracts")
    subparsers.add_parser("describe", help="Describe and validate current G3-E authority")
    subparsers.add_parser("verify", help="Validate current G3-E delivery artifacts")
    args = parser.parse_args(argv)
    if args.command == "build-authority":
        return _emit(build_authority())
    return _emit(validate_authority())


if __name__ == "__main__":
    raise SystemExit(main())

