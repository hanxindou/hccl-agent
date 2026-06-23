"""Tests for calibrated PerformanceModel — smooth decay + breakdown."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.performance_model import PerformanceModel


class TestPerformanceCalibration(unittest.TestCase):

    def setUp(self):
        self.model = PerformanceModel()

    def test_smooth_decay_no_hard_cutoff(self):
        """Latency 100ms should give score > 0 (no sudden zero)."""
        s = self.model.calculate_score(100.0, 12.0, 12.0)
        self.assertGreater(s, 0.0)

    def test_monotonic_decreasing_latency(self):
        """Higher latency → lower score."""
        s1 = self.model.calculate_score(0.1, 12.0, 12.0)
        s2 = self.model.calculate_score(10.0, 12.0, 12.0)
        s3 = self.model.calculate_score(50.0, 12.0, 12.0)
        self.assertGreater(s1, s2)
        self.assertGreater(s2, s3)

    def test_score_in_range(self):
        for lat in [0.001, 0.1, 1.0, 10.0, 50.0, 100.0]:
            s = self.model.calculate_score(lat, 10.0, 12.0)
            self.assertGreaterEqual(s, 0.0)
            self.assertLessEqual(s, 100.0)

    def test_breakdown_has_all_keys(self):
        bd = self.model.calculate_score_breakdown(0.5, 10.0, 12.0)
        for k in ("score", "bandwidth_score", "latency_score",
                  "bw_weighted", "lat_weighted"):
            self.assertIn(k, bd)

    def test_backward_compatible_calculate_score(self):
        s = self.model.calculate_score(0.5, 10.0, 12.0)
        self.assertIsInstance(s, float)

    def test_latency_weight_configured(self):
        m = PerformanceModel()
        m.LATENCY_SCALE = 20.0
        s_fast = m.calculate_score(10.0, 12.0, 12.0)
        m.LATENCY_SCALE = 50.0
        s_slow = m.calculate_score(10.0, 12.0, 12.0)
        self.assertLess(s_fast, s_slow)


if __name__ == "__main__":
    unittest.main()
