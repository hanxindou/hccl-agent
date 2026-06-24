"""Tests: hardware-aware algorithm selection via topology summary."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hardware.node_profile import NodeProfile
from skills.topology_reasoning_skill import TopologyReasoningSkill


class TestHardwareAwareSelection(unittest.TestCase):

    def test_hardware_summary(self):
        nps = [NodeProfile(node_id=0), NodeProfile(node_id=1)]
        hs = TopologyReasoningSkill.hardware_summary(nps)
        self.assertEqual(hs["num_nodes"], 2)
        self.assertEqual(hs["total_devices"], 16)
        self.assertIn("hbm_capacity_gb", hs)

    def test_hardware_summary_empty(self):
        self.assertEqual(TopologyReasoningSkill.hardware_summary([]), {})


if __name__ == "__main__":
    unittest.main()
