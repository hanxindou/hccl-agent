#!/usr/bin/env python3
"""Auto-Tuning sensitivity analysis — find best parameter combination."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.auto_tuning_skill import AutoTuningSkill
from topology.graph_builder import TopologyGraphBuilder
from simulator.simulator import Simulator


def main():
    g, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode="MULTI_NODE")
    sim = Simulator()
    base = sim.simulate_with_graph(g, "AllReduce", "NHR", 256)
    result = AutoTuningSkill.grid_search(
        "NHR", "Fat Tree", 32, 256, base["score"],
    )

    lines = [
        "# Auto-Tuning Analysis", "",
        f"Evaluated: {result['evaluated_configs']} configurations", "",
        "## Best Configuration",
        f"- chunk_size_mb:  {result['best_config']['chunk_size_mb']}",
        f"- pipeline_depth: {result['best_config']['pipeline_depth']}",
        f"- overlap_factor: {result['best_config']['overlap_factor']}",
        f"- Best score:     {result['best_score']:.1f}",
        f"- Base score:     {base['score']:.1f}",
        f"- Improvement:    +{result['best_score'] - base['score']:.1f} pts",
        "",
        "## Top 5 Configurations", "",
        "| Rank | chunk_size | depth | overlap | Score |",
        "|------|-----------|-------|---------|-------|",
    ]
    for i, entry in enumerate(result["top_k"]):
        c = entry["config"]
        lines.append(
            f"| {i+1} | {c['chunk_size_mb']:.0f} | {c['pipeline_depth']:.0f} | "
            f"{c['overlap_factor']:.2f} | {entry['score']:.1f} |"
        )

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "auto_tuning_analysis.md")
    with open(out, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
