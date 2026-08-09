import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent.g3_b3_feature_loop import run_feature_agent
from algorithm.ring_schedule import generate_ring_schedule
from algorithm.topology_model import build_topology
from cost_model.feature_cost import estimate_feature_cost
from feature_completion.flow_control import FlowControlConfig, simulate_flow_control
from feature_completion.reliability import IntegrityConfig, attach_reliability_policy
from feature_completion.selector import modeled_sparse_payload, select_feature_schedule
from feature_completion.sparse import attach_payload_transform, decide_sparse
from feature_completion.contracts import validate_agent_proposal_v2


@pytest.mark.parametrize(
    ("pattern", "expects_block"),
    [
        ((2,), False),
        ((2, 0, 0, 1, 2), True),
        ((0, 0, 1), True),
        ((0, 0, 0, 4), True),
    ],
)
def test_credit_flow_invariants_normal_congestion_and_recovery(pattern, expects_block):
    result = simulate_flow_control(16, 1024, pattern)
    assert all(
        result[key]
        for key in (
            "credits_conserved",
            "no_negative_credit",
            "bounded_inflight",
            "memory_budget_respected",
            "eventually_drains",
            "no_deadlock",
            "fairness",
        )
    )
    assert (result["blocked_producer_events"] > 0) is expects_block
    assert result["available_credit"] == result["config"]["credit_window"]
    assert result["credit_return_events"] == 16


def test_invalid_flow_bounds_and_memory_are_rejected():
    with pytest.raises(ValueError, match="bounds"):
        simulate_flow_control(4, 1024, (1,), FlowControlConfig(credit_window=2, max_inflight_chunks=3))
    with pytest.raises(ValueError, match="memory"):
        simulate_flow_control(4, 1024, (1,), FlowControlConfig(memory_budget_bytes=1024))


def test_wire_cost_splits_all_required_byte_and_cost_fields():
    schedule = generate_ring_schedule("AllReduce", 4, 65536)
    payload = modeled_sparse_payload(65536, "FP32", 0.9)
    decision = decide_sparse(payload)
    v2 = attach_reliability_policy(attach_payload_transform(schedule, payload, decision))
    result = estimate_feature_cost(v2, 100.0, payload, decision, retry_probability=0.01)
    assert {
        "logical_bytes", "payload_bytes", "index_bytes", "metadata_bytes",
        "wire_bytes", "retransmitted_bytes", "detect_cost_us", "encode_cost_us",
        "decode_cost_us", "crc_cost_us", "retry_penalty_us",
    } <= result.keys()
    assert result["wire_bytes"] < result["logical_bytes"]
    assert result["retransmitted_bytes"] > 0
    assert result["truth_label"] == "HOST_SIMULATOR_MODEL"


def passing_probe(_algorithm, _mode):
    return {
        "codec_correctness": True,
        "crc_integrity": True,
        "reconstruction_correctness": True,
        "retry_invariants": True,
    }


def test_selector_uses_dense_fallback_and_sparse_when_cost_effective():
    topology = build_topology("full_mesh", 8)
    dense = select_feature_schedule(
        "AllReduce", topology, 65536, "FP32", "SUM",
        data_profile="S00", sparsity_ratio=0.0, correctness_probe=passing_probe,
    )
    sparse = select_feature_schedule(
        "AllReduce", topology, 65536, "FP32", "SUM",
        data_profile="S90", sparsity_ratio=0.9, correctness_probe=passing_probe,
    )
    assert dense["selected"]["payload_mode"] == "DENSE"
    assert sparse["selected"]["payload_mode"] == "SPARSE_INDEX_VALUE"
    assert all(sparse["selected"]["correctness"].values())
    repeat = select_feature_schedule(
        "AllReduce", topology, 65536, "FP32", "SUM",
        data_profile="S90", sparsity_ratio=0.9, correctness_probe=passing_probe,
    )
    assert repeat["selected"]["schedule_hash"] == sparse["selected"]["schedule_hash"]
    assert repeat["selected"]["cost"] == sparse["selected"]["cost"]


def test_selector_rejects_correctness_failure_even_if_sparse_is_cheaper():
    def failing_probe(_algorithm, mode):
        result = passing_probe(_algorithm, mode)
        if mode == "SPARSE_INDEX_VALUE":
            result["reconstruction_correctness"] = False
        return result

    decision = select_feature_schedule(
        "AllReduce", build_topology("full_mesh", 8), 65536, "FP32", "SUM",
        data_profile="S90", sparsity_ratio=0.9, correctness_probe=failing_probe,
    )
    assert decision["selected"]["payload_mode"] == "DENSE"
    assert any(row["reason_code"] == "CORRECTNESS_HARD_GATE" for row in decision["rejected"])


@pytest.mark.parametrize(
    ("profile", "sparsity", "mode"),
    [("S00", 0.0, "DENSE"), ("S90", 0.9, "SPARSE_INDEX_VALUE")],
)
def test_agent_proposal_is_complete_replayable_and_explains_policy(profile, sparsity, mode):
    agent_input = {
        "primitive": "AllReduce",
        "topology": build_topology("full_mesh", 8),
        "message_size_bytes": 65536,
        "dtype": "FP32",
        "reduce_op": "SUM",
        "data_profile": profile,
        "sparsity_ratio": sparsity,
        "memory_budget_bytes": 64 * 1024 * 1024,
        "consumer_capacity_pattern": (2, 0, 1, 2),
    }
    first = run_feature_agent(agent_input)
    second = run_feature_agent(copy.deepcopy(agent_input))
    assert first["proposal"]["payload_mode"] == mode
    assert first["proposal"]["proposal_hash"] == second["proposal"]["proposal_hash"]
    assert first["evaluation"]["correctness_hard_gate"] is True
    assert "CRC32" in first["proposal"]["integrity_policy"]["checksum_type"]
    assert first["proposal"]["retry_policy"]["max_retries"] == 3
    assert first["proposal"]["flow_control_policy"]["enabled"] is True
    assert "host/simulator" in first["proposal"]["expected_risk"]


def test_g3_b3_d_authority_evidence_is_complete_and_hash_valid():
    roots = sorted((ROOT / "experiments/feature_completion/evidence").glob("g3_b3_d_agent_flow_*"))
    assert len(roots) == 1
    evidence = roots[0]
    required = {
        "wire_cost_audit.json", "selector_decisions.json", "agent_proposals.jsonl",
        "agent_evaluations.jsonl", "agent_reflections.jsonl", "flow_control_audit.json",
        "backpressure_cases.json", "feature_ablation.json", "sparse_break_even.json",
        "pairwise_value_gate.json", "int8_precision_gate.json", "SHA256SUMS",
    }
    assert required <= {path.name for path in evidence.iterdir()}
    for line in (evidence / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected, name = line.split("  ", 1)
        assert hashlib.sha256((evidence / name).read_bytes()).hexdigest() == expected
    result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
    selector = json.loads((evidence / "selector_decisions.json").read_text(encoding="utf-8"))
    flow = json.loads((evidence / "flow_control_audit.json").read_text(encoding="utf-8"))
    assert result["checkpoint_status"] == "COMPLETED"
    assert result["runtime_api_calls"] == []
    assert selector["scenario_count"] == 20
    assert selector["dense_count"] > 0 and selector["sparse_count"] > 0
    assert selector["all_correctness_hard_gates_passed"] is True
    assert flow["passed"] is True and len(flow["cases"]) == 4
    proposals = [json.loads(line) for line in (evidence / "agent_proposals.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(proposals) == 20
    assert all(validate_agent_proposal_v2(proposal) for proposal in proposals)


def test_optional_gates_do_not_expand_scope():
    evidence = next((ROOT / "experiments/feature_completion/evidence").glob("g3_b3_d_agent_flow_*"))
    pairwise = json.loads((evidence / "pairwise_value_gate.json").read_text(encoding="utf-8"))
    int8 = json.loads((evidence / "int8_precision_gate.json").read_text(encoding="utf-8"))
    assert pairwise["status"] == "SKIPPED_BY_VALUE_GATE"
    assert pairwise["pairwise_implemented"] is False
    assert int8["status"] == "DEFERRED_BY_PRECISION_GATE"
    assert int8["int8_implemented"] is False
