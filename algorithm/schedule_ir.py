"""Canonical G3-B2 collective Schedule IR and invariant validation."""

from __future__ import annotations

import hashlib
import json
from typing import Any


SCHEMA_VERSION = "g3-b2-schedule-ir-v1"
PRIMITIVES = {"AllReduce", "AllGather", "ReduceScatter"}
PHASE_TYPES = {"REDUCE_SCATTER", "ALL_GATHER"}


def canonical_schedule_json(schedule: dict[str, Any], *, include_hash: bool = True) -> str:
    value = dict(schedule)
    if not include_hash:
        value.pop("schedule_hash", None)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def schedule_hash(schedule: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_schedule_json(schedule, include_hash=False).encode("utf-8")).hexdigest()


def invariant_results(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    phases = schedule.get("phases", [])
    rank_size = schedule.get("rank_size", 0)
    message_size = schedule.get("message_size_bytes", 0)
    transfers = [transfer for phase in phases for transfer in phase.get("transfers", [])]
    phase_ids = [phase.get("phase_id") for phase in phases]
    transfer_ids = [transfer.get("transfer_id") for transfer in transfers]
    chunk_ranges = {}
    for transfer in transfers:
        chunk_ranges.setdefault(transfer.get("chunk_id"), (transfer.get("offset_bytes"), transfer.get("length_bytes")))
    ordered_chunks = [chunk_ranges[key] for key in sorted(chunk_ranges) if isinstance(key, int)]
    covered = 0
    contiguous = True
    for offset, length in ordered_chunks:
        if offset != covered or not isinstance(length, int) or length < 0:
            contiguous = False
            break
        covered += length
    known_phase_ids: set[str] = set()
    dependencies_valid = True
    for phase in phases:
        dependencies = phase.get("dependencies", [])
        if any(dependency not in known_phase_ids for dependency in dependencies):
            dependencies_valid = False
        known_phase_ids.add(phase.get("phase_id"))
    results = [
        ("schema_version", schedule.get("schema_version") == SCHEMA_VERSION),
        ("primitive_supported", schedule.get("primitive") in PRIMITIVES),
        ("ring_algorithm", schedule.get("algorithm") == "Ring"),
        ("rank_size", isinstance(rank_size, int) and 2 <= rank_size <= 64),
        ("message_size", isinstance(message_size, int) and message_size > 0),
        ("chunk_count", schedule.get("chunk_count") == rank_size and len(ordered_chunks) == rank_size),
        ("chunk_coverage", contiguous and covered == message_size),
        ("phase_ids_unique", len(phase_ids) == len(set(phase_ids)) and all(phase_ids)),
        ("transfer_ids_unique", len(transfer_ids) == len(set(transfer_ids)) and all(transfer_ids)),
        ("dependencies_acyclic", dependencies_valid),
        ("transfer_rank_and_bytes", all(isinstance(t.get("source_rank"), int) and isinstance(t.get("destination_rank"), int) and 0 <= t["source_rank"] < rank_size and 0 <= t["destination_rank"] < rank_size and t["source_rank"] != t["destination_rank"] and isinstance(t.get("length_bytes"), int) and t["length_bytes"] >= 0 for t in transfers)),
        ("phase_transfer_cardinality", all(len(phase.get("transfers", [])) == rank_size and phase.get("phase_type") in PHASE_TYPES for phase in phases)),
        ("bounded_memory", schedule.get("memory_plan", {}).get("bounded") is True and schedule.get("memory_plan", {}).get("peak_materialized_bytes", message_size + 1) <= 2 * schedule.get("chunk_size_bytes", 0)),
        ("schedule_hash", schedule.get("schedule_hash") == schedule_hash(schedule)),
    ]
    return [{"invariant": name, "passed": passed} for name, passed in results]


def validate_schedule(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    required = {
        "schema_version", "schedule_id", "primitive", "algorithm", "rank_size",
        "message_size_bytes", "dtype", "reduce_op", "topology_hash",
        "hardware_profile_hash", "chunk_size_bytes", "chunk_count", "phases",
        "dependencies", "memory_plan", "failure_policy", "estimated_metrics",
        "schedule_hash",
    }
    missing = required - schedule.keys()
    if missing:
        raise ValueError(f"schedule missing required fields: {sorted(missing)}")
    results = invariant_results(schedule)
    failed = [row["invariant"] for row in results if not row["passed"]]
    if failed:
        raise ValueError(f"schedule invariant failure: {failed}")
    return results
