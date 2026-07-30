"""G2-E primitive-specific Checker contracts."""

import unittest

from plugin.hccl_vm_checker import parse_official_result
from plugin.hccl_vm_runner import OfficialCollectiveRequest


ALLGATHER_LOG = """
__HCCL_AGENT_HCCL_CONFIG_EXIT_CODE=0
__HCCL_AGENT_MOCK_EXIT_CODE=0
__HCCL_AGENT_TEST_EXIT_CODE=0
[info] Op summary, opIndex=0, collectiveType=AllGather, rankCount=2,
dataType=INT32, elementCount=8, reduceType=SUM, opGroupSize=2
[info] CheckerV3 stage finished, stage=GenGraph, status=success
[info] CheckerV3 stage finished, stage=SingleTaskCheck, status=success
[info] CheckerV3 stage finished, stage=MemConflict, status=success
[info] CheckerV3 stage finished, stage=SemanticCheck, status=success
[info] op[0] Checker Success
__HCCL_AGENT_CHECKER_EXIT_CODE=0
[info] Shell exited. Host shutting down.
__HCCL_AGENT_VM_EXIT_CODE=0
"""

REDUCESCATTER_LOG = ALLGATHER_LOG.replace(
    "AllGather", "ReduceScatter"
)


class TestHcclVmMultiPrimitiveChecker(unittest.TestCase):

    def test_allgather_ignores_observed_reduce_type(self):
        request = OfficialCollectiveRequest(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        result = parse_official_result(
            ALLGATHER_LOG.replace("reduceType=SUM", "reduceType=MAX"),
            outer_exit_code=0,
            request=request,
        )
        self.assertTrue(result.passed)
        self.assertTrue(result.metadata_match)
        self.assertEqual(result.op_summaries[0]["reduce_type"], "MAX")

    def test_allgather_element_count_is_strict(self):
        request = OfficialCollectiveRequest(
            primitive="AllGather",
            rank_count=2,
            dtype="int32",
            reduce_op=None,
            elements=8,
        )
        result = parse_official_result(
            ALLGATHER_LOG.replace("elementCount=8", "elementCount=16"),
            outer_exit_code=0,
            request=request,
        )
        self.assertFalse(result.passed)
        self.assertFalse(result.metadata_match)

    def test_reducescatter_requires_sum_and_output_element_count(self):
        request = OfficialCollectiveRequest(
            primitive="ReduceScatter",
            rank_count=2,
            dtype="int32",
            reduce_op="sum",
            elements=8,
        )
        passed = parse_official_result(
            REDUCESCATTER_LOG,
            outer_exit_code=0,
            request=request,
        )
        wrong_reduce = parse_official_result(
            REDUCESCATTER_LOG.replace("reduceType=SUM", "reduceType=MAX"),
            outer_exit_code=0,
            request=request,
        )
        self.assertTrue(passed.passed)
        self.assertFalse(wrong_reduce.passed)
        self.assertFalse(wrong_reduce.metadata_match)


if __name__ == "__main__":
    unittest.main()
