"""Tests for the Python ↔ libhccl_plugin.so bridge."""

import os
import sys
import unittest

# Ensure the project root is on sys.path.
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.hccl_bridge import HCCLBridge
from agent.plugin_capability import parse_algorithm_list, map_algorithm_name


class TestPluginBridge(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bridge = HCCLBridge()
        cls.bridge.load_library()

    # ---- library loading ----

    def test_load_library_succeeds(self):
        """The shared library must load without error."""
        # load_library() is idempotent — calling again is safe.
        self.bridge.load_library()
        self.assertIsNotNone(self.bridge._lib)

    def test_missing_library_raises(self):
        with self.assertRaises(FileNotFoundError):
            HCCLBridge(lib_path="/nonexistent/libhccl_plugin.so")

    # ---- version ----

    def test_get_version_non_empty(self):
        version = self.bridge.get_version()
        self.assertIsInstance(version, str)
        self.assertTrue(len(version) > 0, "version string must not be empty")

    def test_get_version_returns_str(self):
        version = self.bridge.get_version()
        self.assertEqual(type(version), str)

    # ---- algorithms ----

    def test_get_algorithms_contains_ring(self):
        algos = self.bridge.get_algorithms()
        self.assertIn("RingAllReduce", algos)

    def test_get_algorithms_non_empty(self):
        algos = self.bridge.get_algorithms()
        self.assertIsInstance(algos, str)
        self.assertTrue(len(algos) > 0)

    # ---- algorithm parsing ----

    def test_parse_algorithm_list(self):
        raw = "RingAllReduce,Butterfly,Mesh,NHR,FatTree"
        parsed = parse_algorithm_list(raw)
        self.assertEqual(
            parsed,
            ["RingAllReduce", "Butterfly", "Mesh", "NHR", "FatTree"],
        )

    def test_parse_empty_string(self):
        self.assertEqual(parse_algorithm_list(""), [])
        self.assertEqual(parse_algorithm_list("  "), [])

    def test_map_algorithm_name(self):
        self.assertEqual(map_algorithm_name("RingAllReduce"), "Ring AllReduce")
        self.assertEqual(map_algorithm_name("FatTree"), "Fat-Tree")
        self.assertEqual(map_algorithm_name("Butterfly"), "Butterfly")
        self.assertEqual(map_algorithm_name("UnknownAlgo"), "UnknownAlgo")

    # ---- print capabilities (visual inspection) ----

    def test_print_capabilities(self):
        """Print plugin info for visual verification."""
        version = self.bridge.get_version()
        algos_raw = self.bridge.get_algorithms()
        algos_list = parse_algorithm_list(algos_raw)
        mapped = [map_algorithm_name(a) for a in algos_list]

        print()
        print("Plugin Version:")
        print(f"  {version}")
        print()
        print("Algorithms (raw):")
        print(f"  {algos_raw}")
        print()
        print("Algorithms (parsed):")
        for a in mapped:
            print(f"  - {a}")

        self.assertTrue(len(version) > 0)
        self.assertTrue(len(algos_list) > 0)


if __name__ == "__main__":
    unittest.main()
