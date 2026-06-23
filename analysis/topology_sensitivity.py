#!/usr/bin/env python3
"""Topology sensitivity — compare topologies at 32 nodes."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from simulator.simulator import Simulator

def main():
    sim = Simulator()
    configs = [
        ("Full Mesh", 32, "SINGLE_NODE"),
        ("Ring", 32, "SINGLE_NODE"),
        ("Fat Tree", 32, "MULTI_NODE"),
        ("Hierarchical", 32, "MULTI_NODE"),
        ("Heterogeneous", 24, "HETEROGENEOUS"),
    ]
    rows = []
    for name, n, mode in configs:
        gpu_per = 8 if n >= 8 else n
        g, _ = TopologyGraphBuilder.build(n, num_gpus_per_node=gpu_per, mode=mode)
        r = sim.simulate_with_graph(g, "AllReduce", "Ring AllReduce", 256)
        bd = sim.model.calculate_score_breakdown(r["latency"], r["bandwidth"])
        rows.append((name, n, r["latency"], r["bandwidth"], bd["score"]))

    rows.sort(key=lambda x: x[4], reverse=True)
    lines = ["# Topology Sensitivity", "",
             "Fixed: Primitive=AllReduce, 256MB, Ring AllReduce", "",
             "| Topology | Nodes | Latency (ms) | Bandwidth (GB/s) | Score |",
             "|----------|-------|-------------|------------------|-------|"]
    for name, n, lat, bw, sc in rows:
        lines.append(f"| {name:20s} | {n:5d} | {lat:11.4f} | {bw:16.2f} | {sc:5.1f} |")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "topology_sensitivity.md")
    with open(out, "w") as f: f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__": main()
