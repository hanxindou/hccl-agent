"""Deterministic randomized collective correctness tests.

The reference path is pure Python and does not call the C plugin. The actual
path goes through ctypes and the library selected by HCCL_PLUGIN_PATH.
"""

import math
import os
import random
import sys
import unittest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."),
)

from plugin.execution_engine import (
    HCCL_BF16,
    HCCL_FP16,
    HCCL_FP32,
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


SEEDS = [20260730, 424242, 13371337]
CASES_PER_SEED = 20

DTYPE_NAMES = {
    HCCL_FP32: "FP32",
    HCCL_FP16: "FP16",
    HCCL_BF16: "BF16",
}
REDUCE_OP_NAMES = {
    HCCL_SUM: "SUM",
    HCCL_PROD: "PROD",
    HCCL_MAX: "MAX",
    HCCL_MIN: "MIN",
    None: "N/A",
}


def _dtype_tolerance(data_type):
    if data_type == HCCL_FP16:
        return 1.0e-3
    if data_type == HCCL_BF16:
        return 2.0e-2
    return 1.0e-5


def _random_value(rng, op):
    if op == HCCL_PROD:
        value = rng.uniform(-1.5, 1.5)
    else:
        value = rng.uniform(-4.0, 4.0)
    if rng.random() < 0.12:
        value = 0.0
    if rng.random() < 0.10:
        value = rng.choice([-1.0, 1.0, 2.0, -2.0])
    if rng.random() < 0.08:
        value = rng.choice([1.0e-3, -1.0e-3, 3.5, -3.5])
    return float(value)


def _allreduce_data(rng, ranks, count, op):
    return [
        [_random_value(rng, op) for _ in range(count)]
        for _ in range(ranks)
    ]


def _allgather_data(rng, ranks, count):
    return [
        [_random_value(rng, None) for _ in range(count)]
        for _ in range(ranks)
    ]


def _reducescatter_data(rng, ranks, count, op):
    return [
        [
            [_random_value(rng, op) for _ in range(count)]
            for _ in range(ranks)
        ]
        for _ in range(ranks)
    ]


def _mandatory_case(case_index):
    cases = [
        ("AllReduce", 1, 1, HCCL_FP32, HCCL_SUM),
        ("AllReduce", 2, 3, HCCL_FP32, HCCL_PROD),
        ("AllReduce", 4, 17, HCCL_FP16, HCCL_SUM),
        ("AllReduce", 8, 7, HCCL_BF16, HCCL_SUM),
        ("AllReduce", 16, 32, HCCL_FP32, HCCL_MIN),
        ("AllReduce", 4, 64, HCCL_FP32, HCCL_MAX),
        ("AllGather", 2, 32, HCCL_FP32, None),
        ("AllGather", 4, 3, HCCL_FP16, None),
        ("AllGather", 8, 17, HCCL_BF16, None),
        ("ReduceScatter", 2, 3, HCCL_FP32, HCCL_MAX),
        ("ReduceScatter", 4, 7, HCCL_BF16, HCCL_PROD),
        ("ReduceScatter", 16, 2, HCCL_FP32, HCCL_MIN),
        ("ReduceScatter", 8, 1, HCCL_FP16, HCCL_SUM),
    ]
    if case_index < len(cases):
        return cases[case_index]
    return None


def _random_case(rng):
    primitive = rng.choice(["AllReduce", "AllGather", "ReduceScatter"])
    ranks = rng.choice([1, 2, 4, 8, 16])
    count = rng.choice([1, 2, 3, 7, 17, 32, 64])
    data_type = rng.choice([HCCL_FP32, HCCL_FP16, HCCL_BF16])
    op = None if primitive == "AllGather" else rng.choice(
        [HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN]
    )
    if primitive in {"AllGather", "ReduceScatter"} and ranks >= 8 and count > 17:
        count = 17
    if data_type in {HCCL_FP16, HCCL_BF16} and op != HCCL_SUM:
        op = rng.choice([HCCL_SUM, op])
    return primitive, ranks, count, data_type, op


def _iter_cases(seed):
    rng = random.Random(seed)
    for case_index in range(CASES_PER_SEED):
        case = _mandatory_case(case_index)
        if case is None:
            case = _random_case(rng)
        primitive, ranks, count, data_type, op = case
        if primitive == "AllReduce":
            payload = _allreduce_data(rng, ranks, count, op)
        elif primitive == "AllGather":
            payload = _allgather_data(rng, ranks, count)
        else:
            payload = _reducescatter_data(rng, ranks, count, op)
        yield {
            "seed": seed,
            "case_index": case_index,
            "primitive": primitive,
            "rank_count": ranks,
            "count": count,
            "dtype": data_type,
            "reduce_op": op,
            "payload": payload,
        }


def _flatten(values):
    if isinstance(values, (list, tuple)):
        flattened = []
        for item in values:
            flattened.extend(_flatten(item))
        return flattened
    return [float(values)]


def _max_abs_error(actual, expected):
    max_error = 0.0
    for actual_value, expected_value in zip(_flatten(actual), _flatten(expected)):
        if math.isnan(expected_value) and math.isnan(actual_value):
            continue
        if math.isinf(expected_value) and math.isinf(actual_value):
            continue
        max_error = max(max_error, abs(actual_value - expected_value))
    return max_error


def _summary(values, limit=8):
    flattened = _flatten(values)
    preview = ", ".join(f"{value:.6g}" for value in flattened[:limit])
    if len(flattened) > limit:
        preview += ", ..."
    return f"len={len(flattened)} [{preview}]"


def _failure_message(case, actual, expected):
    return (
        "seed={seed} case_index={case_index} primitive={primitive} "
        "rank_count={rank_count} count={count} dtype={dtype} "
        "reduce_op={reduce_op} input={input_summary} expected={expected} "
        "actual={actual} max_abs_error={max_abs_error}"
    ).format(
        seed=case["seed"],
        case_index=case["case_index"],
        primitive=case["primitive"],
        rank_count=case["rank_count"],
        count=case["count"],
        dtype=DTYPE_NAMES[case["dtype"]],
        reduce_op=REDUCE_OP_NAMES[case["reduce_op"]],
        input_summary=_summary(case["payload"]),
        expected=_summary(expected),
        actual=_summary(actual),
        max_abs_error=_max_abs_error(actual, expected),
    )


def _assert_nested_close(testcase, actual, expected, tolerance, case):
    actual_flat = _flatten(actual)
    expected_flat = _flatten(expected)
    testcase.assertEqual(
        len(actual_flat),
        len(expected_flat),
        _failure_message(case, actual, expected),
    )
    for actual_value, expected_value in zip(actual_flat, expected_flat):
        message = _failure_message(case, actual, expected)
        if math.isnan(expected_value):
            testcase.assertTrue(math.isnan(actual_value), message)
        elif math.isinf(expected_value):
            testcase.assertTrue(math.isinf(actual_value), message)
            testcase.assertEqual(
                math.copysign(1.0, actual_value),
                math.copysign(1.0, expected_value),
                message,
            )
        else:
            testcase.assertLessEqual(
                abs(actual_value - expected_value),
                tolerance,
                message,
            )


class TestRandomizedCollectiveCorrectness(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ExecutionEngine()
        cls.engine.load_library()

    def test_fixed_seed_randomized_collectives(self):
        seeds = SEEDS
        if os.environ.get("HCCL_RANDOM_SEED"):
            seeds = [int(os.environ["HCCL_RANDOM_SEED"])]
        case_filter = os.environ.get("HCCL_RANDOM_CASE")
        case_filter = int(case_filter) if case_filter is not None else None

        coverage = {
            "primitive": set(),
            "rank": set(),
            "count": set(),
            "dtype": set(),
            "reduce_op": set(),
        }
        executed = 0

        for seed in seeds:
            for case in _iter_cases(seed):
                if case_filter is not None and case["case_index"] != case_filter:
                    continue
                with self.subTest(seed=seed, case_index=case["case_index"]):
                    actual, expected = self._execute_case(case)
                    tolerance = _dtype_tolerance(case["dtype"])
                    _assert_nested_close(self, actual, expected, tolerance, case)
                    coverage["primitive"].add(case["primitive"])
                    coverage["rank"].add(case["rank_count"])
                    coverage["count"].add(case["count"])
                    coverage["dtype"].add(case["dtype"])
                    if case["reduce_op"] is not None:
                        coverage["reduce_op"].add(case["reduce_op"])
                    executed += 1

        if case_filter is None and "HCCL_RANDOM_SEED" not in os.environ:
            self.assertEqual(executed, len(SEEDS) * CASES_PER_SEED)
            self.assertGreaterEqual(executed, 30)
            self.assertEqual(
                coverage["primitive"],
                {"AllReduce", "AllGather", "ReduceScatter"},
            )
            self.assertTrue({1, 2, 4, 8, 16}.issubset(coverage["rank"]))
            self.assertIn(17, coverage["count"])
            self.assertTrue(any(count > 1 for count in coverage["count"]))
            self.assertEqual(coverage["dtype"], {HCCL_FP32, HCCL_FP16, HCCL_BF16})
            self.assertEqual(
                coverage["reduce_op"],
                {HCCL_SUM, HCCL_PROD, HCCL_MAX, HCCL_MIN},
            )

    def _execute_case(self, case):
        primitive = case["primitive"]
        payload = case["payload"]
        data_type = case["dtype"]
        op = case["reduce_op"]

        if primitive == "AllReduce":
            result = self.engine.execute_allreduce_data(
                payload, algorithm="Wrapper", op=op, data_type=data_type,
            )
            self.assertEqual(result["status"], "success", case)
            return result["result"], HcclAllReduceReference(
                payload, op=op, data_type=data_type,
            )
        if primitive == "AllGather":
            result = self.engine.execute_allgather(
                payload, algorithm="Wrapper", data_type=data_type,
            )
            self.assertEqual(result["status"], "success", case)
            return result["result"], HcclAllGatherReference(
                payload, data_type=data_type,
            )

        result = self.engine.execute_reducescatter(
            payload, data_type=data_type, op=op,
        )
        self.assertEqual(result["status"], "success", case)
        return result["result"], HcclReduceScatterReference(
            payload, op=op, data_type=data_type,
        )


if __name__ == "__main__":
    unittest.main()
