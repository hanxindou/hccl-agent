"""G2-F-3 tests for pure no-device direct-backend preflight and guard."""

import importlib
import ast
import unittest
from pathlib import Path


class TestDirectApiBackend(unittest.TestCase):
    def setUp(self):
        self.backend = importlib.import_module("plugin.direct_api_backend")

    def test_windows_safe_import_has_no_runtime_loader(self):
        source = Path(self.backend.__file__).read_text(encoding="utf-8")
        imports = {
            alias.name
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) and node.module
        )
        self.assertNotIn("ctypes", imports)
        self.assertNotIn("plugin.hccl_vm_runner", imports)
        self.assertEqual(self.backend.RUNTIME_API_CALLS, ())

    def test_no_device_preflight_has_required_false_claims(self):
        result = self.backend.diagnose_no_device({
            "npu_smi_found": False, "device_nodes": (), "driver_indicators": (),
        })
        self.assertEqual(result["backend"], "ASCEND_HCCL_DIRECT")
        self.assertEqual(result["status"], "NO_DEVICE_EXPECTED")
        for field in ("direct_hccl_api_call", "real_ascend_npu_validated", "runtime_initialized",
                      "device_opened", "context_created", "stream_created", "communicator_created",
                      "device_buffer_allocated", "collective_executed"):
            self.assertFalse(result[field])
        self.assertEqual(result["runtime_api_calls"], [])

    def test_collectives_and_lifecycle_are_rejected_before_runtime(self):
        for operation in ("acl_init", "create_stream", "all_reduce", "all_gather", "reduce_scatter"):
            with self.assertRaises(self.backend.DirectApiRuntimeRejected):
                self.backend.reject_runtime_request(operation)
        self.assertEqual(self.backend.RUNTIME_API_CALLS, ())
