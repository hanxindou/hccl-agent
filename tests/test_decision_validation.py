"""Tests for DecisionValidationSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.decision_validation_skill import DecisionValidationSkill


class TestDecisionValidation(unittest.TestCase):

    def test_optimal_when_selected_is_best(self):
        candidates = [
            {"algorithm": "Ring AllReduce", "score": 85},
            {"algorithm": "Butterfly", "score": 80},
        ]
        r = DecisionValidationSkill.validate("Ring AllReduce", candidates)
        self.assertTrue(r["is_optimal"])
        self.assertEqual(r["gap"], 0.0)

    def test_not_optimal_when_gap_exists(self):
        candidates = [
            {"algorithm": "NHR", "score": 95},
            {"algorithm": "Ring AllReduce", "score": 80},
        ]
        r = DecisionValidationSkill.validate("Ring AllReduce", candidates)
        self.assertFalse(r["is_optimal"])
        self.assertGreater(r["gap"], 0)

    def test_confidence_high_when_small_gap(self):
        candidates = [
            {"algorithm": "Mesh", "score": 88},
            {"algorithm": "Butterfly", "score": 87},
        ]
        r = DecisionValidationSkill.validate("Butterfly", candidates)
        self.assertIn("confidence", r)

    def test_empty_candidates(self):
        r = DecisionValidationSkill.validate("Ring", [])
        self.assertTrue(r["is_optimal"])


if __name__ == "__main__":
    unittest.main()
