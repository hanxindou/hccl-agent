"""Topology Reasoning Skill — analyse a CommunicationGraph."""

from typing import Any, Dict


class TopologyReasoningSkill:
    """Extract structural properties from a communication graph."""

    @staticmethod
    def analyze(graph: Any) -> Dict[str, Any]:
        """Return human-readable topology summary.

        Parameters
        ----------
        graph : CommunicationGraph
            From topology/graph_builder.py.

        Returns
        -------
        dict  with topology_type, node_count, edge_count,
              average_degree, dominant_link.
        """
        N = graph.num_nodes
        E = len(graph.edges)
        avg_deg = E / max(N, 1)

        link_counts: Dict[str, int] = {}
        for e in graph.edges:
            link_counts[e.link_type] = link_counts.get(e.link_type, 0) + 1
        dominant = max(link_counts, key=link_counts.get) if link_counts else "N/A"

        if N <= 8:
            topo_type = "SingleNode FullMesh"
        elif N <= 64:
            topo_type = "MultiNode FatTree"
        else:
            topo_type = "LargeScale FatTree"

        return {
            "topology_type": topo_type,
            "node_count": N,
            "edge_count": E,
            "average_degree": round(avg_deg, 2),
            "dominant_link": dominant,
        }

    @staticmethod
    def topology_summary(analysis: Dict[str, Any]) -> str:
        """Return a human-readable topology characteristic string."""
        deg = analysis.get("average_degree", 0)
        dom = analysis.get("dominant_link", "N/A")
        n = analysis.get("node_count", 0)

        parts = []
        if deg > 6:
            parts.append("High connectivity")
        elif deg > 2:
            parts.append("Medium connectivity")
        else:
            parts.append("Low diameter")

        if dom == "RoCE":
            parts.append("RoCE-dominated")
        elif dom == "HCCS":
            parts.append("HCCS-dominated")

        if n <= 8:
            parts.append("Single-node structure")
        elif n <= 64:
            parts.append("Hierarchical structure")
        else:
            parts.append("Large-scale distributed structure")

        return ", ".join(parts) if parts else "Unknown topology characteristics"

    @staticmethod
    def detect_topology_change(
        old_analysis: Dict[str, Any],
        new_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare two topology snapshots.

        Returns
        -------
        dict  {"changed": bool, "reason": str}
        """
        if old_analysis["node_count"] != new_analysis["node_count"]:
            return {
                "changed": True,
                "reason": (
                    f"Node count changed: "
                    f"{old_analysis['node_count']} → {new_analysis['node_count']}"
                ),
            }
        if old_analysis["edge_count"] != new_analysis["edge_count"]:
            return {
                "changed": True,
                "reason": "Edge count changed — links added or removed.",
            }
        if old_analysis["dominant_link"] != new_analysis["dominant_link"]:
            return {
                "changed": True,
                "reason": (
                    f"Dominant link type changed: "
                    f"{old_analysis['dominant_link']} → {new_analysis['dominant_link']}"
                ),
            }
        return {"changed": False, "reason": "No significant change detected."}

    @staticmethod
    def hardware_summary(node_profiles):
        """Aggregate hardware resource info across all node profiles."""
        if not node_profiles:
            return {}
        total_hbm = sum(np.hbm_capacity_gb for np in node_profiles)
        total_ub = sum(np.ub_capacity_mb for np in node_profiles)
        numa = node_profiles[0].numa_domains if node_profiles else 0
        devices = sum(np.num_devices for np in node_profiles)
        from hardware.affinity_engine import AffinityEngine
        loc = AffinityEngine.evaluate_locality(node_profiles[0])
        return {
            "num_nodes": len(node_profiles),
            "total_devices": devices,
            "numa_domains": numa,
            "hbm_capacity_gb": total_hbm,
            "ub_capacity_mb": total_ub,
            "locality_score": loc["locality_score"],
        }
