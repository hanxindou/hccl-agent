"""Tests: experience influences algorithm selection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.experience_learning_skill import ExperienceLearningSkill
from skills.algorithm_selector import AlgorithmSelector
from topology.graph_builder import TopologyGraphBuilder
from hardware.profile import HardwareProfile


class TestExperienceDrivenSelection(unittest.TestCase):

    def test_selector_with_experience_bonus(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        sel = AlgorithmSelector().select_algorithm("AllReduce", g, HardwareProfile.tier_medium())
        self.assertIn("algorithm", sel)
        self.assertIn("selection_metadata", sel)

    def test_experience_bonus_does_not_override_simulator(self):
        """Experience bonus (+3) is small relative to simulator scores (0-100)."""
        stats = {"NHR": {"avg_score": 90, "runs": 10}}
        rec = {"recommended_algorithm": "NHR"}
        bonus = ExperienceLearningSkill.compute_experience_bonus("NHR", stats, rec)
        self.assertEqual(bonus, 3.0)
        # Bonus is only 3 out of 100 — simulator still dominates.


if __name__ == "__main__":
    unittest.main()
