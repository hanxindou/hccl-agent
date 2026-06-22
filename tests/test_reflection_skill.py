"""Tests for ReflectionSkill — post-execution analysis."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.reflection_skill import ReflectionSkill


class TestReflectionSkill(unittest.TestCase):

    def setUp(self):
        self.skill = ReflectionSkill()

    # ---- status classification ----

    def test_good_for_fast_execution(self):
        r = self.skill.reflect(95.0, 0.5, "Ring AllReduce")
        self.assertEqual(r["status"], "good")
        self.assertFalse(r["need_replan"])

    def test_warning_for_medium_execution(self):
        r = self.skill.reflect(85.0, 2.0, "Butterfly")
        self.assertEqual(r["status"], "warning")
        self.assertFalse(r["need_replan"])

    def test_poor_for_slow_execution(self):
        r = self.skill.reflect(50.0, 10.0, "NHR")
        self.assertEqual(r["status"], "poor")
        self.assertTrue(r["need_replan"])

    # ---- boundary values ----

    def test_boundary_at_1ms(self):
        r = self.skill.reflect(90.0, 0.999, "Mesh")
        self.assertEqual(r["status"], "good")

    def test_boundary_at_5ms(self):
        r = self.skill.reflect(80.0, 4.999, "Ring AllReduce")
        self.assertEqual(r["status"], "warning")

    def test_boundary_at_5ms_exact(self):
        r = self.skill.reflect(80.0, 5.0, "Fat-Tree")
        self.assertEqual(r["status"], "poor")
        self.assertTrue(r["need_replan"])

    # ---- deviation detection ----

    def test_deviation_detected_when_large_gap(self):
        # expected=(100-20)/500=0.16ms, actual=10ms → ratio≈61
        r = self.skill.reflect(20.0, 10.0, "Mesh")
        self.assertTrue(r["prediction_deviation"])

    def test_no_deviation_when_close(self):
        # expected=(100-0)/500=0.2ms, actual=0.25ms → ratio=0.25
        r = self.skill.reflect(0.0, 0.25, "Butterfly")
        self.assertFalse(r["prediction_deviation"])

    def test_deviation_at_boundary(self):
        # expected=0.2ms, actual=0.31ms → ratio=0.55 > 0.5
        r = self.skill.reflect(0.0, 0.31, "Mesh")
        self.assertTrue(r["prediction_deviation"])

    # ---- algorithm name in message ----

    def test_message_contains_algorithm_name(self):
        r = self.skill.reflect(80.0, 0.2, "NHR")
        self.assertIn("NHR", r["message"])


if __name__ == "__main__":
    unittest.main()
