"""Explicit weighted topology metadata for G3-B2 optimization schedules."""

from __future__ import annotations

import hashlib
import heapq
import json
from typing import Any


def topology_hash(topology: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(topology, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def build_topology(variant: str, ranks: int) -> dict[str, Any]:
    if ranks < 2 or ranks > 1024:
        raise ValueError("topology rank size must be 2..1024")
    if variant not in {"full_mesh", "ring", "fat_tree", "asymmetric"}:
        raise ValueError(f"unsupported topology variant: {variant}")
    group_size = 8
    nodes = []
    for rank in range(ranks):
        nodes.append({"rank": rank, "node_id": f"node-{rank // group_size}", "group_id": f"group-{rank // group_size}", "local_rank": rank % group_size})
    links = []

    def add(source: int, destination: int, link_type: str, bandwidth: float, latency: float, *, oversubscription: float = 1.0, reliability_penalty: float = 0.0, parent_edge: str | None = None) -> None:
        links.append({"source_rank":source,"destination_rank":destination,"link_type":link_type,"effective_bandwidth_gbps":bandwidth,"latency_ms":latency,"oversubscription":oversubscription,"reliability_penalty":reliability_penalty,"utilization":0.0,"parent_edge":parent_edge,"healthy":True})

    if variant == "full_mesh":
        for source in range(ranks):
            for destination in range(ranks):
                if source != destination:
                    add(source, destination, "HCCS", 100.0, 0.002)
    elif variant == "ring":
        for source in range(ranks):
            destination = (source + 1) % ranks
            add(source, destination, "HCCS" if ranks <= 8 else "RoCE", 100.0 if ranks <= 8 else 50.0, 0.002 if ranks <= 8 else 0.005)
            add(destination, source, "HCCS" if ranks <= 8 else "RoCE", 100.0 if ranks <= 8 else 50.0, 0.002 if ranks <= 8 else 0.005)
    else:
        for source in range(ranks):
            node_start = (source // group_size) * group_size
            for destination in range(node_start, min(node_start + group_size, ranks)):
                if source != destination:
                    bandwidth = 100.0
                    latency = 0.002
                    if variant == "asymmetric" and (source + destination) % 5 == 0:
                        bandwidth, latency = 32.0, 0.010
                    add(source, destination, "HCCS" if bandwidth == 100.0 else "PCIe", bandwidth, latency)
        leaders = list(range(0, ranks, group_size))
        for source in leaders:
            for destination in leaders:
                if source != destination:
                    if variant == "asymmetric":
                        selector = (source // group_size + destination // group_size) % 3
                        bandwidth = (25.0, 40.0, 50.0)[selector]
                        latency = (0.014, 0.008, 0.005)[selector]
                        reliability = (0.0002, 0.0001, 0.0)[selector]
                    else:
                        bandwidth, latency, reliability = 50.0, 0.005, 0.0
                    add(source, destination, "RoCE", bandwidth, latency, oversubscription=2.5 if variant == "asymmetric" else 2.0, reliability_penalty=reliability, parent_edge=f"uplink-{source // group_size}")
    topology = {"schema_version":"g3-b2-topology-v1","variant":variant,"rank_size":ranks,"nodes":nodes,"links":links,"group_source":"explicit node metadata","group_size":group_size}
    topology["topology_hash"] = topology_hash(topology)
    return topology


def groups(topology: dict[str, Any]) -> list[dict[str, Any]]:
    by_group: dict[str, list[int]] = {}
    for node in topology["nodes"]:
        by_group.setdefault(node["group_id"], []).append(node["rank"])
    return [{"group_id": key, "ranks": sorted(value), "leader": min(value)} for key, value in sorted(by_group.items())]


def link(topology: dict[str, Any], source: int, destination: int) -> dict[str, Any] | None:
    return next((row for row in topology["links"] if row["source_rank"] == source and row["destination_rank"] == destination and row["healthy"]), None)


def route_link(topology: dict[str, Any], source: int, destination: int) -> dict[str, Any] | None:
    direct = link(topology, source, destination)
    if direct is not None:
        return {**direct, "route": [source, destination]}
    queue = [(0.0, source, [source], float("inf"), 0.0, 1.0, 0.0, [])]
    best = {source: 0.0}
    while queue:
        cost, current, path, bandwidth, latency, oversubscription, reliability, types = heapq.heappop(queue)
        if current == destination:
            return {"source_rank":source,"destination_rank":destination,"link_type":"+".join(types),"effective_bandwidth_gbps":bandwidth,"latency_ms":latency,"oversubscription":oversubscription,"reliability_penalty":reliability,"utilization":0.0,"parent_edge":"multihop","healthy":True,"route":path}
        if cost > best.get(current, float("inf")):
            continue
        for row in topology["links"]:
            if row["source_rank"] != current or not row["healthy"] or row["destination_rank"] in path:
                continue
            edge_cost = row["latency_ms"] + 1.0 / row["effective_bandwidth_gbps"]
            next_cost = cost + edge_cost
            neighbor = row["destination_rank"]
            if next_cost < best.get(neighbor, float("inf")):
                best[neighbor] = next_cost
                heapq.heappush(queue,(next_cost,neighbor,path+[neighbor],min(bandwidth,row["effective_bandwidth_gbps"]),latency+row["latency_ms"],max(oversubscription,row["oversubscription"]),reliability+row["reliability_penalty"],types+[row["link_type"]]))
    return None
