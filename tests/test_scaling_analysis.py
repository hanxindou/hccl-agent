"""Tests for scaling analysis output."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from simulator.simulator import Simulator


class TestScalingAnalysis(unittest.TestCase):

    def test_scaling_scores_decreasing_trend(self):
        """Scores should generally decrease from small to large node counts."""
        sim = Simulator()
        s4  = sim.simulate_with_graph(
            TopologyGraphBuilder.build(4,  mode="SINGLE_NODE")[0], "AllReduce", "Ring AllReduce", 256,
        )["score"]
        s64 = sim.simulate_with_graph(
            TopologyGraphBuilder.build(64, num_gpus_per_node=8, mode="MULTI_NODE")[0], "AllReduce", "Ring AllReduce", 256,
        )["score"]
        self.assertGreater(s4, s64)

    def test_scaling_latency_increasing_trend(self):
        sim = Simulator()
        l4  = sim.simulate_with_graph(
            TopologyGraphBuilder.build(4,  mode="SINGLE_NODE")[0], "AllReduce", "Ring AllReduce", 256,
        )["latency"]
        l64 = sim.simulate_with_graph(
            TopologyGraphBuilder.build(64, num_gpus_per_node=8, mode="MULTI_NODE")[0], "AllReduce", "Ring AllReduce", 256,
        )["latency"]
        self.assertGreater(l64, l4)

    def test_score_never_zero(self):
        sim = Simulator()
        g, _ = TopologyGraphBuilder.build(256, num_gpus_per_node=8, mode="MULTI_NODE")
        r = sim.simulate_with_graph(g, "AllReduce", "Ring AllReduce", 256)
        self.assertGreater(r["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
