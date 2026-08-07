"""Bounded materialization accounting for logical collective messages."""

from __future__ import annotations

from typing import Any


def memory_report(logical_message_bytes: int, chunk_buffer_bytes: int, memory_budget_bytes: int, *, pipeline_depth: int = 2) -> dict[str, Any]:
    if min(logical_message_bytes, chunk_buffer_bytes, memory_budget_bytes, pipeline_depth) <= 0:
        raise ValueError("memory report inputs must be positive")
    chunk = min(logical_message_bytes, chunk_buffer_bytes)
    temporary = chunk
    actual_depth = min(pipeline_depth, max(1, memory_budget_bytes // chunk - 1))
    materialized = min(logical_message_bytes, chunk * actual_depth)
    peak = materialized + temporary
    return {"logical_message_bytes":logical_message_bytes,"materialized_bytes":materialized,"chunk_buffer_bytes":chunk,"temporary_buffer_bytes":temporary,"peak_materialized_bytes":peak,"memory_budget_bytes":memory_budget_bytes,"within_budget":peak<=memory_budget_bytes,"bounded_materialization":True,"materialized_pipeline_depth":actual_depth,"logical_to_materialized_ratio":round(logical_message_bytes/max(1,materialized),9)}


def attach_memory_report(schedule: dict[str, Any], memory_budget_bytes: int) -> dict[str, Any]:
    report=memory_report(schedule["message_size_bytes"],schedule["chunk_size_bytes"],memory_budget_bytes,pipeline_depth=schedule.get("chunk_selection",{}).get("pipeline_depth",2))
    schedule=dict(schedule); schedule["memory_plan"]={**schedule["memory_plan"],**report,"bounded":True,"materialization_mode":"CHUNK_STREAMING"}
    from .schedule_ir import schedule_hash, validate_schedule
    schedule["schedule_hash"]=schedule_hash(schedule); validate_schedule(schedule); return schedule
