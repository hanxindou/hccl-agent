"""Shared helpers for claim-safe, offline G3-F delivery artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DELIVERY_ROOT = ROOT / "docs/submission/demo_video"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def verify_sha256sums(root: Path) -> dict[str, Any]:
    sums = root / "SHA256SUMS"
    if not sums.is_file():
        return {"status": "FAIL", "path": root.relative_to(ROOT).as_posix(), "errors": ["SHA256SUMS missing"]}
    errors: list[str] = []
    checked = 0
    for raw in sums.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        digest, separator, name = raw.partition("  ")
        if not separator or not name or len(digest) != 64:
            errors.append(f"invalid SHA256SUMS line: {raw}")
            continue
        target = root / name
        if not target.is_file():
            errors.append(f"missing payload: {name}")
            continue
        actual = sha256_file(target)
        if actual != digest:
            errors.append(f"digest mismatch: {name}")
        checked += 1
    return {
        "status": "PASS" if not errors else "FAIL",
        "path": root.relative_to(ROOT).as_posix(),
        "files_checked": checked,
        "sha256sums_sha256": sha256_file(sums),
        "errors": errors,
    }


def repository_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()

