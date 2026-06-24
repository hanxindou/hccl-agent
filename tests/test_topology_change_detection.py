"""Tests for topology change detection."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from skills.topology_reasoning_skill import TopologyReasoningSkill


class TestTopologyChangeDetection(unittest.TestCase):

    def test_no_change(self):
        a = {"node_count": 8, "edge_count": 56, "dominant_link": "HCCS"}
        r = TopologyReasoningSkill.detect_topology_change(a, a)
        self.assertFalse(r["changed"])

    def test_node_count_change(self):
        a = {"node_count": 8, "edge_count": 56, "dominant_link": "HCCS"}
        b = {"node_count": 16, "edge_count": 100, "dominant_link": "HCCS"}
        r = TopologyReasoningSkill.detect_topology_change(a, b)
        self.assertTrue(r["changed"])

    def test_edge_count_change(self):
        a = {"node_count": 8, "edge_count": 56, "dominant_link": "HCCS"}
        b = {"node_count": 8, "edge_count": 40, "dominant_link": "HCCS"}
        r = TopologyReasoningSkill.detect_topology_change(a, b)
        self.assertTrue(r["changed"])

    def test_dominant_link_change(self):
        a = {"node_count": 8, "edge_count": 56, "dominant_link": "HCCS"}
        b = {"node_count": 8, "edge_count": 56, "dominant_link": "RoCE"}
        r = TopologyReasoningSkill.detect_topology_change(a, b)
        self.assertTrue(r["changed"])


if __name__ == "__main__":
    unittest.main()
