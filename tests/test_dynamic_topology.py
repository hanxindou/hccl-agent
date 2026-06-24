"""Tests for DynamicTopologyManager."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.dynamic_topology import DynamicTopologyManager
from topology.topology_events import TopologyEvent


class TestDynamicTopology(unittest.TestCase):

    def test_initial_graph(self):
        mgr = DynamicTopologyManager(8)
        self.assertEqual(mgr.current_version(), 0)
        self.assertEqual(mgr.graph.num_nodes, 8)

    def test_node_join_increases_count(self):
        mgr = DynamicTopologyManager(8)
        mgr.apply_event(TopologyEvent("NodeJoin", node_id=8))
        self.assertEqual(mgr.current_node_count(), 9)
        self.assertEqual(mgr.current_version(), 1)

    def test_node_leave_decreases_count(self):
        mgr = DynamicTopologyManager(8)
        mgr.apply_event(TopologyEvent("NodeLeave", node_id=3))
        self.assertEqual(mgr.current_node_count(), 7)
        self.assertGreaterEqual(mgr.graph.num_nodes, 1)

    def test_event_history(self):
        mgr = DynamicTopologyManager(4)
        mgr.apply_event(TopologyEvent("NodeJoin"))
        mgr.apply_event(TopologyEvent("NodeJoin"))
        self.assertEqual(len(mgr.event_history()), 2)

    def test_batch_events(self):
        mgr = DynamicTopologyManager(8)
        events = [
            TopologyEvent("NodeJoin"), TopologyEvent("NodeJoin"),
        ]
        mgr.apply_events(events)
        self.assertEqual(mgr.current_node_count(), 10)
        self.assertEqual(mgr.current_version(), 2)


if __name__ == "__main__":
    unittest.main()
