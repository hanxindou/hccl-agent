"""Experience Learning Skill — similarity search, aggregation,
recommendation, and confidence from historical experience."""

from typing import Any, Dict, List, Optional, Tuple


class ExperienceLearningSkill:
    """Learn from historical runs to inform future decisions."""

    def __init__(self, experience_store: Any = None) -> None:
        self.store = experience_store

    def set_store(self, store: Any) -> None:
        self.store = store

    # ------------------------------------------------------------------
    # Similarity search
    # ------------------------------------------------------------------

    def find_similar(
        self,
        topology: str,
        primitive: str,
        nodes: int,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return top-K historically similar runs."""
        if self.store is None:
            return []
        all_records = self.store.load_all()
        # Filter by primitive exactly, topology loosely.
        filtered = [
            r for r in all_records
            if r.get("primitive") == primitive
        ]
        if not filtered:
            return []
        # Score by node-count proximity (±20%).
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for r in filtered:
            rn = r.get("nodes", 0)
            if rn > 0:
                proximity = abs(nodes - rn) / max(nodes, rn)
            else:
                proximity = 1.0
            scored.append((proximity, r))
        scored.sort(key=lambda x: x[0])
        return [r for _, r in scored[:top_k]]

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def aggregate(
        records: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:
        """Group records by algorithm and compute per-algo stats."""
        groups: Dict[str, Dict[str, float]] = {}
        for r in records:
            algo = r.get("algorithm", "unknown")
            if algo not in groups:
                groups[algo] = {"total_score": 0.0, "total_latency": 0.0,
                                "runs": 0}
            g = groups[algo]
            g["total_score"] += r.get("score", 0.0)
            g["total_latency"] += r.get("latency", 0.0) if "latency" in r else 0.0
            g["runs"] += 1

        stats: Dict[str, Dict[str, float]] = {}
        for algo, g in groups.items():
            n = g["runs"]
            stats[algo] = {
                "avg_score": round(g["total_score"] / n, 2),
                "avg_latency": round(g["total_latency"] / n, 4) if g["total_latency"] > 0 else 0.0,
                "runs": int(n),
            }
        return stats

    # ------------------------------------------------------------------
    # Recommendation
    # ------------------------------------------------------------------

    @staticmethod
    def recommend_algorithm(
        stats: Dict[str, Dict[str, float]],
    ) -> Dict[str, Any]:
        """Recommend the best algorithm based on historical stats."""
        if not stats:
            return {
                "recommended_algorithm": "N/A",
                "confidence": 0.0,
                "historical_runs": 0,
                "reason": "No historical data available.",
            }

        # Score: avg_score weighted by log(runs) to favor both quality and quantity.
        import math
        best_algo = max(
            stats,
            key=lambda a: stats[a]["avg_score"] * math.log(stats[a]["runs"] + 1),
        )
        best = stats[best_algo]
        total_runs = sum(s["runs"] for s in stats.values())

        # Confidence: higher with more runs and larger score gap.
        second_best = sorted(
            [(a, s["avg_score"]) for a, s in stats.items() if a != best_algo],
            key=lambda x: x[1], reverse=True,
        )
        gap = best["avg_score"] - second_best[0][1] if second_best else 0.0
        run_factor = min(best["runs"] / 10.0, 1.0)
        confidence = round(min(0.5 + gap / 30.0 + run_factor * 0.3, 1.0), 2)

        return {
            "recommended_algorithm": best_algo,
            "confidence": confidence,
            "historical_runs": total_runs,
            "reason": (
                f"{best_algo} has the highest historical avg score "
                f"({best['avg_score']:.1f}) over {best['runs']} runs."
            ),
        }

    # ------------------------------------------------------------------
    # Experience bonus for algorithm scoring
    # ------------------------------------------------------------------

    @staticmethod
    def compute_experience_bonus(
        algo: str,
        stats: Dict[str, Dict[str, float]],
        recommendation: Dict[str, Any],
    ) -> float:
        """Return a small bonus/penalty for algorithm selection scoring.

        +3 if algo matches the recommendation,
        -2 if algo performs poorly historically,
        0 otherwise.
        """
        if not stats or algo not in stats:
            return 0.0

        rec_algo = recommendation.get("recommended_algorithm", "")
        if algo == rec_algo:
            return 3.0

        # Penalise algorithms that are far below the best.
        best_avg = max(s["avg_score"] for s in stats.values())
        algo_avg = stats[algo]["avg_score"]
        if best_avg - algo_avg > 10:
            return -2.0

        return 0.0
