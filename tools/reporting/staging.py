"""Internal G3-C report staging with deterministic manifest and verification."""

from __future__ import annotations

import json
import shutil
from pathlib import Path, PurePosixPath
from typing import Any

from .evidence_reader import (
    CHART_ROOT, CLAIM_LEDGER, DATA_LEDGER, REPORT_INDEX, REPORT_ROOT, REQUIREMENT_DELTA,
    RESULT_ROOT, ROOT, STAGE_ROOT, STALE_AUDIT, relative, sha256, source_commit, write_json, write_text,
)


MARKER = ".g3_c_generated.json"


def _prepare_stage() -> None:
    if STAGE_ROOT.exists():
        if not (STAGE_ROOT / MARKER).is_file():
            raise RuntimeError("refusing to replace unmarked report staging directory")
        shutil.rmtree(STAGE_ROOT)
    STAGE_ROOT.mkdir(parents=True)
    write_json(STAGE_ROOT / MARKER, {"owner": "tools.report_cli", "source_commit": source_commit()})


def _copy_file(source: Path, destination: Path, source_map: dict[str, str]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    source_map[destination.relative_to(STAGE_ROOT).as_posix()] = relative(source)


def _copy_tree(source: Path, destination: Path, source_map: dict[str, str], suffixes: set[str]) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file() and path.suffix in suffixes and "__pycache__" not in path.parts:
            _copy_file(path, destination / path.relative_to(source), source_map)


def build_stage() -> dict[str, Any]:
    _prepare_stage()
    source_map: dict[str, str] = {}
    _copy_tree(REPORT_ROOT, STAGE_ROOT / "docs/submission/reports", source_map, {".md"})
    _copy_tree(CHART_ROOT, STAGE_ROOT / "docs/submission/report_chart_data", source_map, {".json"})
    for source in (DATA_LEDGER, CLAIM_LEDGER, REPORT_INDEX, STALE_AUDIT, REQUIREMENT_DELTA):
        _copy_file(source, STAGE_ROOT / relative(source), source_map)
    _copy_tree(ROOT / "tools/reporting", STAGE_ROOT / "tools/reporting", source_map, {".py"})
    _copy_file(ROOT / "tools/report_cli.py", STAGE_ROOT / "tools/report_cli.py", source_map)
    if (ROOT / "tests/reporting").is_dir():
        _copy_tree(ROOT / "tests/reporting", STAGE_ROOT / "tests/reporting", source_map, {".py"})
    payloads = [path for path in sorted(STAGE_ROOT.rglob("*")) if path.is_file() and path.name not in {MARKER, "MANIFEST.json", "SHA256SUMS"}]
    entries = [{
        "staging_path": path.relative_to(STAGE_ROOT).as_posix(),
        "source_path": source_map[path.relative_to(STAGE_ROOT).as_posix()],
        "sha256": sha256(path), "size_bytes": path.stat().st_size,
    } for path in payloads]
    manifest = {
        "schema_version": "g3-c-report-staging-v1", "source_commit": source_commit(),
        "release_ready": False, "final_release_created": False,
        "controlled_competition_doc_included": False, "official_assets_included": False,
        "private_logs_included": False, "entries": entries,
    }
    write_json(STAGE_ROOT / "MANIFEST.json", manifest)
    checksummed = [path for path in sorted(STAGE_ROOT.rglob("*")) if path.is_file() and path.name not in {MARKER, "SHA256SUMS"}]
    write_text(STAGE_ROOT / "SHA256SUMS", "".join(
        f"{sha256(path)}  {path.relative_to(STAGE_ROOT).as_posix()}\n" for path in checksummed))
    return verify_stage()


def verify_stage() -> dict[str, Any]:
    if not (STAGE_ROOT / MARKER).is_file():
        raise RuntimeError("report staging marker missing")
    manifest = json.loads((STAGE_ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("source_commit") != source_commit():
        raise RuntimeError("report staging source commit drift")
    for entry in manifest["entries"]:
        pure = PurePosixPath(entry["staging_path"])
        if pure.is_absolute() or ".." in pure.parts:
            raise RuntimeError(f"unsafe staging path: {pure}")
        path = STAGE_ROOT / Path(*pure.parts)
        if not path.is_file() or sha256(path) != entry["sha256"] or path.stat().st_size != entry["size_bytes"]:
            raise RuntimeError(f"staging manifest mismatch: {pure}")
        if Path(entry["source_path"]).is_absolute():
            raise RuntimeError(f"absolute source path in staging: {entry['source_path']}")
    sums = (STAGE_ROOT / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    covered: set[str] = set()
    for raw in sums:
        expected, name = raw.split("  ", 1)
        pure = PurePosixPath(name)
        if pure.is_absolute() or ".." in pure.parts:
            raise RuntimeError(f"unsafe checksum path: {name}")
        path = STAGE_ROOT / Path(*pure.parts)
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"staging checksum mismatch: {name}")
        covered.add(name)
    actual = {path.relative_to(STAGE_ROOT).as_posix() for path in STAGE_ROOT.rglob("*")
              if path.is_file() and path.name not in {MARKER, "SHA256SUMS"}}
    if covered != actual:
        raise RuntimeError("staging SHA256SUMS coverage mismatch")
    required = {
        "docs/submission/report_data_ledger.json", "docs/submission/report_claim_ledger.json",
        "docs/submission/technical_report_index.md", "docs/submission/stale_document_audit.md",
        "docs/submission/g3_c_requirement_delta.json", "tools/report_cli.py",
    }
    if not required <= actual:
        raise RuntimeError(f"staging required files missing: {sorted(required - actual)}")
    text_payload = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in (STAGE_ROOT / "docs/submission").rglob("*")
        if path.is_file() and path.suffix in {".md", ".json"}
    )
    if "C:\\Users\\" in text_payload or "/home/" in text_payload or "/mnt/" in text_payload:
        raise RuntimeError("absolute private path leaked into report staging")
    result = {
        "schema_version": "g3-c-staging-verification-v1", "status": "PASS",
        "source_commit": source_commit(), "file_count": len(actual) + 1,
        "manifest_entries": len(manifest["entries"]), "sha256_entries": len(covered),
        "official_assets_included": False, "controlled_competition_doc_included": False,
        "private_logs_included": False, "absolute_private_paths": [],
        "real_device_api_executed": False, "runtime_api_calls": [],
    }
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    write_json(RESULT_ROOT / "staging_verification.json", result)
    return result
