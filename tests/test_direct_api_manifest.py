"""Static tests for the G2-F-1 direct HCCL API ABI manifest."""

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "hcccl" / "direct" / "tools"
MANIFEST_PATH = ROOT / "hcccl" / "direct" / "manifest" / "cann_hccl_9.1.0.json"
sys.path.insert(0, str(TOOL_DIR))

from verify_manifest import load_manifest  # noqa: E402


class TestDirectApiManifest(unittest.TestCase):
    """Keep the direct API contract machine-readable and explicitly non-runtime."""

    def setUp(self):
        self.manifest = load_manifest(MANIFEST_PATH)

    def test_manifest_freezes_cann_and_official_repositories(self):
        self.assertEqual(self.manifest["cann"]["version"], "9.1.0")
        self.assertEqual(self.manifest["official_repositories"]["hcomm"]["tracked_worktree"], "clean")
        self.assertEqual(self.manifest["official_repositories"]["hccl"]["tracked_worktree"], "clean")

    def test_manifest_has_all_direct_libraries_and_symbols(self):
        libraries = {entry["name"]: entry for entry in self.manifest["libraries"]}
        self.assertEqual(set(libraries), {"hccl", "hcomm", "acl_rt"})
        self.assertEqual(libraries["hccl"]["soname"], "libhccl.so")
        self.assertTrue({"HcclAllReduce", "HcclAllGather", "HcclReduceScatter"}.issubset(libraries["hccl"]["symbols"]))
        self.assertEqual(libraries["hcomm"]["soname"], "libhcomm.so")
        self.assertEqual(libraries["acl_rt"]["soname"], "libacl_rt.so")

    def test_collective_contract_records_count_semantics_and_unresolved_locality(self):
        functions = {entry["name"]: entry for entry in self.manifest["api_contract"]["functions"]}
        self.assertEqual(functions["HcclAllReduce"]["count_semantics"], "output elements per rank")
        self.assertEqual(functions["HcclAllGather"]["count_semantics"], "input elements per rank")
        self.assertEqual(functions["HcclReduceScatter"]["count_semantics"], "output elements per rank")
        self.assertEqual(self.manifest["api_contract"]["collective_buffer_locality"]["status"], "UNRESOLVED")

    def test_manifest_has_no_g2_f_1_or_f_2_callable_runtime_api(self):
        for entry in self.manifest["api_contract"]["functions"]:
            self.assertIn(entry["safety"], {"REAL_DEVICE_ONLY", "NOT_CALLABLE_IN_G2_F_1_OR_G2_F_2"})

    def test_reader_rejects_resolved_locality_claim(self):
        modified = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        modified["api_contract"]["collective_buffer_locality"]["status"] = "DEVICE"
        temp_path = ROOT / "tests" / "_invalid_direct_manifest.json"
        try:
            temp_path.write_text(json.dumps(modified), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "locality"):
                load_manifest(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
