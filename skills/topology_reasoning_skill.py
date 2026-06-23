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
