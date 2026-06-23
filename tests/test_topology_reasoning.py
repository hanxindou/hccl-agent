"""Tests for TopologyReasoningSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.topology_reasoning_skill import TopologyReasoningSkill
from topology.graph_builder import TopologyGraphBuilder


class TestTopologyReasoning(unittest.TestCase):

    def test_analyze_returns_keys(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        r = TopologyReasoningSkill.analyze(g)
        for k in ("topology_type", "node_count", "edge_count",
                  "average_degree", "dominant_link"):
            self.assertIn(k, r)

    def test_single_node_identified(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        r = TopologyReasoningSkill.analyze(g)
        self.assertIn("SingleNode", r["topology_type"])

    def test_multi_node_identified(self):
        g, _ = TopologyGraphBuilder.build(32, num_gpus_per_node=8, mode="MULTI_NODE")
        r = TopologyReasoningSkill.analyze(g)
        self.assertIn("FatTree", r["topology_type"])

    def test_dominant_link_hccs_for_single_node(self):
        g, _ = TopologyGraphBuilder.build(4, mode="SINGLE_NODE")
        r = TopologyReasoningSkill.analyze(g)
        self.assertEqual(r["dominant_link"], "HCCS")

    def test_edge_count_positive(self):
        g, _ = TopologyGraphBuilder.build(8, mode="SINGLE_NODE")
        r = TopologyReasoningSkill.analyze(g)
        self.assertGreater(r["edge_count"], 0)


if __name__ == "__main__":
    unittest.main()
