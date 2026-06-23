"""Tests: Reflection includes decision quality analysis."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.reflection_skill import ReflectionSkill


class TestReflectionDecisionQuality(unittest.TestCase):

    def setUp(self):
        self.skill = ReflectionSkill()

    def test_decision_quality_present_with_candidates(self):
        candidates = [
            {"algorithm": "Ring AllReduce", "score": 80},
            {"algorithm": "Butterfly", "score": 91},
        ]
        r = self.skill.reflect(
            80, 0.3, "Ring AllReduce", candidate_scores=candidates,
        )
        self.assertIsNotNone(r["decision_quality"])
        self.assertEqual(r["decision_quality"]["best_alternative"], "Butterfly")
        self.assertGreater(r["decision_quality"]["score_gap"], 0)

    def test_decision_quality_none_without_candidates(self):
        r = self.skill.reflect(80, 0.3, "Ring AllReduce")
        self.assertIsNone(r["decision_quality"])

    def test_recommendation_suboptimal_when_gap_large(self):
        candidates = [
            {"algorithm": "Mesh", "score": 70},
            {"algorithm": "NHR", "score": 95},
        ]
        r = self.skill.reflect(
            70, 0.5, "Mesh", candidate_scores=candidates,
        )
        self.assertIn("suboptimal", r["decision_quality"]["recommendation"])


if __name__ == "__main__":
    unittest.main()
