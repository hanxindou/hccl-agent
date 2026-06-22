"""Tests for PolicyEngine — win-rate calculation and score blending."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.policy_engine import PolicyEngine


class TestPolicyEngine(unittest.TestCase):

    # ---- win rates ----

    def test_empty_input(self):
        self.assertEqual(PolicyEngine.calculate_win_rates({}), {})

    def test_single_algorithm(self):
        stats = {"Mesh": {"count": 5, "total_score": 450, "total_time_ms": 1.0}}
        wr = PolicyEngine.calculate_win_rates(stats)
        self.assertEqual(wr, {"Mesh": 1.0})

    def test_multiple_algorithms(self):
        stats = {"Mesh": {"count": 2}, "Butterfly": {"count": 1}}
        wr = PolicyEngine.calculate_win_rates(stats)
        self.assertAlmostEqual(wr["Mesh"], 0.6667, places=3)
        self.assertAlmostEqual(wr["Butterfly"], 0.3333, places=3)

    def test_equal_counts(self):
        stats = {"A": {"count": 3}, "B": {"count": 3}}
        wr = PolicyEngine.calculate_win_rates(stats)
        self.assertEqual(wr["A"], 0.5)
        self.assertEqual(wr["B"], 0.5)

    # ---- ranking ----

    def test_rank_with_win_rates(self):
        sim = {"Ring AllReduce": 82.0, "Butterfly": 86.0, "Mesh": 88.0}
        wr = {"Ring AllReduce": 0.20, "Butterfly": 0.35, "Mesh": 0.45}
        result = PolicyEngine.rank_algorithms(sim, wr)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], "Mesh")
        self.assertAlmostEqual(result[0][1], 75.1, places=1)

    def test_rank_is_sorted_descending(self):
        sim = {"A": 50, "B": 50, "C": 50}
        wr = {"A": 0.1, "B": 0.5, "C": 0.4}
        result = PolicyEngine.rank_algorithms(sim, wr)
        scores = [s for _, s in result]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_missing_algorithm_uses_zero_win_rate(self):
        sim = {"A": 80, "B": 80}
        wr = {"A": 0.5}
        result = PolicyEngine.rank_algorithms(sim, wr)
        # B gets win_rate=0 → score = 80*0.7 + 0 = 56
        # A gets score = 80*0.7 + 50*0.3 = 71
        self.assertEqual(result[0][0], "A")

    def test_boundary_zero_values(self):
        result = PolicyEngine.rank_algorithms({"X": 0}, {})
        self.assertEqual(result[0][1], 0.0)

    def test_no_win_rates_still_ranks(self):
        sim = {"A": 90, "B": 80}
        result = PolicyEngine.rank_algorithms(sim, {})
        self.assertEqual(result[0][0], "A")
        self.assertAlmostEqual(result[0][1], 63.0)  # 90 * 0.7


if __name__ == "__main__":
    unittest.main()
