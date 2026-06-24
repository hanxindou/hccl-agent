"""End-to-end: Optimization Proposal integration."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.hccl_agent import HCCLAgent


class TestOptimizationFlow(unittest.TestCase):

    def test_agent_output_contains_proposal(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        self.assertIn("optimization_proposal", output)
        proposal = output["optimization_proposal"]
        self.assertIn("confidence", proposal)
        self.assertIn("migration_plan", proposal)
        self.assertGreater(proposal["confidence"], 0)

    def test_agent_output_contains_hardware_analysis(self):
        agent = HCCLAgent()
        output = agent.run(nodes=8, message_size=128, primitive="AllReduce")
        self.assertIn("hardware_analysis", output)


if __name__ == "__main__":
    unittest.main()
