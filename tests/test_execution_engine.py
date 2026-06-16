"""Tests for ExecutionEngine — direct algorithm execution via ctypes."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.execution_engine import ExecutionEngine


class TestExecutionEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ExecutionEngine()

    # ---- Ring AllReduce: 4 ranks ----

    def test_ring_allreduce_4_ranks(self):
        result = self.engine.execute_algorithm(
            "Ring AllReduce", [1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["algorithm"], "Ring AllReduce")
        self.assertEqual(
            result["result"],
            [10.0, 10.0, 10.0, 10.0],
        )

    # ---- Ring AllReduce: 8 ranks ----

    def test_ring_allreduce_8_ranks(self):
        data = [float(i) for i in range(1, 9)]  # [1..8]
        result = self.engine.execute_algorithm("Ring AllReduce", data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["result"],
            [36.0] * 8,
        )

    # ---- Butterfly AllReduce ----

    def test_butterfly_4_ranks(self):
        result = self.engine.execute_algorithm(
            "Butterfly", [1.0, 2.0, 3.0, 4.0],
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["algorithm"], "Butterfly")
        self.assertEqual(result["result"], [10.0, 10.0, 10.0, 10.0])

    def test_butterfly_8_ranks(self):
        data = [float(i) for i in range(1, 9)]
        result = self.engine.execute_algorithm("Butterfly", data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [36.0] * 8)

    # ---- NHR AllReduce ----

    def test_nhr_4_ranks(self):
        result = self.engine.execute_algorithm("NHR", [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [10.0, 10.0, 10.0, 10.0])

    def test_nhr_8_ranks(self):
        data = [float(i) for i in range(1, 9)]
        result = self.engine.execute_algorithm("NHR", data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [36.0] * 8)

    def test_nhr_16_ranks(self):
        data = [float(i) for i in range(1, 17)]
        result = self.engine.execute_algorithm("NHR", data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [136.0] * 16)

    # ---- unimplemented algorithms ----

    def test_mesh_4_ranks(self):
        result = self.engine.execute_algorithm("Mesh", [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [10.0, 10.0, 10.0, 10.0])

    def test_mesh_8_ranks(self):
        data = [float(i) for i in range(1, 9)]
        result = self.engine.execute_algorithm("Mesh", data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [36.0] * 8)

    def test_fat_tree_4_ranks(self):
        result = self.engine.execute_algorithm("Fat-Tree", [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [10.0, 10.0, 10.0, 10.0])

    def test_fat_tree_16_ranks(self):
        data = [float(i) for i in range(1, 17)]
        result = self.engine.execute_algorithm("Fat-Tree", data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], [136.0] * 16)

    # ---- unknown algorithm ----

    def test_unknown_algorithm(self):
        result = self.engine.execute_algorithm("UnknownAlgo", [1.0])
        self.assertEqual(result["status"], "unknown_algorithm")

    # ---- empty input ----

    def test_empty_input(self):
        result = self.engine.execute_algorithm("Ring AllReduce", [])
        self.assertEqual(result["status"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
