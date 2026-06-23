"""Decision Validation Skill — verify that the selected algorithm is optimal."""

from typing import Any, Dict, List


class DecisionValidationSkill:
    """Check whether the Agent's chosen algorithm is truly the best."""

    @staticmethod
    def validate(
        selected_algorithm: str,
        candidate_scores: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compare *selected_algorithm* against all candidates.

        Parameters
        ----------
        selected_algorithm : str
        candidate_scores : list[dict]
            Each has "algorithm" and "score".

        Returns
        -------
        dict  with selected, best_score, is_optimal, gap, confidence.
        """
        if not candidate_scores:
            return {
                "selected": selected_algorithm,
                "best_score": 0.0,
                "is_optimal": True,
                "gap": 0.0,
                "confidence": "N/A",
            }

        ranked = sorted(candidate_scores, key=lambda x: x["score"], reverse=True)
        best = ranked[0]
        selected_score = next(
            (c["score"] for c in candidate_scores
             if c["algorithm"] == selected_algorithm),
            best["score"],
        )

        gap = best["score"] - selected_score
        is_optimal = gap < 0.01  # floating-point tolerance

        if gap > 10:
            confidence = "low confidence"
        elif gap > 5:
            confidence = "medium confidence"
        else:
            confidence = "high confidence"

        return {
            "selected": selected_algorithm,
            "best_score": best["score"],
            "best_algorithm": best["algorithm"],
            "selected_score": selected_score,
            "is_optimal": is_optimal,
            "gap": round(gap, 2),
            "confidence": confidence,
        }
