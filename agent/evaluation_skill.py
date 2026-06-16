"""Evaluation Skill — grade algorithm performance and recommend actions.

Consumes a performance result dict (from the Simulator) and produces a
grade with a human-readable recommendation.
"""


class EvaluationSkill:

    # Thresholds
    EXCELLENT_THRESHOLD = 70.0
    GOOD_THRESHOLD     = 50.0
    FAIR_THRESHOLD     = 30.0

    RECOMMENDATIONS = {
        "EXCELLENT": "Current algorithm performs very well.",
        "GOOD":      "Keep current algorithm.",
        "FAIR":      "Consider trying another algorithm.",
        "POOR":      "Strongly recommend algorithm replacement.",
    }

    def evaluate(self, performance_result):
        """Grade a performance result.

        Parameters
        ----------
        performance_result : dict
            Must contain "score" (float).  May also contain "algorithm",
            "latency", "bandwidth".

        Returns
        -------
        dict
            {"grade": "GOOD", "recommendation": "Keep current algorithm."}
        """
        score = performance_result.get("score", 0.0)

        if score >= self.EXCELLENT_THRESHOLD:
            grade = "EXCELLENT"
        elif score >= self.GOOD_THRESHOLD:
            grade = "GOOD"
        elif score >= self.FAIR_THRESHOLD:
            grade = "FAIR"
        else:
            grade = "POOR"

        return {
            "grade": grade,
            "recommendation": self.RECOMMENDATIONS[grade],
        }
