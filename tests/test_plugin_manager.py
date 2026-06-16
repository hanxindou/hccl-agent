"""Tests for PluginManager — Agent ↔ Plugin integration."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from agent.plugin_manager import PluginManager


class TestPluginManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.mgr = PluginManager()

    # ---- init ----

    def test_manager_initializes(self):
        """PluginManager must construct without error."""
        mgr = PluginManager()
        self.assertIsNotNone(mgr.bridge)

    # ---- discover ----

    def test_discover_returns_dict(self):
        info = self.mgr.discover()
        self.assertIsInstance(info, dict)

    def test_discover_version_non_empty(self):
        info = self.mgr.discover()
        self.assertIn("version", info)
        self.assertTrue(len(info["version"]) > 0)

    def test_discover_algorithms_non_empty(self):
        info = self.mgr.discover()
        self.assertIn("algorithms", info)
        self.assertIsInstance(info["algorithms"], list)
        self.assertTrue(len(info["algorithms"]) > 0)

    def test_discover_contains_ring_allreduce(self):
        info = self.mgr.discover()
        self.assertIn("Ring AllReduce", info["algorithms"])

    def test_discover_raw_algorithms(self):
        info = self.mgr.discover()
        self.assertIn("raw_algorithms", info)
        self.assertIn("RingAllReduce", info["raw_algorithms"])

    def test_discover_library_path(self):
        info = self.mgr.discover()
        self.assertIn("library_path", info)
        self.assertTrue(info["library_path"].endswith(".so"))

    # ---- capability report (visual inspection) ----

    def test_print_capability_report(self):
        info = self.mgr.discover()

        print()
        print("Plugin Version:")
        print(f"  {info['version']}")
        print()
        print("Supported Algorithms:")
        for algo in info["algorithms"]:
            print(f"  - {algo}")
        print()

        self.assertTrue(len(info["version"]) > 0)
        self.assertTrue(len(info["algorithms"]) > 0)


if __name__ == "__main__":
    unittest.main()
