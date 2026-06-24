"""Tests: Auto-Tuning integration in Agent."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.hccl_agent import HCCLAgent


class TestAutoTuningFlow(unittest.TestCase):

    def test_agent_output_contains_auto_tuning(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        self.assertIn("auto_tuning", output)
        at = output["auto_tuning"]
        self.assertIn("best_config", at)
        self.assertGreater(at["evaluated_configs"], 0)


if __name__ == "__main__":
    unittest.main()
