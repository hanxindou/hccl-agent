"""Tests: optimization history in Agent output."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.hccl_agent import HCCLAgent


class TestOptimizationHistory(unittest.TestCase):

    def test_agent_output_contains_optimization_history(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        self.assertIn("optimization_history", output)
        hist = output["optimization_history"]
        self.assertIn("iterations", hist)
        self.assertGreaterEqual(hist["total_iterations"], 1)

    def test_agent_output_contains_convergence_analysis(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        conv = output["convergence_analysis"]
        self.assertIn("trend", conv)
        self.assertIn("best_iteration", conv)


if __name__ == "__main__":
    unittest.main()
