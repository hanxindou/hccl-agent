"""Benchmark Suite Skill — run standard scenarios and generate reports."""

import json
import os
from typing import Any, Dict, List


class BenchmarkSuiteSkill:
    """Execute predefined scenarios through the Agent and collect results."""

    def __init__(self, agent: Any = None) -> None:
        self.agent = agent  # HCCLAgent instance (set after init)

    def set_agent(self, agent: Any) -> None:
        self.agent = agent

    # ------------------------------------------------------------------
    # Scenario loading
    # ------------------------------------------------------------------

    @staticmethod
    def load_scenario(path: str) -> Dict[str, Any]:
        """Load a single scenario JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_all_scenarios(
        scenarios_dir: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Load every .json file in *scenarios_dir*."""
        if scenarios_dir is None:
            scenarios_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..", "experiments", "scenarios",
            )
        scenarios: List[Dict[str, Any]] = []
        for fname in sorted(os.listdir(scenarios_dir)):
            if fname.endswith(".json"):
                path = os.path.join(scenarios_dir, fname)
                scenarios.append(BenchmarkSuiteSkill.load_scenario(path))
        return scenarios

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single scenario through the Agent."""
        if self.agent is None:
            raise RuntimeError("BenchmarkSuiteSkill: agent not set.")

        output = self.agent.run(
            nodes=scenario["nodes"],
            message_size=scenario.get("message_size_mb", 128),
            primitive=scenario.get("primitive", "AllReduce"),
        )

        return {
            "scenario": scenario,
            "algorithm": output.get("algorithm", "N/A"),
            "topology": output.get("topology", "N/A"),
            "score": output.get("best_result", {}).get("score", 0),
            "latency": output.get("best_result", {}).get("latency", 0),
            "bandwidth": output.get("best_result", {}).get("bandwidth", 0),
            "decision_trace": output.get("decision_trace", {}),
            "reflection": output.get("reflection", {}),
        }

    def run_all_scenarios(
        self, scenarios: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        """Run every scenario and return results."""
        if scenarios is None:
            scenarios = self.load_all_scenarios()
        return [self.run_scenario(s) for s in scenarios]

    # ------------------------------------------------------------------
    # Report generation
    # ------------------------------------------------------------------

    @staticmethod
    def generate_scenario_report(
        result: Dict[str, Any], output_dir: str | None = None,
    ) -> str:
        """Write a Markdown report for one scenario result."""
        s = result["scenario"]
        dq = result.get("reflection", {}).get("decision_quality") or {}

        lines = [
            f"# Scenario: {s['name']}",
            "",
            "## Scenario Information",
            f"- **Name:** {s['name']}",
            f"- **Nodes:** {s['nodes']}",
            f"- **Topology:** {s['topology']}",
            f"- **Primitive:** {s['primitive']}",
            f"- **Message Size:** {s['message_size_mb']} MB",
            "",
            "## Selected Algorithm",
            f"- **Algorithm:** {result['algorithm']}",
            f"- **Score:** {result['score']:.1f}",
            f"- **Latency:** {result['latency']:.4f} ms",
            f"- **Bandwidth:** {result['bandwidth']:.2f} GB/s",
            "",
            "## Decision Quality",
            f"- **Selected:** {dq.get('selected_algorithm', 'N/A')}",
            f"- **Best Alternative:** {dq.get('best_alternative', 'N/A')}",
            f"- **Score Gap:** {dq.get('score_gap', 'N/A')}",
            f"- **Verdict:** {dq.get('recommendation', 'N/A')}",
            "",
            "## Reflection",
            f"- **Status:** {result.get('reflection', {}).get('status', 'N/A').upper()}",
            f"- **Need Replan:** {result.get('reflection', {}).get('need_replan', False)}",
            "",
        ]

        dt = result.get("decision_trace", {}).get("decision_trace", [])
        if dt:
            lines += ["## Decision Trace", ""]
            for line in dt:
                lines.append(f"- {line}")

        report = "\n".join(lines) + "\n"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            out_path = os.path.join(output_dir, f"{s['name']}.md")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report)

        return report

    @staticmethod
    def generate_summary(
        results: List[Dict[str, Any]],
        output_dir: str | None = None,
    ) -> str:
        """Write a benchmark summary Markdown table."""
        header = (
            "| Scenario | Algorithm | Score | Latency (ms) | Bandwidth (GB/s) | Decision Quality |\n"
            "|----------|-----------|-------|--------------|------------------|------------------|"
        )
        rows = []
        for r in results:
            s = r["scenario"]
            dq = r.get("reflection", {}).get("decision_quality") or {}
            quality = dq.get("recommendation", "N/A")
            rows.append(
                f"| {s['name']} | {r['algorithm']} | {r['score']:.1f} | "
                f"{r['latency']:.4f} | {r['bandwidth']:.2f} | {quality} |"
            )

        summary = (
            "# Benchmark Summary\n\n"
            + header + "\n"
            + "\n".join(rows) + "\n"
        )

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            with open(os.path.join(output_dir, "benchmark_summary.md"), "w",
                      encoding="utf-8") as f:
                f.write(summary)

        return summary
