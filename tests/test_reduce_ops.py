"""FP32 ReduceOp correctness tests using independent Python references."""

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
)
from plugin.hccl_api import (
    HcclAllReduceReference,
    HcclReduceScatterReference,
)


def _reduce_reference(values, op):
    values = [float(value) for value in values]
    if op == HCCL_SUM:
        result = 0.0
        for value in values:
            result += value
        return result
    if op == HCCL_PROD:
        result = 1.0
        for value in values:
            result *= value
        return result
    if op == HCCL_MAX:
        result = values[0]
        for value in values[1:]:
            if value > result:
                result = value
        return result
    if op == HCCL_MIN:
        result = values[0]
        for value in values[1:]:
            if value < result:
                result = value
        return result
    raise ValueError(f"unsupported op: {op}")


def _assert_float_lists_equal(testcase, actual, expected):
    testcase.assertEqual(len(actual), len(expected))
    for a, e in zip(actual, expected):
        if math.isnan(e):
            testcase.assertTrue(math.isnan(a))
        elif math.isinf(e):
            testcase.assertTrue(math.isinf(a))
            testcase.assertEqual(math.copysign(1.0, a), math.copysign(1.0, e))
        else:
            testcase.assertAlmostEqual(a, e, places=5)


def _send_data(ranks, count):
    data = []
    for src in range(ranks):
        src_row = []
        for dst in range(ranks):
            shard = []
            for elem in range(count):
                shard.append(float((src - 2) * (dst + 1)) + elem * 0.5)
            src_row.append(shard)
        data.append(src_row)
    data[1][2][0] = 0.0
    return data


class TestFp32ReduceOps(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ExecutionEngine()
        cls.engine.load_library()

    def test_allreduce_reference_matches_independent_reference(self):
        values = [1.5, -2.0, 0.0, 4.0]
        for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
            with self.subTest(op=op):
                expected = [_reduce_reference(values, op)] * len(values)
                self.assertEqual(HcclAllReduceReference(values, op=op), expected)

    def test_allreduce_multi_element_reference_matches_independent_reference(self):
        matrix = [
            [1.5, -2.0, 0.0],
            [4.0, 0.5, -1.0],
            [-3.0, 2.0, 7.0],
            [0.25, -8.0, 3.0],
        ]
        for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
            with self.subTest(op=op):
                reduced = []
                for elem in range(3):
                    reduced.append(
                        _reduce_reference([row[elem] for row in matrix], op)
                    )
                self.assertEqual(
                    HcclAllReduceReference(matrix, op=op),
                    [reduced for _ in matrix],
                )

    def test_reducescatter_reference_matches_independent_reference(self):
        send_data = _send_data(4, 2)
        for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
            with self.subTest(op=op):
                expected = []
                for dst in range(4):
                    row = []
                    for elem in range(2):
                        row.append(
                            _reduce_reference(
                                [send_data[src][dst][elem] for src in range(4)],
                                op,
                            )
                        )
                    expected.append(row)
                self.assertEqual(
                    HcclReduceScatterReference(send_data, op=op),
                    expected,
                )

    def test_allreduce_actual_dll_reduce_ops(self):
        values = [1.5, -2.0, 0.0, 4.0]
        for algorithm in [
            "Wrapper",
            "Ring",
            "Butterfly",
            "Mesh",
            "NHR",
            "Fat-Tree",
        ]:
            for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
                with self.subTest(algorithm=algorithm, op=op):
                    result = self.engine.execute_allreduce_data(
                        values, algorithm=algorithm, op=op,
                    )
                    self.assertEqual(result["status"], "success")
                    expected = HcclAllReduceReference(values, op=op)
                    _assert_float_lists_equal(self, result["result"], expected)

    def test_allreduce_actual_dll_multi_element_reduce_ops(self):
        values = [
            [1.5, -2.0, 0.0],
            [4.0, 0.5, -1.0],
            [-3.0, 2.0, 7.0],
            [0.25, -8.0, 3.0],
        ]
        for algorithm in [
            "Wrapper",
            "Ring",
            "Butterfly",
            "Mesh",
            "NHR",
            "Fat-Tree",
        ]:
            for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
                with self.subTest(algorithm=algorithm, op=op):
                    result = self.engine.execute_allreduce_data(
                        values, algorithm=algorithm, op=op,
                    )
                    self.assertEqual(result["status"], "success")
                    expected = HcclAllReduceReference(values, op=op)
                    for actual_row, expected_row in zip(result["result"], expected):
                        _assert_float_lists_equal(self, actual_row, expected_row)

    def test_allreduce_v1b_required_rank_count_matrix(self):
        for ranks in [1, 2, 4, 8, 16]:
            for count in [1, 3, 17, 256]:
                values = [
                    [
                        float((rank - 3) * (elem + 1)) + 0.25 * elem
                        for elem in range(count)
                    ]
                    for rank in range(ranks)
                ]
                for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
                    with self.subTest(ranks=ranks, count=count, op=op):
                        result = self.engine.execute_allreduce_data(
                            values, algorithm="Wrapper", op=op,
                        )
                        self.assertEqual(result["status"], "success")
                        expected = HcclAllReduceReference(values, op=op)
                        for actual_row, expected_row in zip(result["result"], expected):
                            _assert_float_lists_equal(self, actual_row, expected_row)

    def test_allreduce_fp16_bf16_v1b_minimum_coverage(self):
        tolerances = {HCCL_FP16: 1.0e-3, HCCL_BF16: 2.0e-2}
        for data_type in [HCCL_FP16, HCCL_BF16]:
            for ranks in [2, 4]:
                for count in [1, 3, 17]:
                    values = [
                        [float(rank + elem) / 3.0 for elem in range(count)]
                        for rank in range(ranks)
                    ]
                    with self.subTest(data_type=data_type, ranks=ranks, count=count):
                        result = self.engine.execute_allreduce_data(
                            values, algorithm="Wrapper",
                            op=HCCL_SUM, data_type=data_type,
                        )
                        self.assertEqual(result["status"], "success")
                        expected = HcclAllReduceReference(
                            values, op=HCCL_SUM, data_type=data_type,
                        )
                        for actual_row, expected_row in zip(result["result"], expected):
                            for actual, reference in zip(actual_row, expected_row):
                                self.assertLessEqual(
                                    abs(actual - reference),
                                    tolerances[data_type],
                                )

    def test_reducescatter_actual_dll_reduce_ops(self):
        send_data = _send_data(4, 2)
        for op in [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]:
            with self.subTest(op=op):
                result = self.engine.execute_reducescatter(send_data, op=op)
                self.assertEqual(result["status"], "success")
                expected = HcclReduceScatterReference(send_data, op=op)
                for actual_row, expected_row in zip(result["result"], expected):
                    _assert_float_lists_equal(self, actual_row, expected_row)

    def test_inf_nan_and_overflow_behavior(self):
        inf_values = [float("inf"), 1.0, 2.0, 3.0]
        inf_result = self.engine.execute_allreduce_data(inf_values, op=HCCL_SUM)
        self.assertEqual(inf_result["status"], "success")
        self.assertTrue(all(math.isinf(value) for value in inf_result["result"]))

        nan_values = [float("nan"), 1.0, 2.0, 3.0]
        nan_result = self.engine.execute_allreduce_data(nan_values, op=HCCL_SUM)
        self.assertEqual(nan_result["status"], "success")
        self.assertTrue(all(math.isnan(value) for value in nan_result["result"]))

        overflow_values = [1.0e20, 1.0e20, 2.0, 1.0]
        overflow_result = self.engine.execute_allreduce_data(
            overflow_values, op=HCCL_PROD,
        )
        self.assertEqual(overflow_result["status"], "success")
        self.assertTrue(all(math.isinf(value) for value in overflow_result["result"]))


if __name__ == "__main__":
    unittest.main()
