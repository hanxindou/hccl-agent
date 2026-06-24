"""Tests for AutoTuningSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.auto_tuning_skill import AutoTuningSkill


class TestAutoTuningSkill(unittest.TestCase):

    def test_generate_parameter_space(self):
        ps = AutoTuningSkill.generate_parameter_space()
        self.assertIn("chunk_size_mb", ps)
        self.assertGreater(len(ps["chunk_size_mb"]), 0)

    def test_enumerate_configurations(self):
        configs = AutoTuningSkill.enumerate_configurations()
        expected = 5 * 3 * 3  # 5 chunks × 3 depths × 3 overlaps
        self.assertEqual(len(configs), expected)

    def test_grid_search_returns_top_k(self):
        r = AutoTuningSkill.grid_search("NHR", "Fat Tree", 32, 256, 42.0)
        self.assertIn("best_config", r)
        self.assertEqual(len(r["top_k"]), 5)
        self.assertEqual(r["evaluated_configs"], 45)

    def test_score_not_exceed_100(self):
        for cfg in AutoTuningSkill.enumerate_configurations():
            s = AutoTuningSkill.evaluate_configuration(cfg, "Ring", "Ring", 8, 128, 95.0)
            self.assertLessEqual(s, 100.0)

    def test_deterministic(self):
        r1 = AutoTuningSkill.grid_search("NHR", "Ring", 8, 128, 50.0)
        r2 = AutoTuningSkill.grid_search("NHR", "Ring", 8, 128, 50.0)
        self.assertEqual(r1["best_score"], r2["best_score"])
        self.assertEqual(r1["best_config"], r2["best_config"])

    def test_best_score_greater_than_base(self):
        r = AutoTuningSkill.grid_search("NHR", "Ring", 8, 128, 50.0)
        self.assertGreaterEqual(r["best_score"], 50.0)


if __name__ == "__main__":
    unittest.main()
