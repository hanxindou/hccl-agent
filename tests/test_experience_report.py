"""Tests: experience report in agent output."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.hccl_agent import HCCLAgent


class TestExperienceReport(unittest.TestCase):

    def test_agent_output_contains_experience_learning(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        self.assertIn("experience_learning", output)


if __name__ == "__main__":
    unittest.main()
