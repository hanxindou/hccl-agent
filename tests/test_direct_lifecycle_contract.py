"""Static G2-F-4 contract checks; runtime execution remains unavailable."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "hcccl" / "direct" / "include" / "hccl_direct_adapter.h").read_text(encoding="utf-8")
SOURCE = (ROOT / "hcccl" / "direct" / "src" / "hccl_direct_adapter.cpp").read_text(encoding="utf-8")


class TestDirectLifecycleContract(unittest.TestCase):
    def test_explicit_lifecycle_states_and_ownership_abi_exist(self):
        for state in ("CREATED", "CONFIGURED", "PREFLIGHT_CHECKED", "NO_DEVICE_EXPECTED",
                      "RUNTIME_READY", "DEVICE_READY", "CONTEXT_READY", "STREAM_READY",
                      "COMM_READY", "BUFFERS_READY", "COLLECTIVE_SUBMITTED", "SYNCHRONIZED",
                      "COMPLETED", "CLEANING", "DESTROYED", "FAILED"):
            self.assertIn(f"HCCL_DIRECT_SESSION_{state}", HEADER)
        for function in ("session_configure", "session_preflight", "session_request_execution",
                         "session_run_model", "session_model_acquire_lease", "session_model_cleanup",
                         "calculate_capacity", "session_verify_owner"):
            self.assertIn(f"hccl_direct_{function}", HEADER)

    def test_adapter_has_no_reachable_official_call_expression(self):
        for function in ("aclInit", "aclFinalize", "aclrtSetDevice", "aclrtCreateStream",
                         "aclrtMalloc", "HcclCommInitClusterInfo", "HcclAllReduce",
                         "HcclAllGather", "HcclReduceScatter"):
            self.assertNotIn(f"{function}(", SOURCE)
        self.assertIn("deterministic lifecycle model", SOURCE)
        self.assertIn("catch (...)", SOURCE)

    def test_capacity_and_cleanup_contract_are_explicit(self):
        self.assertIn("kAdapterMaxBytes", SOURCE)
        self.assertIn("HCCL_DIRECT_FAILURE_CLEANUP_RUNTIME_LEASE", HEADER)
        self.assertIn("HCCL_DIRECT_CLEANUP_RECV_BUFFER", HEADER)
        self.assertIn("HCCL_DIRECT_STATUS_OWNERSHIP_VIOLATION", HEADER)


if __name__ == "__main__":
    unittest.main()
