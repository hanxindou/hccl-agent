"""Tests for NodeProfile."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hardware.node_profile import NodeProfile


class TestNodeProfile(unittest.TestCase):

    def test_default_values(self):
        np = NodeProfile(node_id=0)
        self.assertEqual(np.num_devices, 8)
        self.assertEqual(np.numa_domains, 2)

    def test_to_dict(self):
        np = NodeProfile(node_id=1)
        d = np.to_dict()
        self.assertEqual(d["node_id"], 1)

    def test_from_dict(self):
        np = NodeProfile.from_dict({"node_id": 3, "num_devices": 4})
        self.assertEqual(np.node_id, 3)
        self.assertEqual(np.num_devices, 4)

    def test_resource_summary(self):
        rs = NodeProfile().resource_summary()
        self.assertIn("hbm_gb", rs)
        self.assertIn("ub_mb", rs)


if __name__ == "__main__":
    unittest.main()
