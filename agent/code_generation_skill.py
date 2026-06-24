"""Code Generation Skill — produce HCCL configs, execution plans,
algorithm skeletons, and optimization notes."""

from typing import Any, Dict, List


class CodeGenerationSkill:
    """Generate communication strategy artifacts from algorithm selection."""

    @staticmethod
    def generate_hccl_config(
        primitive: str,
        algorithm: str,
        topology_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Produce a simulated HCCL configuration block.

        Parameters
        ----------
        primitive : str  — AllReduce / AllGather / ReduceScatter
        algorithm : str  — e.g. "Ring AllReduce"
        topology_summary : dict  — from TopologyReasoningSkill

        Returns
        -------
        dict  with algorithm, chunk_size_mb, pipeline_depth,
              communication_pattern, expected_bandwidth, expected_latency.
        """
        chunk = 1.0
        depth = 2
        if "Ring" in algorithm:
            pattern = "Ring (ReduceScatter → AllGather)"
            chunk = 0.5
        elif algorithm == "Butterfly":
            pattern = "Recursive Doubling (log-N pairwise)"
            depth = 1
        elif algorithm == "Mesh":
            pattern = "Full Mesh (concurrent all-to-all)"
            depth = 1
        elif algorithm == "NHR":
            pattern = "Hierarchical Ring (group reduce → leader ring → broadcast)"
        elif algorithm == "Fat-Tree":
            pattern = "Fat-Tree (leaf aggregation → core aggregation → broadcast)"
        else:
            pattern = "Generic"

        expected_bw = 100.0
        expected_lat = 0.002 * topology_summary.get("node_count", 8)

        return {
            "algorithm": algorithm,
            "primitive": primitive,
            "chunk_size_mb": chunk,
            "pipeline_depth": depth,
            "communication_pattern": pattern,
            "expected_bandwidth_gbps": expected_bw,
            "expected_latency_ms": round(expected_lat, 6),
        }

    @staticmethod
    def generate_execution_plan(
        algorithm: str,
        primitive: str,
    ) -> Dict[str, str]:
        """Return a phased execution plan."""
        if "Ring" in algorithm:
            return {
                "phase1": "ReduceScatter — each rank splits data, circulates chunks along ring",
                "phase2": "Ring Exchange — partial sums propagate through pipeline",
                "phase3": "AllGather — fully reduced chunks circulate to all ranks",
            }
        elif algorithm == "Butterfly":
            return {
                "phase1": "Pairwise exchange at distance=1 (nearest neighbour)",
                "phase2": f"Recursive doubling at distance=2,4,8… up to N/2",
                "phase3": "Final broadcast — all ranks hold global result",
            }
        elif algorithm == "Mesh":
            return {
                "phase1": "Concurrent all-to-all send (N×(N-1) simultaneous transfers)",
                "phase2": "Local reduction on each rank",
            }
        elif algorithm == "NHR":
            return {
                "phase1": "Group-local ring reduce (group_size=4)",
                "phase2": "Leader ring reduce across groups",
                "phase3": "Group broadcast — leaders distribute to members",
            }
        elif algorithm == "Fat-Tree":
            return {
                "phase1": "Leaf aggregation — intra-group sum",
                "phase2": "Core aggregation — inter-group leader sum",
                "phase3": "Broadcast — global result to all leaves",
            }
        return {}

    @staticmethod
    def generate_algorithm_skeleton(
        algorithm: str,
        primitive: str,
    ) -> str:
        """Return pseudo-code skeleton of the algorithm."""
        name = algorithm.replace(" ", "")
        phases = CodeGenerationSkill.generate_execution_plan(algorithm, primitive)
        lines = [f"class {name}:", "", f"    def execute(self):"]
        for i, (_, desc) in enumerate(phases.items()):
            method = desc.split(" —")[0].replace(" ", "_").replace("-", "_").lower()
            lines.append(f"        {method}()  # {desc}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def generate_optimization_notes(
        algorithm: str,
        topology_summary: Dict[str, Any],
    ) -> List[str]:
        """Return a list of natural-language optimization notes."""
        notes = [
            f"Selected {algorithm} based on graph-simulated performance.",
            f"Topology: {topology_summary.get('topology_type', 'unknown')} "
            f"({topology_summary.get('node_count', '?')} nodes, "
            f"dominant link: {topology_summary.get('dominant_link', '?')}).",
        ]
        if "Ring" in algorithm:
            notes.append(
                "Ring AllReduce balances bandwidth and latency for "
                "medium-to-large message sizes."
            )
        elif algorithm == "Butterfly":
            notes.append(
                "Butterfly minimises latency (log-N steps) — ideal for "
                "small messages (≤64 KB)."
            )
        elif algorithm == "Mesh":
            notes.append(
                "Mesh maximises bandwidth on full-interconnect topologies "
                "but suffers from O(N²) link contention at scale."
            )
        elif algorithm == "NHR":
            notes.append(
                "NHR leverages hierarchical grouping to reduce ring steps "
                "on multi-node clusters."
            )
        elif algorithm == "Fat-Tree":
            notes.append(
                "Fat-Tree scales efficiently to large node counts through "
                "two-level aggregation."
            )
        notes.append(
            "Potential bottleneck: inter-node link bandwidth — consider "
            "pipeline depth tuning if latency increases."
        )
        return notes
