"""Calibrated performance scoring model (0–100 range, smooth decay).

Uses a smooth latency-decay curve instead of a hard cutoff so scores
degrade gracefully as latency grows.
"""

from typing import Any, Dict, Optional


class PerformanceModel:

    # Configurable weights.
    BANDWIDTH_WEIGHT: float = 0.4
    LATENCY_WEIGHT: float   = 0.6

    # Latency scale for the smooth-decay formula.
    # At latency_ms == LATENCY_SCALE the sub-score is 100 / 2 = 50.
    LATENCY_SCALE: float = 30.0

    # ---- public API (backward-compatible) ----

    def calculate_score(
        self,
        latency_ms: float,
        bandwidth_gb_s: float,
        theoretical_max_bandwidth_gb_s: Optional[float] = None,
    ) -> float:
        """Return a normalised score in [0, 100]."""
        return self.calculate_score_breakdown(
            latency_ms, bandwidth_gb_s, theoretical_max_bandwidth_gb_s,
        )["score"]

    def calculate_score_breakdown(
        self,
        latency_ms: float,
        bandwidth_gb_s: float,
        theoretical_max_bandwidth_gb_s: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Return score with per-component breakdown.

        Returns
        -------
        dict
            score, bandwidth_score, latency_score,
            bw_weighted, lat_weighted, bandwidth_weight, latency_weight.
        """
        # ---- bandwidth sub-score (0–100) ----
        ceiling = (
            theoretical_max_bandwidth_gb_s
            if theoretical_max_bandwidth_gb_s is not None
            else bandwidth_gb_s
        )
        bw_score = (
            min(bandwidth_gb_s / ceiling * 100.0, 100.0)
            if ceiling > 0 else 0.0
        )

        # ---- latency sub-score (0–100) — smooth decay ----
        # 0 ms → 100,  LATENCY_SCALE ms → 50,  ∞ → 0
        lat_score = 100.0 / (1.0 + latency_ms / self.LATENCY_SCALE)

        # ---- weighted contributions ----
        bw_weighted = bw_score * self.BANDWIDTH_WEIGHT
        lat_weighted = lat_score * self.LATENCY_WEIGHT
        final = bw_weighted + lat_weighted

        return {
            "score":            round(final, 2),
            "bandwidth_score":  round(bw_score, 2),
            "latency_score":    round(lat_score, 2),
            "bw_weighted":      round(bw_weighted, 2),
            "lat_weighted":     round(lat_weighted, 2),
            "bandwidth_weight": self.BANDWIDTH_WEIGHT,
            "latency_weight":   self.LATENCY_WEIGHT,
        }
