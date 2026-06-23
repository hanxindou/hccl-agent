"""Tests for ReplanningSkill — alternative algorithm selection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.replanning_skill import ReplanningSkill


class TestReplanningSkill(unittest.TestCase):

    def test_returns_second_ranked(self):
        result = ReplanningSkill.choose_alternative(
            "Mesh", [("Mesh", 91), ("Butterfly", 87), ("Ring AllReduce", 80)],
        )
        self.assertEqual(result, "Butterfly")

    def test_skips_same_name(self):
        result = ReplanningSkill.choose_alternative(
            "Butterfly", [("Butterfly", 91), ("Mesh", 85)],
        )
        self.assertEqual(result, "Mesh")

    def test_single_algorithm_returns_same(self):
        result = ReplanningSkill.choose_alternative(
            "Mesh", [("Mesh", 91)],
        )
        self.assertEqual(result, "Mesh")

    def test_empty_ranking_returns_current(self):
        result = ReplanningSkill.choose_alternative("Mesh", [])
        self.assertEqual(result, "Mesh")

    def test_current_not_in_ranking(self):
        result = ReplanningSkill.choose_alternative(
            "Unknown", [("Mesh", 91), ("Butterfly", 87)],
        )
        self.assertEqual(result, "Mesh")

    def test_all_same_algorithm_returns_current(self):
        result = ReplanningSkill.choose_alternative(
            "Mesh", [("Mesh", 91), ("Mesh", 87)],
        )
        self.assertEqual(result, "Mesh")

    def test_ranking_order_preserved(self):
        result = ReplanningSkill.choose_alternative(
            "A", [("A", 100), ("B", 90), ("C", 80)],
        )
        self.assertEqual(result, "B")

    def test_large_ranking(self):
        ranking = [(f"Algo{i}", 100 - i) for i in range(20)]
        result = ReplanningSkill.choose_alternative("Algo0", ranking)
        self.assertEqual(result, "Algo1")


if __name__ == "__main__":
    unittest.main()
