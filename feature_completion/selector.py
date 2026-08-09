"""Wire-aware G3-B3 selector layered over the frozen G3-B2 candidates."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Callable
from typing import Any

from algorithm.schedule_selector import _routes_valid, _score_schedule
from algorithm.topology_schedules import SUPPORT_MATRIX, generate_schedule
from feature_completion.contracts import canonical_hash, validate_schedule_v2
from feature_completion.flow_control import FlowControlConfig, simulate_flow_control
from feature_completion.reliability import IntegrityConfig, attach_reliability_policy
from feature_completion.sparse import (
    DTYPE_BYTES,
    METADATA_BYTES,
    SparseDecision,
    SparsePayload,
    attach_payload_transform,
    decide_sparse,
    index_width,
)
from cost_model.feature_cost import estimate_feature_cost


FEATURE_SELECTOR_VERSION = "g3-b3-wire-aware-selector-v1"
CORRECTNESS_KEYS = {
    "codec_correctness",
    "crc_integrity",
    "reconstruction_correctness",
    "retry_invariants",
}


def modeled_sparse_payload(
    logical_bytes: int,
    dtype: str,
    sparsity_ratio: float,
) -> SparsePayload:
    """Build accounting-only payload metadata without materializing a tensor."""

    if dtype not in DTYPE_BYTES or logical_bytes <= 0:
        raise ValueError("invalid modeled sparse payload")
    if logical_bytes % DTYPE_BYTES[dtype] or not 0.0 <= sparsity_ratio <= 1.0:
        raise ValueError("unaligned logical bytes or invalid sparsity ratio")
    elements = logical_bytes // DTYPE_BYTES[dtype]
    nonzero = math.floor(elements * (1.0 - sparsity_ratio))
    width = index_width(elements)
    value_bytes = nonzero * DTYPE_BYTES[dtype]
    index_bytes = nonzero * width
    wire_bytes = value_bytes + index_bytes + METADATA_BYTES
    return SparsePayload(
        logical_element_count=elements,
        nonzero_count=nonzero,
        index_width=width,
        indices=(),
        values=b"",
        dtype=dtype,
        logical_bytes=logical_bytes,
        index_bytes=index_bytes,
        value_bytes=value_bytes,
        metadata_bytes=METADATA_BYTES,
        wire_bytes=wire_bytes,
        compression_ratio=logical_bytes / wire_bytes,
        reconstruction_hash="ACCOUNTING_ONLY_NOT_A_PAYLOAD",
    )


def _flow_config(schedule: dict[str, Any], memory_limit_bytes: int) -> FlowControlConfig:
    chunk_bytes = schedule["chunk_size_bytes"]
    memory_slots = max(1, memory_limit_bytes // chunk_bytes)
    window = max(1, min(4, schedule["chunk_count"], memory_slots))
    return FlowControlConfig(
        credit_window=window,
        max_inflight_chunks=window,
        high_watermark=max(1, window - 1),
        low_watermark=0 if window == 1 else 1,
        producer_rate=2,
        memory_budget_bytes=memory_limit_bytes,
    )


def _apply_flow_policy(
    schedule: dict[str, Any],
    config: FlowControlConfig,
) -> dict[str, Any]:
    schedule = dict(schedule)
    schedule["flow_control_policy"] = {
        "enabled": True,
        "credit_window": config.credit_window,
        "max_inflight_chunks": config.max_inflight_chunks,
        "high_watermark": config.high_watermark,
        "low_watermark": config.low_watermark,
    }
    schedule["schedule_hash"] = canonical_hash(
        schedule, omitted_keys=("schedule_hash",),
    )
    validate_schedule_v2(schedule)
    return schedule


def select_feature_schedule(
    primitive: str,
    topology: dict[str, Any],
    message_size_bytes: int,
    dtype: str,
    reduce_op: str | None,
    *,
    data_profile: str,
    sparsity_ratio: float,
    correctness_probe: Callable[[str, str], dict[str, bool]],
    memory_limit_bytes: int = 64 * 1024 * 1024,
    integrity: IntegrityConfig = IntegrityConfig(),
    retry_probability: float = 0.001,
    consumer_capacity_pattern: tuple[int, ...] = (2,),
) -> dict[str, Any]:
    """Select algorithm and payload mode using wire, integrity, and flow costs."""

    if correctness_probe is None:
        raise ValueError("correctness_probe is required by the hard gate")
    payload = modeled_sparse_payload(message_size_bytes, dtype, sparsity_ratio)
    sparse_decision = decide_sparse(payload, memory_limit_bytes=memory_limit_bytes)
    dense_decision = dataclasses.replace(
        sparse_decision,
        selected_mode="DENSE",
        eligible=False,
        fallback_reason="AGENT_DENSE_CANDIDATE",
    )
    candidates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None

    for algorithm in SUPPORT_MATRIX:
        if primitive not in SUPPORT_MATRIX[algorithm]:
            rejected.append({"algorithm": algorithm, "reason_code": "UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR"})
            continue
        try:
            v1 = generate_schedule(
                algorithm,
                primitive,
                topology,
                message_size_bytes,
                dtype,
                reduce_op,
                memory_limit_bytes,
            )
            if not _routes_valid(v1, topology):
                raise ValueError("NO_PATH")
            base_score = round(_score_schedule(v1, topology), 9)
        except ValueError as error:
            rejected.append({"algorithm": algorithm, "reason_code": str(error)})
            continue
        for payload_mode, payload_decision in (
            ("DENSE", dense_decision),
            ("SPARSE_INDEX_VALUE", sparse_decision),
        ):
            if payload_mode == "SPARSE_INDEX_VALUE" and not sparse_decision.eligible:
                rejected.append(
                    {
                        "algorithm": algorithm,
                        "payload_mode": payload_mode,
                        "reason_code": sparse_decision.fallback_reason,
                    }
                )
                continue
            checks = correctness_probe(algorithm, payload_mode)
            missing = CORRECTNESS_KEYS - checks.keys()
            if missing:
                raise ValueError(f"correctness probe missing fields: {sorted(missing)}")
            failed = sorted(key for key, passed in checks.items() if not passed)
            if failed:
                rejected.append(
                    {
                        "algorithm": algorithm,
                        "payload_mode": payload_mode,
                        "reason_code": "CORRECTNESS_HARD_GATE",
                        "failed_checks": failed,
                    }
                )
                continue
            schedule = attach_payload_transform(v1, payload, payload_decision)
            schedule = attach_reliability_policy(schedule, integrity)
            flow = _flow_config(schedule, memory_limit_bytes)
            flow_result = simulate_flow_control(
                schedule["chunk_count"],
                schedule["chunk_size_bytes"],
                consumer_capacity_pattern,
                flow,
            )
            flow_checks = {
                key: flow_result[key]
                for key in (
                    "credits_conserved",
                    "no_negative_credit",
                    "bounded_inflight",
                    "memory_budget_respected",
                    "eventually_drains",
                    "no_deadlock",
                    "fairness",
                )
            }
            if not all(flow_checks.values()):
                rejected.append(
                    {
                        "algorithm": algorithm,
                        "payload_mode": payload_mode,
                        "reason_code": "FLOW_CONTROL_HARD_GATE",
                        "failed_checks": [key for key, passed in flow_checks.items() if not passed],
                    }
                )
                continue
            schedule = _apply_flow_policy(schedule, flow)
            cost = estimate_feature_cost(
                schedule,
                base_score,
                payload,
                payload_decision,
                integrity=integrity,
                retry_probability=retry_probability,
                flow=flow,
                blocked_producer_events=flow_result["blocked_producer_events"],
            )
            candidate = {
                "algorithm": algorithm,
                "payload_mode": payload_mode,
                "schedule": schedule,
                "schedule_hash": schedule["schedule_hash"],
                "cost": cost,
                "flow": {key: value for key, value in flow_result.items() if key != "trace"},
                "correctness": {**checks, **flow_checks},
            }
            candidates.append({key: value for key, value in candidate.items() if key != "schedule"})
            candidate_key = (cost["total_cost_us"], algorithm, payload_mode)
            selected_key = None if selected is None else (
                selected["cost"]["total_cost_us"], selected["algorithm"], selected["payload_mode"],
            )
            if selected_key is None or candidate_key < selected_key:
                selected = candidate

    if selected is None:
        return {
            "schema_version": FEATURE_SELECTOR_VERSION,
            "selected": None,
            "candidates": [],
            "rejected": rejected,
            "fallback": "NONE",
            "selection_reason": "NO_CORRECTNESS_PASSING_CANDIDATE",
        }
    return {
        "schema_version": FEATURE_SELECTOR_VERSION,
        "data_profile": data_profile,
        "sparsity_ratio": sparsity_ratio,
        "selected": selected,
        "candidates": candidates,
        "rejected": rejected,
        "fallback": "NONE",
        "selection_reason": (
            "minimum correctness-passing wire-aware host-model cost including "
            "codec, integrity, retry, and bounded backpressure"
        ),
        "truth_label": "HOST_SIMULATOR_MODEL",
    }
