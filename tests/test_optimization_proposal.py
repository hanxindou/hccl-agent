"""Tests for OptimizationProposalSkill — proposal generation."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.optimization_proposal_skill import OptimizationProposalSkill


class TestOptimizationProposal(unittest.TestCase):

    def setUp(self):
        self.skill = OptimizationProposalSkill()
        self.current = {"algorithm": "Ring AllReduce", "score": 80, "latency": 0.5, "bandwidth": 10}
        self.candidates = [
            {"algorithm": "Ring AllReduce", "score": 80},
            {"algorithm": "NHR", "score": 90},
        ]
        self.topo = {"topology_type": "FatTree", "node_count": 32}

    def test_generates_proposal(self):
        p = self.skill.generate_proposal(self.current, self.candidates, self.topo)
        for k in ("summary", "detected_bottlenecks", "recommendations", "confidence", "migration_plan"):
            self.assertIn(k, p)

    def test_confidence_in_range(self):
        p = self.skill.generate_proposal(self.current, self.candidates, self.topo)
        self.assertGreaterEqual(p["confidence"], 0.0)
        self.assertLessEqual(p["confidence"], 1.0)

    def test_improvements_deterministic(self):
        p1 = self.skill.generate_proposal(self.current, self.candidates, self.topo)
        p2 = self.skill.generate_proposal(self.current, self.candidates, self.topo)
        self.assertEqual(p1["expected_improvements"], p2["expected_improvements"])

    def test_migration_plan_has_steps(self):
        p = self.skill.generate_proposal(self.current, self.candidates, self.topo)
        self.assertGreater(len(p["migration_plan"]), 3)


if __name__ == "__main__":
    unittest.main()
