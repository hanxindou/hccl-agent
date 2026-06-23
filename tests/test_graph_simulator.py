"""Tests for graph-based Simulator integration."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from simulator.simulator import Simulator
from topology.graph_builder import TopologyGraphBuilder


class TestGraphSimulator(unittest.TestCase):

    def setUp(self):
        self.sim = Simulator()
        self.graph, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")

    def test_simulate_with_graph_returns_same_keys(self):
        r = self.sim.simulate_with_graph(self.graph, "AllReduce", "Ring AllReduce")
        for k in ("latency", "bandwidth", "score", "algorithm", "primitive"):
            self.assertIn(k, r)

    def test_single_vs_multi_node_different(self):
        g1, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        g2, _ = TopologyGraphBuilder.build(16, num_gpus_per_node=8, mode="MULTI_NODE")
        r1 = self.sim.simulate_with_graph(g1, "AllReduce", "Ring AllReduce")
        r2 = self.sim.simulate_with_graph(g2, "AllReduce", "Ring AllReduce")
        self.assertNotEqual(r1["latency"], r2["latency"])

    def test_graph_score_in_range(self):
        r = self.sim.simulate_with_graph(self.graph, "AllReduce", "Ring AllReduce")
        self.assertGreaterEqual(r["score"], 0)
        self.assertLessEqual(r["score"], 100)

    def test_old_api_still_works(self):
        """Backward compatibility: evaluate() must still work."""
        r = self.sim.evaluate("Ring AllReduce", "Ring", 8, 128)
        self.assertIn("score", r)

    def test_simulate_collective_still_works(self):
        """Backward compatibility: simulate_collective() must still work."""
        r = self.sim.simulate_collective("AllReduce", "Ring AllReduce", "Ring", 8)
        self.assertIn("score", r)


if __name__ == "__main__":
    unittest.main()
