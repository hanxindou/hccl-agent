"""Explicit multi-candidate schedule selector with fallback NONE."""

from __future__ import annotations

from typing import Any

from .topology_schedules import SUPPORT_MATRIX, generate_schedule
from .topology_model import route_link


def _routes_valid(schedule: dict[str, Any], topology: dict[str, Any]) -> bool:
    return all(route_link(topology, transfer["source_rank"], transfer["destination_rank"]) is not None for phase in schedule["phases"] for transfer in phase["transfers"])


def _score_schedule(schedule: dict[str, Any], topology: dict[str, Any]) -> float:
    phase_costs=schedule["estimated_metrics"].get("phase_costs")
    if phase_costs:
        return sum(row["final_link_time"] for row in phase_costs)
    critical=0.0
    for phase in schedule["phases"]:
        costs=[]
        for transfer in phase["transfers"]:
            row=route_link(topology,transfer["source_rank"],transfer["destination_rank"])
            costs.append(row["latency_ms"]*1000+transfer["length_bytes"]*8/(row["effective_bandwidth_gbps"]*1000))
        critical+=max(costs)
    return critical


def select_schedule(primitive: str, topology: dict[str, Any], message_size_bytes: int, dtype: str="FP32", reduce_op: str|None="SUM", memory_limit_bytes: int=64*1024*1024) -> dict[str, Any]:
    candidates=[]; rejected=[]
    for algorithm in SUPPORT_MATRIX:
        if primitive not in SUPPORT_MATRIX[algorithm]:
            rejected.append({"algorithm":algorithm,"reason_code":"UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR"})
            continue
        try:
            schedule=generate_schedule(algorithm,primitive,topology,message_size_bytes,dtype,reduce_op,memory_limit_bytes)
            if not _routes_valid(schedule, topology):
                raise ValueError("NO_PATH")
            score=_score_schedule(schedule,topology)
            candidates.append({"algorithm":algorithm,"schedule":schedule,"score":round(score,9)})
        except ValueError as error:
            rejected.append({"algorithm":algorithm,"reason_code":str(error)})
    if not candidates:
        return {"selected_algorithm":None,"selected_schedule_hash":None,"selection_reason":"NO_VALID_CANDIDATE","candidate_algorithms":[],"candidate_schedule_hashes":[],"candidate_scores":[],"rejected_reasons":rejected,"fallback":"NONE"}
    selected=min(candidates,key=lambda row:(row["score"],row["algorithm"]))
    return {"selected_algorithm":selected["algorithm"],"selected_schedule_hash":selected["schedule"]["schedule_hash"],"selected_schedule":selected["schedule"],"selection_reason":"minimum explicit frozen analytical schedule score after invariant validation","candidate_algorithms":[row["algorithm"] for row in candidates],"candidate_schedule_hashes":[row["schedule"]["schedule_hash"] for row in candidates],"candidate_scores":[{"algorithm":row["algorithm"],"score":row["score"]} for row in candidates],"rejected_reasons":rejected,"fallback":"NONE"}
