"""Static checks for the G1 CANN/Ascend backend preparation."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


class TestG1CannBackendConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cmake_path = os.path.join(root, "hcccl", "CMakeLists.txt")
        with open(cmake_path, "r", encoding="utf-8") as handle:
            cls.cmake_text = handle.read()

    def test_backend_option_defaults_to_cpu_sim(self):
        self.assertIn('set(HCCL_BACKEND "CPU_SIM"', self.cmake_text)
        self.assertIn("CPU_SIM", self.cmake_text)
        self.assertIn("ASCEND_CANN", self.cmake_text)

    def test_ascend_cann_missing_sdk_fails_clearly(self):
        self.assertIn("HCCL_BACKEND=ASCEND_CANN requires", self.cmake_text)
        self.assertIn("hccl/hccl.h", self.cmake_text)
        self.assertIn("HCCL_CANN_ROOT", self.cmake_text)
        self.assertIn("ASCEND_HOME_PATH", self.cmake_text)
        self.assertIn("CANN_HOME", self.cmake_text)

    def test_ascend_adapter_is_marked_unverified(self):
        self.assertIn("HCCL_ASCEND_CANN_STUB_UNVERIFIED=1", self.cmake_text)
        self.assertIn("HCCL_BACKEND_ASCEND_CANN=1", self.cmake_text)


if __name__ == "__main__":
    unittest.main()
