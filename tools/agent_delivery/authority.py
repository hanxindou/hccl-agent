"""Build and validate the G3-D authority and delivery inventory."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import (
    G3_B2_ROOT,
    G3_B2_SHA256SUMS_SHA256,
    G3_B3_ROOT,
    G3_B3_SHA256SUMS_SHA256,
    G3_C_ROOT,
    OUTPUT_ROOT,
    ROOT,
    assert_relative_repository_paths,
    git,
    load_json,
    relative,
    sha256_file,
    tracked_files,
    verify_sha256sums,
    write_json,
)


PROVENANCE_VOCABULARY = (
    "AGENT_GENERATED",
    "DETERMINISTIC_EVALUATION",
    "HUMAN_INTERVENTION",
    "HISTORICAL_EVIDENCE",
    "REPLAYED_FROM_FROZEN_TRACE",
    "RECONSTRUCTED_FROM_FROZEN_EVIDENCE",
    "HISTORICAL_TRACE_UNAVAILABLE",
    "OFFLINE_REPLAY",
    "ONLINE_LLM_OPTIONAL",
)

COMPONENT_STATUSES = (
    "CURRENT_IMPLEMENTED",
    "FROZEN_HISTORICAL",
    "PARTIAL",
    "OPTIONAL_ONLINE",
    "DOCUMENTATION_ONLY",
    "HISTORICAL_TRACE_UNAVAILABLE",
    "NOT_IN_SCOPE",
)

FORBIDDEN_FEATURE_CHANGES = (
    "collective algorithms",
    "algorithm semantics",
    "Schedule IR execution semantics",
    "topology optimization semantics",
    "Sparse codec semantics",
    "CRC/integrity semantics",
    "timeout/retry semantics",
    "flow-control/backpressure semantics",
    "selector behavior",
    "performance model",
    "simulator equations",
    "benchmark scenarios/results",
    "correctness thresholds",
    "CPU_SIM public ABI",
    "SONAME",
    "19-symbol allowlist",
    "Direct runtime semantics",
    "G3-B2 frozen evidence",
    "G3-B3 frozen evidence",
    "G3-C factual ledgers",
)

FORBIDDEN_RUNTIME_ACTIONS = (
    "ACL runtime",
    "HCCL runtime",
    "device/context/stream",
    "communicator",
    "real collective",
    "MPI",
    "hccl_test",
    "msprof",
)


def _component(
    component_id: str,
    component_type: str,
    source_path: str,
    status: str,
    *,
    owner: str,
    inputs: list[str],
    outputs: list[str],
    tests: list[str],
    evidence: list[str],
    provenance: str,
    side_effects: list[str] | None = None,
    online_dependency: bool = False,
    historical: str = "HISTORICAL_TRACE_UNAVAILABLE",
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "component_type": component_type,
        "source_path": source_path,
        "source_sha256": sha256_file(ROOT / source_path),
        "authority_level": "L4" if status == "FROZEN_HISTORICAL" else "L1",
        "current_status": status,
        "frozen_status": status == "FROZEN_HISTORICAL",
        "entry_or_owner": owner,
        "inputs": inputs,
        "outputs": outputs,
        "side_effects": side_effects or [],
        "online_dependency": online_dependency,
        "tests": tests,
        "relevant_evidence": evidence,
        "historical_record_availability": historical,
        "provenance": provenance,
        "g3_d_output_mapping": [],
        "limitations": limitations or [],
    }


def delivery_contract() -> dict[str, Any]:
    return {
        "schema_version": "g3-d-delivery-contract-v1",
        "checkpoint": "G3-D-A",
        "source_baseline": git("rev-parse", "origin/main"),
        "branch": "codex/g3-d-agent-prompt-delivery",
        "authority_hierarchy": [
            {"level": "L1", "identity": "CURRENT_FINAL_FEATURE_FREEZE_SOURCE", "path": "."},
            {"level": "L2", "identity": "G3_C_FORMAL_REPORTING", "paths": ["docs/submission/report_claim_ledger.json", "docs/submission/report_data_ledger.json", "docs/submission/report_chart_data", "docs/submission/reports", relative(G3_C_ROOT)]},
            {"level": "L3", "identity": "G3_B3_FINAL_FEATURE_EVIDENCE", "path": relative(G3_B3_ROOT), "sha256sums_sha256": G3_B3_SHA256SUMS_SHA256},
            {"level": "L4", "identity": "G3_B2_HISTORICAL_OPTIMIZATION_EVIDENCE", "path": relative(G3_B2_ROOT), "sha256sums_sha256": G3_B2_SHA256SUMS_SHA256},
            {"level": "L5", "identity": "G3_A_HISTORICAL_AUDIT", "paths": ["docs/submission/requirement_matrix.json", "docs/submission/g3_a_gap_report.md", "docs/submission/risk_register.json", "docs/submission/roadmap_assignment.json"]},
        ],
        "claim_language_authority": "docs/submission/report_claim_ledger.json",
        "provenance_vocabulary": list(PROVENANCE_VOCABULARY),
        "mandatory_path": {
            "identity": "OFFLINE_REPLAY",
            "api_keys_required": [],
            "network_required": False,
            "online_llm": "ONLINE_LLM_OPTIONAL",
            "historical_execution": False,
        },
        "feature_freeze": {"status": "FROZEN", "forbidden_changes": list(FORBIDDEN_FEATURE_CHANGES)},
        "hardware_boundary": {"real_device_acceptance": "HARDWARE_BLOCKED", "forbidden_actions": list(FORBIDDEN_RUNTIME_ACTIONS), "runtime_api_calls": []},
        "expected_artifacts": [
            "authority_inventory.json", "delivery_contract.json", "prompt_registry.json",
            "skill_registry.json", "trace_index.json", "traces/g3_b2_optimization_trace.json",
            "traces/g3_b3_feature_completion_trace.json", "source_commit_evidence_claim_mapping.json",
            "human_intervention_disclosure.json",
        ],
        "validation_sentinels": [
            "G3_D_AUTHORITY_INVENTORY_OK", "PROMPT_REGISTRY_OK", "SKILL_REGISTRY_OK",
            "TRACE_INDEX_OK", "OFFLINE_REPLAY_OK", "PROVENANCE_OK",
            "CLAIM_BOUNDARIES_OK", "NO_SECRETS_OK", "G3_D_AGENT_PROMPT_DELIVERY_OK",
        ],
    }


def authority_inventory() -> dict[str, Any]:
    b2 = "experiments/optimization/evidence/g3_b2_f_final_20260807T040000Z"
    b3 = "experiments/feature_completion/evidence/g3_b3_f_final_20260807T170000Z"
    components = [
        _component("agent-entry", "AGENT_ENTRY", "main.py", "CURRENT_IMPLEMENTED", owner="HCCLAgent CLI", inputs=["CLI arguments"], outputs=["Agent result"], tests=["tests/test_agent.py", "tests/test_backend_selection.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION", side_effects=["CPU_SIM run may write local logs"], limitations=["not used by mandatory G3-D replay"]),
        _component("agent-orchestrator", "AGENT_ORCHESTRATION", "agent/hccl_agent.py", "CURRENT_IMPLEMENTED", owner="HCCLAgent", inputs=["nodes", "message_size", "primitive"], outputs=["plan", "proposal", "decision trace", "report fields"], tests=["tests/test_agent.py", "tests/test_algorithm_selection_flow.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION", side_effects=["writes ignored logs and local knowledge/experience"], limitations=["best-effort online reasoning; not mandatory replay"]),
        _component("online-llm", "LLM_BOUNDARY", "agent/llm_client.py", "OPTIONAL_ONLINE", owner="LLMClient", inputs=["prompt", "optional system prompt"], outputs=["provider response"], tests=["tests/test_llm_client.py"], evidence=[], provenance="ONLINE_LLM_OPTIONAL", online_dependency=True, limitations=["DeepSeek only; API key and network required when explicitly used"]),
        _component("prompt-engine", "PROMPT_ENGINE", "agent/prompt_engine.py", "PARTIAL", owner="AgentPromptEngine", inputs=["template", "parameters"], outputs=["filled prompt"], tests=[], evidence=[], provenance="DETERMINISTIC_EVALUATION", side_effects=["writes ignored logs/prompt_calls.jsonl"], limitations=["ignored local logs are not authority evidence"]),
        _component("g3-b2-loop", "DETERMINISTIC_AGENT_LOOP", "agent/g3_b2_optimization_loop.py", "FROZEN_HISTORICAL", owner="hccl-agent:g3_b2_optimization_loop", inputs=["g3-b2-agent-input-v1"], outputs=["proposal", "evaluation", "reflection", "replanning", "selection"], tests=["tests/optimization/test_g3_b2_agent_ablation.py"], evidence=[f"{b2}/agent_trace_inventory.json"], provenance="HISTORICAL_EVIDENCE", historical="AVAILABLE_IN_FROZEN_EVIDENCE", limitations=["performance identity is SIMULATED_ONLY"]),
        _component("g3-b3-loop", "DETERMINISTIC_AGENT_LOOP", "agent/g3_b3_feature_loop.py", "FROZEN_HISTORICAL", owner="hccl-agent:g3_b3_feature_loop", inputs=["g3-b3 feature input"], outputs=["proposal v2", "evaluation", "reflection", "decision"], tests=["tests/feature_completion/test_g3_b3_agent_flow.py"], evidence=[f"{b3}/agent_trace_inventory.json"], provenance="HISTORICAL_EVIDENCE", historical="PARTIAL_FROZEN_RECORDS_NO_HISTORICAL_PROMPT_RESPONSE", limitations=["host/simulator model; no historical Prompt/Response"]),
        _component("offline-template-demo", "CONTROLLED_DEMO", "agent/autonomous_development_loop.py", "CURRENT_IMPLEMENTED", owner="OfflineDevelopmentLoop", inputs=["requirement"], outputs=["temporary generated checker", "compile/test/fix records"], tests=["tests/test_autonomous_development_loop.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION", side_effects=["temporary directory only"], limitations=["not provenance for production C/C++ source"]),
        _component("planning-skill", "SKILL", "agent/planning_skill.py", "CURRENT_IMPLEMENTED", owner="PlanningSkill", inputs=["nodes", "message_size", "primitive"], outputs=["ordered plan"], tests=["tests/test_planning_skill.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION"),
        _component("reasoning-skill", "SKILL", "agent/reasoning_skill.py", "OPTIONAL_ONLINE", owner="ReasoningSkill", inputs=["scenario", "candidates"], outputs=["recommendation", "reasoning"], tests=["tests/test_reasoning_skill.py"], evidence=[], provenance="ONLINE_LLM_OPTIONAL", online_dependency=True),
        _component("evaluation-skill", "SKILL", "agent/evaluation_skill.py", "CURRENT_IMPLEMENTED", owner="EvaluationSkill", inputs=["performance result"], outputs=["grade", "recommendation"], tests=["tests/test_evaluation_skill.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION"),
        _component("execution-skill", "SKILL", "agent/execution_skill.py", "CURRENT_IMPLEMENTED", owner="ExecutionSkill", inputs=["algorithm", "host input data"], outputs=["CPU_SIM execution result"], tests=["tests/test_execution_skill.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION", limitations=["host CPU_SIM; not real HCCL runtime"]),
        _component("reflection-skill", "SKILL", "agent/reflection_skill.py", "CURRENT_IMPLEMENTED", owner="ReflectionSkill", inputs=["prediction", "host execution result", "candidates"], outputs=["reflection", "replan decision"], tests=["tests/test_reflection_skill.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION"),
        _component("replanning-skill", "SKILL", "agent/replanning_skill.py", "CURRENT_IMPLEMENTED", owner="ReplanningSkill", inputs=["current algorithm", "ranking"], outputs=["alternative"], tests=["tests/test_replanning_skill.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION"),
        _component("explanation-skill", "SKILL", "agent/explanation_skill.py", "CURRENT_IMPLEMENTED", owner="ExplanationSkill", inputs=["topology", "candidates", "selection", "reflection"], outputs=["auditable decision trace"], tests=["tests/test_explanation_skill.py"], evidence=[], provenance="DETERMINISTIC_EVALUATION", limitations=["auditable summary only; no hidden chain-of-thought"]),
        _component("g3-b2-prompt-registry", "PROMPT_REGISTRY", "agent/evidence/g3_b2/prompt_registry.json", "FROZEN_HISTORICAL", owner="G3-B2", inputs=["five canonical prompt files"], outputs=["prompt ids, versions, hashes"], tests=["tests/optimization/test_g3_b2_baseline.py"], evidence=[f"{b2}/agent_trace_inventory.json"], provenance="HISTORICAL_EVIDENCE", historical="AVAILABLE_IN_FROZEN_EVIDENCE"),
        _component("g3-c-claim-ledger", "CLAIM_AUTHORITY", "docs/submission/report_claim_ledger.json", "FROZEN_HISTORICAL", owner="G3-C", inputs=["frozen evidence"], outputs=["allowed/prohibited claim language"], tests=["tests/reporting/test_claim_boundaries.py"], evidence=["experiments/submission/evidence/g3_c_20260809T000000Z/claim_boundary_audit.json"], provenance="HISTORICAL_EVIDENCE", historical="AVAILABLE_IN_FROZEN_EVIDENCE"),
    ]
    files = []
    for path in tracked_files(("agent", "skills", "prompts", "tools", "tests")):
        files.append({"path": path, "sha256": sha256_file(ROOT / path)})
    return {
        "schema_version": "g3-d-authority-inventory-v1",
        "checkpoint": "G3-D-A",
        "status": "CURRENT_INVENTORY",
        "source_baseline": git("rev-parse", "origin/main"),
        "components": components,
        "tracked_file_inventory": files,
        "historical_record_policy": "unproven relationships use HISTORICAL_TRACE_UNAVAILABLE",
        "ignored_logs_are_authority": False,
    }


def build_authority_artifacts() -> dict[str, Any]:
    contract = delivery_contract()
    inventory = authority_inventory()
    write_json(OUTPUT_ROOT / "delivery_contract.json", contract)
    write_json(OUTPUT_ROOT / "authority_inventory.json", inventory)
    summary = """# G3-D Agent/Prompt Authority and Inventory\n\nStatus: `CURRENT_INVENTORY`\n\nThis inventory records current source and frozen evidence identities. It is not an original historical Agent execution log. Unproven Prompt, response, human-decision, or commit relationships remain `HISTORICAL_TRACE_UNAVAILABLE`.\n\nMandatory replay is `OFFLINE_REPLAY`; online DeepSeek reasoning is `ONLINE_LLM_OPTIONAL`. Final Feature Freeze and G3-C claim boundaries remain unchanged.\n"""
    (OUTPUT_ROOT / "inventory_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    return validate_authority_artifacts()


def validate_authority_artifacts() -> dict[str, Any]:
    contract = load_json(OUTPUT_ROOT / "delivery_contract.json")
    inventory = load_json(OUTPUT_ROOT / "authority_inventory.json")
    errors: list[str] = []
    b2 = verify_sha256sums(G3_B2_ROOT, G3_B2_SHA256SUMS_SHA256)
    b3 = verify_sha256sums(G3_B3_ROOT, G3_B3_SHA256SUMS_SHA256)
    if b2["status"] != "PASS": errors.append("G3-B2 authority hash failed")
    if b3["status"] != "PASS": errors.append("G3-B3 authority hash failed")
    if set(contract.get("provenance_vocabulary", ())) != set(PROVENANCE_VOCABULARY): errors.append("provenance vocabulary mismatch")
    mandatory = contract.get("mandatory_path", {})
    if mandatory.get("identity") != "OFFLINE_REPLAY" or mandatory.get("api_keys_required") or mandatory.get("network_required") is not False: errors.append("mandatory offline boundary failed")
    if contract.get("claim_language_authority") != "docs/submission/report_claim_ledger.json": errors.append("claim authority mismatch")
    for path in (ROOT / "docs/submission/report_claim_ledger.json", ROOT / "docs/submission/report_data_ledger.json"):
        try: load_json(path)
        except Exception as exc: errors.append(f"ledger unreadable: {relative(path)}: {exc}")
    for row in inventory.get("components", []):
        path = ROOT / row.get("source_path", "")
        if not path.is_file(): errors.append(f"missing component source: {row.get('source_path')}")
        elif sha256_file(path) != row.get("source_sha256"): errors.append(f"component hash mismatch: {row.get('source_path')}")
        if row.get("current_status") not in COMPONENT_STATUSES: errors.append(f"invalid component status: {row.get('component_id')}")
        if row.get("provenance") not in PROVENANCE_VOCABULARY: errors.append(f"invalid provenance: {row.get('component_id')}")
        for test in row.get("tests", []):
            if not (ROOT / test).is_file(): errors.append(f"missing test mapping: {test}")
    if inventory.get("ignored_logs_are_authority") is not False: errors.append("ignored logs must not be authority")
    try:
        assert_relative_repository_paths(contract)
        assert_relative_repository_paths(inventory)
    except ValueError as exc:
        errors.append(str(exc))
    return {
        "schema_version": "g3-d-authority-validation-v1",
        "status": "PASS" if not errors else "FAIL",
        "sentinel": "G3_D_AUTHORITY_INVENTORY_OK" if not errors else None,
        "errors": errors,
        "g3_b2": b2,
        "g3_b3": b3,
        "g3_c_claim_count": load_json(ROOT / "docs/submission/report_claim_ledger.json")["claim_count"],
        "g3_c_metric_count": load_json(ROOT / "docs/submission/report_data_ledger.json")["metric_count"],
        "component_count": len(inventory.get("components", [])),
        "tracked_file_count": len(inventory.get("tracked_file_inventory", [])),
    }

