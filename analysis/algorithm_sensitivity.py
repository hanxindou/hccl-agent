#!/usr/bin/env python3
"""Algorithm sensitivity — compare 5 algorithms at 32 nodes."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from simulator.simulator import Simulator

def main():
    sim = Simulator()
    g, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode="MULTI_NODE")
    algos = ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"]
    rows = []
    for a in algos:
        r = sim.simulate_with_graph(g, "AllReduce", a, 256)
        bd = sim.model.calculate_score_breakdown(r["latency"], r["bandwidth"])
        rows.append((a, r["latency"], r["bandwidth"], bd["score"]))

    rows.sort(key=lambda x: x[3], reverse=True)
    lines = ["# Algorithm Sensitivity", "",
             "Fixed: Nodes=32, Topology=FatTree, Primitive=AllReduce, 256MB", "",
             "| Algorithm | Latency (ms) | Bandwidth (GB/s) | Score |",
             "|-----------|-------------|------------------|-------|"]
    for a, lat, bw, sc in rows:
        lines.append(f"| {a:20s} | {lat:11.4f} | {bw:16.2f} | {sc:5.1f} |")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "algorithm_sensitivity.md")
    with open(out, "w") as f: f.write("\n".join(lines) + "\n")
    print("\n".join(lines))

if __name__ == "__main__": main()
