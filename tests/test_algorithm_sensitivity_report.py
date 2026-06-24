"""Tests for algorithm sensitivity analysis."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from simulator.simulator import Simulator


class TestAlgorithmSensitivityReport(unittest.TestCase):

    def test_all_algorithms_produce_scores(self):
        g, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode="MULTI_NODE")
        sim = Simulator()
        for algo in ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"]:
            r = sim.simulate_with_graph(g, "AllReduce", algo, 512)
            self.assertGreater(r["score"], 0.0)
            self.assertGreater(r["latency"], 0.0)

    def test_algorithms_all_positive_scores(self):
        g, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode="MULTI_NODE")
        sim = Simulator()
        for algo in ["Ring AllReduce", "Butterfly", "Mesh", "NHR", "Fat-Tree"]:
            r = sim.simulate_with_graph(g, "AllReduce", algo, 512)
            self.assertGreater(r["score"], 0.0, f"{algo} should have positive score")


if __name__ == "__main__":
    unittest.main()
