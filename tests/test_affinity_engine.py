"""Tests for AffinityEngine."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from hardware.node_profile import NodeProfile
from hardware.affinity_engine import AffinityEngine


class TestAffinityEngine(unittest.TestCase):

    def setUp(self):
        self.np = NodeProfile(
            device_affinity={0: 0, 1: 0, 2: 1, 3: 1},
            nic_affinity={0: 0, 1: 0, 2: 1, 3: 1},
        )

    def test_same_numa_high_affinity(self):
        aff = AffinityEngine.calculate_device_affinity(0, 1, self.np)
        self.assertGreater(aff, 0.8)

    def test_different_numa_lower_affinity(self):
        aff = AffinityEngine.calculate_device_affinity(0, 2, self.np)
        self.assertLess(aff, 0.8)

    def test_locality_score_range(self):
        loc = AffinityEngine.evaluate_locality(self.np)
        self.assertGreaterEqual(loc["locality_score"], 0)
        self.assertLessEqual(loc["locality_score"], 1)

    def test_nic_affinity(self):
        aff = AffinityEngine.calculate_nic_affinity(0, 0, self.np)
        self.assertEqual(aff, 1.0)


if __name__ == "__main__":
    unittest.main()
