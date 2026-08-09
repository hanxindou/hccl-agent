"""Create the single authoritative G3-C final evidence directory."""

from __future__ import annotations

import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .evidence_reader import (
    CLAIM_LEDGER, DATA_LEDGER, G3_B2_ROOT, G3_B3_ROOT, REPORT_ROOT, REQUIREMENT_DELTA,
    RESULT_ROOT, ROOT, STALE_AUDIT, read_json, relative, sha256, source_commit,
    verify_sha256sums, write_json, write_text,
)
from .report_renderer import REPORT_IDS
from .schemas import USER_ACTIONS


EVIDENCE_PARENT = ROOT / "experiments/submission/evidence"


def _official_commits(manifest: dict[str, Any]) -> dict[str, str]:
    repositories = manifest.get("official_repositories")
    if not isinstance(repositories, dict):
        raise RuntimeError("official repository manifest must be an object mapping")
    return {name: repository["commit"] for name, repository in repositories.items()}


def _junit(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"required regression JUnit missing: {relative(path)}")
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    totals = {name: sum(int(suite.attrib.get(name, "0")) for suite in suites)
              for name in ("tests", "failures", "errors", "skipped")}
    totals["passed"] = totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    totals["status"] = "PASS" if totals["failures"] == totals["errors"] == 0 else "FAIL"
    totals["path"] = relative(path)
    return totals


def _official_state(name: str, path: str, expected: str) -> dict[str, Any]:
    base = ["wsl.exe", "--distribution", "Ubuntu-22.04", "--exec", "git", "-c", f"safe.directory={path}", "-C", path]
    commit = subprocess.run([*base, "rev-parse", "HEAD"], check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    branch = subprocess.run([*base, "branch", "--show-current"], check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    status = subprocess.run([*base, "status", "--short"], check=True, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    if commit != expected or status:
        raise RuntimeError(f"official {name} frozen source drift: commit={commit}, status={status!r}")
    return {"repository": name, "branch": branch, "commit": commit, "tracked_worktree_clean": True,
            "source_identity": "FROZEN_OFFICIAL_REFERENCE_NOT_MODIFIED"}


def _report_inventory(ledger: dict[str, Any], claims: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for filename, report_id in REPORT_IDS.items():
        text = (REPORT_ROOT / filename).read_text(encoding="utf-8")
        rows.append({
            "report_id": report_id, "path": relative(REPORT_ROOT / filename),
            "sha256": sha256(REPORT_ROOT / filename),
            "metric_refs": sorted(set(re.findall(r"<!-- metric:([^ ]+) -->", text))),
            "claim_refs": sorted(row["claim_id"] for row in claims["claims"] if row["report_id"] == report_id),
            "real_device_validated": False, "runtime_api_executed": False,
        })
    return {"schema_version": "g3-c-report-inventory-v1", "report_count": len(rows), "reports": rows}


def _source_index_json(inventory: dict[str, Any]) -> dict[str, Any]:
    return {"schema_version": "g3-c-report-source-index-v1", "reports": [
        {"report_id": row["report_id"], "path": row["path"], "metric_refs": row["metric_refs"],
         "claim_refs": row["claim_refs"]} for row in inventory["reports"]]}


def create_final_evidence(output_value: str) -> dict[str, Any]:
    output = Path(output_value)
    if not output.is_absolute():
        output = ROOT / output
    output = output.resolve()
    if output.exists() or output.parent != EVIDENCE_PARENT.resolve() or not output.name.startswith("g3_c_"):
        raise RuntimeError("G3-C evidence must be one new g3_c_* directory under experiments/submission/evidence")
    existing = list(EVIDENCE_PARENT.glob("g3_c_*"))
    if existing:
        raise RuntimeError(f"G3-C final evidence already exists: {[relative(path) for path in existing]}")
    required_results = (RESULT_ROOT / "report_verification.json", RESULT_ROOT / "chart_data_verification.json",
                        RESULT_ROOT / "staging_verification.json")
    if any(not path.is_file() for path in required_results):
        raise RuntimeError("build, verify, and stage must pass before final evidence")
    verification, chart_verification, staging = map(read_json, required_results)
    if any(item.get("status") != "PASS" for item in (verification, chart_verification, staging)):
        raise RuntimeError("cannot freeze failed report verification or staging")
    focused = _junit(RESULT_ROOT / "reporting-focused.xml")
    full = _junit(RESULT_ROOT / "full-regression.xml")
    if focused["status"] != "PASS" or full["status"] != "PASS":
        raise RuntimeError("cannot freeze failed regression")
    ledger, claims = read_json(DATA_LEDGER), read_json(CLAIM_LEDGER)
    b2_integrity, b3_integrity = verify_sha256sums(G3_B2_ROOT), verify_sha256sums(G3_B3_ROOT)
    e_manifest = read_json(ROOT / "experiments/feature_completion/evidence/g3_b3_e_direct_runtime_20260807T160000Z/manifest.json")
    expected = _official_commits(e_manifest)
    official = {
        "hcomm": _official_state("hcomm", "/home/workspace/hcomm", expected["hcomm"]),
        "hccl": _official_state("hccl", "/home/workspace/hccl", expected["hccl"]),
    }
    report_inventory = _report_inventory(ledger, claims)
    source_index = _source_index_json(report_inventory)
    metric_index = {row["metric_id"]: row for row in ledger["metrics"]}
    def metric(metric_id: str) -> Any:
        return metric_index[metric_id]["value"]
    result = {
        "checkpoint": "G3-C", "checkpoint_status": "COMPLETED", "formal_report_suite": "COMPLETED",
        "system_architecture_report": "COMPLETED", "schedule_ir_report": "COMPLETED",
        "topology_hardware_report": "COMPLETED", "dense_sparse_correctness_report": "COMPLETED",
        "sparse_communication_report": "COMPLETED", "simulator_performance_scale_report": "COMPLETED",
        "integrity_retry_reliability_report": "COMPLETED", "simulator_manual": "COMPLETED",
        "native_plugin_appendix": "COMPLETED", "direct_compile_link_appendix": "COMPLETED",
        "limitations_hardware_plan": "COMPLETED", "data_ledger": "COMPLETED", "claim_ledger": "COMPLETED",
        "chart_data": "COMPLETED", "stale_document_audit": "COMPLETED",
        "final_feature_freeze_preserved": True, "old_evidence_modified": False,
        "performance_target_achievement": "PARTIALLY_SATISFIED", "c_cpp_plugin_compliance": "PARTIALLY_SATISFIED",
        "submission_release_readiness": "PARTIAL", "g3_delivery_readiness": "PARTIAL",
        "real_device_acceptance": "HARDWARE_BLOCKED", "real_device_api_executed": False,
        "direct_hccl_api_call": False, "real_ascend_npu_validated": False, "measured_on_real_npu": False,
        "real_model_executed": False, "msprof_executed": False, "runtime_api_calls": [],
    }
    manifest = {
        "schema_version": "g3-c-final-evidence-v1", "checkpoint": "G3-C",
        "source_commit": source_commit(), "branch": "codex/g3-c-final-formal-report-suite",
        "g3_b2_final_evidence": b2_integrity, "g3_b3_final_evidence": b3_integrity,
        "report_count": report_inventory["report_count"], "metric_count": ledger["metric_count"],
        "claim_count": claims["claim_count"], "chart_count": chart_verification["chart_count"],
        "official_repositories": official,
        "worktree_revision": "G3-C report files pending authorized local commit",
        "final_commit_message": "G3-C build final evidence-derived competition report suite",
    }
    source_hierarchy = {
        "schema_version": "g3-c-source-hierarchy-v1",
        "levels": [
            {"level": "L1", "source": "merged main source/tests/configs", "commit": source_commit()},
            {"level": "L2", "source": relative(G3_B3_ROOT), "identity": "CURRENT_FINAL_FEATURE_EVIDENCE"},
            {"level": "L3", "source": relative(G3_B2_ROOT), "identity": "HISTORICAL_OPTIMIZATION_EVIDENCE"},
            {"level": "L4-L8", "source": "G3-B/G3-A/G2-F/current and historical docs", "identity": "HISTORICAL_EVIDENCE"},
        ],
        "g3_b2_and_g3_b3_are_independent_evidence_families": True,
    }
    g3_b2_audit = {
        "status": "PASS", "truth_label": "SIMULATED_ONLY",
        "weighted_simulated_improvement_percent": metric("g3b2.performance.weighted_geomean_improvement_percent"),
        "wins": metric("g3b2.outcomes.wins"), "ties": metric("g3b2.outcomes.ties"),
        "losses": metric("g3b2.outcomes.losses"), "fixed_ring_baseline_explicit": True,
        "pipeline_overlap_simulator_modeled": True, "logical_1024_not_real_devices": True,
        "source_metric_refs": ["g3b2.performance.weighted_geomean_improvement_percent", "g3b2.outcomes.wins",
                               "g3b2.outcomes.ties", "g3b2.outcomes.losses"],
    }
    g3_b3_audit = {
        "status": "PASS", "sparse": "LOSSLESS_SPARSE_HOST_EXECUTED",
        "integrity": "HOST_INTEGRITY_VALIDATED", "retry": "HOST_RETRY_VALIDATED",
        "backpressure": "SIMULATED_BACKPRESSURE", "direct": "DIRECT_COMPILE_LINK_ONLY",
        "official_call_expression_count": metric("g3b3.direct.official_call_expression_count"),
        "runtime_execution": False, "runtime_api_calls": [],
        "int8": metric("g3b3.gates.int8_quantization"), "pairwise": metric("g3b3.gates.pairwise"),
    }
    files: dict[str, Any] = {
        "manifest.json": manifest, "result.json": result, "source_hierarchy.json": source_hierarchy,
        "source_commit.json": {"source_commit": source_commit(), "g3_b2_final_source_commit": ledger["evidence_snapshots"]["G3-B2"]["final_source_commit"],
                               "g3_b3_final_source_commit": ledger["evidence_snapshots"]["G3-B3"]["final_source_commit"]},
        "evidence_inventory.json": {"G3-B2": b2_integrity, "G3-B3": b3_integrity, "official_repositories": official},
        "report_inventory.json": report_inventory, "report_data_ledger.json": ledger,
        "report_claim_ledger.json": claims, "report_source_index.json": source_index,
        "numeric_traceability_audit.json": verification["numeric_traceability"],
        "claim_boundary_audit.json": verification["claims"],
        "forbidden_claim_audit.json": verification["forbidden_claim_audit"],
        "truth_identity_audit.json": verification["truth_identity_audit"],
        "g3_b2_reporting_audit.json": g3_b2_audit, "g3_b3_reporting_audit.json": g3_b3_audit,
        "sparse_reporting_audit.json": {"status": "PASS", "truth": "LOSSLESS_SPARSE_HOST_EXECUTED",
                                        "physical_wire_measurement": False, "dense_fallback_reported": True},
        "reliability_reporting_audit.json": {"status": "PASS", "crc": "HOST_INTEGRITY_VALIDATED",
                                             "retry": "HOST_RETRY_VALIDATED", "backpressure": "SIMULATED_BACKPRESSURE"},
        "direct_reporting_audit.json": {"status": "PASS", "call_expression_count": metric("g3b3.direct.official_call_expression_count"),
                                        "loaded": False, "executed": False, "direct_hccl_api_call": False,
                                        "runtime_api_calls": []},
        "stale_document_audit.json": {"status": "PASS", "markdown": relative(STALE_AUDIT),
                                      "g3_b2_baseline": "HISTORICAL", "g3_b3_baseline": "CURRENT"},
        "requirement_delta.json": read_json(REQUIREMENT_DELTA),
        "user_action_required.json": {"status": "USER_ACTION_REQUIRED", "items": list(USER_ACTIONS)},
        "report_verification.json": verification, "chart_data_verification.json": chart_verification,
        "staging_verification.json": staging,
        "regression_summary.json": {"status": "PASS", "reporting_focused": focused, "full_regression": full,
                                    "new_performance_benchmark_executed": False, "real_device_api_executed": False},
        "official_source_state.json": official,
    }
    output.mkdir()
    for name, payload in files.items():
        write_json(output / name, payload)
    write_text(output / "README.md", "# G3-C final evidence\n\nEvidence-derived formal report suite freeze. No benchmark, ACL/HCCL runtime, device, communicator, collective, MPI, hccl_test, msprof, PDF, release, or archive operation was executed.\n")
    payloads = [path for path in sorted(output.iterdir()) if path.is_file() and path.name not in {"SHA256SUMS", "EVIDENCE_SHA256"}]
    write_text(output / "SHA256SUMS", "".join(f"{sha256(path)}  {path.name}\n" for path in payloads))
    digest = sha256(output / "SHA256SUMS")
    write_text(output / "EVIDENCE_SHA256", f"{digest}  SHA256SUMS\n")
    verified = verify_sha256sums(output)
    return {"status": "PASS", "path": relative(output), "sha256": digest,
            "files_checked": verified["files_checked"], "official_repositories": official}
