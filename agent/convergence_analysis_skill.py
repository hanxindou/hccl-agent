"""Convergence Analysis Skill — analyse optimization loop results."""

from typing import Any, Dict, List


class ConvergenceAnalysisSkill:
    """Diagnose convergence behaviour."""

    @staticmethod
    def analyze(iterations: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not iterations:
            return {"status": "no_data", "trend": "N/A", "best_iteration": 0}

        scores = [it["score"] for it in iterations]
        best_idx = max(range(len(scores)), key=lambda i: scores[i])

        # Trend analysis.
        if len(scores) >= 2:
            if scores[-1] > scores[0]:
                trend = "improving"
            elif scores[-1] == scores[0]:
                trend = "stable"
            else:
                trend = "declining"
        else:
            trend = "single iteration"

        best = iterations[best_idx]

        return {
            "status": "converged" if len(iterations) < 5 else "max_iterations",
            "trend": trend,
            "best_iteration": best_idx + 1,
            "best_score": best["score"],
            "best_algorithm": best["algorithm"],
            "iterations_run": len(iterations),
            "stagnation_detected": (
                len(scores) >= 2 and scores[-1] <= scores[-2]
            ),
        }
