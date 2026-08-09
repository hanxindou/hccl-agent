"""Verify G3-C ledgers, reports, chart data, claims, and truth boundaries."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .evidence_reader import (
    CHART_ROOT, CLAIM_LEDGER, DATA_LEDGER, G3_B2_ROOT, G3_B3_ROOT, REPORT_INDEX,
    REPORT_ROOT, REQUIREMENT_DELTA, ROOT, STALE_AUDIT, read_json, relative,
    resolve_pointer, sha256, source_commit, verify_sha256sums, write_json,
)
from .ledger_builder import _display, _unit
from .schemas import (
    CHART_FILES, CLAIM_FIELDS, METRIC_FIELDS, PROHIBITED_TRUTH_LABELS, REPORT_FILES,
    REPORT_REQUIRED_HEADINGS, TRUTH_LABELS,
)


ABSOLUTE_PATH_PATTERNS = (
    re.compile(r"[A-Za-z]:[\\/](?:Users|projects)[\\/]", re.IGNORECASE),
    re.compile(r"/(?:home|mnt/[a-z]|Users)/"),
)

FORBIDDEN_ASSERTIONS = (
    re.compile(r"Real-device Validated:\s*`?true", re.IGNORECASE),
    re.compile(r"Runtime API Executed:\s*`?true", re.IGNORECASE),
    re.compile(r"direct_hccl_api_call\s*[=:]\s*true", re.IGNORECASE),
    re.compile(r"real_ascend_npu_validated\s*[=:]\s*true", re.IGNORECASE),
    re.compile(r"measured_on_real_npu\s*[=:]\s*true", re.IGNORECASE),
    re.compile(r"45\.59\s*%?\s*(?:real HCCL|NPU|training) speedup", re.IGNORECASE),
    re.compile(r"modeled_wire_bytes\s*[=:]\s*physically measured", re.IGNORECASE),
)


def _derived_value(row: dict[str, Any], document: Any) -> Any:
    selected = resolve_pointer(document, row["source_json_pointer"])
    method = row["extraction_method"]
    if method == "json_pointer":
        return selected
    if method == "derived:length":
        return len(selected)
    if method == "derived:all_canonical_equal":
        return all(item["canonical_equal"] for item in selected)
    if method == "derived:true_count:correctness":
        return sum(1 for item in selected if item["correctness"] is True)
    raise ValueError(f"unsupported extraction method: {method}")


def verify_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    if ledger.get("schema_version") != "g3-c-report-data-ledger-v1":
        raise ValueError("data ledger schema mismatch")
    if ledger.get("source_commit") != source_commit():
        raise ValueError("data ledger source commit drift")
    metrics = ledger.get("metrics", [])
    if ledger.get("metric_count") != len(metrics) or not metrics:
        raise ValueError("data ledger metric_count mismatch or empty ledger")
    ids: set[str] = set()
    sources: dict[Path, Any] = {}
    for row in metrics:
        missing = [field for field in METRIC_FIELDS if field not in row]
        if missing:
            raise ValueError(f"metric fields missing for {row.get('metric_id')}: {missing}")
        metric_id = row["metric_id"]
        if metric_id in ids:
            raise ValueError(f"duplicate metric id: {metric_id}")
        ids.add(metric_id)
        if row["truth_label"] not in TRUTH_LABELS or row["truth_label"] in PROHIBITED_TRUTH_LABELS:
            raise ValueError(f"unsupported metric truth label: {metric_id}")
        source = ROOT / row["source_path"]
        if Path(row["source_path"]).is_absolute() or not source.is_file():
            raise ValueError(f"invalid metric source path: {metric_id}")
        if sha256(source) != row["source_sha256"]:
            raise ValueError(f"metric source SHA drift: {metric_id}")
        document = sources.setdefault(source, read_json(source))
        expected = _derived_value(row, document)
        if expected != row["value"]:
            raise ValueError(f"metric value/source mismatch: {metric_id}")
        expected_unit = _unit(row["source_json_pointer"].rsplit("/", 1)[-1] or metric_id.rsplit(".", 1)[-1], row["value"])
        if row["unit"] != expected_unit:
            raise ValueError(f"metric unit mismatch: {metric_id}")
        display, rounding = _display(row["value"], row["unit"])
        if row["display_value"] != display or row["rounding_rule"] != rounding:
            raise ValueError(f"metric rounding/display mismatch: {metric_id}")
    snapshots = ledger["evidence_snapshots"]
    current_b2 = verify_sha256sums(G3_B2_ROOT)
    current_b3 = verify_sha256sums(G3_B3_ROOT)
    if snapshots["G3-B2"]["sha256sums_sha256"] != current_b2["sha256sums_sha256"]:
        raise ValueError("G3-B2 evidence snapshot drift")
    if snapshots["G3-B3"]["sha256sums_sha256"] != current_b3["sha256sums_sha256"]:
        raise ValueError("G3-B3 evidence snapshot drift")
    return {"status": "PASS", "metric_count": len(metrics), "unique_metric_ids": len(ids),
            "source_file_count": len(sources), "g3_b2_sha": current_b2["sha256sums_sha256"],
            "g3_b3_sha": current_b3["sha256sums_sha256"]}


def verify_claims(claims: dict[str, Any], metric_ids: set[str]) -> dict[str, Any]:
    if claims.get("schema_version") != "g3-c-report-claim-ledger-v1":
        raise ValueError("claim ledger schema mismatch")
    rows = claims.get("claims", [])
    if claims.get("claim_count") != len(rows) or not rows:
        raise ValueError("claim_count mismatch or empty claim ledger")
    ids: set[str] = set()
    for row in rows:
        missing = [field for field in CLAIM_FIELDS if field not in row]
        if missing:
            raise ValueError(f"claim fields missing: {row.get('claim_id')}: {missing}")
        if row["claim_id"] in ids:
            raise ValueError(f"duplicate claim id: {row['claim_id']}")
        ids.add(row["claim_id"])
        if row["truth_label"] not in TRUTH_LABELS:
            raise ValueError(f"invalid claim truth: {row['claim_id']}")
        if row["status"] != "SUPPORTED" or not row["allowed_wording"] or not row["prohibited_wording"]:
            raise ValueError(f"incomplete claim boundary: {row['claim_id']}")
        missing_metrics = sorted(set(row["metric_refs"]) - metric_ids)
        if missing_metrics:
            raise ValueError(f"claim metric refs missing: {row['claim_id']} {missing_metrics}")
        for evidence in row["evidence_refs"]:
            path = ROOT / evidence
            if Path(evidence).is_absolute() or not path.exists():
                raise ValueError(f"claim evidence missing: {row['claim_id']} {evidence}")
    required = {"C-SPARSE-001", "C-CRC-001", "C-RETRY-001", "C-BP-001", "C-DIRECT-001",
                "C-DIRECT-002", "C-INT8-001", "C-PAIR-001", "C-PERF-001", "C-PERF-002"}
    if not required <= ids:
        raise ValueError(f"required claim boundaries missing: {sorted(required - ids)}")
    return {"status": "PASS", "claim_count": len(rows), "unique_claim_ids": len(ids),
            "truth_identities": sorted({row["truth_label"] for row in rows})}


def _verify_links(path: Path, text: str) -> int:
    checked = 0
    for match in re.finditer(r"\[[^]]+\]\(([^)]+)\)", text):
        target = match.group(1).split("#", 1)[0]
        if not target or "://" in target or target.startswith("#"):
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(ROOT.resolve())
        except ValueError as exc:
            raise ValueError(f"link escapes repository: {relative(path)} -> {target}") from exc
        if not resolved.exists():
            raise ValueError(f"broken relative link: {relative(path)} -> {target}")
        checked += 1
    return checked


def verify_reports(ledger: dict[str, Any]) -> dict[str, Any]:
    metric_index = {row["metric_id"]: row for row in ledger["metrics"]}
    missing = [name for name in REPORT_FILES if not (REPORT_ROOT / name).is_file()]
    if missing or not REPORT_INDEX.is_file() or not STALE_AUDIT.is_file() or not REQUIREMENT_DELTA.is_file():
        raise ValueError(f"required reporting artifacts missing: {missing}")
    links = markers = 0
    for name in REPORT_FILES:
        path = REPORT_ROOT / name
        text = path.read_text(encoding="utf-8")
        if name not in {"README.md", "report_source_index.md"}:
            for heading in REPORT_REQUIRED_HEADINGS:
                if heading not in text:
                    raise ValueError(f"required report heading missing: {name} {heading}")
            for header in ("Report Status:", "Source Commit:", "Evidence Snapshot:", "Execution Identity:",
                           "Real-device Validated:", "Runtime API Executed:", "Applicable Checkpoints:"):
                if header not in text:
                    raise ValueError(f"report header missing: {name} {header}")
            if ledger["source_commit"] not in text:
                raise ValueError(f"report source commit missing: {name}")
        for pattern in ABSOLUTE_PATH_PATTERNS:
            if pattern.search(text):
                raise ValueError(f"absolute private path in report: {name}")
        for pattern in FORBIDDEN_ASSERTIONS:
            if pattern.search(text):
                raise ValueError(f"forbidden positive claim in report: {name}: {pattern.pattern}")
        links += _verify_links(path, text)
        for line in text.splitlines():
            for metric_id in re.findall(r"<!-- metric:([^ ]+) -->", line):
                if metric_id not in metric_index or metric_index[metric_id]["display_value"] not in line:
                    raise ValueError(f"report metric marker mismatch: {name} {metric_id}")
                markers += 1
    index_text = REPORT_INDEX.read_text(encoding="utf-8")
    links += _verify_links(REPORT_INDEX, index_text)
    if "CURRENT FINAL FEATURE BASELINE" not in STALE_AUDIT.read_text(encoding="utf-8"):
        raise ValueError("stale-document audit does not identify current final baseline")
    delta = read_json(REQUIREMENT_DELTA)
    if delta.get("historical_matrix_modified") is not False or delta.get("real_device_api_executed") is not False:
        raise ValueError("requirement delta truth boundary failed")
    if markers < 20:
        raise ValueError("insufficient report numeric trace markers")
    return {"status": "PASS", "formal_report_count": 11, "report_file_count": len(REPORT_FILES),
            "metric_markers_checked": markers, "relative_links_checked": links,
            "absolute_private_paths": [], "forbidden_positive_claims": []}


def verify_chart_data(ledger: dict[str, Any]) -> dict[str, Any]:
    metric_index = {row["metric_id"]: row for row in ledger["metrics"]}
    checked_metrics = 0
    for name in CHART_FILES:
        path = CHART_ROOT / name
        if not path.is_file():
            raise ValueError(f"chart-data missing: {name}")
        payload = read_json(path)
        if payload.get("derived_from") != "docs/submission/report_data_ledger.json":
            raise ValueError(f"chart-data source mismatch: {name}")
        if payload.get("metric_refs") != [row["metric_id"] for row in payload.get("series", [])]:
            raise ValueError(f"chart metric_refs mismatch: {name}")
        for row in payload.get("series", []):
            metric = metric_index.get(row["metric_id"])
            if metric is None or any(row[key] != metric[key] for key in ("value", "unit", "display_value")):
                raise ValueError(f"chart-data not derived from ledger: {name} {row['metric_id']}")
            checked_metrics += 1
    return {"status": "PASS", "chart_count": len(CHART_FILES), "metric_rows_checked": checked_metrics,
            "single_numeric_source": "docs/submission/report_data_ledger.json"}


def _git_diff_from_main() -> list[str]:
    output = subprocess.run(["git", "diff", "--name-only", "main"], cwd=ROOT, check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def verify_all(*, persist: bool = True) -> dict[str, Any]:
    ledger = read_json(DATA_LEDGER)
    claims = read_json(CLAIM_LEDGER)
    ledger_result = verify_ledger(ledger)
    claim_result = verify_claims(claims, {row["metric_id"] for row in ledger["metrics"]})
    report_result = verify_reports(ledger)
    chart_result = verify_chart_data(ledger)
    changed = _git_diff_from_main()
    frozen_prefixes = (relative(G3_B2_ROOT) + "/", relative(G3_B3_ROOT) + "/")
    frozen_changes = [path for path in changed if path.startswith(frozen_prefixes)]
    if frozen_changes:
        raise ValueError(f"frozen authority evidence modified: {frozen_changes}")
    result = {
        "schema_version": "g3-c-report-verification-v1", "status": "PASS",
        "source_commit": source_commit(), "ledger": ledger_result, "claims": claim_result,
        "reports": report_result, "chart_data": chart_result,
        "numeric_traceability": {"status": "PASS", "metrics": ledger_result["metric_count"],
                                 "report_markers": report_result["metric_markers_checked"]},
        "truth_identity_audit": {"status": "PASS", "valid_identities": sorted(TRUTH_LABELS),
                                 "prohibited_identities_present": []},
        "forbidden_claim_audit": {"status": "PASS", "findings": []},
        "old_evidence_modified": False, "frozen_evidence_changes": [],
        "final_feature_freeze_preserved": True,
        "real_device_api_executed": False, "runtime_api_calls": [],
    }
    if persist:
        from .evidence_reader import RESULT_ROOT
        RESULT_ROOT.mkdir(parents=True, exist_ok=True)
        write_json(RESULT_ROOT / "report_verification.json", result)
        write_json(RESULT_ROOT / "chart_data_verification.json", chart_result)
    return result
