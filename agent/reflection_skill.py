"""Reflection Skill — post-execution analysis and self-assessment.

Evaluates whether the chosen algorithm met expectations and decides
if a re-plan is needed.
"""


class ReflectionSkill:

    def reflect(self, predicted_score, actual_execution_time_ms,
                algorithm, candidate_scores=None):
        """Analyse execution results against predictions.

        Parameters
        ----------
        predicted_score : float
        actual_execution_time_ms : float
        algorithm : str
        candidate_scores : list[dict] or None
            Optional — enables decision quality analysis.

        Returns
        -------
        dict
        """
        t = actual_execution_time_ms

        # ---- status classification ----
        if t < 1.0:
            status = "good"
            need_replan = False
            base_msg = (
                f"{algorithm} completed in {t:.4f} ms. "
                "Performance is excellent."
            )
        elif t < 5.0:
            status = "warning"
            need_replan = False
            base_msg = (
                f"{algorithm} completed in {t:.4f} ms. "
                "Performance is acceptable but could be improved."
            )
        else:
            status = "poor"
            need_replan = True
            base_msg = (
                f"{algorithm} took {t:.4f} ms — above the 5 ms "
                "threshold.  Consider switching to a lower-latency "
                "algorithm."
            )

        # ---- prediction deviation (heuristic) ----
        # Compare execution time against a proxy "predicted time"
        # derived from the score: higher score → lower expected time.
        # Use a simple model: expected_time ≈ max(0.01, (100-score)/500)
        expected_ms = max(0.01, (100.0 - predicted_score) / 500.0)
        deviation = False
        if expected_ms > 0:
            error_ratio = abs(t - expected_ms) / expected_ms
            if error_ratio > 0.5:
                deviation = True
                base_msg += (
                    f" Prediction deviation detected "
                    f"(expected ~{expected_ms:.4f} ms, "
                    f"got {t:.4f} ms)."
                )

        # ---- decision quality analysis (optional) ----
        decision_quality = None
        if candidate_scores:
            best_alt = max(
                (c for c in candidate_scores if c["algorithm"] != algorithm),
                key=lambda c: c["score"], default=None,
            )
            if best_alt:
                gap = best_alt["score"] - predicted_score
                decision_quality = {
                    "selected_algorithm": algorithm,
                    "selected_score": predicted_score,
                    "best_alternative": best_alt["algorithm"],
                    "best_alternative_score": best_alt["score"],
                    "score_gap": round(gap, 2),
                    "recommendation": (
                        "Selection is suboptimal — consider replanning."
                        if gap > 5 else "Selection is near-optimal."
                    ),
                }

        return {
            "status": status,
            "message": base_msg,
            "need_replan": need_replan,
            "prediction_deviation": deviation,
            "decision_quality": decision_quality,
        }
