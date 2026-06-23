"""Cost Model Engine — graph-based communication cost estimation.

Computes end-to-end latency from a CommunicationGraph by simulating
message chunking, path traversal, and contention penalties.
"""

import math
from typing import Any, Dict, List, Optional

from topology.graph_builder import CommunicationGraph, TopologyEdge


class CostModelEngine:
    """Estimate collective communication cost over a weighted graph."""

    def __init__(self) -> None:
        pass

    def estimate_allreduce_ring(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str = "Ring AllReduce",
        primitive: str = "AllReduce",
    ) -> Dict[str, Any]:
        """Ring-based AllReduce cost estimation.

        Traverses the nodes in ring order (0→1→2→...→N-1→0),
        sums per-hop edge costs, applies primitive and algorithm
        efficiency factors, then adds contention penalty.
        """
        N = graph.num_nodes
        if N <= 1:
            return self._trivial_result(algorithm_name, primitive, N)

        # Build ring path: 0→1→2→...→N-1→0→1→... (two laps).
        ring_path: List[int] = list(range(N)) + [0]

        # ---- edge traversal cost ----
        total_latency_ms = 0.0
        total_bw_gbps = float("inf")
        for i in range(len(ring_path) - 1):
            segs = graph.all_paths_segments([ring_path[i], ring_path[i + 1]])
            for seg in segs:
                chunk_gb = message_size_mb / 1000.0 / N
                hop_time = (chunk_gb / seg.bandwidth_gbps * 1000.0
                            + seg.latency_ms)
                total_latency_ms += hop_time * seg.contention_weight
                total_bw_gbps = min(total_bw_gbps, seg.bandwidth_gbps)

        # Two-phase: reduce + broadcast.
        total_latency_ms *= 2.0

        efficiency = _ALGO_EFF.get(algorithm_name, 0.90)
        effective_bw = total_bw_gbps * efficiency
        total_latency_ms /= efficiency

        # ---- contention penalty ----
        degree = len(graph.outgoing(0)) if graph.outgoing(0) else 1
        contention_penalty = total_latency_ms * (degree / max(N, 1)) * 0.1 * N

        # ---- overlap factor ----
        overlap = total_latency_ms * 0.05  # proxy for compute-comm overlap

        final_latency = total_latency_ms + contention_penalty - overlap
        final_latency = max(final_latency, 0.0001)

        return self._make_result(algorithm_name, primitive, N,
                                 final_latency, effective_bw)

    def estimate_allreduce_tree(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str = "Butterfly",
        primitive: str = "AllReduce",
    ) -> Dict[str, Any]:
        """Tree-based (log-N) estimation — approximate Butterfly/Fat-Tree."""
        N = graph.num_nodes
        if N <= 1:
            return self._trivial_result(algorithm_name, primitive, N)

        steps = int(math.ceil(math.log2(max(N, 1))))

        # Average edge cost across the graph.
        total_lat = 0.0
        total_bw = 0.0
        edge_count = max(1, len(graph.edges))
        for e in graph.edges:
            total_lat += e.latency_ms
            total_bw += e.bandwidth_gbps
        avg_lat = total_lat / edge_count
        avg_bw = total_bw / edge_count

        tree_latency = avg_lat * steps * 2  # up + down tree
        efficiency = _ALGO_EFF.get(algorithm_name, 0.88)
        effective_bw = avg_bw * efficiency

        return self._make_result(algorithm_name, primitive, N,
                                 tree_latency, effective_bw)

    def estimate_generic(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str,
        primitive: str,
    ) -> Dict[str, Any]:
        """Fallback: default to ring-based estimation."""
        return self.estimate_allreduce_ring(
            graph, message_size_mb, algorithm_name, primitive,
        )

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _trivial_result(algo: str, prim: str, N: int) -> Dict[str, Any]:
        return {
            "algorithm": algo, "primitive": prim, "nodes": N,
            "latency_ms": 0.0, "bandwidth_gbps": 0.0,
            "topology_mode": "single", "edge_count": 0,
        }

    @staticmethod
    def _make_result(
        algo: str, prim: str, N: int, lat: float, bw: float,
    ) -> Dict[str, Any]:
        return {
            "algorithm": algo, "primitive": prim, "nodes": N,
            "latency_ms": round(lat, 6),
            "bandwidth_gbps": round(bw, 2),
            "topology_mode": "graph",
            "edge_count": 0,
        }


# Efficiency factors for graph-based estimation (reuse from simulator).
_ALGO_EFF: Dict[str, float] = {
    "Ring AllReduce": 0.90,
    "Butterfly":      0.85,
    "Mesh":           0.88,
    "NHR":            0.93,
    "Fat-Tree":       0.95,
    "PairWise":       0.82,
}
