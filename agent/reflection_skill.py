"""Reflection Skill — post-execution analysis and self-assessment.

Evaluates whether the chosen algorithm met expectations and decides
if a re-plan is needed.
"""


class ReflectionSkill:

    def reflect(self, predicted_score, actual_execution_time_ms,
                algorithm):
        """Analyse execution results against predictions.

        Parameters
        ----------
        predicted_score : float
            Simulated performance score (0–100).
        actual_execution_time_ms : float
            Measured wall-clock time from BenchmarkSkill.
        algorithm : str
            The algorithm that was executed.

        Returns
        -------
        dict
            {"status": "good"|"warning"|"poor",
             "message": "...",
             "need_replan": bool,
             "prediction_deviation": bool}
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

        return {
            "status": status,
            "message": base_msg,
            "need_replan": need_replan,
            "prediction_deviation": deviation,
        }
