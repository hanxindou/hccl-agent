"""End-to-end reliability flow test."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from simulator.simulator import Simulator
from topology.graph_builder import TopologyGraphBuilder


class TestReliabilityFlow(unittest.TestCase):

    def test_simulate_with_failures_returns_reliability(self):
        sim = Simulator()
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        r = sim.simulate_with_failures(
            g, "AllReduce", "Ring AllReduce", 256,
            link_failure_rate=0.1, seed=42,
        )
        self.assertIn("reliability", r)
        rel = r["reliability"]
        self.assertIn("health", rel)
        self.assertIn("retry", rel)
        self.assertIn("failover", rel)

    def test_healthy_cluster_no_failures(self):
        sim = Simulator()
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        r = sim.simulate_with_failures(
            g, "AllReduce", "Ring AllReduce", 128,
            seed=42,
        )
        self.assertTrue(r["reliability"]["health"]["healthy"])
        self.assertTrue(r["reliability"]["retry"]["success"])


if __name__ == "__main__":
    unittest.main()
