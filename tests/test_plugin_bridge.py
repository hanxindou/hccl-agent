"""Tests for the Python ↔ libhccl_plugin.so bridge."""

import ctypes
import os
import sys
import tempfile
import unittest
from unittest import mock

# Ensure the project root is on sys.path.
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.hccl_bridge import (
    HCCL_ERR_NOT_SUPPORTED,
    HCCL_FP32,
    HCCL_SUM,
    HCCLBridge,
    configure_ctypes_signatures,
    default_library_candidates,
)
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
            HCCLBridge(library_path="/nonexistent/libhccl_plugin.so")

    def test_legacy_lib_path_alias_still_works(self):
        self.assertEqual(self.bridge.lib_path, self.bridge.library_path)

    def test_library_path_takes_priority_over_env(self):
        with tempfile.NamedTemporaryFile() as explicit:
            with tempfile.NamedTemporaryFile() as env_lib:
                old_env = os.environ.get("HCCL_PLUGIN_PATH")
                os.environ["HCCL_PLUGIN_PATH"] = env_lib.name
                try:
                    bridge = HCCLBridge(library_path=explicit.name)
                    self.assertEqual(bridge.lib_path, os.path.normpath(explicit.name))
                    self.assertEqual(bridge.library_source, "library_path")
                finally:
                    if old_env is None:
                        os.environ.pop("HCCL_PLUGIN_PATH", None)
                    else:
                        os.environ["HCCL_PLUGIN_PATH"] = old_env

    def test_env_path_takes_priority_over_default(self):
        with tempfile.NamedTemporaryFile() as env_lib:
            old_env = os.environ.get("HCCL_PLUGIN_PATH")
            os.environ["HCCL_PLUGIN_PATH"] = env_lib.name
            try:
                bridge = HCCLBridge()
                self.assertEqual(bridge.lib_path, os.path.normpath(env_lib.name))
                self.assertEqual(bridge.library_source, "HCCL_PLUGIN_PATH")
            finally:
                if old_env is None:
                    os.environ.pop("HCCL_PLUGIN_PATH", None)
                else:
                    os.environ["HCCL_PLUGIN_PATH"] = old_env

    def test_missing_env_path_raises_clear_error(self):
        old_env = os.environ.get("HCCL_PLUGIN_PATH")
        os.environ["HCCL_PLUGIN_PATH"] = os.path.join(
            tempfile.gettempdir(), "missing_hccl_plugin_for_b1.dll"
        )
        try:
            with self.assertRaisesRegex(FileNotFoundError, "HCCL_PLUGIN_PATH"):
                HCCLBridge()
        finally:
            if old_env is None:
                os.environ.pop("HCCL_PLUGIN_PATH", None)
            else:
                os.environ["HCCL_PLUGIN_PATH"] = old_env

    def test_default_candidate_names_are_platform_specific(self):
        win_candidates = default_library_candidates("Windows")
        linux_candidates = default_library_candidates("Linux")
        self.assertTrue(any(path.endswith("hccl_plugin.dll") for path in win_candidates))
        self.assertTrue(any(path.endswith("libhccl_plugin.so") for path in linux_candidates))

    def test_default_candidates_missing_raises_clear_error(self):
        old_env = os.environ.get("HCCL_PLUGIN_PATH")
        os.environ.pop("HCCL_PLUGIN_PATH", None)
        try:
            with mock.patch(
                "plugin.hccl_bridge.default_library_candidates",
                return_value=[os.path.join(tempfile.gettempdir(), "missing_b1_plugin.dll")],
            ):
                with self.assertRaisesRegex(FileNotFoundError, "attempted paths"):
                    HCCLBridge()
        finally:
            if old_env is not None:
                os.environ["HCCL_PLUGIN_PATH"] = old_env

    def test_load_failure_contains_original_error(self):
        with tempfile.NamedTemporaryFile() as fake_lib:
            bridge = HCCLBridge(library_path=fake_lib.name)
            with self.assertRaisesRegex(OSError, "original error"):
                bridge.load_library()

    def test_missing_symbol_error_names_symbol(self):
        class PartialLibrary:
            def __init__(self):
                self.hcclPluginGetVersion = lambda: b"x"

        with self.assertRaisesRegex(AttributeError, "hcclPluginGetAlgorithms"):
            configure_ctypes_signatures(
                PartialLibrary(), "fake", ["fake"],
            )

    def test_required_argtypes_and_restype_are_configured(self):
        self.bridge.load_library()
        self.assertEqual(self.bridge._lib.hcclAllReduce.restype, ctypes.c_int)
        self.assertEqual(len(self.bridge._lib.hcclAllReduce.argtypes), 6)
        self.assertEqual(self.bridge._lib.hcclAllGather.restype, ctypes.c_int)
        self.assertEqual(len(self.bridge._lib.hcclAllGather.argtypes), 5)
        self.assertEqual(self.bridge._lib.hcclReduceScatter.restype, ctypes.c_int)
        self.assertEqual(len(self.bridge._lib.hcclReduceScatter.argtypes), 6)
        self.assertEqual(self.bridge._lib.hcclBroadcast.restype, ctypes.c_int)
        self.assertEqual(len(self.bridge._lib.hcclBroadcast.argtypes), 6)

    def test_actual_library_exports_standard_wrappers(self):
        self.bridge.load_library()
        for name in [
            "hcclAllReduce",
            "hcclAllGather",
            "hcclReduceScatter",
            "hcclBroadcast",
        ]:
            self.assertTrue(hasattr(self.bridge._lib, name), name)

    def test_actual_allreduce_wrapper_executes(self):
        self.bridge.load_library()
        lib = self.bridge._lib
        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * 4)(0, 1, 2, 3)
        self.assertEqual(lib.hcclCommInit(ctypes.byref(comm), 4, device_ids), 0)
        try:
            inputs = [1.0, 2.0, 3.0, 4.0]
            recv = ctypes.c_float()
            for rank, value in enumerate(inputs):
                lib.hcclSetRank(comm, rank)
                send = ctypes.c_float(value)
                lib.hcclAllReduce(
                    ctypes.byref(send), ctypes.byref(recv),
                    1, HCCL_FP32, HCCL_SUM, comm,
                )
            results = []
            for rank, value in enumerate(inputs):
                lib.hcclSetRank(comm, rank)
                send = ctypes.c_float(value)
                rc = lib.hcclAllReduce(
                    ctypes.byref(send), ctypes.byref(recv),
                    1, HCCL_FP32, HCCL_SUM, comm,
                )
                self.assertEqual(rc, 0)
                results.append(round(recv.value, 6))
            self.assertEqual(results, [10.0, 10.0, 10.0, 10.0])
        finally:
            lib.hcclCommDestroy(comm)

    def test_unimplemented_wrappers_return_not_supported(self):
        self.bridge.load_library()
        lib = self.bridge._lib
        comm = ctypes.c_void_p()
        device_ids = (ctypes.c_int32 * 2)(0, 1)
        self.assertEqual(lib.hcclCommInit(ctypes.byref(comm), 2, device_ids), 0)
        try:
            send = ctypes.c_float(1.0)
            recv = ctypes.c_float(-123.0)
            rc = lib.hcclAllGather(
                ctypes.byref(send), ctypes.byref(recv), 1, HCCL_FP32, comm,
            )
            self.assertEqual(rc, HCCL_ERR_NOT_SUPPORTED)
            self.assertEqual(recv.value, -123.0)

            rc = lib.hcclReduceScatter(
                ctypes.byref(send), ctypes.byref(recv),
                1, HCCL_FP32, HCCL_SUM, comm,
            )
            self.assertEqual(rc, HCCL_ERR_NOT_SUPPORTED)
            self.assertEqual(recv.value, -123.0)

            rc = lib.hcclBroadcast(
                ctypes.byref(send), ctypes.byref(recv),
                1, HCCL_FP32, 0, comm,
            )
            self.assertEqual(rc, HCCL_ERR_NOT_SUPPORTED)
            self.assertEqual(recv.value, -123.0)
        finally:
            lib.hcclCommDestroy(comm)

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
