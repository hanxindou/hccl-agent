"""Tests for ResourceManager."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hardware.node_profile import NodeProfile
from hardware.resource_manager import ResourceManager


class TestResourceManager(unittest.TestCase):

    def setUp(self):
        self.np = NodeProfile(node_id=0, hbm_capacity_gb=64, ub_capacity_mb=0.192)
        self.rm = ResourceManager([self.np])

    def test_allocate_hbm(self):
        self.assertTrue(self.rm.allocate_hbm(0, 10))
        usage = self.rm.get_resource_usage(0)
        self.assertGreater(usage["hbm_used_gb"], 0)

    def test_allocate_exceeds_capacity(self):
        self.assertFalse(self.rm.allocate_hbm(0, 100))

    def test_release_hbm(self):
        self.rm.allocate_hbm(0, 20)
        self.rm.release_hbm(0, 10)
        usage = self.rm.get_resource_usage(0)
        self.assertAlmostEqual(usage["hbm_used_gb"], 10)

    def test_get_resource_usage_defaults(self):
        usage = self.rm.get_resource_usage(0)
        self.assertIn("hbm_available_gb", usage)


if __name__ == "__main__":
    unittest.main()
