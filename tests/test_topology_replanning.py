"""Tests for topology-driven replanning."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from agent.replanning_skill import ReplanningSkill


class TestTopologyReplanning(unittest.TestCase):

    def test_topology_changed_forces_replan(self):
        ranking = [("Mesh", 90), ("Ring AllReduce", 80)]
        r = ReplanningSkill.choose_alternative(
            "Ring AllReduce", ranking, topology_changed=True,
        )
        self.assertEqual(r, "Mesh")

    def test_no_change_no_force(self):
        ranking = [("Ring AllReduce", 90), ("Mesh", 80)]
        r = ReplanningSkill.choose_alternative(
            "Mesh", ranking, topology_changed=False,
        )
        self.assertEqual(r, "Ring AllReduce")

    def test_single_algorithm_topology_changed(self):
        ranking = [("Ring AllReduce", 90)]
        r = ReplanningSkill.choose_alternative(
            "Ring AllReduce", ranking, topology_changed=True,
        )
        self.assertEqual(r, "Ring AllReduce")


if __name__ == "__main__":
    unittest.main()
