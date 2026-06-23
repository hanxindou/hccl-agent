"""Tests for CostModelEngine."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cost_model.engine import CostModelEngine
from topology.graph_builder import TopologyGraphBuilder


class TestCostModel(unittest.TestCase):

    def setUp(self):
        self.engine = CostModelEngine()
        self.graph, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")

    def test_ring_estimate_returns_keys(self):
        r = self.engine.estimate_allreduce_ring(self.graph, 128.0)
        self.assertIn("latency_ms", r)
        self.assertIn("bandwidth_gbps", r)
        self.assertGreater(r["latency_ms"], 0)

    def test_tree_estimate(self):
        r = self.engine.estimate_allreduce_tree(self.graph, 128.0, "Butterfly")
        self.assertIn("latency_ms", r)

    def test_different_algorithms_different_cost(self):
        r1 = self.engine.estimate_allreduce_ring(self.graph, 256.0, "Ring AllReduce")
        r2 = self.engine.estimate_allreduce_tree(self.graph, 256.0, "Butterfly")
        self.assertNotEqual(r1["latency_ms"], r2["latency_ms"])

    def test_generic_fallback(self):
        r = self.engine.estimate_generic(self.graph, 64.0, "UnknownAlgo", "AllReduce")
        self.assertIn("latency_ms", r)

    def test_single_node_trivial(self):
        g, _ = TopologyGraphBuilder.build(1, mode="SINGLE_NODE")
        r = self.engine.estimate_allreduce_ring(g, 10.0)
        self.assertEqual(r["latency_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
