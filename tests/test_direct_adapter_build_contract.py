"""Static G2-F-2 checks for direct-adapter isolation and build-only boundaries."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CMAKE = (ROOT / "hcccl" / "CMakeLists.txt").read_text(encoding="utf-8")
HEADER = (ROOT / "hcccl" / "direct" / "include" / "hccl_direct_adapter.h").read_text(encoding="utf-8")
SOURCE = (ROOT / "hcccl" / "direct" / "src" / "hccl_direct_adapter.cpp").read_text(encoding="utf-8")


class TestDirectAdapterBuildContract(unittest.TestCase):
    """Ensure F2 remains a separate, compile-only implementation boundary."""

    def test_feature_is_off_by_default_and_target_is_static(self):
        self.assertIn("option(HCCL_ENABLE_ASCEND_HCCL_DIRECT", CMAKE)
        self.assertIn("OFF)", CMAKE)
        self.assertIn("add_library(hccl_direct_adapter STATIC", CMAKE)
        self.assertNotIn("target_link_libraries(hccl_direct_adapter", CMAKE)

    def test_cpu_sim_target_stays_separate(self):
        self.assertIn("add_library(hccl_plugin SHARED ${SOURCES})", CMAKE)
        self.assertIn("HCCL_BACKEND_CPU_SIM=1", CMAKE)
        self.assertIn("HCCL_PLUGIN_PATH", (ROOT / "plugin" / "hccl_bridge.py").read_text(encoding="utf-8"))

    def test_c_abi_is_independent_of_cpu_sim_names(self):
        self.assertIn("typedef struct hccl_direct_session hccl_direct_session_t", HEADER)
        self.assertIn('extern "C"', HEADER)
        for cpu_symbol in ("hcclCommInit", "hcclSetRank", "hcclAllReduce", "hcclAllGather", "hcclReduceScatter"):
            self.assertNotIn(cpu_symbol, HEADER)

    def test_source_performs_signature_checks_but_no_official_api_call(self):
        for function in (
            "HcclAllReduce", "HcclAllGather", "HcclReduceScatter", "HcclCommInitClusterInfo",
            "aclInit", "aclrtSetDevice", "aclrtCreateContext", "aclrtCreateStream", "aclrtMalloc",
        ):
            self.assertIn(f"decltype(&{function})", SOURCE)
            self.assertNotIn(f"{function}(", SOURCE)
        self.assertIn("catch (...)", SOURCE)
        self.assertIn("HCCL_DIRECT_STATUS_BUILD_ONLY", SOURCE)


if __name__ == "__main__":
    unittest.main()
