"""Topology-aware hierarchical non-uniform collective schedule generation."""

from __future__ import annotations

import math
from typing import Any, Callable

from .chunk_policy import select_chunk
from .ring_schedule import generate_ring_schedule
from .schedule_ir import SCHEMA_VERSION, schedule_hash, validate_schedule
from .topology_model import groups, link, route_link


class UnsupportedAlgorithmPrimitivePair(ValueError):
    code = "UNSUPPORTED_ALGORITHM_PRIMITIVE_PAIR"

    def __init__(self, algorithm: str, primitive: str):
        super().__init__(f"{self.code}: {algorithm}/{primitive}")
        self.algorithm = algorithm
        self.primitive = primitive


SUPPORT_MATRIX = {
    "Ring": {"AllReduce", "AllGather", "ReduceScatter"},
    "Butterfly": {"AllReduce", "AllGather"},
    "Mesh": {"AllReduce", "ReduceScatter"},
    "NHR": {"AllReduce"},
    "Hierarchical": {"AllReduce"},
}


def _chunk_ranges(message: int, chunk_size: int) -> list[tuple[int, int, int]]:
    return [(index, offset, min(chunk_size, message - offset)) for index, offset in enumerate(range(0, message, chunk_size))]


def _transfer(phase: int, ordinal: int, source: int, destination: int, chunk: tuple[int, int, int], operation: str, link_id: str) -> dict[str, Any]:
    chunk_id, offset, length = chunk
    return {"chunk_id":chunk_id,"destination_rank":destination,"length_bytes":length,"link_id":link_id,"offset_bytes":offset,"operation":operation,"source_rank":source,"transfer_id":f"transfer-{phase:04d}-{ordinal:06d}"}


def _link_cost(link_row: dict[str, Any], length: int, concurrent: int, cross_group: bool) -> dict[str, float]:
    base = link_row["latency_ms"] * 1000 + length * 8 / (link_row["effective_bandwidth_gbps"] * 1000)
    congestion = base * (max(0, concurrent - 1) * 0.04 + max(0.0, link_row["oversubscription"] - 1.0) * 0.10 + (0.05 if cross_group else 0.0))
    reliability = base * link_row["reliability_penalty"]
    return {"base_link_time":round(base,9),"congestion_penalty":round(congestion+reliability,9),"final_link_time":round(base+congestion+reliability,9)}


def _finalize(algorithm: str, primitive: str, topology: dict[str, Any], message: int, dtype: str, reduce_op: str | None, chunk: dict[str, Any], phases: list[dict[str, Any]], metadata: dict[str, Any]) -> dict[str, Any]:
    chunks = _chunk_ranges(message, chunk["chunk_size"])
    seen = {transfer["chunk_id"] for phase in phases for transfer in phase["transfers"]}
    if seen != set(range(len(chunks))):
        raise ValueError("schedule does not cover every chunk")
    total_bytes = sum(t["length_bytes"] for p in phases for t in p["transfers"])
    schedule = {
        "algorithm":algorithm,"chunk_count":len(chunks),"chunk_size_bytes":chunk["chunk_size"],
        "dependencies":[{"from":phases[index-1]["phase_id"],"to":phases[index]["phase_id"]} for index in range(1,len(phases))],
        "dtype":dtype,"estimated_metrics":{"critical_path_steps":len(phases),"modeled_transfer_bytes":total_bytes,"phase_count":len(phases),"phase_costs":[phase["cost"] for phase in phases]},
        "failure_policy":{"fallback_policy":"NONE","max_retries":3,"on_no_path":"EXPECTED_NO_PATH_FAILURE","retry_policy":"BOUNDED"},
        "hardware_profile_hash":"g3-b2-frozen-hardware-v1","memory_plan":{"bounded":True,"buffer_count":2,"logical_message_bytes":message,"materialization_mode":"CHUNK_STREAMING","materialized_bytes":min(message,chunk["chunk_size"]*2),"chunk_buffer_bytes":chunk["chunk_size"],"temporary_buffer_bytes":chunk["chunk_size"],"peak_materialized_bytes":min(message,chunk["chunk_size"]*2),"memory_budget_bytes":chunk["memory_limit_bytes"],"within_budget":chunk["chunk_size"]*2<=chunk["memory_limit_bytes"]},
        "message_size_bytes":message,"phases":phases,"primitive":primitive,"rank_size":topology["rank_size"],"reduce_op":None if primitive=="AllGather" else reduce_op,
        "schedule_id":f"{algorithm.lower()}-{primitive.lower()}-r{topology['rank_size']}-m{message}","schema_version":SCHEMA_VERSION,"topology_hash":topology["topology_hash"],
        "optimization_metadata":metadata,"chunk_selection":chunk,
    }
    schedule["schedule_hash"] = schedule_hash(schedule)
    validate_schedule(schedule)
    return schedule


def _chunk(topology: dict[str, Any], message: int, memory_limit: int) -> dict[str, Any]:
    links = topology["links"]
    bandwidth = min(row["effective_bandwidth_gbps"] for row in links)
    latency = max(row["latency_ms"] for row in links)
    depth = max(1, math.ceil(math.log2(topology["rank_size"])))
    return select_chunk(message, topology["rank_size"], depth, bandwidth, latency, min(topology["rank_size"],8), memory_limit)


def generate_butterfly(primitive: str, topology: dict[str, Any], message: int, dtype: str="FP32", reduce_op: str|None="SUM", memory_limit: int=64*1024*1024) -> dict[str, Any]:
    if primitive not in SUPPORT_MATRIX["Butterfly"]: raise UnsupportedAlgorithmPrimitivePair("Butterfly",primitive)
    ranks=topology["rank_size"]
    if ranks & (ranks-1): raise ValueError("BUTTERFLY_REQUIRES_POWER_OF_TWO")
    chunk=_chunk(topology,message,memory_limit); chunks=_chunk_ranges(message,chunk["chunk_size"]); phases=[]
    for step in range(int(math.log2(ranks))):
        transfers=[]
        for source in range(ranks):
            destination=source^(1<<step); row=route_link(topology,source,destination)
            if row is None: raise ValueError("NO_PATH")
            for item in chunks: transfers.append(_transfer(step,len(transfers),source,destination,item,"REDUCE" if primitive=="AllReduce" else "COPY",f"{source}->{destination}"))
        costs=[_link_cost(route_link(topology,t["source_rank"],t["destination_rank"]),t["length_bytes"],1,False) for t in transfers]
        phases.append({"dependencies":[] if step==0 else [f"phase-{step-1:04d}"],"phase_id":f"phase-{step:04d}","phase_index":step,"phase_type":"BUTTERFLY_EXCHANGE","transfers":transfers,"cost":{"base_link_time":max(c["base_link_time"] for c in costs),"congestion_penalty":max(c["congestion_penalty"] for c in costs),"final_link_time":max(c["final_link_time"] for c in costs)}})
    return _finalize("Butterfly",primitive,topology,message,dtype,reduce_op,chunk,phases,{"partner_rule":"rank XOR (1 << step)","deterministic_peer_order":True,"power_of_two_required":True})


def nhr_order(topology: dict[str, Any], transfer_bytes: int) -> tuple[list[int], list[dict[str, Any]]]:
    remaining=set(range(topology["rank_size"])); order=[min(remaining)]; remaining.remove(order[0]); segments=[]
    while remaining:
        source=order[-1]; candidates=[]
        for destination in sorted(remaining):
            row=route_link(topology,source,destination)
            if row is None: continue
            cost=_link_cost(row,transfer_bytes,1,True)["final_link_time"]
            candidates.append((cost,destination,row))
        if not candidates: raise ValueError("NO_PATH")
        cost,destination,row=min(candidates,key=lambda item:(item[0],item[1])); order.append(destination); remaining.remove(destination)
        segments.append({"source_rank":source,"destination_rank":destination,"estimated_cost":cost,"link_type":row["link_type"]})
    closing=route_link(topology,order[-1],order[0])
    if closing is None: raise ValueError("NO_PATH")
    segments.append({"source_rank":order[-1],"destination_rank":order[0],"estimated_cost":_link_cost(closing,transfer_bytes,1,True)["final_link_time"],"link_type":closing["link_type"]})
    return order,segments


def generate_nhr(primitive: str, topology: dict[str, Any], message: int, dtype: str="FP32", reduce_op: str|None="SUM", memory_limit: int=64*1024*1024) -> dict[str, Any]:
    if primitive not in SUPPORT_MATRIX["NHR"]: raise UnsupportedAlgorithmPrimitivePair("NHR",primitive)
    chunk=_chunk(topology,message,memory_limit); chunks=_chunk_ranges(message,chunk["chunk_size"]); order,segments=nhr_order(topology,chunk["chunk_size"]); phases=[]
    for step in range(2*(topology["rank_size"]-1)):
        phase_type="REDUCE_SCATTER" if step<topology["rank_size"]-1 else "ALL_GATHER"; transfers=[]; costs=[]
        for index,source in enumerate(order):
            destination=order[(index+1)%len(order)]; row=route_link(topology,source,destination)
            for item in chunks:
                transfers.append(_transfer(step,len(transfers),source,destination,item,"REDUCE" if phase_type=="REDUCE_SCATTER" else "COPY",f"{source}->{destination}")); costs.append(_link_cost(row,item[2],1,True))
        phases.append({"dependencies":[] if step==0 else [f"phase-{step-1:04d}"],"phase_id":f"phase-{step:04d}","phase_index":step,"phase_type":phase_type,"transfers":transfers,"cost":{"base_link_time":max(c["base_link_time"] for c in costs),"congestion_penalty":max(c["congestion_penalty"] for c in costs),"final_link_time":max(c["final_link_time"] for c in costs)}})
    return _finalize("NHR",primitive,topology,message,dtype,reduce_op,chunk,phases,{"non_uniform_ring_order":order,"segment_costs":segments,"weight_formula":"latency_cost + transfer_bytes/effective_bandwidth + congestion_penalty + reliability_penalty","topology_assumption":topology["variant"]})


def generate_hierarchical(primitive: str, topology: dict[str, Any], message: int, dtype: str="FP32", reduce_op: str|None="SUM", memory_limit: int=64*1024*1024) -> dict[str, Any]:
    if primitive not in SUPPORT_MATRIX["Hierarchical"]: raise UnsupportedAlgorithmPrimitivePair("Hierarchical",primitive)
    group_rows=groups(topology)
    if len(group_rows)<2: raise ValueError("NO_VALID_HIERARCHY")
    chunk=_chunk(topology,message,memory_limit); chunks=_chunk_ranges(message,chunk["chunk_size"]); phases=[]
    definitions=[("INTRA_GROUP_REDUCE",[(rank,g["leader"]) for g in group_rows for rank in g["ranks"] if rank!=g["leader"]]),("INTER_GROUP_ALLREDUCE",[(g["leader"],group_rows[(index+1)%len(group_rows)]["leader"]) for index,g in enumerate(group_rows)]),("INTRA_GROUP_DISTRIBUTE",[(g["leader"],rank) for g in group_rows for rank in g["ranks"] if rank!=g["leader"]])]
    for index,(phase_type,pairs) in enumerate(definitions):
        transfers=[]; costs=[]
        for source,destination in pairs:
            row=link(topology,source,destination)
            if row is None: raise ValueError("NO_PATH")
            cross=next(n["group_id"] for n in topology["nodes"] if n["rank"]==source)!=next(n["group_id"] for n in topology["nodes"] if n["rank"]==destination)
            for item in chunks:
                transfers.append(_transfer(index,len(transfers),source,destination,item,"REDUCE" if phase_type!="INTRA_GROUP_DISTRIBUTE" else "COPY",f"{source}->{destination}")); costs.append(_link_cost(row,item[2],len(pairs),cross))
        phases.append({"dependencies":[] if index==0 else [f"phase-{index-1:04d}"],"phase_id":f"phase-{index:04d}","phase_index":index,"phase_type":phase_type,"transfers":transfers,"cost":{"base_link_time":max(c["base_link_time"] for c in costs),"congestion_penalty":max(c["congestion_penalty"] for c in costs),"final_link_time":max(c["final_link_time"] for c in costs)}})
    return _finalize("Hierarchical",primitive,topology,message,dtype,reduce_op,chunk,phases,{"groups":group_rows,"group_source":topology["group_source"],"leaders":[g["leader"] for g in group_rows],"intra_link":"HCCS/PCIe from topology","inter_link":"RoCE from topology","oversubscription":max(row["oversubscription"] for row in topology["links"]),"fallback_condition":"NONE; structured failure","no_valid_hierarchy_condition":"fewer than two explicit metadata groups"})


def generate_mesh(primitive: str, topology: dict[str, Any], message: int, dtype: str="FP32", reduce_op: str|None="SUM", memory_limit: int=64*1024*1024) -> dict[str, Any]:
    if primitive not in SUPPORT_MATRIX["Mesh"]: raise UnsupportedAlgorithmPrimitivePair("Mesh",primitive)
    ranks=topology["rank_size"]; fanout=4 if topology["variant"]=="full_mesh" else 2; chunk=_chunk(topology,message,memory_limit); chunks=_chunk_ranges(message,chunk["chunk_size"])
    packed: list[dict[str, Any]]=[]
    detected_conflicts=0
    for offset in range(1,ranks):
        for source in range(ranks):
            destination=(source+offset)%ranks; row=route_link(topology,source,destination)
            if row is None: raise ValueError("NO_PATH")
            route=row.get("route",[source,destination]); edges={(route[index],route[index+1]) for index in range(len(route)-1)}
            placed=False
            for bucket in packed:
                if not (edges & bucket["edges"]) and bucket["source_counts"].get(source,0)<fanout:
                    bucket["operations"].append((source,destination,row)); bucket["edges"].update(edges); bucket["source_counts"][source]=bucket["source_counts"].get(source,0)+1; placed=True; break
                detected_conflicts += int(bool(edges & bucket["edges"]))
            if not placed:
                packed.append({"operations":[(source,destination,row)],"edges":set(edges),"source_counts":{source:1}})
    phases=[]
    for phase_index,bucket in enumerate(packed):
        transfers=[]; costs=[]
        for source,destination,row in bucket["operations"]:
            route=row.get("route",[source,destination]); link_id="route:"+"->".join(str(rank) for rank in route)
            for item in chunks:
                transfers.append(_transfer(phase_index,len(transfers),source,destination,item,"REDUCE",link_id)); costs.append(_link_cost(row,item[2],len(bucket["operations"]),False))
        phases.append({"dependencies":[] if phase_index==0 else [f"phase-{phase_index-1:04d}"],"phase_id":f"phase-{phase_index:04d}","phase_index":phase_index,"phase_type":"MESH_TRANSFER","transfers":transfers,"cost":{"base_link_time":max(c["base_link_time"] for c in costs),"congestion_penalty":max(c["congestion_penalty"] for c in costs),"final_link_time":max(c["final_link_time"] for c in costs)}})
    return _finalize("Mesh",primitive,topology,message,dtype,reduce_op,chunk,phases,{"fanout_limit":fanout,"shared_link_conflict_check":True,"detected_conflicts_serialized":detected_conflicts,"topology_constraint":"direct full-mesh links" if topology["variant"]=="full_mesh" else "physical-edge-disjoint bounded fanout"})


def generate_schedule(algorithm: str, primitive: str, topology: dict[str, Any], message: int, dtype: str="FP32", reduce_op: str|None="SUM", memory_limit: int=64*1024*1024) -> dict[str, Any]:
    if algorithm not in SUPPORT_MATRIX or primitive not in SUPPORT_MATRIX[algorithm]: raise UnsupportedAlgorithmPrimitivePair(algorithm,primitive)
    if algorithm=="Ring": return generate_ring_schedule(primitive,topology["rank_size"],message,dtype=dtype,reduce_op=reduce_op,topology_hash=topology["topology_hash"])
    generators: dict[str,Callable[...,dict[str,Any]]]={"Butterfly":generate_butterfly,"Mesh":generate_mesh,"NHR":generate_nhr,"Hierarchical":generate_hierarchical}
    return generators[algorithm](primitive,topology,message,dtype,reduce_op,memory_limit)
