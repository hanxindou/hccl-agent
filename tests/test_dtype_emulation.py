"""FP16/BF16 CPU software emulation tests using the real plugin DLL."""

import math
import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.execution_engine import (
    HCCL_BF16,
    HCCL_FP16,
    HCCL_MAX,
    HCCL_MIN,
    HCCL_PROD,
    HCCL_SUM,
    ExecutionEngine,
    roundtrip_dtype_value,
)
from plugin.hccl_api import (
    HcclAllGatherReference,
    HcclAllReduceReference,
    HcclReduceScatterReference,
)


def _assert_close_or_same_special(testcase, actual, expected, tolerance):
    if math.isnan(expected):
        testcase.assertTrue(math.isnan(actual))
    elif math.isinf(expected):
        testcase.assertTrue(math.isinf(actual))
        testcase.assertEqual(math.copysign(1.0, actual), math.copysign(1.0, expected))
    else:
        testcase.assertLessEqual(abs(actual - expected), tolerance)


class TestDtypeEmulation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ExecutionEngine()
        cls.engine.load_library()

    def test_roundtrip_boundaries(self):
        values = [
            0.0,
            -0.0,
            1.5,
            -2.25,
            65504.0,
            1.0e-8,
            float("inf"),
            float("-inf"),
            float("nan"),
        ]
        for data_type in [HCCL_FP16, HCCL_BF16]:
            for value in values:
                with self.subTest(data_type=data_type, value=value):
                    result = roundtrip_dtype_value(value, data_type)
                    if math.isnan(value):
                        self.assertTrue(math.isnan(result))
                    elif math.isinf(value):
                        self.assertTrue(math.isinf(result))

    def test_allreduce_fp16_bf16_reduce_ops(self):
        values = [1.5, -2.0, 0.0, 4.0]
        tolerances = {HCCL_FP16: 1.0e-3, HCCL_BF16: 2.0e-2}
        for data_type in [HCCL_FP16, HCCL_BF16]:
            for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
                with self.subTest(data_type=data_type, op=op):
                    result = self.engine.execute_allreduce_data(
                        values, op=op, data_type=data_type,
                    )
                    self.assertEqual(result["status"], "success")
                    expected = HcclAllReduceReference(
                        values, op=op, data_type=data_type,
                    )
                    for actual, reference in zip(result["result"], expected):
                        _assert_close_or_same_special(
                            self, actual, reference, tolerances[data_type],
                        )

    def test_allgather_fp16_bf16(self):
        send_data = [[0.5, -2.25], [3.75, 0.0], [65504.0, 1.0], [2.0, -4.0]]
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

    def test_reducescatter_fp16_bf16_reduce_ops(self):
        send_data = [
            [
                [float((src - 2) * (dst + 1)) + elem * 0.5
                 for elem in range(2)]
                for dst in range(4)
            ]
            for src in range(4)
        ]
        send_data[1][2][0] = 0.0
        tolerances = {HCCL_FP16: 1.0e-3, HCCL_BF16: 2.0e-2}
        for data_type in [HCCL_FP16, HCCL_BF16]:
            for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
                with self.subTest(data_type=data_type, op=op):
                    result = self.engine.execute_reducescatter(
                        send_data, data_type=data_type, op=op,
                    )
                    self.assertEqual(result["status"], "success")
                    expected = HcclReduceScatterReference(
                        send_data, op=op, data_type=data_type,
                    )
                    for actual_row, expected_row in zip(result["result"], expected):
                        for actual, reference in zip(actual_row, expected_row):
                            _assert_close_or_same_special(
                                self, actual, reference, tolerances[data_type],
                            )

    def test_inf_nan_and_overflow(self):
        for data_type in [HCCL_FP16, HCCL_BF16]:
            with self.subTest(data_type=data_type, case="inf"):
                result = self.engine.execute_allreduce_data(
                    [float("inf"), 1.0, 2.0, 3.0],
                    op=HCCL_SUM,
                    data_type=data_type,
                )
                self.assertEqual(result["status"], "success")
                self.assertTrue(all(math.isinf(value) for value in result["result"]))

            with self.subTest(data_type=data_type, case="nan"):
                result = self.engine.execute_allreduce_data(
                    [float("nan"), 1.0, 2.0, 3.0],
                    op=HCCL_SUM,
                    data_type=data_type,
                )
                self.assertEqual(result["status"], "success")
                self.assertTrue(all(math.isnan(value) for value in result["result"]))

            with self.subTest(data_type=data_type, case="overflow"):
                result = self.engine.execute_allreduce_data(
                    [1.0e20, 1.0e20, 2.0, 1.0],
                    op=HCCL_PROD,
                    data_type=data_type,
                )
                self.assertEqual(result["status"], "success")
                self.assertTrue(all(math.isinf(value) for value in result["result"]))


if __name__ == "__main__":
    unittest.main()
