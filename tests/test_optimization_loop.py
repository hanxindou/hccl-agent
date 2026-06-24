"""Tests for OptimizationLoopSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.optimization_loop_skill import OptimizationLoopSkill


class TestOptimizationLoop(unittest.TestCase):

    def test_converges_within_max_iterations(self):
        r = OptimizationLoopSkill.run_until_converged(
            {"algorithm": "Ring AllReduce", "score": 80, "topology": "Ring", "nodes": 8},
            {}, max_iterations=5,
        )
        self.assertLessEqual(r["total_iterations"], 5)
        self.assertIn("best_score", r)

    def test_improvement_percent_non_negative(self):
        r = OptimizationLoopSkill.run_until_converged(
            {"algorithm": "NHR", "score": 70}, {}, max_iterations=3,
        )
        self.assertGreaterEqual(r["improvement_percent"], 0.0)

    def test_iterations_recorded(self):
        r = OptimizationLoopSkill.run_until_converged(
            {"algorithm": "Mesh", "score": 60}, {}, max_iterations=3,
        )
        self.assertEqual(len(r["iterations"]), r["total_iterations"])

    def test_deterministic(self):
        r1 = OptimizationLoopSkill.run_until_converged(
            {"algorithm": "Butterfly", "score": 85}, {}, max_iterations=3,
        )
        r2 = OptimizationLoopSkill.run_until_converged(
            {"algorithm": "Butterfly", "score": 85}, {}, max_iterations=3,
        )
        self.assertEqual(r1["best_score"], r2["best_score"])


if __name__ == "__main__":
    unittest.main()
