"""Read and verify frozen evidence without modifying it."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
G3_B2_ROOT = ROOT / "experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z"
G3_B3_ROOT = ROOT / "experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z"
REPORT_ROOT = ROOT / "docs/submission/reports"
CHART_ROOT = ROOT / "docs/submission/report_chart_data"
DATA_LEDGER = ROOT / "docs/submission/report_data_ledger.json"
CLAIM_LEDGER = ROOT / "docs/submission/report_claim_ledger.json"
REPORT_INDEX = ROOT / "docs/submission/technical_report_index.md"
STALE_AUDIT = ROOT / "docs/submission/stale_document_audit.md"
REQUIREMENT_DELTA = ROOT / "docs/submission/g3_c_requirement_delta.json"
STAGE_ROOT = ROOT / "dist/g3-c-report-staging"
RESULT_ROOT = ROOT / "dist/g3-c-report-results"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8", newline="\n")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def resolve_pointer(document: Any, pointer: str) -> Any:
    if pointer in ("", "/"):
        return document
    current = document
    for raw in pointer.lstrip("/").split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(token)] if isinstance(current, list) else current[token]
    return current


def verify_sha256sums(directory: Path) -> dict[str, Any]:
    sums = directory / "SHA256SUMS"
    if not sums.is_file():
        raise RuntimeError(f"missing SHA256SUMS: {relative(directory)}")
    checked = 0
    for raw in sums.read_text(encoding="utf-8").splitlines():
        expected, name = raw.split("  ", 1)
        target = directory / name
        if not target.is_file() or sha256(target) != expected:
            raise RuntimeError(f"frozen evidence checksum mismatch: {relative(target)}")
        checked += 1
    return {
        "status": "PASS", "path": relative(directory), "files_checked": checked,
        "sha256sums_sha256": sha256(sums),
    }


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def source_commit() -> str:
    """Return the merged-main baseline, not a later G3-C reporting commit."""
    return git("merge-base", "HEAD", "main")


def evidence_inventory() -> dict[str, Any]:
    b2 = verify_sha256sums(G3_B2_ROOT)
    b3 = verify_sha256sums(G3_B3_ROOT)
    b2_manifest = read_json(G3_B2_ROOT / "manifest.json")
    b3_manifest = read_json(G3_B3_ROOT / "manifest.json")
    return {
        "schema_version": "g3-c-evidence-inventory-v1",
        "source_commit": source_commit(),
        "families": {
            "G3-B2": {**b2, "final_source_commit": b2_manifest["final_source_commit"],
                       "identity": "HISTORICAL_OPTIMIZATION_EVIDENCE"},
            "G3-B3": {**b3, "final_source_commit": b3_manifest["source_commit"],
                       "identity": "CURRENT_FINAL_FEATURE_EVIDENCE"},
        },
        "old_evidence_modified": False,
    }
