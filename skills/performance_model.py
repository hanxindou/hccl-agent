"""Normalised performance scoring model (0–100 range).

Replaces the old ``bandwidth * 0.7 - latency * 0.3`` formula which
had no fixed range and favoured low-step-count algorithms regardless
of real-world constraints.
"""


class PerformanceModel:

    # Weighting of bandwidth vs latency in the final score.
    BANDWIDTH_WEIGHT = 0.4
    LATENCY_WEIGHT   = 0.6

    # ms of latency that reduces the latency sub-score by 1 point.
    # 0 ms → 100,  0.1 ms → 0 (with penalty = 1000).
    LATENCY_PENALTY = 1000.0

    def calculate_score(self, latency_ms, bandwidth_gb_s,
                        theoretical_max_bandwidth_gb_s=None):
        """Return a normalised score in [0, 100].

        Parameters
        ----------
        latency_ms : float
            Estimated end-to-end latency in milliseconds.
        bandwidth_gb_s : float
            Estimated effective bandwidth in GB/s.
        theoretical_max_bandwidth_gb_s : float or None
            Ceiling for bandwidth scoring.  When None the effective
            bandwidth itself is used as the ceiling, which means the
            bandwidth sub-score is always 100.  Callers should pass
            the per-link bandwidth (in GB/s) to get meaningful
            differentiation.

        Returns
        -------
        float — score in [0, 100], rounded to 2 decimal places.
        """
        # ---- bandwidth sub-score (0–100) ----
        ceiling = (theoretical_max_bandwidth_gb_s
                   if theoretical_max_bandwidth_gb_s is not None
                   else bandwidth_gb_s)
        if ceiling > 0:
            bw_score = min(bandwidth_gb_s / ceiling * 100.0, 100.0)
        else:
            bw_score = 0.0

        # ---- latency sub-score (0–100) ----
        lat_penalty = latency_ms * self.LATENCY_PENALTY
        lat_score = max(0.0, 100.0 - lat_penalty)

        # ---- composite ----
        score = (bw_score * self.BANDWIDTH_WEIGHT +
                 lat_score * self.LATENCY_WEIGHT)

        return round(score, 2)
