"""Tests for the normalised PerformanceModel (0–100 scoring)."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from skills.performance_model import PerformanceModel


class TestPerformanceModel(unittest.TestCase):

    def setUp(self):
        self.model = PerformanceModel()

    # ---- score range ----

    def test_score_in_range_zero_to_100(self):
        """All scores must fall in [0, 100]."""
        cases = [
            (0.001, 12.5, 12.5),      # best case
            (0.028, 11.88, 12.5),     # Ring 8 nodes
            (0.5, 10.0, 12.5),        # medium latency
            (2.0, 5.0, 12.5),         # high latency
            (30.0, 2.0, 12.5),        # worst case
            (0.001, 12.5, 12.5),      # perfect
        ]
        for lat, bw, ceiling in cases:
            score = self.model.calculate_score(lat, bw, ceiling)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)

    def test_perfect_conditions_give_high_score(self):
        """Zero latency + full bandwidth → near 100."""
        score = self.model.calculate_score(0.0, 12.5, 12.5)
        self.assertGreaterEqual(score, 99.0)

    def test_high_latency_gives_lower_score(self):
        """2ms latency → lower than 0.01ms (smooth decay, no hard cutoff)."""
        s_low = self.model.calculate_score(0.01, 12.5, 12.5)
        s_high = self.model.calculate_score(2.0, 12.5, 12.5)
        self.assertGreater(s_low, s_high)
        self.assertGreater(s_high, 0.0)

    # ---- bandwidth differentiation ----

    def test_lower_bandwidth_gives_lower_score(self):
        s1 = self.model.calculate_score(0.01, 12.5, 12.5)
        s2 = self.model.calculate_score(0.01, 6.25, 12.5)
        self.assertGreater(s1, s2)

    # ---- latency differentiation ----

    def test_higher_latency_gives_lower_score(self):
        s1 = self.model.calculate_score(0.01, 12.5, 12.5)
        s2 = self.model.calculate_score(0.05, 12.5, 12.5)
        self.assertGreater(s1, s2)

    # ---- edge cases ----

    def test_zero_ceiling(self):
        score = self.model.calculate_score(0.01, 10.0, 0.0)
        self.assertGreaterEqual(score, 0.0)

    def test_no_ceiling_passed(self):
        """Without ceiling, bandwidth sub-score is always 100."""
        score = self.model.calculate_score(0.01, 5.0)
        # bw_score = 100, lat_score ≈ 99.5
        self.assertGreater(score, 90.0)

    def test_score_is_float_rounded(self):
        score = self.model.calculate_score(0.033, 11.25, 12.5)
        self.assertIsInstance(score, float)


if __name__ == "__main__":
    unittest.main()
