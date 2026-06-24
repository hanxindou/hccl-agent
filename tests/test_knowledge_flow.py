"""Tests: Knowledge integration in Agent."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.hccl_agent import HCCLAgent


class TestKnowledgeFlow(unittest.TestCase):

    def test_agent_output_contains_knowledge_context(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        self.assertIn("knowledge_context", output)

    def test_agent_output_contains_best_practice(self):
        agent = HCCLAgent()
        # First run populates knowledge base.
        agent.run(nodes=8, message_size=128, primitive="AllReduce")
        # Second run should find the first run's case.
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        kc = output["knowledge_context"]
        self.assertGreater(kc["count"], 0)


if __name__ == "__main__":
    unittest.main()
