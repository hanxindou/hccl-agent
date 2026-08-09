"""Deterministic credit-based bounded in-flight and backpressure model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


FLOW_CONTROL_VERSION = "g3-b3-credit-flow-control-v1"


@dataclass(frozen=True)
class FlowControlConfig:
    credit_window: int = 4
    max_inflight_chunks: int = 4
    high_watermark: int = 3
    low_watermark: int = 1
    producer_rate: int = 2
    memory_budget_bytes: int = 64 * 1024 * 1024


def validate_flow_config(config: FlowControlConfig, chunk_bytes: int) -> None:
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be positive")
    if not (
        1 <= config.max_inflight_chunks <= config.credit_window
        and 0 <= config.low_watermark <= config.high_watermark <= config.max_inflight_chunks
        and config.producer_rate >= 1
    ):
        raise ValueError("invalid credit flow-control bounds")
    if config.max_inflight_chunks * chunk_bytes > config.memory_budget_bytes:
        raise ValueError("flow-control configuration exceeds memory budget")


def simulate_flow_control(
    total_chunks: int,
    chunk_bytes: int,
    consumer_capacity_pattern: Sequence[int],
    config: FlowControlConfig = FlowControlConfig(),
) -> dict:
    if total_chunks < 0:
        raise ValueError("total_chunks must be non-negative")
    if not consumer_capacity_pattern or any(value < 0 for value in consumer_capacity_pattern):
        raise ValueError("consumer capacity pattern must be non-empty and non-negative")
    validate_flow_config(config, chunk_bytes)

    available_credit = config.credit_window
    inflight: list[int] = []
    produced = 0
    completed: list[int] = []
    blocked_events = 0
    credit_return_events = 0
    maximum_inflight = 0
    maximum_materialized = 0
    paused = False
    trace = []
    tick = 0
    maximum_ticks = max(16, total_chunks * 16 + len(consumer_capacity_pattern) * 4)

    while (produced < total_chunks or inflight) and tick < maximum_ticks:
        capacity = consumer_capacity_pattern[
            tick if tick < len(consumer_capacity_pattern) else len(consumer_capacity_pattern) - 1
        ]
        consumed_now = []
        for _ in range(min(capacity, len(inflight))):
            consumed_now.append(inflight.pop(0))
            available_credit += 1
            credit_return_events += 1
        completed.extend(consumed_now)

        if paused and len(inflight) <= config.low_watermark:
            paused = False

        produced_now = []
        for _ in range(config.producer_rate):
            if produced >= total_chunks:
                break
            if paused or available_credit == 0 or len(inflight) >= config.max_inflight_chunks:
                blocked_events += 1
                break
            inflight.append(produced)
            produced_now.append(produced)
            produced += 1
            available_credit -= 1
            if len(inflight) >= config.high_watermark:
                paused = True
                break

        maximum_inflight = max(maximum_inflight, len(inflight))
        maximum_materialized = max(maximum_materialized, len(inflight) * chunk_bytes)
        credit_conserved = available_credit + len(inflight) == config.credit_window
        if available_credit < 0 or len(inflight) > config.max_inflight_chunks or not credit_conserved:
            raise RuntimeError("credit flow-control invariant failure")
        trace.append(
            {
                "tick": tick,
                "consumer_capacity": capacity,
                "produced_chunks": produced_now,
                "consumed_chunks": consumed_now,
                "inflight": list(inflight),
                "available_credit": available_credit,
                "producer_paused": paused,
                "credit_conserved": credit_conserved,
            }
        )
        tick += 1

    drained = produced == total_chunks and not inflight
    fairness = completed == list(range(total_chunks))
    return {
        "schema_version": FLOW_CONTROL_VERSION,
        "total_chunks": total_chunks,
        "chunk_bytes": chunk_bytes,
        "config": {
            "credit_window": config.credit_window,
            "max_inflight_chunks": config.max_inflight_chunks,
            "high_watermark": config.high_watermark,
            "low_watermark": config.low_watermark,
            "producer_rate": config.producer_rate,
            "memory_budget_bytes": config.memory_budget_bytes,
        },
        "available_credit": available_credit,
        "max_inflight_observed": maximum_inflight,
        "peak_materialized_bytes": maximum_materialized,
        "blocked_producer_events": blocked_events,
        "credit_return_events": credit_return_events,
        "completed_order": completed,
        "credits_conserved": all(row["credit_conserved"] for row in trace),
        "no_negative_credit": all(row["available_credit"] >= 0 for row in trace),
        "bounded_inflight": maximum_inflight <= config.max_inflight_chunks,
        "memory_budget_respected": maximum_materialized <= config.memory_budget_bytes,
        "eventually_drains": drained,
        "no_deadlock": drained,
        "fairness": fairness,
        "ticks": tick,
        "trace": trace,
        "truth_label": "SIMULATED_BACKPRESSURE",
    }
