"""Shared deterministic helpers for G3-D delivery artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "docs/submission/agent_delivery"
G3_B2_ROOT = ROOT / "experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z"
G3_B3_ROOT = ROOT / "experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z"
G3_B3_AGENT_ROOT = ROOT / "experiments/feature_completion/evidence/g3_b3_d_agent_flow_20260807T150515Z"
G3_C_ROOT = ROOT / "experiments/submission/evidence/g3_c_20260809T000000Z"

G3_B2_SHA256SUMS_SHA256 = "99e81dc858e965fd339f2e2e1c711f85238479fb89521c5f8ebaf673f4c05483"
G3_B3_SHA256SUMS_SHA256 = "45b437e76c09a023f908cb8f724849bd93b3bd65fefb3cc4514251eb4af3e754"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True,
    )
    return completed.stdout.strip()


def tracked_files(prefixes: Iterable[str]) -> list[str]:
    values = git("ls-files", "--", *prefixes).splitlines()
    return sorted(value.replace("\\", "/") for value in values if value)


def verify_sha256sums(root: Path, expected_digest: str) -> dict[str, Any]:
    sums = root / "SHA256SUMS"
    actual_digest = sha256_file(sums)
    mismatches: list[str] = []
    checked = 0
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, name = line.split("  ", 1)
        target = root / name
        if not target.is_file() or sha256_file(target) != expected:
            mismatches.append(name)
        checked += 1
    return {
        "path": relative(root),
        "files_checked": checked,
        "sha256sums_sha256": actual_digest,
        "expected_sha256sums_sha256": expected_digest,
        "mismatches": mismatches,
        "status": "PASS" if actual_digest == expected_digest and not mismatches else "FAIL",
    }


def strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from strings(key)
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def assert_relative_repository_paths(value: Any) -> None:
    for item in strings(value):
        lowered = item.lower()
        if ":\\" in item or lowered.startswith(("/home/", "/users/", "/mnt/", "file://")):
            raise ValueError(f"local absolute path is forbidden: {item}")

