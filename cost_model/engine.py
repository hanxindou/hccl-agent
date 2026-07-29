"""Cost Model Engine — graph-based analytical communication estimation.

The D1 model is intentionally explicit and traceable:

latency = startup_cost
        + communication_steps * per_step_latency
        + transferred_bytes / effective_bandwidth
        + contention_penalty

It is a CPU-side analytical model, not real HCCL/CANN performance.
"""

import math
from typing import Any, Dict, List, Optional

from topology.graph_builder import CommunicationGraph, TopologyEdge


class CostModelEngine:
    """Estimate collective communication cost over a weighted graph."""

    STARTUP_COST_MS = 0.003

    PARAMETER_SOURCES: Dict[str, Dict[str, Any]] = {
        "startup_cost_ms": {
            "unit": "ms",
            "default": STARTUP_COST_MS,
            "source": "project analytical default",
            "applies_to": "all topologies",
            "calibrated": False,
            "confidence": "low",
        },
        "bandwidth_gbps": {
            "unit": "Gbps",
            "default": "HardwareProfile link_types",
            "source": "hardware/profile.py relative tiers",
            "applies_to": "HCCS/RoCE/PCIe",
            "calibrated": False,
            "confidence": "medium",
        },
        "latency_ms": {
            "unit": "ms",
            "default": "HardwareProfile link_types",
            "source": "hardware/profile.py relative tiers",
            "applies_to": "HCCS/RoCE/PCIe",
            "calibrated": False,
            "confidence": "medium",
        },
        "contention_penalty": {
            "unit": "ms",
            "default": "derived from node scale, link mix, algorithm",
            "source": "D1 analytical model",
            "applies_to": "all topologies",
            "calibrated": False,
            "confidence": "low",
        },
    }

    def __init__(self) -> None:
        pass

    def estimate_allreduce_ring(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str = "Ring AllReduce",
        primitive: str = "AllReduce",
    ) -> Dict[str, Any]:
        """Ring-style cost estimation for AllReduce/NHR/ReduceScatter."""
        return self.estimate_collective(
            graph, message_size_mb, algorithm_name, primitive,
        )

    def estimate_allreduce_tree(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str = "Butterfly",
        primitive: str = "AllReduce",
    ) -> Dict[str, Any]:
        """Tree-style cost estimation for Butterfly/Fat-Tree/Mesh."""
        return self.estimate_collective(
            graph, message_size_mb, algorithm_name, primitive,
        )

    def estimate_generic(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str,
        primitive: str,
    ) -> Dict[str, Any]:
        """Fallback: default to ring-based estimation."""
        return self.estimate_collective(
            graph, message_size_mb, algorithm_name, primitive,
        )

    def estimate_collective(
        self,
        graph: CommunicationGraph,
        message_size_mb: float,
        algorithm_name: str,
        primitive: str,
    ) -> Dict[str, Any]:
        """Estimate collective latency/bandwidth using the D1 formula."""
        N = graph.num_nodes
        if N <= 1:
            return self._trivial_result(algorithm_name, primitive, N)

        message_size_mb = max(float(message_size_mb), 0.0)
        stats = self._graph_stats(graph)
        steps = self._communication_steps(N, algorithm_name, primitive)
        transfer_multiplier = self._transfer_multiplier(N, primitive, algorithm_name)
        transferred_bytes = message_size_mb * 1024.0 * 1024.0 * transfer_multiplier

        efficiency = _ALGO_EFF.get(algorithm_name, 0.85)
        contention_factor = self._contention_factor(N, algorithm_name, stats)
        effective_bw_gbps = max(
            stats["bottleneck_bandwidth_gbps"] * efficiency / contention_factor,
            0.001,
        )
        bandwidth_time_ms = (
            transferred_bytes * 8.0 / (effective_bw_gbps * 1_000_000_000.0) * 1000.0
        )

        per_step_latency = stats["weighted_latency_ms"]
        step_latency_ms = steps * per_step_latency
        contention_penalty_ms = (
            (step_latency_ms + bandwidth_time_ms) *
            (contention_factor - 1.0) * 0.20
        )
        final_latency = (
            self.STARTUP_COST_MS +
            step_latency_ms +
            bandwidth_time_ms +
            contention_penalty_ms
        )
        final_latency = max(final_latency, 0.0001)

        return self._make_result(
            algorithm_name, primitive, N, final_latency, effective_bw_gbps,
            edge_count=len(graph.edges),
            link_types=stats["link_types"],
            communication_steps=steps,
            transferred_bytes=int(transferred_bytes),
            contention_penalty_ms=contention_penalty_ms,
            per_step_latency_ms=per_step_latency,
            parameter_sources=self.PARAMETER_SOURCES,
            assumptions=[
                "CPU_SIMULATED / ANALYTICAL_MODEL only",
                "topology/graph_builder.py CommunicationGraph is the main topology model",
                "bandwidth and latency come from HardwareProfile relative tiers",
                "no CANN/HCCL hardware calibration has been applied",
            ],
        )

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _trivial_result(algo: str, prim: str, N: int) -> Dict[str, Any]:
        return {
            "algorithm": algo, "primitive": prim, "nodes": N,
            "latency_ms": 0.0, "bandwidth_gbps": 0.0,
            "topology_mode": "graph", "edge_count": 0,
            "model_type": "ANALYTICAL_MODEL",
            "communication_steps": 0,
            "transferred_bytes": 0,
            "contention_penalty_ms": 0.0,
            "link_types": [],
            "parameter_sources": CostModelEngine.PARAMETER_SOURCES,
        }

    @staticmethod
    def _make_result(
        algo: str, prim: str, N: int, lat: float, bw: float,
        edge_count: int = 0,
        link_types: Optional[List[str]] = None,
        communication_steps: float = 0.0,
        transferred_bytes: int = 0,
        contention_penalty_ms: float = 0.0,
        per_step_latency_ms: float = 0.0,
        parameter_sources: Optional[Dict[str, Dict[str, Any]]] = None,
        assumptions: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return {
            "algorithm": algo, "primitive": prim, "nodes": N,
            "latency_ms": round(lat, 6),
            "bandwidth_gbps": round(bw, 2),
            "topology_mode": "graph",
            "edge_count": edge_count,
            "model_type": "ANALYTICAL_MODEL",
            "communication_steps": round(communication_steps, 4),
            "transferred_bytes": transferred_bytes,
            "contention_penalty_ms": round(contention_penalty_ms, 6),
            "per_step_latency_ms": round(per_step_latency_ms, 6),
            "link_types": link_types or [],
            "parameter_sources": parameter_sources or CostModelEngine.PARAMETER_SOURCES,
            "model_assumptions": assumptions or [],
        }

    @staticmethod
    def _graph_stats(graph: CommunicationGraph) -> Dict[str, Any]:
        if not graph.edges:
            return {
                "weighted_latency_ms": 0.0,
                "bottleneck_bandwidth_gbps": 0.0,
                "avg_bandwidth_gbps": 0.0,
                "avg_contention": 1.0,
                "link_types": [],
            }

        total_weight = 0.0
        weighted_lat = 0.0
        bottleneck = float("inf")
        total_bw = 0.0
        total_contention = 0.0
        link_types = sorted({e.link_type for e in graph.edges})
        for edge in graph.edges:
            weight = edge.contention_weight
            total_weight += weight
            weighted_lat += edge.latency_ms * weight
            bottleneck = min(bottleneck, edge.bandwidth_gbps)
            total_bw += edge.bandwidth_gbps
            total_contention += edge.contention_weight

        count = max(1, len(graph.edges))
        return {
            "weighted_latency_ms": weighted_lat / max(total_weight, 1.0),
            "bottleneck_bandwidth_gbps": bottleneck,
            "avg_bandwidth_gbps": total_bw / count,
            "avg_contention": total_contention / count,
            "link_types": link_types,
        }

    @staticmethod
    def _communication_steps(N: int, algorithm_name: str, primitive: str) -> float:
        if primitive == "AllGather":
            primitive_factor = 1.0
        elif primitive == "ReduceScatter":
            primitive_factor = 1.0
        else:
            primitive_factor = 2.0

        if algorithm_name == "Ring AllReduce":
            return max(1.0, primitive_factor * (N - 1))
        if algorithm_name == "Butterfly":
            return max(1.0, primitive_factor * math.ceil(math.log2(max(N, 1))))
        if algorithm_name == "Mesh":
            return 1.0 + max(0, N - 1) * 0.15
        if algorithm_name == "NHR":
            groups = math.ceil(N / 8.0)
            return max(1.0, (8 - 1) + 2 * max(0, groups - 1))
        if algorithm_name == "Fat-Tree":
            return max(1.0, primitive_factor * math.ceil(math.log2(max(N, 1))))
        if algorithm_name == "PairWise":
            return max(1.0, N - 1)
        return max(1.0, N)

    @staticmethod
    def _transfer_multiplier(N: int, primitive: str, algorithm_name: str) -> float:
        if N <= 1:
            return 0.0
        if primitive == "AllGather":
            return (N - 1) / N
        if primitive == "ReduceScatter":
            return (N - 1) / N
        if algorithm_name == "Mesh":
            return N - 1
        return 2.0 * (N - 1) / N

    @staticmethod
    def _contention_factor(
        N: int, algorithm_name: str, stats: Dict[str, Any],
    ) -> float:
        link_mix_penalty = 1.0 + max(0, len(stats["link_types"]) - 1) * 0.10
        scale_penalty = 1.0 + math.log2(max(N, 2)) * 0.03
        algo_penalty = {
            "Mesh": 1.0 + max(0, N - 1) * 0.12,
            "Fat-Tree": 1.0 + math.log2(max(N, 2)) * 0.04,
            "NHR": 1.0 + math.log2(max(N, 2)) * 0.025,
        }.get(algorithm_name, 1.0)
        return max(1.0, stats["avg_contention"] * link_mix_penalty *
                   scale_penalty * algo_penalty)


# Efficiency factors for graph-based estimation (reuse from simulator).
_ALGO_EFF: Dict[str, float] = {
    "Ring AllReduce": 0.90,
    "Butterfly":      0.85,
    "Mesh":           0.88,
    "NHR":            0.93,
    "Fat-Tree":       0.95,
    "PairWise":       0.82,
}
