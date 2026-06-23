#!/usr/bin/env python3
"""Benchmark Runner — execute all scenarios and generate reports.

Usage:
    python3 experiments/benchmark_runner.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from agent.hccl_agent import HCCLAgent
from skills.benchmark_suite_skill import BenchmarkSuiteSkill


def main() -> None:
    agent = HCCLAgent()
    suite = BenchmarkSuiteSkill(agent)

    scenarios = suite.load_all_scenarios()
    print(f"Loaded {len(scenarios)} scenarios.\n")

    results = []
    for s in scenarios:
        print(f"  Running: {s['name']} ... ", end="", flush=True)
        r = suite.run_scenario(s)
        results.append(r)
        print(f" → {r['algorithm']} (score={r['score']:.1f})")

    # Generate per-scenario reports.
    reports_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "reports",
    )
    for r in results:
        suite.generate_scenario_report(r, output_dir=reports_dir)

    # Generate summary.
    summary = suite.generate_summary(results, output_dir=reports_dir)
    print(f"\nReports written to {reports_dir}/")
    print(summary)


if __name__ == "__main__":
    main()
