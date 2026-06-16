"""Tests for EvaluationSkill — performance grading."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.evaluation_skill import EvaluationSkill


class TestEvaluationSkill(unittest.TestCase):

    def setUp(self):
        self.skill = EvaluationSkill()

    def test_excellent_score_80(self):
        result = self.skill.evaluate(
            {"algorithm": "Ring AllReduce", "score": 80.0},
        )
        self.assertEqual(result["grade"], "EXCELLENT")

    def test_excellent_boundary_70(self):
        result = self.skill.evaluate({"score": 70.0})
        self.assertEqual(result["grade"], "EXCELLENT")

    def test_good_score_60(self):
        result = self.skill.evaluate({"score": 60.0})
        self.assertEqual(result["grade"], "GOOD")

    def test_good_boundary_50(self):
        result = self.skill.evaluate({"score": 50.0})
        self.assertEqual(result["grade"], "GOOD")

    def test_fair_score_40(self):
        result = self.skill.evaluate({"score": 40.0})
        self.assertEqual(result["grade"], "FAIR")

    def test_fair_boundary_30(self):
        result = self.skill.evaluate({"score": 30.0})
        self.assertEqual(result["grade"], "FAIR")

    def test_poor_score_20(self):
        result = self.skill.evaluate({"score": 20.0})
        self.assertEqual(result["grade"], "POOR")

    def test_poor_score_zero(self):
        result = self.skill.evaluate({"score": 0.0})
        self.assertEqual(result["grade"], "POOR")

    def test_missing_score_defaults_to_poor(self):
        result = self.skill.evaluate({})
        self.assertEqual(result["grade"], "POOR")

    def test_recommendation_present(self):
        result = self.skill.evaluate({"score": 60.0})
        self.assertIn("recommendation", result)
        self.assertTrue(len(result["recommendation"]) > 0)


if __name__ == "__main__":
    unittest.main()
