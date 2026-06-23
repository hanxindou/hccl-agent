"""Tests for AlgorithmSelector — topology-aware ranking."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.algorithm_selector import AlgorithmSelector, SUPPORTED_ALGORITHMS
from topology.graph_builder import TopologyGraphBuilder
from hardware.profile import HardwareProfile


class TestAlgorithmSelector(unittest.TestCase):

    def setUp(self):
        self.selector = AlgorithmSelector()
        self.graph, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        self.profile = HardwareProfile.tier_medium()

    def test_select_allreduce_returns_best(self):
        r = self.selector.select_algorithm(
            "AllReduce", self.graph, self.profile,
        )
        self.assertIn("algorithm", r)
        self.assertIn("score", r)
        self.assertIn("candidates", r)

    def test_candidates_ranked_by_score(self):
        r = self.selector.select_algorithm(
            "AllReduce", self.graph, self.profile,
        )
        scores = [c["score"] for c in r["candidates"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_selected_is_first_candidate(self):
        r = self.selector.select_algorithm(
            "AllReduce", self.graph, self.profile,
        )
        self.assertEqual(r["algorithm"], r["candidates"][0]["algorithm"])

    def test_different_primitives_different_candidates(self):
        r1 = self.selector.select_algorithm(
            "AllGather", self.graph, self.profile,
        )
        r2 = self.selector.select_algorithm(
            "ReduceScatter", self.graph, self.profile,
        )
        algs1 = {c["algorithm"] for c in r1["candidates"]}
        algs2 = {c["algorithm"] for c in r2["candidates"]}
        self.assertNotEqual(algs1, algs2)

    def test_supported_algorithms_non_empty(self):
        self.assertGreater(len(SUPPORTED_ALGORITHMS), 0)


if __name__ == "__main__":
    unittest.main()
