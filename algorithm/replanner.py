"""Structured topology-event schedule invalidation and replanning."""

from __future__ import annotations

import copy
import time
from typing import Any

from .memory_model import attach_memory_report
from .schedule_ir import validate_schedule
from .schedule_selector import select_schedule
from .topology_model import build_topology, route_link, topology_hash
from simulator.collective_correctness import Case, run_case


EVENT_TYPES={"LINK_DEGRADED","LINK_DOWN","LINK_RECOVERED","RANK_REMOVED","RANK_RECOVERED","NO_ALTERNATE_PATH"}


def _rehash(topology: dict[str, Any]) -> None:
    topology.pop("topology_hash",None); topology["topology_hash"]=topology_hash(topology)


def apply_topology_event(topology: dict[str, Any], event: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event_type=event.get("event_type")
    if event_type not in EVENT_TYPES: raise ValueError(f"unsupported topology event: {event_type}")
    updated=copy.deepcopy(topology); affected=[]
    if event_type in {"RANK_REMOVED","RANK_RECOVERED"}:
        delta=-1 if event_type=="RANK_REMOVED" else 1
        new_size=updated["rank_size"]+delta
        if new_size<2 or new_size>1024: raise ValueError("rank event exceeds supported range")
        affected=[{"rank":event.get("rank",updated["rank_size"]-1),"action":event_type}]
        updated=build_topology(updated["variant"],new_size)
        updated["rank_reconfiguration"]={"event_type":event_type,"old_rank_size":topology["rank_size"],"new_rank_size":new_size,"rank_mapping":"contiguous simulator remap"}
        _rehash(updated); return updated,affected
    source=int(event.get("source_rank",0)); destination=int(event.get("destination_rank",1))
    matched=[row for row in updated["links"] if row["source_rank"]==source and row["destination_rank"]==destination]
    if event_type=="NO_ALTERNATE_PATH":
        isolated=int(event.get("rank",0))
        matched=[row for row in updated["links"] if row["source_rank"]==isolated or row["destination_rank"]==isolated]
        for row in matched: row["healthy"]=False
    elif not matched:
        raise ValueError("event link not present in topology")
    elif event_type=="LINK_DEGRADED":
        for row in matched:
            row["effective_bandwidth_gbps"]*=float(event.get("bandwidth_scale",0.5)); row["latency_ms"]*=float(event.get("latency_scale",2.0)); row["degraded"]=True
    elif event_type=="LINK_DOWN":
        for row in matched: row["healthy"]=False
    elif event_type=="LINK_RECOVERED":
        for row in matched: row["healthy"]=True; row.pop("degraded",None)
    affected=[{"source_rank":row["source_rank"],"destination_rank":row["destination_rank"],"healthy":row["healthy"]} for row in matched]
    _rehash(updated); return updated,affected


def _post_replan_checks(schedule: dict[str, Any], topology: dict[str, Any], memory_budget: int) -> dict[str, Any]:
    validate_schedule(schedule)
    transfers=[transfer for phase in schedule["phases"] for transfer in phase["transfers"]]
    ids=[row["transfer_id"] for row in transfers]
    chunks={row["chunk_id"] for row in transfers}
    routes=all(route_link(topology,row["source_rank"],row["destination_rank"]) is not None for row in transfers)
    return {"invariants_passed":True,"rank_ordering_valid":[node["rank"] for node in topology["nodes"]]==list(range(topology["rank_size"])),"no_duplicate_transfer":len(ids)==len(set(ids)),"no_missing_chunk":chunks==set(range(schedule["chunk_count"])),"route_validity":routes,"bounded_memory":schedule["memory_plan"]["peak_materialized_bytes"]<=memory_budget and schedule["memory_plan"]["within_budget"]}


def replan(old_schedule: dict[str, Any], topology: dict[str, Any], event: dict[str, Any], *, memory_budget_bytes: int=64*1024*1024) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    started=time.perf_counter(); old_topology_hash=topology["topology_hash"]; updated,affected=apply_topology_event(topology,event)
    primitive=old_schedule["primitive"]; message=old_schedule["message_size_bytes"]; dtype=old_schedule["dtype"]; reduce_op=old_schedule["reduce_op"]
    decision=select_schedule(primitive,updated,message,dtype,reduce_op,memory_budget_bytes)
    if decision["selected_schedule_hash"] is None:
        trace={"event_id":event["event_id"],"event_type":event["event_type"],"old_topology_hash":old_topology_hash,"new_topology_hash":updated["topology_hash"],"old_schedule_hash":old_schedule["schedule_hash"],"new_schedule_hash":None,"affected_links":affected,"candidate_count":0,"selected_algorithm":None,"replan_reason":"no reachable invariant-valid candidate; fallback NONE","simulated_replan_time_ms":round((time.perf_counter()-started)*1000,9),"correctness_after_replan":False,"final_status":"EXPECTED_NO_PATH_FAILURE","schedule_invalidated":True,"fallback":"NONE","post_replan_checks":None}
        return updated,None,trace
    schedule=attach_memory_report(decision["selected_schedule"],memory_budget_bytes)
    topology_name={"full_mesh":"FULL_MESH","ring":"RING","fat_tree":"FAT_TREE","asymmetric":"HETEROGENEOUS"}[updated["variant"]]
    outcome=run_case(Case(primitive,dtype,None if primitive=="AllGather" else reduce_op,updated["rank_size"],topology_name,"replan_correctness",message,20260804),exact=True)
    checks=_post_replan_checks(schedule,updated,memory_budget_bytes); correctness=outcome["exact_match"] and outcome["within_dtype_tolerance"] and all(checks.values())
    trace={"event_id":event["event_id"],"event_type":event["event_type"],"old_topology_hash":old_topology_hash,"new_topology_hash":updated["topology_hash"],"old_schedule_hash":old_schedule["schedule_hash"],"new_schedule_hash":schedule["schedule_hash"],"affected_links":affected,"candidate_count":len(decision["candidate_algorithms"]),"selected_algorithm":decision["selected_algorithm"],"replan_reason":"topology hash changed; regenerate, validate, correctness-gate, and select","simulated_replan_time_ms":round((time.perf_counter()-started)*1000,9),"correctness_after_replan":correctness,"output_hash":outcome["output_hash"],"final_status":"REPLANNED" if correctness else "REPLAN_VALIDATION_FAILED","schedule_invalidated":True,"fallback":"NONE","post_replan_checks":checks}
    return updated,schedule,trace
