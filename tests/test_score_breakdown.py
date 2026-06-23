"""Tests for score breakdown in Simulator."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.performance_model import PerformanceModel


class TestScoreBreakdown(unittest.TestCase):

    def test_breakdown_components_sum_to_score(self):
        model = PerformanceModel()
        bd = model.calculate_score_breakdown(2.0, 10.0, 12.0)
        total = bd["bw_weighted"] + bd["lat_weighted"]
        self.assertAlmostEqual(bd["score"], total, places=1)

    def test_breakdown_score_matches_calculate_score(self):
        model = PerformanceModel()
        bd = model.calculate_score_breakdown(1.0, 8.0, 12.0)
        s = model.calculate_score(1.0, 8.0, 12.0)
        self.assertEqual(bd["score"], s)

    def test_weights_sum_to_one(self):
        model = PerformanceModel()
        self.assertAlmostEqual(
            model.BANDWIDTH_WEIGHT + model.LATENCY_WEIGHT, 1.0,
        )


if __name__ == "__main__":
    unittest.main()
