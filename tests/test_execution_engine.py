"""Tests for ExecutionEngine — direct algorithm execution via ctypes."""

import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.execution_engine import (
    HCCL_MAX,
    HCCL_MIN,
    HCCL_PROD,
    HCCL_SUM,
    ExecutionEngine,
)
from plugin.hccl_api import (
    HcclAllGatherReference,
    HcclAllReduceReference,
    HcclReduceScatterReference,
)


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

    def test_allreduce_data_reduce_ops(self):
        data = [1.5, -2.0, 0.0, 4.0]
        for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
            with self.subTest(op=op):
                result = self.engine.execute_allreduce_data(data, op=op)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["result"], HcclAllReduceReference(data, op=op))

    # ---- unknown algorithm ----

    def test_unknown_algorithm(self):
        result = self.engine.execute_algorithm("UnknownAlgo", [1.0])
        self.assertEqual(result["status"], "unknown_algorithm")

    # ---- empty input ----

    def test_empty_input(self):
        result = self.engine.execute_algorithm("Ring AllReduce", [])
        self.assertEqual(result["status"], "invalid_input")

    # ---- AllGather data execution ----

    def test_allgather_wrapper_4_ranks_count_2(self):
        send_data = [[float(rank * 100 + elem + 1) for elem in range(2)]
                     for rank in range(4)]
        result = self.engine.execute_allgather(send_data, algorithm="Wrapper")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], HcclAllGatherReference(send_data))

    def test_allgather_butterfly_8_ranks_count_3(self):
        send_data = [[float(rank * 100 + elem + 1) for elem in range(3)]
                     for rank in range(8)]
        result = self.engine.execute_allgather(send_data, algorithm="Butterfly")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], HcclAllGatherReference(send_data))

    # ---- ReduceScatter data execution ----

    def test_reducescatter_wrapper_4_ranks_count_2(self):
        send_data = [
            [
                [float(src * 1000 + dst * 100 + elem + 1)
                 for elem in range(2)]
                for dst in range(4)
            ]
            for src in range(4)
        ]
        result = self.engine.execute_reducescatter(send_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], HcclReduceScatterReference(send_data))

    def test_reducescatter_wrapper_8_ranks_count_3(self):
        send_data = [
            [
                [float(src * 1000 + dst * 100 + elem + 1)
                 for elem in range(3)]
                for dst in range(8)
            ]
            for src in range(8)
        ]
        result = self.engine.execute_reducescatter(send_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["result"], HcclReduceScatterReference(send_data))

    def test_reducescatter_reduce_ops(self):
        send_data = [
            [
                [float((src - 2) * (dst + 1)) + elem * 0.5
                 for elem in range(2)]
                for dst in range(4)
            ]
            for src in range(4)
        ]
        send_data[1][2][0] = 0.0
        for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
            with self.subTest(op=op):
                result = self.engine.execute_reducescatter(send_data, op=op)
                self.assertEqual(result["status"], "success")
                self.assertEqual(
                    result["result"],
                    HcclReduceScatterReference(send_data, op=op),
                )


if __name__ == "__main__":
    unittest.main()
