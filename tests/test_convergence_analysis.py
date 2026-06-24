"""Tests for ConvergenceAnalysisSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.convergence_analysis_skill import ConvergenceAnalysisSkill


class TestConvergenceAnalysis(unittest.TestCase):

    def test_analyze_empty(self):
        r = ConvergenceAnalysisSkill.analyze([])
        self.assertEqual(r["status"], "no_data")

    def test_improving_trend(self):
        iterations = [
            {"iteration": 1, "algorithm": "Ring", "score": 80},
            {"iteration": 2, "algorithm": "Ring", "score": 85},
        ]
        r = ConvergenceAnalysisSkill.analyze(iterations)
        self.assertEqual(r["trend"], "improving")
        self.assertEqual(r["best_iteration"], 2)

    def test_single_iteration(self):
        iterations = [{"iteration": 1, "algorithm": "NHR", "score": 90}]
        r = ConvergenceAnalysisSkill.analyze(iterations)
        self.assertEqual(r["trend"], "single iteration")

    def test_stagnation_detected(self):
        iterations = [
            {"iteration": 1, "algorithm": "Mesh", "score": 75},
            {"iteration": 2, "algorithm": "Mesh", "score": 75},
        ]
        r = ConvergenceAnalysisSkill.analyze(iterations)
        self.assertTrue(r["stagnation_detected"])


if __name__ == "__main__":
    unittest.main()
