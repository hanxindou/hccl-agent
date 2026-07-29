"""ReduceScatter CPU_SIM data correctness tests using the real plugin DLL."""

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
    HCCL_MAX,
    HCCL_MIN,
    HCCL_PROD,
    HCCL_SUM,
    ExecutionEngine,
)
from plugin.hccl_api import HcclReduceScatterReference


def _send_data(ranks, count):
    return [
        [
            [float(src * 1000 + dst * 100 + elem + 1)
             for elem in range(count)]
            for dst in range(ranks)
        ]
        for src in range(ranks)
    ]


class TestReduceScatterDataCorrectness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ExecutionEngine()
        cls.engine.load_library()

    def assert_reducescatter_matches_reference(self, ranks, count):
        send_data = _send_data(ranks, count)
        result = self.engine.execute_reducescatter(send_data)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["return_code"], 0)
        self.assertEqual(result["result"], HcclReduceScatterReference(send_data))

    def test_actual_library_path_is_loaded(self):
        self.assertTrue(os.path.exists(self.engine.lib_path))
        self.assertIsNotNone(self.engine._lib)

    def test_count_1_for_required_ranks(self):
        for ranks in [1, 4, 8, 16]:
            with self.subTest(ranks=ranks):
                self.assert_reducescatter_matches_reference(ranks, 1)

    def test_count_gt_1_for_required_ranks(self):
        for ranks, count in [(4, 2), (8, 3), (16, 2)]:
            with self.subTest(ranks=ranks, count=count):
                self.assert_reducescatter_matches_reference(ranks, count)

    def test_fp16_bf16_match_reference(self):
        send_data = _send_data(4, 1)
        for data_type in [HCCL_FP16, HCCL_BF16]:
            with self.subTest(data_type=data_type):
                result = self.engine.execute_reducescatter(
                    send_data, data_type=data_type, op=HCCL_SUM,
                )
                self.assertEqual(result["status"], "success")
                self.assertEqual(
                    result["result"],
                    HcclReduceScatterReference(
                        send_data, op=HCCL_SUM, data_type=data_type,
                    ),
                )

    def test_fp32_reduce_ops_match_reference(self):
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

    def test_invalid_python_input_is_reported(self):
        self.assertEqual(
            self.engine.execute_reducescatter([])["return_code"],
            HCCL_ERR_INVALID_ARG,
        )
        self.assertEqual(
            self.engine.execute_reducescatter([[[1.0]], [[2.0]]])
            ["return_code"],
            HCCL_ERR_INVALID_ARG,
        )
        self.assertEqual(
            self.engine.execute_reducescatter([[[1.0], [2.0]], [[3.0], []]])
            ["return_code"],
            HCCL_ERR_INVALID_ARG,
        )

    def test_two_rank_legacy_shape_is_not_supported(self):
        result = self.engine.execute_reducescatter(_send_data(2, 1))
        self.assertEqual(result["status"], "not_supported")
        self.assertEqual(result["return_code"], HCCL_ERR_NOT_SUPPORTED)


if __name__ == "__main__":
    unittest.main()
