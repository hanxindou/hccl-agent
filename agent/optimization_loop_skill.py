"""Optimization Loop Skill — iterate Plan→Execute→Reflect→Optimize until convergence."""

from typing import Any, Dict, List


class OptimizationLoopSkill:
    """Run multiple optimization iterations and track improvement."""

    DEFAULT_MAX_ITERATIONS: int = 5
    IMPROVEMENT_THRESHOLD: float = 2.0   # minimum % score gain per iteration
    STAGNATION_LIMIT: int = 2            # consecutive rounds without gain

    @staticmethod
    def run_until_converged(
        initial_plan: Dict[str, Any],
        cluster_config: Dict[str, Any],
        max_iterations: int | None = None,
        evaluate_fn: Any = None,
    ) -> Dict[str, Any]:
        """Iteratively refine algorithm and parameters.

        Parameters
        ----------
        initial_plan : dict  — "algorithm", "score", "topology", "nodes"
        cluster_config : dict  — cluster parameters
        max_iterations : int or None
        evaluate_fn : callable(plan) → {"score": float, ...}
            External evaluation function (e.g. Simulator).

        Returns
        -------
        dict  iterations, best_score, improvement_percent, converged.
        """
        if max_iterations is None:
            max_iterations = OptimizationLoopSkill.DEFAULT_MAX_ITERATIONS

        iterations: List[Dict[str, Any]] = []
        current = dict(initial_plan)
        best_score = initial_plan.get("score", 0.0)
        stable_rounds = 0

        for i in range(max_iterations):
            # Evaluate current configuration.
            if evaluate_fn:
                result = evaluate_fn(current)
            else:
                result = {"score": current.get("score", 0.0),
                          "latency": current.get("latency", 0.0),
                          "bandwidth": current.get("bandwidth", 0.0)}

            score = result.get("score", 0.0)
            improved = score > best_score * (1.0 + OptimizationLoopSkill.IMPROVEMENT_THRESHOLD / 100.0)
            if improved:
                best_score = score
                stable_rounds = 0
            else:
                stable_rounds += 1

            iterations.append({
                "iteration": i + 1,
                "algorithm": current.get("algorithm", "N/A"),
                "score": score,
                "latency": result.get("latency", 0),
                "bandwidth": result.get("bandwidth", 0),
                "changes": current.get("changes", "initial"),
            })

            # Check convergence.
            if stable_rounds >= OptimizationLoopSkill.STAGNATION_LIMIT:
                break

            # Prepare next iteration: apply a simulated improvement.
            # Shift to the next-best algorithm or adjust tuning params.
            alt = current.get("alternative")
            if alt:
                current["algorithm"] = alt
                current["changes"] = f"switched to {alt}"
            else:
                # Tune parameters.
                current["changes"] = "parameter tuning"
                current["score"] = min(100.0, current.get("score", 0.0) * 1.01)

        initial = initial_plan.get("score", 1.0)
        improvement = ((best_score - initial) / initial * 100.0) if initial > 0 else 0.0

        return {
            "iterations": iterations,
            "best_score": round(best_score, 2),
            "improvement_percent": round(improvement, 1),
            "converged": stable_rounds >= OptimizationLoopSkill.STAGNATION_LIMIT,
            "total_iterations": len(iterations),
        }
