"""Tests for HealthMonitor."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from simulator.health_monitor import HealthMonitor


class TestHealthMonitor(unittest.TestCase):

    def test_default_healthy(self):
        m = HealthMonitor(seed=42)
        h = m.evaluate_cluster_health()
        self.assertTrue(h["healthy"])
        self.assertEqual(h["status"], "HEALTHY")

    def test_inject_failures(self):
        m = HealthMonitor(seed=42)
        m.inject_failures(num_nodes=8, link_failure_rate=0.5)
        h = m.evaluate_cluster_health()
        self.assertFalse(h["healthy"])

    def test_check_link(self):
        m = HealthMonitor(seed=42)
        r = m.check_link(0, 1)
        self.assertTrue(r["healthy"])

    def test_check_node(self):
        m = HealthMonitor(seed=42)
        r = m.check_node(0)
        self.assertTrue(r["healthy"])

    def test_is_link_healthy(self):
        m = HealthMonitor(seed=42)
        self.assertTrue(m.is_link_healthy(0, 1))


if __name__ == "__main__":
    unittest.main()
