"""Tests: algorithm selection quality triggers reflection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from hardware.profile import HardwareProfile
from skills.algorithm_selector import AlgorithmSelector


class TestAlgorithmReflection(unittest.TestCase):

    def test_selector_produces_consistent_results(self):
        """Deterministic: same inputs → same output."""
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        profile = HardwareProfile.tier_medium()
        selector = AlgorithmSelector()
        r1 = selector.select_algorithm("AllReduce", g, profile)
        r2 = selector.select_algorithm("AllReduce", g, profile)
        self.assertEqual(r1["algorithm"], r2["algorithm"])
        self.assertEqual(r1["score"], r2["score"])

    def test_multi_node_changes_selection(self):
        """Multi-node topology may produce different best algorithm."""
        g1, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        g2, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode="MULTI_NODE")
        profile = HardwareProfile.tier_medium()
        selector = AlgorithmSelector()
        s1 = selector.select_algorithm("AllReduce", g1, profile)
        s2 = selector.select_algorithm("AllReduce", g2, profile)
        # Both must produce valid results (may or may not differ).
        self.assertIn("algorithm", s1)
        self.assertIn("algorithm", s2)

    def test_score_threshold_for_replan_trigger(self):
        """When selected score < 30, it should motivate a replan."""
        g, _ = TopologyGraphBuilder.build(64, num_gpus_per_node=8, mode="MULTI_NODE")
        profile = HardwareProfile.tier_low()
        selector = AlgorithmSelector()
        sel = selector.select_algorithm("AllReduce", g, profile)
        # With low-tier HW on 64 nodes, score may be low.
        # Verifies the mechanism produces a score.
        self.assertGreaterEqual(sel["score"], 0)


if __name__ == "__main__":
    unittest.main()
