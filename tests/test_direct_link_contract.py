"""Static G2-F-3 checks for direct official-library link isolation."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMAKE = (ROOT / "hcccl" / "CMakeLists.txt").read_text(encoding="utf-8")
LINK_SOURCE = (ROOT / "hcccl" / "direct" / "src" / "hccl_direct_link_audit.cpp").read_text(encoding="utf-8")


class TestDirectLinkContract(unittest.TestCase):
    def test_link_audit_uses_only_canonical_cann_library_directory(self):
        self.assertIn("get_filename_component(HCCL_DIRECT_CANN_REAL_ROOT", CMAKE)
        self.assertIn("x86_64-linux/lib64", CMAKE)
        self.assertIn("NO_DEFAULT_PATH", CMAKE)
        self.assertIn("add_executable(hccl_direct_link_audit", CMAKE)
        for library in ("hccl", "hcomm", "acl_rt"):
            self.assertIn(f'"${{HCCL_DIRECT_{library}_LIBRARY}}"', CMAKE)

    def test_link_artifact_references_symbols_but_never_calls_them(self):
        self.assertIn("makes no ACL/HCCL API call", LINK_SOURCE)
        for function in ("HcclAllReduce", "HcclAllGather", "HcclReduceScatter", "aclInit"):
            self.assertIn(f"&{function}", LINK_SOURCE)
            self.assertNotIn(f"{function}(", LINK_SOURCE)

    def test_build_only_adapter_is_preserved(self):
        self.assertIn("add_library(hccl_direct_adapter STATIC", CMAKE)
        self.assertNotIn("target_link_libraries(hccl_direct_adapter", CMAKE)
