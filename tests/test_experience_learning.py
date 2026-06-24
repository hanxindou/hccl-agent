"""Tests for ExperienceLearningSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.experience_learning_skill import ExperienceLearningSkill


class TestExperienceLearning(unittest.TestCase):

    def test_aggregate_empty(self):
        self.assertEqual(ExperienceLearningSkill.aggregate([]), {})

    def test_aggregate_computes_stats(self):
        records = [
            {"algorithm": "NHR", "score": 42, "latency": 0.5, "nodes": 32},
            {"algorithm": "NHR", "score": 40, "latency": 0.6, "nodes": 32},
            {"algorithm": "Ring AllReduce", "score": 35, "latency": 0.8, "nodes": 32},
        ]
        stats = ExperienceLearningSkill.aggregate(records)
        self.assertIn("NHR", stats)
        self.assertEqual(stats["NHR"]["runs"], 2)
        self.assertAlmostEqual(stats["NHR"]["avg_score"], 41.0)

    def test_recommend_no_data(self):
        r = ExperienceLearningSkill.recommend_algorithm({})
        self.assertEqual(r["recommended_algorithm"], "N/A")

    def test_recommend_picks_best(self):
        stats = {"Ring": {"avg_score": 35, "runs": 5}, "NHR": {"avg_score": 42, "runs": 8}}
        r = ExperienceLearningSkill.recommend_algorithm(stats)
        self.assertEqual(r["recommended_algorithm"], "NHR")

    def test_confidence_in_range(self):
        stats = {"Ring": {"avg_score": 80, "runs": 20}, "Butterfly": {"avg_score": 60, "runs": 5}}
        r = ExperienceLearningSkill.recommend_algorithm(stats)
        self.assertGreaterEqual(r["confidence"], 0)
        self.assertLessEqual(r["confidence"], 1)

    def test_experience_bonus_recommended(self):
        stats = {"NHR": {"avg_score": 42, "runs": 8}}
        rec = {"recommended_algorithm": "NHR"}
        bonus = ExperienceLearningSkill.compute_experience_bonus("NHR", stats, rec)
        self.assertGreater(bonus, 0)

    def test_experience_bonus_poor(self):
        stats = {"Ring": {"avg_score": 80, "runs": 20}, "NHR": {"avg_score": 40, "runs": 3}}
        rec = ExperienceLearningSkill.recommend_algorithm(stats)
        bonus = ExperienceLearningSkill.compute_experience_bonus("NHR", stats, rec)
        self.assertLess(bonus, 0)


if __name__ == "__main__":
    unittest.main()
