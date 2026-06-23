"""Algorithm Selector — topology-aware, graph-based algorithm ranking."""

from typing import Any, Dict, List

SUPPORTED_ALGORITHMS: List[str] = [
    "Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree", "PairWise",
]

_PRIMITIVE_CANDIDATES: Dict[str, List[str]] = {
    "AllReduce":     ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"],
    "AllGather":     ["Mesh", "Butterfly", "Ring AllReduce"],
    "ReduceScatter": ["Ring AllReduce", "NHR", "Fat-Tree"],
    "Broadcast":     ["Fat-Tree", "Ring AllReduce"],
}


class AlgorithmSelector:
    """Rank algorithms by graph-based simulation scores."""

    def __init__(self) -> None:
        pass

    def select_algorithm(
        self,
        primitive: str,
        topology_graph: Any,
        hardware_profile: Any,
        candidate_algorithms: List[str] | None = None,
        message_size_mb: float = 128.0,
    ) -> Dict[str, Any]:
        """Evaluate each candidate on *topology_graph*, return the best.

        Parameters
        ----------
        primitive : str
            AllReduce / AllGather / ReduceScatter / Broadcast.
        topology_graph : CommunicationGraph
        hardware_profile : HardwareProfile
        candidate_algorithms : list[str] or None
            If None, uses the default candidate set for *primitive*.
        message_size_mb : float

        Returns
        -------
        dict
            {"algorithm": "...", "score": ..., "reason": "...",
             "candidates": [...], "scores": {...}}
        """
        if candidate_algorithms is None:
            candidate_algorithms = _PRIMITIVE_CANDIDATES.get(
                primitive, ["Ring AllReduce"],
            )

        from simulator.simulator import Simulator
        sim = Simulator()

        scores: Dict[str, float] = {}
        details: List[Dict[str, Any]] = []

        for algo in candidate_algorithms:
            r = sim.simulate_with_graph(
                topology_graph, primitive, algo, message_size_mb,
            )
            s = r["score"]
            scores[algo] = s
            details.append({
                "algorithm": algo,
                "score": s,
                "latency": r["latency"],
                "bandwidth": r["bandwidth"],
            })

        # Sort by score descending.
        details.sort(key=lambda x: x["score"], reverse=True)
        best = details[0]

        return {
            "algorithm": best["algorithm"],
            "score": best["score"],
            "reason": (
                f"Selected {best['algorithm']} — "
                f"score={best['score']:.1f}, "
                f"latency={best['latency']:.4f}ms, "
                f"bandwidth={best['bandwidth']:.2f}GB/s. "
                f"Compared {len(details)} candidates on graph topology."
            ),
            "candidates": details,
            "scores": scores,
        }
