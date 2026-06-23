"""Tests for TopologyGraphBuilder and CommunicationGraph."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.graph_builder import TopologyGraphBuilder, CommunicationGraph


class TestTopologyGraphBuilder(unittest.TestCase):

    def test_single_node_full_mesh(self):
        g, meta = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        self.assertEqual(g.num_nodes, 8)
        self.assertGreater(len(g.edges), 0)
        self.assertEqual(meta["mode"], "SINGLE_NODE")

    def test_multi_node_has_roce_edges(self):
        g, meta = TopologyGraphBuilder.build(16, num_gpus_per_node=8,
                                             mode="MULTI_NODE")
        roce_count = sum(1 for e in g.edges if e.link_type == "RoCE")
        self.assertGreater(roce_count, 0)
        self.assertEqual(meta["topology"], "Fat Tree")

    def test_hetero_has_mixed_links(self):
        g, _ = TopologyGraphBuilder.build(12, num_gpus_per_node=4,
                                          mode="HETEROGENEOUS")
        types = {e.link_type for e in g.edges}
        self.assertGreaterEqual(len(types), 2)

    def test_graph_edges_have_bandwidth(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        for e in g.edges:
            self.assertGreater(e.bandwidth_gbps, 0)
            self.assertGreaterEqual(e.latency_ms, 0)

    def test_all_pairs_reachable_single_node(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        for i in range(4):
            for j in range(4):
                if i != j:
                    segs = g.all_paths_segments([i, j])
                    self.assertEqual(len(segs), 1)

    def test_outgoing_returns_edges(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        self.assertGreater(len(g.outgoing(0)), 0)


if __name__ == "__main__":
    unittest.main()
