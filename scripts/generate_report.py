#!/usr/bin/env python3
"""Generate a Markdown performance report from experiment logs.

Reads logs/runs.jsonl and produces a report covering algorithm comparison,
latency/bandwidth analysis, and winner statistics — matching the
competition's performance report requirement.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime


def load_runs(log_dir=None):
    if log_dir is None:
        log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "logs",
        )
    run_log = os.path.join(log_dir, "runs.jsonl")
    if not os.path.exists(run_log):
        print(f"No run log found at {run_log}", file=sys.stderr)
        return []

    runs = []
    with open(run_log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    runs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return runs


def build_algorithm_comparison(runs):
    """Group runs by algorithm, compute avg latency / bandwidth / score."""
    groups = defaultdict(list)
    for r in runs:
        algo = r.get("best_algorithm", "unknown")
        br = r.get("best_result", {})
        groups[algo].append({
            "latency": br.get("latency", 0),
            "bandwidth": br.get("bandwidth", 0),
            "score": br.get("score", 0),
        })

    rows = []
    for algo, entries in sorted(groups.items()):
        n = len(entries)
        avg_lat = sum(e["latency"] for e in entries) / n
        avg_bw = sum(e["bandwidth"] for e in entries) / n
        avg_score = sum(e["score"] for e in entries) / n
        rows.append({
            "algorithm": algo,
            "runs": n,
            "avg_latency_ms": round(avg_lat, 4),
            "avg_bandwidth_gbs": round(avg_bw, 2),
            "avg_score": round(avg_score, 2),
        })

    # Sort by avg_score descending.
    rows.sort(key=lambda x: x["avg_score"], reverse=True)
    return rows


def build_primitive_breakdown(runs):
    groups = defaultdict(list)
    for r in runs:
        p = r.get("primitive", "unknown")
        groups[p].append(r.get("best_result", {}).get("score", 0))

    rows = []
    for prim, scores in sorted(groups.items()):
        rows.append({
            "primitive": prim,
            "runs": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
        })
    return rows


def build_topology_breakdown(runs):
    groups = defaultdict(list)
    for r in runs:
        t = r.get("topology", "unknown")
        groups[t].append(r)

    rows = []
    for topo, entries in sorted(groups.items()):
        algos = defaultdict(int)
        for e in entries:
            algos[e.get("best_algorithm", "?")] += 1
        best_algo = max(algos, key=algos.get)
        rows.append({
            "topology": topo,
            "runs": len(entries),
            "top_algorithm": best_algo,
            "algo_distribution": dict(algos),
        })
    return rows


def build_message_size_analysis(runs):
    """Compare algorithm choice by message-size bucket."""
    buckets = [
        (0, 0.064, "<=64 KB"),
        (0.064, 1, "64 KB – 1 MB"),
        (1, 512, "1 MB – 512 MB"),
        (512, 1024, "512 MB – 1 GB"),
        (1024, float("inf"), ">=1 GB"),
    ]

    rows = []
    for lo, hi, label in buckets:
        in_range = [
            r for r in runs
            if lo <= r.get("message_size_mb", 0) < hi
        ]
        if not in_range:
            continue
        algo_counts = defaultdict(int)
        for r in in_range:
            algo_counts[r.get("best_algorithm", "?")] += 1
        rows.append({
            "range": label,
            "runs": len(in_range),
            "top_algorithm": max(algo_counts, key=algo_counts.get),
            "distribution": dict(algo_counts),
        })
    return rows


def generate_report(runs, output_path=None):
    """Generate a full Markdown report and write to *output_path*.

    If output_path is None, the report is written to
    logs/performance_report.md.
    """
    if output_path is None:
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "logs",
            "performance_report.md",
        )

    if not runs:
        report = [
            "# HCCL Agent — Performance Report",
            "",
            f"**Generated:** {datetime.utcnow().isoformat()}Z",
            "",
            "## Status",
            "",
            "No experiment runs recorded yet. Run `python3 main.py` with "
            "some parameters to populate the log.",
        ]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report) + "\n")
        print(f"Empty report written to {output_path}")
        return output_path

    algo_rows = build_algorithm_comparison(runs)
    prim_rows = build_primitive_breakdown(runs)
    topo_rows = build_topology_breakdown(runs)
    msg_rows = build_message_size_analysis(runs)

    lines = []
    lines.append("# HCCL Agent — Performance Report")
    lines.append("")
    lines.append(
        f"**Generated:** {datetime.utcnow().isoformat()}Z  "
    )
    lines.append(f"**Total runs:** {len(runs)}")
    lines.append("")

    # ---- Algorithm Comparison ----
    lines.append("## 1. Algorithm Performance Comparison")
    lines.append("")
    lines.append(
        "| Algorithm | Runs | Avg Latency (ms) | Avg Bandwidth (GB/s) | "
        "Avg Score |"
    )
    lines.append(
        "|-----------|------|------------------|----------------------|"
        "----------|"
    )
    for r in algo_rows:
        lines.append(
            f"| {r['algorithm']} | {r['runs']} | "
            f"{r['avg_latency_ms']} | {r['avg_bandwidth_gbs']} | "
            f"{r['avg_score']} |"
        )
    lines.append("")

    # ---- Primitive Breakdown ----
    lines.append("## 2. Performance by Collective Primitive")
    lines.append("")
    lines.append(
        "| Primitive | Runs | Avg Score | Min Score | Max Score |"
    )
    lines.append(
        "|-----------|------|-----------|-----------|-----------|"
    )
    for r in prim_rows:
        lines.append(
            f"| {r['primitive']} | {r['runs']} | "
            f"{r['avg_score']} | {r['min_score']} | {r['max_score']} |"
        )
    lines.append("")

    # ---- Topology Breakdown ----
    lines.append("## 3. Algorithm Wins by Topology")
    lines.append("")
    lines.append(
        "| Topology | Runs | Top Algorithm | Distribution |"
    )
    lines.append(
        "|----------|------|---------------|--------------|"
    )
    for r in topo_rows:
        dist_str = ", ".join(
            f"{a}: {c}" for a, c in r["algo_distribution"].items()
        )
        lines.append(
            f"| {r['topology']} | {r['runs']} | "
            f"{r['top_algorithm']} | {dist_str} |"
        )
    lines.append("")

    # ---- Message-Size Analysis ----
    lines.append("## 4. Algorithm Choice by Message Size")
    lines.append("")
    lines.append(
        "| Message Size Range | Runs | Top Algorithm | Distribution |"
    )
    lines.append(
        "|--------------------|------|---------------|--------------|"
    )
    for r in msg_rows:
        dist_str = ", ".join(
            f"{a}: {c}" for a, c in r["distribution"].items()
        )
        lines.append(
            f"| {r['range']} | {r['runs']} | "
            f"{r['top_algorithm']} | {dist_str} |"
        )
    lines.append("")

    # ---- Recent Runs ----
    lines.append("## 5. Recent Runs (last 10)")
    lines.append("")
    lines.append(
        "| Time | Nodes | Msg (MB) | Primitive | Topology | "
        "Best Algorithm | Score |"
    )
    lines.append(
        "|------|-------|----------|-----------|----------|"
        "----------------|-------|"
    )
    for r in runs[-10:]:
        ts = r.get("timestamp", "?")[:19]
        lines.append(
            f"| {ts} | {r.get('nodes', '?')} | "
            f"{r.get('message_size_mb', '?')} | "
            f"{r.get('primitive', '?')} | "
            f"{r.get('topology', '?')} | "
            f"{r.get('best_algorithm', '?')} | "
            f"{r.get('best_result', {}).get('score', '?')} |"
        )
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Report written to {output_path}")
    return output_path


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(script_dir, "..", "logs")
    runs = load_runs(log_dir)
    generate_report(runs)


if __name__ == "__main__":
    main()
