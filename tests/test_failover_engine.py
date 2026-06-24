"""Tests for FailoverEngine."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from simulator.failover_engine import FailoverEngine
from topology.graph_builder import TopologyGraphBuilder


class TestFailoverEngine(unittest.TestCase):

    def test_direct_path_no_failover(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        fe = FailoverEngine()
        r = fe.reroute(g, 0, 2)
        self.assertTrue(r["found"])
        self.assertFalse(r["failover_triggered"])
        self.assertEqual(r["route"], [0, 2])

    def test_failover_route(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        fe = FailoverEngine()
        r = fe.reroute(g, 0, 2, failed_edge=(0, 2))
        self.assertTrue(r["found"])
        self.assertEqual(r["hops"], 2)

    def test_failover_count_increments(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        fe = FailoverEngine()
        fe.reroute(g, 0, 2, failed_edge=(0, 2))
        self.assertGreater(fe.failover_count, 0)


if __name__ == "__main__":
    unittest.main()
