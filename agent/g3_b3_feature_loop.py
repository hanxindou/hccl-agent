"""Replayable G3-B3 Agent loop for sparse, integrity, and flow decisions."""

from __future__ import annotations

from typing import Any

from feature_completion.contracts import (
    AGENT_PROPOSAL_VERSION,
    canonical_hash,
    validate_agent_proposal_v2,
)
from feature_completion.reliability import (
    Fault,
    IntegrityConfig,
    IntegrityMetadata,
    execute_transfer,
)
from feature_completion.selector import select_feature_schedule
from feature_completion.sparse import (
    pack_values,
    sparse_collective,
    unpack_values,
)


FEATURE_AGENT_VERSION = "g3-b3-feature-agent-loop-v1"
REQUIRED_INPUTS = {
    "primitive",
    "topology",
    "message_size_bytes",
    "dtype",
    "reduce_op",
    "data_profile",
    "sparsity_ratio",
    "memory_budget_bytes",
}


def _probe_inputs(primitive: str, ranks: int, sparsity: float) -> list[list[float]]:
    elements = ranks * 2 if primitive == "ReduceScatter" else 32
    rows = []
    for rank in range(ranks):
        row = []
        for index in range(elements):
            marker = (rank * 19 + index * 13) % 100
            row.append(0.0 if marker < round(sparsity * 100) else float((rank + 1) * ((index % 7) - 3)))
        rows.append(row)
    return rows


def _quantized(values: list[float], dtype: str) -> list[float]:
    return unpack_values(pack_values(values, dtype), dtype)


def _dense_reference(
    primitive: str,
    rows: list[list[float]],
    dtype: str,
    reduce_op: str | None,
) -> list[list[float]]:
    values = [_quantized(row, dtype) for row in rows]
    if primitive == "AllGather":
        gathered = [item for row in values for item in row]
        return [list(gathered) for _ in values]
    reduced = []
    for index in range(len(values[0])):
        column = [row[index] for row in values]
        item = sum(column) if reduce_op == "SUM" else (max(column) if reduce_op == "MAX" else min(column))
        reduced.append(_quantized([item], dtype)[0])
    if primitive == "AllReduce":
        return [list(reduced) for _ in values]
    count = len(reduced) // len(values)
    return [reduced[rank * count : (rank + 1) * count] for rank in range(len(values))]


def _correctness_probe(agent_input: dict[str, Any]):
    rows = _probe_inputs(
        agent_input["primitive"],
        agent_input["topology"]["rank_size"],
        agent_input["sparsity_ratio"],
    )
    sparse_result = sparse_collective(
        agent_input["primitive"],
        rows,
        dtype=agent_input["dtype"],
        reduce_op=agent_input["reduce_op"],
        memory_limit_bytes=agent_input["memory_budget_bytes"],
    )
    reference = _dense_reference(
        agent_input["primitive"], rows, agent_input["dtype"], agent_input["reduce_op"],
    )
    integrity = execute_transfer(
        b"g3-b3-agent-integrity-probe",
        IntegrityMetadata(1, 0, 0),
        IntegrityConfig(fault=Fault.BIT_FLIP, fault_until_attempt=0),
    )

    def probe(_algorithm: str, payload_mode: str) -> dict[str, bool]:
        reconstructed = sparse_result["outputs"] == reference
        return {
            "codec_correctness": reconstructed if payload_mode == "SPARSE_INDEX_VALUE" else True,
            "crc_integrity": integrity.corruption_detected and integrity.result_code == "HCCL_SUCCESS",
            "reconstruction_correctness": reconstructed,
            "retry_invariants": integrity.recovered and integrity.attempt_count == 2,
        }

    return probe


def run_feature_agent(agent_input: dict[str, Any]) -> dict[str, Any]:
    missing = REQUIRED_INPUTS - agent_input.keys()
    if missing:
        raise ValueError(f"missing G3-B3 Agent inputs: {sorted(missing)}")
    integrity = IntegrityConfig(
        max_retries=int(agent_input.get("max_retries", 3)),
        logical_timeout_ticks=int(agent_input.get("logical_timeout_ticks", 8)),
    )
    decision = select_feature_schedule(
        agent_input["primitive"],
        agent_input["topology"],
        agent_input["message_size_bytes"],
        agent_input["dtype"],
        agent_input["reduce_op"],
        data_profile=agent_input["data_profile"],
        sparsity_ratio=agent_input["sparsity_ratio"],
        correctness_probe=_correctness_probe(agent_input),
        memory_limit_bytes=agent_input["memory_budget_bytes"],
        integrity=integrity,
        retry_probability=float(agent_input.get("retry_probability", 0.001)),
        consumer_capacity_pattern=tuple(agent_input.get("consumer_capacity_pattern", (2,))),
    )
    selected = decision["selected"]
    if selected is None:
        return {
            "schema_version": FEATURE_AGENT_VERSION,
            "proposal": None,
            "evaluation": {"selected": False, "correctness_hard_gate": False},
            "reflection": {"action": "retain explicit failure", "reason": decision["selection_reason"]},
            "decision": decision,
            "truth_label": "HOST_SIMULATOR_MODEL",
        }
    schedule = selected["schedule"]
    cost = selected["cost"]
    transform = schedule["payload_transform"]
    proposal = {
        "schema_version": AGENT_PROPOSAL_VERSION,
        "proposal_id": f"proposal-{schedule['schedule_hash'][:16]}",
        "schedule_algorithm": selected["algorithm"],
        "payload_mode": selected["payload_mode"],
        "sparse_codec": transform["codec"],
        "data_profile": agent_input["data_profile"],
        "sparsity_ratio": agent_input["sparsity_ratio"],
        "logical_bytes": cost["logical_bytes"],
        "estimated_wire_bytes": cost["wire_bytes"] + cost["retransmitted_bytes"],
        "metadata_overhead": cost["metadata_bytes"] + cost["integrity_metadata_bytes"] + cost["crc_bytes"],
        "estimated_compression_ratio": cost["logical_bytes"] / max(1, cost["wire_bytes"]),
        "encode_cost": cost["encode_cost_us"],
        "decode_cost": cost["decode_cost_us"],
        "chunk_size": schedule["chunk_size_bytes"],
        "pipeline_depth": min(4, schedule["chunk_count"]),
        "credit_window": schedule["flow_control_policy"]["credit_window"],
        "integrity_policy": schedule["integrity_policy"],
        "retry_policy": schedule["transport_policy"],
        "flow_control_policy": schedule["flow_control_policy"],
        "dense_fallback_condition": transform["fallback_reason"],
        "fallback_conditions": [
            "sparse wire plus codec cost is not lower than dense",
            "memory budget would be exceeded",
            "any correctness or integrity hard gate fails",
        ],
        "correctness_plan": [
            "compare lossless reconstruction with independent dense reference",
            "verify CRC32 before accept",
            "reject retry and flow invariant failures",
        ],
        "validation_plan": [
            "fixed sparse profile replay",
            "schedule v2 invariant validation",
            "bounded credit and eventual-drain checks",
        ],
        "expected_benefit": (
            f"select {selected['payload_mode']} because total modeled cost "
            f"is {cost['total_cost_us']:.9f} us after wire, codec, integrity, retry, and flow accounting"
        ),
        "expected_risk": (
            "host/simulator cost is not calibrated to Ascend hardware and wire bytes are not physical measurements"
        ),
    }
    proposal["proposal_hash"] = canonical_hash(proposal, omitted_keys=("proposal_hash",))
    validate_agent_proposal_v2(proposal)
    evaluation = {
        "proposal_id": proposal["proposal_id"],
        "selected": True,
        "correctness_hard_gate": all(selected["correctness"].values()),
        "selected_total_cost_us": cost["total_cost_us"],
        "candidate_count": len(decision["candidates"]),
        "rejected_count": len(decision["rejected"]),
        "truth_label": "HOST_SIMULATOR_MODEL",
    }
    reflection = {
        "proposal_id": proposal["proposal_id"],
        "action": "accept correctness-passing minimum wire-aware modeled cost candidate",
        "payload_reason": (
            "sparse payload reduces modeled total cost after metadata" if selected["payload_mode"] == "SPARSE_INDEX_VALUE"
            else f"dense fallback retained: {transform['fallback_reason']}"
        ),
        "integrity_reason": "CRC32 verification and bounded retry remain mandatory for both dense and sparse",
        "flow_reason": "credit window bounds in-flight chunks and producer pauses under modeled saturation",
        "model_boundary": "HOST_SIMULATOR_MODEL",
    }
    return {
        "schema_version": FEATURE_AGENT_VERSION,
        "input_hash": canonical_hash(agent_input),
        "proposal": proposal,
        "evaluation": evaluation,
        "reflection": reflection,
        "decision": decision,
        "truth_label": "HOST_SIMULATOR_MODEL",
    }
