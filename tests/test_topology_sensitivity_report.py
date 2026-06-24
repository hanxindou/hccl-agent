"""Tests for topology sensitivity analysis."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder
from simulator.simulator import Simulator


class TestTopologySensitivityReport(unittest.TestCase):

    def test_all_topologies_produce_scores(self):
        sim = Simulator()
        configs = [
            (32, "SINGLE_NODE"),
            (32, "SINGLE_NODE"),
            (32, "MULTI_NODE"),
            (32, "MULTI_NODE"),
            (24, "HETEROGENEOUS"),
        ]
        for n, mode in configs:
            g, _ = TopologyGraphBuilder.build(n, num_gpus_per_node=8, mode=mode)
            r = sim.simulate_with_graph(g, "AllReduce", "Ring AllReduce", 512)
            self.assertGreater(r["score"], 0.0)

    def test_different_topologies_different_scores(self):
        sim = Simulator()
        scores = set()
        for mode in ["SINGLE_NODE", "MULTI_NODE"]:
            g, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode=mode)
            r = sim.simulate_with_graph(g, "AllReduce", "Ring AllReduce", 512)
            scores.add(round(r["score"], 1))
        self.assertGreater(len(scores), 1,
                           "Different topology modes should produce different scores")


if __name__ == "__main__":
    unittest.main()
