"""Normalize frozen G3-B2/G3-B3 Agent traces and replay them offline."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

from .authority import PROVENANCE_VOCABULARY
from .common import (
    G3_B2_ROOT,
    G3_B2_SHA256SUMS_SHA256,
    G3_B3_AGENT_ROOT,
    G3_B3_ROOT,
    G3_B3_SHA256SUMS_SHA256,
    OUTPUT_ROOT,
    ROOT,
    assert_relative_repository_paths,
    canonical_sha256,
    load_json,
    relative,
    sha256_file,
    verify_sha256sums,
    write_json,
)


TRACE_SCHEMA = "g3-d-normalized-agent-trace-v1"
INDEX_SCHEMA = "g3-d-trace-index-v1"
TRACE_ROOT = OUTPUT_ROOT / "traces"


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _source(path: Path) -> dict[str, str]:
    return {"path": relative(path), "sha256": sha256_file(path)}


def _commit_ref(value: str, *, relationship: str) -> dict[str, Any]:
    if value.startswith("SELF_") or value.startswith("RESOLVED_"):
        return {"commit": None, "recorded_value": value, "relationship": relationship, "commit_validity": "UNRESOLVED", "provenance": "HISTORICAL_TRACE_UNAVAILABLE"}
    completed = subprocess.run(["git", "cat-file", "-e", f"{value}^{{commit}}"], cwd=ROOT, capture_output=True)
    if completed.returncode != 0:
        return {"commit": None, "recorded_value": value, "relationship": relationship, "commit_validity": "UNRESOLVED", "provenance": "HISTORICAL_TRACE_UNAVAILABLE"}
    resolved = subprocess.run(["git", "rev-parse", value], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    return {"commit": resolved, "recorded_value": value, "relationship": relationship, "commit_validity": "VALID", "provenance": "HISTORICAL_EVIDENCE"}


def normalize_g3_b2() -> dict[str, Any]:
    agent_root = ROOT / "agent/evidence/g3_b2"
    run_path = agent_root / "runs/g3-b2-e-authoritative-optimization-round1.json"
    proposal_path = agent_root / "proposals/g3-b2-e-authoritative-optimization-round1.json"
    evaluation_path = agent_root / "evaluations/g3-b2-e-authoritative-optimization-round1.json"
    reflection_path = agent_root / "reflections/g3-b2-e-authoritative-optimization-round1.json"
    replan_path = agent_root / "runs/g3_b2_d_replan_memory_pipeline.json"
    human_path = agent_root / "human_intervention.json"
    mapping_path = agent_root / "commit_mapping.json"
    run = load_json(run_path)
    proposal = load_json(proposal_path)
    evaluation = load_json(evaluation_path)
    reflection = load_json(reflection_path)
    mapping = load_json(mapping_path)
    refs = [_source(path) for path in (run_path, proposal_path, evaluation_path, reflection_path, replan_path, human_path, mapping_path)]
    commits = [_commit_ref(row["result_commit"], relationship=row["phase"]) for row in mapping["entries"]]
    return {
        "trace_id": "g3-b2-optimization-authoritative-round1",
        "schema_version": TRACE_SCHEMA,
        "scenario": "G3-B2 frozen scheduling/topology optimization and A0-A7 evaluation",
        "source_checkpoint": "G3-B2",
        "source_evidence_path": relative(run_path),
        "source_evidence_sha256": sha256_file(run_path),
        "source_evidence_root": relative(G3_B2_ROOT),
        "source_evidence_root_sha256": G3_B2_SHA256SUMS_SHA256,
        "source_commit": "efd946c47ec626d996667ab941a1acf598157ce0",
        "prompt_id": run["prompt_id"],
        "prompt_version": run["prompt_version"],
        "prompt_relationship_status": "HISTORICAL_EVIDENCE",
        "skills": ["g3-b2-optimization-loop", "benchmark-skill", "reflection-skill", "replanning-skill"],
        "input": {"input_hash": run["input_hash"], "original_full_input": "HISTORICAL_TRACE_UNAVAILABLE"},
        "proposal": proposal,
        "deterministic_evaluation": evaluation,
        "reflection": reflection,
        "replanning": {"status": "RECONSTRUCTED_FROM_FROZEN_EVIDENCE", "source_ref": _source(replan_path), "record": load_json(replan_path)},
        "final_decision": {
            "selected": run["selected"],
            "selected_schedule": evaluation["selected"],
            "weighted_simulated_improvement_raw_percent": evaluation["performance_gates"]["weighted_geomean_improvement_percent"],
            "weighted_simulated_improvement_display": "45.59%",
            "wins": evaluation["wins"], "ties": evaluation["ties"], "losses": evaluation["losses"],
        },
        "human_intervention_status": "HUMAN_INTERVENTION",
        "human_intervention_refs": load_json(human_path)["interventions"],
        "output_artifact": relative(evaluation_path),
        "source_refs": refs,
        "commit_refs": commits,
        "claim_refs": ["C-PERF-001", "C-PERF-002", "C-PIPE-001", "C-SCALE-001"],
        "limitations": ["SIMULATED_ONLY", "not real HCCL, NPU, training, or physical network performance", "normalized record is not an original raw Agent log"],
        "source_record_provenance": "HISTORICAL_EVIDENCE",
        "provenance_identity": "RECONSTRUCTED_FROM_FROZEN_EVIDENCE",
        "execution_identity": "SIMULATED_ONLY",
        "hidden_chain_of_thought_included": False,
    }


def normalize_g3_b3() -> dict[str, Any]:
    proposal_path = G3_B3_AGENT_ROOT / "agent_proposals.jsonl"
    evaluation_path = G3_B3_AGENT_ROOT / "agent_evaluations.jsonl"
    reflection_path = G3_B3_AGENT_ROOT / "agent_reflections.jsonl"
    pairwise_path = G3_B3_AGENT_ROOT / "pairwise_value_gate.json"
    int8_path = G3_B3_AGENT_ROOT / "int8_precision_gate.json"
    result_path = G3_B3_ROOT / "result.json"
    proposals = _jsonl(proposal_path)
    evaluations = _jsonl(evaluation_path)
    reflections = _jsonl(reflection_path)
    if not (len(proposals) == len(evaluations) == len(reflections)):
        raise ValueError("G3-B3 proposal/evaluation/reflection counts differ")
    records = []
    for proposal, evaluation, reflection in zip(proposals, evaluations, reflections):
        if proposal["proposal_id"] != evaluation["proposal_id"] or proposal["proposal_id"] != reflection["proposal_id"]:
            raise ValueError("G3-B3 proposal relationship mismatch")
        records.append({"scenario_id": evaluation["scenario_id"], "proposal": proposal, "deterministic_evaluation": evaluation, "reflection": reflection})
    result = load_json(result_path)
    refs = [_source(path) for path in (proposal_path, evaluation_path, reflection_path, pairwise_path, int8_path, result_path, G3_B3_ROOT / "agent_trace_inventory.json", G3_B3_ROOT / "manifest.json")]
    return {
        "trace_id": "g3-b3-feature-completion-agent-flow",
        "schema_version": TRACE_SCHEMA,
        "scenario": "G3-B3 frozen sparse/integrity/retry/flow feature proposal and value gates",
        "source_checkpoint": "G3-B3",
        "source_evidence_path": relative(proposal_path),
        "source_evidence_sha256": sha256_file(proposal_path),
        "source_evidence_root": relative(G3_B3_ROOT),
        "source_evidence_root_sha256": G3_B3_SHA256SUMS_SHA256,
        "source_commit": "3585d5074d827459f117d79484aaa4f282cbf19c",
        "prompt_id": None,
        "prompt_version": None,
        "prompt_relationship_status": "HISTORICAL_TRACE_UNAVAILABLE",
        "skills": ["g3-b3-feature-loop"],
        "input": {"record_count": len(records), "original_prompt_response": "HISTORICAL_TRACE_UNAVAILABLE"},
        "proposal": {"records": [row["proposal"] for row in records]},
        "deterministic_evaluation": {"records": [row["deterministic_evaluation"] for row in records]},
        "reflection": {"records": [row["reflection"] for row in records]},
        "replanning": {"status": "NOT_APPLICABLE", "reason": "frozen G3-B3 feature loop records proposal/evaluation/reflection and deterministic gates, not a replan stage"},
        "final_decision": {
            "implemented": ["lossless_sparse", "host_integrity_crc_retry", "agent_flow_control_integration"],
            "int8_quantization": result["int8_quantization"],
            "pairwise": result["pairwise"],
            "record_counts": {"proposal": len(proposals), "evaluation": len(evaluations), "reflection": len(reflections)},
            "runtime_api_calls": result["runtime_api_calls"],
        },
        "human_intervention_status": "HISTORICAL_TRACE_UNAVAILABLE",
        "human_intervention_refs": [],
        "output_artifact": relative(G3_B3_ROOT / "agent_trace_inventory.json"),
        "source_refs": refs,
        "commit_refs": [_commit_ref("3585d5074d827459f117d79484aaa4f282cbf19c", relationship="G3-B3 final source")],
        "claim_refs": ["C-IR-001", "C-SPARSE-001", "C-SPARSE-002", "C-SPARSE-003", "C-CRC-001", "C-RETRY-001", "C-BP-001", "C-INT8-001", "C-PAIR-001"],
        "limitations": ["host/simulator evidence identities remain separate", "no historical Prompt/Response or hidden reasoning is available", "no real device runtime execution"],
        "source_record_provenance": "HISTORICAL_EVIDENCE",
        "provenance_identity": "RECONSTRUCTED_FROM_FROZEN_EVIDENCE",
        "execution_identity": ["LOSSLESS_SPARSE_HOST_EXECUTED", "HOST_INTEGRITY_VALIDATED", "HOST_RETRY_VALIDATED", "SIMULATED_BACKPRESSURE", "REAL_DEVICE_NOT_EXECUTED"],
        "hidden_chain_of_thought_included": False,
    }


def build_traces() -> dict[str, Any]:
    traces = (normalize_g3_b2(), normalize_g3_b3())
    TRACE_ROOT.mkdir(parents=True, exist_ok=True)
    paths = {
        traces[0]["trace_id"]: TRACE_ROOT / "g3_b2_optimization_trace.json",
        traces[1]["trace_id"]: TRACE_ROOT / "g3_b3_feature_completion_trace.json",
    }
    for trace in traces:
        write_json(paths[trace["trace_id"]], trace)
    index_rows = []
    for trace in traces:
        path = paths[trace["trace_id"]]
        index_rows.append({
            "trace_id": trace["trace_id"], "path": relative(path), "sha256": sha256_file(path),
            "source_checkpoint": trace["source_checkpoint"], "source_commit": trace["source_commit"],
            "source_evidence_root": trace["source_evidence_root"], "source_evidence_root_sha256": trace["source_evidence_root_sha256"],
            "prompt_relationship_status": trace["prompt_relationship_status"],
            "provenance": "RECONSTRUCTED_FROM_FROZEN_EVIDENCE",
        })
    index = {"schema_version": INDEX_SCHEMA, "status": "NORMALIZED", "traces": index_rows}
    write_json(OUTPUT_ROOT / "trace_index.json", index)
    lines = ["# G3-D Trace and Provenance Index", "", "Normalized records are reconstructions from frozen evidence, not original historical executions.", "", "| Trace ID | Checkpoint | Prompt relationship | Provenance |", "| --- | --- | --- | --- |"]
    for row in index_rows:
        lines.append(f"| `{row['trace_id']}` | `{row['source_checkpoint']}` | `{row['prompt_relationship_status']}` | `{row['provenance']}` |")
    (OUTPUT_ROOT / "trace_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return validate_traces()


def replay_trace(trace_id: str) -> dict[str, Any]:
    index = load_json(OUTPUT_ROOT / "trace_index.json")
    row = next((item for item in index["traces"] if item["trace_id"] == trace_id), None)
    if row is None:
        raise ValueError(f"unknown trace_id: {trace_id}")
    trace_path = ROOT / row["path"]
    if sha256_file(trace_path) != row["sha256"]:
        raise ValueError("normalized trace hash mismatch")
    trace = load_json(trace_path)
    replay = {
        "schema_version": "g3-d-offline-replay-v1",
        "status": "PASS",
        "trace_id": trace_id,
        "source_trace_path": row["path"],
        "source_trace_sha256": row["sha256"],
        "steps": [
            {"stage": "input", "record": trace["input"]},
            {"stage": "proposal", "record": trace["proposal"]},
            {"stage": "deterministic_evaluation", "record": trace["deterministic_evaluation"]},
            {"stage": "reflection", "record": trace["reflection"]},
            {"stage": "replanning", "record": trace["replanning"]},
            {"stage": "final_decision", "record": trace["final_decision"]},
        ],
        "provenance_identity": "REPLAYED_FROM_FROZEN_TRACE",
        "source_record_provenance": trace["source_record_provenance"],
        "execution_identity": trace["execution_identity"],
        "historical_execution": False,
        "offline": True,
        "network_used": False,
        "api_keys_used": [],
        "runtime_api_calls": [],
        "hidden_chain_of_thought_included": False,
    }
    replay["replay_sha256"] = canonical_sha256(replay)
    return replay


def _commit_valid(value: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{value}^{{commit}}"], cwd=ROOT, capture_output=True).returncode == 0


def validate_traces() -> dict[str, Any]:
    index = load_json(OUTPUT_ROOT / "trace_index.json")
    registries = load_json(OUTPUT_ROOT / "prompt_registry.json"), load_json(OUTPUT_ROOT / "skill_registry.json")
    prompt_ids = {row["prompt_id"] for row in registries[0]["prompts"]}
    skill_ids = {row["skill_id"] for row in registries[1]["skills"]}
    claim_ids = {row["claim_id"] for row in load_json(ROOT / "docs/submission/report_claim_ledger.json")["claims"]}
    metrics = {row["metric_id"]: row for row in load_json(ROOT / "docs/submission/report_data_ledger.json")["metrics"]}
    errors: list[str] = []
    if index.get("schema_version") != INDEX_SCHEMA: errors.append("trace index schema mismatch")
    trace_ids = [row.get("trace_id") for row in index.get("traces", [])]
    if len(trace_ids) != len(set(trace_ids)): errors.append("duplicate trace_id")
    traces: dict[str, dict[str, Any]] = {}
    for row in index.get("traces", []):
        path = ROOT / row["path"]
        if not path.is_file() or sha256_file(path) != row["sha256"]: errors.append(f"trace path/hash mismatch: {row['trace_id']}"); continue
        trace = load_json(path); traces[row["trace_id"]] = trace
        if trace.get("schema_version") != TRACE_SCHEMA: errors.append(f"trace schema mismatch: {row['trace_id']}")
        primary = ROOT / trace.get("source_evidence_path", "")
        if not primary.is_file() or sha256_file(primary) != trace.get("source_evidence_sha256"): errors.append(f"primary evidence mismatch: {row['trace_id']}")
        if not _commit_valid(trace.get("source_commit", "")): errors.append(f"invalid source commit: {row['trace_id']}")
        if trace.get("prompt_id") is not None and trace["prompt_id"] not in prompt_ids: errors.append(f"unknown prompt: {row['trace_id']}")
        if trace.get("prompt_id") is None and trace.get("prompt_relationship_status") != "HISTORICAL_TRACE_UNAVAILABLE": errors.append(f"missing prompt status: {row['trace_id']}")
        for skill in trace.get("skills", []):
            if skill not in skill_ids: errors.append(f"unknown skill {skill}: {row['trace_id']}")
        for claim in trace.get("claim_refs", []):
            if claim not in claim_ids: errors.append(f"unknown claim {claim}: {row['trace_id']}")
        if trace.get("provenance_identity") not in PROVENANCE_VOCABULARY: errors.append(f"invalid provenance: {row['trace_id']}")
        if trace.get("hidden_chain_of_thought_included") is not False: errors.append(f"hidden chain field invalid: {row['trace_id']}")
        for ref in trace.get("source_refs", []):
            target = ROOT / ref["path"]
            if not target.is_file() or sha256_file(target) != ref["sha256"]: errors.append(f"source ref mismatch: {ref['path']}")
    b2 = traces.get("g3-b2-optimization-authoritative-round1", {})
    b2_decision = b2.get("final_decision", {})
    perf = metrics.get("g3b2.performance.weighted_geomean_improvement_percent", {})
    if b2_decision.get("weighted_simulated_improvement_raw_percent") != 45.59283008 or perf.get("value") != 45.59283008 or perf.get("display_value") != "45.59%": errors.append("G3-B2 performance identity mismatch")
    if [b2_decision.get(key) for key in ("wins", "ties", "losses")] != [18, 0, 0]: errors.append("G3-B2 outcomes mismatch")
    if b2.get("execution_identity") != "SIMULATED_ONLY": errors.append("G3-B2 truth identity mismatch")
    b3 = traces.get("g3-b3-feature-completion-agent-flow", {})
    b3_decision = b3.get("final_decision", {})
    if b3_decision.get("record_counts") != {"proposal": 20, "evaluation": 20, "reflection": 20}: errors.append("G3-B3 record count mismatch")
    if b3_decision.get("int8_quantization") != "DEFERRED_BY_PRECISION_GATE": errors.append("INT8 gate mismatch")
    if b3_decision.get("pairwise") != "SKIPPED_BY_VALUE_GATE": errors.append("PairWise gate mismatch")
    if b3.get("prompt_relationship_status") != "HISTORICAL_TRACE_UNAVAILABLE": errors.append("G3-B3 historical Prompt boundary mismatch")
    replay_hashes: dict[str, str] = {}
    for trace_id in trace_ids:
        first = replay_trace(trace_id); second = replay_trace(trace_id)
        if first != second or first["replay_sha256"] != second["replay_sha256"]: errors.append(f"replay nondeterministic: {trace_id}")
        if first["historical_execution"] or not first["offline"] or first["network_used"] or first["api_keys_used"] or first["runtime_api_calls"]: errors.append(f"offline boundary failed: {trace_id}")
        replay_hashes[trace_id] = first["replay_sha256"]
    if verify_sha256sums(G3_B2_ROOT, G3_B2_SHA256SUMS_SHA256)["status"] != "PASS": errors.append("G3-B2 root changed")
    if verify_sha256sums(G3_B3_ROOT, G3_B3_SHA256SUMS_SHA256)["status"] != "PASS": errors.append("G3-B3 root changed")
    try:
        assert_relative_repository_paths(index)
        for trace in traces.values(): assert_relative_repository_paths(trace)
    except ValueError as exc:
        errors.append(str(exc))
    return {
        "schema_version": "g3-d-trace-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "trace_count": len(trace_ids),
        "replay_hashes": replay_hashes,
        "sentinels": ["TRACE_INDEX_OK", "OFFLINE_REPLAY_OK"] if not errors else [],
    }

