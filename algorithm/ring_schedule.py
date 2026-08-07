"""Deterministic Ring schedules for AllReduce, AllGather, and ReduceScatter."""

from __future__ import annotations

from typing import Any

from .schedule_ir import SCHEMA_VERSION, schedule_hash, validate_schedule


def _chunks(message_size_bytes: int, rank_size: int) -> list[dict[str, int]]:
    base, remainder = divmod(message_size_bytes, rank_size)
    chunks = []
    offset = 0
    for chunk_id in range(rank_size):
        length = base + (1 if chunk_id < remainder else 0)
        chunks.append({"chunk_id": chunk_id, "offset_bytes": offset, "length_bytes": length})
        offset += length
    return chunks


def _phase(phase_index: int, phase_type: str, rank_size: int, chunks: list[dict[str, int]], previous: str | None) -> dict[str, Any]:
    phase_id = f"phase-{phase_index:04d}"
    local_step = phase_index if phase_type == "REDUCE_SCATTER" else phase_index
    transfers = []
    for source in range(rank_size):
        if phase_type == "REDUCE_SCATTER":
            chunk_id = (source - local_step - 1) % rank_size
            operation = "REDUCE"
        else:
            chunk_id = (source - local_step) % rank_size
            operation = "COPY"
        chunk = chunks[chunk_id]
        destination = (source + 1) % rank_size
        transfers.append({
            "chunk_id": chunk_id,
            "destination_rank": destination,
            "length_bytes": chunk["length_bytes"],
            "link_id": f"ring:{source}->{destination}",
            "offset_bytes": chunk["offset_bytes"],
            "operation": operation,
            "source_rank": source,
            "transfer_id": f"transfer-{phase_index:04d}-{source:04d}",
        })
    return {
        "dependencies": [] if previous is None else [previous],
        "phase_id": phase_id,
        "phase_index": phase_index,
        "phase_type": phase_type,
        "transfers": transfers,
    }


def generate_ring_schedule(
    primitive: str,
    rank_size: int,
    message_size_bytes: int,
    *,
    dtype: str = "FP32",
    reduce_op: str | None = "SUM",
    topology_hash: str = "test-topology-v1",
    hardware_profile_hash: str = "g3-b2-frozen-hardware-v1",
) -> dict[str, Any]:
    if primitive not in {"AllReduce", "AllGather", "ReduceScatter"}:
        raise ValueError(f"unsupported Ring primitive: {primitive}")
    if rank_size < 2 or rank_size > 64 or message_size_bytes < 1:
        raise ValueError("Ring schedule requires 2..64 ranks and a positive message size")
    if primitive == "AllGather":
        reduce_op = None
    chunks = _chunks(message_size_bytes, rank_size)
    phase_types = []
    if primitive in {"AllReduce", "ReduceScatter"}:
        phase_types.extend(["REDUCE_SCATTER"] * (rank_size - 1))
    if primitive in {"AllReduce", "AllGather"}:
        phase_types.extend(["ALL_GATHER"] * (rank_size - 1))
    phases = []
    for index, phase_type in enumerate(phase_types):
        local_step = index if phase_type == "REDUCE_SCATTER" else index - (rank_size - 1 if primitive == "AllReduce" else 0)
        phases.append(_phase(local_step if phase_type == "ALL_GATHER" else index, phase_type, rank_size, chunks, phases[-1]["phase_id"] if phases else None))
        phases[-1]["phase_index"] = index
        phases[-1]["phase_id"] = f"phase-{index:04d}"
        phases[-1]["dependencies"] = [] if index == 0 else [f"phase-{index - 1:04d}"]
        for source, transfer in enumerate(phases[-1]["transfers"]):
            transfer["transfer_id"] = f"transfer-{index:04d}-{source:04d}"
    schedule: dict[str, Any] = {
        "algorithm": "Ring",
        "chunk_count": rank_size,
        "chunk_size_bytes": max(chunk["length_bytes"] for chunk in chunks),
        "dependencies": [{"from": f"phase-{index - 1:04d}", "to": f"phase-{index:04d}"} for index in range(1, len(phases))],
        "dtype": dtype,
        "estimated_metrics": {"critical_path_steps": len(phases), "modeled_transfer_bytes": sum(t["length_bytes"] for p in phases for t in p["transfers"]), "phase_count": len(phases)},
        "failure_policy": {"fallback_policy": "NONE", "max_retries": 3, "on_no_path": "EXPECTED_NO_PATH_FAILURE", "retry_policy": "BOUNDED"},
        "hardware_profile_hash": hardware_profile_hash,
        "memory_plan": {"bounded": True, "buffer_count": 2, "logical_message_bytes": message_size_bytes, "materialization_mode": "CHUNK_STREAMING", "peak_materialized_bytes": max(chunk["length_bytes"] for chunk in chunks) * 2},
        "message_size_bytes": message_size_bytes,
        "phases": phases,
        "primitive": primitive,
        "rank_size": rank_size,
        "reduce_op": reduce_op,
        "schedule_id": f"ring-{primitive.lower()}-r{rank_size}-m{message_size_bytes}",
        "schema_version": SCHEMA_VERSION,
        "topology_hash": topology_hash,
    }
    schedule["schedule_hash"] = schedule_hash(schedule)
    validate_schedule(schedule)
    return schedule
