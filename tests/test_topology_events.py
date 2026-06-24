"""Tests for TopologyEvent types."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from topology.topology_events import TopologyEvent


class TestTopologyEvents(unittest.TestCase):

    def test_node_join_event(self):
        e = TopologyEvent("NodeJoin", node_id=5)
        self.assertEqual(e.event_type, "NodeJoin")
        self.assertEqual(e.node_id, 5)

    def test_link_failure_event(self):
        e = TopologyEvent("LinkFailure", src=0, dst=3)
        self.assertEqual(e.event_type, "LinkFailure")
        self.assertEqual(e.src, 0)
        self.assertEqual(e.dst, 3)

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            TopologyEvent("InvalidType")

    def test_all_valid_types_accepted(self):
        for t in TopologyEvent.VALID_TYPES:
            e = TopologyEvent(t)
            self.assertEqual(e.event_type, t)

    def test_event_repr(self):
        e = TopologyEvent("NodeJoin", node_id=3)
        self.assertIn("NodeJoin", repr(e))
        self.assertIn("3", repr(e))


if __name__ == "__main__":
    unittest.main()
