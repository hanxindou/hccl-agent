"""Finite, versioned adaptive chunk selection."""

from __future__ import annotations

import math
from typing import Any


CHUNK_POLICY_VERSION = "g3-b2-chunk-policy-v1"
CHUNK_CANDIDATES = (64 * 1024, 256 * 1024, 1024 * 1024, 4 * 1024 * 1024, 16 * 1024 * 1024)


def select_chunk(message_size: int, rank_size: int, topology_depth: int, bandwidth_gbps: float, latency_ms: float, concurrency: int, memory_limit_bytes: int) -> dict[str, Any]:
    if min(message_size, rank_size, topology_depth, concurrency, memory_limit_bytes) <= 0 or bandwidth_gbps <= 0 or latency_ms < 0:
        raise ValueError("invalid chunk selection input")
    scores = []
    for candidate in CHUNK_CANDIDATES:
        if candidate * 2 > memory_limit_bytes:
            scores.append({"chunk_size":candidate,"eligible":False,"score":None,"reason":"MEMORY_LIMIT"})
            continue
        effective = min(candidate, message_size)
        chunks = max(1, math.ceil(message_size / effective))
        serialization_us = message_size * 8 / (bandwidth_gbps * 1000)
        launch_us = chunks * 0.25
        latency_us = topology_depth * latency_ms * 1000 * math.ceil(chunks / concurrency)
        concurrency_penalty = max(0, concurrency - 1) * (serialization_us / max(1, chunks)) * 0.02
        tail_penalty = (chunks % rank_size) / rank_size
        score = serialization_us + launch_us + latency_us + concurrency_penalty + tail_penalty
        scores.append({"chunk_size":candidate,"eligible":True,"score":round(score,9),"reason":"FINITE_FROZEN_CANDIDATE"})
    eligible = [row for row in scores if row["eligible"]]
    if not eligible:
        raise ValueError("no chunk candidate fits memory limit")
    selected = min(eligible, key=lambda row: (row["score"], row["chunk_size"]))
    actual = min(selected["chunk_size"], message_size)
    return {"policy_version":CHUNK_POLICY_VERSION,"chunk_size":actual,"chunk_count":math.ceil(message_size/actual),"pipeline_depth":min(4,max(1,math.ceil(message_size/actual))),"memory_limit_bytes":memory_limit_bytes,"selection_reason":"minimum frozen analytical candidate score","candidate_scores":scores}
