"""G3-B3 wire-aware extension over the frozen G3-B2 schedule score."""

from __future__ import annotations

from typing import Any

from feature_completion.flow_control import FlowControlConfig
from feature_completion.reliability import IntegrityConfig
from feature_completion.sparse import SparseDecision, SparsePayload


FEATURE_COST_VERSION = "g3-b3-wire-aware-cost-v1"


def estimate_feature_cost(
    schedule: dict[str, Any],
    base_schedule_score_us: float,
    payload: SparsePayload,
    decision: SparseDecision,
    *,
    integrity: IntegrityConfig = IntegrityConfig(),
    retry_probability: float = 0.0,
    flow: FlowControlConfig = FlowControlConfig(),
    blocked_producer_events: int = 0,
) -> dict[str, Any]:
    if not 0.0 <= retry_probability <= 1.0:
        raise ValueError("retry_probability must be in [0, 1]")
    logical_transfer_bytes = int(schedule["estimated_metrics"]["modeled_transfer_bytes"])
    if payload.logical_bytes <= 0:
        raise ValueError("payload logical bytes must be positive")
    if decision.eligible:
        value_bytes = round(logical_transfer_bytes * payload.value_bytes / payload.logical_bytes)
        index_bytes = round(logical_transfer_bytes * payload.index_bytes / payload.logical_bytes)
        metadata_bytes = max(1, len([t for p in schedule["phases"] for t in p["transfers"]])) * payload.metadata_bytes
        payload_bytes = value_bytes
        wire_bytes = value_bytes + index_bytes + metadata_bytes
    else:
        value_bytes = logical_transfer_bytes
        index_bytes = 0
        metadata_bytes = 0
        payload_bytes = logical_transfer_bytes
        wire_bytes = logical_transfer_bytes
    transfer_count = len([transfer for phase in schedule["phases"] for transfer in phase["transfers"]])
    integrity_metadata_bytes = transfer_count * 32
    crc_bytes = transfer_count * 4
    expected_retry_bytes = round((wire_bytes + integrity_metadata_bytes + crc_bytes) * retry_probability)
    retransmitted_bytes = expected_retry_bytes
    detect_cost_us = decision.detect_cost_equivalent_bytes / 25000.0
    encode_cost_us = decision.encode_cost_equivalent_bytes / 25000.0 if decision.eligible else 0.0
    decode_cost_us = decision.decode_cost_equivalent_bytes / 25000.0 if decision.eligible else 0.0
    crc_cost_us = (wire_bytes + integrity_metadata_bytes) / 20000.0
    retry_penalty_us = expected_retry_bytes / 10000.0
    backpressure_penalty_us = blocked_producer_events * 0.1
    byte_ratio = (wire_bytes + integrity_metadata_bytes + crc_bytes + expected_retry_bytes) / max(1, logical_transfer_bytes)
    communication_cost_us = base_schedule_score_us * byte_ratio
    total_cost_us = communication_cost_us + detect_cost_us + encode_cost_us + decode_cost_us + crc_cost_us + retry_penalty_us + backpressure_penalty_us
    return {
        "schema_version": FEATURE_COST_VERSION,
        "logical_bytes": logical_transfer_bytes,
        "payload_bytes": payload_bytes,
        "value_bytes": value_bytes,
        "index_bytes": index_bytes,
        "metadata_bytes": metadata_bytes,
        "integrity_metadata_bytes": integrity_metadata_bytes,
        "crc_bytes": crc_bytes,
        "wire_bytes": wire_bytes + integrity_metadata_bytes + crc_bytes,
        "retransmitted_bytes": retransmitted_bytes,
        "detect_cost_us": round(detect_cost_us, 9),
        "encode_cost_us": round(encode_cost_us, 9),
        "decode_cost_us": round(decode_cost_us, 9),
        "crc_cost_us": round(crc_cost_us, 9),
        "retry_probability": retry_probability,
        "expected_retry_bytes": expected_retry_bytes,
        "retry_penalty_us": round(retry_penalty_us, 9),
        "backpressure_penalty_us": round(backpressure_penalty_us, 9),
        "base_schedule_score_us": round(base_schedule_score_us, 9),
        "communication_cost_us": round(communication_cost_us, 9),
        "total_cost_us": round(total_cost_us, 9),
        "selected_mode": decision.selected_mode,
        "credit_window": flow.credit_window,
        "max_inflight_chunks": flow.max_inflight_chunks,
        "truth_label": "HOST_SIMULATOR_MODEL",
    }
