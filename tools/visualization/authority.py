"""Build and validate the G3-E-A visualization authority contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    CHART_DATA_ROOT,
    CLAIM_LEDGER,
    DATA_LEDGER,
    G3_B2_ROOT,
    G3_B2_SHA256SUMS_SHA256,
    G3_B3_ROOT,
    G3_B3_SHA256SUMS_SHA256,
    G3_C_ROOT,
    G3_C_SHA256SUMS_SHA256,
    G3_D_ROOT,
    G3_D_SHA256SUMS_SHA256,
    OUTPUT_ROOT,
    ROOT,
    assert_portable,
    git,
    load_json,
    relative,
    sha256_file,
    verify_sha256sums,
    write_json,
    write_text,
)


TRUTH_IDENTITIES = (
    "HOST_EXECUTED",
    "CPU_EXECUTED",
    "SIMULATED_ONLY",
    "LOSSLESS_SPARSE_HOST_EXECUTED",
    "HOST_INTEGRITY_VALIDATED",
    "HOST_RETRY_VALIDATED",
    "SIMULATED_BACKPRESSURE",
    "DIRECT_READINESS_ONLY",
    "DIRECT_COMPILE_LINK_ONLY",
    "REAL_DEVICE_NOT_EXECUTED",
    "HISTORICAL_EVIDENCE",
    "OFFLINE_REPLAY",
    "REPLAYED_FROM_FROZEN_TRACE",
    "RECONSTRUCTED_FROM_FROZEN_EVIDENCE",
    "AGENT_GENERATED",
    "DETERMINISTIC_EVALUATION",
    "HUMAN_INTERVENTION",
    "HISTORICAL_TRACE_UNAVAILABLE",
    "ONLINE_LLM_OPTIONAL",
)

CANDIDATE_STATUSES = (
    "REQUIRED",
    "RECOMMENDED",
    "OPTIONAL",
    "REJECTED_BY_EVIDENCE",
    "REJECTED_BY_CLARITY",
    "NOT_APPLICABLE",
)

CHART_STORY_ROLES = {
    "algorithm_support_matrix": "algorithm and primitive coverage",
    "backpressure_behavior": "simulated reliability boundary",
    "claim_boundary_summary": "truth and validation ladder",
    "correctness_coverage": "host correctness coverage",
    "crc_retry_cases": "host integrity and bounded retry",
    "direct_readiness_status": "compile/link-only readiness boundary",
    "g3_b2_ablation": "optimization contribution evidence",
    "g3_b2_bandwidth_comparison": "simulated optimization comparison",
    "g3_b2_latency_comparison": "simulated optimization comparison",
    "g3_b2_scale": "logical/model scaling",
    "reliability_outcomes": "layered reliability outcomes",
    "schedule_phase_comparison": "Schedule IR and topology phases",
    "sparse_break_even": "sparse decision boundary",
    "sparse_compression_ratio": "modeled sparse accounting",
    "sparse_dense_fallback": "lossless dense fallback",
    "sparse_wire_bytes": "modeled sparse wire bytes",
}


def _scenario_scope(metric_ids: list[str]) -> str:
    if not metric_ids:
        return "non-numeric or claim-derived summary"
    prefixes = {".".join(metric_id.split(".")[:3]) for metric_id in metric_ids}
    return ", ".join(sorted(prefixes))


def _allowed_visualizations(chart_id: str) -> list[str]:
    if chart_id.endswith("matrix") or "coverage" in chart_id or "status" in chart_id:
        return ["labeled matrix", "validation ladder", "directly labeled bars"]
    if "latency" in chart_id or "bandwidth" in chart_id or "scale" in chart_id:
        return ["small multiples", "paired bars", "line chart with explicit units"]
    if "wire" in chart_id or "compression" in chart_id or "break_even" in chart_id:
        return ["stacked bars", "line chart", "directly labeled comparison"]
    return ["directly labeled bars", "small multiples", "evidence table"]


def _forbidden_interpretations(truths: list[str]) -> list[str]:
    values = ["real-device execution or measurement"]
    if "SIMULATED_ONLY" in truths:
        values.extend(["real Ascend/NPU performance", "training speedup"])
    if "LOSSLESS_SPARSE_HOST_EXECUTED" in truths:
        values.extend(["physical NIC byte measurement", "real network compression measurement"])
    if "SIMULATED_BACKPRESSURE" in truths:
        values.append("measured NIC/HCCL backpressure")
    if "DIRECT_COMPILE_LINK_ONLY" in truths or "REAL_DEVICE_NOT_EXECUTED" in truths:
        values.append("successful ACL/HCCL runtime collective")
    return sorted(set(values))


def chart_data_inventory() -> dict[str, Any]:
    ledger = load_json(DATA_LEDGER)
    claims = load_json(CLAIM_LEDGER)
    metrics = {row["metric_id"]: row for row in ledger["metrics"]}
    claim_rows = {row["claim_id"]: row for row in claims["claims"]}
    artifacts = []
    for path in sorted(CHART_DATA_ROOT.glob("*.json")):
        payload = load_json(path)
        metric_ids = payload.get("metric_refs", [])
        rows = [metrics[metric_id] for metric_id in metric_ids]
        claim_refs = sorted(
            claim_id
            for claim_id, claim in claim_rows.items()
            if set(claim.get("metric_refs", ())) & set(metric_ids)
        )
        raw_truths = [payload.get("truth_label")] + [
            row.get("truth_label") or row.get("execution_identity") for row in rows
        ]
        truths = sorted({
            identity.strip()
            for truth in raw_truths
            if truth
            for identity in truth.split("+")
        })
        artifacts.append({
            "chart_data_id": payload["chart_id"],
            "source_path": relative(path),
            "source_sha256": sha256_file(path),
            "metric_ids": metric_ids,
            "metric_count": len(metric_ids),
            "claim_refs": claim_refs,
            "units": sorted({row["unit"] for row in rows}),
            "rounding": sorted({row["rounding_rule"] for row in rows}),
            "truth_identity": truths,
            "scenario_scope": _scenario_scope(metric_ids),
            "allowed_visualizations": _allowed_visualizations(payload["chart_id"]),
            "forbidden_interpretations": _forbidden_interpretations(truths),
            "candidate_story_role": CHART_STORY_ROLES[payload["chart_id"]],
        })
    return {
        "schema_version": "g3-e-chart-data-inventory-v1",
        "status": "CURRENT_AUTHORITY_INVENTORY",
        "derived_from": "docs/submission/report_data_ledger.json",
        "chart_data_count": len(artifacts),
        "claim_count": claims["claim_count"],
        "metric_count": ledger["metric_count"],
        "artifacts": artifacts,
    }


def visualization_contract() -> dict[str, Any]:
    return {
        "schema_version": "g3-e-visualization-contract-v1",
        "checkpoint": "G3-E-A",
        "status": "FROZEN_CONTRACT",
        "source_baseline": git("rev-parse", "origin/main"),
        "authority_routing": {
            "numeric_fact": "docs/submission/report_data_ledger.json",
            "external_wording": "docs/submission/report_claim_ledger.json",
            "chart_source_data": "docs/submission/report_chart_data",
            "agent_provenance": "docs/submission/agent_delivery",
            "feature_implementation": "merged source and G3-B3 evidence",
            "optimization_history": "G3-B2 evidence",
            "historical_gap": "G3-A audit",
        },
        "authority_conflict_status": "BLOCKED_BY_AUTHORITY_CONFLICT",
        "truth_identities": list(TRUTH_IDENTITIES),
        "candidate_statuses": list(CANDIDATE_STATUSES),
        "numerical_policy": {
            "single_source": "G3-C chart-data plus data ledger plus canonical display rounding",
            "manual_authoritative_constants": False,
            "raw_benchmark_input": False,
            "display_value_is_canonical": True,
        },
        "renderer_decision": {
            "mandatory": "Python stdlib deterministic self-contained SVG",
            "canonical_asset": "SVG",
            "png": "OPTIONAL_NON_CANONICAL_ONLY_IF_DETERMINISTIC",
            "external_dependency_required": False,
            "network_required": False,
            "browser_service_required": False,
        },
        "visual_integrity_rules": [
            "no unnecessary 3D, area, or volume encoding",
            "no unjustified truncated axis; non-zero baseline must be explicit",
            "no unnecessary dual axis",
            "simulation, host execution, readiness, and real device remain visually distinct",
            "logical ranks are never physical NPU validation",
            "modeled wire bytes are never NIC measurement",
            "truth identity is not encoded by color alone",
            "every final figure has units, caption, alt text, source/claim mapping, limitations, and forbidden interpretations",
        ],
        "design_contract": {
            "presentation_friendly": "16:9",
            "vector_first": True,
            "self_contained": True,
            "private_fonts": False,
            "accessible_contrast": True,
            "key_semantics_color_only": False,
            "language": "USER_ACTION_REQUIRED",
            "template": "USER_ACTION_REQUIRED",
        },
        "mandatory_offline_boundary": {
            "network": False,
            "remote_assets": False,
            "api_keys": [],
            "external_llm": False,
            "benchmark_rerun": False,
            "hardware_runtime": False,
        },
        "feature_freeze": "PRESERVED",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "runtime_api_calls": [],
    }


def _candidate(
    figure_id: str,
    title: str,
    purpose: str,
    figure_type: str,
    data_sources: list[str],
    claim_refs: list[str],
    truths: list[str],
    question: str,
    position: str,
    priority: int,
    status: str,
    limitations: list[str],
) -> dict[str, Any]:
    return {
        "figure_id": figure_id,
        "title": title,
        "purpose": purpose,
        "figure_type": figure_type,
        "data_sources": data_sources,
        "claim_refs": claim_refs,
        "truth_identity": truths,
        "audience_question": question,
        "story_position": position,
        "priority": priority,
        "limitations": limitations,
        "status": status,
    }


def candidate_inventory() -> dict[str, Any]:
    chart = "docs/submission/report_chart_data/"
    rows = [
        _candidate("FIG-01", "System execution and validation architecture", "Separate CPU_SIM, simulator validation, Direct readiness, and real-device gap.", "architecture diagram", ["main.py", "agent/hccl_agent.py", "tools/submission_cli/core.py"], ["C-ARCH-001", "C-ARCH-002"], ["HOST_EXECUTED", "REAL_DEVICE_NOT_EXECUTED"], "What is the system and what actually ran?", "System", 1, "REQUIRED", ["architecture relation only; not performance evidence"]),
        _candidate("FIG-02", "Schedule IR and topology-aware optimization pipeline", "Explain schedule generation, topology costs, selection, and replanning.", "process diagram", [chart + "schedule_phase_comparison.json", chart + "algorithm_support_matrix.json"], ["C-IR-001"], ["HOST_EXECUTED", "SIMULATED_ONLY"], "What changed in the optimization pipeline?", "Optimization", 2, "REQUIRED", ["optimization outcomes are simulated"]),
        _candidate("FIG-03", "Frozen simulated latency comparison", "Show scenario-level baseline versus final modeled latency.", "log-scale paired bars", [chart + "g3_b2_latency_comparison.json"], ["C-PERF-001"], ["SIMULATED_ONLY"], "Where does the optimization improvement appear?", "Evidence", 3, "REQUIRED", ["not real NPU or training latency"]),
        _candidate("FIG-04", "18 wins, 0 ties, 0 losses", "Summarize the frozen simulated scenario comparison and canonical weighted result.", "directly labeled outcome summary", [chart + "g3_b2_latency_comparison.json", chart + "g3_b2_bandwidth_comparison.json"], ["C-PERF-001", "C-PERF-002"], ["SIMULATED_ONLY"], "How consistent was the modeled result?", "Evidence", 4, "REQUIRED", ["18 frozen simulated scenarios only", "45.59% is canonical display, not hardware speedup"]),
        _candidate("FIG-05", "Logical scale trend", "Show modeled behavior through the frozen logical rank range.", "line chart", [chart + "g3_b2_scale.json"], ["C-SCALE-001"], ["SIMULATED_ONLY"], "What scale was modeled?", "Evidence", 7, "RECOMMENDED", ["logical/model ranks, not physical NPU cluster"]),
        _candidate("FIG-06", "Lossless sparse wire-accounting boundary", "Explain density, modeled bytes, break-even, compression ratio, and dense fallback.", "small multiples", [chart + "sparse_wire_bytes.json", chart + "sparse_break_even.json", chart + "sparse_compression_ratio.json", chart + "sparse_dense_fallback.json"], ["C-SPARSE-001", "C-SPARSE-002", "C-SPARSE-003"], ["LOSSLESS_SPARSE_HOST_EXECUTED"], "When is sparse useful and what was actually validated?", "Feature completion", 5, "REQUIRED", ["host correctness plus modeled/logical bytes; not NIC measurement"]),
        _candidate("FIG-07", "Integrity, retry, and backpressure layers", "Separate host CRC, host retry, and simulated backpressure evidence.", "layered outcome matrix", [chart + "crc_retry_cases.json", chart + "backpressure_behavior.json", chart + "reliability_outcomes.json"], ["C-CRC-001", "C-RETRY-001", "C-BP-001"], ["HOST_INTEGRITY_VALIDATED", "HOST_RETRY_VALIDATED", "SIMULATED_BACKPRESSURE"], "Which reliability properties were validated at each layer?", "Feature completion", 6, "REQUIRED", ["not NIC/HCCL hardware reliability"]),
        _candidate("FIG-08", "Agent-assisted optimization loop", "Show proposal, deterministic evaluation, human governance, reflection/replanning, and evidence mapping.", "provenance process diagram", ["docs/submission/agent_delivery/trace_index.json", "docs/submission/agent_delivery/source_commit_evidence_claim_mapping.json"], ["C-PERF-001", "C-IR-001"], ["AGENT_GENERATED", "DETERMINISTIC_EVALUATION", "HUMAN_INTERVENTION", "RECONSTRUCTED_FROM_FROZEN_EVIDENCE"], "What did the Agent and humans actually do?", "Agent role", 5, "REQUIRED", ["normalized reconstruction is not hidden reasoning or original historical execution"]),
        _candidate("FIG-09", "G3-B3 feature decision flow", "Show implemented, deferred, and skipped decisions without hiding negative gates.", "decision flow diagram", ["docs/submission/agent_delivery/traces/g3_b3_feature_completion_trace.json"], ["C-INT8-001", "C-PAIR-001"], ["RECONSTRUCTED_FROM_FROZEN_EVIDENCE", "HISTORICAL_TRACE_UNAVAILABLE"], "Why were INT8 and PairWise not implemented?", "Agent role", 8, "RECOMMENDED", ["historical Prompt/Response unavailable"]),
        _candidate("FIG-10", "Direct readiness validation ladder", "Distinguish source call expressions, compile/link readiness, CPU_SIM ABI, and missing runtime execution.", "validation ladder", [chart + "direct_readiness_status.json", "hcccl/submission/native_plugin_abi_manifest.json"], ["C-DIRECT-001", "C-DIRECT-002", "C-ABI-001"], ["CPU_EXECUTED", "DIRECT_COMPILE_LINK_ONLY", "REAL_DEVICE_NOT_EXECUTED"], "What does Direct readiness prove?", "Limitations", 6, "REQUIRED", ["no ACL/HCCL runtime, communicator, or real collective executed"]),
        _candidate("FIG-11", "Optimization ablation", "Attribute modeled contribution across the frozen optimization stages.", "waterfall-style bars", [chart + "g3_b2_ablation.json"], ["C-PERF-001", "C-PIPE-001"], ["SIMULATED_ONLY"], "Which stages contributed to the modeled result?", "Evidence", 9, "RECOMMENDED", ["modeled ablation, not hardware attribution"]),
        _candidate("FIG-12", "Truth and evidence boundary matrix", "Give reviewers a compact host/simulator/readiness/real-device map.", "labeled matrix", [chart + "claim_boundary_summary.json"], ["C-ARCH-001", "C-DIRECT-002", "C-MODEL-001"], ["HOST_EXECUTED", "SIMULATED_ONLY", "DIRECT_READINESS_ONLY", "REAL_DEVICE_NOT_EXECUTED"], "Which statements are safe at each evidence layer?", "Limitations", 2, "REQUIRED", ["summary does not replace claim ledger"]),
        _candidate("FIG-13", "Algorithm and topology coverage", "Show implemented primitives/algorithm families and topology-aware phase differences.", "coverage matrix", [chart + "algorithm_support_matrix.json", chart + "schedule_phase_comparison.json"], ["C-IR-001"], ["HOST_EXECUTED", "SIMULATED_ONLY"], "What algorithm/topology breadth is implemented?", "System", 10, "RECOMMENDED", ["coverage does not imply real-device validation"]),
    ]
    return {
        "schema_version": "g3-e-chart-candidate-inventory-v1",
        "status": "CANDIDATES_FROZEN_NO_ASSETS_BUILT",
        "selection_policy": ["competition relevance", "technical distinctness", "evidence strength", "clarity", "claim safety"],
        "recommended_main_figure_range": {"minimum": 8, "maximum": 12, "hard_requirement": False},
        "candidate_count": len(rows),
        "candidates": rows,
    }


def story_contract() -> dict[str, Any]:
    return {
        "schema_version": "g3-e-story-contract-v1",
        "status": "STRUCTURE_FROZEN_FINAL_NARRATIVE_NOT_WRITTEN",
        "sequence": ["Problem", "System", "Optimization", "Feature completion", "Agent role", "Evidence", "Limitations", "Competition value"],
        "layers_required": ["30-second", "3-minute", "technical defense"],
        "strongest_evidence_boundary": {
            "raw": 45.59283008,
            "canonical_display": "45.59%",
            "truth_identity": "SIMULATED_ONLY",
            "wins": 18,
            "ties": 0,
            "losses": 0,
            "authoritative_source": "docs/submission/report_data_ledger.json",
        },
        "agent_wording": "Agent-assisted, deterministically evaluated, human-governed, offline replayable",
        "real_device_acceptance": "HARDWARE_BLOCKED",
        "final_language": "USER_ACTION_REQUIRED",
        "final_template": "USER_ACTION_REQUIRED",
    }


def build_authority() -> dict[str, Any]:
    write_json(OUTPUT_ROOT / "visualization_contract.json", visualization_contract())
    write_json(OUTPUT_ROOT / "chart_data_inventory.json", chart_data_inventory())
    write_json(OUTPUT_ROOT / "chart_candidate_inventory.json", candidate_inventory())
    write_json(OUTPUT_ROOT / "story_contract.json", story_contract())
    write_text(OUTPUT_ROOT / "README.md", """# G3-E Competition Visualization and Innovation Narrative

Status: `G3-E-A AUTHORITY CONTRACT`

This directory is the submission-facing visualization delivery root. G3-C chart-data/data-ledger/claim-ledger are the sole numerical and claim authority; G3-D registries and normalized traces are the Agent provenance authority. G3-E creates no new technical truth.

G3-E-A inventories authority and candidates only. No final chart asset is generated at this checkpoint. Mandatory rendering is offline, deterministic, self-contained SVG-first, benchmark-free, and real-device-free.
""")
    return validate_authority()


def validate_authority() -> dict[str, Any]:
    errors: list[str] = []
    contract = load_json(OUTPUT_ROOT / "visualization_contract.json")
    inventory = load_json(OUTPUT_ROOT / "chart_data_inventory.json")
    candidates = load_json(OUTPUT_ROOT / "chart_candidate_inventory.json")
    story = load_json(OUTPUT_ROOT / "story_contract.json")
    ledger = load_json(DATA_LEDGER)
    claims = load_json(CLAIM_LEDGER)
    metric_map = {row["metric_id"]: row for row in ledger["metrics"]}
    claim_map = {row["claim_id"]: row for row in claims["claims"]}
    if inventory.get("chart_data_count") != 16: errors.append("chart-data count mismatch")
    if inventory.get("metric_count") != 1082 or len(metric_map) != 1082: errors.append("metric count mismatch")
    if inventory.get("claim_count") != 21 or len(claim_map) != 21: errors.append("claim count mismatch")
    if set(contract.get("truth_identities", ())) != set(TRUTH_IDENTITIES): errors.append("truth identity allowlist mismatch")
    if set(contract.get("candidate_statuses", ())) != set(CANDIDATE_STATUSES): errors.append("candidate status allowlist mismatch")
    if contract.get("renderer_decision", {}).get("canonical_asset") != "SVG": errors.append("canonical renderer contract mismatch")
    for artifact in inventory.get("artifacts", []):
        path = ROOT / artifact["source_path"]
        if not path.is_file() or sha256_file(path) != artifact["source_sha256"]: errors.append(f"chart-data hash mismatch: {artifact['chart_data_id']}"); continue
        payload = load_json(path)
        if payload.get("derived_from") != "docs/submission/report_data_ledger.json": errors.append(f"invalid chart data source: {artifact['chart_data_id']}")
        if payload.get("metric_refs") != artifact["metric_ids"]: errors.append(f"metric inventory mismatch: {artifact['chart_data_id']}")
        for row in payload.get("series", []):
            metric = metric_map.get(row.get("metric_id"))
            if metric is None: errors.append(f"unknown chart metric: {row.get('metric_id')}"); continue
            for key in ("value", "display_value", "unit"):
                if row.get(key) != metric.get(key): errors.append(f"canonical chart value mismatch: {artifact['chart_data_id']} {row.get('metric_id')} {key}")
        for claim_id in artifact.get("claim_refs", []):
            if claim_id not in claim_map: errors.append(f"unknown chart claim: {claim_id}")
        if any(identity not in TRUTH_IDENTITIES for identity in artifact.get("truth_identity", [])): errors.append(f"invalid chart truth identity: {artifact['chart_data_id']}")
    candidate_ids = [row["figure_id"] for row in candidates.get("candidates", [])]
    if len(candidate_ids) != len(set(candidate_ids)) or candidates.get("candidate_count") != len(candidate_ids): errors.append("candidate ID/count mismatch")
    for row in candidates.get("candidates", []):
        if row.get("status") not in CANDIDATE_STATUSES: errors.append(f"invalid candidate status: {row.get('figure_id')}")
        for claim_id in row.get("claim_refs", []):
            if claim_id not in claim_map: errors.append(f"unknown candidate claim: {claim_id}")
        if any(identity not in TRUTH_IDENTITIES for identity in row.get("truth_identity", [])): errors.append(f"invalid candidate truth: {row.get('figure_id')}")
        for source in row.get("data_sources", []):
            if not (ROOT / source).is_file(): errors.append(f"missing candidate source: {row.get('figure_id')} {source}")
    if story.get("strongest_evidence_boundary", {}).get("canonical_display") != "45.59%" or story.get("strongest_evidence_boundary", {}).get("truth_identity") != "SIMULATED_ONLY": errors.append("canonical performance boundary mismatch")
    g3_d = {
        "prompts": len(load_json(ROOT / "docs/submission/agent_delivery/prompt_registry.json")["prompts"]),
        "skills": len(load_json(ROOT / "docs/submission/agent_delivery/skill_registry.json")["skills"]),
        "traces": len(load_json(ROOT / "docs/submission/agent_delivery/trace_index.json")["traces"]),
        "mappings": load_json(ROOT / "docs/submission/agent_delivery/source_commit_evidence_claim_mapping.json")["relationship_count"],
        "human_records": len(load_json(ROOT / "docs/submission/agent_delivery/human_intervention_disclosure.json")["g3_b2"]["records"]),
    }
    if g3_d != {"prompts": 12, "skills": 31, "traces": 2, "mappings": 56, "human_records": 6}: errors.append("G3-D baseline count mismatch")
    roots = {
        "g3_b2": verify_sha256sums(G3_B2_ROOT, G3_B2_SHA256SUMS_SHA256),
        "g3_b3": verify_sha256sums(G3_B3_ROOT, G3_B3_SHA256SUMS_SHA256),
        "g3_c": verify_sha256sums(G3_C_ROOT, G3_C_SHA256SUMS_SHA256),
        "g3_d": verify_sha256sums(G3_D_ROOT, G3_D_SHA256SUMS_SHA256),
    }
    for name, result in roots.items():
        if result["status"] != "PASS": errors.append(f"{name} authority hash mismatch")
    try:
        for value in (contract, inventory, candidates, story): assert_portable(value)
    except ValueError as exc:
        errors.append(str(exc))
    return {
        "schema_version": "g3-e-visualization-authority-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "chart_data_count": inventory.get("chart_data_count"),
        "metric_count": len(metric_map),
        "claim_count": len(claim_map),
        "candidate_count": len(candidate_ids),
        "g3_d_counts": g3_d,
        "authority_roots": roots,
        "sentinel": "G3_E_VISUALIZATION_AUTHORITY_OK" if not errors else None,
        "final_assets_built": False,
        "benchmark_rerun": False,
        "runtime_api_calls": [],
    }
