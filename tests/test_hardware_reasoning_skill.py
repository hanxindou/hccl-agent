"""Tests for HardwareReasoningSkill."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hardware.node_profile import NodeProfile
from hardware.resource_manager import ResourceManager
from skills.hardware_reasoning_skill import HardwareReasoningSkill


class TestHardwareReasoningSkill(unittest.TestCase):

    def setUp(self):
        self.np = NodeProfile(node_id=0)
        self.rm = ResourceManager([self.np])

    def test_analyze_resources(self):
        r = HardwareReasoningSkill.analyze_resources(self.rm, 0)
        self.assertIn("resource_pressure", r)

    def test_detect_bottlenecks(self):
        b = HardwareReasoningSkill.detect_bottlenecks([self.np], self.rm)
        self.assertIsInstance(b, list)

    def test_recommend_placement(self):
        r = HardwareReasoningSkill.recommend_placement(self.np, 8)
        self.assertIn("ranks_per_numa", r)

    def test_bottleneck_after_allocation(self):
        self.rm.allocate_hbm(0, 63.5)
        b = HardwareReasoningSkill.detect_bottlenecks([self.np], self.rm)
        self.assertGreater(len(b), 0)


if __name__ == "__main__":
    unittest.main()
