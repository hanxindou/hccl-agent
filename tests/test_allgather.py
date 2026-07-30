"""AllGather CPU_SIM data correctness tests using the real plugin DLL."""

import ctypes
import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.execution_engine import (
    HCCL_BF16,
    HCCL_ERR_INVALID_ARG,
    HCCL_ERR_NOT_SUPPORTED,
    HCCL_FP16,
    HCCL_FP32,
    ExecutionEngine,
)
from plugin.hccl_api import HcclAllGatherReference


def _send_data(ranks, count):
    return [
        [float(rank * 100 + elem + 1) for elem in range(count)]
        for rank in range(ranks)
    ]


class TestAllGatherDataCorrectness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ExecutionEngine()
        cls.engine.load_library()

    def assert_allgather_matches_reference(self, ranks, count, algorithm):
        send_data = _send_data(ranks, count)
        result = self.engine.execute_allgather(send_data, algorithm=algorithm)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["return_code"], 0)
        self.assertEqual(result["result"], HcclAllGatherReference(send_data))

    def test_actual_library_path_is_loaded(self):
        self.assertTrue(os.path.exists(self.engine.lib_path))
        self.assertIsNotNone(self.engine._lib)

    def test_wrapper_uses_real_hccl_allgather(self):
        self.assert_allgather_matches_reference(4, 2, "Wrapper")

    def test_ring_count_1_for_required_ranks(self):
        for ranks in [2, 4, 8, 16]:
            with self.subTest(ranks=ranks):
                self.assert_allgather_matches_reference(ranks, 1, "Ring")

    def test_ring_count_gt_1_for_required_ranks(self):
        for ranks, count in [(4, 2), (8, 3), (16, 2)]:
            with self.subTest(ranks=ranks, count=count):
                self.assert_allgather_matches_reference(ranks, count, "Ring")

    def test_butterfly_count_1_for_required_ranks(self):
        for ranks in [2, 4, 8, 16]:
            with self.subTest(ranks=ranks):
                self.assert_allgather_matches_reference(ranks, 1, "Butterfly")

    def test_butterfly_count_gt_1_for_required_ranks(self):
        for ranks, count in [(4, 2), (8, 3), (16, 2)]:
            with self.subTest(ranks=ranks, count=count):
                self.assert_allgather_matches_reference(ranks, count, "Butterfly")

    def test_one_rank_layout(self):
        for algorithm in ["Ring", "Butterfly", "Wrapper"]:
            with self.subTest(algorithm=algorithm):
                self.assert_allgather_matches_reference(1, 1, algorithm)

    def test_ring_and_butterfly_results_match(self):
        send_data = _send_data(8, 3)
        ring = self.engine.execute_allgather(send_data, algorithm="Ring")
        butterfly = self.engine.execute_allgather(send_data, algorithm="Butterfly")
        self.assertEqual(ring["status"], "success")
        self.assertEqual(butterfly["status"], "success")
        self.assertEqual(ring["result"], butterfly["result"])

    def test_fp16_and_bf16_match_reference(self):
        send_data = _send_data(4, 1)
        for data_type in [HCCL_FP16, HCCL_BF16]:
            with self.subTest(data_type=data_type):
                result = self.engine.execute_allgather(
                    send_data, algorithm="Wrapper", data_type=data_type,
                )
                self.assertEqual(result["status"], "success")
                self.assertEqual(
                    result["result"],
                    HcclAllGatherReference(send_data, data_type=data_type),
                )

    def test_butterfly_rejects_non_power_of_two(self):
        result = self.engine.execute_allgather(_send_data(3, 1), algorithm="Butterfly")
        self.assertEqual(result["status"], "not_supported")
        self.assertEqual(result["return_code"], HCCL_ERR_NOT_SUPPORTED)

    def test_invalid_python_input_is_reported(self):
        self.assertEqual(
            self.engine.execute_allgather([], algorithm="Wrapper")["return_code"],
            HCCL_ERR_INVALID_ARG,
        )
        self.assertEqual(
            self.engine.execute_allgather([[1.0], [2.0, 3.0]], algorithm="Wrapper")
            ["return_code"],
            HCCL_ERR_INVALID_ARG,
        )

    def test_null_arguments_return_invalid_arg(self):
        lib = self.engine._lib
        comm = ctypes.c_void_p()
        ids = (ctypes.c_int32 * 4)(0, 1, 2, 3)
        self.assertEqual(lib.hcclCommInit(ctypes.byref(comm), 4, ids), 0)
        try:
            send = (ctypes.c_float * 4)(1.0, 2.0, 3.0, 4.0)
            recv = (ctypes.c_float * 16)()
            self.assertEqual(
                lib.hcclAllGather(None, recv, 1, HCCL_FP32, comm),
                HCCL_ERR_INVALID_ARG,
            )
            self.assertEqual(
                lib.hcclAllGather(send, None, 1, HCCL_FP32, comm),
                HCCL_ERR_INVALID_ARG,
            )
            self.assertEqual(
                lib.hcclAllGather(send, recv, 0, HCCL_FP32, comm),
                HCCL_ERR_INVALID_ARG,
            )
            self.assertEqual(
                lib.hcclAllGather(send, recv, 1, HCCL_FP32, None),
                HCCL_ERR_INVALID_ARG,
            )
        finally:
            lib.hcclCommDestroy(comm)


if __name__ == "__main__":
    unittest.main()
